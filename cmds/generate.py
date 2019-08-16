__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t.mazza@css-mendel.it>
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
from warnings import simplefilter

from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from io_stream.generator import PyntacleGenerator
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.reporter import PyntacleReporter


class Generate:

    def __init__(self, args):
        self.logging = log
        self.args = None
        self.args = args
        if self.args.seed:
            random.seed(self.args.seed)

        self.date = runtime_date
        if not self.args.output_separator:
            self.args.output_separator = '\t'

        # - DEPRECATED-Check for pycairo
        # if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
        #     sys.stdout.write(pycairo_message)
        #     self.args.no_plot = True

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        sys.stdout.write(run_start)
        if self.args.which == "random":

            if self.args.nodes is None:
                self.args.nodes = random.randint(100, 500)
            else:
                try:
                    self.args.nodes = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write(u"Number of nodes must be a positive integer. Quitting\n")
                    sys.exit(1)

            if not self.args.probability and self.args.edges:

                try:
                    self.args.edges = int(self.args.edges)
                    u"Generating graph with random topology\nParameters:\nNumber of nodes: {0}\nNumber of edges: {1}\n".format(
                        self.args.nodes, self.args.edges)
                    
                    graph = PyntacleGenerator.Random([self.args.nodes, self.args.edges], name="Random", seed=self.args.seed)

                except (ValueError, TypeError, IllegalGraphSizeError):
                    sys.stderr.write(
                        u"Number of nodes must be a positive integer greater than 2 and number of edges must be a positive integer greater than zero. Quitting\n")
                    sys.exit(1)

            else:
                if not self.args.probability:
                    self.args.probability = 0.5

                else:
                    try:
                        self.args.probability = float(self.args.probability)
                        if self.args.probability > 1.0 or self.args.probability < 0.0:
                            raise ValueError

                    except ValueError:
                        sys.stderr.write(u"Probability must be a float between 0 and 1. Quitting\n")
                        sys.exit(1)

                try:
                    sys.stdout.write(
                        "uGenerating graph with random topology\nParameters:\nNumber of nodes: {0}\nProbability of wiring: {1}\n".format(
                            self.args.nodes, self.args.probability))
                    graph = PyntacleGenerator.Random([self.args.nodes, self.args.probability], name="Random", seed=self.args.seed)

                except (ValueError, TypeError, IllegalGraphSizeError):
                    sys.stderr.write(
                        u"Number of nodes must be a positive integer greater than 2 and a probability must be a float between 0 and 1. Quitting\n")
                    sys.exit(1)
                
        elif self.args.which == "scale-free":
            if self.args.nodes is None:
                self.args.nodes = random.randint(100, 500)

            else:
                try:
                    self.args.nodes = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write(u"Number of nodes must be a positive integer. Quitting\n")
                    sys.exit(1)

            if self.args.avg_edges is None:
                self.args.avg_edges = random.randint(10, 100)

            else:
                try:
                    self.args.avg_edges = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write(u"Number of outgoing edges must be a positive integer. Quitting\n")
                    sys.exit(1)

            try:
                sys.stdout.write(
                    u"Generating graph with scale-free topology\nParameters:\nNumber of Nodes: {0}\nNumber of Outgoing edges: {1}\n".format(
                        self.args.nodes, self.args.avg_edges))
                graph = PyntacleGenerator.ScaleFree([self.args.nodes, self.args.avg_edges], name="ScaleFree", seed=self.args.seed)

            except (ValueError, TypeError, IllegalGraphSizeError):
                sys.stderr.write(
                    u"Number of nodes and number of outgoing edges must be positive integers. Quitting\n")
                sys.exit(1)

        elif self.args.which == "tree":

            if self.args.nodes is None:
                self.args.nodes = random.randint(100, 500)

            else:
                try:
                    self.args.nodes = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write(u"Number of nodes must be a positive integer. Quitting\n")
                    sys.exit(1)

            if self.args.children is None:
                self.args.children = random.randint(2, 10)

            else:
                try:
                    self.args.children = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write(u"Number of children must be a positive integer. Quitting\n")
                    sys.exit(1)

            try:
                sys.stdout.write(
                    u"Generating Graph with tree topology\nParameters:\nNumber of nodes: {0}\nChildren per node: {1}\n".format(
                        self.args.nodes, self.args.children))
                graph = PyntacleGenerator.Tree([self.args.nodes, self.args.children], name="Tree", seed=self.args.seed)

            except (ValueError, TypeError, IllegalGraphSizeError):
                sys.stderr.write(
                    u"Number of nodes and number of children must be positive integers. Quitting\n")
                sys.exit(1)

        elif self.args.which == "small-world":
            
            #This does not happen anymore, as default is 2.
            # if not self.args.lattice_size:
            #     self.args.lattice_size = 10
            #
            # if not self.args.nei:
            #     self.args.nei = random.randint(1, 5)

            if isinstance(self.args.lattice, str):
                try:
                    self.args.lattice = int(self.args.lattice)
                    self.args.lattice_size = int(self.args.lattice_size)
                    self.args.nei = int(self.args.nei)
                    self.args.probability = float(self.args.probability)

                    if 0 < self.args.probability > 1.0:
                        raise ValueError

                    if self.args.lattice_size <= 1:
                        raise ValueError

                    if self.args.nei < 1:
                        raise ValueError

                    if self.args.lattice <= 1:
                        raise ValueError

                except ValueError:
                    sys.stderr.write(
                        u"One of the parameters you specified is not the proper type or it is out of boundaries. Quitting\n")
                    sys.exit(1)

            try:
                sys.stdout.write(
                    u"Generating Graph with small-world topology\nParameters:\nInitial lattice dimensions: {0}\nLattice size: {1}\nNei (number of edges that connect each graph): {2}\nRewiring probability: {3}\n".format(
                        self.args.lattice, self.args.lattice_size, self.args.nei, self.args.probability))
                graph = PyntacleGenerator.SmallWorld(
                    [self.args.lattice, self.args.lattice_size, self.args.nei, self.args.probability], name="SmallWorld", seed=self.args.seed)

            except(TypeError, ValueError):
                sys.stderr.write(
                    u"The parameters you chose were invalid. Please check your command line. Quitting\n")

        if graph.vcount() < 2 and graph.ecount() < 1:
            sys.stdout.write("Generated Graph is too small ({} nodes, {} edges). Re-run this command and tune your parameters. Quitting\n".format(graph.ecount(), graph.ecount()))
            sys.exit(1)

        sys.stdout.write(section_end)

        sys.stdout.write(report_start)

        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"WARNING: output directory does not exist {} will be created\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        if self.args.output_file is None:
            self.args.output_file = graph["name"][0]

        out_form = format_dictionary.get(self.args.output_format, "NA")
        if self.args.no_output_header:
            sys.stdout.write(u"Skipping header on output graph file\n")
            output_header = False

        else:
            output_header = True

        if out_form == "NA":
            sys.stderr.write(u"Output extension specified is not supported. Quitting\n")
            sys.exit(1)

        output_path = os.path.join(self.args.directory, ".".join([self.args.output_file, out_form]))
        sys.stdout.write(u"Path to graph : {}\n".format(output_path))

        if self.args.output_separator is None:
            sys.stdout.write(u"Using '\\t' as default separator for output file\n")
            self.args.output_separator = "\t"

        # output generated networks
        if out_form == "adjm":
            sys.stdout.write(u"Writing generated graph to an adjacency matrix\n")
            PyntacleExporter.AdjacencyMatrix(graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "egl":
            sys.stdout.write(u"Writing generated graph to an edge list\n")
            PyntacleExporter.EdgeList(graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "sif":
            sys.stdout.write(u"Writing generated graph to a Simple Interaction Format (SIF) file\n")
            PyntacleExporter.Sif(graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "dot":
            sys.stdout.write(u"Writing generated graph to a DOT file\n")

            # Ignore ugly RuntimeWarnings while creating a dot
            simplefilter("ignore", RuntimeWarning)
            PyntacleExporter.Dot(graph, output_path)

        elif out_form == "graph":
            sys.stdout.write(u"Writing generated graph to a binary file (ending in .graph)\n")
            PyntacleExporter.Binary(graph, output_path)

        if not self.args.no_plot and graph.vcount() < 5000:
            suffix = "_".join(graph["name"])
            sys.stdout.write(u"Plotting generated network in {} directory with PyntacleInk\n".format(self.args.directory))
            reporter = PyntacleReporter(graph=graph)
            reporter.pyntacleink_report(report_dir=self.args.directory, report_dict=None, suffix=suffix)

        elif graph.vcount() >= 5000:
            sys.stdout.write(
                u"The graph has too many nodes ({}). PyntacleInk allows plotting for network with N < 5000. No visual representation will be produced\n".format(
                    graph.vcount()))
        else:
            sys.stdout.write(pyntacleink_skip_msg)

        #todo arrivato qui
        #new plotting part (replaces old generator plot)

        # Check provided dimensions' format
        # if self.args.plot_dim:  # define custom format
        #     self.args.plot_dim = self.args.plot_dim.split(",")
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
        #
        # if not self.args.no_plot and graph.vcount() < 1000:
        #     sys.stdout.write(u"Drawing generated graph\n")
        #     # generates plot directory
        #     plot_dir = os.path.join(self.args.directory, "pyntacle-plots")
        #
        #     if not os.path.isdir(plot_dir):
        #         os.mkdir(plot_dir)
        #
        #     plot_path = os.path.join(plot_dir, ".".join([self.args.output_file, self.args.plot_format]))
        #
        #     pal = sns.color_palette("Spectral", 10).as_hex()
        #     pal2 = sns.color_palette("RdYlGn", 10).as_hex()
        #     framepal = sns.color_palette("Spectral", 10, desat=0.5).as_hex()
        #     framepal2 = sns.color_palette("RdYlGn", 10, desat=0.5).as_hex()
        #
        #     other_nodes_size = 18
        #
        #
        #     # deep sky blue
        #     plot_graph = PlotGraph(graph=graph)
        #
        #     # define layout according to the toplogy of the graph
        #     if self.args.which == "random":
        #         if self.args.plot_layout != "random":
        #             plot_graph.set_layouts(self.args.plot_layout)
        #         else:
        #             plot_graph.set_layouts(layout="random")
        #         other_nodes_colour = pal[-3]
        #         frame_vertex_colour = framepal[-3]
        #
        #     elif self.args.which == "scale-free":
        #         if self.args.plot_layout != "fr" and self.args.plot_layout != "fruchterman_reingold":
        #             plot_graph.set_layouts(self.args.plot_layout)
        #         else:
        #             plot_graph.set_layouts(layout="fr")
        #         other_nodes_colour = pal[3]
        #         frame_vertex_colour = framepal[3]
        #
        #     elif self.args.which == "tree":
        #         if self.args.plot_layout != "rt" and self.args.plot_layout != "reingold_tilford":
        #             plot_graph.set_layouts(self.args.plot_layout)
        #         else:
        #             plot_graph.set_layouts(layout="reingold_tilford")
        #         other_nodes_colour = pal2[-2]
        #         frame_vertex_colour = framepal2[-2]
        #
        #     else:
        #         if self.args.plot_layout != "circle":
        #             plot_graph.set_layouts(self.args.plot_layout)
        #         else:
        #             plot_graph.set_layouts(layout="circle")
        #         other_nodes_colour = pal[0]
        #         frame_vertex_colour = framepal[0]
        #
        #     node_colors = [other_nodes_colour] * graph.vcount()
        #     plot_graph.set_node_colors(colors=node_colors)
        #     plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph
        #     node_sizes = [other_nodes_size] * graph.vcount()
        #     plot_graph.set_node_sizes(sizes=node_sizes)
        #     frame_vertex_colour = [frame_vertex_colour]*graph.vcount()
        #
        #     sys.stdout.write(
        #         u"Drawing graph in {} format at path: {}\n".format(self.args.plot_format, plot_path))
        #
        #     plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2, keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=frame_vertex_colour)
        #
        # elif not self.args.no_plot and graph.vcount() >= 1000:
        #     self.logging.warning(
        #         u"Graph is above Pyntacle plotting capability ({} nodes, we plot graph with at best 1000 nodes). Graph plotting will be skipped.".format(
        #             graph.vcount()))

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(section_end)
        sys.stdout.write(u"Pyntacle generate completed successfully\n")
        if self.args.repeat == 1:
            sys.exit(0)
