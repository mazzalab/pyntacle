from algorithms.key_player import *
from algorithms.key_player import _KeyplayerAttribute
from exceptions.generic_error import Error
from io_stream.graph_to_binary import GraphToBinary
from misc.graph_load import GraphLoad
from misc.kp_runner import *
from report.plotter import *
from report.reporter import *
from utils.graph_utils import *

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "14 November 2016"
__license__ = u"""
  Copyright (C) 20016-2017  Tommaso Mazza <t,mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software; you can use and redistribute it under
  the terms of the BY-NC-ND license as published by
  Creative Commons; either version 4 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  License for more details.

  You should have received a copy of the license along with this
  work. If not, see http://creativecommons.org/licenses/by-nc-nd/4.0/.
  """


class KeyPlayer():
    """
    **[EXPAND]**
    """
    def __init__(self, args):
        self.logging = log
        self.args = args
        # Check for pycairo
        if not self.args.no_plot and util.find_spec("cairo") is None:
            sys.stdout.write("WARNING: It seems that the pycairo library is not installed/available. Plots"
                             "will not be produced.")
            self.args.no_plot = True

    def run(self):
        cursor = CursorAnimation()
        cursor.daemon = True
        cursor.start()
        if self.args.m_reach == None and self.args.type in ["pos", "all"]:
            raise Error("m reach distance must be provided")

        # Checking input file
        if self.args.input_file is None:
            self.logging.error(
                "Please specify an input file using the -i option.".format(self.args.input_file))
            sys.exit()
        if not os.path.exists(self.args.input_file):
            self.logging.error("Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit()
        if self.args.no_header:
            header = False
        else:
            header = True
        # check output directory

        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: Output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        # Parsing optional node list
        if hasattr(self.args, 'nodes'):
            self.args.nodes = self.args.nodes.split(',')
            # self.args.nodes = [str.lower(x) for x in self.args.nodes]

        if not hasattr(self.args, 'which'):
            raise Error("usage: pyntacle.py keyplayer {kp-finder, kp-info} [options]'")

        self.logging.debug('Running pyntacle keyplayer, with arguments')
        self.logging.debug(self.args)

        # Load Graph
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header).graph_load()

        # init Utils global stuff
        utils = GraphUtils(graph=graph)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(
                    "Taking the largest component of the input graph as you requested ({} nodes, {} edges)\n".format(
                        graph.vcount(), graph.ecount()))

            except MultipleSolutionsError:
                sys.stderr.write(
                    "The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the \"--largest-component\" option. Quitting\n")
                sys.exit(1)

        # Check provided dimensions' format
        if self.args.plot_dim:  # define custom format
            self.args.plot_dim = self.args.plot_dim.split(",")
    
            for i in range(0, len(self.args.plot_dim)):
                try:
                    self.args.plot_dim[i] = int(self.args.plot_dim[i])
        
                except ValueError:
                    sys.stderr.write(
                        "Format specified must be a comma separated list of values(e.g. 1920,1080). Quitting\n")
                    sys.exit(1)
        
                if self.args.plot_dim[i] <= 0:
                    sys.stderr.write(
                        "Format specified must be a comma separated list of values(e.g. 1920,1080). Quitting\n")
                    sys.exit(1)
    
            plot_size = tuple(self.args.plot_dim)

        else:
            # generate different formats according to graph size
            if graph.vcount() <= 150:
                plot_size = (800, 800)
    
            else:
                plot_size = (1600, 1600)
                
        # initialize keyplayer wrapper
        kp_runner = KeyPlayerWrapper(
            graph=graph)  # initialize keyplayer wrapper #will run KP metrics on behalf of us

        if self.args.which == 'kp-finder':
            k_size = self.args.k_size
            # Greedy optimization
            if self.args.implementation == "greedy":

                sys.stdout.write("Using Greedy Optimization Algorithm for searching optimal KP-Set\n")

                if self.args.type == 'neg' or self.args.type == 'all':  # will not return nothing, as "get_results" will do it.
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using F (kp neg measure)\n".format(
                            self.args.k_size))
                    kp_runner.run_greedy(key_player=_KeyplayerAttribute.F, kpsize=self.args.k_size)

                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using DF (kp neg measure)\n".format(
                            self.args.k_size))
                    kp_runner.run_greedy(key_player=_KeyplayerAttribute.DF, kpsize=self.args.k_size)

                if self.args.type == 'pos' or self.args.type == 'all':
                    kp_runner.run_greedy(key_player=_KeyplayerAttribute.DR, kpsize=self.args.k_size)
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using dR (kp pos measure)\n".format(
                            self.args.k_size))

                    kp_runner.run_greedy(key_player=_KeyplayerAttribute.MREACH, kpsize=self.args.k_size,
                                         m=self.args.m_reach)
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {0} using an MREACH measure of {1} (kp pos measure)\n".format(
                            self.args.k_size, self.args.m_reach))

            elif self.args.implementation == "brute-force":
                sys.stdout.write("Using Brute Force for searching optimal KP-Set\n")

                if self.args.type == 'neg' or self.args.type == 'all':  # will not return nothing, as "get_results" will do it.
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using F (kp neg measure)\n".format(
                            self.args.k_size))
                    kp_runner.run_bruteforce(key_player=_KeyplayerAttribute.F, kpsize=self.args.k_size)

                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using DF (kp neg measure)\n".format(
                            self.args.k_size))
                    kp_runner.run_bruteforce(key_player=_KeyplayerAttribute.DF, kpsize=self.args.k_size)

                if self.args.type == 'pos' or self.args.type == 'all':
                    kp_runner.run_bruteforce(key_player=_KeyplayerAttribute.DR, kpsize=self.args.k_size)
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using dR (kp pos measure)\n".format(
                            self.args.k_size))

                    kp_runner.run_bruteforce(key_player=_KeyplayerAttribute.MREACH, kpsize=self.args.k_size,
                                             m=self.args.m_reach)
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {0} using an MREACH measure of {1} (kp pos measure)\n".format(
                            self.args.k_size, self.args.m_reach))

            else:
                sys.stdout.write("Wrong implementatio. Please contact pyntacle Developers and sent this error message, along with a command line and a log.\nQuitting.\n")
                sys.exit(1)

            sys.stdout.write("Search for the best kp set completed!\n")

            results = kp_runner.get_results()

            for kp in results.keys(): #ONJE OF THE keys represent the algorithm, so no else exit in here

                if kp == _KeyplayerAttribute.F or kp == _KeyplayerAttribute.DF:
                    sys.stdout.write(
                        'kp set of size {0} for Key Player Metric {1} is {2} with value {3} (starting value is {4})\n'.format(
                            self.args.k_size, kp.name, ",".join(results[kp][1]), results[kp][2],
                            results[kp][0]))

                elif kp == _KeyplayerAttribute.DR:
                    sys.stdout.write('kp set of size {0} for Key Player Metric {1} is {2} with value {3}\n'.format(
                        self.args.k_size, kp.name, ",".join(results[kp][1]), results[kp][2]))

                elif kp == _KeyplayerAttribute.MREACH:
                    node_perc_reached = ((results[kp][2] + len(results[kp][1])) / graph.vcount()) * 100
                    if node_perc_reached == 100:
                        node_perc_reached = int(node_perc_reached)
                    else:
                        node_perc_reached = round(node_perc_reached, 2)

                    sys.stdout.write(
                        'kp set of size {0} with a reach of {1} for Key Player Metric {2} is {3} with value {4} (reaching the {5}% of nodes)\n'.format(
                            self.args.k_size, self.args.m_reach, kp.name, ",".join(results[kp][1]),
                            results[kp][2], node_perc_reached))

        # kpinfo: compute kpmetrics for a set of predetermined nodes
        elif self.args.which == 'kp-info':
            k_size = len(self.args.nodes)

            sys.stdout.write('\nNodes given as input: {}\n'.format(self.args.nodes))
            if self.args.type == 'neg' or self.args.type == 'all':
                kp_runner.run_pos_or_neg(choice="kpp-neg", names_list=self.args.nodes, recalculate=True)
                # sys.stdout.write('F: {0}\t DF: {1}\n'.format(F, DF))

            if self.args.type == 'pos' or self.args.type == 'all':
                kp_runner.run_pos_or_neg(choice="kpp-pos", names_list=self.args.nodes, recalculate=True,
                                         m=self.args.m_reach)
                # sys.stdout.write('MR: {0}\t dR: {1}\n'.format(MR, dR))

            results = kp_runner.get_results()
            sys.stdout.write("keyplayer metrics report for {} values:\n".format(self.args.type.upper()))
            for metric in results.keys():

                if metric == _KeyplayerAttribute.F or metric == _KeyplayerAttribute.DF:
                    sys.stdout.write(
                        "starting value for {0} is {1}. removing nodes {2} gives a {0} value of {3}\n".format(
                            metric.name, results[metric][0], self.args.nodes, results[metric][-1]))

                elif metric == _KeyplayerAttribute.MREACH:
                    perc_node_reached = results[metric][-1] + len(self.args.nodes) / graph.vcount()
                    sys.stdout.write(
                        "Nodes {0} have an {1} of {2}, meaning they can reach the {3}% of nodes in {4} steps\n".format(
                            results[metric][1], metric.name, results[metric][-1], perc_node_reached,
                            self.args.m_reach))

                else:
                    sys.stdout.write(
                        "{0} value for nodes {1} is {2}\n".format(metric.name, results[metric][1],
                                                                  results[metric][-1]))
        else:
            log.critical(
                "This should not happen. Please contact pyntacle Developers and send your command line. Quitting\n.")
            sys.exit(1)

        # reporting and plotting part

        sys.stdout.write("Producing report in {} format.\n".format(self.args.report_format))

        report_prefix = "_".join(
            ["pyntacle", self.args.which, graph["name"][0], "kpsize", str(k_size), results.get("algorithm", "KP-Info"),"report", runtime_date])
        report_path = os.path.join(self.args.directory, ".".join([report_prefix, self.args.report_format]))

        if os.path.exists(report_path):
            self.logging.warning(
                "A report with the same name ({}) already exists, overwriting it".format
                (os.path.basename(report_path)))

        r = pyntacleReporter(graph=graph)
        r.report_KP(resultsdic=results, m=self.args.m_reach)
        r.create_report(report_path=report_path)

        if self.args.save_binary:
            sys.stdout.write("Saving graph to a Binary file\n")
            binary_path = os.path.join(self.args.directory, report_prefix + ".graph")
            GraphToBinary(graph=graph).save(file_name=binary_path)

        # generate and output plot
        if not self.args.no_plot or graph.vcount() < 1000:
    
            sys.stdout.write("Generating plots in {} format.\n".format(self.args.plot_format))

            plot_dir = os.path.join(self.args.directory, "pyntacle-Plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    "A directory named \"pyntacle-Plots\" already exists, I may overwrite something in there")

            else:
                os.mkdir(plot_dir)


            plot_graph = PlotGraph(graph=graph)

            plot_format = self.args.plot_format
            plot_graph.set_node_label(labels=graph.vs()["name"])  # assign node labels to graph

            pal = sns.color_palette("Accent", 8).as_hex()
            framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()

            other_nodes_colour = pal[2]
            other_frame_colour = framepal[2]

            other_nodes_size = 25
            # other_nodes_shape = "circle"
            other_edge_width = 1

            for metric in results:

                if metric.name == "F":

                    f_nodes_colour = pal[0]
                    f_frames_colour = framepal[0]
                    # create a list of node colours
                    node_colours = [f_nodes_colour if x["name"] in results[metric][1] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [f_frames_colour if x["name"] in results[metric][1] else other_frame_colour
                                    for x in
                                    graph.vs()]

                    plot_graph.set_node_colours(colours=node_colours)

                    # node_shapes = ["square" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                elif metric.name == "DF":
                    df_nodes_colour = pal[1]
                    df_frames_colour = framepal[1]

                    # create a list of node colours
                    node_colours = [df_nodes_colour if x["name"] in results[metric][1] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [df_frames_colour if x["name"] in results[metric][1] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colours(colours=node_colours)

                    # node_shapes = ["rectangle" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                elif metric.name == "MREACH":
                    mreach_nodes_colour = pal[4]
                    mreach_frames_colour = framepal[4]
                    # create a list of node colours
                    node_colours = [
                        mreach_nodes_colour if x["name"] in results[metric][1] else other_nodes_colour for x
                        in
                        graph.vs()]

                    node_frames = [mreach_frames_colour if x["name"] in results[metric][1] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colours(colours=node_colours)


                    # node_shapes = ["triangle-up" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                elif metric.name == "dR":
                    dr_nodes_colour = pal[3]
                    dr_frames_colour = framepal[3]

                    # create a list of node colours
                    node_colours = [dr_nodes_colour if x["name"] in results[metric][1] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [dr_frames_colour if x["name"] in results[metric][1] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colours(colours=node_colours)

                    # node_shapes = ["triangle-down" if x["name"] in results[metric][1] else other_nodes_shape for x in
                    #                graph.vs()]
                    #
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                else:
                    self.logging.critical(
                        "This should not happen. Please contact pyntacle developer and send a command line, along with a log. Quitting\n")
                    sys.exit(1)

                node_sizes = [35 if x["name"] in results[metric][1] else other_nodes_size for x in graph.vs()]

                plot_graph.set_node_sizes(sizes=node_sizes)
                # print (other_edge_width)

                #     print (edge.source(), edge.target())
                # add recursive edge widths
                if metric.name != "MREACH":

                    edge_widths = [5 if any(y in results[metric][1] for y in x["node_names"]) else other_edge_width for
                                   x in graph.es()]

                else:
                    mreach_nodes = results[metric][1]
                    # get node indices of corresponding kpset
                    indices = GraphUtils(graph=graph).get_node_indices(mreach_nodes)

                    edge_widths = [other_edge_width for x in
                                   range(0, graph.ecount())]  # define a starting list of values

                    mreach_width = (self.args.m_reach * 2) + 2  # maxium and minimum boundaries for edge width
                    # print(mreach_width)

                    if mreach_width > 10:
                        sys.stdout.write(
                            "WARNING - you choose a very high value of m-reach, the edge with may be too big, hence obscuring a great part of the plot\n")

                    memory_indices = indices
                    step_before = indices

                    for i in range(1, self.args.m_reach + 1):
                        # print(mreach_width)
                        neighbours = Graph.neighborhood(graph, vertices=indices)
                        # print(neighbours)

                        indices = [y for x in neighbours for y in x]  # flat out list of indices
                        # print(indices)
                        remaining_indices = list(set(indices) - set(memory_indices))

                        # print(remaining_indices)
                        # print(step_before)

                        mreach_edge_ids = []
                        for elem in step_before:
                            for el in remaining_indices:
                                try:
                                    mreach_edge_ids.append(graph.get_eid(elem, el))
                                except InternalError:
                                    pass

                        # print (mreach_edge_ids)
                        for edge in mreach_edge_ids:
                            edge_widths[edge] = mreach_width

                        # finally
                        mreach_width = mreach_width - 2
                        memory_indices = memory_indices + remaining_indices
                        step_before = remaining_indices

                        # sys.exit()

                plot_graph.set_edge_widths(edge_widths)

                plot_graph.set_layouts(layout="fruchterman_reingold")

                plot_path = os.path.join(plot_dir, "_".join(["keyplayer", graph["name"][0], "report", metric.name,
                                                             datetime.datetime.now().strftime(
                                                                 "%d%m%Y%H%M")]) + "." + plot_format)
                if os.path.exists(plot_path):
                    sys.stdout.write(
                        "WARNING - A plot with the name ({}) already exists, overwriting it\n".format(
                            os.path.basename(plot_path)))
                # print(plot_path)
                # input()
                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=True,
                                      keep_aspect_ratio=True, vertex_label_size=8, vertex_frame_color=node_frames)

        elif graph.vcount() >= 1000:
            sys.stdout.write("The graph has too many nodes ({}). Can't draw graph\n".format(graph.vcount()))
        cursor.stop()
        sys.stdout.write("pyntacle Keyplayer completed successfully. Ending\n")
        sys.exit(0)