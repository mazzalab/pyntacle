__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.3.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2020"
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
import filecmp
from warnings import simplefilter

from graph_operations.set_operations import GraphSetOps
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.reporter import PyntacleReporter
from tools.enums import ReportEnum
from tools.graph_utils import GraphUtils
from internal.graph_load import GraphLoad
from exceptions.multiple_solutions_error import MultipleSolutionsError
from exceptions.unsupported_graph_error import UnsupportedGraphError
from exceptions.generic_error import Error


class Set:
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py set {union, intersection, difference} [options]'")

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if not os.path.exists(self.args.input_file_1) or not os.path.exists(self.args.input_file_2):
            sys.stderr.write(u"One of the two input files does not exist. Quit\n")
            sys.exit(1)

        if filecmp.cmp(self.args.input_file_1, self.args.input_file_2, shallow=False):
            sys.stderr.write(u"The two input files are equal. Quit\n")
            sys.exit(1)

        input_header = True
        if self.args.no_header:
            input_header = False

        sys.stdout.write(import_start)
        input_format = format_dictionary.get(self.args.format, "NA")
        sys.stdout.write(u"Reading first input file\n")
        graph1 = GraphLoad(self.args.input_file_1, file_format=input_format,
                           header=input_header, separator=self.args.input_separator).graph_load()

        sys.stdout.write(u"Reading second input file\n")
        graph2 = GraphLoad(self.args.input_file_2, file_format=input_format,
                           header=input_header, separator=self.args.input_separator).graph_load()

        # init Utils global stuff
        utils1 = GraphUtils(graph=graph1)
        utils2 = GraphUtils(graph=graph2)

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

        if self.args.largest_component:
            try:
                graph1 = utils1.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph {0} as you requested ({1} nodes, {2} edges)\n".format(graph2["name"],
                        graph1.vcount(), graph1.ecount()))
                utils1.set_graph(graph1)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"Graph {} has two largest components of the same size. Cannot choose one. either remove one of the components or run 'pyntacle set' without the '--largest-component' option. Quit\n".format(graph1["name"]))
                sys.exit(1)

            try:
                graph2 = utils2.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph {0} as you requested ({1} nodes, {2} edges)\n".format(
                        graph2["name"],graph2.vcount(), graph2.ecount()))
                utils2.set_graph(graph2)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"Graph {} has two largest components of the same size. Cannot choose one: either remove one of the components or run 'pyntacle set' without the '--largest-component' option. Quit\n".format(
                        graph2["name"]))
                sys.exit(1)
       

        if self.args.format == "sif" or not all(x is None for x in graph1.es()["sif_interaction"]) or not all(
                        x is None for x in graph2.es()["sif_interaction"]):
            sys.stdout.write(u"WARNING: Interaction stored in SIF files will be removed\n")

        # GraphSetOps(graph1=graph1, graph2=graph2,new_name = new_name
        sys.stdout.write(section_end)
        sys.stdout.write(run_start)
        if self.args.which == "union":
            sys.stdout.write(
                u"Performing union between input graph {} and {}\n".format(self.args.input_file_1,
                                                                           self.args.input_file_2))

            output_graph = GraphSetOps.union(graph1, graph2, self.args.output_file)
        elif self.args.which == "intersection":
            sys.stdout.write(
                u"Performing intersection between input graph {} and {}\n".format(self.args.input_file_1,
                                                                                  self.args.input_file_2))

            output_graph = GraphSetOps.intersection(graph1, graph2, self.args.output_file)

            if output_graph.ecount() == 0:
                sys.stdout.write(
                    u"The intersection is empty and a graph will not be generated\n")
                if not self.args.suppress_cursor:
                    cursor.stop()
                sys.exit(0)
        else:
            # elif self.args.which == "difference":
            sys.stdout.write(
                "Performing difference between input graph {} and  {}\n".format(self.args.input_file_1,
                                                                                self.args.input_file_2))

            output_graph = GraphSetOps.difference(graph1, graph2, self.args.output_file)
            if output_graph.vcount() == graph1.vcount() and output_graph.ecount() == graph1.ecount():
                sys.stdout.write(u"Graphs {} and {} are disjoint\n".format(
                    os.path.basename(self.args.input_file_1), os.path.basename(self.args.input_file_2)))

            if output_graph.vcount() > 1 and output_graph.ecount() == 0:
                sys.stdout.write(
                    u"Graph difference returned {} isolates. A graph will not be produced. Quit\n".format(
                        output_graph.vcount()))
                sys.exit(0)

        sys.stdout.write(section_end)
        sys.stdout.write(report_start)
        # print pyntacle_commands_utils to command line
        sys.stdout.write(u"Report of set operation: {}\n".format(self.args.which))
        sys.stdout.write(section_end)
        sys.stdout.write(u"Input graphs:\n")

        sys.stdout.write(
            u"Graph 1: {0}\nNodes:\t{1}\nEdges:\t{2}\nComponents:\t{3}\n".format(graph1["name"][0], graph1.vcount(),
                                                                                   graph1.ecount(),
                                                                                   len(graph1.components())))
        sys.stdout.write(section_end)
        sys.stdout.write(
            u"Graph 2: {0}\nNodes:\t{1}\nEdges:\t{2}\nComponents:\t{3}\n".format(graph2["name"][0], graph2.vcount(),
                                                                                   graph2.ecount(),
                                                                                   len(graph2.components())))

        sys.stdout.write(section_end)
        sys.stdout.write(u"Resulting graph:\n")
        sys.stdout.write(u"Nodes:\t{0}\nEdges:\t{1}\nComponents:\t{2}\n".format(output_graph.vcount(),
                                                                               output_graph.ecount(),
                                                                               len(output_graph.components())))

        sys.stdout.write(section_end)
        sys.stdout.write(report_start)
        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"WARNING: The output directory does not exist. It will be created at {}\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        out_form = format_dictionary.get(self.args.output_format, "NA")
        output_path = os.path.join(self.args.directory, ".".join([self.args.output_file, out_form]))

        sys.stdout.write(u"Basename of output graph: {}\n".format(self.args.output_file))
        sys.stdout.write(u"Path of the generated graph: {}\n".format(output_path))

        # producing output graph
        if self.args.no_output_header:
            sys.stdout.write(u"Skipping header in output file\n")
            output_header = False

        else:
            output_header = True

        if self.args.output_separator is None:
            sys.stdout.write(u"Using '\\t' as default separator for the output file\n")
            self.args.output_separator = "\t"

        if os.path.exists(output_path):
            self.logging.warning(u"A file named {} already exist. It will be overwritten".format(output_path))

        # output generated networks
        if out_form == "adjm":
            sys.stdout.write(u"Writing the resulting graph to an adjacency matrix file\n")
            PyntacleExporter.AdjacencyMatrix(output_graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "egl":
            sys.stdout.write(u"Writing the resulting graph to an edge-list file\n")
            PyntacleExporter.EdgeList(output_graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "sif":
            sys.stdout.write(u"Writing the resulting graph to a SIF file\n")
            PyntacleExporter.Sif(output_graph, output_path, sep=self.args.output_separator, header=output_header)

        elif out_form == "dot":
            sys.stdout.write("Writing the resulting graph to a DOT file\n")

            # Ignore ugly RuntimeWarnings while creating a dot
            simplefilter("ignore", RuntimeWarning)
            PyntacleExporter.Dot(output_graph, output_path)

        elif out_form == "graph":
            sys.stdout.write("Writing the resulting graph to a binary file (with .graph extension)\n")
            PyntacleExporter.Binary(output_graph, output_path)

        intersection_set = []
        for v in output_graph.vs():
            parent_g1 = "_".join(graph1["name"])
            parent_g2 = "_".join(graph2["name"])

            if parent_g1 in v["parent"] and parent_g2 in v["parent"]:
                intersection_set.append(v["name"])
            elif parent_g1 in v["parent"] and not parent_g2 in v["parent"]:
                intersection_set.append(v["name"])
            elif parent_g2 in v["parent"] and not parent_g1 in v["parent"]:
                pass

        reporter1 = PyntacleReporter(graph=graph1)  # init reporter1
        reporter2 = PyntacleReporter(graph=graph2)  # init reporter2
        reporter_final = PyntacleReporter(graph=output_graph)
        
        set1_attr_dict = OrderedDict()
        set2_attr_dict = OrderedDict()
        setF_attr_dict = OrderedDict()

        if self.args.which == 'intersection':
            setF_attr_dict['\nCommon nodes'] = 'Node names'#(len(intersection_set), ','.join(intersection_set))
            setF_attr_dict[len(intersection_set)] = ','.join(intersection_set)
        reporter1.create_report(ReportEnum.Set, set1_attr_dict)
        reporter2.create_report(ReportEnum.Set, set2_attr_dict)
        reporter_final.create_report(ReportEnum.Set, setF_attr_dict)

        reporter1.report[1] = ['\n--- Graph 1 ---']
        reporter2.report[1] = ['--- Graph 2 ---']
        del(reporter1.report[-1])
        del(reporter2.report[-1])
        del(reporter2.report[0])
        del(reporter_final.report[0])
        for e in reporter_final.report:
            if e[0] == 'Pyntacle command:':
                e[1] = e[1] + ' ' + self.args.which
        
        reporter_final.report[0] = ['\n--- Resulting graph ---']
        reporter1.report.extend(reporter2.report)
        reporter1.report.extend(reporter_final.report)
        reporter1.write_report(report_dir=self.args.directory, format=self.args.report_format)

        total_nodes = len(list(set(graph1.vs["name"]).union(set(graph2.vs["name"]))))

        if not self.args.no_plot and total_nodes < 5000:
            both_graphs = GraphSetOps.union(graph1, graph2, 'Both')
            report_dict = OrderedDict()
            report_dict['algorithm'] = self.args.which
            report_dict[0] = {'nodes': ','.join(output_graph.vs["name"]), 'edges': output_graph.es["adjacent_nodes"]}

            #create custom instance of reporter to be passed to pyntacleink and storing appropriate values
            reporter_both_graphs = PyntacleReporter(graph=both_graphs)
            reporter_both_graphs.report_type = ReportEnum.Set

            suffix = "_".join(["_".join(graph1["name"]), "Set", "_".join(graph2["name"])])

            sys.stdout.write(u"Plotting {} in {} with PyntacleInk\n".format(self.args.which, self.args.directory))
            reporter_both_graphs.pyntacleink_report(report_dir=self.args.directory, report_dict=report_dict, suffix=suffix)

        elif total_nodes >= 5000:
            sys.stdout.write(
                u"The sum of the nodes of the two graphs is {}. PyntacleInk can plot graphs with N < 5000. This graph will not be plotted\n".format(
                    total_nodes))
        else:
            sys.stdout.write(pyntacleink_skip_msg)

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(section_end)

        sys.stdout.write(u"Pyntacle set completed successfully\n")
        sys.exit(0)
