__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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

from algorithms.greedy_optimization_NEW import GreedyOptimization
from algorithms.bruteforce_search_NEW import BruteforceSearch
from misc.timeit import timeit
from misc.enums import KPPOSchoices, KPNEGchoices
from misc.graph_routines import check_graph_consistency
from algorithms.keyplayer_NEW import KeyPlayer
from config import *
from igraph import Graph
from random import seed

""" This file contains a series of wrappers for single KP Metrics, Greedy Optimization and Bruteforce Search. This 
enables to wrap the result into a structure that can be passed to Pyntacle commands"""

class KPWrapper():
    '''
    Wrapper for the KeyPlayer class, in order to pass proper data structures to the reporter class
    '''

    logger = None
    """:type: logger"""

    @check_graph_consistency
    def __init__(self, graph: Graph):
        '''
        Given a single metric, compute it and store it into a dictionary of results

        :param key_player: a KeyplayerAttribute object
        :param names_list: a list of node names
        :param recalculate: boolean, whether to pass the "recalculate" flag to the KeyPlayer Method
        :param m: if MREACH is specified, this must be specified as well
        '''

        self.kp = KeyPlayer
        self.logger = log
        self.graph = graph
        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    @timeit
    def run_KPPos(self, nodes:list, kpp_type:KPPOSchoices, m=None, max_distances=None):
        """

        :param nodes:
        :param kpp_type:
        :param m:
        :param max_distances:
        :return:
        """
        if not isinstance(kpp_type, KPPOSchoices):
            raise TypeError("metric must be ones of the \"KPPOSchoices\" metrics, {} found".format(type(kpp_type).__name__))

        if not isinstance(nodes, list) and not all(isinstance(x, str) for x in nodes):
            raise ValueError("Nodes must be a list of string")

        if not all(x in self.graph.vs(["name"]) for x in nodes):
            raise KeyError("one of the nodes not in the vertex [\"name\"] attrobute. Are you sure those node names are correct?")

        if not isinstance(m, int) and m <= 0 and kpp_type == KPPOSchoices.mreach:
            raise ValueError("\"m\" must be specified for mreach and must be a positive integer")

        if kpp_type == KPPOSchoices.dR:
            single_result = self.kp.dR(graph=self.graph, nodes=nodes, max_distances=max_distances)

        else:
            single_result = self.kp.mreach(graph=self.graph, nodes=nodes, max_distances=max_distances, m=m)

        self.results[kpp_type.name] = [nodes, single_result]

    @timeit
    def run_KPNeg(self, nodes:list, kpp_type:KPNEGchoices, max_distances=None):
        """

        :param nodes:
        :param kpp_type:
        :param max_distances:
        :return:
        """

        if not isinstance(kpp_type, KPNEGchoices):
            raise TypeError("metric must be ones of the \"KPNEGchoices\" metrics, {} found".format(type(kpp_type).__name__))

        if not isinstance(nodes, list) and not all(isinstance(x, str) for x in nodes):
            raise ValueError("Nodes must be a list of string")

        if not all(x in self.graph.vs(["name"]) for x in nodes):
            raise KeyError("one of the nodes not in the vertex [\"name\"] attribute. Are you sure those node names are correct?")

        else:
            copy = self.graph.copy()
            copy.delete_vertices(nodes)

        if kpp_type == KPPOSchoices.dF:
            single_result = self.kp.dF(graph=copy, max_distances=max_distances)

        else:
            single_result = self.kp.F(graph=copy)

        self.results[kpp_type.name] = [nodes, single_result]

    def get_results(self) -> dict:
        """
        returns the dicionary with the queried KP metrics for the given set of nodes
        :return dict: results: a dictionaary with the name of the KP metrics queried as keys and a list for each kp
        metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results

class GOWrapper:
    """
    Wrapper for the Greedy Optimization, in order to pass proper data structures to the pyntacle tool class
    """

    logger = None
    """:type: logger"""

    @check_graph_consistency
    def __init__(self, graph: Graph):
        '''
        Initizialize the class
        '''

        self.go = GreedyOptimization
        self.logger = log
        self.graph = graph
        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    @timeit
    def run_fragmentation(self, kpp_size:int, kpp_type:KPNEGchoices, max_distances=None, seed=None):
        """
        Wrapper around the Greedy Optimization Module that stores the greedy optimization results for KPPOS metrics
        :param kpp_size:
        :param kpp_type:
        :param max_distances:
        :param int seed: a seed that can be passed in order to replicate GO results
        :return:
        """
        if not isinstance(kpp_size, int) and kpp_size < 1:
            raise ValueError("\kpp_size\" must be a positive integer of size 1")

        if not isinstance(kpp_type, KPNEGchoices):
            raise TypeError("\"kpp_type\" must be one of the KPPNEGchoices options available")

        go_results = self.go.fragmentation(graph=self.graph, kpp_size=kpp_size, kpp_type=kpp_type, max_distances=max_distances, seed=seed)
        self.results[kpp_type.name] = [go_results[0], go_results[1]]

    @timeit
    def run_reachability(self, kpp_size:int, kpp_type:KPNEGchoices, max_distances=None, m=None):
        """
        Wrapper around the Greedy Optimization Module that stores the greedy optimization results for KPPOS metrics
        :param KPPOSchoices kpp_type:
        :param int max_distances:
        :param int m:
        :return:
        """
        if not isinstance(kpp_size, int) and kpp_size < 1:
            raise ValueError("\kpp_size\" must be a positive integer of size 1")

        if not isinstance(kpp_type, KPNEGchoices):
            raise TypeError("\"kpp_type\" must be one of the KPPNEGchoices options available")

        if not isinstance(m, int) and m <= 0 and kpp_type == KPPOSchoices.mreach:
            raise ValueError("\"m\" must be specified for mreach and must be a positive integer")

        go_results = self.go.reachability(graph=self.graph, kpp_size=kpp_size, kpp_type=kpp_type, max_distances=max_distances, seed=seed, m=m)
        self.results[kpp_type.name] = [go_results[0], go_results[1]]

    def get_results(self) -> dict:
        """
        returns the dicionary with the queried KP metrics for the given set of nodes
        :return dict: results: a dictionaary with the name of the KP metrics queried as keys and a list for each kp
        metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results


class BFWrapper:
    @check_graph_consistency
    def __init__(self, graph: Graph):
        '''
        Initizialize the class
        '''

        self.go = GreedyOptimization
        self.logger = log
        self.graph = graph
        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    @timeit
    def run_fragmentation(self):
        pass

    @timeit
    def run_reachability(self):
        pass

    def get_results(self) -> dict:
        """
        returns the dicionary with the queried KP metrics for the given set of nodes
        :return dict: results: a dictionaary with the name of the KP metrics queried as keys and a list for each kp
        metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results

