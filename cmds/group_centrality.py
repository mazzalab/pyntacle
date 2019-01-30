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


from config import *
import random
import importlib
from colorama import Fore, Style
from collections import OrderedDict
from itertools import chain
from internal.graph_load import GraphLoad
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as ipw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from tools.enums import ReportEnum, GroupDistanceEnum, GroupCentralityEnum, CmodeEnum
from tools.add_attributes import AddAttributes
from tools.graph_utils import GraphUtils as gu
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError
from exceptions.missing_attribute_error import MissingAttributeError
from cmds.cmds_utils.plotter import PlotGraph
from cmds.cmds_utils.reporter import PyntacleReporter

class GroupCentrality():
    def __init__(self, args):
        self.logging = log
        self.args = None
        self.args = args
        self.date = runtime_date

        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write(u"Warning: It seems that the pycairo library is not installed/available. Graph plot(s)"
                             "will not be produced.\n")
            self.args.no_plot = True

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        # if self.args.type in ["all", "closeness"]:
        #     if self.args.group_distances is None:
        #         sys.stderr.write(u"Group distance must be specified for group closeness using the `-D --group-distance` argument. Quitting.\n")
        #         sys.exit(1)
        #         sys.exit(1)

        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        #verify that group distance is set if group closeness is specified
        distancedict = {"min": GroupDistanceEnum.minimum, "max":GroupDistanceEnum.maximum, "mean": GroupDistanceEnum.mean}
        if self.args.type in ["all", "closeness"]:
            if self.args.group_distance is None:
                sys.stdout.write(
                    "'--group-distance/-D parameter must be specified for group closeness. It must be one of the followings: {}'. Quitting.\n".format(
                        ",".join(distancedict.keys())))
                sys.exit(1)
            if self.args.group_distance not in distancedict.keys():
                sys.stdout.write("'--group-distance/-D parameter must be one of the followings: {}'. Quitting.\n".format(",".join(distancedict.keys())))
                sys.exit(1)
            else:
                group_distance = distancedict[self.args.group_distance]

        # Parsing optional node list
        if hasattr(self.args, 'nodes'):
            self.args.nodes = self.args.nodes.split(',')
            # self.args.nodes = [str.lower(x) for x in self.args.nodes]

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py groupcentrality {gr-finder, gr-info} [options]'")

        if self.args.no_header:
            header = False
        else:
            header = True

        sys.stdout.write(u"Importing graph from file...\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header,
                          separator=self.args.input_separator).graph_load()

        # init graph utils class
        utils = gu(graph=graph)

        if hasattr(self.args, 'nodes'):

            try:
                utils.nodes_in_graph(self.args.nodes)

            except:
                sys.stderr.write("One or more of the specified nodes is not present in the graph. Please check your spelling and the presence of empty spaces in between node names. Quitting.\n")
                sys.exit(1)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph as you requested ({} nodes, {} edges)...\n".format(
                        graph.vcount(), graph.ecount()))
                #reinitialize graph utils class
                utils.set_graph(graph)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting.\n")
                sys.exit(1)

            #check that the nodes are in the largest component
            if self.args.nodes is not None:

                try:
                    utils.nodes_in_graph(self.args.nodes)

                except:
                    sys.stderr.write("One or more of the specified nodes is not present in the largest graph component. Select a different set or remove this option. Quitting.\n")
                    sys.exit(1)

        if 'implementation' in graph.attributes():
            implementation = graph['implementation']
        else:
            implementation = CmodeEnum.igraph

        # check that output directory is properly set
        createdir = False
        if not os.path.isdir(self.args.directory):
            createdir = True

        # control plot dimensions
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
            plot_size = (800, 600)

            if graph.vcount() > 150:
                plot_size = (1600, 1600)

        # initialize reporter for later usage and plot dimension for later usage
        r = PyntacleReporter(graph=graph)
        results = OrderedDict()

        if self.args.which == "gr-finder":
            k_size = self.args.k_size

            # Greedy optimization
            if self.args.implementation == "greedy":
                if self.args.seed:
                    random.seed(self.args.seed)

                report_type = ReportEnum.GR_greedy
                go_runner = gow(graph=graph)
                sys.stdout.write(u"Using greedy optimization algorithm for searching optimal set of nodes using group centrality metrics...\n")

                if self.args.type in (["all", "degree"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the Group degree...\n".format(
                            self.args.k_size))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_degree,
                                                  seed=self.args.seed,
                                                  cmode=implementation)

                if self.args.type in (["all", "betweenness"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the group betweenness...\n".format(
                            self.args.k_size))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_betweenness,
                                                  seed=self.args.seed,
                                                  cmode=implementation)

                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the group closeness using the {1} distance from the node set...\n".format(
                            self.args.k_size, group_distance.name))


                    go_runner.run_groupcentrality(k = self.args.k_size,gr_type=GroupCentralityEnum.group_closeness, seed=self.args.seed, cmode=implementation ,distance=group_distance)

                results.update(go_runner.get_results())

            #bruteforce implementation
            elif self.args.implementation == "brute-force":

                if self.args.threads > 1:
                    plural = "s"
                else:
                    plural = ""

                report_type = ReportEnum.GR_bruteforce
                bf_runner = bfw(graph=graph)
                sys.stdout.write(u"Using brute-force search algorithm to find the best set(s) that optimize group centrality metrics...\n")

                if self.args.type in (["all", "degree"]):
                    sys.stdout.write(
                        u"Finding the best set(s) of nodes of size {0} that maximizes the group degree using {1} thread{2}...\n".format(
                            self.args.k_size, group_distance.name, self.args.threads, plural))
                    bf_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_degree,
                                                  cmode=implementation, threads=self.args.threads)

                if self.args.type in (["all", "betweenness"]):
                    sys.stdout.write(
                        u"Finding the best set(s) of nodes of size {0} that maximizes the group betweenness using {1} thread{2}...\n".format(
                            self.args.k_size, group_distance.name, self.args.threads, plural))

                    bf_runner.run_groupcentrality(k = self.args.k_size, gr_type=GroupCentralityEnum.group_betweenness, cmode=implementation,threads=self.args.threads)

                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Finding the best set(s) of nodes of size {0} that maximizes the group closeness using the {1} distance from the node set and {2} thread{3}...\n".format(
                            self.args.k_size, group_distance.name, self.args.threads, plural))
                    bf_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_closeness, cmode=implementation, threads=self.args.threads, distance=group_distance)

                results.update(bf_runner.get_results())

            #shell output report part
            sys.stdout.write(Fore.RED + Style.BRIGHT + u"\n### RUN SUMMARY ###\n" + Style.RESET_ALL)
            sys.stdout.write(u"Node set size for group centrality search: {}\n".format(str(self.args.k_size)))
            for kk in results.keys():

                if len(results[kk][0]) > 1 and self.args.implementation == 'brute-force':
                    plurals = ['s', 'are']
                else:
                    plurals = ['', 'is']

                if results[kk][0][0] is None:  # the case in which there's no solution
                    results[kk][0] = ["None"]

                if self.args.implementation == 'brute-force':
                    list_of_results = ['(' + ', '.join(x) + ')' for x in results[kk][0]]

                else:
                    list_of_results = results[kk][0]

                if kk == GroupCentralityEnum.group_degree.name:
                    sys.stdout.write(
                        u'Node set{0} of size {1} for group degree centrality {2} ({3})\nwith value {4}\n'.format(
                            plurals[0], self.args.k_size, plurals[1], ', '.join(list_of_results), results[kk][1]))

                elif kk == GroupCentralityEnum.group_betweenness.name:
                    sys.stdout.write(u'Node set{0} of size {1} for group betweenness centrality {2} ({3})\nwith value {4}\n'.format(
                        plurals[0], self.args.k_size, plurals[1], ', '.join(list_of_results), results[kk][1]))

                elif kk.startswith(GroupCentralityEnum.group_closeness.name):
                    sys.stdout.write(u'Node set{0} of size {1} for group closeness centrality {2} ({3})\nwith value {4}.\nThe {5} distance was considered for computing closeness.\n'.format(
                        plurals[0], self.args.k_size, plurals[1], ',\n'.join(list_of_results), results[kk][1], group_distance.name))

            sys.stdout.write(Fore.RED + Style.BRIGHT + u"### END OF SUMMARY ###\n" + Style.RESET_ALL)

            #prepare report
            report_prefix = "_".join(
                ["pyntacle", self.args.which, graph["name"][0], "k", str(k_size), report_type.name, "report",
                 self.date])

        elif self.args.which == "gr-info":
            report_type = ReportEnum.GR_info
            sys.stdout.write("Computing group centrality for the input node set...\n")
            sys.stdout.write(u"Nodes given as input: ({})\n".format(', '.join(self.args.nodes)))

            grinfo_runner = ipw(graph=graph, nodes=self.args.nodes)

            if self.args.type in (["degree", "all"]):
                grinfo_runner.run_groupcentrality(gr_type=GroupCentralityEnum.group_degree, cmode=implementation)

            if self.args.type in (["betweenness", "all"]):
                grinfo_runner.run_groupcentrality(gr_type=GroupCentralityEnum.group_betweenness, cmode=implementation)

            if self.args.type in (["closeness", "all"]):
                grinfo_runner.run_groupcentrality(gr_type=GroupCentralityEnum.group_closeness, cmode=implementation, gr_distance=group_distance)

            results.update(grinfo_runner.get_results())

            sys.stdout.write(Fore.RED + Style.BRIGHT + u"\n### RUN SUMMARY ###\n" + Style.RESET_ALL)

            for metric in results.keys():

                if metric == GroupCentralityEnum.group_degree.name:
                    sys.stdout.write("The group degree value for the input node set:\n\t({0})\nis {1}\n".format(', '.join(results[metric][0]),
                                                                 results[metric][1]))

                if metric == GroupCentralityEnum.group_betweenness.name:
                    sys.stdout.write(
                        "The group betweenness value for the input node set:\n\t({0})\nis {1}\n".format(', '.join(results[metric][0]),
                                                                                        results[metric][1]))

                if metric.startswith(GroupCentralityEnum.group_closeness.name):
                    sys.stdout.write(
                        "The group closeness value for the input node set:\n\t({0})\nis {1}. The measure was computed using a {2} group distance between the set and the rest of the graph.\n".format(', '.join(results[metric][0]),
                                                                                      results[metric][1], group_distance.name))

            sys.stdout.write(Fore.RED + Style.BRIGHT + "### END OF SUMMARY ###\n" + Style.RESET_ALL)

            report_prefix = "_".join(
                ["pyntacle", self.args.which, graph["name"][0], report_type.name, "report", self.date])

        else:
            sys.stdout.write(
                u"Critical Error. Please contact Pyntacle developers and report this issue, along with your command line. Quitting.\n")
            sys.exit(1)

        #output part#####

        if createdir:
            sys.stdout.write(u"Warning: output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        if self.args.save_binary:
            # reproduce octopus behaviour by adding kp information to the graph before saving it
            sys.stdout.write(u"Saving graph to a binary file (ending in .graph) in the specified output directory...\n")

            for key in results.keys():
                if self.args.which == "gr-finder":
                    if self.args.implementation == "brute-force":
                        suffix = "bruteforce"
                        attr_key = tuple(tuple(sorted(tuple(x))) for x in results[key][0])

                    else:
                        suffix = "greedy"
                        attr_key = tuple(sorted(tuple(results[key][0])))

                else:
                    suffix = "info"
                    attr_key = tuple(sorted(tuple(results[key][0])))

                attr_name = "_".join([key, suffix])
                attr_val = results[key][1]

                if attr_name in graph.attributes():
                    if not isinstance(graph[attr_name], dict):
                        sys.stdout.write("Warning: attribute {} does not point to a dictionary, will overwrite.\n".format(attr_name))
                        AddAttributes.add_graph_attributes(graph, attr_name, {attr_key: attr_val})
                    else:
                        if attr_key in graph[attr_name]:
                            sys.stdout.write("Warning: {} already present in the {} graph attribute, will overwrite...\n".format(attr_key, attr_val))
                        graph[attr_name].update({attr_key: attr_val})
                else:
                    AddAttributes.add_graph_attributes(graph, attr_name, {attr_key: attr_val})

            binary_prefix = "_".join([os.path.splitext(os.path.basename(self.args.input_file))[0], self.args.which, self.date])
            binary_path = os.path.join(self.args.directory, binary_prefix + ".graph")
            PyntacleExporter.Binary(graph, binary_path)

        sys.stdout.write(u"Producing report in {} format...\n".format(self.args.report_format))

        report_path = os.path.join(self.args.directory, ".".join([report_prefix, self.args.report_format]))

        if os.path.exists(report_path):
            self.logging.warning(
                u"A report with the same name ({}) already exists, overwriting it.".format
                (os.path.basename(report_path)))

        r.create_report(report_type=report_type, report=results)
        r.write_report(report_dir=self.args.directory, format=self.args.report_format)

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
                if self.args.which == 'gr-finder' and self.args.implementation == "brute-force":
                    results[metric][0] = list(set(list(chain(*results[metric][0]))))

                if metric.startswith(GroupCentralityEnum.group_closeness.name):
                    cl_nodes_colour = pal[5]
                    cl_frames_colour = framepal[5]
                    # create a list of node colors
                    node_colors = [cl_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour
                                   for x in graph.vs()]
                    node_frames = [cl_frames_colour if x["name"] in results[metric][0] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)

                elif metric == GroupCentralityEnum.group_degree:
                    dg_nodes_colour = pal[4]
                    dg_frames_colour = framepal[4]

                    # create a list of node colors
                    node_colors = [dg_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [dg_frames_colour if x["name"] in results[metric][0] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)

                else: #group betweenness
                    bt_nodes_colour = pal[6]
                    bt_frames_colour = framepal[6]

                    # create a list of node colors
                    node_colors = [bt_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [bt_frames_colour if x["name"] in results[metric][0] else other_frame_colour
                                   for x in
                                   graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)

                node_sizes = [35 if x["name"] in results[metric][0] else other_nodes_size for x in graph.vs()]
                plot_graph.set_node_sizes(sizes=node_sizes)

                edge_widths = [5 if any(y in results[metric][0] for y in x["adjacent_nodes"]) else other_edge_width for
                               x in graph.es()]

                plot_graph.set_edge_widths(edge_widths)
                plot_graph.set_layouts(self.args.plot_layout)

                plot_path = os.path.join(plot_dir, "_".join(
                    [self.args.which, graph["name"][0], metric, self.date]) + "." + plot_format)
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


        sys.stdout.write(u"Pyntacle groupcentrality completed successfully. Ending.\n")
        sys.exit(0)
