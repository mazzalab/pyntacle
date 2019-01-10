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


from config import *
import random
import importlib
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw

##REQUIRED FOR GRINFO
from algorithms.local_topology import LocalTopology as loc
from algorithms.greedy_optimization import GreedyOptimization as go
from algorithms.bruteforce_search import BruteforceSearch as bf



from itertools import chain
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import PlotGraph
from cmds.cmds_utils.reporter import PyntacleReporter
from tools.graph_utils import GraphUtils as gu
from internal.graph_load import GraphLoad
from tools.enums import ReportEnum, CmodeEnum
from tools.add_attributes import AddAttributes
from colorama import Fore, Style


class GroupCentrality():
    def __init__(self, args):
        self.logging = log
        self.args = None
        self.args = args
        if self.args.seed:
            random.seed(self.args.seed)

        if not self.args.no_plot and importlib.util.find_spec("cairo") is None:
            sys.stdout.write(u"Warning: It seems that the pycairo library is not installed/available. Graph plot(s)"
                             "will not be produced.\n")
            self.args.no_plot = True

    def run(self):
        if not self.args.suppress_cursor:
            cursor = CursorAnimation()
            cursor.daemon = True
            cursor.start()

        if self.args.group_distances is None and self.args.type in ["all", "closeness"]:
            sys.stderr.write(u"Group distance must be required for group closeness (--param). Quitting.\n")

        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"Warning: output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

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

        sys.stdout.write("Reading input file...\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header,
                          separator=self.args.input_separator).graph_load()

        # init graph utils class
        utils = gu(graph=graph)

        if self.args.largest_component:
            try:
                graph = gu.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph as you requested ({} nodes, {} edges)...\n".format(
                        graph.vcount(), graph.ecount()))
                #reinitialize graph utils class
                utils.set_graph(graph)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting.\n")
                sys.exit(1)

        if hasattr(self.args, 'nodes'):
            try:
                utils.check_name_list(self.args.nodes)
            except:
                #REMINDER: FERMATO QUA, fixa il problema della largest component
                if self.args.nodes is not None:
                    sys.stdout.write(u"Computing local metrics for nodes ({})\n".format(', '.join(self.args.nodes)))

                    try:
                        utils.check_name_list(self.args.nodes.split(","))  # to check everything's in order

                    except MissingAttributeError:
                        sys.stderr.write(
                            u"One of the nodes you specified is not in the input graph, check your node list and its formatting.Quitting.\n")
                        sys.exit(1)

        sys.stdout.write(u"Pyntacle groupcentrality completed successfully. Ending.\n")
        sys.exit(0)

##########################################################################################################