__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.4"
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

from config import *
from exceptions.generic_error import Error
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.illegal_argument_number_error import IllegalArgumentNumberError
from io_stream.generator import *
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import *
from warnings import simplefilter

class Generate():
    def __init__(self, args):
        self.logging = log
        self.args = None
        self.args = args
        if self.args.seed:
            random.seed(self.args.seed)

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if self.args.which == "random":

            if self.args.nodes is None:
                self.args.nodes = random.randint(100, 500)
            else:
                try:
                    self.args.nodes = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write("Number of nodes must be a positive integer. Quitting\n")
                    sys.exit(1)

            if not self.args.probability and self.args.edges:

                try:
                    self.args.edges = int(self.args.edges)
                    "Generating Graph with Scale Random Topology\nParameters:\nNumber of Nodes: {0}\nNumber of Edges: {1}\n".format(
                        self.args.nodes, self.args.edges)
                    
                    graph = Generator.Random([self.args.nodes, self.args.edges], name="Random", seed=self.args.seed)

                except (ValueError, TypeError, IllegalGraphSizeError):
                    sys.stderr.write(
                        "Number of nodes must be a positive integer greater than 2 and number of edges must be a positive integer greater than zero. Quitting\n")
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
                        sys.stderr.write("Probability must be a float between 0 and 1. Quitting.")

                try:
                    sys.stdout.write(
                        "Generating Graph with Random Topology\nParameters:\nNumber of Nodes: {0}\nProbability of wiring: {1}\n".format(
                            self.args.nodes, self.args.probability))
                    graph = Generator.Random([self.args.nodes, self.args.probability], name="Random", seed=self.args.seed)

                except (ValueError, TypeError, IllegalGraphSizeError):
                    sys.stderr.write(
                        "Number of nodes must be a positive integer greater than 2 and a probability must be a float between 0 and 1. Quitting\n")
                    sys.exit(1)
                
        elif self.args.which == "scale-free":
            if self.args.nodes is None:
                self.args.nodes = random.randint(100, 500)

            else:
                try:
                    self.args.nodes = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write("Number of nodes must be a positive integer. Quitting\n")
                    sys.exit(1)

            if self.args.avg_edges is None:
                self.args.avg_edges = random.randint(10, 100)

            else:
                try:
                    self.args.avg_edges = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write("Number of outgoing edges must be a positive integer. Quitting\n")
                    sys.exit(1)

            try:
                sys.stdout.write(
                    "Generating Graph with Scale Free Topology\nParameters:\nNumber of Nodes: {0}\nNumber of Outging edges: {1}\n".format(
                        self.args.nodes, self.args.avg_edges))
                graph = Generator.ScaleFree([self.args.nodes, self.args.avg_edges], name="ScaleFree", seed=self.args.seed)

            except (ValueError, TypeError, IllegalGraphSizeError):
                sys.stderr.write(
                    "Number of nodes  and number of outgoing edges must be positive integersmust be a positive integer. Quitting\n")
                sys.exit(1)

        elif self.args.which == "tree":

            if self.args.nodes is None:
                self.args.nodes = random.randint(100, 500)

            else:
                try:
                    self.args.nodes = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write("Number of nodes must be a positive integer. Quitting\n")
                    sys.exit(1)

            if self.args.children is None:
                self.args.children = random.randint(2, 10)

            else:
                try:
                    self.args.children = int(self.args.nodes)

                except ValueError:
                    sys.stderr.write("Number of children must be a positive integer. Quitting\n")
                    sys.exit(1)

            try:
                sys.stdout.write(
                    "Generating Graph with Tree Topology\nParameters:\nNumber of Nodes: {0}\nChildren per Node: {1}\n".format(
                        self.args.nodes, self.args.children))
                graph = Generator.Tree([self.args.nodes, self.args.children], name="Tree", seed=self.args.seed)

            except (ValueError, TypeError, IllegalGraphSizeError):
                sys.stderr.write(
                    "Number of nodes and number of children must be positive integersmust be a positive integer. Quitting\n")
                sys.exit(1)

        elif self.args.which == "small-world":
            
            #This does not happen anymore, as default is 2.
            if not self.args.lattice_size:
                self.args.lattice_size = random.randint(2, 5)
                
            if not self.args.nei:
                self.args.nei = random.randint(1, 5)

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
                        "ERROR: One of the parameters you specified is not the proper type or it is out of boundaries. Quitting\n")
                    sys.exit(1)

            try:
                sys.stdout.write(
                    "Generating Graph with Small World Topology\nParameters:\nLattice Dimensions: {0}\nLattice Size: {1}\nNei (number of edges that connect each graph): {2}\nRewiring Probability: {3}\n".format(
                        self.args.lattice, self.args.lattice_size, self.args.nei, self.args.probability))
                graph = Generator.SmallWorld(
                    [self.args.lattice, self.args.lattice_size, self.args.nei, self.args.probability], name="SmallWorld", seed=self.args.seed)

            except(TypeError, ValueError, IllegalArgumentNumberError):
                sys.stderr.write(
                    "ERROR : The parameters you chose were invalid. Please check your command line. Quitting.\n")

        else:
            raise Error("This should not appear. Contact pyntacle Developer for Debugging")

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
                
        if self.args.no_output_header:
            sys.stdout.write("Not outputting header as you requested\n")
            output_header = False

        else:
            output_header = True

        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: Output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        if self.args.output_file is None:
            self.args.output_file = graph["name"][0]

        out_form = format_dictionary.get(self.args.output_format, "NA")

        if out_form == "NA":
            sys.stderr.write("Output extension specified is not supported, see  \"--help\" for more info\n. Quitting")
            sys.exit(1)

        output_path = os.path.join(self.args.directory, ".".join([self.args.output_file, out_form]))
        sys.stdout.write("Path to generated Graph is: {}\n".format(output_path))

        if self.args.output_separator is None:
            sys.stdout.write("Using \"\\t\" as default separator for output file\n")
            self.args.output_separator = "\t"

        if os.path.exists(output_path):
            self.logging.warning("A file named {} already exist, I will overwrite it".format(output_path))

        # output generated networks
        if out_form == "adjm":
            sys.stdout.write("Creating Adjacency Matrix of the generated graph\n")
            PyntacleExporter.AdjacencyMatrix(graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "egl":
            sys.stdout.write("Creating Edge List of the generated graph\n")
            PyntacleExporter.EdgeList(graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "sif":
            sys.stdout.write("Creating Simple Interaction File of the generated graph\n")
            PyntacleExporter.Sif(graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "dot":
            sys.stdout.write("Creating DOT File of the generated graph\n")

            # Ignore ugly RuntimeWarnings while creating a dot
            simplefilter("ignore", RuntimeWarning)
            PyntacleExporter.Dot(graph, output_path)

        elif out_form == "graph":
            sys.stdout.write("Storing the created graph into a .graph (binary) file\n")
            PyntacleExporter.Binary(graph, output_path)

        if not self.args.no_plot and graph.vcount() < 1000:
            sys.stdout.write("Drawing Generated Graph\n")
            # generates plot directory
            plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    "A directory named \"pyntacle-plots\" already exist, I may overwrite something in there")

            else:
                os.mkdir(plot_dir)

            plot_path = os.path.join(plot_dir, ".".join([self.args.output_file, self.args.plot_format]))

            pal = sns.color_palette("Spectral", 10).as_hex()
            pal2 = sns.color_palette("RdYlGn", 10).as_hex()
            framepal = sns.color_palette("Spectral", 10, desat=0.5).as_hex()
            framepal2 = sns.color_palette("RdYlGn", 10, desat=0.5).as_hex()

            other_nodes_size = 18


            # deep sky blue
            plot_graph = PlotGraph(graph=graph)

            # define layout according to the toplogy of the graph
            if self.args.which == "random":
                if self.args.plot_layout != "random":
                    plot_graph.set_layouts(self.args.plot_layout)
                else:
                    plot_graph.set_layouts(layout="random")
                other_nodes_colour = pal[-3]
                frame_vertex_colour = framepal[-3]

            elif self.args.which == "scale-free":
                if self.args.plot_layout != "fr" and self.args.plot_layout != "fruchterman_reingold":
                    plot_graph.set_layouts(self.args.plot_layout)
                else:
                    plot_graph.set_layouts(layout="fr")
                other_nodes_colour = pal[3]
                frame_vertex_colour = framepal[3]

            elif self.args.which == "tree":
                if self.args.plot_layout != "rt" and self.args.plot_layout != "reingold_tilford":
                    plot_graph.set_layouts(self.args.plot_layout)
                else:
                    plot_graph.set_layouts(layout="reingold_tilford")
                other_nodes_colour = pal2[-2]
                frame_vertex_colour = framepal2[-2]

            else:
                if self.args.plot_layout != "circle":
                    plot_graph.set_layouts(self.args.plot_layout)
                else:
                    plot_graph.set_layouts(layout="circle")
                other_nodes_colour = pal[0]
                frame_vertex_colour = framepal[0]

            node_colors = [other_nodes_colour] * graph.vcount()
            plot_graph.set_node_colors(colors=node_colors)
            plot_graph.set_node_labels(labels=graph.vs()["name"])  # assign node labels to graph
            node_sizes = [other_nodes_size] * graph.vcount()
            plot_graph.set_node_sizes(sizes=node_sizes)
            frame_vertex_colour = [frame_vertex_colour]*graph.vcount()

            sys.stdout.write(
                "Drawing graph in {} format at path: {}\n".format(self.args.plot_format, plot_path))

            if os.path.exists(plot_path):
                self.logging.warning(
                    "A path with the same name already exist. I will overwrite current drawing")

            plot_graph.plot_graph(path=plot_path, bbox=plot_size, margin=20, edge_curved=0.2, keep_aspect_ratio=True, vertex_label_size=6, vertex_frame_color=frame_vertex_colour)

        elif not self.args.no_plot and graph.vcount() >= 1000:
            self.logging.warning(
                "Graph ({} nodes) exceeds pyntacle limits for plotting (maximum 1000 nodes). Will not draw Graph".format(
                    graph.vcount()))
            sys.exit(0)

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write("pyntacle Generate completed successfully.\n")
        if self.args.repeat == 1:
            sys.exit(0)
