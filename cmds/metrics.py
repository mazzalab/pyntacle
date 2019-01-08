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

from algorithms.shortest_path import ShortestPath
from algorithms.global_topology import GlobalTopology
from algorithms.local_topology import LocalTopology
from algorithms.sparseness import *
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import *
from cmds.cmds_utils.reporter import *
from io_stream.import_attributes import ImportAttributes
from internal.graph_load import GraphLoad,separator_detect

from tools.graph_utils import GraphUtils
from tools.add_attributes import AddAttributes
from tools.enums import *
from exceptions.missing_attribute_error import MissingAttributeError

class Metrics:
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
        if self.args.no_header:
            header = False
        else:
            header = True

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py metrics {global, local} [options]")

        # Checking input file
        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            self.logging.error(u"Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit(1)

        # check output directory
        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"Warning: Output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        self.logging.debug(u'Running Pyntacle metrics, with arguments ')
        self.logging.debug(self.args)

        # Load Graph
        sys.stdout.write(u"Importing graph from file...\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header, separator=self.args.input_separator).graph_load()
        # init Utils global stuff
        utils = GraphUtils(graph=graph)

        # Decide implementation
        if '__implementation' in graph.attributes():
            implementation = graph['__implementation']
        else:
            implementation = CmodeEnum.igraph
            
        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(u"Taking the largest component of the input graph as you requested ({} nodes, {} edges)\n".format(graph.vcount(), graph.ecount()))

            except MultipleSolutionsError:
                sys.stderr.write(u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting\n")
                sys.exit(1)

        # Check provided dimensions' format
        if self.args.plot_dim:  # define custom format
            self.args.plot_dim = self.args.plot_dim.split(",")

            if len(self.args.plot_dim) != 2:
                sys.stderr.write(
                    u"Format specified must be a comma separated list of values(e.g. 1920,1080). Quitting.\n")

            for i in range(0, len(self.args.plot_dim)):
                try:
                    self.args.plot_dim[i] = int(self.args.plot_dim[i])

                except ValueError:
                    sys.stderr.write(
                        u"Format specified must be a comma-separated list of values(e.g. 1920,1080). Quitting\n")
                    sys.exit(1)

                if self.args.plot_dim[i] <= 0:
                    sys.stderr.write(
                        u"Format specified must be a comma-separated list of values(e.g. 1920,1080). Quitting\n")
                    sys.exit(1)

            plot_size = tuple(self.args.plot_dim)

        else:
            # generate different formats according to graph size
            if graph.vcount() <= 150:
                plot_size = (800, 800)

            else:
                plot_size = (1600, 1600)

        if self.args.which == "local":

            reporter = pyntacleReporter(graph=graph) #init reporter

            if self.args.nodes is not None:
                sys.stdout.write(u"Computing local metrics for nodes ({})\n".format(', '.join(self.args.nodes)))

                try:
                    utils.check_name_list(self.args.nodes.split(","))  # to check everything's in order

                except MissingAttributeError:
                    sys.stderr.write(
                        u"One of the nodes you specified is not in the input graph, check your node list and its formatting.Quitting.\n")
                    sys.exit(1)

            else:
                sys.stdout.write(u"Computing local metrics for all nodes in the graph...\n")

            if self.args.damping_factor < 0.0 or self.args.damping_factor > 1.0:
                sys.stderr.write(u"Damping factor must be between 0 and 1. Quitting.\n")
                sys.exit(1)

            else:

                if not self.args.weights is None:
                    if not os.path.exists(self.args.weights):
                        sys.stderr.write(
                            u"Weights file {} does not exist. Quitting.\n".format(self.args.weights))
                        sys.exit(1)

                    else:
                        #Needs a file that has a 'weights' column.
                        sys.stdout.write(u"Adding edge weights from file {}...\n".format(self.args.weights))
                        ImportAttributes.import_edge_attributes(graph, self.args.weights, sep=separator_detect(self.args.weights), mode=self.args.weights_format)
                        try:
                            weights = [float(x) if x!=None else 1.0 for x in graph.es()["weights"]]
                        except KeyError:
                            sys.stderr.write(u"The attribute file does not contain a column named 'weights'."
                                             "Please fix it and launch Pyntacle again.\n")
                            sys.exit(1)

                else:
                    weights = None
                    
            # create pyntacle_commands_utils for the selected metrics
            if self.args.nodes is None:
                nodes_list = graph.vs()["name"]
                report_prefix = "_".join(["pyntacle", graph["name"][0], "local_metrics", "report",
                                          self.date])
            else:
                nodes_list = self.args.nodes.split(",")
                report_prefix = "_".join(
                    ["pyntacle", graph["name"][0], "local_metrics_selected_nodes_report",
                     self.date])

            local_attributes_dict = OrderedDict({LocalAttributeEnum.degree.name: LocalTopology.degree(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.clustering_coefficient.name: LocalTopology.clustering_coefficient(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.betweenness.name: LocalTopology.betweenness(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.closeness.name: LocalTopology.closeness(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.radiality.name: LocalTopology.radiality(graph=graph, nodes=nodes_list, cmode=implementation),
                                                 LocalAttributeEnum.radiality_reach.name: LocalTopology.radiality_reach(graph=graph, nodes=nodes_list, cmode=implementation),
                                                 LocalAttributeEnum.eccentricity.name: LocalTopology.eccentricity(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.eigenvector_centrality.name : LocalTopology.eigenvector_centrality(graph=graph, nodes=nodes_list),
                                                 LocalAttributeEnum.pagerank.name: LocalTopology.pagerank(graph=graph, nodes=nodes_list, weights=weights, damping=self.args.damping_factor)})
            
            if self.args.nodes:
                local_attributes_dict["nodes"] = self.args.nodes

            sys.stdout.write(u"Producing report in {} format...\n".format(self.args.report_format))
            report_path = os.path.join(self.args.directory, report_prefix + self.args.report_format)

            if os.path.exists(report_path):
                sys.stdout.write(u"Warning: File {} already exists, overwriting it.\n".format(report_path))

            reporter.create_report(ReportEnum.Local, local_attributes_dict)
            reporter.write_report(report_dir=self.args.directory, format=self.args.report_format)

            if not self.args.no_plot and graph.vcount() < 1000:
    
                sys.stdout.write(u"Generating plots in {} format...\n".format(self.args.plot_format))
                
                # generates plot directory
                plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

                if os.path.isdir(plot_dir):
                    self.logging.warning(
                        "A directory named 'pyntacle-plots' already exists, I may overwrite something in there.")

                else:
                    os.makedirs(plot_dir, exist_ok=True)

                plot_graph = PlotGraph(graph=graph)
                plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph

                pal = sns.color_palette("Accent", 8).as_hex()
                framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()

                other_nodes_colour = pal[2]
                other_frame_colour = framepal[2]
                other_nodes_size = 25

                if self.args.nodes:  # make node selected of a different colour and bigger than the other ones, so they can be visualized
                    sys.stdout.write(u"Highlighting nodes ({}) in plot...\n".format(', '.join(nodes_list)))
                    selected_nodes_colour = pal[0]
                    selected_nodes_frames = framepal[0]

                    node_colors = [selected_nodes_colour if x["name"] in nodes_list else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [selected_nodes_frames if x["name"] in nodes_list else other_frame_colour
                                    for x in
                                    graph.vs()]

                    #print(node_colors)

                    plot_graph.set_node_colors(colors=node_colors)

                    node_sizes = [45 if x["name"] in nodes_list else other_nodes_size for x in graph.vs()]
                    plot_graph.set_node_sizes(sizes=node_sizes)

                else:
                    # sys.stdout.write("Plotting network\n".format(nodes_list))
                    node_colors = [other_nodes_colour] * graph.vcount()
                    node_frames = [other_frame_colour] * graph.vcount()
                    plot_graph.set_node_colors(colors=node_colors)

                    node_sizes = [other_nodes_size] * graph.vcount()
                    plot_graph.set_node_sizes(sizes=node_sizes)

                # define layout
                plot_graph.set_layouts(self.args.plot_layout)

                plot_path = os.path.join(plot_dir, ".".join(["_".join(
                    ["pyntacle", graph["name"][0], "local_metrics_plot_",
                     self.date]), self.args.plot_format]))
                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

            elif not self.args.no_plot and graph.vcount() >= 1000:
                sys.stdout.write(u"The graph has too many nodes ({}). It will not be drawn.\n".format(graph.vcount()))

        elif self.args.which == "global":
            
            sys.stdout.write(u"Computing global metrics...\n")

            global_attributes_dict = OrderedDict({GlobalAttributeEnum.average_shortest_path_length.name: ShortestPath.average_global_shortest_path_length(graph=graph),
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

            sys.stdout.write(u"Producing global metrics report for the input graph...\n")
            report_prefix = "_".join(
                ["pyntacle", graph["name"][0], "global_metrics_report",
                 self.date])
            
            reporter = pyntacleReporter(graph=graph)  # init reporter
            reporter.create_report(ReportEnum.Global, global_attributes_dict)
            reporter.write_report(report_dir=self.args.directory, format=self.args.report_format)

            if self.args.no_nodes:  # create an additional report for the graph minus the selected nodes
                report_prefix_nonodes = "_".join(["pyntacle", graph["name"][0], "global_metrics_nonodes", "report",
                                          self.date])
                
                sys.stdout.write(u"Removing nodes:\n\t{}\nfrom input graph and computing Global Metrics.\n".format(self.args.no_nodes))
                nodes_list = self.args.no_nodes.split(",")

                # this will be useful when producing the two global topology plots, one for the global graph and the other one fo all nodes
                nodes_list = [x.replace(" ", "") for x in nodes_list]
                index_list = utils.get_node_indices(node_names=nodes_list)

                # delete vertices
                graph_nonodes = graph.copy()
                graph_nonodes.delete_vertices(index_list) #remove target nodes

                global_attributes_dict_nonodes = OrderedDict({
                    'Removed nodes': ','.join(nodes_list),
                    GlobalAttributeEnum.average_shortest_path_length.name: ShortestPath.average_global_shortest_path_length(
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

                sys.stdout.write(u"Producing global metrics report for the input graph after node removal...\n")
                graph_nonodes["name"][0] += '_without_nodes'
                reporter = pyntacleReporter(graph=graph_nonodes)  # init reporter
                reporter.create_report(ReportEnum.Global, global_attributes_dict_nonodes)
                reporter.write_report(report_dir=self.args.directory, format=self.args.report_format)

            if not self.args.no_plot and graph.vcount() < 1000:

                if self.args.no_nodes:
                    sys.stdout.write(u"Generating plots of both input graph {} and the graph without nodes...\n".format(os.path.basename(self.args.input_file)))

                else:
                    sys.stdout.write(u"Generating plot of input graph {}...\n".format(os.path.basename(self.args.input_file)))

                # generates plot directory
                plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

                if os.path.isdir(plot_dir):
                    self.logging.warning(
                        u"Warning: A directory named 'pyntacle-plots' already exists, I may overwrite something in there")

                else:
                    os.mkdir(plot_dir)

                other_nodes_size = 25
                pal = sns.color_palette("Accent", 8).as_hex()
                framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()
                other_nodes_colour = pal[2]
                other_frame_colour = framepal[2]
                no_nodes_size = 35
                no_nodes_colour = pal[4]
                no_nodes_frames = framepal[4]

                if self.args.no_nodes:
                    plot_path = os.path.join(plot_dir, ".".join(["_".join(["pyntacle", re.sub('_without_nodes', '', graph["name"][0]),"global_metrics_plot", self.date]),self.args.plot_format]))
                    node_colors = [no_nodes_colour if x["name"] in nodes_list else other_nodes_colour for x
                                    in
                                    graph.vs()]
                    node_frames = [no_nodes_frames if x["name"] in nodes_list else other_frame_colour for x
                                   in
                                   graph.vs()]

                    node_sizes = [no_nodes_size if x["name"] in nodes_list else other_nodes_size for x in
                                  graph.vs()]

                else:
                    node_colors = [other_nodes_colour] * graph.vcount()
                    node_frames = [other_frame_colour] * graph.vcount()
                    node_sizes = [other_nodes_size] * graph.vcount()
                    plot_path = os.path.join(plot_dir, ".".join(["_".join(["pyntacle", graph["name"][0],"global_metrics_plot", self.date]), self.args.plot_format]))

                plot_graph = PlotGraph(graph=graph)
                plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph

                plot_graph.set_node_colors(colors=node_colors)
                plot_graph.set_node_sizes(sizes=node_sizes)

                plot_graph.set_node_colors(colors=node_colors)
                plot_graph.set_node_sizes(sizes=node_sizes)

                # define layout
                plot_graph.set_layouts(self.args.plot_layout)

                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

                if self.args.no_nodes:

                    plot_graph = PlotGraph(graph=graph_nonodes)
                    plot_graph.set_node_labels(labels=graph_nonodes.vs()["name"])  # assign node labels to graph

                    # print(graph_copy.vs()["name"])
                    node_colors = [other_nodes_colour] * graph_nonodes.vcount()
                    node_frames = [other_frame_colour] * graph_nonodes.vcount()
                    node_sizes = [other_nodes_size] * graph_nonodes.vcount()

                    plot_graph.set_node_colors(colors=node_colors)
                    plot_graph.set_node_sizes(sizes=node_sizes)

                    # define layout
                    plot_graph.set_layouts(self.args.plot_layout)

                    plot_path = os.path.join(plot_dir, ".".join(["_".join(["pyntacle", graph["name"][0], "global_metrics_plot",self.date]),self.args.plot_format]))

                    plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                          keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=node_frames)

            elif not self.args.no_plot and graph.vcount() >= 1000:
                sys.stdout.write(u"The graph has too many nodes ({}). It will not be drawn.\n".format(graph.vcount()))
        else:
            self.logging.critical(
                u"Critical error. Please contact Pyntacle developers and report this error, along with your command. Quitting\n")
            sys.exit(1)

        if self.args.save_binary:

            binary_path = os.path.join(self.args.directory, report_prefix.replace('_report_', '_') + ".graph")
            # elif self.args.no_nodes:
            # nodes_list = graph_nonodes.vs()
            if self.args.which == 'local':
                if self.args.nodes:
                    nodes_list = self.args.nodes.split(",")
                else:
                    nodes_list = graph.vs["name"]
                for key in local_attributes_dict:
                    AddAttributes.add_node_attributes(graph, key, local_attributes_dict[key], nodes_list)

            elif self.args.which == 'global':
                if self.args.no_nodes:
                    binary_path_nonodes = os.path.join(self.args.directory, report_prefix_nonodes.replace('_report_', '_') + ".graph")
                    sys.stdout.write(u"The --no-nodes option was selected to calculate the global metrics. A second graph without those "
                                     "nodes and said metrics will be saved in a second Binary file.\n".format(os.path.basename(binary_path_nonodes)))
                    for key in global_attributes_dict_nonodes:
                        AddAttributes.add_graph_attributes(graph_nonodes, key, global_attributes_dict_nonodes[key])
                    
                    PyntacleExporter.Binary(graph_nonodes, binary_path_nonodes)

                for key in global_attributes_dict:
                    AddAttributes.add_graph_attributes(graph, key, global_attributes_dict[key])
                    
            sys.stdout.write(u"Saving graph to a binary file (ending in .graph).\n")
            PyntacleExporter.Binary(graph, binary_path)

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(u"Pyntacle metrics completed successfully.Ending.\n")
        sys.exit(0)
