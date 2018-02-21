import pandas as pd
from config import *
from algorithms.global_topology import GlobalTopology, _GlobalAttribute
from algorithms.local_topology import LocalTopology, _LocalAttribute
from algorithms.sparseness import *
from algorithms.sparseness import _SparsenessAttribute
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError
from io_stream.exporter_NEW import Exporter
from report.plotter import *
from report.reporter import *
from io_stream.import_attributes import ImportAttributes
from misc.graph_load import *
from utils.graph_utils import GraphUtils

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
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


class Metrics():
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
        if self.args.no_header:
            header = False
        else:
            header = True

        if not hasattr(self.args, 'which'):
            raise Error("usage: pyntacle.py metrics {global, local} [options]")

        # Checking input file
        if self.args.input_file is None:
            self.logging.error(
                "Please specify an input file using the -i option.".format(self.args.input_file))
            sys.exit()

        if not os.path.exists(self.args.input_file):
            self.logging.error("Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit()

        # check output directory
        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: Output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        self.logging.debug('Running pyntacle metrics, with arguments')
        self.logging.debug(self.args)

        # Load Graph
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header).graph_load()

        # init Utils global stuff
        utils = GraphUtils(graph=graph)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write("Taking the largest component of the input graph as you requested ({} nodes, {} edges)\n".format(graph.vcount(), graph.ecount()))

            except MultipleSolutionsError:
                sys.stderr.write("The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the \"--largest-component\" option. Quitting\n")
                sys.exit(1)

        # Check provided dimensions' format
        if self.args.plot_dim:  # define custom format
            self.args.plot_dim = self.args.plot_dim.split(",")

            if len(self.args.plot_dim) != 2:
                sys.stderr.write(
                    "Format specified must be a comma separated list of values(e.g. 1920,1080). Quitting.\n")

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

        self.args.report_format = "." + self.args.report_format

        if self.args.which == "local":

            reporter = pyntacleReporter(graph=graph) #init reporter

            # initialize local attribute method

            local_attributes = LocalTopology(graph=graph)

            if self.args.nodes is not None:
                sys.stdout.write("Computing local metrics for nodes {}\n".format(self.args.nodes))
                nodes_list = self.args.nodes.split(",")
                index_list = utils.get_node_indices(node_names=nodes_list)
                # print(index_list)

                try:
                    utils.check_name_list(nodes_list)  # to check everything's in order

                except MissingAttributeError:
                    self.logging.error(
                        "One of the nodes you specified is not in the input graph, check your node list and its formatting")
                    sys.exit(1)

            else:
                sys.stdout.write("Computing local metrics for all nodes in the graph\n")
                index_list = None

            local_attributes.degree(index_list=index_list, recalculate=True)
            local_attributes.clustering_coefficient(index_list=index_list, recalculate=True)
            local_attributes.betweenness(index_list=index_list, recalculate=True)
            local_attributes.closeness(index_list=index_list, recalculate=True)
            local_attributes.radiality(index_list=index_list, recalculate=True)
            local_attributes.radiality_reach(index_list=index_list, recalculate=True)
            local_attributes.eccentricity(index_list=index_list, recalculate=True)
            local_attributes.shortest_path(index_list=index_list, recalculate=True)

            if self.args.damping_factor < 0.0 and self.args.damping_factor > 1.0:
                self.logging.error("damping factor must be betweeen 0 and 1")
                sys.exit(1)

            else:

                if self.args.weights is None:

                    local_attributes.pagerank(index_list=index_list, weights=None,
                                              damping=self.args.damping_factor,
                                              recalculate=True)

                else:
                    if not os.path.exists(self.args.weights):
                        sys.stderr.write(
                            "Input file {} does not exist. Quitting.\n".format(self.args.weights))
                        sys.exit(1)

                    else:
                        sys.stdout.write("Adding Edge Weights from file {}\n".format(self.args.weights))

                        weights_sep = separator_detect(self.args.weights)
                        graph = GraphLoad(self.args.input_file, self.args.format, header).graph_load()

                        weights = pd.read_csv(filepath_or_buffer=self.args.weights, sep=weights_sep)

                        # Check attributes file's format
                        if any(i in weights.iloc[0, 0] for i in ' ()'):
                            mode = 'cytoscape'
                            weightscol = 1
                        else:
                            mode = 'standard'
                            weightscol = 2
                        
                        # convert the weights to floats
                        try:
                            [float(x) for x in weights[weights.columns[weightscol]].values]

                        except (ValueError, TypeError) as errs:
                            sys.stderr.write("Weights must be float or integers. Quitting\n")
                            sys.exit(1)

                        if len(weights.columns) >= 2:
                            self.logging.warning(
                                "Using column 3 as edge weights for pagerank. Adding the other values as edge attributes, but they will not be used for pagerank computing\n")
                            weights_name = weights.columns[weightscol]  # store the name of the attribute
                            print("name", weights_name)
                            ImportAttributes(graph).import_edge_attributes(file_name=self.args.weights,
                                                                           sep=weights_sep,
                                                                           mode=mode)
                            print(list(graph.es))
                            weights_list = [float(x) if isinstance(x, str) else None for x in
                                            graph.es()[weights_name]]

                            local_attributes.pagerank(index_list=index_list, weights=weights_list,
                                                      damping=self.args.damping_factor, recalculate=True)

                        else:
                            sys.stderr(
                                "weights file must contains at least two columns, the first should represent node names and the second ther respective weights. Quitting.\n")
                            sys.exit(1)

            # create report for the selected metrics
            if self.args.nodes is None:
                nodes_list = graph.vs()["name"]
                report_prefix = "_".join(["pyntacle", graph["name"][0], "local_metrics", "report",
                                          runtime_date])
            else:
                report_prefix = "_".join(
                    ["pyntacle", graph["name"][0], "local_metrics_selected_nodes_report",
                     runtime_date])

            sys.stdout.write("Producing report in {} format.\n".format(self.args.report_format))

            report_path = os.path.join(self.args.directory, report_prefix + self.args.report_format)

            if os.path.exists(report_path):
                sys.stdout.write("WARNING: File {} already exists, overwriting it\n".format(report_path))

            local_attributes_list = [_LocalAttribute.degree,
                                     _LocalAttribute.clustering_coefficient,
                                     _LocalAttribute.betweenness,
                                     _LocalAttribute.shortest_path,
                                     _LocalAttribute.closeness,
                                     _LocalAttribute.radiality,
                                     _LocalAttribute.radiality_reach,
                                     _LocalAttribute.eccentricity,
                                     _LocalAttribute.pagerank]

            reporter.report_local_topology(node_names=nodes_list, local_attributes_list=local_attributes_list)

            reporter.create_report(report_path=report_path)

            if not self.args.no_plot and graph.vcount() < 1000:
    
                sys.stdout.write("Generating plots in {} format.\n".format(self.args.plot_format))
                
                # generates plot directory
                plot_dir = os.path.join(self.args.directory, "pyntacle-Plots")

                if os.path.isdir(plot_dir):
                    self.logging.warning(
                        "A directory named \"pyntacle-Plots\" already exists, I may overwrite something in there")

                else:
                    os.makedirs(plot_dir, exist_ok=True)

                plot_graph = PlotGraph(graph=graph)
                plot_graph.set_node_label(labels=graph.vs()["name"])  # assign node labels to graph

                pal = sns.color_palette("Accent", 8).as_hex()
                framepal = sns.color_palette("Accent", 8, desat=0.5).as_hex()

                other_nodes_colour = pal[2]
                other_frame_colour = framepal[2]
                other_nodes_size = 25

                if self.args.nodes:  # make node selected of a different colour and bigger than the other ones, so they can be visualized
                    sys.stdout.write("Highlighting nodes {} in plot\n".format(nodes_list))
                    selected_nodes_colour = pal[0]
                    selected_nodes_frames = framepal[0]

                    node_colours = [selected_nodes_colour if x["name"] in nodes_list else other_nodes_colour
                                    for x in
                                    graph.vs()]
                    node_frames = [selected_nodes_frames if x["name"] in nodes_list else other_frame_colour
                                    for x in
                                    graph.vs()]

                    #print(node_colours)

                    plot_graph.set_node_colours(colours=node_colours)

                    node_sizes = [45 if x["name"] in nodes_list else other_nodes_size for x in graph.vs()]
                    plot_graph.set_node_sizes(sizes=node_sizes)

                else:
                    # sys.stdout.write("Plotting network\n".format(nodes_list))
                    node_colours = [other_nodes_colour] * graph.vcount()
                    node_frames = [other_frame_colour] * graph.vcount()
                    plot_graph.set_node_colours(colours=node_colours)

                    node_sizes = [other_nodes_size] * graph.vcount()
                    plot_graph.set_node_sizes(sizes=node_sizes)

                # define layout
                plot_graph.set_layouts()

                plot_path = os.path.join(plot_dir, ".".join(["_".join(
                    ["pyntacle", graph["name"][0], "local_metrics_plot_",
                     runtime_date]), self.args.plot_format]))
                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=True,
                                      keep_aspect_ratio=True, vertex_label_size=8, vertex_frame_color=node_frames)

            elif not self.args.no_plot and graph.vcount() >= 1000:
                sys.stdout.write("The graph has too many nodes ({}). Can't draw graph\n".format(graph.vcount()))

        elif self.args.which == "global":

            #define all global attributes that will be found
            global_attributes_list = [_GlobalAttribute.average_degree, _GlobalAttribute.average_path_length,
                                      _GlobalAttribute.diameter, _GlobalAttribute.density,
                                      _GlobalAttribute.clustering_coefficient,
                                      _GlobalAttribute.weighted_clustering_coefficient,
                                      _GlobalAttribute.average_eccentricity, _GlobalAttribute.average_radiality,
                                      _GlobalAttribute.average_radiality_reach, _GlobalAttribute.average_closeness,
                                      _GlobalAttribute.pi,
                                      _SparsenessAttribute.completeness,
                                      _SparsenessAttribute.completeness_legacy,
                                      _SparsenessAttribute.compactness]

            #find metrics for the whole graph (without removing nodes)
            sys.stdout.write("Computing global Metrics for whole graph\n")
            global_topology = GlobalTopology(graph=graph)
            sparseness = Sparseness(graph=graph)

            global_topology.clustering_coefficient(recalculate=True)

            global_topology.weighted_clustering_coefficient(recalculate=True)
            global_topology.average_closeness(recalculate=True)
            global_topology.average_degree(recalculate=True)
            global_topology.average_eccentricity(recalculate=True)
            global_topology.average_radiality(recalculate=True)
            global_topology.average_radiality_reach(recalculate=True)
            global_topology.average_path_length(recalculate=True)
            global_topology.density(recalculate=True)
            global_topology.diameter(recalculate=True)
            global_topology.pi(recalculate=True)
            sparseness.compactness(recalculate=True)
            sparseness.completeness(recalculate=True)
            sparseness.completeness_legacy(recalculate=True)


            if not self.args.no_nodes: #create standard report for the whole graph
                sys.stdout.write("Producing report\n")

                reporter = pyntacleReporter(graph=graph)
                reporter.report_global_topology(global_attributes_list)
                report_prefix = "_".join(["pyntacle", graph["name"][0], "global", "metrics", "report"])

                report_path = os.path.join(self.args.directory, "_".join(
                    [report_prefix, runtime_date]) + self.args.report_format)

                reporter.report_global_topology(global_attributes_list)
                reporter.create_report(report_path=report_path)

            else:

                sys.stdout.write("Removing nodes {} from input graph and computing global metrics\n".format(self.args.no_nodes))
                nodes_list = self.args.no_nodes.split(",")

                # this will be useful when producing the two global topology plots, one for the global graph and the other one fo all nodes
                nodes_list = [x.replace(" ", "") for x in nodes_list]
                index_list = utils.get_node_indices(node_names=nodes_list)

                # delete vertices
                graph_nonodes = graph.copy()
                graph_nonodes.delete_vertices(index_list) #remove target nodes

                global_topology_nonodes= GlobalTopology(graph_nonodes)
                sparseness_nonodes = Sparseness(graph_nonodes)

                global_topology_nonodes.clustering_coefficient(recalculate=True)
                global_topology_nonodes.weighted_clustering_coefficient(recalculate=True)
                global_topology_nonodes.average_closeness(recalculate=True)
                global_topology_nonodes.average_degree(recalculate=True)
                global_topology_nonodes.average_eccentricity(recalculate=True)
                global_topology_nonodes.average_radiality(recalculate=True)
                global_topology_nonodes.average_radiality_reach(recalculate=True)
                global_topology_nonodes.average_path_length(recalculate=True)
                global_topology_nonodes.density(recalculate=True)
                global_topology_nonodes.diameter(recalculate=True)
                global_topology_nonodes.pi(recalculate=True)

                sparseness_nonodes.compactness(recalculate=True)
                sparseness_nonodes.completeness(recalculate=True)
                sparseness_nonodes.completeness_legacy(recalculate=True)

                sys.stdout.write("Producing report\n")
                reporter = pyntacleReporter(graph=graph, graph2=graph_nonodes)
                reporter.report_global_comparisons(attributes_list=global_attributes_list)

                report_prefix = "_".join(["pyntacle", graph["name"][0], "global", "metrics", "nonodes", "report"])

                report_path = os.path.join(self.args.directory, "_".join(
                    [report_prefix, runtime_date]) + self.args.report_format)

                reporter.create_report(report_path=report_path)

            if not self.args.no_plot and graph.vcount() < 1000:

                if self.args.no_nodes:
                    sys.stdout.write("Generating Plots of both input graph {} and the graph without nodes\n".format(os.path.basename(self.args.input_file)))

                else:
                    sys.stdout.write("Generating Plot of input graph {}\n".format(os.path.basename(self.args.input_file)))

                # generates plot directory
                plot_dir = os.path.join(self.args.directory, "pyntacle-Plots")

                if os.path.isdir(plot_dir):
                    self.logging.warning(
                        "WARNING: A directory named \"pyntacle-Plots\" already exists, I may overwrite something in there")

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
                    plot_path = os.path.join(plot_dir, ".".join(["_".join(["pyntacle", graph["name"][0],"global_metrics_plot_original", runtime_date]),self.args.plot_format]))
                    node_colours = [no_nodes_colour if x["name"] in nodes_list else other_nodes_colour for x
                                    in
                                    graph.vs()]
                    node_frames = [no_nodes_frames if x["name"] in nodes_list else other_frame_colour for x
                                   in
                                   graph.vs()]

                    node_sizes = [no_nodes_size if x["name"] in nodes_list else other_nodes_size for x in
                                  graph.vs()]

                else:
                    node_colours = [other_nodes_colour] * graph.vcount()
                    node_frames = [other_frame_colour] * graph.vcount()
                    node_sizes = [other_nodes_size] * graph.vcount()
                    plot_path = os.path.join(plot_dir, ".".join(["_".join(["pyntacle", graph["name"][0],"global_metrics_plot", runtime_date]), self.args.plot_format]))

                plot_graph = PlotGraph(graph=graph)
                plot_graph.set_node_label(labels=graph.vs()["name"])  # assign node labels to graph

                plot_graph.set_node_colours(colours=node_colours)
                plot_graph.set_node_sizes(sizes=node_sizes)

                plot_graph.set_node_colours(colours=node_colours)
                plot_graph.set_node_sizes(sizes=node_sizes)

                # define layout
                plot_graph.set_layouts()

                plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=True,
                                      keep_aspect_ratio=True, vertex_label_size=8, vertex_frame_color=node_frames)

                if self.args.no_nodes:

                    plot_graph = PlotGraph(graph=graph_nonodes)
                    plot_graph.set_node_label(labels=graph_nonodes.vs()["name"])  # assign node labels to graph

                    # print(graph_copy.vs()["name"])
                    node_colours = [other_nodes_colour] * graph_nonodes.vcount()
                    node_frames = [other_frame_colour] * graph_nonodes.vcount()
                    node_sizes = [other_nodes_size] * graph_nonodes.vcount()

                    plot_graph.set_node_colours(colours=node_colours)
                    plot_graph.set_node_sizes(sizes=node_sizes)

                    # define layout
                    plot_graph.set_layouts()

                    plot_path = os.path.join(plot_dir, ".".join(["_".join(["pyntacle", graph["name"][0],"global_metrics_plot_nonodes",runtime_date]),self.args.plot_format]))

                    plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=True,
                                          keep_aspect_ratio=True, vertex_label_size=8, vertex_frame_color=node_frames)

            elif not self.args.no_plot and graph.vcount() >= 1000:
                sys.stdout.write("The graph has too many nodes ({}). Can't draw graph\n".format(graph.vcount()))
        else:
            self.logging.critical(
                "This should not happen. Please contact Dedadlus developer and send a command line, along with a log. Quitti9ng\n")
            sys.exit(1)

        if self.args.save_binary:
            sys.stdout.write("Saving graph to a Binary file\n")
            binary_path = os.path.join(self.args.directory, report_prefix + ".graph")
            Exporter.Binary(graph, binary_path)
        cursor.stop()
        sys.stdout.write("pyntacle Metrics completed successfully. Ending\n")
        sys.exit(0)
