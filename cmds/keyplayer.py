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
from collections import OrderedDict
from itertools import chain
from igraph import Graph

from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from algorithms.keyplayer import KeyPlayer as kpp


from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import PlotGraph
from cmds.cmds_utils.reporter import PyntacleReporter
from tools.graph_utils import GraphUtils as gu
from tools.enums import ReportEnum, CmodeEnum, KpnegEnum, KpposEnum
from tools.add_attributes import AddAttributes
from internal.graph_load import GraphLoad
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError


class KeyPlayer:
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date
        # Check for pycairo
        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write(pycairo_message)
            self.args.no_plot = True

    def run(self):
        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py keyplayer {kp-finder, kp-info} [options]'")

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
                u"Please specify an input file using the `-i/--input-file` option. Quitting\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        if self.args.no_header:
            header = False
        else:
            header = True

        # Load Graph
        sys.stdout.write(import_start)
        sys.stdout.write(u"Importing graph from file\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header, separator=self.args.input_separator).graph_load()
        # init graph utils class

        utils = gu(graph=graph)

        if hasattr(self.args, "nodes"):
            self.args.nodes = self.args.nodes.split(",")

            if not utils.nodes_in_graph(self.args.nodes):
                sys.stderr.write(
                    "One or more of the specified nodes {} is not present in the graph. Please check your spelling and the presence of empty spaces between node names. Quitting\n".format(self.args.nodes))
                sys.exit(1)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph as you requested ({} nodes, {} edges)\n".format(
                        graph.vcount(), graph.ecount()))
                # reinitialize graph utils class
                utils.set_graph(graph)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting\n")
                sys.exit(1)

            if hasattr(self.args, 'nodes'):
                if not utils.nodes_in_graph(self.args.nodes):
                    sys.stderr.write(
                        "One or more of the specified nodes is not present in the largest graph component. Select a different set or remove this option. Quitting\n")
                    sys.exit(1)

        if hasattr(self.args, "k_size") and self.args.k_size >= graph.vcount():
            sys.stderr.write("The 'k' argument ({}) must be strictly less than the graph size({}). Quitting\n".format(self.args.k_size, graph.vcount()))
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

        #initialize reporter for later usage and plot dimension for later usage
        r = PyntacleReporter(graph=graph)
        initial_results = {}
        results = OrderedDict()

        sys.stdout.write(section_end)
        sys.stdout.write(run_start)

        if self.args.which == 'kp-finder':

            # Greedy optimization
            if self.args.implementation == "greedy":
                report_type = ReportEnum.KP_greedy
                kp_runner = gow(graph=graph)

                sys.stdout.write(u"Using greedy optimization algorithm for searching optimal key player set for the requested key player metrics\n")
                sys.stdout.write(sep_line)

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding optimal set of nodes of size {0} that maximizes F\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, seed=self.args.seed, cmode=implementation)
                    sys.stdout.write(sep_line)
                        
                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding optimal set of nodes of size {0} that maximizes dF\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                max_distance=self.args.max_distance, seed=self.args.seed,
                                                cmode=implementation)
                    sys.stdout.write(sep_line)

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding optimal set of nodes of size {0} that maximizes dR\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distance, seed=self.args.seed,
                                               cmode=implementation)
                    sys.stdout.write(sep_line)

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding optimal set of nodes of size {0} that maximizes the m-reach at distance {1}\n".format(
                            self.args.k_size, self.args.m_reach))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distance, seed=self.args.seed,
                                               cmode=implementation)
                    sys.stdout.write(sep_line)

            elif self.args.implementation == "brute-force":
                report_type = ReportEnum.KP_bruteforce
                kp_runner = bfw(graph=graph)
                sys.stdout.write(u"Using brute-force search algorithm to find the best key player set(s)\n")
                sys.stdout.write(sep_line)

                if self.args.type in (['F', 'neg', 'all']):

                    sys.stdout.write(
                        u"KP-NEG: Finding best set (or sets) of nodes of size {0} that holds the maximum F\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, threads=self.args.threads)
                    sys.stdout.write(sep_line)


                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding best set(s) of nodes of size {0} that holds the maximum dF\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=CmodeEnum.igraph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                max_distance=self.args.max_distance,
                                                cmode=CmodeEnum.igraph, threads=self.args.threads)
                    sys.stdout.write(sep_line)

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding best set(s) of nodes of size {0} that hold the maximum dR\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distance,
                                               cmode=CmodeEnum.igraph, threads=self.args.threads)
                    sys.stdout.write(sep_line)
                    
                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding the best set(s) of nodes of size {0} that maximizes the m-reach at distance {1}\n".format(
                            self.args.k_size, self.args.m_reach))

                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distance,
                                               cmode=CmodeEnum.igraph, threads=self.args.threads)
                    sys.stdout.write(sep_line)

            #get report results
            results.update(kp_runner.get_results())
            sys.stdout.write(section_end)
            sys.stdout.write(summary_start)
            sys.stdout.write(u"Node set size for key player search: {}\n".format(str(self.args.k_size)))

            sys.stdout.write(sep_line)
            for kp in results.keys():

                if len(results[kp][0]) > 1 and self.args.implementation == 'brute-force':
                    plurals = ['s', 'are']
                else:
                    plurals = ['', 'is']

                if results[kp][0][0] is None:  # the case in which there's no solution
                    results[kp][0] = ["None"]

                if self.args.implementation == 'brute-force':
                    list_of_results = "\n".join(['(' + ', '.join(x) + ')' for x in results[kp][0]])
                else:
                    list_of_results = "(" + ", ".join(results[kp][0]) + ")"

                if kp == KpnegEnum.F.name or kp == KpnegEnum.dF.name:
                    # joining initial results with final ones
                    results[kp].append(initial_results[kp])

                    sys.stdout.write(
                        u"Key player set{0} of size {1} for negative key player index {2} {3}:\n{4}\nFinal {2} value: {5}\nStarting graph {2} was {6}\n".format(
                            plurals[0], self.args.k_size, kp, plurals[1], list_of_results, results[kp][1], results[kp][2]))
                    sys.stdout.write(sep_line)

                elif kp == KpposEnum.dR.name:
                    sys.stdout.write(u"Key player set{0} of size {1} for positive key player index {2} {3}:\n{4}\nFinal {2} value: {5}\n".format(
                        plurals[0], self.args.k_size, kp, plurals[1], list_of_results, results[kp][1]))
                    sys.stdout.write(sep_line)

                elif kp == KpposEnum.mreach.name:
                    results[kp].append(self.args.m_reach)
                    node_perc_reached = ((self.args.k_size + results[kp][1]) / graph.vcount()) * 100
                    if node_perc_reached == 100:
                        node_perc_reached = int(node_perc_reached)
                    else:
                        node_perc_reached = round(node_perc_reached, 2)
                    sys.stdout.write(
                        u'Key player set{0} of size {1} for positive key player index m-reach, using at best '
                        '{3} steps {4}:\n{5}\nwith value {6} on {8} (number of nodes reached on total number of nodes)\nThe total percentage of nodes, which '
                        'includes the kp-set, is {7}%\n'
                        .format(
                            plurals[0], self.args.k_size, kp, self.args.m_reach,  plurals[1], list_of_results,
                            results[kp][1], node_perc_reached, graph.vcount()))
                    sys.stdout.write(sep_line)
            sys.stdout.write(section_end)

        # kpinfo: compute kpmetrics for a set of predetermined nodes
        elif self.args.which == 'kp-info':
            report_type = ReportEnum.KP_info
            initial_results = OrderedDict()
            kp_runner = kpw(graph=graph, nodes=self.args.nodes)
            results = OrderedDict()

            sys.stdout.write(u"Nodes given as input: ({})\n".format(', '.join(self.args.nodes)))
            sys.stdout.write(sep_line)

            if self.args.type in (['F', 'neg', 'all']):
                initial_results[KpnegEnum.F.name] = kpp.F(graph)
                kp_runner.run_fragmentation(KpnegEnum.F)
                sys.stdout.write(sep_line)
            if self.args.type in (['dF', 'neg', 'all']):
                initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation, max_distance=self.args.max_distance)
                kp_runner.run_fragmentation(KpnegEnum.dF, max_distance=self.args.max_distance,
                                            cmode=implementation)
                sys.stdout.write(sep_line)

            if self.args.type in (['dR', 'pos', 'all']):
                kp_runner.run_reachability(KpposEnum.dR, max_distance=self.args.max_distance,
                                           cmode=implementation)
                sys.stdout.write(sep_line)

            if self.args.type in (['mreach', 'pos', 'all']):
                kp_runner.run_reachability(KpposEnum.mreach, m=self.args.m_reach,
                                           max_distance=self.args.max_distance, cmode=implementation)
                sys.stdout.write(sep_line)

            sys.stdout.write(section_end)
            results.update(kp_runner.get_results())
            sys.stdout.write(summary_start)
            for metric in results.keys():

                if metric == KpnegEnum.F.name or metric == KpnegEnum.dF.name:
                    results[metric].append(initial_results[metric])
                    sys.stdout.write(
                        u"Removing node set \n({2})\ngives a {0} value of {3}\nStarting graph {0} was {1}\n".format(
                            metric, results[metric][2], ', '.join(self.args.nodes), results[metric][1]))
                    sys.stdout.write(sep_line)

                elif metric == KpposEnum.mreach.name:
                    results[metric].append(self.args.m_reach)
                    perc_node_reached = round((results[metric][1] + len(self.args.nodes)) / graph.vcount() * 100, 3)
                    sys.stdout.write(
                        u"The m-reach of node set:\n({0})\nis {1} on {4} (number of nodes reached on total number of "
                        u"nodes)\nThis means it can reach the {2}% of remaining nodes in the graph nodes in at most {3} steps\n".format(
                            ', '.join(results[metric][0]), results[metric][1], perc_node_reached,
                            self.args.m_reach, graph.vcount()))
                    sys.stdout.write(sep_line)

                else: #dR case
                    sys.stdout.write(
                        "The {0} value for node set:\n({1})\nis {2}\n".format(metric, ', '.join(results[metric][0]),
                                                                  results[metric][1]))
                    sys.stdout.write(sep_line)
            sys.stdout.write(section_end)

        sys.stdout.write(report_start)
        sys.stdout.write("Writing Results\n")
        # check output directory
        if createdir:
            sys.stdout.write(u"WARNING: output directory does not exist, {} will be created\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        # reporting and plotting part
        sys.stdout.write(u"Producing report in {} format\n".format(self.args.report_format))

        r.create_report(report_type=report_type, report=results)
        r.write_report(report_dir=self.args.directory, format=self.args.report_format)
        
        if self.args.save_binary:
            # reproduce octopus behaviour by adding kp information to the graph before saving it
            sys.stdout.write(u"Saving graph to a binary file (ending in .graph)\n")

            for key in results.keys():
                if key == KpposEnum.mreach.name: #replace the mreach distance
                    new_mreach = "_".join([KpposEnum.mreach.name, str(results[KpposEnum.mreach.name][-1])])
                    #create new key
                    results[new_mreach] = results[KpposEnum.mreach.name][:-1] #remove the mreach distance before adding it to the binary file
                    del results[KpposEnum.mreach.name]
                    key = new_mreach

                if self.args.which == "kp-finder":
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
                        sys.stdout.write("WARNING: attribute {} does not point to a dictionary, will overwrite\n".format(attr_name))
                        AddAttributes.add_graph_attributes(graph, attr_name, {attr_key: attr_val})
                    else:
                        if attr_key in graph[attr_name]:
                            sys.stdout.write("WARNING: {} already present in the {} graph attribute, will overwrite\n".format(attr_key, attr_val))
                        graph[attr_name].update({attr_key: attr_val})
                else:
                    AddAttributes.add_graph_attributes(graph, attr_name, {attr_key: attr_val})

            binary_prefix = "_".join([os.path.splitext(os.path.basename(self.args.input_file))[0], self.args.which, self.date])
            binary_path = os.path.join(self.args.directory, binary_prefix + ".graph")
            PyntacleExporter.Binary(graph, binary_path)

        # generate and output plot
        if not self.args.no_plot and graph.vcount() < 1000:
    
            sys.stdout.write(u"Generating network plots in {} format\n".format(self.args.plot_format))
            plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

            if not os.path.isdir(plot_dir):
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

                elif metric == "m-reach":
                    mreach_nodes_colour = pal[4]
                    mreach_frames_colour = framepal[4]
                    # create a list of node colors
                    node_colors = [mreach_nodes_colour if x["name"] in results[metric][0] else other_nodes_colour for x in graph.vs()]
                    node_frames = [mreach_frames_colour if x["name"] in results[metric][0] else other_frame_colour for x in graph.vs()]

                    plot_graph.set_node_colors(colors=node_colors)


                    # node_shapes = ["triangle-up" if x["name"] in results[metric][1] else other_nodes_shape for x in graph.vs()]
                    # plot_graph.set_node_shapes(shapes=node_shapes)

                else: #dR
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
                        sys.stdout.write(u"WARNING: you chose a very high value of m-reach, the edge width "
                                         "may be too big, hence it may not be represented correctly\n")
                    else:
                        mreach_nodes = results[metric][0]
                        # get node indices of corresponding kpset
                        indices = utils.get_node_indices(mreach_nodes)
    
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

                plot_path = os.path.join(plot_dir, "_".join([self.args.which, ["name"][0], metric, self.date]) + "." + plot_format)
                if os.path.exists(plot_path):
                    sys.stdout.write(
                        u"WARNING: a plot with the name ({}) already exists, overwriting it\n".format(
                            os.path.basename(plot_path)))

                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

        elif graph.vcount() >= 1000:
            sys.stdout.write(u"The graph has too many nodes ({}, we plot nodes with a maximum of 1000 nodes). It will not be drawn\n".format(graph.vcount()))

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(section_end)
        sys.stdout.write(u"Pyntacle keyplayer completed successfully\n")

        sys.exit(0)