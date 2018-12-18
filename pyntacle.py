__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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
    sys.exit('Python < 3.4 is not supported. Please use "python3" instead or update your python version.')

from colorama import Fore, Style, init

if os.name == "nt":
    init(convert=True)


from cmds.cmds_utils.reporter import *
# Main commands wrappers
from cmds.keyplayer import KeyPlayer as kp_command
from cmds.metrics import Metrics as metrics_command
from cmds.convert import Convert as convert_command
from cmds.generate import Generate as generate_command
from cmds.set import Set as set_command
from cmds.communities import Communities as communities_command
from pyntacletests.test_suite import Suite


def _check_value(self, action, value):
    # converted value must be one of the choices (if specified)
    if action.choices is not None and value not in action.choices:
        args = {'value': value,
                'choices': ', '.join(map(repr, action.choices))}
        msg = 'invalid choice: %(value)r'
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
        sys.stdout.write('\n')
        sys.tracebacklimit = 0
        verbosity = 0

        # Overriding argparse's mischievous and buggy error message
        argparse.ArgumentParser._check_value = _check_value

        parser = argparse.ArgumentParser(
            description="Main description",
            usage=Fore.RED + Style.BRIGHT + 'pyntacle' + Fore.GREEN + ' <command>' + Fore.RED
                  + ''' [<args>]

The available commands in Pyntacle are:\n''' + Style.RESET_ALL + 100 * '-' +
                  Fore.GREEN + '\n  keyplayer       ' + Fore.CYAN + 'Compute key-player metrics for a specifc'
                                                                    ' set of nodes (kp-info) or perform the '
                                                                    'search of set of nodes that maximize key'
                                                                    ' player metrics (kp-finder).' +
                  Fore.GREEN + '\n  metrics         ' + Fore.CYAN + 'Compute various types of metrics for a '
                                                                    'set of nodes of a network or for the '
                                                                    'whole graph.' +
                  Fore.GREEN + '\n  convert         ' + Fore.CYAN + 'Easily convert a network file from one '
                                                                    'format to another. ' +
                  Fore.GREEN + '\n  set             ' + Fore.CYAN + 'Performs set operations (union, '
                                                                    'intersection, difference) between two '
                                                                    'networks using graph logical algorithms.'
                                                                    ' Output the resulting network, along '
                                                                    'with the attributes of the graphs '
                                                                    'of origin. ' +
                  Fore.GREEN + '\n  generate        ' + Fore.CYAN + 'Generate random networks based on '
                                                                    'several topologies (useful to compared '
                                                                    'results against predefined network '
                                                                    'topologies). ' +
                  Fore.GREEN + '\n  communities     ' + Fore.CYAN + 'Find communities within a graph using'
                                                                    'several community-finding (or modular '
                                                                    'decomposition)algorithms. It produces '
                                                                    'several network files, each containing '
                                                                    'an induced subgraph. ' 
                                                                    'Communities can be filtered by nodes and '
                                                                    'component number.' +
                  Fore.GREEN + '\n  test            ' + Fore.CYAN + 'Performs a series of tests to check '
                                                                    'Pyntacle integrity. Useful after '
                                                                    'installing Pyntacle and for debugging '
                                                                    'purposes.\n' +
                  Style.RESET_ALL + 100 * '-', )

        parser.add_argument('command', help='Subcommand to run', type=lambda s: s.lower())
        parser.add_argument('-v', action="count", help="Verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging)")
        parser.add_argument('-V', "--version", action="version", version="Pyntacle v0.2.3.3",
                            help="Shows program version number and quits")

        # Detect verbosity
        for arg in sys.argv:
            if arg in ['-v', '-vv', '-vvv']:
                verbosity = arg.count('v')
        # Logging levels setup
        if verbosity == 2:
            log.setLevel(logging.INFO)
        elif verbosity >= 3:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.WARN)

        # Continue parsing of the first two arguments
        args = parser.parse_args(sys.argv[1:2])
        
        if not hasattr(self, args.command) and args.command != 'test':
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name
        if args.command == 'test':
            self.pyntacle_test()
        else:
            getattr(self, args.command)()

    def keyplayer(self):
        parser = argparse.ArgumentParser(
            description='Compute key-player metrics for a specifc set of nodes (kp-info) or perform the '
                        'search of set of nodes that maximize key player metrics (kp-finder).\n\n'
                        'Subcommands:\n\n' + 100 * '-' + '\n' +
                        '   kp-finder\t           Finds the best kp set of size k using key player metrics and either a '
                        '\n\t\t\t   greedy or a bruteforce algorithm.\n\n'
                        '   kp-info\t           Computes specified key player metrics for a selected subset of nodes.\n' + 100 * '-',
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=100,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + 'pyntacle keyplayer'
                  + Fore.GREEN + Style.BRIGHT + ' {kp-finder, kp-info}'
                  + Fore.LIGHTBLUE_EX + ' --type {pos | neg | all | F | dF | dR | mreach}' + Fore.RED + ' [arguments]\n' + Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('-i', '--input-file', metavar='',
                            help="(Required) Path to the network input file. It can be an Adjacency Matrix, an "
                                 "Edge List, a Simple Interaction File (SIF), a DOT file or a Binary file "
                                 "storing an igraph.Graph object. See File Format Specifications on the "
                                 "website for more details.")

        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Input format. 'adjmat' for adjacency matrix, 'edgelist' for edge list, "
                                 "'sif' for Simple Interaction format, 'dot' for DOT file, 'bin' "
                                 "for binary file. See https://goo.gl/9wFRfM for more information and abbreviations.")

        parser.add_argument('--input-separator', metavar='', default=None, help="Specifies the field separator for the input file. "
                                    
                                                                                "If not provided, Pyntacle tries to guess it automatically.")
                            
        parser.add_argument('-N', '--no-header', default=False, action='store_true',
                            help='Specify this option if your input text file with an optional header '
                                 '(Adjacency Matrix, Edge List, SIF file) doesn’t contain one. By default, '
                                 'we assume a header is present.')
        parser.add_argument('-m', '--m-reach', metavar='', type=int, help='(Required for mreach) The maximum '
                                                                          'distance that will be '
                                                                          'used when computing the mreach '
                                                                          'metric. Must be provided if mreach'
                                                                          ' is computed.')
        
        parser.add_argument('-M', '--max-distances', metavar='', type=int, help='(Optional) The number of steps upon which two nodes are considered disconnected. By default, no maximum distance is set.')

        parser.add_argument('-t', "--type", metavar='', choices=['pos', 'neg', 'all', 'F', 'dF', 'dR', 'mreach'], default='all',
                            help="The key player metric(s) that will be computed by Pyntacle. Choices are "
                                 "'all' (all metrics), 'pos' (all reachability metrics, hence dR and mreach),"
                                 " 'neg' (all fragmentation metrics, both F and dF). 'dR', 'mreach', 'F', "
                                 "'dF'. Default is 'all'.")
        
        parser.add_argument('-L', '--largest-component', action='store_true',
                            help='Use this option only to consider the largest component of the input network'
                                 ' and exclude any other one. Useful when the network contains small '
                                 'components or isolates. Will raise an error if the network has two largest'
                                 ' components of the same size.')

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will store Pyntacle results. If the directory does not "
                                 "exist, we will create one at the specified path. Default is the present "
                                 "working directory.")

        parser.add_argument('-r', '--report-format', metavar='', default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            type=lambda s: s.lower(),
                            help="Specifies the format that will be used to output the report produced by "
                                 "Pyntacle. Choices are “txt” and “tsv” for tab separated value files, “csv” "
                                 "for comma-separated value files, “xlsx” for Excel files. Default is “txt”.")

        parser.add_argument('-P', '--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(), metavar='',
                            help="Use this option to specify the format of choice of the plots produced by "
                                 "Pyntacle and stored in the “Plots” directory inside your output "
                                 "directory. Choices are “pdf”, “png” and “svg”. Default is “pdf”. "
                                 "Overridden by --no-plot. ")

        parser.add_argument('--plot-dim', metavar='',
                            help="Comma-separated values that specifies the size of the produced plot(s)."
                                 " Default is “800,800” for graph <= 150 nodes and “1600,1600” for larger "
                                 "graphs. Overridden by --no-plot. ")

        parser.add_argument('--plot-layout', metavar='',
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="This option allows to choose one of the predefined layout for network "
                                 "plotting. Choices are “fruchterman_reingold” (default), “kamada_kawai”, "
                                 "“large_graph”, “random”, “reingold_tilford”. Default is "
                                 "“fruchterman_reingold”. Bypassed if `--no-plot` if specified or the graph "
                                 "exceeds the maximum number of nodes. See The full command line guide at "
                                 "https://goo.gl/p9gN62 for more information.")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not ouput the graphical representation of the plot.")
        
        parser.add_argument("--save-binary", action="store_true",
                            help="Save a binary file (with a .graph extension) that contains an igraph.Graph "
                                 "object. This object is the one processed by Pyntacle. ")

        parser.add_argument('--suppress-cursor', action="store_true", help="suppress Pyntacle animated cursor")
        
        parser.add_argument('-v', action="count", help="verbosity level of the internal Pyntacle logger. "
                                                       "-vvv is the highest level (for debugging).")

        
        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        # Subparser for the kp-info case
        info_case_parser = subparsers.add_parser("kp-info",
                                                  usage='pyntacle keyplayer kp-info [-h] [-m] [-f] [-N] [-d] [-L] [-M] [-T] [--input-separator] [--save-binary] [--report-format] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input-file [FILE] --nodes NODES',
                                                  add_help=False, parents=[parser],
                                                  formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                      max_help_position=100,
                                                                                                      width=150))
        info_case_parser.set_defaults(which='kp-info')
        info_case_parser.add_argument("-n", "--nodes", help='(Required) Comma separated list of node names. Key player metrics of choice will be computed for selected nodes. Nodes must match the node names in the input graph, or column index in case the input file does not have a header. Will raise an error if any of the nodes is not found. ',
                                       required=True)
        # Subparser for kp-finder case
        finder_case_parser = subparsers.add_parser("kp-finder",
                                                   usage='pyntacle keyplayer kp-finder [-h] [-m] [-f] [--input-separator] [-N] [-d] [-L] [-M] [-T] [-I] [-S] [--save-binary] [--report-format] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input-file [FILE] -k [K]',
                                                   add_help=False, parents=[parser],
                                                   formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                       max_help_position=100,
                                                                                       width=150))
        finder_case_parser.add_argument('-k', '--k-size', metavar='', type=int, default=2,
                                        help='(Required) an integer specifying the size of the desired key player set to be found. Defaults to 2.', required=True)

        finder_case_parser.add_argument('-I', '--implementation', metavar='', type=str, default="greedy",
                                        choices=["brute-force", "greedy"],
                                        help='The algorithm used for the search of key players. Choices are '
                                             '"greedy" for the greedy optimization and "brute-force" for '
                                             'bruteforce optimization. Default is "greedy".')

        finder_case_parser.add_argument("-S", "--seed", type=int, help="For greedy optimization, set a seed at the beginning of the computation. Useful for getting reproducible results. Ignored when performing bruteforce search. ",
                                        metavar="", default=None)
        finder_case_parser.add_argument('-T', "--threads", metavar='', default=n_cpus, type=threads_type,
                            help="Specify the number of cores that will be used in brute-force. Defaults to "
                                 "the maximum number of threads available in your machine - 1")
        
        finder_case_parser.set_defaults(which='kp-finder')

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])
        
        if len(sys.argv) < 4 or (sys.argv[2] not in ('kp-finder', 'kp-info')):
            parser.print_help()
            raise Error(
                'Usage: pyntacle keyplayer {kp-finder, kp-info} [arguments] (use --help for command description)')

        kp = kp_command(args)
        try:
            kp.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def group_centrality(self):
        #TODO compila da qua
        pass



    def metrics(self):

        parser = argparse.ArgumentParser(
            description='Computes various types of metrics for a set of nodes of a network or for the whole graph.\n\n'
                        'Subcommands:\n\n' + 90 * '-' + '\n' +
                        '  global\tComputes global centrality measures for the whole graph. Can also be used'
                        '\n\t\tto remove nodes from the graph and computing these global centrality'
                        '\n\t\tmeasures before and after the node removal. \n\n'
                        '  local\t        Computes local centrality measures for a single node, a group of nodes '
                        '\n\t\tor all nodes in the graph.\n'
                        + 90 * '-',

            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=100,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + 'pyntacle metrics' + Fore.GREEN + Style.BRIGHT + ' {global, local}' + Fore.RED +
                  ' [arguments]' + Style.RESET_ALL)
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('-i', '--input-file', metavar="",
                            help="(Required) Path to the network input file. It can be an Adjacency Matrix, an "
                                 "Edge List, a Simple Interaction File (SIF), a DOT file or a Binary file "
                                 "storing an igraph.Graph object. See File Format Specifications on the "
                                 "website for more details.")
        # These are options instead
        parser.add_argument('-f', '--format', metavar="",
                            choices=format_dictionary.keys(),
                            help="Specifies the format of the input file passed using the --input-file "
                                 "command. "
                                 "'adjmat' for adjacency matrix, 'edgelist' for edge list, 'sif' for "
                                 "Simple Interaction format, 'dot' for DOT file, 'bin' for binary file. "
                                 "See https://goo.gl/9wFRfM for more information and abbreviations.")

        parser.add_argument('--input-separator', metavar="", default=None, help="Specifies the field separator for the input file. "
                                                                                "If not provided, Pyntacle tries to guess it automatically.")
        
        parser.add_argument('-N', '--no-header', default=False, action='store_true',
                            help='Specify this option if your input text file with an optional header '
                                 '(Adjacency Matrix, Edge List, SIF file) doesn’t contain one. By default, '
                                 'we assume a header is present.')

        parser.add_argument('-d', "--directory", default=os.getcwd(), metavar="",
                            help="Directory that will store Pyntacle results. If the directory does not "
                                 "exist, we will create one at the specified path. Default is the present "
                                 "working directory. ")

        parser.add_argument('--report-format', '-r', metavar="", default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            help="Specifies the format that will be used to output the report produced by "
                                 "Pyntacle. Choices are “txt” and “tsv” for tab separated value files, “csv” "
                                 "for comma-separated value files, “xlsx” for Excel files. Default is “txt”.")

        parser.add_argument('-P', '--plot-format', metavar="", choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="Use this option to specify the format of choice of the plots produced by "
                                 "Pyntacle and stored in the “Plots” directory inside your output "
                                 "directory. Choices are “pdf”, “png” and “svg”. Default is “pdf”. "
                                 "Overridden by --no-plot.")

        parser.add_argument('--plot-dim',
                            help="Comma-separated values that specifies the size of the produced plot(s)."
                                 " Default is “800,800” for graph <= 150 nodes and “1600,1600” for larger "
                                 "graphs. Overridden by --no-plot.")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not ouput the graphical representation of the plot.")

        parser.add_argument('--plot-layout', metavar="",
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="This option allows to choose one of the predefined layout for network "
                                 "plotting. Choices are “fruchterman_reingold” (default), “kamada_kawai”, "
                                 "“large_graph”, “random”, “reingold_tilford”. Default is "
                                 "“fruchterman_reingold”. Bypassed if `--no-plot` if specified or the graph "
                                 "exceeds the maximum number of nodes. See The full command line guide at "
                                 "https://goo.gl/p9gN62 for more information.")
        
        parser.add_argument("--save-binary", action="store_true",
                            help="Save a binary file (with a .graph extension) that contains an igraph.Graph "
                                 "object. This object is the one processed by Pyntacle.")

        parser.add_argument('-L', '--largest-component', action='store_true',
                            help='Use this option only to consider the largest component of the input '
                                 'network and exclude any other one. Useful when the network contains small '
                                 'components or isolates. Will raise an error if the network has two largest'
                                 ' components of the same size.')

        parser.add_argument('--suppress-cursor', action="store_true", help="suppress Pyntacle animated cursor")

        parser.add_argument('-v', action="count",
                            help="Verbosity level of the internal Pyntacle logger. -vvv is the highest level"
                                 " (for debugging).")

        subparsers = parser.add_subparsers(metavar="", help=argparse.SUPPRESS)

        # Subparser for the nodes case
        local_subparser = subparsers.add_parser("local",
                                                usage='pyntacle metrics local [-h] [-f] [-N] [-L] [--input-separator] [--save-binary] [--plot-format] [--plot-dim] [--no-plot] --input-file [FILE] --nodes NODES',
                                                add_help=False, parents=[parser],
                                                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                    max_help_position=100,
                                                                                                    width=150))
        local_subparser.add_argument("-n", "--nodes",
                                     help='Comma separated list of node names on which local centrality '
                                          'metrics will be computed. Must correspond to the node names in the'
                                          ' input graph. Will raise an error if any of the nodes is not found.')
        local_subparser.add_argument("--damping-factor", default=0.85, type=float,
                                     help="When computing the pagerank centrality index, specify a damping "
                                          "factor for each node. Default is 0.85.")
        local_subparser.add_argument("--weights", "-w", type=str, default=None,
                                     help="An edge attribute file storing weights that will be used to "
                                          "compute the pagerank index. Must be either a Standard Edge "
                                          "Attribute Format or a Ctyotscape Edge Attribute format, and a "
                                          "column named 'weights' must be present. See File Format "
                                          "Specifications for more details. ")
        
        local_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                          default="standard",
                                          help="(Required for --weights) Specify the format of the input "
                                               "weights attributes file. Choices are \"standard\" for "
                                               "standard edge attributes file (a tabular file) or "
                                               "\"cytoscape\" for a Cytoscape Edge Attribute File. "
                                               "Default is \"standard\".")

        local_subparser.set_defaults(which='local')

        # Subparser for global case
        global_subparser = subparsers.add_parser("global",
                                                 usage='pyntacle metrics global [-h] [-f] [-N] [-L] [--input-separator] [--save-binary] [--plot-format] [--plot-dim] [--no-plot] --input-file [FILE] -n/--no-nodes',
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        global_subparser.add_argument('-n', '--no-nodes', metavar="", type=str,
                                      help='Remove a set of nodes and compute global metrics without these nodes.')

        global_subparser.set_defaults(which='global')

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ('global', 'local')):
            raise Error('usage: pyntacle metrics {global, local} [arguments] (use --help for command description)')

        sys.stdout.write('Running Pyntacle metrics\n')
        mt = metrics_command(args)
        try:
            mt.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def convert(self):
        parser = argparse.ArgumentParser(
            description='Easily convert a network file from one format to another.',
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + 'pyntacle convert [arguments]' + Style.RESET_ALL)

        parser.add_argument('-i', '--input-file', metavar="", required=True,
                            help=" (Required) Path to the network input file. It can be an Adjacency Matrix, "
                                 "an Edge List, a Simple Interaction File (SIF), a DOT file or a Binary file"
                                 " storing an igraph.Graph object. See File Format Specifications on "
                                 "the website for more details.")
        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Specifies the format of the input file passed using the --input-file "
                                 "command. Different file formats can be specified using different keywords:"
                                 " 'adjmat' for adjacency matrix, 'edgelist' for edge list, 'sif' for "
                                 "Simple Interaction format, 'dot' for DOT file, 'bin' for binary file.")

        parser.add_argument('--input-separator', metavar='', default=None,
                            help="Specifies the field separator for the input file. "
                                 "If not provided, Pyntacle tries to guess it automatically.")
        
        parser.add_argument('-N', '--no-header', default=False, action='store_true',
                            help='Specify this option if your input text file with an optional header '
                                 '(Adjacency Matrix, Edge List, SIF file) doesn’t contain one. By default, '
                                 'we assume a header is present.')

        parser.add_argument('--no-output-header', default=False, action='store_true',
                            help='specify this option if you don’t want a header to be written on your output'
                                 ' network files with an optional header (Adjacency Matrix, Edge List, SIF '
                                 'files). If not specified, your output files will contain a header.')

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will store Pyntacle results. If the directory does not "
                                 "exist, we will create one at the specified path. Default is the present "
                                 "working directory.")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="Basename of the output file. If not specified, a standard name will be "
                                 "generated.")

        parser.add_argument("-u", "--output-format", metavar='',
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format of resulting file. Follows the same rules of the "
                                 "`--format` options. Default is “adjmat” (Adjacency Matrix).")

        parser.add_argument("--output-separator", metavar="",
                            help="Specify a desired output separator for your output files. Default is “\t”."
                                 " Note: the separator must be specified in quotes.")

        parser.add_argument('--suppress-cursor', action="store_true", help="suppress Pyntacle animated cursor")

        parser.add_argument('-v', action="count", help="Verbosity level of the internal Pyntacle logger. -vvv"
                                                       " is the highest level (for debugging).")

        # NOT prefixing the argument with -- means it's not optional
        args = parser.parse_args(sys.argv[2:])
        if len(sys.argv) < 4:
            raise Error('usage: pyntacle convert [arguments] (use --help for command description)')

        if args.format is not None:
            if format_dictionary[args.format] == format_dictionary[args.output_format]:
                log.error("The output format specified is the same as the input format. Quitting.\n")
                sys.exit(0)
        sys.stdout.write("Running Pyntacle convert\n")

        cv = convert_command(args)
        try:
            cv.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def generate(self):

        parser = argparse.ArgumentParser(
            description='Generate random networks based on several topologies (useful to compared results '
                        'against predefined network topologies).\n\n'
                        'Subcommands:\n\n' + 90 * '-' + '\n' +
                        '  random\t      Generate a random network following the Erdos–Renyi model.\n\n'
                        '  scale-free\t      Generate a network following scale free topology according to the '
                        '\n\t\t      model proposed by Barabási and Albert.\n\n'
                        '  tree\t              Generate a network that follow a tree topology, as described here.\n\n'
                        '  small-world\t      Generate a network following the Watts-Strogatz model.\n'+ 90 * '-',
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + 'pyntacle generate' + Fore.GREEN + Style.BRIGHT +
                  ' {random, scale-free, tree, small-world}' + Fore.RED +
                  ' [arguments]' + Style.RESET_ALL+ Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will store Pyntacle results. If the directory does not "
                                 "exist, we will create one at the specified path. Default is the present "
                                 "working directory.")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="Basename of the output file. If not specified, a standard name will be "
                                 "generated.")

        parser.add_argument("-u", "--output-format", metavar="",
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format for the output communities. 'adjmat' for "
                                 "'adjacency matrix', 'edgelist' for edge list, 'sif' for "
                                 "Simple Interaction format, 'dot' for DOT file, 'bin' for binary file. "
                                 "'See https://goo.gl/9wFRfM for more information and abbreviations.")

        parser.add_argument("--output-separator", metavar="",
                            help="Specify a desired output separator for your output files. Default is “\t”."
                                 " Note: the separator must be specified in quotes.")

        parser.add_argument("--no-output-header", action="store_true",
                            help='Specify this option if you don’t want a header to be written on your'
                                 ' output network files with an optional header (Adjacency Matrix, Edge List,'
                                 ' SIF files). If not specified, your output files will contain a header.')

        parser.add_argument('-P', '--plot-format', choices=["svg", "pdf", "png"], metavar='', default="pdf",
                            type=lambda s: s.lower(),
                            help="Use this option to specify the format of choice of the plots produced by "
                                 "Pyntacle and stored in the “Plots” directory inside your output"
                                 " directory. Choices are “pdf”, “png” and “svg”. Default is “pdf”."
                                 " Overridden by --no-plot.")

        parser.add_argument('--plot-dim', metavar='',
                            help="Comma-separated values that specifies the size of the produced plot(s). "
                                 "Default is “800,800” for graph <= 150 nodes and “1600,1600” for larger "
                                 "graphs. Overridden by --no-plot.")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not ouput the graphical representation of the plot.")
        
        parser.add_argument('--plot-layout', metavar='',
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="This option allows to choose one of the predefined layout for network "
                                 "plotting. Choices are “fruchterman_reingold”, “kamada_kawai”, "
                                 "“large_graph”, “random”, “reingold_tilford”. The default choice depends on "
                                 "the kind of graph that is generated. Bypassed if `--no-plot` if specified or the graph "
                                 "exceeds the maximum number of nodes. See The full command line guide at "
                                 "https://goo.gl/p9gN62 for more information.")

        parser.add_argument("-S", "--seed", type=int, help="Set a seed when creating a network (useful for "
                                                           "recreating the same networks). Overridden by --repeat",
                            metavar="", default=None)
        
        parser.add_argument("-R", "--repeat", metavar='', type=int, default=1,
                            help="Specify the number of graphs that will be generated. Default is 1."
                                 " Note: --repeat overrides --seed.")

        parser.add_argument('--suppress-cursor', action="store_true", help="suppress Pyntacle animated cursor")
        
        parser.add_argument('-v', action="count", help="Verbosity level of the internal Pyntacle logger. -vvv"
                                                       " is the highest level (for debugging).")

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)
        # Subparser for the nodes case

        random_subparser = subparsers.add_parser("random",
                                                 usage='pyntacle generate random [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-n INT] [-p FLOAT] [-e INT]',
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        random_subparser.set_defaults(which='random')

        random_subparser.add_argument("-n", "--nodes", type=int,
                                      help="number of nodes of the output graph. If not specified, will be a number between 100 and 500 (chosen randomly)")

        random_subparser.add_argument("-p", "--probability",
                                      help="Wiring probability for connecting each node pair. Must be a float between 0 and 1. Default is 0.5. Overrides -e/--edges if specified.")

        random_subparser.add_argument("-e", "--edges", type=int,
                                      help="Resulting number of edges. Excluded if -p/--probability is present.")

        
        smallworld_subparser = subparsers.add_parser("small-world",
                                                     usage='pyntacle generate small-world [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-l INT] [-s INT] [--nei INT] [-p FLOAT]',
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))
        smallworld_subparser.set_defaults(which='small-world')

        smallworld_subparser.add_argument("-l", "--lattice", default=2,
                                          help="The lattice dimension of the starting lattice that will be "
                                               "created as a base for the small-world network. Default is 2. "
                                               "It is highly recommended to use small values, as lattices with"
                                               " a size greater than 4 can create memory load issues on "
                                               "standard desktops.")

        smallworld_subparser.add_argument("-s", "--lattice-size", default=2,
                                          help="Size of the lattice among all dimensions. Default is 2. "
                                               "It is highly recommended to keep this number low.")

        smallworld_subparser.add_argument("--nei", default=None,
                                          help="Number of steps in which two vertices will be connected. Default is choosen randomly between 2 and 5")

        smallworld_subparser.add_argument("-p", "--probability", default=0.5,
                                          help="Rewiring Probability. Default is 0.5")
        
        scalefree_subparser = subparsers.add_parser("scale-free",
                                                    usage='pyntacle generate scale-free [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-n INT] [-a INT]',
                                                    add_help=False, parents=[parser],
                                                    formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                        max_help_position=100,
                                                                                                        width=150))
        scalefree_subparser.set_defaults(which='scale-free')

        scalefree_subparser.add_argument("-n", "--nodes",
                                         help="Number of nodes of the output graph. Must be a positive integer. If not specified, it wil be a number between 100 and 500 (chosen randomly).")

        scalefree_subparser.add_argument("-a", "--avg-edges",
                                         help="Average number of edges for each node in the scale-free "
                                              "network. Must be a positive integer. If not specified, it will"
                                              " be a number between 10 and 100 (chosen randomly). ")

        tree_subparser = subparsers.add_parser("tree",
                                               usage='pyntacle generate tree [-h] [-o] [-d] [-u] [--no-output-header] [--output-separator] [--plot-format] [--plot-dim] [--no-plot] [-S INT] [-R INT] [-n INT] [-c INT]',
                                               add_help=False, parents=[parser],
                                               formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                   max_help_position=100,
                                                                                                   width=150))
        tree_subparser.set_defaults(which='tree')

        tree_subparser.add_argument("-n", "--nodes",
                                    help="Number of nodes of the output graph. Must be a positive integer. If not specified, it will be a number between 100 and 500 (chosen randomly).")
        tree_subparser.add_argument("-c", "--children",
                                    help="Positive integer representing the number of children per node branch. If not specified, will be a number between 2 and 10 (chosen randomly).")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ('random', 'scale-free', 'tree', 'small-world')):
            raise Error(
                'usage: pyntacle generate {random, scale-free, tree, small-world} [arguments] (use --help for command description)')

        sys.stdout.write('Running Pyntacle generate\n')
        original_args = deepcopy(args)
        for r in range(0, args.repeat):
            args = deepcopy(original_args)
            if not args.seed:
                print("generating new seed")
                args.seed = nprandom.randint(1,1000000)
            elif args.seed and args.repeat!=1:
                sys.stdout.write("WARNING: you have supplied both --repeat greater than 1, and --seed. The former overrides"
                                 "the latter, so {0} different graphs will be produced with a random seed.\n".format(str(args.repeat)))
                args.seed = random.randint(1,1000000)
            gen = generate_command(args)
            try:
                gen.run()
            except KeyboardInterrupt:
                sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def communities(self):
        parser = argparse.ArgumentParser(
            description='Find communities within a graph using several community-finding (or modular '
                        'decomposition) algorithms. Produces several network files, each one containing an'
                        ' induced subgraph of every community found. Communities can be filtered by nodes'
                        ' and components number.\n\n'
                        'Subcommands:\n\n' + 90 * '-' + '\n' +
                        '  fastgreedy\t\t      Performs module detection on tthe input network using the fastgreedy algorithm.\n\n'
                        '  infomap\t\t      Performs module detection on the input network using the community infomap algorithm.\n\n'
                        '  leading-eigenvector\t      Performs module detection on the input network using the leading eigenvector algorithm.\n\n'
                        '  community-walktrap\t      Performs module detection on the input network using the community walktrap algorithm.\n' + 90 * '-',
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + 'pyntacle communities' + Fore.GREEN + Style.BRIGHT + ' {fastgreedy, '
                                                                                                   'infomap, leading-eigenvector, community-walktrap} ' + Fore.RED + '[arguments]' + Style.RESET_ALL)

        parser.add_argument('-i', '--input-file', metavar='',
                            help="(Required) Path to the network input file. It can be an Adjacency Matrix, "
                                 "an Edge List, a Simple Interaction File (SIF), a DOT file or a Binary file"
                                 " storing an igraph.Graph object.")
        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Specifies the format of the input file passed using the --input-file "
                                 "command. "
                                 "'adjmat' for adjacency matrix, 'edgelist' for edge list, 'sif' for "
                                 "Simple Interaction format, 'dot' for DOT file, 'bin' for binary file. "
                                 "See https://goo.gl/9wFRfM for more information and abbreviations.")

        parser.add_argument('--input-separator', metavar='', default=None,
                            help="Specifies the field separator for the input file. "
                                 "If not provided, Pyntacle tries to guess it automatically.")
        
        parser.add_argument("--min-nodes", "-m", help="An integer specifying the minimum number of nodes that"
                                                      " a community must have to be returned. Communities "
                                                      "with a lesser number of nodes will be discarded.")

        parser.add_argument("--max-nodes", "-M",
                            help="An integer specifying the maximum number of nodes that a community must "
                                 "have to be returned. Communities with a higher number of nodes will be "
                                 "discarded.")

        parser.add_argument("--min-components", "-c",
                            help="If your community happens to have more than one component, specify the "
                                 "minimum number of components the community must have in order not to be "
                                 "filtered out. Default is 1.")

        parser.add_argument("--max-components", "-C",
                            help="If your community happens to have more than one component, specify the "
                                 "minimum number of components the community must have in order not to be "
                                 "filtered out.")

        parser.add_argument('-N', '--no-header', default=False, action='store_true',
                            help='Specify this option if your input text file with an optional header '
                                 '(Adjacency Matrix, Edge List, SIF file) doesn’t contain one. By default, '
                                 'we assume a header is present.')

        parser.add_argument("--no-output-header", action="store_true",
                            help='Specify this option if you don’t want a header to be written on your output'
                                 ' network files with an optional header (Adjacency Matrix, Edge List, SIF'
                                 ' files). If not specified, your output files will contain a header.')

        parser.add_argument('-d', "--directory", default=os.getcwd(), metavar='',
                            help="Directory that will store Pyntacle results. If the directory does not "
                                 "exist, we will create one at the specified path. Default is the present "
                                 "working directory.")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="Basename of the output file. If not specified, a standard name will be "
                                 "generated.")

        parser.add_argument("-u", "--output-format", metavar='',
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format for the output communities. Follows the same rules "
                                 "of the `--format` options. Default is “adjmat” (Adjacency Matrix).")

        parser.add_argument("--output-separator", metavar="",
                            help="specify a desired output separator for your output files. Default is “\t”. "
                                 "Note: the separator must be specified in quotes.")

        parser.add_argument('-P', '--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="Use this option to specify the format of choice of the plots produced by "
                                 "Pyntacle and stored in the “Plots” directory inside your output "
                                 "directory. Choices are “pdf”, “png” and “svg”. Default is “pdf”. "
                                 "Overridden by --no-plot.")

        parser.add_argument('--plot-dim',
                            help="Comma-separated values that specifies the size of the produced plot(s). "
                                 "Default is “800,800” for graph <= 150 nodes and “1600,1600” for larger "
                                 "graphs. Overridden by --no-plot.")
        
        parser.add_argument('--plot-layout', metavar='',
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="This option allows to choose one of the predefined layout for network "
                                 "plotting. Choices are “fruchterman_reingold” (default), “kamada_kawai”, "
                                 "“large_graph”, “random”, “reingold_tilford”. Default is "
                                 "“fruchterman_reingold”. Bypassed if `--no-plot` if specified or the graph "
                                 "exceeds the maximum number of nodes. NOTE: the layout will be passed to each "
                                 "subcommunity in the network found using modularity. See The full command "
                                 "line guide at "
                                 "https://goo.gl/p9gN62 for more information.")
        
        parser.add_argument("--no-plot", action="store_true",
                            help="Do not ouput the graphical representation of the plot.")

        parser.add_argument("--save-binary", action="store_true",
                            help="Save a binary file (with a .graph extension) in the output directory that "
                                 "contains an igraph.Graph object. This object will contain a vertex "
                                 "attribute called __module_number to retrace the corresponding community "
                                 "to which the node was assigned.")

        parser.add_argument('-L', '--largest-component', action='store_true',
                            help='Use this option if you want Pyntacle to consider only the largest component'
                                 ' of the input network and exclude any other one. Useful when the network'
                                 ' contains small components or isolates. Will raise an error if the network'
                                 ' has two largest components of the same size.')

        parser.add_argument('--suppress-cursor', action="store_true", help="suppress Pyntacle animated cursor")

        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        fastgreedy_subparser = subparsers.add_parser("fastgreedy",
                                                     usage='pyntacle communities fastgreedy [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE] [--weights FILE] [--weights-format] [--clusters]',
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))

        fastgreedy_subparser.set_defaults(which='fastgreedy')

        fastgreedy_subparser.add_argument("--weights", metavar="",
                        help="An edge attribute file storing weights that will be used to compute the "
                             "pagerank index. Must be either a Standard Edge Attribute Format or a Ctyotscape"
                             " Edge Attribute format, and a column named 'weights' must be present. See File"
                             " Format Specifications  on the website for more details. Only the first"
                             " attribute will be used. ")
        
        fastgreedy_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                          default="standard",
                                          help="(Required for --weights) Specify the format of the input weight attributes file. "
                                               "Choices are \"standard\" for standard edge attributes file "
                                               "(a tabular file) or \"cytoscape\" for a Cytoscape Edge "
                                               "Attribute File. Default is \"default\".")
        
        fastgreedy_subparser.add_argument("--clusters", metavar="",
                                          help="Specify the number of modules around which the fastgreedy "
                                               "algorithm will optimize the search. By default, this option "
                                               "is disabled. ")

        infomap_subparser = subparsers.add_parser("infomap",
                                                  usage='pyntacle communities infomap [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE]',
                                                  add_help=False, parents=[parser],
                                                  formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                      max_help_position=100,
                                                                                                      width=150))
        infomap_subparser.set_defaults(which='infomap')

        leading_eigenvector_subparser = subparsers.add_parser("leading-eigenvector",
                                                              usage='pyntacle communities leading-eigenvector [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE]',
                                                              add_help=False, parents=[parser],
                                                              formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                                  max_help_position=100,
                                                                                                                  width=150))
        leading_eigenvector_subparser.set_defaults(which='leading-eigenvector')

        community_walktrap_subparser = subparsers.add_parser("community-walktrap",
                                                             usage='pyntacle communities community-walktrap [-h] [-f] [-N] [-d] [-M] [-m] [-C] [-c] [-L] [-P] [--input-separator] [--plot-dim] [--no-plot] [--save-binary] [-o] [-u] [--no-output-header] [--output-separator] --input-file [FILE] [--clusters] [--steps] [--weights] [--weights-format]',
                                                             add_help=False, parents=[parser],
                                                             formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                                 max_help_position=100,
                                                                                                                 width=150))
        community_walktrap_subparser.set_defaults(which='community-walktrap')

        community_walktrap_subparser.add_argument("--weights",
                                                  help="An edge attribute file storing weights that will be "
                                                       "used to compute the pagerank index. Must be either a"
                                                       " Standard Edge Attribute Format or a Ctyotscape Edge"
                                                       " Attribute format, and a column named 'weights' must"
                                                       " be present. See File Format Specifications on the website for more"
                                                       " details. Only the first attribute will be used.")
        community_walktrap_subparser.add_argument("--clusters",
                                                  help="Specify the number of modules that will be ouput by"
                                                       " the module decomposition algorithm. If not"
                                                       " specified, a maximized number of modules will be"
                                                       " generated")

        community_walktrap_subparser.add_argument("--steps",
                                                  help="Specify the maximum length for random walks that will"
                                                       " be used tio find communities. The higher this"
                                                       " number, the lesser cohesive will be the communities."
                                                       " Default is 3.", default='3')

        community_walktrap_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                                  default="standard",
                                                  help="(Required for --weights) Specifies the format of the"
                                                       " input weight attributes file. Choices are "
                                                       "\"standard\" for standard edge attributes file "
                                                       "(a tabular file) or \"cytoscape\" for a Cytoscape "
                                                       "Edge Attribute File. Default is \"default\".")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (
                    sys.argv[2] not in ('fastgreedy', 'infomap', 'leading-eigenvector', 'community-walktrap')):
            raise Error(
                'usage: pyntacle communities {fastgreedy, infomap, leading-eigenvector, community-walktrap} [arguments] (use --help for command description)')

        sys.stdout.write('Running Pyntacle communities\n')

        comm = communities_command(args)
        try:
            comm.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def set(self):

        parser = argparse.ArgumentParser(
            description='Performs set operations (union, intersection, difference) between two networks using'
                        ' graph logical algorithms. Output the resulting network, along with the attributes'
                        ' of the graphs of origin.\n\n'
                        'Subcommands:\n\n' + 90 * '-' + '\n' +
                        '  intersect\t      Performs the intersection among two input graph(s). Returns only the '
                        '\n\t\t      common nodes connected by the common edges. It will also give a '
                        '\n\t\t      detailed summary regarding this operation.\n\n'
                        '  union\t\t      Performs the union among the input graph(s) (also called graph merging). '
                        '\n\t\t      Returns a graph storing both input graphs. Nodes and edges in common '
                        '\n\t\t      will retain both the original attributes belonging to them.\n\n'
                        '  difference\t      Performs the difference among the two input graphs. Returns the nodes '
                        '\n\t\t      and edges belonging only to the first input graph. NOTE: the results '
                        '\n\t\t      will differ when switching the -1/--input-file-1 and the '
                        '\n\t\t      -2/--input-file-2 arguments.\n'+ 90 * '-',
            formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(prog, width=140,
                                                                              max_help_position=100),
            usage=Fore.RED + Style.BRIGHT + 'pyntacle set ' + Fore.GREEN + Style.BRIGHT + '{union, intersection,'
                                                                                            ' difference}' + Fore.RED + ' [arguments]' + Style.RESET_ALL)
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('-1', '--input-file-1', metavar='',
                            help="(Required) Path to the first network input file for set operations. It can"
                                 " be an Adjacency Matrix, an Edge List, a Simple Interaction File (SIF), a"
                                 " DOT file or a Binary file storing an igraph.Graph object. See File Format"
                                 " Specifications on the website for more details. ")

        parser.add_argument('-2', '--input-file-2', metavar='',
                            help="(Required) Path to the second network input file for set operations. It can"
                                 " be an Adjacency Matrix, an Edge List, a Simple Interaction File (SIF), a"
                                 " DOT file or a Binary file storing an igraph.Graph object. See File Format"
                                 " Specifications on the website for more details.")

        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Specifies the format of the input file passed using the -1/--input-file-1 "
                                 "and the -2/--input-file-2 command. Different file formats can be specified "
                                 "using different keywords: 'adjmat' for adjacency matrix, 'edgelist' for "
                                 "edge list, sif for Simple Interaction format, 'dot' for DOT file, 'bin'"
                                 " for binary file. See https://goo.gl/9wFRfM for more information and "
                                 "abbreviations. NOTE: The two files must have the same format. If not, use "
                                 "pyntacle convert to convert your files to the same format")

        parser.add_argument('--input-separator', metavar='', default=None,
                            help="Specifies the field separator for the input files. "
                                 "If not provided, Pyntacle tries to guess it automatically.")
        
        parser.add_argument("-N", "--no-header", "-n", action="store_true",
                            help="Specify this option if your input text file with an optional header "
                                 "(Adjacency Matrix, Edge List, SIF file) doesn’t contain one. By default,"
                                 " we assume a header is present.")

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will store Pyntacle results. If the directory does not "
                                 "exist, we will create one at the specified path. Default is the present "
                                 "working directory.")

        parser.add_argument('-P', '--plot-format', choices=["svg", "pdf", "png"], default="pdf", metavar='',
                            type=lambda s: s.lower(),
                            help="Use this option to specify the format of choice of the plots produced by "
                                 "Pyntacle and stored in the “Plots” directory inside your output "
                                 "directory. Choices are “pdf”, “png” and “svg”. Default is “pdf”. Overridden"
                                 " by --no-plot.")

        parser.add_argument('--plot-dim', metavar="",
                            help="Comma-separated values that specifies the size of the produced plot(s). "
                                 "Default is “800,800” for graph <= 150 nodes and “1600,1600” for larger "
                                 "graphs. Overridden by --no-plot.")

        parser.add_argument('--plot-layout', metavar='',
                            choices=["circle", "fruchterman_reingold", "fr", "kamada_kawai", "kk",
                                     "large_graph", "lgl", "random", "reingold_tilford", "rt"],
                            default="fr",
                            help="This option allows to choose one of the predefined layout for network "
                                 "plotting. Choices are “fruchterman_reingold” (default), “kamada_kawai”, "
                                 "“large_graph”, “random”, “reingold_tilford”. Default is "
                                 "“fruchterman_reingold”. Bypassed if `--no-plot` if specified or the graph "
                                 "exceeds the maximum number of nodes. NOTE: the layout will be passed to both"
                                 " the input and the resulting graph. See The full command "
                                 "line guide at "
                                 "https://goo.gl/p9gN62 for more information.")
        
        parser.add_argument("--no-plot", action="store_true",
                            help="Do not ouput the graphical representation of the plot.")

        parser.add_argument("-u", "--output-format", metavar='',
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format for the resulting file(s). Follows the same rules of "
                                 "the `--format` options. Default is “adjmat” (Adjacency Matrix).")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="Basename of the output file. If not specified, a standard name will be "
                                 "generated. ")

        parser.add_argument("--no-output-header", action="store_true",
                            help='Specify this option if you don’t want a header to be written on your output'
                                 ' network files with an optional header (Adjacency Matrix, Edge List, SIF'
                                 ' files). If not specified, your output files will contain a header.')

        parser.add_argument("--output-separator", metavar="",
                            help="Specify a desired output separator for your output files. Default is “\t”."
                                 " Note: the separator must be specified in quotes.")

        parser.add_argument('-L', '--largest-component', action='store_true',
                            help='use this option if you want Pyntacle to consider only the largest component'
                                 ' of the input network and exclude any other one. Useful when the network'
                                 ' contains small components or isolates. Will raise an error if the network'
                                 ' has two largest components of the same size.')

        parser.add_argument('--report-format', '-r', default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            metavar='',
                            help="Specifies the format that will be used to output the report produced by "
                                 "Pyntacle. Choices are “txt” and “tsv” for tab separated value files, “csv” "
                                 "for comma-separated value files, “xlsx” for Excel files. Default is “txt”.")

        parser.add_argument('--suppress-cursor', action="store_true", help="suppress Pyntacle animated cursor")

        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        unite_subparser = subparsers.add_parser("union",
                                                usage='pyntacle set union [-h] [-1] [-2] [-f] [-N] [-d] [-L] [--input-separator] [--report-format] [-P] [--plot-dim] [--no-plot] [-o] [-u] [--output-format STR] [--output-separator] [--no-output-header]',
                                                add_help=False, parents=[parser],
                                                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                    max_help_position=100,
                                                                                                    width=150))
        unite_subparser.set_defaults(which='union')
        
        intersection_subparser = subparsers.add_parser("intersection",
                                                       usage='pyntacle set intersection [-h] [-1] [-2] [-f] [-N] [-d] [-L] [--input-separator] [--report-format] [-P] [--plot-dim] [--no-plot] [-o] [-u] [--output-format STR] [--output-separator] [--no-output-header]',
                                                       add_help=False, parents=[parser],
                                                       formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                           max_help_position=100,
                                                                                                           width=150))
        intersection_subparser.set_defaults(which='intersection')

        difference_subparser = subparsers.add_parser("difference",
                                                     usage='pyntacle set difference [-h] [-1] [-2] [-f] [-N] [-d] [-L] [--input-separator] [--report-format] [-P] [--plot-dim] [--no-plot] [-o] [-u] [--output-format STR] [--output-separator] [--no-output-header] ',
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))
        difference_subparser.set_defaults(which='difference')

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) <= 5 or (sys.argv[2] not in ('union', 'intersection', 'difference')):
            raise Error(
                'usage: pyntacle set {union, intersection, difference} [arguments] (use --help for command description)')

        sys.stdout.write('Running Pyntacle set\n')
        set = set_command(args)
        try:
            set.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")
    
    def pyntacle_test(self):
        runner = unittest.TextTestRunner()
        runner.run(Suite())

if __name__ == '__main__':
    App()
