from warnings import simplefilter

from exceptions.multiple_solutions_error import MultipleSolutionsError
from graph_operations.modules_finder import CommunityFinder
from io_stream.exporter import PyntacleExporter
from kp_tools.plotter import PlotGraph
from io_stream.import_attributes import ImportAttributes
from tools.modules_utils import ModuleUtils
from misc.graph_load import *
from tools.graph_utils import *

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


class Communities():
    """
    **[EXPAND]**
    """
    def __init__(self, args):
        self.logging = log
        self.args = args
        if not self.args.output_separator:
            self.args.output_separator = '\t'
        # Check for pycairo
        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write("WARNING: It seems that the pycairo library is not installed/available. Plots"
                             "will not be produced.")
            self.args.no_plot = True

    def run(self):
        cursor = CursorAnimation()
        cursor.daemon = True
        cursor.start()
        if not self.args.input_file:
            sys.stderr.write("ERROR: Input file is missing. Quitting\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stderr.write("ERROR: path {} does not exist. Quitting\n".format(self.args.input_file))
            sys.exit(1)

        input_header = True
        if self.args.no_header:
            input_header = False

        input_format =format_dictionary.get(self.args.format, "NA")

        graph = GraphLoad(self.args.input_file, file_format=input_format,
                          header=input_header).graph_load()

        # init Utils global stuff
        utils = GraphUtils(graph=graph)

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

        # initialize module finder method
        communities = CommunityFinder(graph=graph)
        # initialize ImportAttributes method
        attrs = ImportAttributes(graph=graph)

        # define plot sizes
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

        if self.args.which == "fastgreedy":
            if self.args.weights is not None:
                # import edge attributes
                if not os.path.exists(self.args.weights):
                    sys.stderr.write("Weights file {} does not exist. Quitting\n".format(self.args.weights))
                    sys.exit(1)

                else:
                    sep = separator_detect(self.args.weights)
                    try:
                        attrnames = attrs.import_edge_attributes(file_name=self.args.weight, sep=sep)
                        # get attribute name
                        if self.args.weights_name is None:
                            self.args.weights_name = attrnames[0]

                        else:
                            if self.args.weights_name not in graph.es.attributes():
                                sys.stderr(
                                    "weight Name {} was not imported into Graph, check your weights file. Quitting\n".format(
                                        self.args.weights_name))

                        # cast every weight to float
                        for i, weight in graph.es()[self.args.weights_name]:
                            try:
                                graph.es(i)[self.args.weights_name] = float(weight)
                            except:
                                self.logging.warning(
                                    "cannnot convert {} to float, replacing it with NoneType".format(weight))
                                graph.es(i)[self.args.weights_name] = None

                        graph.es()[self.args.weights_name] = [float(x) if x is not None else None for x in
                                                              graph.es()[self.args.weights_name]]

                    except:
                        sys.stderr.write(
                            "Something went wrong during the weights importing. See help and documentation. Quitting.\n")
                        sys.exit(1)
            else:
                self.args.weights_name = None

            if self.args.clusters is not None:
                try:
                    self.args.clusters = int(self.args.clusters)

                except:
                    sys.stderr.write("argument of \"--clusters\" must be an integer. Quitting\n")
                    sys.exit(1)

            sys.stdout.write("Running Community finding using fastgreedy algorithm\n")
            communities.fastgreedy(weights=self.args.weights_name, n=self.args.clusters)
            mods = communities.get_modules()
            algorithm = "fastgreedy"

        elif self.args.which == "infomap":
            sys.stdout.write("Running Community finding using infomap algorithm\n")
            communities.infomap()
            mods = communities.get_modules()
            algorithm = "infomap"

        elif self.args.which == "leading-eigenvector":
            sys.stdout.write("Running Community finding using leading-eigenvector algorithm\n")
            communities.leading_eigenvector()
            mods = communities.get_modules()
            algorithm = "leading-eigenvector"

        elif self.args.which == "community-walktrap":
            try:
                self.args.steps = int(self.args.steps)

            except:
                sys.stderr.write("Argument of \"--steps\" must be an integer. Quitting\n")
                sys.exit(1)

            if self.args.weights is not None:
                # import edge attributes
                if not os.path.exists(self.args.weights):
                    sys.stderr.write("Weights file {} does not exist. Quitting\n".format(self.args.weights))
                    sys.exit(1)

                else:
                    sep = separator_detect(self.args.weights)
                    try:
                        attrnames = attrs.import_edge_attributes(file_name=self.args.weight, sep=sep)
                        # get attribute name
                        if self.args.weights_name is None:
                            self.args.weights_name = attrnames[0]


                        else:
                            if self.args.weights_name not in graph.es.attributes():
                                sys.stderr(
                                    "weight Name {} was not imported into Graph, check your weights file. Quitting\n".format(
                                        self.args.weights_name))

                        # cast every weight to float
                        for i, weight in graph.es()[self.args.weights_name]:
                            try:
                                graph.es(i)[self.args.weights_name] = float(weight)
                            except:
                                self.logging.warning(
                                    "cannnot convert {} to float, replacing it with NoneType".format(weight))
                                graph.es(i)[self.args.weights_name] = None

                    except:
                        sys.stderr.write(
                            "Something went wrong during the weights importing. See help and documentation. Quitting.\n")
                        sys.exit(1)

                    graph.es()[self.args.weights_name] = [float(x) if x is not None else None for x in
                                                          graph.es()[self.args.weights_name]]

            if self.args.clusters is not None:
                try:
                    self.args.clusters = int(self.args.clusters)

                except:
                    sys.stderr.write("argument of \"--clusters\" must be an integer. Quitting\n")
                    sys.exit(1)

            sys.stdout.write(
                "Running Community finding using community walktrap algorithm at maximum {} steps\n".format(
                    self.args.steps))
            communities.community_walktrap(weights=self.args.weights_name, n=self.args.clusters,
                                           steps=self.args.steps)
            mods = communities.get_modules()
            algorithm = "community-walktrap"

        else:
            self.logging.critical("This should not happen. Please contact pyntacle Developers and send your "
                                  "command line, along with a log. Quitting\n.")
            sys.exit(1)

        mods_report = []
        for i, elem in enumerate(mods):
            mods_report.append(
                "\t".join([str(x) for x in [i, elem.vcount(), elem.ecount(), len(elem.components())]]) + "\n")

        sys.stdout.write(
            "pyntacle - Community Finding Report:\nalgorithm:{0}\nTotal number of Modules Found:"
            "\t{1}\nIndex\tNodes\tEdges \tComponents\n{2}".format(
                algorithm, len(mods), "".join(mods_report)))

        # initialize Moduleutils class
        mod_utils = ModuleUtils(graph=graph, algorithm=algorithm, modules=mods)
        mod_utils.add_modules_info()

        if not all(x is None for x in [self.args.min_nodes, self.args.max_nodes, self.args.min_components,
                                       self.args.max_components]):
            init_mods = len(mods)

            if self.args.min_nodes is not None:
                try:
                    self.args.min_nodes = int(self.args.min_nodes)

                except:
                    sys.stderr.write("argument of \"--min-set\" must be an integer. Quitting\n")
                    sys.exit(1)

            if self.args.max_nodes is not None:
                try:
                    self.args.max_nodes = int(self.args.max_nodes)

                except:
                    sys.stderr.write("argument of \"--max-set\" must be an integer. Quitting\n")
                    sys.exit(1)

            if self.args.max_components is not None:
                try:
                    self.args.max_components = int(self.args.max_components)

                except:
                    sys.stderr.write("argument of \"--max-components\" must be an integer. Quitting\n")
                    sys.exit(1)

            if self.args.min_components is not None:
                try:
                    self.args.min_components = int(self.args.min_components)

                except:
                    sys.stderr.write("argument of \"--min_components\" must be an integer. Quitting\n")
                    sys.exit(1)

            info = [x if x is not None else "NA" for x in
                    (self.args.min_nodes, self.args.max_nodes, self.args.max_components,
                     self.args.min_components)]
            sys.stdout.write(
                "Filtering Subgraphs according to your criteria:\nminimum number of nodes per modules: {0}\n"
                "maximum number of nodes per module: {1}\nminimum number of components: {2}\n"
                "maximum number of components: {3}\n".format(
                    *info))

            mod_utils.filter_subgraphs(min_nodes=self.args.min_nodes, max_nodes=self.args.max_nodes,
                                       min_components=self.args.min_components,
                                       max_components=self.args.max_components)
            sys.stdout.write("Filtered out {0} modules. Keeping {1} modules. Producing Output.\n".format(
                (len(mod_utils.modules) - init_mods), len(mod_utils.modules)))

        else:
            sys.stdout.write("No modules to filter. Proceeding to writing modules.\n")

        mod_utils.label_modules_in_graph()
        final_mods = mod_utils.get_modules()

        # producing output graph
        if self.args.no_output_header:
            sys.stdout.write("Not creating header on output files as you requested\n")
            output_header = False

        else:
            output_header = True

        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: Output directory does not exists, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        # dictionary that stores the extension of the output file
        if self.args.output_format is None:
            self.args.output_format = self.args.format

        out_form = format_dictionary.get(self.args.output_format, "NA")

        if self.args.output_file is None:
            # insert random name generator
            self.args.output_file = "_".join(["pyntacle", graph["name"][0], algorithm])
            sys.stdout.write(
                "output modules name not specified. Basename of the output modules will be {}\n".format(
                    self.args.output_file))

        output_basename = os.path.join(self.args.directory, self.args.output_file)

        # output generated networks
        if out_form == "adjm":
            sys.stdout.write("Creating Adjacency Matrix of each community\n")
            for i, elem in enumerate(final_mods):
                output_path = ".".join(["_".join([output_basename, str(i), datetime.datetime.now().strftime(
                    "%d%m%Y%H%M")]), out_form])
                PyntacleExporter.AdjacencyMatrix(elem, output_path, sep=self.args.output_separator,
                                         header=output_header)

        elif out_form == "egl":
            sys.stdout.write("Creating Edge List of each final community\n")
            for i, elem in enumerate(final_mods):
                output_path = ".".join(["_".join([output_basename, str(i), datetime.datetime.now().strftime(
                    "%d%m%Y%H%M")]), out_form])
                PyntacleExporter.EdgeList(elem, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "sif":
            sys.stdout.write("Creating Simple Interaction File of each final community\n")
            for i, elem in enumerate(final_mods):
                output_path = ".".join(["_".join([output_basename, str(i), datetime.datetime.now().strftime(
                    "%d%m%Y%H%M")]), out_form])
                PyntacleExporter.Sif(elem, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "dot":
            sys.stdout.write("Creating DOT File of the each final community\n")
            for i, elem in enumerate(final_mods):
                output_path = ".".join(["_".join([output_basename, str(i), datetime.datetime.now().strftime(
                    "%d%m%Y%H%M")]), out_form])

                # Ignore ugly RuntimeWarnings while creating a dot
                simplefilter("ignore", RuntimeWarning)
                PyntacleExporter.Dot(elem, output_path)

        elif out_form == "bin":
            sys.stdout.write("Storing each community into a .graph (binary) file\n")
            for i, elem in enumerate(final_mods):
                output_path = ".".join(["_".join([output_basename, str(i), datetime.datetime.now().strftime(
                    "%d%m%Y%H%M")]), out_form])
                PyntacleExporter.Binary(elem, output_path)

        # save the original graph into a binary file
        if self.args.save_binary:
            binary_name = ".".join(["pyntacle_communities", "graph"])
            binary_path = os.path.join(self.args.directory, binary_name)
            sys.stdout.write(
                "Storing the input graph with module labels into .graph file at path {}\n".format(
                    binary_path))

        if not self.args.no_plot:

            plot_dir = os.path.join(self.args.directory, "pyntacle-Plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    "A directory named \"pyntacle-Plots\" already exists, I may overwrite something in there")

            else:
                os.mkdir(plot_dir)

            avail_colours_fill = sns.color_palette("Spectral", n_colors=len(
                final_mods)).as_hex()  # available colours for node fill
            avail_colours_borders = sns.color_palette("Spectral", n_colors=len(final_mods),
                                                      desat=0.5).as_hex()

            if graph.vcount() < 1000:

                sys.stdout.write("Generating plots in {} format.\n".format(self.args.plot_format))

                main_plot_path = os.path.join(plot_dir, ".".join(["_".join(
                    ["pyntacle", os.path.splitext(os.path.basename(self.args.input_file))[0], "modules",
                     runtime_date]), self.args.plot_format]))

                # initialize general graph Drawer
                sys.stdout.write("Drawing Original Graph with corresponding modules\n")
                graph_plotter = PlotGraph(graph=graph)
                graph_plotter.set_node_label(labels=graph.vs()["name"])
                graph_plotter.set_node_sizes([30] * graph.vcount())

                # define different colours for each module
                not_in_module_colours = "#A9A9A9"
                col_list = []
                bord_list = []
                for elem in graph.vs():
                    module = elem["__module"]
                    if module is not None:
                        col_list.append(avail_colours_fill[module])
                        bord_list.append(avail_colours_borders[module])

                    else:
                        col_list.append(not_in_module_colours)
                        bord_list.append(not_in_module_colours)

                graph_plotter.set_node_colours(col_list)
                graph_plotter.set_layouts()
                graph_plotter.plot_graph(path=main_plot_path, bbox=plot_size, margin=20, edge_curved=True,
                                         keep_aspect_ratio=True, vertex_label_size=8,
                                         vertex_frame_color=bord_list)
            else:
                sys.stdout.write(
                    "Input Graph is above pyntacle Plotting limits ({} nodes, we support 1000 nodes). Will skip plotting this module.\n".format(
                        graph.vcount()))

            if len(final_mods) > 20:
                self.logging.warning(
                    "The number of modules ({}) is very high, hence the node colours of each module may be very similar".format(
                        len(final_mods)))

            sys.stdout.write("Drawing Each Module Separately\n")

            for i, comm in enumerate(final_mods):
                if comm.vcount() <= 1000:
                    plotter = PlotGraph(graph=comm)
                    plotter.set_node_label(labels=comm.vs()["name"])

                    plotter.set_node_colours([avail_colours_fill[i]] * comm.vcount())

                    plotter.set_node_sizes([30] * comm.vcount())

                    comm_plot_path = os.path.join(plot_dir, ".".join(
                        ["_".join([self.args.output_file, str(i), datetime.datetime.now().strftime(
                            "%d%m%Y%H%M")]), self.args.plot_format]))

                    plotter.set_layouts()
                    plotter.plot_graph(path=comm_plot_path, bbox=plot_size, margin=20, edge_curved=True,
                                       keep_aspect_ratio=True, vertex_label_size=8,
                                       vertex_frame_color=[avail_colours_borders[i]] * comm.vcount())

                else:
                    sys.stdout.write(
                        "Module {0} is above pyntacle Plotting limits ({1} nodes , we support 1000 nodes). Will skip plotting this module.\n".format(
                            i, comm.vcount()))
        cursor.stop()
        sys.stdout.write("Community Finding completed successfully. Ending\n")
        sys.exit(0)
