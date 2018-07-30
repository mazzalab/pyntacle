__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.2"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t.mazza@css-mendel.it>
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

from cmds.cmds_utils.kpsearch_wrapper import KPWrapper as kpw
from cmds.cmds_utils.kpsearch_wrapper import GOWrapper as gow
from cmds.cmds_utils.kpsearch_wrapper import BFWrapper as bfw
from algorithms.keyplayer import KeyPlayer as kpp
from itertools import chain
from exceptions.generic_error import Error
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import *
from cmds.cmds_utils.reporter import *
from tools.graph_utils import *
from tools.misc.graph_load import *
from tools.enums import ReportEnum, CmodeEnum
from tools.add_attributes import AddAttributes

class KeyPlayer():
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date
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
        sys.stdout.write("Reading input file...\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header, separator=self.args.input_separator).graph_load()
        # print(graph.summary())
        # print(graph.vs()["name"])
        # for elem in graph.vs():
        #     print (elem["name"], elem.index, elem.degree())
        # sys.exit(0)

        if hasattr(self.args, 'nodes'):
            if not all(x in graph.vs["name"] for x in self.args.nodes):
                raise WrongArgumentError("One or more nodes you supplied could not be found in the input graph.")
        # init Utils global stuff
        utils = GraphUtils(graph=graph)
        
        if '__implementation' in graph.attributes():
            implementation = graph['__implementation']
        else:
            implementation = CmodeEnum.igraph
            
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
        
        r = pyntacleReporter(graph=graph)

        if self.args.which == 'kp-finder':
            k_size = self.args.k_size
            initial_results = {}
            results = OrderedDict()
            # Greedy optimization
            if self.args.implementation == "greedy":
                report_type = ReportEnum.KP_greedy.name
                kp_runner = gow(graph=graph)
                sys.stdout.write("Using Greedy Optimization Algorithm for searching optimal KP-Set\n")

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {0} using F (kp neg measure)\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    if initial_results[KpnegEnum.F.name] != 1:
                        kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, seed=self.args.seed)
                    else:
                        self.logging.warning("Initial value of F is 1. Skipping search.")
                        results[KpnegEnum.F.name] = [[], 1, 1]
                        
                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {0} using dF (kp neg measure)\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, implementation=implementation)

                    if initial_results[KpnegEnum.dF.name] != 1:
                        kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                    max_distance=self.args.max_distances, seed=self.args.seed,
                                                    implementation=implementation)
                    else:
                        self.logging.warning("Initial value of dF is 1. Skipping search.")
                        results[KpnegEnum.dF.name] = [[], 1, 1]

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using dR (kp pos measure)\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distances, seed=self.args.seed,
                                               implementation=implementation)

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {0} using an MREACH measure of {1} (kp pos measure)\n".format(
                            self.args.k_size, self.args.m_reach))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distances, seed=self.args.seed,
                                               implementation=implementation)

            elif self.args.implementation == "brute-force":
                report_type = ReportEnum.KP_bruteforce.name
                kp_runner = bfw(graph=graph)
                sys.stdout.write("Using Brute Force for searching optimal KP-Set\n")

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using F (kp neg measure)\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    if initial_results[KpnegEnum.F.name] != 1:
                        kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F)

                    else:
                        self.logging.warning("Initial value of F is 1. Skipping search.")
                        results[KpnegEnum.F.name] = [[], 1, 1]

                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using dF (kp neg measure)\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, implementation=implementation)
                    if initial_results[KpnegEnum.dF.name] != 1:
                        kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                    max_distance=self.args.max_distances, implementation=implementation)
                    else:
                        self.logging.warning("Initial value of dF is 1. Skipping search.")
                        results[KpnegEnum.dF.name] = [[], 1, 1]

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {} using dR (kp pos measure)\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distances, implementation=implementation)
                    
                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        "Finding best set of kp-nodes of size {0} using an MREACH measure of {1} (kp pos measure)\n".format(
                            self.args.k_size, self.args.m_reach))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distances, implementation=implementation)

            else:
                sys.stdout.write("Wrong implementation. Please contact pyntacle Developers and sent this error message, along with a command line and a log.\nQuitting.\n")
                sys.exit(1)
            
            sys.stdout.write("Search for the best kp set completed!\n")

            results.update(kp_runner.get_results())
            
            for kp in results.keys(): #ONE OF THE keys represent the algorithm, so no else exit in here
                
                if len(results[kp][0])>1:
                    plurals = ['s', 'are']
                else:
                    plurals = ['', 'is']
                    
                if kp == KpnegEnum.F.name or kp == KpnegEnum.dF.name:
                    # joining initial results with final ones
                    results[kp].append(initial_results[kp])
                    
                    sys.stdout.write(
                        'kp set{0} of size {1} for Key Player Metric {2} {3} {4} with value {5} (starting value is {6})\n'.format(
                            plurals[0], self.args.k_size, kp, plurals[1], results[kp][0], results[kp][1], results[kp][2]))

                elif kp == KpposEnum.dR.name:
                    sys.stdout.write('kp set{0} of size {1} for Key Player Metric {2} {3} {4} with value {5}\n'.format(
                        plurals[0], self.args.k_size, kp, plurals[1], results[kp][0], results[kp][1]))

                elif kp == KpposEnum.mreach.name:
                    results[kp].append(self.args.m_reach)
                    node_perc_reached = ((self.args.k_size + results[kp][1]) / graph.vcount()) * 100
                    if node_perc_reached == 100:
                        node_perc_reached = int(node_perc_reached)
                    else:
                        node_perc_reached = round(node_perc_reached, 2)
                    sys.stdout.write(
                        'kp set{0} of size {1} with a reach of {2} for Key Player Metric {3} {4} {5} with value {6} (reaching the {7}% of nodes)\n'.format(
                            plurals[0], self.args.k_size, self.args.m_reach, kp, plurals[1], results[kp][0],
                            results[kp][1], node_perc_reached))


            if self.args.implementation == "brute-force":
                r.create_report(report_type=ReportEnum.KP_bruteforce, report=results)
            elif self.args.implementation == "greedy":
                r.create_report(report_type=ReportEnum.KP_greedy, report=results)

        # kpinfo: compute kpmetrics for a set of predetermined nodes
        elif self.args.which == 'kp-info':
            report_type = ReportEnum.KPinfo.name
            k_size = len(self.args.nodes)
            initial_results = {}
            kp_runner = kpw(graph=graph)
            results = OrderedDict()

            sys.stdout.write('\nNodes given as input: {}\n'.format(self.args.nodes))
            if self.args.type in (['F', 'neg', 'all']):
                initial_results[KpnegEnum.F.name] = kpp.F(graph)
                kp_runner.run_KPNeg(self.args.nodes, KpnegEnum.F)
            if self.args.type in (['dF', 'neg', 'all']):
                initial_results[KpnegEnum.dF.name] = kpp.dF(graph, implementation=implementation)
                kp_runner.run_KPNeg(self.args.nodes, KpnegEnum.dF, max_distance=self.args.max_distances,
                                    implementation=implementation)

            if self.args.type in (['dR', 'pos', 'all']):
                kp_runner.run_KPPos(self.args.nodes, KpposEnum.dR, max_distance=self.args.max_distances,
                                    implementation=implementation)

            if self.args.type in (['mreach', 'pos', 'all']):
                kp_runner.run_KPPos(self.args.nodes, KpposEnum.mreach, m=self.args.m_reach,
                                    max_distance=self.args.max_distances, implementation=implementation)

            results.update(kp_runner.get_results())

            sys.stdout.write("Keyplayer metric(s) {}:\n".format(self.args.type.upper()))
            for metric in results.keys():

                if metric == KpnegEnum.F.name or metric == KpnegEnum.dF.name:
                    results[metric].append(initial_results[metric])
                    sys.stdout.write(
                        "Starting value for {0} is {1}. Removing nodes {2} gives a {0} value of {3}\n".format(
                            metric, results[metric][2], self.args.nodes, results[metric][1]))

                elif metric == KpposEnum.mreach.name:
                    results[metric].append(self.args.m_reach)
                    perc_node_reached = (results[metric][1] + len(self.args.nodes)) / graph.vcount() * 100
                    sys.stdout.write(
                        "Nodes {0} have an {1} of {2}, Meaning they can reach the {3}% of nodes in {4} steps\n".format(
                            results[metric][0], metric, results[metric][1], perc_node_reached,
                            self.args.m_reach))

                else: #dR case
                    sys.stdout.write(
                        "{0} value for nodes {1} is {2}\n".format(metric, results[metric][0],
                                                                  results[metric][1]))
            r.create_report(report_type=ReportEnum.KPinfo, report=results)

        else:
            log.critical(
                "This should not happen. Please contact pyntacle Developers and send your command line. Quitting\n.")
            sys.exit(1)

        # reporting and plotting part

        sys.stdout.write("Producing report in {} format.\n".format(self.args.report_format))
        report_prefix = "_".join(
            ["pyntacle", self.args.which, graph["name"][0], "kpsize", str(k_size), report_type, "report", self.date])
        report_path = os.path.join(self.args.directory, ".".join([report_prefix, self.args.report_format]))

        if os.path.exists(report_path):
            self.logging.warning(
                "A report with the same name ({}) already exists, overwriting it".format
                (os.path.basename(report_path)))
        
        r.write_report(report_dir=self.args.directory, format=self.args.report_format)
        
        if self.args.save_binary:
            #reproduce octopus behaviour by adding kp information to the graph before saving it
            sys.stdout.write("Saving graph to a Binary file\n")
            #step 1: decidee the type of the implementation

            bf = False
            if self.args.which == "kp-info":
                bin_type = "kpinfo"
            else:
                if self.args.implementation == "brute-force":
                    bin_type = "bruteforce"
                    bf = True

                else:
                    bin_type = "greedy"

            queried_stuff = results.keys()
            if KpnegEnum.F.name in queried_stuff:
                if KpnegEnum.F.name in graph.attributes():
                    sys.stdout.write("{} already present, will overwrite\n".format(KpnegEnum.F.name))
                graph[KpnegEnum.F.name] = results[KpnegEnum.F.name][-1] #initial F value
                k = "_".join([KpnegEnum.F.name, bin_type])

                if bf:
                    AddAttributes(graph).add_graph_attributes(k, {tuple(tuple(x) for x in results[KpnegEnum.F.name][0]): results[KpnegEnum.F.name][1]})
                else:
                    AddAttributes(graph).add_graph_attributes(k, {tuple(results[KpnegEnum.F.name][0]): results[KpnegEnum.F.name][1]})

            if KpnegEnum.dF.name in queried_stuff:
                graph[KpnegEnum.dF.name] = results[KpnegEnum.dF.name][-1]  #initial dF value
                k = "_".join([KpnegEnum.dF.name, bin_type])

                if bf:
                    AddAttributes(graph).add_graph_attributes(k, {tuple(tuple(x) for x in results[KpnegEnum.dF.name][0]): results[KpnegEnum.dF.name][1]})
                else:
                    AddAttributes(graph).add_graph_attributes(k, {tuple(results[KpnegEnum.dF.name][0]):results[KpnegEnum.dF.name][1]})

            if KpposEnum.dR.name in queried_stuff:
                k = "_".join([KpposEnum.dR.name, bin_type])
                if bf:
                    AddAttributes(graph).add_graph_attributes(k, {
                        tuple(tuple(x) for x in results[KpposEnum.dR.name][0]): results[KpposEnum.dR.name][1]})
                else:
                    AddAttributes(graph).add_graph_attributes(k, {tuple(results[KpposEnum.dR.name][0]):results[KpposEnum.dR.name][1]})

            if KpposEnum.mreach.name in queried_stuff:
                k = "_".join([KpposEnum.mreach.name, str(results[KpposEnum.mreach.name][-1]), bin_type])

                if bf:
                    AddAttributes(graph).add_graph_attributes(k, {
                        tuple(tuple(x) for x in results[KpposEnum.mreach.name][0]): results[KpposEnum.mreach.name][1]})
                else:
                    AddAttributes(graph).add_graph_attributes(k, {
                        tuple(results[KpposEnum.mreach.name][0]): results[KpposEnum.mreach.name][1]})
            binary_prefix = "_".join(["pyntacle", graph["name"][0], "kpsize", str(k_size),
                                      report_type, self.date])
            binary_path = os.path.join(self.args.directory, binary_prefix + ".graph")
            PyntacleExporter.Binary(graph, binary_path)

        # generate and output plot
        if not self.args.no_plot and graph.vcount() < 1000:
    
            sys.stdout.write("Generating plots in {} format.\n".format(self.args.plot_format))
            plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    "A directory named \"pyntacle-plots\" already exists, I may overwrite something in there")

            else:
                os.mkdir(plot_dir)

            plot_graph = PlotGraph(graph=graph)

            plot_format = self.args.plot_format
            plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph
            pal = sns.color_palette("Accent", 8).as_hex()
            framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()

            other_nodes_colour = pal[2]
            other_frame_colour = framepal[2]

            other_nodes_size = 25
            # other_nodes_shape = "circle"
            other_edge_width = 1

            for metric in results:
                if self.args.which == 'kp-finder' and self.args.implementation == "brute-force":
                    results[metric][0] = list(set(list(chain(*results[metric][0]))))
                    
                if metric == "F":

                    f_nodes_colour = pal[0]
                    f_frames_colour = framepal[0]
                    # create a list of node colors
                    node_colors = [f_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour
                                    for x in graph.vs()]
                    node_frames = [f_frames_colour if x["name"] in results[metric][0] else other_frame_colour
                                    for x in
                                    graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)

                    # node_shapes = ["square" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                elif metric == "dF":
                    df_nodes_colour = pal[1]
                    df_frames_colour = framepal[1]

                    # create a list of node colors
                    node_colors = [df_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [df_frames_colour if x["name"] in results[metric][0] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)

                    # node_shapes = ["rectangle" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                elif metric == "mreach":
                    mreach_nodes_colour = pal[4]
                    mreach_frames_colour = framepal[4]
                    # create a list of node colors
                    node_colors = [mreach_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour for x in graph.vs()]
                    node_frames = [mreach_frames_colour if x["name"] in results[metric][0] else other_frame_colour for x in graph.vs()]


                    plot_graph.set_node_colors(colors=node_colors)


                    # node_shapes = ["triangle-up" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                elif metric == "dR":
                    dr_nodes_colour = pal[3]
                    dr_frames_colour = framepal[3]

                    # create a list of node colors
                    node_colors = [dr_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [dr_frames_colour if x["name"] in results[metric][0] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)

                    # node_shapes = ["triangle-down" if x["name"] in results[metric][1] else other_nodes_shape for x in
                    #                graph.vs()]
                    #
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                else:
                    self.logging.critical(
                        "This should not happen. Please contact pyntacle developer and send a command line, along with a log. Quitting\n")
                    sys.exit(1)

                node_sizes = [35 if x["name"] in results[metric][0] else other_nodes_size for x in graph.vs()]

                plot_graph.set_node_sizes(sizes=node_sizes)
                # print (other_edge_width)

                #     print (edge.source(), edge.target())
                # add recursive edge widths
                if metric != "mreach":

                    edge_widths = [5 if any(y in results[metric][0] for y in x["node_names"]) else other_edge_width for
                                   x in graph.es()]

                else:
                    if self.args.m_reach > 5:
                        edge_widths = [5 if any(y in results[metric][0] for y in x["node_names"])
                                       else other_edge_width for x in graph.es()]
                        sys.stdout.write("WARNING - you chose a very high value of m-reach, the edge width "
                                         "may be too big, hence it will not be represented dynamically.\n")
                    else:
                        mreach_nodes = results[metric][0]
                        # get node indices of corresponding kpset
                        indices = GraphUtils(graph=graph).get_node_indices(mreach_nodes)
    
                        edge_widths = [other_edge_width] * graph.ecount()  # define a starting list of values
    
                        mreach_width = (self.args.m_reach * 2) + 2  # maxium and minimum boundaries for edge width
                        # print(mreach_width)
    
    
                        memory_indices = indices
                        step_before = indices
    
                        for i in range(1, self.args.m_reach + 1):
                            # print(mreach_width)
                            neighbours = Graph.neighborhood(graph, vertices=indices)
                            # print(neighbours)
    
                            indices = list(chain(*neighbours)) # flat out list of indices
                            # print(indices)
                            remaining_indices = list(set(indices) - set(memory_indices))
    
                            # print(remaining_indices)
                            # print(step_before)
    
                            mreach_edge_ids = []

                            for elem in step_before:
                                for el in remaining_indices:
                                    if Graph.are_connected(graph, elem, el):
                                        mreach_edge_ids.append(graph.get_eid(elem, el))
    
                            # print (mreach_edge_ids)
                            for edge in mreach_edge_ids:
                                edge_widths[edge] = mreach_width
    
                            # finally
                            mreach_width = mreach_width - 2
                            memory_indices = memory_indices + remaining_indices
                            step_before = remaining_indices

                        # sys.exit()

                plot_graph.set_edge_widths(edge_widths)

                plot_graph.set_layouts(self.args.plot_layout)

                plot_path = os.path.join(plot_dir, "_".join(["keyplayer", graph["name"][0], "report", metric, self.date]) + "." + plot_format)
                if os.path.exists(plot_path):
                    sys.stdout.write(
                        "WARNING - A plot with the name ({}) already exists, overwriting it\n".format(
                            os.path.basename(plot_path)))

                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

        elif graph.vcount() >= 1000:
            sys.stdout.write("The graph has too many nodes ({}). Can't draw graph\n".format(graph.vcount()))
        cursor.stop()
        sys.stdout.write("pyntacle Keyplayer completed successfully. Ending\n")
        sys.exit(0)