__author__ = u"Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.3"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"09/07/2020"
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
from internal.graph_load import GraphLoad
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as ipw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from cmds.cmds_utils.group_search_wrapper import SGDWrapper as sgd
from tools.enums import ReportEnum, GroupDistanceEnum, GroupCentralityEnum, CmodeEnum
from tools.add_attributes import AddAttributes
from tools.graph_utils import GraphUtils as gu
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError
from cmds.cmds_utils.reporter import PyntacleReporter


class GroupCentrality:
    def __init__(self, args):
        self.logging = log
        self.args = None
        self.args = args
        self.date = runtime_date

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        # verify that group distance is set when the group closeness is specified
        distancedict = {"min": GroupDistanceEnum.minimum, "max": GroupDistanceEnum.maximum,
                        "mean": GroupDistanceEnum.mean}
        if self.args.type in ["all", "closeness"]:
            if self.args.group_distance not in distancedict.keys():
                sys.stdout.write("'--group-distance/-D parameter must be one of the followings: {}'. Quitting\n".format(
                    ",".join(distancedict.keys())))
                sys.exit(1)
            else:
                group_distance = distancedict[self.args.group_distance]

        # Parsing optional node list
        if hasattr(self.args, 'nodes'):
            self.args.nodes = self.args.nodes.split(',')
            # self.args.nodes = [str.lower(x) for x in self.args.nodes]

        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py groupcentrality {gr-finder, gr-info} [options]'")

        if self.args.no_header:
            header = False
        else:
            header = True

        sys.stdout.write(import_start)
        sys.stdout.write(u"Importing graph from file\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header,
                          separator=self.args.input_separator).graph_load()

        # auto-select the implementation type
        if self.args.nprocs > 1:
            graph["implementation"] = CmodeEnum.igraph
            implementation = CmodeEnum.igraph
        elif graph.vcount() < 250:
            graph["implementation"] = CmodeEnum.igraph
            implementation = CmodeEnum.igraph
        else:
            graph["implementation"] = CmodeEnum.cpu
            implementation = CmodeEnum.cpu

        utils = gu(graph=graph)
        if hasattr(self.args, 'nodes'):

            if not utils.nodes_in_graph(self.args.nodes):
                sys.stderr.write(
                    "One or more of the specified nodes is not present in the graph. Quitting\n")
                sys.exit(1)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(
                    u"Extracting the largest component of the input graph as you requested ({} nodes, {} edges)\n".format(
                        graph.vcount(), graph.ecount()))
                # reinitialize graph utils class
                utils.set_graph(graph)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting\n")
                sys.exit(1)

            # check that the nodes are in the largest component
            if hasattr(self.args, 'nodes'):

                if not utils.nodes_in_graph(self.args.nodes):
                    sys.stderr.write(
                        "One or more of the specified nodes is not present in the largest graph component. Select a different set or remove this option. Quitting\n")
                    sys.exit(1)

        if hasattr(self.args, "k_size") and self.args.k_size >= graph.vcount():
            sys.stderr.write("The 'k' argument ({}) must be strictly less than the graph size({}). Quitting\n".format(
                self.args.k_size, graph.vcount()))
            sys.exit(1)

        # check that the output directory is properly set
        createdir = False
        if not os.path.isdir(self.args.directory):
            createdir = True

        #  initialize reporter for later use
        reporter = PyntacleReporter(graph=graph)
        results = OrderedDict()

        sys.stdout.write(section_end)
        sys.stdout.write(run_start)

        if self.args.which == "gr-finder":
            # Greedy optimization
            if self.args.implementation == "greedy":
                report_type = ReportEnum.GR_greedy
                go_runner = gow(graph=graph)
                sys.stdout.write(
                    u"Using greedy optimization algorithm to search the optimal set of nodes using group-centrality metrics\n")
                sys.stdout.write(sep_line)

                if self.args.type in (["all", "degree"]):
                    sys.stdout.write(
                        u"Searching a set of nodes of size {0} that optimizes the group-degree\n".format(
                            self.args.k_size))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_degree,
                                                  cmode=implementation)
                    sys.stdout.write(sep_line)

                if self.args.type in (["all", "betweenness"]):
                    sys.stdout.write(
                        u"Searching a set of nodes of size {0} that optimizes the group-betweenness\n".format(
                            self.args.k_size))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_betweenness,
                                                  cmode=implementation)
                    sys.stdout.write(sep_line)

                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Searching a set of nodes of size {0} that optimizes the group-closeness using the {1} distance from the node set\n".format(
                            self.args.k_size, group_distance.name))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_closeness,
                                                  cmode=implementation, distance=group_distance)
                    sys.stdout.write(sep_line)

                sys.stdout.write(sep_line)
                results.update(go_runner.get_results())

            # Bruteforce implementation
            elif self.args.implementation == "brute-force":

                if self.args.nprocs > 1:
                    plural = "s"
                else:
                    plural = ""

                report_type = ReportEnum.GR_bruteforce
                bf_runner = bfw(graph=graph)
                sys.stdout.write(
                    u"Using brute-force search algorithm to find the best set(s) that optimize group-centrality metrics\n")
                sys.stdout.write(sep_line)

                if self.args.type in (["all", "degree"]):
                    sys.stdout.write(
                        u"Searching the best set(s) of nodes of size {0} that maximizes the group-degree using {1} process{2}\n".format(
                            self.args.k_size, self.args.nprocs, plural))
                    bf_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_degree,
                                                  cmode=implementation, nprocs=self.args.nprocs)

                    sys.stdout.write(sep_line)

                if self.args.type in (["all", "betweenness"]):
                    sys.stdout.write(
                        u"Searching the best set(s) of nodes of size {0} that maximizes the group-betweenness using {1} process{2}\n".format(
                            self.args.k_size, self.args.nprocs, plural))
                    bf_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_betweenness,
                                                  cmode=implementation, nprocs=self.args.nprocs)
                    sys.stdout.write(sep_line)

                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Searching the best set(s) of nodes of size {0} that maximizes the group-closeness using the {1} distance from the node set and {2} process{3}\n".format(
                            self.args.k_size, group_distance, self.args.nprocs, plural))
                    bf_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_closeness,
                                                  cmode=implementation, nprocs=self.args.nprocs,
                                                  distance=group_distance)
                    sys.stdout.write(sep_line)

                results.update(bf_runner.get_results())

            # Stochastic gradient descent implementation
            elif self.args.implementation == "sgd":
                # process optional args
                probability: float = self.args.swap_probability
                if probability and probability < 0 or probability > 1:
                    sys.stderr.write(
                        "'probability' must be a decimal number between 0 and 1. Quitting\n")
                    sys.exit(1)

                tolerance: float = self.args.tolerance
                if tolerance and probability < 0:
                    sys.stderr.write(
                        "'tolerance' must be a positive decimal number. Quitting\n")
                    sys.exit(1)

                maxsec: int = self.args.maxsec
                if maxsec and maxsec < 0:
                    sys.stderr.write(
                        "'maxsec' must be a positive decimal number. Quitting\n")
                    sys.exit(1)
                optional_args = dict(probability=probability, tolerance=tolerance, maxsec=maxsec)

                report_type = ReportEnum.GR_stochasticgradientdescent
                sgd_runner = sgd(graph=graph)
                sys.stdout.write(
                    u"Running the Stochastic Gradient Descent algorithm\n")
                sys.stdout.write(sep_line)

                if self.args.type in (["all", "degree"]):
                    sys.stdout.write(
                        u"Searching a set of nodes of size {0} that optimizes the group-degree\n".format(
                            self.args.k_size))

                    sgd_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_degree,
                                                   distance=group_distance, cmode=implementation,
                                                   **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write(sep_line)

                if self.args.type in (["all", "betweenness"]):
                    sys.stdout.write(
                        u"Searching a set of nodes of size {0} that optimizes the group-betweenness\n".format(
                            self.args.k_size))

                    sgd_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_betweenness,
                                                   distance=group_distance, cmode=implementation,
                                                   **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write(sep_line)

                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Searching a set of nodes of size {0} that optimizes the group-closeness using the {1} distance from the node set\n".format(
                            self.args.k_size, group_distance.name))

                    sgd_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_closeness,
                                                   distance=group_distance, cmode=implementation,
                                                   **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write(sep_line)

                sys.stdout.write(sep_line)
                results.update(sgd_runner.get_results())

            # shell output report part
            sys.stdout.write(section_end)
            sys.stdout.write(summary_start)
            sys.stdout.write(u"Set size for group centrality search: {}\n".format(str(self.args.k_size)))
            sys.stdout.write(sep_line)

            for kk in results.keys():
                if len(results[kk][0]) > 1 and self.args.implementation == 'brute-force':
                    plurals = ['s', 'are']
                else:
                    plurals = ['', 'is']

                if results[kk][0][0] is None:  # the case in which there's no solution
                    results[kk][0] = ["None"]

                if self.args.implementation == 'brute-force':
                    list_of_results = "\n".join(['(' + ', '.join(x) + ')' for x in results[kk][0]])

                else:
                    list_of_results = "(" + ", ".join(results[kk][0]) + ")"

                sys.stdout.write(
                    u'Best set{0} of size {1} for {5} centrality {2}:\n{3}\nwith value {4}\n'.format(
                        plurals[0], self.args.k_size, plurals[1], list_of_results, results[kk][1],
                        " ".join(kk.split("_")[:2])))

                if kk.startswith(GroupCentralityEnum.group_closeness.name):
                    sys.stdout.write(
                        "The {} distance was considered for computing the group-closeness\n".format(
                            group_distance.name))

                sys.stdout.write("\n")

            sys.stdout.write(section_end)

        elif self.args.which == "gr-info":
            report_type = ReportEnum.GR_info
            sys.stdout.write("Input node set: ({})\n".format(', '.join(self.args.nodes)))
            sys.stdout.write(sep_line)

            grinfo_runner = ipw(graph=graph, nodes=self.args.nodes)

            if self.args.type in (["degree", "all"]):
                grinfo_runner.run_groupcentrality(gr_type=GroupCentralityEnum.group_degree, cmode=implementation)

            if self.args.type in (["betweenness", "all"]):
                grinfo_runner.run_groupcentrality(gr_type=GroupCentralityEnum.group_betweenness, cmode=implementation)

            if self.args.type in (["closeness", "all"]):
                grinfo_runner.run_groupcentrality(gr_type=GroupCentralityEnum.group_closeness, cmode=implementation,
                                                  gr_distance=group_distance)

            results.update(grinfo_runner.get_results())

            sys.stdout.write(summary_start)

            for metric in results.keys():
                if metric == GroupCentralityEnum.group_degree.name:
                    sys.stdout.write("The group-degree value for the input node set:\n({0})\nis {1}\n".format(
                        ', '.join(results[metric][0]),
                        results[metric][1]))
                    sys.stdout.write("\n")

                if metric == GroupCentralityEnum.group_betweenness.name:
                    sys.stdout.write(
                        "The group-betweenness value for the input node set:\n({0})\nis {1}\n".format(
                            ', '.join(results[metric][0]),
                            results[metric][1]))
                    sys.stdout.write("\n")

                if metric.startswith(GroupCentralityEnum.group_closeness.name):
                    sys.stdout.write(
                        "The group-closeness value for the input node set:\n({0})\nis {1}.\nThe {2} distance was considered between the set and the rest of the graph\n".format(
                            ', '.join(results[metric][0]),
                            results[metric][1], group_distance.name))
                    sys.stdout.write("\n")

            sys.stdout.write(section_end)

        # output part
        sys.stdout.write(report_start)

        if createdir:
            sys.stdout.write(u"WARNING: output directory does not exist, {} will be created".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        sys.stdout.write(u"Writing report in {} format\n".format(self.args.report_format))

        reporter.create_report(report_type=report_type, report=results)
        reporter.write_report(report_dir=self.args.directory, format=self.args.report_format)

        # PyntacleInk section
        if not self.args.no_plot and graph.vcount() < 5000:
            suffix = "_".join(graph["name"])
            sys.stdout.write(
                u"Plotting network and run results in {} directory with PyntacleInk\n".format(self.args.directory))
            reporter.pyntacleink_report(report_dir=self.args.directory, report_dict=results, suffix=suffix)

        elif graph.vcount() >= 5000:
            sys.stdout.write(
                u"The graph has too many nodes ({}). PyntacleInk allows plotting for network with N < 5000. No visual representation will be produced\n".format(
                    graph.vcount()))
        else:
            sys.stdout.write(pyntacleink_skip_msg)

        if self.args.save_binary:
            # reproduce octopus behaviour by adding kp information to the graph before saving it
            sys.stdout.write(u"Saving graph to a binary file (ending in .graph)\n")

            for key in results.keys():
                if self.args.which == "gr-finder":
                    if self.args.implementation == "brute-force":
                        suffix = "bruteforce"
                        attr_key = tuple(tuple(sorted(tuple(x))) for x in results[key][0])
                    elif self.args.implementation == "greedy":
                        suffix = "greedy"
                        attr_key = tuple(sorted(tuple(results[key][0])))
                    else:
                        suffix = "sgd"
                        attr_key = tuple(sorted(tuple(results[key][0])))
                else:
                    suffix = "info"
                    attr_key = tuple(sorted(tuple(results[key][0])))

                attr_name = "_".join([key, suffix])
                attr_val = results[key][1]

                if attr_name in graph.attributes():
                    if not isinstance(graph[attr_name], dict):
                        sys.stdout.write(
                            "WARNING: attribute {} does not point to a dictionary, will overwrite".format(attr_name))
                        AddAttributes.add_graph_attribute(graph, attr_name, {attr_key: attr_val})
                    else:
                        if attr_key in graph[attr_name]:
                            sys.stdout.write(
                                "WARNING: {} already present in the {} graph attribute, will overwrite\n".format(
                                    attr_key, attr_val))
                        graph[attr_name].update({attr_key: attr_val})
                else:
                    AddAttributes.add_graph_attribute(graph, attr_name, {attr_key: attr_val})

            binary_prefix = "_".join(
                [os.path.splitext(os.path.basename(self.args.input_file))[0], self.args.which, self.date])
            binary_path = os.path.join(self.args.directory, binary_prefix + ".graph")
            PyntacleExporter.Binary(graph, binary_path)

        if not self.args.suppress_cursor:
            cursor.stop()

        sys.stdout.write(section_end)
        sys.stdout.write(u"Pyntacle group-centrality completed successfully\n")
        sys.exit(0)
