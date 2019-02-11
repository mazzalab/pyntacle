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
from collections import OrderedDict
from warnings import simplefilter
from graph_operations.communities import CommunityFinder, ModuleUtils
from io_stream.import_attributes import ImportAttributes
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import PlotGraph
from cmds.cmds_utils.reporter import PyntacleReporter
from tools.graph_utils import *
from tools.enums import ReportEnum
from internal.graph_load import GraphLoad, separator_detect
from exceptions.generic_error import Error


class Communities():
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date
        if not hasattr(self.args, 'which'):
            raise Error(
                u"usage: pyntacle.py communities{infomap, community-walktrap, fastgreedy, leading-eigenvector} [options]'")
        # Check for pycairo
        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write(u"Warning: It seems that the pycairo library is not installed/available. Graph plot(s)"
                             "will not be produced.\n")
            self.args.no_plot = True

        if not self.args.output_separator:
            self.args.output_separator = '\t'

    def run(self):

        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stderr.write(u"Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit(1)

        input_header = True
        if self.args.no_header:
            input_header = False

        input_format = format_dictionary.get(self.args.format, "NA")

        sys.stdout.write(u"Importing graph from file...\n")
        graph = GraphLoad(self.args.input_file, file_format=input_format,
                          header=input_header, separator=self.args.input_separator).graph_load()

        # init Utils global stuff
        utils = GraphUtils(graph=graph)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph as you requested ({} nodes, {} edges).\n".format(
                        graph.vcount(), graph.ecount()))
                utils.set_graph(graph)


            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting.\n")
                sys.exit(1)

        # initialize module finder method
        communities = CommunityFinder(graph=graph)
        # initialize Reporter
        r = PyntacleReporter(graph=graph)
        report_type = ReportEnum.Communities
        results = OrderedDict()
        results["algorithm"] = self.args.which

        # define plot sizes
        if self.args.plot_dim:  # define custom format
            self.args.plot_dim = self.args.plot_dim.split(",")

            for i in range(0, len(self.args.plot_dim)):
                try:
                    self.args.plot_dim[i] = int(self.args.plot_dim[i])

                except ValueError:
                    sys.stderr.write(
                        u"Format specified must be a comma separated list of values(e.g. 1920,1080). Quitting.\n")
                    sys.exit(1)

                if self.args.plot_dim[i] <= 0:
                    sys.stderr.write(
                        u"Format specified must be a comma separated list of values(e.g. 1920,1080). Quitting.\n")
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
                    sys.stderr.write(u"Attribute file {} does not exist. Quitting\n".format(self.args.weights))
                    sys.exit(1)

                else:
                    ImportAttributes.import_edge_attributes(graph, self.args.weights,
                                                            sep=separator_detect(self.args.weights),
                                                            mode=self.args.weights_format)
                    weights = [float(x) if x != None else 1.0 for x in graph.es()["weights"]]

            else:
                weights = None

            if self.args.clusters is not None:
                try:
                    self.args.clusters = int(self.args.clusters)

                except:
                    sys.stderr.write(u"argument of '--clusters' must be an integer. Quitting.\n")
                    sys.exit(1)

            sys.stdout.write(u"Running community-finding using the fastgreedy algorithm...\n")
            communities.fastgreedy(weights=weights, n=self.args.clusters)
            mods = communities.get_modules
            algorithm = "fastgreedy"

        elif self.args.which == "infomap":
            sys.stdout.write(u"Running community-finding using the infomap algorithm...\n")
            communities.infomap()
            mods = communities.get_modules
            algorithm = "infomap"

        elif self.args.which == "leading-eigenvector":
            sys.stdout.write(u"Running community-finding using the leading-eigenvector algorithm...\n")
            communities.leading_eigenvector()
            mods = communities.get_modules
            algorithm = "leading-eigenvector"

        elif self.args.which == "community-walktrap":
            try:
                self.args.steps = int(self.args.steps)

            except:
                sys.stderr.write(u"Argument of '--steps' must be an integer. Quitting.\n")
                sys.exit(1)

            if self.args.weights is not None:
                # import edge attributes
                if not os.path.exists(self.args.weights):
                    sys.stderr.write(u"Weights file {} does not exist. Quitting.\n".format(self.args.weights))
                    sys.exit(1)

                else:
                    ImportAttributes.import_edge_attributes(graph, self.args.weights,
                                                            sep=separator_detect(self.args.weights),
                                                            mode=self.args.weights_format)
                    weights = [float(x) if x != None else 1.0 for x in graph.es()["weights"]]

            else:
                weights = None

            if self.args.clusters is not None:
                try:
                    self.args.clusters = int(self.args.clusters)

                except:
                    sys.stderr.write(u"Argument of '--clusters' must be an integer. Quitting.\n")
                    sys.exit(1)

            sys.stdout.write(
                u"Running community-finding using the community walktrap algorithm at maximum {} steps.\n".format(
                    self.args.steps))
            communities.community_walktrap(weights=weights, n=self.args.clusters,
                                           steps=self.args.steps)
            mods = communities.get_modules
            algorithm = "community-walktrap"

        else:
            sys.stderr.write(u"This should not happen. Please contact Pyntacle developers and send your "
                             "command line, along with a log. Quitting.\n")
            sys.exit(1)

        mods_report = []
        if not mods:
            sys.stderr.write(u"No communities found. Quitting.")
            sys.exit(1)
        for i, elem in enumerate(mods):
            mods_report.append(
                "\t".join([str(x) for x in [i, elem.vcount(), elem.ecount(), len(elem.components())]]) + "\n")

        sys.stdout.write(
            u"Pyntacle - Community finding report:\nAlgorithm:{0}\nTotal number of communities found:"
            "\t{1}\nIndex\tNodes\tEdges \tComponents\n{2}".format(
                algorithm, len(mods), "".join(mods_report)))

        # initialize Moduleutils class
        mod_utils = ModuleUtils(modules=mods)

        if not all(x is None for x in [self.args.min_nodes, self.args.max_nodes, self.args.min_components,
                                       self.args.max_components]):
            init_mods = len(mods)

            if self.args.min_nodes is not None:
                try:
                    self.args.min_nodes = int(self.args.min_nodes)

                except:
                    sys.stderr.write(u"Argument of '--min-nodes' must be an integer. Quitting.\n")
                    sys.exit(1)

            if self.args.max_nodes is not None:
                try:
                    self.args.max_nodes = int(self.args.max_nodes)

                except:
                    sys.stderr.write(u"Argument of '--max-nodes' must be an integer. Quitting.\n")
                    sys.exit(1)

            if self.args.max_components is not None:
                try:
                    self.args.max_components = int(self.args.max_components)
                except:

                    sys.stderr.write(u"Argument of '--max-components' must be an integer. Quitting.\n")
                    sys.exit(1)

            if self.args.min_components is not None:
                try:
                    self.args.min_components = int(self.args.min_components)

                except:
                    sys.stderr.write(u"Argument of '--min-components' must be an integer. Quitting.\n")
                    sys.exit(1)

            mod_utils.filter_subgraphs(min_nodes=self.args.min_nodes, max_nodes=self.args.max_nodes,
                                       min_components=self.args.min_components,
                                       max_components=self.args.max_components)
            if len(mod_utils.modules) > 0:
                sys.stdout.write(
                    u"Filtered out {0} communities. Keeping {1} communities. Writing induced subgraph of communities to file...\n".format(
                        (init_mods - len(mod_utils.modules)), len(mod_utils.modules)))
            else:
                sys.stderr.write(
                    u"No community could be kept using the current filters. Quitting.\n")
                sys.exit(0)

        else:
            sys.stdout.write(u"No filters specified. All modules will be kept.\n")

        mod_utils.label_modules_in_graph(graph=graph)
        final_mods = mod_utils.get_modules()

        for elem in final_mods:
            results[elem["module"]] = [elem.vcount(), elem.ecount(), len(elem.components())]


        # producing output graph
        if self.args.no_output_header:
            sys.stdout.write(u"Skipping header writing on output graph community files.\n")
            output_header = False

        else:
            output_header = True

        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"Warning: output directory does not exists, will create one at {}.\n".format(
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
                u"Basename of the output modules will be {} (default).\n".format(
                    self.args.output_file))

        output_basename = os.path.join(self.args.directory, self.args.output_file)
        # output generated networks
        for elem in final_mods:
            output_path = ".".join(["_".join([output_basename, str(elem["module"]), self.date]), out_form])
            if out_form == "adjm":
                sys.stdout.write(u"Writing each community to an adjacency matrix...\n")
                PyntacleExporter.AdjacencyMatrix(elem, output_path, sep=self.args.output_separator,
                                                 header=output_header)
            elif out_form == "egl":
                sys.stdout.write(u"Writing each community to an edge list...\n")
                PyntacleExporter.EdgeList(elem, output_path, sep=self.args.output_separator, header=output_header)

            elif out_form == "sif":
                sys.stdout.write(u"Writing each community to a Simple Interaction Format (SIF) file...\n")
                PyntacleExporter.Sif(elem, output_path, sep=self.args.output_separator, header=output_header)

            elif out_form == "dot":
                sys.stdout.write(u"Writing each community to a DOT file...\n")
                # Ignore ugly RuntimeWarnings while creating a dot
                simplefilter("ignore", RuntimeWarning)
                PyntacleExporter.Dot(elem, output_path)

            elif out_form == "bin":
                sys.stdout.write(u"Writing each community to a binary file (ending in .graph)...\n")
                PyntacleExporter.Binary(elem, output_path)

        # reporting and plotting part
        sys.stdout.write(u"Producing report in {} format...\n".format(self.args.report_format))

        r.create_report(report_type=report_type, report=results)
        r.write_report(report_dir=self.args.directory, format=self.args.report_format)

        # save the original graph into a binary file
        if self.args.save_binary:
            binary_name = ".".join(["_".join([os.path.splitext(os.path.basename(self.args.input_file))[0], "communities"]), "graph"])
            binary_path = os.path.join(self.args.directory, binary_name)
            sys.stdout.write(
                u"Storing the input graph with module labels into a binary file in the results directory...\n".format(
                    binary_path))

        if not self.args.no_plot:

            plot_dir = os.path.join(self.args.directory, "pyntacle-plots")

            if os.path.isdir(plot_dir):
                self.logging.warning(
                    u"A directory named \"pyntacle-plots\" already exists.")

            else:
                os.mkdir(plot_dir)

            avail_colors_fill = sns.color_palette("Spectral", n_colors=len(
                final_mods)).as_hex()  # available colors for node fill
            avail_colors_borders = sns.color_palette("Spectral", n_colors=len(final_mods),
                                                     desat=0.5).as_hex()

            if graph.vcount() < 1000:

                sys.stdout.write(u"Plotting graph in {} format...\n".format(self.args.plot_format))

                main_plot_path = os.path.join(plot_dir, ".".join(["_".join(
                    [self.args.which, os.path.splitext(os.path.basename(self.args.input_file))[0], "communities",
                     self.date]), self.args.plot_format]))

                # initialize general graph Drawer
                sys.stdout.write(u"Drawing original graph, highlighting communities...\n")
                graph_plotter = PlotGraph(graph=graph)
                graph_plotter.set_node_labels(labels=graph.vs()["name"])
                graph_plotter.set_node_sizes([30] * graph.vcount())

                # define different colors for each module
                not_in_module_colors = "#A9A9A9"
                col_list = []
                bord_list = []
                for elem in graph.vs():
                    module = elem["module"]
                    if module is not None:
                        col_list.append(avail_colors_fill[module])
                        bord_list.append(avail_colors_borders[module])

                    else:
                        col_list.append(not_in_module_colors)
                        bord_list.append(not_in_module_colors)

                graph_plotter.set_node_colors(col_list)
                graph_plotter.set_layouts(self.args.plot_layout)
                graph_plotter.plot_graph(path=main_plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                         keep_aspect_ratio=True, vertex_label_size=6,
                                         vertex_frame_color=bord_list)
            else:
                sys.stdout.write(
                    u"Input graph is above Pyntacle plotting capability ({} nodes, we plot graph with at best 1000 nodes). Will skip plotting this module.\n".format(
                        graph.vcount()))

            if len(final_mods) > 20:
                self.logging.warning(
                    u"The number of modules found ({}) is very high. The plot of the input graph will have nuanced colors.".format(
                        len(final_mods)))

            sys.stdout.write("Drawing Each Module Separately...\n")

            for i, comm in enumerate(final_mods):
                if comm.vcount() <= 1000:
                    plotter = PlotGraph(graph=comm)
                    plotter.set_node_labels(labels=comm.vs()["name"])

                    plotter.set_node_colors([avail_colors_fill[i]] * comm.vcount())

                    plotter.set_node_sizes([30] * comm.vcount())

                    comm_plot_path = os.path.join(plot_dir, ".".join(
                        ["_".join([self.args.output_file, str(comm["module"]), self.date]),
                         self.args.plot_format]))

                    plotter.set_layouts(self.args.plot_layout)
                    plotter.plot_graph(path=comm_plot_path, bbox=plot_size, margin=20, edge_curved=0.2,
                                       keep_aspect_ratio=True, vertex_label_size=6,
                                       vertex_frame_color=[avail_colors_borders[i]] * comm.vcount())

                else:
                    sys.stdout.write(
                        u"Module {0} is above Pyntacle plotting limits ({1} nodes, communities with at best 1000 nodes are plotted). Plotting will be skipped.\n".format(
                            i, comm.vcount()))
        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(u"Pyntacle communities completed successfully. Ending.\n")
        sys.exit(0)
