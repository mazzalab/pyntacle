__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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

from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from algorithms.keyplayer import KeyPlayer as kpp
from itertools import chain
from exceptions.generic_error import Error
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import *
from cmds.cmds_utils.reporter import *
from tools.graph_utils import *
from internal.graph_load import GraphLoad, separator_detect
from tools.enums import ReportEnum, CmodeEnum
from tools.add_attributes import AddAttributes
from colorama import Fore, Style


class KeyPlayer():
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date
        # Check for pycairo
        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write(u"Warning: It seems that the pycairo library is not installed/available. Graph plot(s)"
                             "will not be produced.\n")
            self.args.no_plot = True

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if self.args.m_reach == None and self.args.type in ["pos", "all"]:
            sys.stderr.write(u"m-reach distance must be provided for computing m-reach. Quitting\n")
            sys.exit(1)

        # Checking input file
        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        if self.args.no_header:
            header = False
        else:
            header = True

        # check output directory

        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"Warning: output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        # Parsing optional node list
        if hasattr(self.args, 'nodes'):
            self.args.nodes = self.args.nodes.split(',')
            # self.args.nodes = [str.lower(x) for x in self.args.nodes]

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py keyplayer {kp-finder, kp-info} [options]'")

        self.logging.debug(u"Running Pyntacle keyplayer, with arguments")
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
                sys.stderr.write(u"One or more nodes you supplied could not be found in the input graph.\n")
                sys.exit(1)

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
                    u"Taking the largest component of the input graph as you requested ({} nodes, {} edges)...\n".format(
                        graph.vcount(), graph.ecount()))

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting.\n")
                sys.exit(1)

        # Check provided dimensions' format
        if self.args.plot_dim:  # define custom format
            self.args.plot_dim = self.args.plot_dim.split(",")
    
            for i in range(0, len(self.args.plot_dim)):
                try:
                    self.args.plot_dim[i] = int(self.args.plot_dim[i])

                    if self.args.plot_dim[i] <= 0:
                        raise ValueError
        
                except ValueError:
                    sys.stderr.write(
                        u"Format specified must be a comma-separated list of positive integers (e.g. 1920,1080). Quitting\n")
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
                sys.stdout.write(u"Using greedy optimization algorithm for searching optimal key player set...\n")

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding optimal set of nodes of size {0} that maximizes the F index...\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, seed=self.args.seed)
                    # if initial_results[KpnegEnum.F.name] != 1:
                    #     kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, seed=self.args.seed)
                    # else:
                    #     self.logging.warning("Initial value of F is 1. Skipping search.")
                    #     results[KpnegEnum.F.name] = [[], 1, 1]
                        
                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding optimal set of nodes of size {0} that maximizes the F index...\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                max_distance=self.args.max_distances, seed=self.args.seed,
                                                implementation=implementation)

                    # if initial_results[KpnegEnum.dF.name] != 1:
                    #     kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                    #                                 max_distance=self.args.max_distances, seed=self.args.seed,
                    #                                 implementation=implementation)
                    # else:
                    #     self.logging.warning("Initial value of dF is 1. Skipping search.")
                    #     results[KpnegEnum.dF.name] = [[], 1, 1]

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding optimal set of nodes of size {0} that maximizes the dR index...\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distances, seed=self.args.seed,
                                               implementation = implementation)

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding optimal set of nodes of size {0} that maximizes the nodes reached (m-reach) at a distance {1}...".format(
                            self.args.k_size, self.args.m_reach))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distances, seed=self.args.seed,
                                               implementation=implementation)

            elif self.args.implementation == "brute-force":

                report_type = ReportEnum.KP_bruteforce.name
                kp_runner = bfw(graph=graph)
                sys.stdout.write(u"Using brute-force search algorithm to find the optimal key player set(s)...\n")

                if self.args.type in (['F', 'neg', 'all']):

                    sys.stdout.write(
                        u"KP-NEG: Finding best set(s) of nodes of size {0} that hold the higher value of F among their peers...\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, threads=self.args.threads)
                    # if initial_results[KpnegEnum.F.name] != 1:
                    #     kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, threads=self.args.threads)
                    #
                    # else:
                    #     self.logging.warning("Graph already owns the maximum F value (1.0) Skipping search.")
                    #     results[KpnegEnum.F.name] = [[None], 1, 1]

                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding best set(s) of nodes of size {0} that hold the higher value of dF among their peers...\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=CmodeEnum.igraph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                    max_distance=self.args.max_distances,
                                                    implementation=CmodeEnum.igraph, threads=self.args.threads)
                    # if initial_results[KpnegEnum.dF.name] != 1:
                    # else:
                    #     self.logging.warning("Graph already owns the maximum dF value (1.0) Skipping search.")
                    #     results[KpnegEnum.dF.name] = [[None], 1, 1]

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding best set(s) of nodes of size {0} that hold the higher value of dR among their peers...\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distances,
                                               implementation=CmodeEnum.igraph, threads=self.args.threads)
                    
                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding the best set(s) of nodes of size {0} that maximizes the nodes reached (m-reach) at a distance {1}...".format(
                            self.args.k_size, self.args.m_reach))

                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distances,
                                               implementation=CmodeEnum.igraph, threads=self.args.threads)

            else:
                sys.stdout.write(u"Critcal Error. Please contact Pyntacle developers and Report this issue, along with your command line. Quitting.\n")
                sys.exit(1)

            results.update(kp_runner.get_results())


            sys.stdout.write(Fore.RED + Style.BRIGHT + u"\n### RUN SUMMARY ###\n" + Style.RESET_ALL)
            sys.stdout.write(u"key player set size: {}\n".format(self.args.k_size))
            for kp in results.keys(): #ONE OF THE keys represent the algorithm, so no else exit in here

                if len(results[kp][0]) > 1 and self.args.implementation == 'brute-force':
                    plurals = ['s', 'are']
                else:
                    plurals = ['', 'is']

                if results[kp][0][0] is None:  # the case in which there's no solution
                    results[kp][0] = ["None"]
                
                if self.args.implementation == 'brute-force':
                    list_of_results = ['('+ ', '.join(x) + ')' for x in results[kp][0]]

                else:
                    list_of_results = results[kp][0]
                    
                if kp == KpnegEnum.F.name or kp == KpnegEnum.dF.name:
                    # joining initial results with final ones
                    results[kp].append(initial_results[kp])

                    sys.stdout.write(
                        u'Key player set{0} of size {1} for negative key player index {2} {3} ({4}) with value {5} (Original {2} value  was {6}).\n'.format(
                            plurals[0], self.args.k_size, kp, plurals[1], ', '.join(list_of_results), results[kp][1], results[kp][2]))

                elif kp == KpposEnum.dR.name:
                    sys.stdout.write(u'Key player set{0} of size {1} for positive key player index {2} {3} ({4}) with value {5}.\n'.format(
                        plurals[0], self.args.k_size, kp, plurals[1], ', '.join(list_of_results), results[kp][1]))

                elif kp == KpposEnum.mreach.name:
                    results[kp].append(self.args.m_reach)
                    node_perc_reached = ((self.args.k_size + results[kp][1]) / graph.vcount()) * 100
                    if node_perc_reached == 100:
                        node_perc_reached = int(node_perc_reached)
                    else:
                        node_perc_reached = round(node_perc_reached, 2)
                    sys.stdout.write(
                        u'Key player set{0} of size {1} for positive key player index {2}, using a maximum distance of '
                        '{3} {4} with value {5} (number of nodes reached)\n. The total percentage of nodes, which '
                        'includes the kp-set, is {7}%.\n'
                        .format(
                            plurals[0], self.args.k_size, kp, self.args.m_reach,  plurals[1], ', '.join(list_of_results),
                            results[kp][1], node_perc_reached))
            
            sys.stdout.write(Fore.RED + Style.BRIGHT + u"### END OF SUMMARY ###\n" + Style.RESET_ALL)


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

            sys.stdout.write(u"\nNodes given as input: ({})\n".format(', '.join(self.args.nodes)))
            if self.args.type in (['F', 'neg', 'all']):
                initial_results[KpnegEnum.F.name] = kpp.F(graph)
                kp_runner.run_fragmentation(self.args.nodes, KpnegEnum.F)
            if self.args.type in (['dF', 'neg', 'all']):
                initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                kp_runner.run_fragmentation(self.args.nodes, KpnegEnum.dF, max_distance=self.args.max_distances,
                                            implementation=implementation)

            if self.args.type in (['dR', 'pos', 'all']):
                kp_runner.run_reachability(self.args.nodes, KpposEnum.dR, max_distance=self.args.max_distances,
                                           implementation=implementation)

            if self.args.type in (['mreach', 'pos', 'all']):
                kp_runner.run_reachability(self.args.nodes, KpposEnum.mreach, m=self.args.m_reach,
                                           max_distance=self.args.max_distances, implementation=implementation)

            results.update(kp_runner.get_results())
            sys.stdout.write(Fore.RED + Style.BRIGHT + u"\n### RUN SUMMARY ###\n" + Style.RESET_ALL)
            for metric in results.keys():

                if metric == KpnegEnum.F.name or metric == KpnegEnum.dF.name:
                    results[metric].append(initial_results[metric])
                    sys.stdout.write(
                        u"Starting value for {0} is {1}. Removing nodes:\n({2})\ngives a {0} value of {3}.\n".format(
                            metric, results[metric][2], ', '.join(self.args.nodes), results[metric][1]))

                elif metric == KpposEnum.mreach.name:
                    results[metric].append(self.args.m_reach)
                    perc_node_reached = round((results[metric][1] + len(self.args.nodes)) / graph.vcount() * 100, 3)
                    sys.stdout.write(
                        u"Nodes:\n({0})\nhave a {1} of {2}. This means they can reach the {3}% of nodes in at best {4} steps.\n".format(
                            ', '.join(results[metric][0]), metric, results[metric][1], perc_node_reached,
                            self.args.m_reach))

                else: #dR case
                    sys.stdout.write(
                        "{0} value for node:\n({1}) is {2}\n".format(metric, ', '.join(results[metric][0]),
                                                                  results[metric][1]))
            r.create_report(report_type=ReportEnum.KPinfo, report=results)
            sys.stdout.write(Fore.RED + Style.BRIGHT + "### END OF SUMMARY ###\n" + Style.RESET_ALL)

        else:
            log.critical(
                u"Critical Error. Please contact Pyntacle Developers and report this problem, along with your comman line. Quitting\n.")
            sys.exit(1)

        # reporting and plotting part

        sys.stdout.write(u"Producing report in {} format...\n".format(self.args.report_format))
        report_prefix = "_".join(
            ["pyntacle", self.args.which, graph["name"][0], "kpsize", str(k_size), report_type, "report", self.date])
        report_path = os.path.join(self.args.directory, ".".join([report_prefix, self.args.report_format]))

        if os.path.exists(report_path):
            self.logging.warning(
                u"A report with the same name ({}) already exists, overwriting it.".format
                (os.path.basename(report_path)))
        
        r.write_report(report_dir=self.args.directory, format=self.args.report_format)
        
        if self.args.save_binary:
            #reproduce octopus behaviour by adding kp information to the graph before saving it
            sys.stdout.write(u"Saving graph to a binary file (ending in .graph)...\n")
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
                    sys.stdout.write(u"{} already present in input graph attributes, will overwrite.\n".format(KpnegEnum.F.name))
                graph[KpnegEnum.F.name] = results[KpnegEnum.F.name][-1] #initial F value
                k = "_".join([KpnegEnum.F.name, bin_type])

                if bf:
                    AddAttributes.add_graph_attributes(graph, k, {tuple(tuple(x) for x in results[KpnegEnum.F.name][0]): results[KpnegEnum.F.name][1]})
                else:
                    AddAttributes.add_graph_attributes(graph, k, {tuple(results[KpnegEnum.F.name][0]): results[KpnegEnum.F.name][1]})

            if KpnegEnum.dF.name in queried_stuff:
                graph[KpnegEnum.dF.name] = results[KpnegEnum.dF.name][-1]  #initial dF value
                k = "_".join([KpnegEnum.dF.name, bin_type])

                if bf:
                    AddAttributes.add_graph_attributes(graph, k, {tuple(tuple(x) for x in results[KpnegEnum.dF.name][0]): results[KpnegEnum.dF.name][1]})
                else:
                    AddAttributes.add_graph_attributes(graph, k, {tuple(results[KpnegEnum.dF.name][0]):results[KpnegEnum.dF.name][1]})

            if KpposEnum.dR.name in queried_stuff:
                k = "_".join([KpposEnum.dR.name, bin_type])
                if bf:
                    AddAttributes.add_graph_attributes(graph, k, {
                        tuple(tuple(x) for x in results[KpposEnum.dR.name][0]): results[KpposEnum.dR.name][1]})
                else:
                    AddAttributes.add_graph_attributes(graph, k, {tuple(results[KpposEnum.dR.name][0]):results[KpposEnum.dR.name][1]})

            if KpposEnum.mreach.name in queried_stuff:
                k = "_".join([KpposEnum.mreach.name, str(results[KpposEnum.mreach.name][-1]), bin_type])

                if bf:
                    AddAttributes.add_graph_attributes(graph, k, {
                        tuple(tuple(x) for x in results[KpposEnum.mreach.name][0]): results[KpposEnum.mreach.name][1]})
                else:
                    AddAttributes.add_graph_attributes(graph, k, {
                        tuple(results[KpposEnum.mreach.name][0]): results[KpposEnum.mreach.name][1]})
            binary_prefix = "_".join(["pyntacle", graph["name"][0], "kpsize", str(k_size),
                                      report_type, self.date])
            binary_path = os.path.join(self.args.directory, binary_prefix + ".graph")
            PyntacleExporter.Binary(graph, binary_path)

        # generate and output plot
        if not self.args.no_plot and graph.vcount() < 1000:
    
            sys.stdout.write(u"Generating plots in {} format...\n".format(self.args.plot_format))
            plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    u"A directory named 'pyntacle-plots' already exists, I may overwrite something in there.")

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
                        u"Critical error. Please contact Pyntacle developer and send your command line. Quitting.\n")
                    sys.exit(1)

                node_sizes = [35 if x["name"] in results[metric][0] else other_nodes_size for x in graph.vs()]

                plot_graph.set_node_sizes(sizes=node_sizes)
                # print (other_edge_width)

                #     print (edge.source(), edge.target())
                # add recursive edge widths
                if metric != "mreach":

                    edge_widths = [5 if any(y in results[metric][0] for y in x["adjacent_nodes"]) else other_edge_width for
                                   x in graph.es()]

                else:
                    if self.args.m_reach > 5:
                        edge_widths = [5 if any(y in results[metric][0] for y in x["adjacent_nodes"])
                                       else other_edge_width for x in graph.es()]
                        sys.stdout.write(u"Warning: you chose a very high value of m-reach, the edge width "
                                         "may be too big, hence it may not be represented correctly.\n")
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
                        u"Warning: a plot with the name ({}) already exists, overwriting it.\n".format(
                            os.path.basename(plot_path)))

                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

        elif graph.vcount() >= 1000:
            sys.stdout.write(u"The graph has too many nodes ({}, we plot nodes with a maximum of 1000 nodes). It will not be drawn.\n".format(graph.vcount()))
        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(u"Pyntacle keyplayer completed successfully.\n")
        sys.exit(0)