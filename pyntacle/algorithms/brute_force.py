import math
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
from algorithms.key_player import *
import sys
import igraph as ig
import multiprocessing
import pandas as pd
import numpy as np
import pickle as pkl
from functools import partial
from GraphTacle import Graphtacle


def call_keyPlayerFinder(grafo, chunks, operation, mdist=None):
    kppset_score_pairs = {}
    ksp_f={}
    ksp_df={}
    ksp_dr={}
    ksp_reach={}
    c=1
    for node_names in chunks:
        temp_grafo = ig.Graph(directed=False,vertex_attrs={"name":grafo.vs["name"],"label": grafo.vs["label"]},edges=grafo.get_edgelist())
        temp_grafo.delete_vertices(node_names)

        if operation=="all":
            ksp_f[node_names] = fragmentation(temp_grafo)  ## negative
            ksp_df[node_names] = distance_fragmentation(temp_grafo)  ## negative
            nodes = []
            
            for i in list(node_names): 
                nodes.append(grafo.vs.find(name=i).index)
            
            ksp_dr[node_names] = distance_weighted_reach(grafo,nodes)  ## positive
            ksp_reach[node_names] = reachability(grafo,mdist,nodes) ##positive

            if c==len(chunks):
                kppset_score_pairs={"kp-set":list(ksp_f.keys()), "F":list(ksp_f.values()), "dF":list(ksp_df.values()), "dR":list(ksp_dr.values()), "mreach":list(ksp_reach.values())}
            c=c+1

        elif operation=="F":
            kppset_score_pairs[node_names] = fragmentation(temp_grafo)  ## negative
        elif operation=="dF":
            kppset_score_pairs[node_names] = distance_fragmentation(temp_grafo)  ## negative
        elif operation=="dR":
            nodes = []
            for i in list(node_names): 
                nodes.append(grafo.vs.find(name=i).index)
            kppset_score_pairs[node_names] = distance_weighted_reach(grafo,nodes)  ## positive
        elif operation=="mreach":
            nodes = []
            for i in list(node_names): 
                nodes.append(grafo.vs.find(name=i).index)
            kppset_score_pairs[node_names] = reachability(grafo,mdist,nodes) ##positive
        else:
            raise TypeError(u"'all | F | dF | dR | mreach' are the available options if the multicore flag -oper is activated, default all") 
    
    ##### debugging
       
    #####
    return kppset_score_pairs



def brute_force_keyplayer(grafo,operation,k_size=None,mdist=None,nodes=None, nprocs=1):##### mettere 1
    
    node_names = grafo.vs["name"]
    kpset_score_pairs={}
    allS = list(itertools.combinations(node_names, k_size))
    if nprocs > 1:
        print("Parallelization")
        # # Create chunks
        chunklen = math.ceil(len(allS) / nprocs)
        chunks = [allS[i * chunklen:(i + 1) * chunklen] for i in range(nprocs)] ## divide i chunks in parti uguali, tante quante sono i nprocs
        with ProcessPoolExecutor(max_workers=nprocs) as executor:
            future_dict = {executor.submit(call_keyPlayerFinder, grafo=grafo, chunks=chunk, operation=operation, mdist=mdist): chunk for chunk in chunks}

            for future in as_completed(future_dict):
                chunk = future_dict[future]
                try:
                    partial_result = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (chunk, exc))
                else:
                    # Merge the dictionaries without overwriting the same keys (error in the Capocefalo version?)
                    for key, value in partial_result.items():
                        if key in kpset_score_pairs:
                            # Assume the values are lists and concatenate them
                            kpset_score_pairs[key].extend(value)
                        else:
                            # If the key is not present in the kpset_score_pairs, add it
                            kpset_score_pairs[key] = value

    else:
        sys.stdout.write(u"\nBrute-force search of the best kp-set of size {}\n".format(k_size))
        chunks = allS
        kpset_score_pairs = call_keyPlayerFinder(grafo, chunks, operation, mdist)

    if operation!="all":
        maxKpp = max(kpset_score_pairs.values())
        final = [sorted(list(x)) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == maxKpp]
        maxKpp = maxKpp
        return final, maxKpp
    else:
        maxKppF = max(kpset_score_pairs["F"])
        maxKppdF = max(kpset_score_pairs["dF"])
        maxKppdR = max(kpset_score_pairs["dR"])
        maxKppM = max(kpset_score_pairs["mreach"])

        kpset_score_pairs=pd.DataFrame(kpset_score_pairs)

        tF = list(kpset_score_pairs["kp-set"][kpset_score_pairs["F"]==float(maxKppF)])
        tdF = list(kpset_score_pairs["kp-set"][kpset_score_pairs["dF"]==float(maxKppdF)])
        tdR = list(kpset_score_pairs["kp-set"][kpset_score_pairs["dR"]==float(maxKppdR)])
        tM = list(kpset_score_pairs["kp-set"][kpset_score_pairs["mreach"]==float(maxKppM)])
        df = pd.DataFrame({"K-set":[tF,tdF,tdR,tM], "Operation": ["F", "dF", "dR", "mreach"], "Score": [maxKppF,maxKppdF,maxKppdR,maxKppM]})

        #### debugging

        ####

        return df




    ############## groupcentrality
