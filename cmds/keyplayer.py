__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.2"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"09/06/2020"
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

from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from cmds.cmds_utils.group_search_wrapper import SGDWrapper as sgd
from algorithms.keyplayer import KeyPlayer as kpp

from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.reporter import PyntacleReporter
from tools.graph_utils import GraphUtils as gu
from tools.enums import ReportEnum, CmodeEnum, KpnegEnum, KpposEnum
from tools.add_attributes import AddAttributes
from internal.graph_load import GraphLoad
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError


class KeyPlayer:
    def __init__(self, args):
        self.logging = log
        self.args = args
        self.date = runtime_date

    def run(self):
        if not hasattr(self.args, 'which'):
            raise Error(u"usage: pyntacle.py keyplayer {kp-finder, kp-info} [options]'")

        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if self.args.m_reach is None and self.args.type in ["pos", "all"]:
            sys.stderr.write(u"m-reach distance must be provided for computing m-reach\n")
            sys.exit(1)

        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify the input file using the `-i/--input-file` option\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        if self.args.no_header:
            header = False
        else:
            header = True

        # Load Graph
        sys.stdout.write(import_start)
        sys.stdout.write(u"Importing graph from file\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header,
                          separator=self.args.input_separator).graph_load()
        sys.stdout.write("\n")

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
        if hasattr(self.args, "nodes"):
            self.args.nodes = self.args.nodes.split(",")

            if not utils.nodes_in_graph(self.args.nodes):
                sys.stderr.write(
                    "One or more of the specified nodes {} is not present in the graph. Please check the spelling and the presence of empty spaces within node names. Quitting\n".format(
                        self.args.nodes))
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

        # initialize reporter for later usage
        r = PyntacleReporter(graph=graph)
        initial_results = {}
        results = OrderedDict()

        sys.stdout.write(run_start)
        if self.args.which == 'kp-finder':
            if self.args.implementation == "greedy":
                report_type = ReportEnum.KP_greedy
                kp_runner = gow(graph=graph)

                sys.stdout.write(
                    u"Using greedy optimization algorithm for searching the optimal key player set for the requested key player metrics\n")
                sys.stdout.write("\n")

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-Neg: Finding optimal set of nodes of size {0} that maximizes F\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, cmode=implementation)
                    sys.stdout.write("\n")

                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-Neg: Finding optimal set of nodes of size {0} that maximizes dF\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF, cmode=implementation)
                    sys.stdout.write("\n")

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-Pos: Finding optimal set of nodes of size {0} that maximizes dR\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR, cmode=implementation)
                    sys.stdout.write("\n")

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-Pos: Finding optimal set of nodes of size {0} that maximizes the m-reach at distance {1}\n".format(
                            self.args.k_size, self.args.m_reach))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               cmode=implementation)
                    sys.stdout.write("\n")

            elif self.args.implementation == "brute-force":
                report_type = ReportEnum.KP_bruteforce
                kp_runner = bfw(graph=graph)
                sys.stdout.write(u"Using brute-force search algorithm to find the best key player set(s)\n")
                sys.stdout.write(sep_line)

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-Neg: Finding best set (or sets) of nodes of size {0} that holds the maximum F\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, nprocs=self.args.nprocs,
                                                cmode=implementation)
                    sys.stdout.write("\n")

                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-Neg: Finding best set(s) of nodes of size {0} that holds the maximum dF\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                cmode=implementation, nprocs=self.args.nprocs)

                    sys.stdout.write("\n")

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-Pos: Finding best set(s) of nodes of size {0} that hold the maximum dR\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               cmode=implementation, nprocs=self.args.nprocs)

                    sys.stdout.write(sep_line)

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-Pos: Finding the best set(s) of nodes of size {0} that maximizes the m-reach at distance {1}\n".format(
                            self.args.k_size, self.args.m_reach))

                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               cmode=implementation, nprocs=self.args.nprocs)

                    sys.stdout.write("\n")

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

                report_type = ReportEnum.KP_stochasticgradientdescent
                kp_runner = sgd(graph=graph)
                sys.stdout.write(
                    u"Running the Stochastic Gradient Descent algorithm\n")
                sys.stdout.write("\n")

                if self.args.type in (['F', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-Neg: Finding optimal set of nodes of size {0} that maximizes F\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, cmode=implementation,
                                                **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write("\n")

                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-Neg: Finding optimal set of nodes of size {0} that maximizes dF\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF, cmode=implementation,
                                                **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write("\n")

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-Pos: Finding optimal set of nodes of size {0} that maximizes dR\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR, m=self.args.m_reach,
                                               cmode=implementation,
                                               **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write("\n")

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-Pos: Finding optimal set of nodes of size {0} that maximizes the m-reach at distance {1}\n".format(
                            self.args.k_size, self.args.m_reach))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               cmode=implementation,
                                               **{k: v for k, v in optional_args.items() if v is not None})
                    sys.stdout.write("\n")

            #  get report results
            results.update(kp_runner.get_results())
            sys.stdout.write(summary_start)
            sys.stdout.write(u"Node set size for key-player search: {}\n".format(str(self.args.k_size)))

            sys.stdout.write("\n")
            for kp in results.keys():
                if len(results[kp][0]) > 1 and self.args.implementation in ['brute-force', 'sgd']:
                    plurals = ['s', 'are']
                else:
                    plurals = ['', 'is']

                if results[kp][0][0] is None:  # the case in which there's no solution
                    results[kp][0] = ["None"]

                if self.args.implementation in ['brute-force', 'sgd']:
                    list_of_results = "\n".join(['(' + ', '.join(x) + ')' for x in results[kp][0]])
                else:
                    list_of_results = "(" + ", ".join(results[kp][0]) + ")"

                if kp == KpnegEnum.F.name or kp == KpnegEnum.dF.name:
                    # joining initial results with final ones
                    results[kp].append(initial_results[kp])

                    sys.stdout.write(
                        u"The best key-player set{0} of size {1} for negative key-player index {2} {3}:\n {4}\n Final {2} value: {5}\n Starting graph {2} was {6}\n".format(
                            plurals[0], self.args.k_size, kp, plurals[1], list_of_results, results[kp][1],
                            results[kp][2]))
                    sys.stdout.write("\n")

                elif kp == KpposEnum.dR.name:
                    sys.stdout.write(
                        u"The best key-player set{0} of size {1} for positive key-player index {2} {3}:\n {4}\n Final {2} value: {5}\n".format(
                            plurals[0], self.args.k_size, kp, plurals[1], list_of_results, results[kp][1]))
                    sys.stdout.write("\n")

                elif kp == KpposEnum.mreach.name:
                    results[kp].append(self.args.m_reach)
                    node_perc_reached = ((self.args.k_size + results[kp][1]) / graph.vcount()) * 100
                    if node_perc_reached == 100:
                        node_perc_reached = int(node_perc_reached)
                    else:
                        node_perc_reached = round(node_perc_reached, 2)
                    sys.stdout.write(
                        u'Key-player set{0} of size {1} for positive key player index m-reach, using at most '
                        '{3} steps {4}:\n{5}\nwith value {6} on {8} (number of nodes reached on total number of nodes)\nThe total percentage of nodes, which '
                        'includes the kp-set, is {7}%\n'
                            .format(
                            plurals[0], self.args.k_size, kp, self.args.m_reach, plurals[1], list_of_results,
                            results[kp][1], node_perc_reached, graph.vcount()))
                    sys.stdout.write("\n")

        # kpinfo: compute kpmetrics for a set of predetermined nodes
        elif self.args.which == 'kp-info':
            report_type = ReportEnum.KP_info
            initial_results = OrderedDict()
            kp_runner = kpw(graph=graph, nodes=self.args.nodes)
            results = OrderedDict()

            sys.stdout.write(u"Input node set: ({})\n".format(', '.join(self.args.nodes)))
            sys.stdout.write("\n")

            if self.args.type in (['F', 'neg', 'all']):
                initial_results[KpnegEnum.F.name] = kpp.F(graph)
                kp_runner.run_fragmentation(KpnegEnum.F)
                sys.stdout.write("\n")
            if self.args.type in (['dF', 'neg', 'all']):
                initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=implementation)
                kp_runner.run_fragmentation(KpnegEnum.dF, cmode=implementation)
                sys.stdout.write("\n")

            if self.args.type in (['dR', 'pos', 'all']):
                kp_runner.run_reachability(KpposEnum.dR, cmode=implementation)
                sys.stdout.write("\n")

            if self.args.type in (['mreach', 'pos', 'all']):
                kp_runner.run_reachability(KpposEnum.mreach, m=self.args.m_reach, cmode=implementation)
                sys.stdout.write("\n")

            results.update(kp_runner.get_results())
            sys.stdout.write(summary_start)
            for metric in results.keys():
                if metric == KpnegEnum.F.name or metric == KpnegEnum.dF.name:
                    results[metric].append(initial_results[metric])
                    sys.stdout.write(
                        u"Removing node set \n({2})\ngives a {0} value of {3}\nStarting graph {0}: {1}\n".format(
                            metric, results[metric][2], ', '.join(self.args.nodes), results[metric][1]))
                    sys.stdout.write("\n")

                elif metric == KpposEnum.mreach.name:
                    results[metric].append(self.args.m_reach)
                    perc_node_reached = round((results[metric][1] + len(self.args.nodes)) / graph.vcount() * 100, 3)
                    sys.stdout.write(
                        u"The m-reach of node set:\n({0})\nis {1} on {4} (number of nodes reached on total number of "
                        u"nodes)\nThis means it can reach the {2}% of remaining nodes in the graph nodes in at most {3} steps\n".format(
                            ', '.join(results[metric][0]), results[metric][1], perc_node_reached,
                            self.args.m_reach, graph.vcount()))
                    sys.stdout.write("\n")

                else:  # dR case
                    sys.stdout.write(
                        "The {0} value for node set:\n({1})\nis {2}\n".format(metric, ', '.join(results[metric][0]),
                                                                              results[metric][1]))
                    sys.stdout.write("\n")

        sys.stdout.write(report_start)
        # check output directory
        if createdir:
            sys.stdout.write(u"WARNING: output directory does not exist, {} will be created\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        # reporting and plotting part
        sys.stdout.write(u"Writing report in {} format\n".format(self.args.report_format))

        r.create_report(report_type=report_type, report=results)
        r.write_report(report_dir=self.args.directory, format=self.args.report_format)

        # PyntacleInk section
        if not self.args.no_plot and graph.vcount() < 5000:
            suffix = "_".join(graph["name"])
            sys.stdout.write(
                u"Plotting network and run results in {} directory with PyntacleInk\n".format(self.args.directory))
            r.pyntacleink_report(report_dir=self.args.directory, report_dict=results, suffix=suffix)

        elif graph.vcount() >= 5000:
            sys.stdout.write(
                u"The graph has too many nodes ({}). PyntacleInk can plot networks with N < 5000. This graph will not be plotted\n".format(
                    graph.vcount()))
        else:
            sys.stdout.write(pyntacleink_skip_msg)

        if self.args.save_binary:
            # reproduce octopus behaviour by adding kp information to the graph before saving it
            sys.stdout.write(
                u"Saving final network into a binary file (with the .graph suffix) in the output directory\n")

            for key in results.keys():
                if key == KpposEnum.mreach.name:  # replace the mreach distance
                    new_mreach = "_".join([KpposEnum.mreach.name, str(results[KpposEnum.mreach.name][-1])])
                    # create new key
                    results[new_mreach] = results[KpposEnum.mreach.name][
                                          :-1]  # remove the mreach distance before adding it to the binary file
                    del results[KpposEnum.mreach.name]
                    key = new_mreach

                if self.args.which == "kp-finder":
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
                            "WARNING: attribute {} does not point to a dictionary, will overwrite\n".format(attr_name))
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

        sys.stdout.write("\n")
        sys.stdout.write(u"Pyntacle keyplayer completed successfully\n")

        sys.exit(0)
