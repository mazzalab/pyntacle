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
#todo mauro checks formatting to terminal
# external libraries
from config import *
import argparse
import sys
import os
import unittest
import random
from numpy import random as nprandom
from copy import deepcopy
from exceptions.generic_error import Error

if sys.version_info <= (3, 4):
    sys.exit("Python < 3.4 is not supported. Please use 'python3' instead or update your Python compiler.")

from colorama import Fore, Style, init

if os.name == "nt":
    init(convert=True)

from cmds.cmds_utils.reporter import *
# Main commands wrappers
from cmds.keyplayer import KeyPlayer as kp_command
from cmds.group_centrality import GroupCentrality as gr_command
from cmds.metrics import Metrics as metrics_command
from cmds.convert import Convert as convert_command
from cmds.generate import Generate as generate_command
from cmds.set import Set as set_command
from cmds.communities import Communities as communities_command
from pyntacletests.test_suite import Suite


def _check_value(self, action, value):
    # converted value must be one of the choices (if specified)
    if action.choices is not None and value not in action.choices:
        args = {"value": value,
                "choices": ", ".join(map(repr, action.choices))}
        msg = "invalid choice: %(value)r"
        raise argparse.ArgumentError(action, msg % args)


def threads_type(x):
    x = int(x)
    if x < 1:
        raise argparse.ArgumentTypeError("Minimum threads number is 1")
    if x > cpu_count():
        raise argparse.ArgumentTypeError("Maximum threads number is {} for this machine".format(cpu_count()))

    return x


