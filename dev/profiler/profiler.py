import cProfile, pstats, io
import numpy as np
import pandas as pd
from pstats import SortKey
import subprocess
import tracemalloc
import linecache
import timeit
from time import time
import os
from functools import partial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def traceMalloc():

    def display_top(snapshot, key_type='lineno', limit=3):
        snapshot = snapshot.filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
        ))
        top_stats = snapshot.statistics(key_type)

        print("Top %s lines" % limit)
        for index, stat in enumerate(top_stats[:limit], 1):
            frame = stat.traceback[0]
            # replace "/path/to/module/file.py" with "module/file.py"
            filename = os.sep.join(frame.filename.split(os.sep)[-2:])
            print("#%s: %s:%s: %.1f KiB"
                % (index, filename, frame.lineno, stat.size / 1024))
            line = linecache.getline(frame.filename, frame.lineno).strip()
            if line:
                print('    %s' % line)

        other = top_stats[limit:]
        if other:
            size = sum(stat.size for stat in other)
            print("%s other: %.1f KiB" % (len(other), size / 1024))
        total = sum(stat.size for stat in top_stats)
        print("Total allocated size: %.1f KiB" % (total / 1024))


    tracemalloc.start()

    parser = create_parser()

    # global measurment
    args = parser.parse_args(['global', '-t', 'matrix', '-i', './profiling/graphs/erdos_renyi.txt'])
    
    # function to memory trace
    main(args)

    snapshot = tracemalloc.take_snapshot()
    display_top(snapshot)

    tracemalloc.stop()
    
    return



################Execution Graph################
# gprof2dot -f pstats myLog.profile -o callingGraph.dot #

# dot -Tsvg ./callingGraph.dot  -O # GraphViz visualization

###################NOTES###################
# non sarebbe il caso di gestire meglio le descrizione del --help? a volte sono confusionarie. 
# manca l'implementazione della adj matrix per grafi diretti Non prevista
# perchè le probabilità sono fissate? FIXED
# errore nella variabile outputdir FIXED

# profiling function
def cProfiler_compute(func, runs, args, verbose=False, output_file=None):

    if runs < 0:
        print("Runs must be >= 1")
        return
     
    def stdout_to_pd(stdout_value) -> list:
    
        # split the output 
        splitted_output = stdout_value.split("\n")
        print(splitted_output[0])
        pandas_rows = []

        #skip the first 5 lines and the last 3
        for i in range(5, len(splitted_output)-3):
            
            temp = splitted_output[i].split()
            line = []

            line.append(temp[0])

            for token in temp[1:5]:
                line.append(float(token))
            
            line.append(" ".join(temp[5:]))
            pandas_rows.append(line)

        return pandas_rows

    pr = cProfile.Profile()

    profiler = cProfile.Profile()
    profiler.enable()
    func(args) # func(*args, **keywords)
    profiler.disable()

    if output_file != None:

        profiler.dump_stats(output_file)
        path, profile_name = os.path.split(output_file)

        dot_name = profile_name[:-7] + ".dot"
        svg_name = profile_name[:-7] + ".svg"

        result = subprocess.run(["gprof2dot", "-f", "pstats", output_file, "-o", os.path.join(path, dot_name), "--show-samples"], capture_output=True)
        result = subprocess.run(["dot", "-Tsvg", os.path.join(path, dot_name), "-o", os.path.join(path, svg_name)], capture_output=True) 

    output = io.StringIO()
    stats = pstats.Stats(profiler, stream=output)
    stats.strip_dirs().sort_stats("name")
    stats.print_stats()

    profiler_output = output.getvalue()

    if verbose:
        print("------------callers------------")
        output.truncate(0)
        output.seek(0)
        stats.print_callers()
        print(f"\n{output.getvalue()}\n")
        # print("\n#################################################################################\n")

    df = pd.DataFrame(stdout_to_pd(profiler_output), columns=["ncalls",  "tottime",  "percall_tot",  "cumtime",  "percall_cum", "filename:lineno(function)"])
    results = np.zeros((runs, df.shape[0], 4))

    results[0,:,:] = df[["tottime",  "percall_tot",  "cumtime",  "percall_cum"]]

    for run in range(1, runs):

        pr.clear()
        profiler.enable()
        func(args) #  func(*args, **keywords)
        profiler.disable()

        output = io.StringIO()
        stats = pstats.Stats(profiler, stream=output)
        stats.strip_dirs().sort_stats("name")
        # stats.sort_stats('cumulative')  
        stats.print_stats()

        df = pd.DataFrame(stdout_to_pd(profiler_output), columns=["ncalls",  "tottime",  "percall_tot",  "cumtime",  "percall_cum", "filename:lineno(function)"])

        results[run, :, :] = df[["tottime",  "percall_tot",  "cumtime",  "percall_cum"]]
    
    # mean and std of multiple runs
    mean_results = np.mean(results, axis=0)
    std_results = np.std(results, axis=0)

    if runs > 1:
        for i in range(4):

            column = df.columns[i+1]
            df[column + '_mean'] =  mean_results[:,i]
            df[column + '_std'] = std_results[:,i]

            df.sort_values(by=['tottime_mean'], ascending=False, inplace=True)
            total_time = np.sum(df['tottime_mean'])
            std_time = np.sum(df['tottime_std'])
    else:
        df.sort_values(by=[ 'tottime'], ascending=False, inplace=True)    
        total_time = np.sum(df['tottime'])
        std_time = 0

    if verbose:
        print(df)

    return total_time, std_time

