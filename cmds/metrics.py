__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """
from config import *
from collections import OrderedDict
from algorithms.shortest_path import ShortestPath
from algorithms.global_topology import GlobalTopology
from algorithms.local_topology import LocalTopology
from algorithms.sparseness import *
from io_stream.exporter import PyntacleExporter
from io_stream.import_attributes import ImportAttributes
from cmds.cmds_utils.reporter import PyntacleReporter
from tools.graph_utils import GraphUtils as gu
from tools.add_attributes import AddAttributes
from tools.enums import *
from internal.graph_load import GraphLoad,separator_detect
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError

class Metrics:
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py metrics {local, global} [options]'")

        # - DEPRECATED- Check for pycairo
        # if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
        #     sys.stdout.write(pycairo_message)
        #     self.args.no_plot = True

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()
        if self.args.no_header:
            header = False
        else:
            header = True

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py metrics {global, local} [options]")

        # Checking input file
        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            self.logging.error(u"Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit(1)

        if hasattr(self.args, "damping_factor"):
            if self.args.damping_factor is not None:
                if self.args.damping_factor < 0.0 or self.args.damping_factor > 1.0:
                    sys.stderr.write(u"Damping factor must be between 0 and 1. Quitting\n")
                    sys.exit(1)

        self.logging.debug(u'Running Pyntacle metrics, with arguments ')
        self.logging.debug(self.args)

        # Load Graph
        sys.stdout.write(import_start)
        sys.stdout.write(u"Importing graph from file\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header, separator=self.args.input_separator).graph_load()
        # init Utils global stuff
        utils = gu(graph=graph)

        if hasattr(self.args, "nodes"):
            if self.args.nodes is not None:

                self.args.nodes = self.args.nodes.split(",")

                if not utils.nodes_in_graph(self.args.nodes):
                    sys.stderr.write(
                        "One or more of the specified nodes is not present in the graph. Please check your spelling and the presence of empty spaces in between node names. Quitting\n")
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

            if self.args.nodes is not None:
                if not utils.nodes_in_graph(self.args.nodes):
                    sys.stderr.write(
                        "One or more of the specified nodes is not present in the largest graph component. Select a different set or remove this option. Quitting\n")
                    sys.exit(1)

        # Decide implementation
        if 'implementation' in graph.attributes():
            implementation = graph['implementation']
        else:
            implementation = CmodeEnum.igraph

        if hasattr(self.args, "nodes"):
            if self.args.weights is not None:
                sys.stdout.write(u"Adding edge weights from file {}\n".format(self.args.weights))
                if not os.path.exists(self.args.weights):
                    sys.stderr.write(
                        u"Weights file {} does not exist. Is the path correct?\n".format(self.args.weights))
                    sys.exit(1)

                ImportAttributes.import_edge_attributes(graph, self.args.weights,
                                                        sep=separator_detect(self.args.weights),
                                                        mode=self.args.weights_format)
                try:
                    weights = [float(x) if x is not None else 1.0 for x in graph.es()["weights"]]

                except KeyError:
                    sys.stderr.write(u"The attribute file does not contain a column named 'weights'."
                                     "Quitting\n")
                    sys.exit(1)
            else:
                weights = None

        # LEGACY - OLD PLOTTER
        # Check provided dimensions' format
        # if hasattr(self.args.plot_dim, "plot_dim"):
        #     # define custom format
        #     self.args.plot_dim = self.args.plot_dim.split(",")
        #
        #     if len(self.args.plot_dim) != 2:
        #         sys.stderr.write(
        #             u"Format specified must be a comma-separated list of values(e.g. 1920,1080). Quitting\n")
        #
        #     for i in range(0, len(self.args.plot_dim)):
        #         try:
        #             self.args.plot_dim[i] = int(self.args.plot_dim[i])
        #
        #         except ValueError:
        #             sys.stderr.write(
        #                 u"Format specified must be a comma-separated list of values(e.g. 1920,1080). Quitting\n")
        #             sys.exit(1)
        #
        #         if self.args.plot_dim[i] <= 0:
        #             sys.stderr.write(
        #                 u"Format specified must be a comma-separated list of values(e.g. 1920,1080). Quitting\n")
        #             sys.exit(1)
        #
        #     plot_size = tuple(self.args.plot_dim)
        #
        # else:
        #     # generate different formats according to graph size
        #     if graph.vcount() <= 150:
        #         plot_size = (800, 800)
        #
        #     else:
        #         plot_size = (1600, 1600)

        sys.stdout.write(section_end) #end report
        sys.stdout.write(run_start) #start run

        if self.args.which == "local":

            if self.args.nodes is not None:
                sys.stdout.write(u"Computing local metrics for nodes {}\n".format(', '.join(self.args.nodes)))
                nodes_list = self.args.nodes

            else:
                sys.stdout.write(u"Computing local metrics for all nodes in the graph\n")
                nodes_list = None

            local_attributes_dict = OrderedDict({LocalAttributeEnum.degree.name: LocalTopology.degree(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.clustering_coefficient.name: LocalTopology.clustering_coefficient(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.betweenness.name: LocalTopology.betweenness(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.closeness.name: LocalTopology.closeness(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.radiality.name: LocalTopology.radiality(graph=graph, nodes=nodes_list, cmode=implementation),
                                                 LocalAttributeEnum.radiality_reach.name: LocalTopology.radiality_reach(graph=graph, nodes=nodes_list, cmode=implementation),
                                                 LocalAttributeEnum.eccentricity.name: LocalTopology.eccentricity(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.eigenvector.name : LocalTopology.eigenvector(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.pagerank.name: LocalTopology.pagerank(graph=graph, nodes=nodes_list, weights=weights, damping=self.args.damping_factor)})

            if self.args.nodes:
                local_attributes_dict["nodes"] = self.args.nodes

            sys.stdout.write("Local metrics computed\n")
            sys.stdout.write(section_end)
            sys.stdout.write(report_start)
            # check output directory

            if not os.path.isdir(self.args.directory):
                sys.stdout.write(u"WARNING: Output directory does not exist; {} will be created\n".format(
                    os.path.abspath(self.args.directory)))
                os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

            sys.stdout.write(u"Writing report in {} format\n".format(self.args.report_format))

            graph_copy = graph.copy() #work on the copy so that savebinary and the plotting doesn't conflict
            r = PyntacleReporter(graph=graph_copy) #reporter-plotter
            r.create_report(ReportEnum.Local, local_attributes_dict)
            r.write_report(report_dir=self.args.directory, format=self.args.report_format)

            if not self.args.no_plot and graph.vcount() < 5000:
                #todo mauro: ci sono due degree: ho rinominato il degree che calcoliamo noi come "Degree (Pyntacle). Vedi tu se ti piace o no
                #todo mauro la closeness è ancora buggata, ma i valori ci sono tutti!
                local_attributes_dict_pyink = OrderedDict()

                #replaces "_" with " " in local attributes_dict and capitalize the first letter
                for elem in local_attributes_dict:

                    if elem == "nodes":
                        local_attributes_dict_pyink[elem] = local_attributes_dict[elem]

                    elif elem == "degree":
                        local_attributes_dict_pyink["Degree (Pyntacle)"] = local_attributes_dict[elem]

                    else: #don't change the "nodes" key (this is unnecessary as nodes is not used as an attribute
                        newelem = elem.replace("_", " ")
                        newelem = newelem.capitalize()
                        local_attributes_dict_pyink[newelem] = local_attributes_dict[elem]

                suffix = "_".join(graph_copy["name"])
                sys.stdout.write(u"Plotting network in {} directory\n".format(self.args.directory))

                #add the metrics to the graph_copy so they are added shown in the filters subfield
                sys.stdout.write("Adding local indices to the graph to view them in PyntacleInk. (in the \"Filters\" subpanel)\n")

                if self.args.nodes:
                    nodes_info = local_attributes_dict_pyink.get("nodes")
                else:
                    nodes_info = graph.vs()["name"]

                for attr in local_attributes_dict_pyink:
                    if attr != "nodes": #available only if self.args.nodes is present in cmd args
                        AddAttributes.add_node_attribute(graph_copy, attr_name=attr, attr_list=local_attributes_dict_pyink[attr], nodes=nodes_info)

                r.pyntacleink_report(report_dir=self.args.directory, report_dict=None, suffix=suffix) #add it to the report

            elif graph.vcount() >= 5000:
                sys.stdout.write(
                    u"The graph has too many nodes ({}). Pyntacle allows plotting for network with N < 5000. No visual representation will be produced\n".format(
                        graph.vcount()))

            else:
                sys.stdout.write(pyntacleink_skip_msg)

            # - LEGACY - OLD PLOTTER -
            # if not self.args.no_plot and graph.vcount() < 1000:
            #
            #     sys.stdout.write(u"Generating plots in {} format\n".format(self.args.plot_format))
            #
            #     # generates plot directory
            #     plot_dir = os.path.join(self.args.directory, "pyntacle-plots")
            #
            #     if not os.path.isdir(plot_dir):
            #         os.makedirs(plot_dir, exist_ok=True)
            #
            #
            #     plot_graph = PlotGraph(graph=graph)
            #     plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph
            #
            #     pal = sns.color_palette("Accent", 8).as_hex()
            #     framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()
            #
            #     other_nodes_colour = pal[2]
            #     other_frame_colour = framepal[2]
            #     other_nodes_size = 25
            #
            #     if self.args.nodes:  # make node selected of a different colour and bigger than the other ones, so they can be visualized
            #         sys.stdout.write(u"Highlighting nodes ({}) in plot\n".format(', '.join(nodes_list)))
            #         selected_nodes_colour = pal[0]
            #         selected_nodes_frames = framepal[0]
            #
            #         node_colors = [selected_nodes_colour if x["name"] in nodes_list else other_nodes_colour
            #                         for x in
            #                         graph.vs()]
            #         node_frames = [selected_nodes_frames if x["name"] in nodes_list else other_frame_colour
            #                         for x in
            #                         graph.vs()]
            #
            #         #print(node_colors)
            #
            #         plot_graph.set_node_colors(colors=node_colors)
            #
            #         node_sizes = [45 if x["name"] in nodes_list else other_nodes_size for x in graph.vs()]
            #         plot_graph.set_node_sizes(sizes=node_sizes)
            #
            #     else:
            #         # sys.stdout.write("Plotting network\n".format(nodes_list))
            #         node_colors = [other_nodes_colour] * graph.vcount()
            #         node_frames = [other_frame_colour] * graph.vcount()
            #         plot_graph.set_node_colors(colors=node_colors)
            #
            #         node_sizes = [other_nodes_size] * graph.vcount()
            #         plot_graph.set_node_sizes(sizes=node_sizes)
            #
            #     # define layout
            #     plot_graph.set_layouts(self.args.plot_layout)
            #
            #     plot_path = os.path.join(plot_dir, ".".join(["_".join(
            #         [graph["name"][0],
            #          self.date]), self.args.plot_format]))
            #     plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
            #                           keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)
            #
            # elif not self.args.no_plot and graph.vcount() >= 1000:
            #     sys.stdout.write(u"The graph has too many nodes ({}). It will not be drawn\n".format(graph.vcount()))

        elif self.args.which == "global":
            
            sys.stdout.write(u"Computing global metrics\n")
            global_attributes_dict = OrderedDict({GlobalAttributeEnum.average_shortest_path_length.name: ShortestPath.average_global_shortest_path_length(graph=graph),
                                                  GlobalAttributeEnum.median_shortest_path_length.name: ShortestPath.median_global_shortest_path_length(graph=graph),
                                                  GlobalAttributeEnum.diameter.name: GlobalTopology.diameter(graph=graph),
                                                  GlobalAttributeEnum.components.name: GlobalTopology.components(graph=graph),
                                                  GlobalAttributeEnum.radius.name: GlobalTopology.radius(graph=graph),
                                                  GlobalAttributeEnum.density.name: GlobalTopology.density(graph=graph),
                                                  GlobalAttributeEnum.pi.name: GlobalTopology.pi(graph=graph),
                                                  GlobalAttributeEnum.average_clustering_coefficient.name: GlobalTopology.average_clustering_coefficient(graph=graph),
                                                  GlobalAttributeEnum.weighted_clustering_coefficient.name: GlobalTopology.weighted_clustering_coefficient(graph=graph),
                                                  GlobalAttributeEnum.average_degree.name: GlobalTopology.average_degree(graph=graph),
                                                  GlobalAttributeEnum.average_closeness.name: GlobalTopology.average_closeness(graph=graph),
                                                  GlobalAttributeEnum.average_eccentricity.name: GlobalTopology.average_eccentricity(graph=graph),
                                                  GlobalAttributeEnum.average_radiality.name: GlobalTopology.average_radiality(graph=graph, cmode=implementation),
                                                  GlobalAttributeEnum.average_radiality_reach.name: GlobalTopology.average_radiality_reach(graph=graph, cmode=implementation),
                                                  GlobalAttributeEnum.completeness_naive.name: Sparseness.completeness_naive(graph=graph),
                                                  GlobalAttributeEnum.completeness.name: Sparseness.completeness(graph=graph),
                                                  GlobalAttributeEnum.compactness.name: Sparseness.compactness(graph=graph)
                                                  })

            sys.stdout.write(u"Global metrics computed\n")
            sys.stdout.write(section_end)
            sys.stdout.write(report_start)
            sys.stdout.write(u"Producing global metrics report for the input graph\n")

            r = PyntacleReporter(graph=graph)  # init reporter
            r.create_report(ReportEnum.Global, global_attributes_dict)
            r.write_report(report_dir=self.args.directory, format=self.args.report_format)

            if self.args.no_nodes:  # create an additional report for the graph minus the selected nodes
                if len(self.args.no_nodes) > 1:
                    plural = "s"
                else:
                    plural = ""
                
                sys.stdout.write(u"Removing node{}:\n\t{}\nfrom input graph and computing Global Metrics\n".format(plural, self.args.no_nodes))
                nodes_list = self.args.no_nodes.split(",")

                # this will be useful when producing the two global topology plots, one for the global graph and the other one fo all nodes
                nodes_list = [x.replace(" ", "") for x in nodes_list]
                index_list = utils.get_node_indices(nodes=nodes_list)

                # delete vertices
                graph_nonodes = graph.copy()
                graph_nonodes.delete_vertices(index_list) #remove target nodes

                global_attributes_dict_nonodes = OrderedDict({
                    'Removed nodes': ','.join(nodes_list),
                    GlobalAttributeEnum.average_shortest_path_length.name: ShortestPath.average_global_shortest_path_length(
                        graph=graph_nonodes),
                    GlobalAttributeEnum.median_shortest_path_length.name: ShortestPath.median_global_shortest_path_length(
                        graph=graph_nonodes),
                    GlobalAttributeEnum.diameter.name: GlobalTopology.diameter(graph=graph_nonodes),
                    GlobalAttributeEnum.components.name: GlobalTopology.components(graph=graph_nonodes),
                    GlobalAttributeEnum.radius.name: GlobalTopology.radius(graph=graph_nonodes),
                    GlobalAttributeEnum.density.name: GlobalTopology.density(graph=graph_nonodes),
                    GlobalAttributeEnum.pi.name: GlobalTopology.pi(graph=graph_nonodes),
                    GlobalAttributeEnum.average_clustering_coefficient.name: GlobalTopology.average_clustering_coefficient(
                        graph=graph_nonodes),
                    GlobalAttributeEnum.weighted_clustering_coefficient.name: GlobalTopology.weighted_clustering_coefficient(
                        graph=graph_nonodes),
                    GlobalAttributeEnum.average_degree.name: GlobalTopology.average_degree(graph=graph_nonodes),
                    GlobalAttributeEnum.average_closeness.name: GlobalTopology.average_closeness(graph=graph_nonodes),
                    GlobalAttributeEnum.average_eccentricity.name: GlobalTopology.average_eccentricity(graph=graph_nonodes),
                    GlobalAttributeEnum.average_radiality.name: GlobalTopology.average_radiality(graph=graph_nonodes,
                                                                                                 cmode=implementation),
                    GlobalAttributeEnum.average_radiality_reach.name: GlobalTopology.average_radiality_reach(
                        graph=graph_nonodes, cmode=implementation),
                    GlobalAttributeEnum.completeness_naive.name: Sparseness.completeness_naive(graph=graph_nonodes),
                    GlobalAttributeEnum.completeness.name: Sparseness.completeness(graph=graph_nonodes),
                    GlobalAttributeEnum.compactness.name: Sparseness.compactness(graph=graph_nonodes),
                })

                sys.stdout.write(u"Producing global metrics report for the input graph after node removal\n")
                graph_nonodes["name"][0] += '_no_nodes'
                r_nonodes = PyntacleReporter(graph=graph_nonodes)  # init reporter
                r_nonodes.create_report(ReportEnum.Global, global_attributes_dict_nonodes)
                r_nonodes.write_report(report_dir=self.args.directory, format=self.args.report_format)

            if not self.args.no_plot and graph.vcount() < 5000:
                if self.args.no_nodes:
                    sys.stdout.write(u"Plotting network (with and without nodes) in {} directory\n".format(self.args.directory))
                else:
                    sys.stdout.write(
                        u"Plotting network in {} directory\n".format(self.args.directory))

                suffix = "_".join(graph["name"])

                if self.args.no_nodes: #produce an additional report without nodes (i know, i know)

                    #replace "_" with " " for a clearer comprehension
                    global_attributes_dict_nonodes_pyink = OrderedDict()

                    for elem in global_attributes_dict_nonodes:
                        newelem = elem.replace("_", " ")
                        global_attributes_dict_nonodes_pyink[newelem] = global_attributes_dict_nonodes[elem]

                    #todo mauro: il dizionario viene parsato correttamente e STA nell'html e nel json, ma il visualizzatore non fa vedere le righe: perchè?
                    r_nonodes.pyntacleink_report(report_dir=self.args.directory, report_dict=global_attributes_dict_nonodes_pyink, suffix=suffix) #report without nodes
                    suffix = suffix.replace("_no_nodes", "") #create new suffix for the "normal"_report

                #produce graphical report of the original file
                global_attributes_dict_pyink = OrderedDict()
                for elem in global_attributes_dict:
                    newelem = elem.replace("_", " ")
                    global_attributes_dict_pyink[newelem] = global_attributes_dict[elem]

                #todo prova che le chiavi ci sono
                # print(global_attributes_dict_nonodes_pyink)
                # input()

                r.pyntacleink_report(report_dir=self.args.directory, report_dict=global_attributes_dict_pyink,
                                         suffix=suffix)

            elif not self.args.no_plot and graph.vcount() >= 5000:
                u"The graph has too many nodes ({}). PyntacleInk allows plotting for network with N < 5000. No visual representation will be produced\n".format(
                    graph.vcount())

            else:
                sys.stdout.write(pyntacleink_skip_msg)

            # - LEGACY - OLD PLOTTER -
            # if not self.args.no_plot and graph.vcount() < 1000:
            #
            #     if self.args.no_nodes:
            #       sys.stdout.write(u"Generating plots of both the input network and the resulting network without nodes {} in {} format\n".format(self.args.no_nodes, self.args.plot_format))
            #
            #     else:
            #         sys.stdout.write(u"Generating network plot in {} format\n".format(self.args.plot_format))
            #
            #     # generates plot directory
            #     plot_dir = os.path.join(self.args.directory, "pyntacle-plots")
            #
            #     if not os.path.isdir(plot_dir):
            #         os.mkdir(plot_dir)
            #
            #     other_nodes_size = 25
            #     pal = sns.color_palette("Accent", 8).as_hex()
            #     framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()
            #     other_nodes_colour = pal[2]
            #     other_frame_colour = framepal[2]
            #     no_nodes_size = 35
            #     no_nodes_colour = pal[4]
            #     no_nodes_frames = framepal[4]
            #
                # if self.args.no_nodes:
                #     plot_path = os.path.join(plot_dir, ".".join(["_".join(["metric", self.args.which, re.sub('_nodes_removed', '', graph["name"][0]),"global_metrics_plot", self.date]), self.args.plot_format]))
                #     node_colors = [no_nodes_colour if x["name"] in nodes_list else other_nodes_colour for x
                #                     in
                #                     graph.vs()]
                #     node_frames = [no_nodes_frames if x["name"] in nodes_list else other_frame_colour for x
                #                    in
                #                    graph.vs()]
                #
                #     node_sizes = [no_nodes_size if x["name"] in nodes_list else other_nodes_size for x in
                #                   graph.vs()]
                #
                # else:
                #     node_colors = [other_nodes_colour] * graph.vcount()
                #     node_frames = [other_frame_colour] * graph.vcount()
                #     node_sizes = [other_nodes_size] * graph.vcount()
                #     plot_path = os.path.join(plot_dir, ".".join(["_".join(["Metric", self.args.which, graph["name"][0], self.date]), self.args.plot_format]))
                #
                # plot_graph = PlotGraph(graph=graph)
                # plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph
                #
                # plot_graph.set_node_colors(colors=node_colors)
                # plot_graph.set_node_sizes(sizes=node_sizes)
                #
                # plot_graph.set_node_colors(colors=node_colors)
                # plot_graph.set_node_sizes(sizes=node_sizes)
                #
                # # define layout
                # plot_graph.set_layouts(self.args.plot_layout)
                #
                # plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                #                       keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)
                #
                # if self.args.no_nodes:
                #
                #     plot_graph = PlotGraph(graph=graph_nonodes)
                #     plot_graph.set_node_labels(labels=graph_nonodes.vs()["name"])  # assign node labels to graph
                #
                #     # print(graph_copy.vs()["name"])
                #     node_colors = [other_nodes_colour] * graph_nonodes.vcount()
                #     node_frames = [other_frame_colour] * graph_nonodes.vcount()
                #     node_sizes = [other_nodes_size] * graph_nonodes.vcount()
                #
                #     plot_graph.set_node_colors(colors=node_colors)
                #     plot_graph.set_node_sizes(sizes=node_sizes)
                #
                #     # define layout
                #     plot_graph.set_layouts(self.args.plot_layout)
                #
                #     plot_path = os.path.join(plot_dir, ".".join(["_".join([graph["name"][0], "_no_nodes", self.date]),self.args.plot_format]))
                #
                #     plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                #                           keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

            # elif not self.args.no_plot and graph.vcount() >= 1000:
            #     sys.stdout.write(u"The graph has too many nodes ({}). It will not be drawn\n".format(graph.vcount()))

        if self.args.save_binary:
            sys.stdout.write(u"Saving graph to a binary file (ending in .graph)\n")
            basename_graph = os.path.splitext(os.path.basename(self.args.input_file))[0]
            binary_path = os.path.join(self.args.directory, basename_graph + ".graph")

            if self.args.which == 'local':
                if self.args.nodes:
                    nodes_list = self.args.nodes.split(",")
                else:
                    nodes_list = graph.vs["name"]
                for key in local_attributes_dict:
                    AddAttributes.add_node_attributes(graph, key, local_attributes_dict[key], nodes_list)
                PyntacleExporter.Binary(graph, binary_path)

            elif self.args.which == 'global':

                for key in global_attributes_dict:
                    if (key == "average_shortest_path_length" or key == 'median_shortest_path_length'):
                        newkey = re.sub("_shortest_path_length", "_global_shortest_path_length", key)
                    else:
                        newkey = key
                    AddAttributes.add_graph_attributes(graph, newkey, global_attributes_dict[key])
                PyntacleExporter.Binary(graph, binary_path)

                if self.args.no_nodes:
                    binary_path_nonodes = os.path.join(self.args.directory, basename_graph + "_no_nodes" + ".graph")
                    sys.stdout.write(u"Saving a binary of the input graph without the requested nodes at path: {}\n".format(os.path.basename(binary_path_nonodes)))
                    for key in global_attributes_dict_nonodes:
                        if (key == "average_shortest_path_length" or key == 'median_shortest_path_length'):
                            newkey = re.sub("_shortest_path_length", "_global_shortest_path_length", key)
                        else:
                            newkey = key
                        AddAttributes.add_graph_attributes(graph_nonodes, newkey, global_attributes_dict_nonodes[key])
                    
                    PyntacleExporter.Binary(graph_nonodes, binary_path_nonodes)

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(section_end)
        sys.stdout.write(u"Pyntacle metrics completed successfully\n")
        sys.exit(0)
