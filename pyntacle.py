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

# external libraries
from config import *
import argparse
import sys
import os
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


def _check_value(self, action, value):
    # converted value must be one of the choices (if specified)
    if action.choices is not None and value not in action.choices:
        args = {'value': value,
                'choices': ', '.join(map(repr, action.choices))}
        msg = 'invalid choice: %(value)r'
        raise argparse.ArgumentError(action, msg % args)


# todo: Controlla che tutte le opzioni stiano effettivamente negli USAGE

class App:
    def __init__(self):
        sys.stdout.write('\n')
        sys.tracebacklimit = 0
        verbosity = 0

        # Overriding argparse's mischievous and buggy error message
        argparse.ArgumentParser._check_value = _check_value

        parser = argparse.ArgumentParser(
            description="Main description",
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py' + Fore.GREEN + ' <command>' + Fore.RED
                  + ''' [<args>]

The available commands in pyntacle are:\n''' + Style.RESET_ALL + 100 * '-' +
                  Fore.GREEN + '\n  keyplayer       ' + Fore.CYAN + 'Find Best Key-Player Set of size X or get Key-Player metrics from a set of nodes' +
                  Fore.GREEN + '\n  metrics         ' + Fore.CYAN + 'Get global metrics for the input graph or local metrics for a set of nodes' +
                  Fore.GREEN + '\n  convert         ' + Fore.CYAN + 'Convert one graph stored into a file into another graph' +
                  Fore.GREEN + '\n  set             ' + Fore.CYAN + 'Perform set operation on two graphs' +
                  Fore.GREEN + '\n  generate        ' + Fore.CYAN + 'Create a graph based on several topologies' +
                  Fore.GREEN + '\n  communities     ' + Fore.CYAN + 'Find communities within a Graph using several modular decomposition algorithms\n' +
                  Style.RESET_ALL + 100 * '-')

        parser.add_argument('command', help='subcommand to run', type=lambda s: s.lower())
        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")
        parser.add_argument('-V', "--version", action="version", version="pyntacle v0.1 (alpha)")

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
        
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def keyplayer(self):
        parser = argparse.ArgumentParser(
            description='Key player calculator\n\nSubcommands:\n' + 90 * '-' + '\n' +
                        '  kp-finder\t        find the best kp set of given metrics using a greedy algorithm\n'
                        '  kp-info\t        find kp metrics for user defined set of nodes\n\n' + 90 * '-',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py keyplayer'
                  + Fore.GREEN + Style.BRIGHT + ' {kp-finder, kp-info}'
                  + Fore.LIGHTBLUE_EX + ' --type {pos | neg | all | F | dF | dR | mreach}' + Fore.RED + ' [arguments]\n' + Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('-i', '--input_file', metavar='',
                            help="input file in the form of adjacency matrix, edge list, Simple Interaction format (.sif), Binary file and simple dot file.")  # todo Explain available extensions

        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Input format. \'adjmat\' for adjacency matrix, \'edgelist\' for edge list, \'sif\' for Simple Interaction format, \'dot\' for DOT file, \'bin\' for binary file")

        parser.add_argument('--no-header', default=False, action='store_true',
                            help='use this option if the input file has no header')
        parser.add_argument('-m', '--m-reach', metavar='', type=int, help='m value for m-reach')
        
        parser.add_argument('-M', '--max_distances', metavar='', type=int, help='(Optional) the maximum number of steps after which nodes are considered disconnected. By default, no maximum distance is allowed.')

        parser.add_argument('-t', "--type", metavar='', choices=['pos', 'neg', 'all', 'F', 'dF', 'dR', 'mreach'], default='all',
                            help="kp algorithm to be executed. Choices: {pos, neg, all, F, dF, dR, mreach} Default is \"all\" (computes all kp-metrics")
        
        parser.add_argument('--largest-component', action='store_true',
                            help='Use this option to perform Kp search only on the largest component of a graph. If two components of the same size exist, this will not work. Recommended for very fragmented network with only one large component')

        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will contain results (default is the current working directory). If the directory does not exist, we will create one")

        parser.add_argument('--report-format', '-r', metavar='', default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            type=lambda s: s.lower(),
                            help="Specify a different report format according to your tastes. \"txt\" and \"tsv\" are tab delimited format. Available formats:{txt, tsv, csv, xlsx}. Default is \"txt\"")

        parser.add_argument('--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(), metavar='',
                            help="define the format of your plot. Choices are {svg, pdf, png}. Default is \"pdf\"")

        parser.add_argument('--plot-dim', metavar='',
                            help="Comma-separated format of your plot (default is 800,800 for graph <= 150 nodes and 1600,1600 for larger graphs")

        parser.add_argument("--save-binary", action="store_true",
                            help="Save a binary file (ending with .graph) in the output directory containing your igraph object")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not output plots (recommended for graphs above 1k nodes)")

        parser.add_argument('-T', "--threads", metavar='', default=n_cpus, type=int,
                            help="Number of threads that pyntacle will use. Generally, increasing the number of threads will speed up the execution. Defaults to the maximum numbe rof threads available in your machine - 1")
        

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        # Subparser for the kp-info case
        info_case_parser = subparsers.add_parser("kp-info",
                                                  usage='pyntacle.py keyplayer kp-info [-h] [-f] [-d] [-m] [-v] [--save-binary] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input_file [FILE] --nodes NODES',
                                                  add_help=False, parents=[parser],
                                                  formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                      max_help_position=100,
                                                                                                      width=150))
        info_case_parser.set_defaults(which='kp-info')
        info_case_parser.add_argument("--nodes", help='comma-separated list of nodes (e.g. --nodes 1,2,3,4)',
                                       required=True)
        # Subparser for kp-finder case
        finder_case_parser = subparsers.add_parser("kp-finder",
                                                   usage='pyntacle.py keyplayer kp-finder [-h] [-f] [-d] [-m] [-v] [-I] [-S] [--save-binary] [--plot-format] [--plot-dim] [--no-plot] --type [TYPE] --input_file [FILE] -k [K]',
                                                   add_help=False, parents=[parser],
                                                   formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                       max_help_position=100,
                                                                                       width=150))
        finder_case_parser.add_argument('-k', '--k-size', metavar='', type=int, default=2,
                                        help='size of the set for greedy optimization (default is 2)', required=True)

        finder_case_parser.add_argument('-I', '--implementation', metavar='', type=str, default="greedy",
                                        choices=["brute-force", "greedy"],
                                        help='Type of implementation you want to find yourt keyplayer. Choices are \"greedy\" (default), \"brute-force\", '
                                             'using the greedy optimization described by Borgatti and \"brute-force\" in which ALL the optimal solution are found')

        finder_case_parser.add_argument("-S", "--seed", type=int, help="Seed (integer) for the random component of the kp-finder (greedy implementation only). "
                                                 "If set, for each seed the finder will always produce "
                                                 "the same results.", metavar="", default=None)
        finder_case_parser.set_defaults(which='kp-finder')

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])
        
        if len(sys.argv) < 4 or (sys.argv[2] not in ('kp-finder', 'kp-info')):
            parser.print_help()
            raise Error(
                'Usage: pyntacle.py keyplayer {kp-finder, kp-info} [arguments] (use --help for command description)')

        kp = kp_command(args)
        try:
            kp.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")


    def metrics(self):

        parser = argparse.ArgumentParser(
            description='Metrics Calculations at Global and local level\n\nSubcommands:\n'
                        '  global\t      provides metrics for the whole graph\n'
                        '  local\t      provides metrics for each node or for a suibset of nodes',

            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py metrics' + Fore.GREEN + Style.BRIGHT + ' {global, local}' + Fore.RED +
                  ' [arguments]' + Style.RESET_ALL)
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('-i', '--input_file', metavar='',
                            help="input file in the form of adjacency matrix, adjacency list, DOT file (.dot), Simple interaction format (SIF)")  # todo description of all available formats?
        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Input format. \'adjmat\' for adjacency matrix, \'edgelist\' for edge list, \'sif\' for Simple Interaction format, \'dot\' for DOT file, \'bin\' for binary file")

        parser.add_argument('--no-header', default=False, action='store_true',
                            help='use this option if the input file has no header')

        parser.add_argument('-d', "--directory", default=os.getcwd(), metavar='',
                            help="Directory that will contain results (default is the current working directory). If the directory does not exist, it will be created")

        parser.add_argument('--report-format', '-r', default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            help="Specify a different report format according to your tastes. \"txt\" and \"tsv\" are tab delimited format. Available formats:{txt, tsv, csv, xlsx}")

        parser.add_argument('--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="define the format of \"--draw-graph\". Choices are {svg, pdf, png}. Default is \"pdf\"")

        parser.add_argument('--plot-dim',
                            help="Comma-separated format of your plot (default is 800,800 for graph <= 150 nodes and 1600,1600 for larger graphs")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not output plots (recommended for graphs above 1k nodes)")

        parser.add_argument("--save-binary", action="store_true",
                            help="Save a binary file in the output directory containing your igraph object")

        parser.add_argument('--largest-component', action='store_true',
                            help='Use this option to compute metrics only on the largest component of a graph. If two components of the same size exist, this will not work. Recommended for very fragmented network with only one large component')

        parser.add_argument('-v', action="count",
                            help="verbosity level. -vvv is the highest level (up to the \"info\" field)")

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        # Subparser for the nodes case
        local_subparser = subparsers.add_parser("local",
                                                usage='pyntacle.py metrics local [-h] [-f] [-v] [-d] [-a] [--save-binary] [--plot-format] [--no-plot] --input_file [FILE] --nodes NODES',
                                                add_help=False, parents=[parser],
                                                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                    max_help_position=100,
                                                                                                    width=150))
        local_subparser.add_argument("--nodes",
                                     help='A specific set of comma-separated list of nodes (e.g. --nodes 1,2,3,4) on which compute local metrics. Default is set for all nodes')
        local_subparser.add_argument("--damping-factor", default=0.85, type=float,
                                     help="for pagerank, specify a damping factor (default is 0.85)")
        local_subparser.add_argument("--weights", "-w", type=str, default=None,
                                     help="for pagerank, an optional file of edge attributes with an header and relative node names of the edge on the first two columns that will be used. See documentation for examples.")
        
        local_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                          default="standard",
                                          help="Specify the format of the input weight attributes file. Choices are \"standard\" for standard edge attributes file (a dataframe) or \"cytoscape\" for Cytoscape edge attribute file. Default is \"default\"")

        local_subparser.set_defaults(which='local')

        # Subparser for global case
        global_subparser = subparsers.add_parser("global",
                                                 usage='pyntacle.py metrics global [-h] [-f] [-v] [-d] [-a] [--save-binary] [--plot-format] [--no-plot] --input_file [FILE] -n/--no-nodes',
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        global_subparser.add_argument('-n', '--no-nodes', metavar='', type=str,
                                      help='Remove a set of nodes and compute global metrics without these nodes')

        global_subparser.set_defaults(which='global')

        # now that we're inside a subcommand, ignore the first
        # TWO args, ie the command and subcommand
        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ('global', 'local')):
            raise Error('usage: pyntacle.py metrics {global, local} [arguments] (use --help for command description)')

        sys.stdout.write('Running pyntacle metrics\n')
        mt = metrics_command(args)
        try:
            mt.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def convert(self):
        parser = argparse.ArgumentParser(
            description='Convert a graph stored in a file format to another format',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py convert [arguments]' + Style.RESET_ALL)

        parser.add_argument('-i', '--input_file', metavar="", required=True,
                            help="Input format. \'adjmat\' for adjacency matrix, \'edgelist\' for edge list, \'sif\' for Simple Interaction format, \'dot\' for DOT file, \'bin\' for binary file")
        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Input format. \'adjmat\' for adjacency matrix, \'edgelist\' for edge list, \'sif\' for Simple Interaction format, \'dot\' for DOT file, \'bin\' for binary file")

        parser.add_argument('--no-header', default=False, action='store_true',
                            help='use this option if the input file has no header')

        parser.add_argument('--no-output-header', default=False, action='store_true',
                            help='use this option if you do not want an header in the output file')

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will contain results (default is the current working directory). If the directory does not exist, we will create one")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="basename of the output file. If not specified, is the basename of the input file")

        parser.add_argument("-u", "--output-format", metavar='',
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format. Default is \"adjmat\" (Adjacency Matrix)")

        parser.add_argument("--output-separator", metavar="",
                            help="Optional custom separator to output stuff. Default is the same separator that you used in the input file")

        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        # NOT prefixing the argument with -- means it's not optional
        args = parser.parse_args(sys.argv[2:])
        if len(sys.argv) < 4:
            raise Error('usage: pyntacle.py convert [arguments] (use --help for command description)')

        if args.format is not None:
            if format_dictionary[args.format] == format_dictionary[args.output_format]:
                log.error("The output format specified is the same as the input format. Quitting.\n")
                sys.exit(0)
        sys.stdout.write("Running pyntacle convert\n")

        cv = convert_command(args)
        try:
            cv.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def generate(self):

        parser = argparse.ArgumentParser(
            description='Generate graphs based on specific topologies using the igraph Generator\n\nSubcommands:\n'
                        '  random\t      random generator\n'
                        '  scale-free\t      scale-free generator\n'
                        '  tree\t              tree generator\n'
                        '  small-world\t      small-world generator',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py generate' + Fore.GREEN + Style.BRIGHT +
                  ' {random, scale-free, tree, small-world}' + Fore.RED +
                  ' [arguments]' + Style.RESET_ALL+ Style.RESET_ALL)

        # NOT prefixing the argument with -- means it's not optional

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will contain results (default is the current working directory). If the directory does not exist, we will create one")

        parser.add_argument("--output-file", "-o",
                            help="base name of the output file. If not specified, a significant name  with a random code will be generated")

        parser.add_argument("-u", "--output-format", metavar="",
                            choices=format_dictionary.keys(),
                            default='adjmat',
                            help='Desired output format. Default is \'adjmat\' (Adjacency Matrix)')

        parser.add_argument("--output-separator", metavar="",
                            help="Optional custom separator for output files. Default is \"\\t\"")

        parser.add_argument("--no-output-header", action="store_true",
                            help='Requires that your ouput file does not have an header. By default, an header is generated')

        parser.add_argument('--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="Define the format of \"--draw-graph\". Choices are {svg, pdf, png}. Default is \"pdf\"")

        parser.add_argument('--plot-dim',
                            help="Comma-separated format of your plot (default is 800,800 for graph <= 150 nodes and 1600,1600 for larger graphs")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not output plots (recommended for graphs above 1k nodes)")

        parser.add_argument("-S", "--seed", type=int, help="Seed (integer) for the random component of the generators. "
                                                 "If set, for each seed the generator will always produce "
                                                 "the same graph.", metavar="", default=None)
        
        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)
        # Subparser for the nodes case

        random_subparser = subparsers.add_parser("random",
                                                 usage='pyntacle.py generate random [-h] [-v] [-o] [-d] [-n INT] [-S INT] [-p FLOAT] [--e INT] [--no-plot]',
                                                 add_help=False, parents=[parser],
                                                 formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                     max_help_position=100,
                                                                                                     width=150))
        random_subparser.set_defaults(which='random')

        random_subparser.add_argument("-n", "--nodes", type=int,
                                      help="number of nodes of the output graph. If not specified, will be a number between 30 and 300 (chosen randomly)")

        random_subparser.add_argument("-p", "--probability",
                                      help="Wiring probability of connecting each node pair. Must be a float between 0 and 1. Default is 0.5. Excludes --edges")

        random_subparser.add_argument("-e", "--edges", type=int,
                                      help="The number of random edges that the random graph will have. Is excluded if -p is present")

        scalefree_subparser = subparsers.add_parser("scale-free",
                                                    usage='pyntacle.py generate scale-free[-h] [-v] [-o] [-d] [-n INT] [-S INT] [-m INT] [--no-plot]',
                                                    add_help=False, parents=[parser],
                                                    formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                        max_help_position=100,
                                                                                                        width=150))
        scalefree_subparser.set_defaults(which='scale-free')

        scalefree_subparser.add_argument("-n", "--nodes",
                                         help="Number of nodes of the output graph. If not specified, will be a number between 100 and 1000 (chosen randomly)")

        scalefree_subparser.add_argument("-m", "--outgoing-edges",
                                         help="Number of outgoing edges for each node in the scale-free graph. Must be a positive integer. If not specified, it will be chosen randomly between 10 and 100")

        tree_subparser = subparsers.add_parser("tree",
                                               usage='pyntacle.py generate scale-free[-h] [-v] [-o] [-d] [-n INT] [-S INT] [-c INT] [--no-plot]',
                                               add_help=False, parents=[parser],
                                               formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                   max_help_position=100,
                                                                                                   width=150))
        tree_subparser.set_defaults(which='tree')

        tree_subparser.add_argument("-n", "--nodes",
                                    help="Number of nodes of the output graph. If not specified, will be a number between 100 and 1000 (chosen randomly)")
        tree_subparser.add_argument("-c", "--children",
                                    help="Number of Children per node branch. If not specified, will be a number between 2 and 10")

        smallworld_subparser = subparsers.add_parser("small-world",
                                                     usage='pyntacle.py generate scale-free[-h] [-v] [-o] [-d] [-l INT] [-S INT] [-s INT] [-n INT] [-p FLOAT] [--no-plot]',
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))
        smallworld_subparser.set_defaults(which='small-world')

        smallworld_subparser.add_argument("-l", "--lattice", default=2,
                                          help="The lattice Dimensions. Defaulty is 2. It is highliy recommeneded not use small values,as lattices with great dimensions cannot be handeld by a normal Desktop")

        smallworld_subparser.add_argument("-s", "--lattice-size", default=None,
                                          help="Dimension of the lattice among all dimension. Default is a number between 2 and 5. It is highly recommended to keep this number low")

        smallworld_subparser.add_argument("-n", "--nei", default=None,
                                          help="Number of steps in which two vertices will be connected. Default is choosen randomly between 2 and 5")

        smallworld_subparser.add_argument("-p", "--probability", default=0.5,
                                          help="Rewiring Probability. Default is 0.5")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (sys.argv[2] not in ('random', 'scale-free', 'tree', 'small-world')):
            raise Error(
                'usage: pyntacle.py generate {random, scale-free, tree, small-world} [arguments] (use --help for command description)')

        sys.stdout.write('Running pyntacle generate\n')
        gen = generate_command(args)
        try:
            gen.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def communities(self):
        parser = argparse.ArgumentParser(
            description='Divide your graph into modules using one of the provided algorithms for module detection and outputs a series of subgraphs\n',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py communities' + Fore.GREEN + Style.BRIGHT + ' {fast_greedy, '
                                                                                                   'infomap, leading-eigenvector, community-walktrap} ' + Fore.RED + '[arguments]' + Style.RESET_ALL)

        parser.add_argument('-i', '--input_file', metavar='',
                            help="input file in the form of adjacency matrix, adjacency list, DOT file (.dot), Simple interaction format (SIF)")
        # These are options instead
        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Input format. \'adjmat\' for adjacency matrix, \'edgelist\' for edge list, \'sif\' for Simple Interaction format, \'dot\' for DOT file, \'bin\' for binary file")

        parser.add_argument("--min-nodes", "-m", help="minimum size of modules (graph below thresold will be discarded")

        parser.add_argument("--max-nodes", "-M",
                            help="maximum size of modules (in terms of nodes) (graph below thresold will be discarded")

        parser.add_argument("--min-components", "-c",
                            help="mimimum number of components to consider a module acceptable")

        parser.add_argument("--max-components", "-C",
                            help="minimum number of components to consider a module acceptable")

        parser.add_argument('--no-header', default=False, action='store_true',
                            help='use this option if the input file has no header')

        parser.add_argument("--no-output-header", action="store_true",
                            help='Requires that your ouput file does not have an header. By default, an header is generated')

        parser.add_argument('-d', "--directory", default=os.getcwd(), metavar='',
                            help="Directory that will contain results (default is the current working directory). If the directory does not exists, it will be created")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="basename of the output file and name of the output graph. If not specified, a standard name will be generated")

        parser.add_argument("-u", "--output-format", metavar='',
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format. Default is \"adjmat\" (Adjacency _Matrix)")

        parser.add_argument("--output-separator", metavar="",
                            help="Optional custom separator for output files. Default is the same separator that you used in the #1 input file #1")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not output plots (recommended for graphs above 1k nodes)")

        parser.add_argument('--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="define the format of \"--draw-graph\". Choices are {svg, pdf, png}. Default is \"pdf\"")

        parser.add_argument('--plot-dim',
                            help="Comma-separated format of your plot (default is 800,800 for graph <= 150 nodes and 1600,1600 for larger graphs")

        parser.add_argument("--save-binary", action="store_true",
                            help="Save a binary file in the output directory containing your igraph object with module attributes. See documentation for more help.")

        parser.add_argument('--largest-component', action='store_true',
                            help='Use this option to perform community finding only on the largest component of a graph. If two components of the same size exist, this will not work. Recommended for very fragmented network with only one large component')

        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        fastgreedy_subparser = subparsers.add_parser("fast_greedy",
                                                     usage='pyntacle.py communities fast_greedy [-h] [-v] [-o] [-d] [-dr] [-m] [-M] [-c] [-C] [--weights] [--clusters] [--no-plot]',
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))

        fastgreedy_subparser.set_defaults(which='fast_greedy')

        fastgreedy_subparser.add_argument("--weights", metavar="",
                                          help="a file containing edge attributes, either a tabular way or a cytoscape edge attribute file. See documentation for more help on this")
        fastgreedy_subparser.add_argument("--clusters", metavar="",
                                          help="Specify the number of modules that will be outputted by the module decomposition algorithm. If not specified, a maximized number of modules will be generated")

        fastgreedy_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                          default="standard",
                                          help="Specify the format of the input weight attributes file. Choices are \"standard\" for standard edge attributes file (a dataframe) or \"cytoscape\" for Cytoscape edge attribute file. Default is \"default\"")

        infomap_subparser = subparsers.add_parser("infomap",
                                                  usage='pyntacle.py communities infomap [-h] [-v] [-o] [-d] [-dr] [-m] [-M] [-c] [-C] [--no-plot]',
                                                  add_help=False, parents=[parser],
                                                  formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                      max_help_position=100,
                                                                                                      width=150))
        infomap_subparser.set_defaults(which='infomap')

        leading_eigenvector_subparser = subparsers.add_parser("leading-eigenvector",
                                                              usage='pyntacle.py communities leading-eigenvector [-h] [-v] [-o] [-d] [-dr] [-m] [-M] [-c] [-C] [--no-plot]',
                                                              add_help=False, parents=[parser],
                                                              formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                                  max_help_position=100,
                                                                                                                  width=150))
        leading_eigenvector_subparser.set_defaults(which='leading-eigenvector')

        community_walktrap_subparser = subparsers.add_parser("community-walktrap",
                                                             usage='pyntacle.py communities community-walktrap [-h] [-v] [-o] [-d] [-dr] [-m] [-M] [-c] [-C] [--no-plot]',
                                                             add_help=False, parents=[parser],
                                                             formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                                 max_help_position=100,
                                                                                                                 width=150))
        community_walktrap_subparser.set_defaults(which='community-walktrap')

        community_walktrap_subparser.add_argument("--weights",
                                                  help="a file containing edge attributes, either a tabular way or a cytoscape edge attribute file. See documentation for more help on this")
        community_walktrap_subparser.add_argument("--clusters",
                                                  help="Specify the number of modules that will be oupoutted by the module decomposition algorithm. If not specified, a maximized number of modules will be generated")

        community_walktrap_subparser.add_argument("--steps",
                                                  help="Specify the length of random walks that will be used by the algorithm  to find modules. Default is 3.", default='3')

        community_walktrap_subparser.add_argument("--weights-format", choices=["standard", "cytoscape"], metavar="",
                                                  default="standard",
                                                  help="Specify the format of the input weight attributes file. Choices are \"standard\" for standard edge attributes file (a dataframe) or \"cytoscape\" for Cytoscape edge attribute file. Default is \"default\"")

        community_walktrap_subparser.add_argument("--weights-name", choices=["default", "cytoscape"], metavar="",
                                                  help="specify the name of the column attribute that will be used to divide module. If not specified, the first column after the edges in the weights file will be taken")

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) < 4 or (
                    sys.argv[2] not in ('fast_greedy', 'infomap', 'leading-eigenvector', 'community-walktrap')):
            raise Error(
                'usage: pyntacle.py communities {fast_greedy, infomap, leading-eigenvector, community-walktrap} [arguments] (use --help for command description)')

        sys.stdout.write('Running pyntacle communities\n')

        comm = communities_command(args)
        try:
            comm.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

    def set(self):

        parser = argparse.ArgumentParser(
            description='perform one of the 3 set operations: union, intersection, difference of two graphs on two input graphs\n',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage=Fore.RED + Style.BRIGHT + 'pyntacle.py set ' + Fore.GREEN + Style.BRIGHT + '{union, intersection,'
                                                                                            ' difference}' + Fore.RED + ' [arguments]' + Style.RESET_ALL)
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('-1', '--input-file-1', metavar='',
                            help="first input graph in the form of adjacency matrix, adjacency list, DOT file (.dot), Simple interaction format (SIF) or binary file (.graph)")

        parser.add_argument('-2', '--input-file-2', metavar='',
                            help="second input graph in the form of adjacency matrix, adjacency list, DOT file (.dot), Simple interaction format (SIF) or binary file (.graph)")

        parser.add_argument('-f', '--format', metavar='',
                            choices=format_dictionary.keys(),
                            help="Input format of the input graphs. Allowed values are 'adjmat' for adjacency matrix, 'edgelist' for edge list, sif for Simple Interaction format, \'dot\' for DOT file, \'bin\' for binary file. "
                                 "The two files must have the same format. If not, use pyntacle Convert to convert your files to the same format")

        parser.add_argument("--no-header", "-n", action="store_true",
                            help="Specify if the input file Does not contain an header. If one of the two input files has an header, be sure to remove or adding it using pyntacle Convert")

        parser.add_argument('-d', "--directory", metavar='', default=os.getcwd(),
                            help="Directory that will contain results (default is the current working directory). If the directory does not exist, we will create one")

        parser.add_argument('-v', action="count", help="verbosity level. -vvv is the highest level")

        parser.add_argument('--plot-format', choices=["svg", "pdf", "png"], default="pdf",
                            type=lambda s: s.lower(),
                            help="define the format of \"--draw-graph\". Choices are {svg, pdf, png}. Default is \"pdf\"")

        parser.add_argument('--plot-dim', metavar="",
                            help="Comma-separated format of your plot (default is 800,800 for graph <= 150 nodes and 1600,1600 for larger graphs")

        parser.add_argument("--no-plot", action="store_true",
                            help="Do not output plots (recommended for graphs above 1k nodes)")

        parser.add_argument("-u", "--output-format", metavar='',
                            choices=format_dictionary.keys(), default="adjmat",
                            help="Desired output format. Default is \"adjmat\" (Adjacency _Matrix)")

        parser.add_argument("--output-file", "-o", metavar='',
                            help="basename of the output file and name of the output graph. If not specified, a standard name will be generated")

        parser.add_argument("--no-output-header", action="store_true",
                            help='Requires that your ouput file does not have an header. By default, an header is generated')

        parser.add_argument("--output-separator", metavar="",
                            help="Optional custom separator for output files. Default is the same separator that you used in the #1 input file #1")

        parser.add_argument('--largest-component', action='store_true',
                            help='Use this option to perform a set operation only on the largest component of a graph. If two components of the same size exist, this will not work. Recommended for very fragmented network with only one large component')

        parser.add_argument('--report-format', '-r', default="txt", choices=["txt", "csv", "xlsx", "tsv"],
                            help="Specify a different report format according to your tastes. \"txt\" and \"tsv\" are tab delimited format. Available formats:{txt, tsv, csv, xlsx}")


        subparsers = parser.add_subparsers(metavar='', help=argparse.SUPPRESS)

        unite_subparser = subparsers.add_parser("union",
                                                usage='pyntacle.py set union [-1] [-2] [-h] [-v] [-o] [-d] [--output-format STR] [--output-separator] [--no-output-header] [--no-plot]',
                                                add_help=False, parents=[parser],
                                                formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                    max_help_position=100,
                                                                                                    width=150))
        unite_subparser.set_defaults(which='union')

        intersection_subparser = subparsers.add_parser("intersection",
                                                       usage='pyntacle.py set union [-1] [-2] [-h] [-v] [-o] [-d] [--output-format STR] [--output-separator] [--no-output-header] [--no-plot]',
                                                       add_help=False, parents=[parser],
                                                       formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                           max_help_position=100,
                                                                                                           width=150))
        intersection_subparser.set_defaults(which='intersection')

        difference_subparser = subparsers.add_parser("difference",
                                                     usage='pyntacle.py set union [-1] [-2] [-h] [-v] [-o] [-d] [--output-format STR] [--output-separator] [--no-output-header] [--no-plot]',
                                                     add_help=False, parents=[parser],
                                                     formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                                                         max_help_position=100,
                                                                                                         width=150))
        difference_subparser.set_defaults(which='difference')

        args = parser.parse_args(sys.argv[2:])

        if len(sys.argv) <= 5 or (sys.argv[2] not in ('union', 'intersection', 'difference')):
            raise Error(
                'usage: pyntacle.py set {union, intersection, difference} [arguments] (use --help for command description)')

        sys.stdout.write('Running pyntacle set\n')
        set = set_command(args)
        try:
            set.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nReceived SIGKILL from Keyboard\n")

if __name__ == '__main__':
    App()