def cProfiling():

    # Coarse-grained profiling
    for graph_type in ["erdos-renyi"]:
        for index_nodes, nodes_num in enumerate(["1000"]):
            for index_proba, proba in enumerate(["0.25"]):


                # Generate graph
                print("################################################")
                print(f"Graph type: {graph_type}\nNodes num: {nodes_num}\nProba: {proba}")
                # Define the function and arguments in the setup
                
                setup = f"""
from main import main, create_parser
import sys

# orig_stdout = sys.stdout
# f = open('./out.txt', 'w')
# sys.stdout = f

parser = create_parser()
args = parser.parse_args(['generate', 'erdos-renyi', '-t', 'matrix', '-n', '{str(nodes_num)}', '-p', '{str(proba)}', '-o', './profiling/graphs'])
"""

                # Benchmark the function call with the argument
                # execution_time = timeit.timeit(stmt="main(args)", setup=setup, globals=globals(), number=1)
                # print(f"Generate -> -n {nodes_num} -p {proba}\nExecution time: {execution_time} seconds:\n\n")
                # generate_exec[(nodes_num, proba)] = execution_time
                
                # generate the graph
                # args = parser.parse_args(['generate', 'erdos-renyi', '-t', 'matrix', '-n', nodes_num, '-p', proba, '-o', './profiling/graphs'])
                # timeit.timeit()
                
                # key-player-finder
                keyplayer_exec = {}

                for oper in ["dF"]: #ho tolto dF
                    for k in ['1','2','3']:
                        setup = f"""
from main import main, create_parser
import sys

parser = create_parser()
args = parser.parse_args(['keyplayer', 'kp-finder', '-t', 'dot', '-i', './profiling/graphs/barabasi.dot', '-k', '{k}', '-a', 'greedy', '-oper', '{oper}'])
"""
                    
                        # Benchmark the function call with the argument
                        runs = []

                        for run  in range(1):
                            start = time()
                            execution_time = timeit.timeit(stmt="main(args)", setup=setup, globals=globals(), number=10)
                            end = time()
                            runs.append((end-start)/10)
                            print(f"Execution time: {(end-start)/10} seconds:\n\tKp-finder -> -k {k} -oper {oper} -n {nodes_num} -p {proba}\n\n")
                        keyplayer_exec[(oper, k, nodes_num, proba)] = runs
                        print("################################################")
                
                
                kp_time = pd.DataFrame.from_dict(keyplayer_exec, columns=['time_' + str(i) for i in range(len(runs))], orient='index')
                index = pd.MultiIndex.from_tuples(keyplayer_exec.keys(), names=['oper', 'k', 'nodes_num', 'proba'])
                kp_time = kp_time.set_index(index)
                print(kp_time)
                # kp_time.to_csv(f"./profiling/results/Python_{nodes_num}_e{proba}.tsv", sep="\t", index=True)
                       
    return 


def writeTimes(time_diz):

    return 

if __name__ == '__main__':
    # traceMalloc()
    cProfiling()
	# main()
    # plot_benchmark()

#PROFILER NOTES
'''
- From grafo_to_matrix removed "name_from_edge" (91 sec -> 41 sec)  10000 nodi
- From grafo_to_dot removed "name_from_edge"    (59.813 -> 27.822)  10000 nodi



Key players info:

Bottleneck is "distance_fragmentation" 64% of the computation, caused by search for shortest paths (around 8min for 10k 0.25 on my pc)
- The call happens 3 times, possible solutions: run twice, or run once per metric (?)

Greedy approach, instead of recomputing the shotest path every single time -> better solutions?
For Distqance Frag. -> compute the distance only for nodes that are higher than i

'''