class App:
    def __init__(self):
        sys.stdout.write("\n")
        sys.tracebacklimit = 0
        verbosity = 0

        # Overriding argparse's mischievous and buggy error message
        argparse.ArgumentParser._check_value = _check_value

        parser = argparse.ArgumentParser(
            description="Main Description",
            usage=Fore.RED + Style.BRIGHT + "pyntacle" + Fore.GREEN + " <command>" + Fore.RED
                  + """ [<args>]
The available commands in Pyntacle are:\n""" + Style.RESET_ALL + 100 * "-" +
                  Fore.GREEN + "\n  keyplayer       " + Fore.CYAN + "Computes key player metrics (goo.gl/uj8jCR) for a "
                                                                    "specific set of nodes ('kp-info')\n                  or finds a set of "
                                                                    "nodes of size k that owns the optimal or the best "
                                                                    "score ('kp-finder')." +
                  Fore.GREEN + "\n\n  groupcentrality " + Fore.CYAN + "Computes group centrality metrics (goo.gl/82Whxu), "
                                                                    "a variation of classical node\n                  centrality indices. "
                                                                    "These metrics can be computed for "
                                                                    "a specific set of nodes ('gr-info')\n                  or they can be "
                                                                    "used to find a set of node of size k that own "
                                                                    "the optimal or the best score ('gr-finder')." +
                  Fore.GREEN + "\n\n  metrics         " + Fore.CYAN + "Computes metrics of local and global nature for a "
                                                                    "set of nodes of a network or for the "
                                                                    "whole graph." +
                  Fore.GREEN + "\n\n  convert         " + Fore.CYAN + "Converts a network file format to another one." +
                  Fore.GREEN + "\n\n  set             " + Fore.CYAN + "Performs set operations ('union', "
                                                                    "'intersection', 'difference') between two "
                                                                    "networks\n                  using graph logical operations." +
                  Fore.GREEN + "\n\n  generate        " + Fore.CYAN + "Generates in-silico networks that follow"
                                                                    "one of the available topologies." +
                  Fore.GREEN + "\n\n  communities     " + Fore.CYAN + "Finds communities within a graph using"
                                                                    "several community-finding algorithms. Produces\n                  "
                                                                    "several network files, each containing "
                                                                    "an induced subgraph." +
                  Fore.GREEN + "\n\n  test            " + Fore.CYAN + "Performs a series of tests to check "
                                                                    "the integrity of Pyntacle. Useful to test if\n                  "
                                                                    "Pyntacle was installed correctly and for debugging "
                                                                    "tasks.\n" +
                  Style.RESET_ALL + 100 * "-", )

        parser.add_argument("command", help="Subcommand to run", type=lambda s: s.lower())
        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")
        parser.add_argument("-V", "--version", action="version", version="Pyntacle v1.0.0",
                            help="Shows program version number and quits.")

        # Detect verbosity
        for arg in sys.argv:
            if arg in ["-v", "-vv", "-vvv"]:
                verbosity = arg.count("v")
        # Logging levels setup
        if verbosity == 2:
            log.setLevel(logging.INFO)
        elif verbosity >= 3:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.WARN)

        # Continue parsing of the first two arguments
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command) and args.command != "test":
            sys.stdout.write("Unrecognized command.\n")
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name
        if args.command == "test":
            self.pyntacle_test()
        else:
            getattr(self, args.command)()

    def keyplayer(self):
        parser = argparse.ArgumentParser(
            description="Computes key player metrics for a specific set of nodes ('kp-info') or performs the "
                        "search of node set that hold the optimal or the best key player index value ('kp-finder').\n\n"
                        "Subcommands:\n\n" + 100 * "-" + "\n" +
                        "   kp-finder\t           Finds the best kp set of size k using key player metrics by means of "
                        "either a\n\t\t\t  greedy or a brute-force algorithm.\n\n"
                        "   kp-info\t           Computes specified key player metrics for a selected subset of nodes.\n" + 100 * "-",
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=100,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle keyplayer"
                  + Fore.GREEN + Style.BRIGHT + " {kp-finder, kp-info}"
                  + Fore.LIGHTBLUE_EX + " --type {all | pos | neg | F | dF | dR | mreach}" + Fore.RED + " [arguments]\n" + Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument("-i", "--input-file", metavar="",
                            help="(REQUIRED) Path to the input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")

        # These are options instead
        parser.add_argument("-f", "--format", metavar="",
                            choices=format_dictionary.keys(),
                            help="Input network file format: 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information on the network file formats "
                                 "and other available abbreviations. If not specified, the input format will be guessed.")

        parser.add_argument("--input-separator", metavar="", default=None,
                            help="The field separator for the input file. "
                                 "If not provided, Pyntacle tries to "
                                 "guess it automatically.")

        parser.add_argument("-N", "--no-header", default=False, action="store_true",
                            help="A flag that must be specified if the input network file (adjacency matrix, edge list, SIF file) "
                                 "does not contain a header. By default, we assume a header is present.")
        parser.add_argument("-m", "--m-reach", metavar="", type=int, help="The maximum "
                                                                          "distance that will be "
                                                                          "used to compute the m-reach "
                                                                          "metric. Must be provided if m-reach"
                                                                          " is computed.")

        parser.add_argument("-M", "--max-distance", metavar="", type=int, help="(OPTIONAL) The number of steps after"
                                                                               " which two nodes will be considered as "
                                                                               "disconnected. By default, "
                                                                               "no maximum distance is set.")

        parser.add_argument("-t", "--type", metavar="", choices=["pos", "neg", "all", "F", "dF", "dR", "mreach"],
                            default="all",
                            help="The key player metric (or metrics) of interest. Choices are: "
                                 "'all' (all metrics), 'pos' (reachabiliy metrics: dR and m-reach),"
                                 " 'neg' (fragmentation metrics: F dF). 'dR', 'mreach', 'F', "
                                 "'dF'. Default is 'all'.")

        parser.add_argument("-L", "--largest-component", action="store_true",
                            help="Considers only the largest component of the input graph and excludes the smaller ones."
                                 "It will raise an error if the network has two largest"
                                 " components of the same size.")

        parser.add_argument("-d", "--directory", metavar="", default=os.getcwd(),
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("-r", "--report-format", metavar="", default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            type=lambda s: s.lower(),
                            help="The format of the report produced by "
                                 "Pyntacle. Choices are: 'txt' and 'tsv' (tab-separated file), 'csv' "
                                 "(comma-separated value file), 'xlsx' (Excel file). Default is 'txt'.")

        parser.add_argument("-P", "--plot-format", choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(), metavar="",
                            help="The format for the network representation produced by "
                                 "Pyntacle. Choices are: 'pdf', 'png' and 'svg'. Defaults to 'pdf'. "
                                 "Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-dim", metavar="",
                            help="The dimensions (as comma-separated values) of the graphical representation of the "
                                 "results. Default is '800,800' for graph with less than 150 nodes and '1600,1600' "
                                 "otherwise. Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-layout", metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="Specifies one of the predefined layout for the graphical representation of the network. "
                                 "Choices are: 'fruchterman_reingold', 'kamada_kawai', "
                                 "'large_graph', 'random', 'reingold_tilford'. Default is "
                                 "'fruchterman_reingold'. Bypassed if the '--no-plot' flag if specified or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--no-plot", action="store_true",
                            help="Skips the graphical representation of the plot.")

        parser.add_argument("--save-binary", action="store_true",
                            help="Saves a binary file (ending in '.graph') that contains the network "
                                 "and all the operations performed on it in an 'igraph.Graph' object.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)

        # Subparser for the kp-info case
        info_case_parser = subparsers.add_parser("kp-info",
                                                 usage="pyntacle keyplayer kp-info [-h] [-m] [-f] [-N] [-d] [-L] [-M] [-T] [--input-separator] [--save-binary] [--report-format] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input-file [FILE] --nodes NODES",
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        info_case_parser.set_defaults(which="kp-info")
        info_case_parser.add_argument("-n", "--nodes",
                                      help="(REQUIRED) Comma-separated list of strings, corresponding to the node names in the input graph, or column index of the input network file if the 'no-header' flag is specified.",
                                      required=True)
        # Subparser for kp-finder case
        finder_case_parser = subparsers.add_parser("kp-finder",
                                                   usage="pyntacle keyplayer kp-finder [-h] [-m] [-f] [--input-separator] [-N] [-d] [-L] [-M] [-T] [-I] [-S] [--save-binary] [--report-format] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input-file [FILE] -k [K]",
                                                   add_help=False, parents=[parser],
                                                   formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                       max_help_position=100,
                                                                                                       width=150))
        finder_case_parser.add_argument("-k", "--k-size", metavar="", type=int,
                                        help="(REQUIRED) An integer specifying the size of the node set size.",
                                        required=True)

        finder_case_parser.add_argument("-I", "--implementation", metavar="", type=str, default="greedy",
                                        choices=["brute-force", "greedy"],
                                        help="The strategy used for the search of the node set. Choices are: 'greedy' "
                                             "(a greedy optimization algorithm aimed at finding an optimal solution) "
                                             "and 'brute-force' for a brute-force search that find the best solution "
                                             "(or solutions). 'greedy' is the default strategy.")

        finder_case_parser.add_argument("-S", "--seed", type=int, help="(GREEDY OPTIMIZATION ONLY) Sets a user-defined "
                                                                       "seed to replicate the greedy optimization search.",
                                        metavar="", default=None)
        finder_case_parser.add_argument("-T", "--threads", metavar="", default=n_cpus, type=threads_type,
                                        help="Specifies the number of cores that will be used in brute-force. Defaults to "
                                             "the maximum number of cores available in your machine - 1.")

        finder_case_parser.set_defaults(which="kp-finder")

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ("kp-finder", "kp-info")):
            parser.print_help()
            raise Error(
                "Usage: pyntacle keyplayer {kp-finder, kp-info} [arguments] (use --help for command description)")

        kp = kp_command(args)
        try:
            kp.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def groupcentrality(self):
        parser = argparse.ArgumentParser(
            description="Computes group centrality metrics (defined in goo.gl/82Whxu) for a specific set of nodes "
                        "('gr-info') or perform the "
                        "search of set of nodes that maximize key player metrics ('group-finder').\n\n"
                        "Subcommands:\n\n" + 100 * "-" + "\n" +
                        "   gr-finder\t           Finds the optimal or the best set of size 'k' for a group centrality index (or indices) by means of either a "
                        "\n\t\t\t   greedy optimization or a brute-force algorithm.\n\n"
                        "   gr-info\t           Computes all or a selected group-centrality metric for a selected subset of nodes.\n" + 100 * "-",
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=100,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle groupcentrality"
                  + Fore.GREEN + Style.BRIGHT + " {gr-finder, gr-info}"
                  + Fore.LIGHTBLUE_EX + " --type {all | degree | closeness | betwenness }" + Fore.RED + " [arguments]\n" + Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument("-i", "--input-file", metavar="",
                            help="(REQUIRED) Path to the input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")

        # These are options instead
        parser.add_argument("-f", "--format", metavar="",
                            choices=format_dictionary.keys(),
                            help="Input network file format: 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information "
                                 "and other available abbreviations. If not specified, the input format will be guessed.")

        parser.add_argument("--input-separator", metavar="", default=None,
                            help="The field separator for the input file. "
                                 "If not provided, Pyntacle tries to guess it automatically.")

        parser.add_argument("-N", "--no-header", default=False, action="store_true",
                            help="A flag that must be used if the input network file (adjacency matrix, edge list, SIF file) "
                                 "does not contain a header. By default, we assume a header is present.")

        parser.add_argument("-t", "--type", metavar="", choices=["all", "degree", "closeness", "betweenness"],
                            default="all",
                            help="The group centrality metric (or metrics) of interest. Choices are: "
                                 "'all' (all metrics), 'degree' (group degree only),"
                                 " 'closeness' (group closeness), 'betweenness' (group betweenness).* Default is 'all'.")

        parser.add_argument("-D", "--group-distance", metavar="", choices=["mean", "min", "max"], default="min",
                            help="(REQUIRED FOR GROUP CLOSENESS) The criterion to use to compute the distance between "
                                 "the node set and the rest of the graph. "
                                 "Choices are: 'mean' (averages the distances among the node set and the rest of the graph),"
                                 "'min' (takes the minimum distance among the node set and the rest of the graph),"
                                 "'max'' (takes the maximum distance among the node set and the rest of the graph).  Defaults to 'min'.")

        parser.add_argument("-L", "--largest-component", action="store_true",
                            help="Considers only the largest component of the input graph and excludes the smaller ones."
                                 "It will raise an error if the network has two largest"
                                 " components of the same size.")

        parser.add_argument("-d", "--directory", metavar="", default=os.getcwd(),
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("-r", "--report-format", metavar="", default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            type=lambda s: s.lower(),
                            help="The format of the report produced by "
                                 "Pyntacle. Choices are: 'txt' and 'tsv' (tab-separated file), 'csv' "
                                 "(comma-separated value file), 'xlsx' (Excel file). Default is 'txt'.")

        parser.add_argument("-P", "--plot-format", choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(), metavar="",
                            help="The format for the network representation produced by "
                                 "Pyntacle. Choices are: 'pdf', 'png' and 'svg'. Defaults to 'pdf'. "
                                 "Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-dim", metavar="",
                            help="The dimensions (as comma-separated values) of the graphical representation of the "
                                 "results. Default is '800,800' for graph with less than 150 nodes and '1600,1600' "
                                 "otherwise. Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-layout", metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="Specifies one of the predefined layout for the graphical representation of the network. "
                                 "Choices are: 'fruchterman_reingold', 'kamada_kawai', "
                                 "'large_graph', 'random', 'reingold_tilford'. Default is "
                                 "'fruchterman_reingold'. Bypassed if the '--no-plot' flag if specified or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--no-plot", action="store_true",
                            help="Skips the graphical representation of the plot.")

        parser.add_argument("--save-binary", action="store_true",
                            help="Saves a binary file (ending in '.graph') that contains the network "
                                 "and all the operations performed on it in an 'igraph.Graph` object.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)

        # Subparser for the kp-info case
        info_case_parser = subparsers.add_parser("gr-info",
                                                 usage="pyntacle keyplayer kp-info [-h] [-f] [-N] [-d] [-L] [-M] [-T] [--input-separator] [--save-binary] [--report-format] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input-file [FILE] --nodes NODES",
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        info_case_parser.set_defaults(which="gr-info")
        info_case_parser.add_argument("-n", "--nodes",
                                      help="(REQUIRED) Comma-separated list of strings, corresponding to the node names in the input graph, or column index of the input network file if the 'no-header' flag is specified.",
                                      required=True)
        # Subparser for kp-finder case
        finder_case_parser = subparsers.add_parser("gr-finder",
                                                   usage="pyntacle keyplayer kp-finder [-h] [-f] [--input-separator] [-N] [-d] [-L] [-M] [-T] [-I] [-S] [--save-binary] [--report-format] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input-file [FILE] -k [K]",
                                                   add_help=False, parents=[parser],
                                                   formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                       max_help_position=100,
                                                                                                       width=150))
        finder_case_parser.add_argument("-k", "--k-size", metavar="", type=int,
                                        help="(REQUIRED) An integer specifying the size of the node set size.",
                                        required=True)

        finder_case_parser.add_argument("-I", "--implementation", metavar="", type=str, default="greedy",
                                        choices=["brute-force", "greedy"],
                                        help="The strategy used for the search of the node set. Choices are: 'greedy' (a greedy optimization algorithm aimed at finding an optimal solution) "
                                             "and 'brute-force' for a brute-force search that find the best solution (or solutions). 'greedy' is the default strategy.")

        finder_case_parser.add_argument("-S", "--seed", type=int,
                                        help="(GREEDY OPTIMIZATION ONLY) Sets a user-defined seed to replicate the greedy optimization search.",
                                        metavar="", default=None)
        finder_case_parser.add_argument("-T", "--threads", metavar="", default=n_cpus, type=threads_type,
                                        help="(BRUTE-FORCE SEARCH ONLY) Specifies the number of cores that will be used in brute-force. Defaults to "
                                             "the maximum number of cores available in your machine - 1.")

        finder_case_parser.set_defaults(which="gr-finder")

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ("gr-finder", "gr-info")):
            parser.print_help()
            raise Error(
                "Usage: pyntacle groupcentrality {gr-finder, gr-info} [arguments] (use --help for command description)")

        gr = gr_command(args)
        try:
            gr.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def metrics(self):

        parser = argparse.ArgumentParser(
            description="Computes various types of metrics for a set of nodes of a network or for the whole graph.\n\n"
                        "Subcommands:\n\n" + 90 * "-" + "\n" +
                        "  global\tComputes global centrality measures for the whole graph. Can also be used"
                        "\n\t\tto remove nodes from the graph and computing these global centrality"
                        "\n\t\tmeasures before and after the node removal. \n\n"
                        "  local\t        Computes local centrality measures for a single node, a group of nodes "
                        "\n\t\tor all nodes in the graph.\n"
                        + 90 * "-",

            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=100,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle metrics" + Fore.GREEN + Style.BRIGHT + " {global, local}" + Fore.RED +
                  " [arguments]" + Style.RESET_ALL)
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument("-i", "--input-file", metavar="",
                            help="(REQUIRED) Path to the input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")
        # These are options instead
        parser.add_argument("-f", "--format", metavar="",
                            choices=format_dictionary.keys(),
                            help="Input network file format: 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information "
                                 "and other available abbreviations. If not specified, the input format will be guessed.")

        parser.add_argument("--input-separator", metavar="", default=None,
                            help="The field separator for the input file. "
                                 "If not provided, Pyntacle tries to guess it automatically.")

        parser.add_argument("-N", "--no-header", default=False, action="store_true",
                            help="A flag that must be used if the input network file (adjacency matrix, edge list, SIF file) "
                                 "does not contain a header. By default, we assume a header is present.")

        parser.add_argument("-d", "--directory", default=os.getcwd(), metavar="",
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("--report-format", "-r", metavar="", default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            help="The format of the report produced by "
                                 "Pyntacle. Choices are: 'txt' and 'tsv' (tab-separated file), 'csv' "
                                 "(comma-separated value file), 'xlsx' (Excel file). Default is 'txt'.")

        parser.add_argument("-P", "--plot-format", metavar="", choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="The format for the network representation produced by "
                                 "Pyntacle. Choices are: 'pdf', 'png' and 'svg'. Defaults to 'pdf'. "
                                 "Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-dim",
                            help="The dimensions (as comma-separated values) of the graphical representation of the "
                                 "results. Default is '800,800' for graph with less than 150 nodes and '1600,1600' "
                                 "otherwise. Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--no-plot", action="store_true",
                            help="Skips the graphical representation of the plot.")

        parser.add_argument("--plot-layout", metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="Specifies one of the predefined layout for the graphical representation of the network. "
                                 "Choices are: 'fruchterman_reingold', 'kamada_kawai', "
                                 "'large_graph', 'random', 'reingold_tilford'. Default is "
                                 "'fruchterman_reingold'. Bypassed if the '--no-plot' flag if specified or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--save-binary", action="store_true",
                            help="Saves a binary file (ending in '.graph') that contains the network "
                                 "and all the operations performed on it in an 'igraph.Graph' object.")

        parser.add_argument("-L", "--largest-component", action="store_true",
                            help="Considers only the largest component of the input graph and excludes the smaller ones."
                                 "It will raise an error if the network has two largest"
                                 " components of the same size.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count",
                            help="Verbosity level of the internal Pyntacle logger. "
                                 "-vvv is the highest level (for debugging purposes).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)

        # Subparser for the nodes case
        local_subparser = subparsers.add_parser("local",
                                                usage="pyntacle metrics local [-h] [-f] [-N] [-L] [--input-separator] [--save-binary] [--plot-format] [--plot-dim] [--no-plot] --input-file [FILE] --nodes NODES",
                                                add_help=False, parents=[parser],
                                                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                    max_help_position=100,
                                                                                                    width=150))
        local_subparser.add_argument("-n", "--nodes",
                                     help="(REQUIRED) Comma-separated list of strings, corresponding to the node names "
                                          "in the input graph, or column index of the input network file if the "
                                          "'no-header' flag is specified. If not specified, local centrality indices"
                                          "will be computed for all nodes in the input graph.")

        local_subparser.add_argument("--damping-factor", default=0.85, type=float,
                                     help="A float specifying the damping "
                                          "factor that will be used to compute the PageRank index. Default is 0.85.")

        local_subparser.add_argument("--weights", "-w", type=str, default=None,
                                     help="Path to an edge attribute file storing weights that will be used to "
                                          "compute the PageRank index. Must be either a standard edge "
                                          "attribute file or a Cytoscape legacy attribute file. See https://goo.gl/9wFRfM for more details on edge attribute files."
                                          "NOTE: A column named 'weights' must be present in the edge attribute file.")

        local_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                     default="standard",
                                     help="The format of the input "
                                          "edge attribute file. Choices are: 'standard' for "
                                          " a standard edge attributes file  or "
                                          "'cytoscape' for the Cytoscape legacy attribute file. "
                                          "See https://goo.gl/9wFRfM for more details on edge attribute files."
                                          "Default is 'standard'.")

        local_subparser.set_defaults(which="local")

        # Subparser for global case
        global_subparser = subparsers.add_parser("global",
                                                 usage="pyntacle metrics global [-h] [-f] [-N] [-L] [--input-separator] [--save-binary] [--plot-format] [--plot-dim] [--no-plot] --input-file [FILE] -n/--no-nodes",
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        global_subparser.add_argument("-n", "--no-nodes", metavar="", type=str,
                                      help="Comma-separated list corresponding to vertices names or a list of indices "
                                           "matching the column index in the node adjacency matrix if 'no-header' "
                                           "is specified. These nodes will be removed from the input graph, and global "
                                           "metrics will be computed before and after the node removal.")

        global_subparser.set_defaults(which="global")

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ("global", "local")):
            raise Error("usage: pyntacle metrics {global, local} [arguments] (use --help for command description)")

        sys.stdout.write("Running Pyntacle metrics...\n")
        mt = metrics_command(args)
        try:
            mt.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def convert(self):
        parser = argparse.ArgumentParser(
            description="Converts a network file from one format to another.",
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle convert [arguments]" + Style.RESET_ALL)

        parser.add_argument("-i", "--input-file", metavar="",
                            help="(REQUIRED) Path to the input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")
        # These are options instead
        parser.add_argument("-f", "--format", metavar="",
                            choices=format_dictionary.keys(),
                            help="Input network file format: 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information "
                                 "and other available abbreviations. If not specified, the input format will be guessed.")

        parser.add_argument("--input-separator", metavar="", default=None,
                            help="The field separator for the input file. "
                                 "If not provided, Pyntacle tries to guess it automatically.")

        parser.add_argument("-N", "--no-header", default=False, action="store_true",
                            help="A flag that must be used if the input network file (adjacency matrix, edge list, SIF file) "
                                 "does not contain a header. By default, we assume a header is present.")

        parser.add_argument("--no-output-header", default=False, action="store_true",
                            help="Skips the creation of a header for the resulting network file if the output format is"
                                 " an adjacency matrix, an edge list or a SIF file. See https://goo.gl/9wFRfM for more "
                                 "details on accepted network file formats and their specifics."
                                 "If not specified the output network files will contain a header by default.")

        parser.add_argument("-d", "--directory", metavar="", default=os.getcwd(),
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("--output-file", "-o", metavar="",
                            help="Basename of the output network file. If not specified, the basename of the output "
                                 "file will be the same as the input network file.")

        parser.add_argument("-u", "--output-format", metavar="", required=True,
                            choices=format_dictionary.keys(),
                            help="(REQUIRED) The output network file format. The same abbreviations used in the "
                                 "'--format' are applied. See https://goo.gl/9wFRfM for more information on available "
                                 "network file formats and the complete list of abbreviations.")

        parser.add_argument("--output-separator", metavar="",
                            help="The field separator of the output network file. Default is '\t'."
                                 " NOTE: the separator must be wrapped in quotes.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")

        # NOT prefixing the argument with -- means it's not optional
        args = parser.parse_args(sys.argv[2:])
        if len(sys.argv) < 4:
            raise Error("usage: pyntacle convert [arguments] (use --help for command description)")

        if args.format is not None:
            if format_dictionary[args.format] == format_dictionary[args.output_format]:
                log.error("The output format specified is the same as the input format. Quitting.\n")
                sys.exit(0)
        sys.stdout.write("Running Pyntacle convert...\n")

        cv = convert_command(args)
        try:
            cv.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def generate(self):

        parser = argparse.ArgumentParser(
            description="Generates in silico networks based on a series of predetermined topologies.\n\n"
                        "Subcommands:\n\n" + 90 * "-" + "\n" +
                        "  random\t      Random network created using the Erdos–Renyi model.\n\n"
                        "  scale-free\t      The scale-free topology according to the "
                        "\n\t\t      model proposed by Barabási and Albert.\n\n"
                        "  tree\t              A hierarchical tree network.\n\n"
                        "  small-world\t      The small-world topology described in the Watts-Strogatz model.\n" + 90 * "-",
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle generate" + Fore.GREEN + Style.BRIGHT +
                  " {random, scale-free, tree, small-world}" + Fore.RED +
                  " [arguments]" + Style.RESET_ALL + Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional

        parser.add_argument("-d", "--directory", metavar="", default=os.getcwd(),
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("--output-file", "-o", metavar="",
                            help="Basename of the output network file. If not specified, it will default to the name of the"
                                 "network model, its nodes and edges and a random character string.")

        parser.add_argument("-u", "--output-format", metavar="",
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format for the output in silico networks.The same abbreviations used in the "
                                 "'--format' are applied. See https://goo.gl/9wFRfM for more information on available "
                                 "network file formats and the complete list of abbreviations.")

        parser.add_argument("--output-separator", metavar="",
                            help="The field separator of the output network file. Default is '\t'."
                                 " NOTE: the separator must be wrapped in quotes.")

        parser.add_argument("--no-output-header", action="store_true",
                            help="Skips the creation of a header for the resulting network file if the output format is"
                                 " an adjacency matrix, an edge list or a SIF file. See https://goo.gl/9wFRfM for more "
                                 "details on accepted network file formats and their specifics."
                                 "If not specified the output network file will contain a header by default.")

        parser.add_argument("-P", "--plot-format", choices=["svg", "pdf", "png"], metavar="", default="pdf",
                            type=lambda s: s.lower(),
                            help="The format for the network representation produced by "
                                 "Pyntacle. Choices are: 'pdf', 'png' and 'svg'. Defaults to 'pdf'. "
                                 "Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-dim", metavar="",
                            help="The dimensions (as comma-separated values) of the graphical representation of the "
                                 "results. Default is '800,800' for graph with less than 150 nodes and '1600,1600' "
                                 "otherwise. Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--no-plot", action="store_true",
                            help="Skips the graphical representation of the plot.")

        parser.add_argument("--plot-layout", metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="Specifies one of the predefined layout for the graphical representation of the network. "
                                 "Choices are: 'fruchterman_reingold', 'kamada_kawai', "
                                 "'large_graph', 'random', 'reingold_tilford'. Default is "
                                 "'fruchterman_reingold'. Bypassed if the '--no-plot' flag if specified or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("-S", "--seed", type=int, help="Sets a seed when creating a network, to replicate the "
                                                           "network construction. Overridden by '--repeat'.",
                            metavar="", default=None)

        parser.add_argument("-R", "--repeat", metavar="", type=int, default=1,
                            help="Repeats the graph generation for 'n' times. Default is 1."
                                 " NOTE: '--repeat' overrides '--seed'.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)
        # Subparser for the nodes case

        random_subparser = subparsers.add_parser("random",
                                                 usage="pyntacle generate random [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-n INT] [-p FLOAT] [-e INT]",
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        random_subparser.set_defaults(which="random")

        random_subparser.add_argument("-n", "--nodes", type=int,
                                      help="Number of vertices of the resulting random graph. "
                                           "If not specified, it will be a number between 100 and 500 (chosen randomly)")

        random_subparser.add_argument("-p", "--probability",
                                      help="The wiring probability to connect each node pair. Must be a float between 0 and 1. Default is 0.5. Overrides '--edges'.")

        random_subparser.add_argument("-e", "--edges", type=int,
                                      help="The resulting number of edges.")

        smallworld_subparser = subparsers.add_parser("small-world",
                                                     usage="pyntacle generate small-world [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-l INT] [-s INT] [--nei INT] [-p FLOAT]",
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))
        smallworld_subparser.set_defaults(which="small-world")

        smallworld_subparser.add_argument("-l", "--lattice", default=2,
                                          help="The dimension of a starting network lattice upon which the"
                                               "Watts-Strogatz model will be applied to generate the small-world. "
                                               "Default is 2. NOTE: It is highly recommended to use small values, "
                                               "as lattices spread across multiple dimensions may create critical "
                                               "memory issues.")

        smallworld_subparser.add_argument("-s", "--lattice-size", default=2,
                                          help="Size of the lattice among all dimensions. Default is 2. "
                                               "NOTE: It is highly recommended to use small values, as lattices "
                                               "spread across multiple dimensions may create critical memory issues.")

        smallworld_subparser.add_argument("--nei", default=None,
                                          help="The maximum distance in which two nodes will be connected. Default is a"
                                               "random integer between 2 and 5.")

        smallworld_subparser.add_argument("-p", "--probability", default=0.5,
                                          help="Rewiring probability. Default is 0.5")

        scalefree_subparser = subparsers.add_parser("scale-free",
                                                    usage="pyntacle generate scale-free [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-n INT] [-a INT]",
                                                    add_help=False, parents=[parser],
                                                    formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                        max_help_position=100,
                                                                                                        width=150))
        scalefree_subparser.set_defaults(which="scale-free")

        scalefree_subparser.add_argument("-n", "--nodes",
                                         help="Number of vertices of the resulting scale-free network. "
                                              "If not specified, it will be a number between 100 and 500 (chosen randomly)")

        scalefree_subparser.add_argument("-a", "--avg-edges",
                                         help="Average number of node neighbours for each vertex in the scale-free network."
                                              "If not specified, it will be a number between "
                                              "10 and 100 (chosen randomly).")

        tree_subparser = subparsers.add_parser("tree",
                                               usage="pyntacle generate tree [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-n INT] [-c INT]",
                                               add_help=False, parents=[parser],
                                               formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                   max_help_position=100,
                                                                                                   width=150))
        tree_subparser.set_defaults(which="tree")

        tree_subparser.add_argument("-n", "--nodes",
                                    help="Number of vertices of the resulting tree graph. "
                                         "If not specified, it will be a number between 100 and 500 (chosen randomly)")
        tree_subparser.add_argument("-c", "--children",
                                    help="The number of children nodes per parent. "
                                         "If not specified, will be a number between 2 and 10 (chosen randomly).")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ("random", "scale-free", "tree", "small-world")):
            raise Error(
                "usage: pyntacle generate {random, scale-free, tree, small-world} [arguments] (use --help for command description)")

        sys.stdout.write("Running Pyntacle generate...\n")
        original_args = deepcopy(args)
        for r in range(0, args.repeat):
            args = deepcopy(original_args)
            if not args.seed:
                print("generating new seed")
                args.seed = nprandom.randint(1, 1000000)
            elif args.seed and args.repeat != 1:
                sys.stdout.write(
                    "WARNING: you have supplied both --repeat greater than 1, and --seed. The former overrides"
                    "the latter, so {0} different graphs will be produced with a random seed.\n".format(
                        str(args.repeat)))
                args.seed = random.randint(1, 1000000)
            gen = generate_command(args)
            try:
                gen.run()
            except KeyboardInterrupt:
                sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def communities(self):
        parser = argparse.ArgumentParser(
            description="Detects communities of tightly connected nodes within a graph by means of different modular "
                        "decomposition algorithms. Produces several network files, each one containing an"
                        " induced subgraph of every community found. The resulting communities can be filtered by the"
                        "number of nodes or components \n\n"
                        "Subcommands:\n\n" + 90 * "-" + "\n" +
                        "  fastgreedy\t\t      Modular decomposition by means of the fastgreedy algorithm \n\n"
                        "  infomap\t\t         Modular decomposition by means of the naive implementation of the infomap algorithm.\n\n"
                        "  leading-eigenvector\t      Modular decomposition computing the leading eigenvectors for each community.\n\n"
                        "  community-walktrap\t      Modular decomposition by means of random walks within the graph.\n" + 90 * "-",
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle communities" + Fore.GREEN + Style.BRIGHT + " {fastgreedy, "
                                                                                                 "infomap, leading-eigenvector, community-walktrap} " + Fore.RED + "[arguments]" + Style.RESET_ALL)

        parser.add_argument("-i", "--input-file", metavar="",
                            help="(REQUIRED) Path to the input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")
        # These are options instead
        parser.add_argument("-f", "--format", metavar="",
                            choices=format_dictionary.keys(),
                            help="Input network file format: 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information "
                                 "and other available abbreviations. If not specified, the input format will be guessed.")

        parser.add_argument("--input-separator", metavar="", default=None,
                            help="The field separator for the input file. "
                                 "If not provided, Pyntacle tries to guess it automatically.")

        parser.add_argument("--min-nodes", "-m", help="Filters the resulting communities and keeps only those with a "
                                                      "number of vertices equal or greater than this treshold.")

        parser.add_argument("--max-nodes", "-M",
                            help="Filters the resulting communities and keeps only those with a "
                                 "number of vertices equal or lesser than this threshold.")

        parser.add_argument("--min-components", "-c",
                            help="Filters the resulting communities and keeps only those with a "
                                 "number of components equal or greater than this threshold.")

        parser.add_argument("--max-components", "-C",
                            help="Filters the resulting communities and keeps only those with a "
                                 "number of components equal or greater than this threshold.")

        parser.add_argument("-N", "--no-header", default=False, action="store_true",
                            help="A flag that must be used if the input network file (adjacency matrix, edge list, SIF file) "
                                 "does not contain a header. By default, we assume a header is present.")

        parser.add_argument("--no-output-header", action="store_true",
                            help="Skips the creation of a header for the resulting network files if the output format is"
                                 " an adjacency matrix, an edge list or a SIF file. See https://goo.gl/9wFRfM for more "
                                 "details on accepted network file formats and their specifics."
                                 "If not specified the output network files will contain a header by default.")

        parser.add_argument("-d", "--directory", default=os.getcwd(), metavar="",
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("--output-file", "-o", metavar="",
                            help="Basename of the output network files. If not specified, a standard name will be "
                                 "generated.")

        parser.add_argument("-u", "--output-format", metavar="",
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format for the output network files storing communities. The same "
                                 "abbreviations used in the '--format' are applied. See https://goo.gl/9wFRfM for "
                                 "more information on available network file formats and the complete list of abbreviations.")

        parser.add_argument("--output-separator", metavar="",
                            help="The field separator of the output network file. Default is '\t'."
                                 " NOTE: the separator must be wrapped in quotes.")

        parser.add_argument("-P", "--plot-format", choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="The format for the network representation produced by "
                                 "Pyntacle. Choices are: 'pdf', 'png' and 'svg'. Defaults to 'pdf'. "
                                 "Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-dim",
                            help="The dimensions (as comma-separated values) of the graphical representation of the "
                                 "results. Default is '800,800' for graph with less than 150 nodes and '1600,1600' "
                                 "otherwise. Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-layout", metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="Specifies one of the predefined layout for the graphical representation of the network. "
                                 "Choices are: 'fruchterman_reingold', 'kamada_kawai', "
                                 "'large_graph', 'random', 'reingold_tilford'. Default is "
                                 "'fruchterman_reingold'. Bypassed if the '--no-plot' flag if specified or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--no-plot", action="store_true",
                            help="Skips the graphical representation of the plot.")

        parser.add_argument("--save-binary", action="store_true",
                            help="Saves a binary file (ending in '.graph') that contains the network "
                                 "and all the operations performed on it in an 'igraph.Graph' object")

        parser.add_argument("-L", "--largest-component", action="store_true",
                            help="Considers only the largest component of the input graph and excludes the smaller ones."
                                 "It will raise an error if the network has two largest"
                                 " components of the same size.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)

        fastgreedy_subparser = subparsers.add_parser("fastgreedy",
                                                     usage="pyntacle communities fastgreedy [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE] [--weights FILE] [--weights-format] [--clusters]",
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))

        fastgreedy_subparser.set_defaults(which="fastgreedy")

        fastgreedy_subparser.add_argument("--weights", metavar="",
                                          help="Path to an edge attribute file storing weights that will be passed to the"
                                               "fastgreedy algorithm. Must be either a standard edge attribute file or a "
                                               "Cytoscape legacy attribute file. "
                                               "See https://goo.gl/9wFRfM for more details on edge attribute files."
                                               "NOTE: A column named 'weights' must be present in the edge attribute file.")

        fastgreedy_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                          default="standard",
                                          help="The format of the input "
                                               "edge attribute file. Choices are: 'standard' for "
                                               " a standard edge attributes file  or "
                                               "'cytoscape' for the Cytoscape legacy attribute file. "
                                               "See https://goo.gl/9wFRfM for more details on edge attribute files."
                                               "Default is 'standard'.")

        fastgreedy_subparser.add_argument("--clusters", metavar="",
                                          help="Specifies the number of clusters around which the modular decomposition "
                                               "algorithm will optimize its module search.")

        infomap_subparser = subparsers.add_parser("infomap",
                                                  usage="pyntacle communities infomap [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE]",
                                                  add_help=False, parents=[parser],
                                                  formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                      max_help_position=100,
                                                                                                      width=150))
        infomap_subparser.set_defaults(which="infomap")

        leading_eigenvector_subparser = subparsers.add_parser("leading-eigenvector",
                                                              usage="pyntacle communities leading-eigenvector [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE]",
                                                              add_help=False, parents=[parser],
                                                              formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                                  max_help_position=100,
                                                                                                                  width=150))
        leading_eigenvector_subparser.set_defaults(which="leading-eigenvector")

        community_walktrap_subparser = subparsers.add_parser("community-walktrap",
                                                             usage="pyntacle communities community-walktrap [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE] [--clusters] [--steps] [--weights] [--weights-format]",
                                                             add_help=False, parents=[parser],
                                                             formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                                 max_help_position=100,
                                                                                                                 width=150))
        community_walktrap_subparser.set_defaults(which="community-walktrap")

        community_walktrap_subparser.add_argument("--weights",
                                                  help="Path to an edge attribute file storing weights that will be "
                                                       "passed to the walktrap algorithm. Must be either a standard "
                                                       "edge attribute file or a Cytoscape legacy attribute file. "
                                                       "See https://goo.gl/9wFRfM for more details on edge attribute files."
                                                       "NOTE: A column named 'weights' must be present in the edge attribute file.")
        community_walktrap_subparser.add_argument("--clusters",
                                                  help="Specifies the number of clusters around which the modular "
                                                       "decomposition algorithm will optimize its module search.")

        community_walktrap_subparser.add_argument("--steps",
                                                  help="Specifies the maximum number of steps for the random walker. "
                                                       "High number of steps leads to lesser cohese communities. "
                                                       "Default is 3.", default="3")

        community_walktrap_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                                  default="standard",
                                                  help="The format of the input "
                                                       "edge attribute file. Choices are: 'standard' for "
                                                       " a standard edge attributes file  or "
                                                       "'cytoscape' for the Cytoscape legacy attribute file. "
                                                       "See https://goo.gl/9wFRfM for more details on edge attribute files."
                                                       "Default is 'standard'.")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (
                sys.argv[2] not in ("fastgreedy", "infomap", "leading-eigenvector", "community-walktrap")):
            raise Error(
                "usage: pyntacle communities {fastgreedy, infomap, leading-eigenvector, community-walktrap} [arguments] (use --help for command description)")

        sys.stdout.write("Running Pyntacle communities...\n")

        comm = communities_command(args)
        try:
            comm.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def set(self):

        parser = argparse.ArgumentParser(
            description="Performs set operations (union, intersection, difference) between two networks using"
                        "logical graph operations.\n\n"
                        "Subcommands:\n\n" + 90 * "-" + "\n" +
                        "  intersection\t      Graph intersection. Returns only the "
                        "\n\t\t      common nodes and their connecting edges among the two graphs of interest.\n\n"
                        "  union\t\t      Graph union. Returns a resulting merged graph of the original two networks, marking the common nodes"
                        "among them along with their common connecting edges"
                        "  difference\t      Performs the difference between the two input graphs. Returns the nodes "
                        "\n\t\t      and edges belonging only to the first input graph. NOTE: the difference among graph is not reciprocal"
                        + 90 * "-",
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + "pyntacle set " + Fore.GREEN + Style.BRIGHT + "{union, intersection,"
                                                                                          " difference}" + Fore.RED + " [arguments]" + Style.RESET_ALL)
        # NOT prefixing the argument with -- means it"s not optional
        parser.add_argument("-1", "--input-file-1", metavar="",
                            help="(REQUIRED) Path to the first input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")

        parser.add_argument("-2", "--input-file-2", metavar="",
                            help="(REQUIRED) Path to the first input network file. It can be an adjacency matrix, an "
                                 "edge list, a Simple Interaction (SIF) file, a DOT file or a binary "
                                 "storing an igraph.Graph object. See goo.gl/A2Q1H4 for more details.")

        parser.add_argument("-f", "--format", metavar="",
                            choices=format_dictionary.keys(),
                            help="Specifies the format of the input files passed using the -1/--input-file-1 "
                                 "and the -2/--input-file-2 command. Different file formats can be specified "
                                 "using different keywords e.g. 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information"
                                 "and other available abbreviations. If not specified, the input format will be guessed."
                                 "NOTE: The two network files MUST have the same format. If not, use "
                                 "'pyntacle convert' to convert them to a common accepted network file format.")

        parser.add_argument("--input-separator", metavar="", default=None,
                            help="The field separator for the input files. "
                                 "If not provided, Pyntacle tries to guess it automatically.")

        parser.add_argument("-N", "--no-header", "-n", action="store_true",
                            help="A flag that must be used if the input network file (adjacency matrix, edge list, SIF file) "
                                 "does not contain a header. By default, we assume a header is present.")

        parser.add_argument("-d", "--directory", metavar="", default=os.getcwd(),
                            help="The directory that will store Pyntacle results. If the directory does not "
                                 "exist, it will be created at the desired location. Default is the current "
                                 "working directory.")

        parser.add_argument("-P", "--plot-format", choices=["svg", "pdf", "png"], default="pdf", metavar="",
                            type=lambda s: s.lower(),
                            help="The format for the network representation produced by "
                                 "Pyntacle. Choices are: 'pdf', 'png' and 'svg'. Defaults to 'pdf'. "
                                 "Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-dim", metavar="",
                            help="The dimensions (as comma-separated values) of the graphical representation of the "
                                 "results. Default is '800,800' for graph with less than 150 nodes and '1600,1600' "
                                 "otherwise. Overridden by the '--no-plot' flag or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--plot-layout", metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="Specifies one of the predefined layout for the graphical representation of the network. "
                                 "Choices are: 'fruchterman_reingold', 'kamada_kawai', "
                                 "'large_graph', 'random', 'reingold_tilford'. Default is "
                                 "'fruchterman_reingold'. Bypassed if the '--no-plot' flag if specified or if the graph "
                                 "is too big to be represented (larger than 1000 nodes).")

        parser.add_argument("--no-plot", action="store_true",
                            help="Skips the graphical representation of the plot.")

        parser.add_argument("-u", "--output-format", metavar="",
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format for the resulting network file.The same abbreviations used in the "
                                 "'--format' are applied. See https://goo.gl/9wFRfM for more information on available "
                                 "network file formats and the complete list of abbreviations.")

        parser.add_argument("--output-file", "-o", metavar="",
                            help="Basename of the output network file. If not specified, the default output basename file will ")

        parser.add_argument("--no-output-header", action="store_true",
                            help="Skips the creation of a header for the resulting network files if the output format is"
                                 " an adjacency matrix, an edge list or a SIF file. See https://goo.gl/9wFRfM for more "
                                 "details on accepted network file formats and their specifics."
                                 "If not specified the output network file will contain a header by default.")

        parser.add_argument("--output-separator", metavar="",
                            help="The field separator of the output network file. Default is '\t'."
                                 " NOTE: the separator must be wrapped in quotes.")

        parser.add_argument("-L", "--largest-component", action="store_true",
                            help="Considers only the largest component of the input graph and excludes the smaller ones."
                                 "It will raise an error if the network has two largest"
                                 " components of the same size.")

        parser.add_argument("--report-format", "-r", default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            metavar="",
                            help="The format of the report produced by "
                                 "Pyntacle. Choices are: 'txt' and 'tsv' (tab-separated file), 'csv' "
                                 "(comma-separated value file), 'xlsx' (Excel file). Default is 'txt'.")

        parser.add_argument("--suppress-cursor", action="store_true",
                            help="Suppresses the animated cursor during Pyntacle execution.")

        parser.add_argument("-v", action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging purposes).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)

        unite_subparser = subparsers.add_parser("union",
                                                usage="pyntacle set union [-h] [-1] [-2] [-f] [-N] [-d] [-L] [--input-separator] [--report-format] [-P] [--plot-dim] [--no-plot] [-o] [-u] [--output-format STR] [--output-separator] [--no-output-header]",
                                                add_help=False, parents=[parser],
                                                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                    max_help_position=100,
                                                                                                    width=150))
        unite_subparser.set_defaults(which="union")

        intersection_subparser = subparsers.add_parser("intersection",
                                                       usage="pyntacle set intersection [-h] [-1] [-2] [-f] [-N] [-d] [-L] [--input-separator] [--report-format] [-P] [--plot-dim] [--no-plot] [-o] [-u] [--output-format STR] [--output-separator] [--no-output-header]",
                                                       add_help=False, parents=[parser],
                                                       formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                           max_help_position=100,
                                                                                                           width=150))
        intersection_subparser.set_defaults(which="intersection")

        difference_subparser = subparsers.add_parser("difference",
                                                     usage="pyntacle set difference [-h] [-1] [-2] [-f] [-N] [-d] [-L] [--input-separator] [--report-format] [-P] [--plot-dim] [--no-plot] [-o] [-u] [--output-format STR] [--output-separator] [--no-output-header] ",
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))
        difference_subparser.set_defaults(which="difference")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) <= 5 or (sys.argv[2] not in ("union", "intersection", "difference")):
            raise Error(
                "usage: pyntacle set {union, intersection, difference} [arguments] (use --help for command description)")

        sys.stdout.write("Running Pyntacle set...\n")
        set = set_command(args)
        try:
            set.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def pyntacle_test(self):
        runner = unittest.TextTestRunner()
        runner.run(Suite())


if __name__ == "__main__":
    App()