def call_groupcentralityFinder(grafo, chunks, np_counts, np_paths, operation, distance_type="min"):
    gc_d={} # degree
    gc_b={} # betweenness
    gc_c={} # closeness
    c=1
    score_pairs_partial = {}
    for node_names in chunks:
        if operation == "all":
            gc_d[node_names] = grafo.group_degree(nodes=node_names)

            if np_counts is None or np_counts.size == 0:
                np_counts = grafo.get_shortestpath_count()
            gc_b[node_names] = grafo.group_betweenness(np_counts=np_counts,nodes=node_names)
            if np_paths is None or np_paths.size == 0:
                np_paths = grafo.get_shortestpaths()
            
            gc_c[node_names] = grafo.group_closeness(nodes=node_names, np_paths=np_paths, distance_type=distance_type)
            if c==len(chunks):
                score_pairs_partial={"cg-set":list(gc_d.keys()), "Degree":list(gc_d.values()), "Closeness":list(gc_c.values()), "Betweenness":list(gc_b.values())}
            c=c+1

        elif operation == "degree":
            score = grafo.group_degree(nodes=node_names)
            score_pairs_partial[tuple(node_names)] = score
        elif operation == "closeness":
            if np_paths is None or np_paths.size == 0:
                np_paths = grafo.get_shortestpaths()
            score = grafo.group_closeness(node_names, np_paths=np_paths, distance_type=distance_type)
            score_pairs_partial[tuple(node_names)] = score
        elif operation == "betweenness":
            if np_counts is None or np_counts.size == 0:
                np_counts = grafo.get_shortestpath_count()
            score = grafo.group_betweenness(np_counts=np_counts,nodes=node_names)
            score_pairs_partial[tuple(node_names)] = score
        else:
            raise WrongArgumentError("{} function not yet implemented.".format(operation))

    return score_pairs_partial




def brute_force_groupcentrality(grafo, k_size, operation, distance_type, nprocs=1):
    
    node_names = grafo.vs["name"]
    # Generate all combinations of size k
    allS = list(itertools.combinations(node_names, k_size))
    sys.stdout.write(u"Evaluating {} possible solutions\n".format(len(allS)))

    # Pre-calculate all shortest paths count and shortest paths
    np_counts = grafo.get_shortestpath_count()
    np_paths = grafo.get_shortestpaths()
    score_pairs_partial={}

    if nprocs > 1:
        print(f"Parallelization with {int(nprocs)} processes")
        # # Create chunks
        chunklen = math.ceil(len(allS) / nprocs)
        chunks = [allS[i * chunklen:(i + 1) * chunklen] for i in range(nprocs)] ## divide i chunks in parti uguali, tante quante sono i nprocs
        with ProcessPoolExecutor(max_workers=nprocs) as executor:
            future_dict = {executor.submit(call_groupcentralityFinder, grafo=grafo, chunks=chunk, np_counts=np_counts, \
                            np_paths=np_paths, operation=operation, distance_type=distance_type): chunk for chunk in chunks}

            for future in as_completed(future_dict):
                chunk = future_dict[future]
                try:
                    partial_result = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (chunk, exc))
                else:
                    # Merge the dictionaries without overwriting the same keys (error in the Capocefalo version?)
                    for key, value in partial_result.items():
                        if key in score_pairs_partial:
                            # Assume the values are lists and concatenate them
                            score_pairs_partial[key].extend(value)
                        else:
                            # If the key is not present in the kpset_score_pairs, add it
                            score_pairs_partial[key] = value
    else:
        sys.stdout.write(u"Brute-force search of the best group of nodes of size {}\n".format(k_size))

        chunks = allS
        score_pairs_partial = call_groupcentralityFinder(grafo, chunks=chunks,np_counts=np_counts,np_paths=np_paths,operation=operation, distance_type=distance_type)

    if operation!="all":
        _group_score = max(score_pairs_partial.values())  # take the maximum value
        final = [sorted(list(x)) for x in score_pairs_partial.keys() if score_pairs_partial[x] == _group_score]
        return final, _group_score
    else:
        maxD= max(score_pairs_partial["Degree"])
        maxB= max(score_pairs_partial["Betweenness"])
        maxC= max(score_pairs_partial["Closeness"])

        score_pairs_partial=pd.DataFrame(score_pairs_partial)

        tD = list(score_pairs_partial["cg-set"][score_pairs_partial["Degree"]==float(maxD)])
        tB = list(score_pairs_partial["cg-set"][score_pairs_partial["Betweenness"]==float(maxB)])
        tC = list(score_pairs_partial["cg-set"][score_pairs_partial["Closeness"]==float(maxC)])
        df = pd.DataFrame({"Nodes Set":[tD,tB,tC], "Operation": ["Degree", "Betweenness", "Closeness"], "Score": [maxD,maxB,maxC]})
        
        return df
       