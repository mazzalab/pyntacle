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
from collections import OrderedDict
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as ipw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from tools.enums import ReportEnum, GroupDistanceEnum, GroupCentralityEnum

##REQUIRED FOR GRINFO
from algorithms.local_topology import LocalTopology as loc
from algorithms.greedy_optimization import GreedyOptimization as go
from algorithms.bruteforce_search import BruteforceSearch as bf



from itertools import chain
from exceptions.generic_error import Error
from exceptions.multiple_solutions_error import MultipleSolutionsError
from exceptions.missing_attribute_error import MissingAttributeError
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

        if self.args.type in ["all", "closeness"]:
            if self.args.group_distances is None:
                sys.stderr.write(u"Group distance must be specified for group closeness using the `-D --group-distance` argument. Quitting.\n")
                sys.exit(1)

        if self.args.input_file is None:
            sys.stderr.write(
                u"Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stdout.write(u"Cannot find {}. Is the path correct?\n".format(self.args.input_file))
            sys.exit(1)

        #verify that group distances is set if group closeness is specified
        distancedict = {"min": GroupDistanceEnum.minimum, "max":GroupDistanceEnum.maximum, "mean": GroupDistanceEnum.mean}
        if self.args.type in ["all", "closeness"]:
            if self.args.group_distances is None:
                sys.stdout.write(
                    "'--group-distances/-D parameter must be specified for group closeness. It must be one of the followings: {}'. Quitting.\n".format(
                        ",".join(distancedict.keys())))
                sys.exit(1)
            if self.args.group_distances not in distancedict.keys():
                sys.stdout.write("'--group-distances/-D parameter must be one of the followings: {}'. Quitting.\n".format(",".join(distancedict.keys())))
                sys.exit(1)
            else:
                group_distances = distancedict[self.args.group_distances]

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

        sys.stdout.write(u"Importing graph from file...\n")
        graph = GraphLoad(self.args.input_file, format_dictionary.get(self.args.format, "NA"), header,
                          separator=self.args.input_separator).graph_load()

        # init graph utils class
        utils = gu(graph=graph)

        if hasattr(self.args, 'nodes'):
            self.args.nodes = self.args.nodes.split(",")

            try:
                utils.nodes_in_graph(self.args.nodes)

            except:
                sys.stderr.write("One or more of the specified nodes is not present in the graph. Please check your spelling and the presence of empty spaces in between node names. Quitting.\n")
                sys.exit(1)

        if self.args.largest_component:
            try:
                graph = utils.get_largest_component()
                sys.stdout.write(
                    u"Taking the largest component of the input graph as you requested ({} nodes, {} edges)...\n".format(
                        graph.vcount(), graph.ecount()))
                #reinitialize graph utils class
                utils.set_graph(graph)

            except MultipleSolutionsError:
                sys.stderr.write(
                    u"The graph has two largest components of the same size. Cannot choose one. Please parse your file or remove the '--largest-component' option. Quitting.\n")
                sys.exit(1)

            #check that the nodes are in the largest component
            if self.args.nodes is not None:

                try:
                    utils.nodes_in_graph(self.args.nodes)

                except:
                    sys.stderr.write("One or more of the specified nodes is not present in the largest graph component. Select a different set or remove this option. Quitting.\n")
                    sys.exit(1)

        # check that output directory is properly set
        createdir = False
        if not os.path.isdir(self.args.directory):
            createdir = True

        # control plot dimensions
        if self.args.plot_dim:  # define custom format
            self.args.plot_dim = self.args.plot_dim.split(",")

            for i in range(0, len(self.args.plot_dim)):
                try:
                    self.args.plot_dim[i] = int(self.args.plot_dim[i])

                    if self.args.plot_dim[i] <= 0:
                        raise ValueError

                except ValueError:
                    sys.stderr.write(
                        u"Format specified must be a comma-separated list of positive integers (e.g. 1920,1080). Quitting\n")
                    sys.exit(1)

            plot_size = tuple(self.args.plot_dim)

        else:
            plot_size = (800, 600)

            if graph.vcount() > 150:
                plot_size = (1600, 1600)

        # initialize reporter for later usage and plot dimension for later usage
        r = PyntacleReporter(graph=graph)
        initial_results = {}
        results = OrderedDict()

        if self.args.which == 'gr-finder':
            k_size = self.args.k_size

            # Greedy optimization
            if self.args.implementation == "greedy":
                report_type = ReportEnum.GR_greedy
                go_runner = gow(graph=graph)
                sys.stdout.write(u"Using greedy optimization algorithm for searching optimal set of nodes using group centrality metrics...\n")


                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the group closeness using the {1} distance from the node set...\n".format(
                            self.args.k_size, group_distances.name))


                    go_runner.run_groupcentrality(k = self.args.k_size,gr_type=GroupCentralityEnum.group_closeness, max_distance=self.args.max_distances, seed=None, cmode=self.args.implementation,distance=group_distances)

                if self.args.type in (["all", "degree"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the Group degree...\n".format(
                            self.args.k_size))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_degree,
                                                  seed=None,
                                                  cmode=self.args.implementation)

                if self.args.type in (["all", "betweenness"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the group betweenness...\n".format(
                            self.args.k_size))

                    go_runner.run_groupcentrality(k=self.args.k_size, gr_type=GroupCentralityEnum.group_betweenness,
                                                  seed=None,
                                                  cmode=self.args.implementation)

            elif self.args.implementation == "brute-force":

                if self.args.thread > 1:
                    plural = "s"

                else:
                    plural = ""

                report_type = ReportEnum.GR_bruteforce.name
                bf_runner = bfw(graph=graph)
                sys.stdout.write(u"Using brute-force search algorithm to find the best set(s) that optimize group centrality metrics...\n")

                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"Finding optimal set of nodes of size {0} that maximizes the group closeness using the {1} distance from the node set and {} thread{}...\n".format(
                            self.args.k_size, group_distances.name, self.args.threads, plural))


                if self.args.type in (["all", "closeness"]):
                    sys.stdout.write(
                        u"KP-NEG: Finding best set(s) of nodes of size {0} that hold the higher value of F among their peers...\n".format(
                            self.args.k_size))
                    initial_results[KpnegEnum.F.name] = kpp.F(graph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.F, threads=self.args.threads)

                if self.args.type in (['dF', 'neg', 'all']):
                    sys.stdout.write(
                        u"KP-NEG: Finding best set(s) of nodes of size {0} that hold the higher value of dF among their peers...\n".format(
                            self.args.k_size))

                    initial_results[KpnegEnum.dF.name] = kpp.dF(graph, cmode=CmodeEnum.igraph)
                    kp_runner.run_fragmentation(self.args.k_size, KpnegEnum.dF,
                                                max_distance=self.args.max_distances,
                                                cmode=CmodeEnum.igraph, threads=self.args.threads)

                if self.args.type in (['dR', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding best set(s) of nodes of size {0} that hold the higher value of dR among their peers...\n".format(
                            self.args.k_size))
                    kp_runner.run_reachability(self.args.k_size, KpposEnum.dR,
                                               max_distance=self.args.max_distances,
                                               cmode=CmodeEnum.igraph, threads=self.args.threads)

                if self.args.type in (['mreach', 'pos', 'all']):
                    sys.stdout.write(
                        u"KP-POS: Finding the best set(s) of nodes of size {0} that maximizes the nodes reached (m-reach) at a distance {1}...".format(
                            self.args.k_size, self.args.m_reach))

                    kp_runner.run_reachability(self.args.k_size, KpposEnum.mreach, m=self.args.m_reach,
                                               max_distance=self.args.max_distances,
                                               cmode=CmodeEnum.igraph, threads=self.args.threads)

            else:
                sys.stdout.write(
                    u"Critical Error. Please contact Pyntacle developers and report this issue, along with your command line. Quitting.\n")
                sys.exit(1)

        #output part
        if createdir:
            sys.stdout.write(u"Warning: output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        sys.stdout.write(u"Pyntacle groupcentrality completed successfully. Ending.\n")
        sys.exit(0)
