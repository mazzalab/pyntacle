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

from config import *
import filecmp
from warnings import simplefilter
from exceptions.multiple_solutions_error import MultipleSolutionsError
from graph_operations.logic_ops import GraphSetter
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import PlotGraph
from cmds.cmds_utils.reporter import *
from tools.misc.enums import Reports
from tools.misc.graph_load import *

class Set():
    """
    **[EXPAND]**
    """
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date

        # Check for pycairo
        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write("WARNING: It seems that the pycairo library is not installed/available. Plots"
                             "will not be produced.")
            self.args.no_plot = True

    def run(self):
        # process input files
        cursor = CursorAnimation()
        cursor.daemon = True
        cursor.start()
        if not self.args.input_file_1 or not self.args.input_file_2:
            sys.stderr.write("ERROR: one of the two input files is missing. Quitting\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file_1) or not os.path.exists(self.args.input_file_2):
            sys.stderr.write("ERROR: one of the two input files does not exist. Quitting\n")
            sys.exit(1)

        if filecmp.cmp(self.args.input_file_1, self.args.input_file_2, shallow=False):
            sys.stderr.write("ERROR: The two input files are equal\n")
            sys.exit(1)

        input_header = True
        if self.args.no_header:
            input_header = False

        input_format = format_dictionary.get(self.args.format, "NA")

        graph1 = GraphLoad(self.args.input_file_1, file_format=input_format,
                           header=input_header).graph_load

        graph2 = GraphLoad(self.args.input_file_2, file_format=input_format,
                           header=input_header).graph_load

        # init Utils global stuff
        utils1 = GraphUtils(graph=graph1)
        utils2 = GraphUtils(graph=graph2)

        if self.args.largest_component:
            try:
                graph1 = utils1.get_largest_component()
                sys.stdout.write(
                    "Taking the largest component of the input graph {0} as you requested ({1} nodes, {2} edges)\n".format(graph2["name"],
                        graph1.vcount(), graph1.ecount()))

            except MultipleSolutionsError:
                sys.stderr.write(
                    "Graph {} has two largest components of the same size. Cannot choose one. Please parse your file or remove the \"--largest-component\" option. Quitting\n".format(graph1["name"]))
                sys.exit(1)

            try:
                graph2 = utils2.get_largest_component()
                sys.stdout.write(
                    "Taking the largest component of the input graph {0} as you requested ({1} nodes, {2} edges)\n".format(
                        graph2["name"],graph2.vcount(), graph2.ecount()))

            except MultipleSolutionsError:
                sys.stderr.write(
                    "Graph {} has two largest components of the same size. Cannot choose one. Please parse your file or remove the \"--largest-component\" option. Quitting\n".format(
                        graph2["name"]))
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
            if graph1.vcount() <= 150 and graph2.vcount() <= 150:
                plot_size = (800, 800)

            else:
                plot_size = (1600, 1600)

        if self.args.format == "sif" or all(x is None for x in graph1.es()["__sif_interaction"]) or all(
                        x is None for x in graph2.es()["__sif_interaction"]):
            sys.stdout.write("WARNING. Interaction stored in SIF files will be removed\n")

        if self.args.output_file is None:
            if self.args.which == "union":

                self.args.output_file = "_".join \
                    ([os.path.splitext(os.path.basename(self.args.input_file_1))[0], "UNION",
                      os.path.splitext(os.path.basename(self.args.input_file_2))[0],
                      self.date])

            elif self.args.which == "intersection":
                self.args.output_file = "_".join \
                    ([os.path.splitext(os.path.basename(self.args.input_file_1))[0], "INTERSECTION",
                      os.path.splitext(os.path.basename(self.args.input_file_2))[0],
                      self.date])

            elif self.args.which == "difference":

                self.args.output_file = "_".join(
                    [os.path.splitext(os.path.basename(self.args.input_file_1))[0], "DIFFERENCE",
                     os.path.splitext(os.path.basename(self.args.input_file_2))[0],
                     self.date])
            else:
                self.logging.critical(
                    "This should not happen. Please contact pyntacle developers and send a log of the error.\nQuitting.")
                sys.exit(1)

            sys.stdout.write("basename of output graph: {}\n".format(self.args.output_file))

        # initialize set class
        setter = GraphSetter(graph1=graph1, graph2=graph2, new_name=self.args.output_file)

        # NOT prefixing the argument with -- means it's not optional

        # GraphSetter(graph1=graph1, graph2=graph2,new_name = new_name
        
        if self.args.which == "union":
            sys.stdout.write(
                "Running pyntacle Union on input graph {} and  {}\n".format(self.args.input_file_1,
                                                                           self.args.input_file_2))

            output_graph = setter.union()

            if all(len(x) <= 2 for x in output_graph.vs()["__parent"]):
                sys.stdout.write(
                    "There were no common nodes when performing Graph union. Will return Two disjointed graphs.\n")

        elif self.args.which == "intersection":
            sys.stdout.write(
                "Running pyntacle Intersection on input graph {} and  {}\n".format(self.args.input_file_1,
                                                                                  self.args.input_file_2))

            output_graph = setter.intersection()

            if output_graph.ecount() == 0:
                sys.stdout.write(
                    "No intersection was possible for the two input graphs. No output will be generated\n")
                sys.exit(0)

        elif self.args.which == "difference":
            sys.stdout.write(
                "Running pyntacle Difference on input graph {} and  {}\n".format(self.args.input_file_1,
                                                                                  self.args.input_file_2))

            output_graph = setter.difference()
            if output_graph.vcount() == graph1.vcount() and output_graph.ecount() == graph1.ecount():
                sys.stdout.write("Nothing of graph {} could be subtracted from graph {}\n".format(
                    os.path.basename(self.args.input_file_1), os.path.basename(self.args.input_file_2)))

        else:
            self.logging.critical(
                "This should not happen. Please contact pyntacle developer and send a command line, along with a log. Quitting\n")
            sys.exit(1)


        # print pyntacle_commands_utils to command line
        sys.stdout.write("pyntacle Report on set Operation: {}\n".format(self.args.which))
        sys.stdout.write("Input Graphs\n")

        sys.stdout.write(
            "Graph ---{0}---\nNodes:\t{1}\nEdges:\t{2}\nComponents:\t{3}\n".format(graph1["name"][0], graph1.vcount(),
                                                                                   graph1.ecount(),
                                                                                   len(graph1.components())))
        sys.stdout.write(
            "Graph ---{0}---\nNodes:\t{1}\nEdges:\t{2}\nComponents:\t{3}\n".format(graph2["name"][0], graph2.vcount(),
                                                                                   graph2.ecount(),
                                                                                   len(graph2.components())))

        sys.stdout.write("\nResulting Graph\n")
        sys.stdout.write("Nodes:\t{0}\nEdges:\t{1}\nComponents:\t{2}\n".format(output_graph.vcount(),
                                                                               output_graph.ecount(),
                                                                               len(output_graph.components())))

        # producing output graph
        if self.args.no_output_header:
            sys.stdout.write("Not creating header on output file as you requested\n")
            output_header = False

        else:
            output_header = True

        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: Output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        out_form = format_dictionary.get(self.args.output_format, "NA")
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
            PyntacleExporter.AdjacencyMatrix(output_graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "egl":
            sys.stdout.write("Creating Edge List of the generated graph\n")
            PyntacleExporter.EdgeList(output_graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "sif":
            sys.stdout.write("Creating Simple Interaction File of the generated graph\n")
            PyntacleExporter.Sif(output_graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "dot":
            sys.stdout.write("Creating DOT File of the generated graph\n")

            # Ignore ugly RuntimeWarnings while creating a dot
            simplefilter("ignore", RuntimeWarning)
            PyntacleExporter.Dot(output_graph, output_path)

        elif out_form == "bin":
            sys.stdout.write("Storing the created graph into a .graph (binary) file\n")
            PyntacleExporter.Binary(output_graph, output_path)

        sys.stdout.write(
            "Path to the output graph after set operation: {}\n".format(os.path.abspath(output_path)))

        # producing plots
        if not self.args.no_plot:
            # generates plot directory
            plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    "A directory named \"pyntacle-plots\" already exists, I may overwrite something in there")

            else:
                os.mkdir(plot_dir)
            sys.stdout.write("Generating plots in {} format.\n".format(self.args.plot_format))
            sys.stdout.write("Drawing Starting Graphs\n")

            graph1_plot_path = os.path.join(plot_dir, ".".join(
                ["_".join([os.path.splitext(os.path.basename(self.args.input_file_1))[0],
                           self.date]), self.args.plot_format]))
            graph2_plot_path = os.path.join(plot_dir, ".".join(
                ["_".join([os.path.splitext(os.path.basename(self.args.input_file_2))[0],
                           self.date]), self.args.plot_format]))

            graph1_plotter = PlotGraph(graph=graph1)
            graph2_plotter = PlotGraph(graph=graph2)

            # first create two plots of the input graph
            input_graph_node_size = 25

            pal = sns.color_palette("hls", 10).as_hex()
            framepal = sns.color_palette("hls", 10, desat=0.5).as_hex()

            graph_1_colour = pal[0]
            graph_1_frame = framepal[0]
            graph_2_colour = pal[3]
            graph_2_frame = framepal[3]

            # set input graph node labels
            graph1_plotter.set_node_labels(labels=graph1.vs()["name"])
            graph2_plotter.set_node_labels(labels=graph2.vs()["name"])

            # set input graph node colors
            graph1_plotter.set_node_colors(colors=[graph_1_colour] * graph1.vcount())
            graph2_plotter.set_node_colors(colors=[graph_2_colour] * graph2.vcount())

            # set input graphs node sizes
            graph1_plotter.set_node_sizes(sizes=[input_graph_node_size] * graph1.vcount())
            graph2_plotter.set_node_sizes(sizes=[input_graph_node_size] * graph2.vcount())

            # set input graph vertex colors
            graph_1_frame_colors = [graph_1_frame] * graph1.vcount()
            graph_2_frame_colors = [graph_2_frame] * graph1.vcount()

            # define layouts
            graph1_plotter.set_layouts()
            graph2_plotter.set_layouts()

            # plot input graphs
            graph1_plotter.plot_graph(path=graph1_plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6,
                                      vertex_frame_color=graph_1_frame_colors)
            graph2_plotter.plot_graph(path=graph2_plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                      keep_aspect_ratio=True, vertex_label_size=6,
                                      vertex_frame_color=graph_2_frame_colors)

            if output_graph.vcount() > 0:

                # plot output graph
                output_plot_path = os.path.join(plot_dir,
                                                ".".join(["_".join(["pyntacle", self.args.output_file,
                                                                    self.date]),
                                                          self.args.plot_format]))
                output_graph_plotter = PlotGraph(graph=output_graph)  # init plotter class

                # for the merge part
                sys.stdout.write("Drawing Resulting Graph\n")
                node_intersection_colour = pal[1]
                node_intersection_frame = framepal[1]

                node_intersection_size = 45

                intersection_node_color_list = []
                intersection_frame_color_list = []

                intersection_set = []
                for v in output_graph.vs():
                    parent_g1 = graph1["name"][0]
                    parent_g2 = graph2["name"][0]

                    if parent_g1 in v["__parent"] and parent_g2 in v["__parent"]:
                        intersection_node_color_list.append(node_intersection_colour)
                        intersection_frame_color_list.append(node_intersection_frame)
                        intersection_set.append(v["name"])
                        
                    elif parent_g1 in v["__parent"] and not parent_g2 in v["__parent"]:
                        intersection_node_color_list.append(graph_1_colour)
                        intersection_frame_color_list.append(graph_1_frame)

                    elif parent_g2 in v["__parent"] and not parent_g1 in v["__parent"]:
                        intersection_node_color_list.append(graph_2_colour)
                        intersection_frame_color_list.append(graph_2_frame)


                output_graph_plotter.set_node_colors(colors=intersection_node_color_list)
                output_graph_plotter.set_node_sizes(sizes=[
                    node_intersection_size if parent_g1 in v["__parent"] and parent_g2 in v[
                        "__parent"] else input_graph_node_size for v in output_graph.vs()])

                output_graph_plotter.set_node_labels(labels=output_graph.vs()["name"])
                output_graph_plotter.set_layouts()
                output_graph_plotter.plot_graph(path=output_plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                                keep_aspect_ratio=True, vertex_label_size=6,
                                                vertex_frame_color=intersection_frame_color_list)

            else:
                sys.stdout.write("The output graph does not contain vertices. Can't draw graph\n")

        elif not self.args.no_plot and (graph1.vcount() >= 1000 or graph2.vcount() >= 1000):
            self.logging.warning(
                "One of the two input Graphs exceeds pyntacle limits for plotting (maximum 1000 nodes). Will not draw Graph")
        
        
        # Report
        reporter1 = pyntacleReporter(graph=graph1)  # init reporter1
        reporter2 = pyntacleReporter(graph=graph2)  # init reporter2
        reporter_final = pyntacleReporter(graph=output_graph)
        
        set1_attr_dict = OrderedDict()
        set2_attr_dict = OrderedDict()
        setF_attr_dict = OrderedDict()

        if self.args.which == 'intersection':
            setF_attr_dict['\nCommon Nodes'] = 'Node names'#(len(intersection_set), ','.join(intersection_set))
            setF_attr_dict[len(intersection_set)] = ','.join(intersection_set)
        reporter1.create_report(Reports.Set, set1_attr_dict)
        reporter2.create_report(Reports.Set, set2_attr_dict)
        reporter_final.create_report(Reports.Set, setF_attr_dict)
        
        reporter1.report[1] = ['\n--- Graph 1 ---']
        reporter2.report[1] = ['--- Graph 2 ---']
        del(reporter1.report[-1])
        del(reporter2.report[-1])
        del(reporter2.report[0])
        del(reporter_final.report[0])
        for e in reporter_final.report:
            if e[0] == 'Pyntacle Command:':
                e[1] = e[1] + ' ' + self.args.which
        
        reporter_final.report[0] = ['\n--- Resulting Graph ---']
        reporter1.report.extend(reporter2.report)
        reporter1.report.extend(reporter_final.report)
        reporter1.write_report(report_dir=self.args.directory, format=self.args.report_format)
        cursor.stop()
        sys.stdout.write("pyntacle Set completed successfully\n")
        sys.exit(0)
