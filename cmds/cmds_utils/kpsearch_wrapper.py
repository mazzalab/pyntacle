__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.3"
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

from config import *
from tools.enums import CmodeEnum
from algorithms.greedy_optimization import GreedyOptimization
from algorithms.bruteforce_search import BruteforceSearch
from tools.graph_utils import GraphUtils as gu
from private.timeit import timeit
from tools.enums import KpposEnum, KpnegEnum
from algorithms.keyplayer import KeyPlayer
from igraph import Graph

""" This file contains a series of wrappers for single KP Metrics, Greedy Optimization and Bruteforce Search. This 
enables to wrap the result into a structure that can be passed to Pyntacle commands"""


class KPWrapper:
    '''
    Wrapper for the KeyPlayer class, in order to pass proper data structures to the reporter class
    '''

    logger = None
    """:type: logger"""

    def __init__(self, graph: Graph):
        self.kp = KeyPlayer
        self.logger = log
        self.logger.info("Initializing search of KP metrics for a selected set of nodes")
        
        gu(graph=graph).check_graph()
        self.graph = graph
            
        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    @timeit
    def run_KPPos(self, nodes, kp_type:KpposEnum, m=None, max_distance=None, implementation=CmodeEnum.igraph):
        """
        Run Single KPP-POS metrics on a single node or a set of nodes, adds everuything to the "results" object
        :param nodes: either a single node name or a list of node names
        :param KpposEnum kp_type: one of the KPPNEGchoices defined in private.enums
        :param int m: if kp_type is the m-reach, specifies the maximum distance for mreach to be computed
        :param int max_distance: maximum shortest path distance allowed (must be a positive integer greater than 0
        """
        if not isinstance(kp_type, KpposEnum):
            raise TypeError("metric must be ones of the \"KPPOSchoices\" metrics, {} found".format(type(kp_type).__name__))

        if isinstance(nodes, str):
            nodes=[nodes]
        else:
            if not isinstance(nodes, list) and not all(isinstance(x, str) for x in nodes):
                raise ValueError("Nodes must be a list of string")

        if not all(x in self.graph.vs()["name"] for x in nodes):
            raise KeyError("one of the nodes not in the vertex [\"name\"] attribute. "
                           "Are you sure those node names are correct?")

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError("\"m\" must be specified for mreach ")
            elif not isinstance(m, int) or m <= 0 :
                raise ValueError("\"m\" must be a positive integer for mreach ")

        self.logger.info("Computing {0} for nodes ({1})".format(kp_type.name, ", ".join(nodes)))
        if kp_type == KpposEnum.dR:
            single_result = self.kp.dR(graph=self.graph, nodes=nodes, max_distance=max_distance,
                                       implementation=implementation)

        else:
            single_result = self.kp.mreach(graph=self.graph, nodes=nodes, max_distance=max_distance, m=m, implementation=implementation)

        self.results[kp_type.name] = [nodes, single_result]
        self.logger.info("KP POS search completed, results are in the \"results\" dictionary")

    @timeit
    def run_KPNeg(self, nodes, kp_type:KpnegEnum, max_distance=None, implementation = CmodeEnum.igraph):
        """
        Run KP NEG metrics for a node or a set of nodes
        :param nodes: either a single node name or a list of node names
        :param KpnegEnum kp_type: one of the KPPNEGchoices defined in private.enums
        :param int max_distance: maximum shortest path distance allowed (must be a positive integer greater than 0.
        """
        if not isinstance(kp_type, KpnegEnum):
            raise TypeError("metric must be ones of the \"KPNEGchoices\" metrics, {} found".format(type(kp_type).__name__))

        if isinstance(nodes, str):
            nodes = [nodes]
        else:
            if not isinstance(nodes, list) and not all(isinstance(x, str) for x in nodes):
                raise ValueError("Nodes must be a list of string")

        if not all(x in self.graph.vs()["name"] for x in nodes):
            raise KeyError("one of the nodes not in the vertex [\"name\"] attribute. Are you sure those node names are correct?")

        else:
            copy = self.graph.copy()
            copy.delete_vertices(nodes)
            
        sys.stdout.write(
            "Computing {0} for nodes ({1})\n".format(kp_type.name, ", ".join(nodes)))

        if kp_type == KpnegEnum.dF:
            single_result = self.kp.dF(graph=copy, max_distance=max_distance, implementation=implementation)

        else:
            single_result = self.kp.F(graph=copy)

        self.results[kp_type.name] = [nodes, single_result]
        self.logger.info("KP POS search completed, results are in the \"results\" dictionary")

    def get_results(self) -> dict:
        """
        returns the dictionary with the queried KP metrics for the given set of nodes
        :return dict: results: a dictionary with the name of the KP metrics queried as keys and a list for each kp
        metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results


class GOWrapper:
    """
    Wrapper for the Greedy Optimization, in order to pass proper data structures to the pyntacle tool class
    """

    logger = None

    def __init__(self, graph: Graph):

        self.go = GreedyOptimization
        self.logger = log
        self.logger.info("Initializing Greedy Optimization")

        gu(graph=graph).check_graph() #check the input graph

        self.graph = graph

        self.graph = graph
        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    @timeit
    def run_fragmentation(self, kp_size:int, kp_type:KpnegEnum, max_distance=None, seed=None, implementation=CmodeEnum.igraph):
        """
        Wrapper around the Greedy Optimization Module that stores the greedy optimization results for KPPOS metrics in the
        "results" dictionary
        :param int kp_size: size of the kpp-set to be found
        :param KpnegEnum kp_type: on of the KPNEGchoices enumerators stored in private.enums
        :param int max_distances: maximum shortest path distance allowed in the shortest path matrix
        :param int seed: a seed that can be passed in order to replicate GO results
        """
        if not isinstance(kp_size, int) or kp_size < 1:
            raise ValueError("\kp_size\" must be a positive integer of size 1")

        if not isinstance(kp_type, KpnegEnum):
            raise TypeError("\"kp_type\" must be one of the KPPNEGchoices options available")

        go_results = self.go.fragmentation(graph=self.graph, kp_size=kp_size, kp_type=kp_type, max_distance=max_distance, seed=seed, implementation=implementation)
        self.results[kp_type.name] = [go_results[0], go_results[1]]

    @timeit
    def run_reachability(self, kp_size:int, kp_type:KpposEnum, m=None, max_distance=None, seed=None, implementation=CmodeEnum.igraph):
        """
        Wrapper around the Greedy Optimization Module that stores the greedy optimization results for KPPOS metrics
        :param int kp_size: size of the kpp-set to be found
        :param KpposEnum kp_type: on of the KPPOSchoices enumerators stored in private.enums
        :param int max_distances: maximum shortest path distance allowed in the shortest path matrix
        :param int seed: a seed that can be passed in order to replicate GO results
        :param int m: for the "mreach" metrics, a positive integer greatrer than one representing the maximum distance for mreach
        """
        if not isinstance(kp_size, int) or kp_size < 1:
            raise ValueError("\kp_size\" must be a positive integer of size 1")

        if not isinstance(kp_type, KpposEnum):
            raise TypeError("\"kp_type\" must be one of the KPPPOSchoices options available")

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError("\"m\" must be a specified for mreach ")
            elif not isinstance(m, int) or m <= 0 :
                raise ValueError("\"m\" must be a positive integer for mreach ")

        go_results = self.go.reachability(graph=self.graph, kp_size=kp_size, kp_type=kp_type, max_distance=max_distance, seed=seed, m=m, implementation=implementation)

        self.results[kp_type.name] = [go_results[0], go_results[1]]

    def get_results(self) -> dict:
        """
        returns the dicionary with the queried KP metrics and the set of nodes found by greedy optimization, along with the
        corresponding value.
        :return dict: results: a dictionary with the name of the KP metrics queried as keys and a list for each kp
        metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results


class BFWrapper:

    def __init__(self, graph: Graph):
        '''
        Initizialize the class
        '''

        self.bf = BruteforceSearch
        self.logger = log
        self.logger.info("Initializing BruteForce search")

        gu(graph=graph).check_graph()
        self.graph = graph
        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    @timeit
    def run_fragmentation(self, kp_size:int, kp_type:KpnegEnum, max_distance=None, implementation=CmodeEnum.igraph, threads=n_cpus):
        """
        Wrapper around the Bruteforce Search Module that stores the greedy optimization results for KPPOS metrics in
        the "results" dictionary
        :param int kp_size: size of the kpp-set to be found
        :param KpnegEnum kp_type: on of the KPNEGchoices enumerators stored in private.enums
        :param int max_distances: maximum shortest path distance allowed in the shortest path matrix
        """
        if not isinstance(kp_size, int) or kp_size < 1:
            raise ValueError("\kp_size\" must be a positive integer of size 1")

        if not isinstance(kp_type, KpnegEnum):
            raise TypeError("\"kp_type\" must be one of the KPPNEGchoices options available")

        bf_results = self.bf.fragmentation(graph=self.graph, kp_size=kp_size, kp_type=kp_type,
                                           max_distance=max_distance, implementation=implementation, ncores=threads)
        self.results[kp_type.name] = [bf_results[0], bf_results[1]]

    @timeit
    def run_reachability(self, kp_size: int, kp_type: KpposEnum, m=None, max_distance=None, implementation=CmodeEnum.igraph, threads=n_cpus):
        """
        Wrapper around the Bruteforce Search Module that stores the greedy optimization results for KPPOS metrics
        :param int kp_size: size of the kpp-set to be found
        :param KpposEnum kp_type: on of the KPPOSchoices enumerators stored in private.enums
        :param int max_distance: maximum shortest path distance allowed in the shortest path matrix
        :param int m: for the "mreach" metrics, a positive integer greatrer than one representing the maximum distance for mreach
        """
        if not isinstance(kp_size, int) or kp_size < 1:
            raise ValueError("\kpp_size\" must be a positive integer of size 1")

        if not isinstance(kp_type, KpposEnum):
            raise TypeError("\"kp_type\" must be one of the KPPNEGchoices options available")

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError("\"m\" must be a specified for mreach ")
            elif not isinstance(m, int) or m <= 0 :
                raise ValueError("\"m\" must be a positive integer for mreach ")

        bf_results = self.bf.reachability(graph=self.graph, kp_size=kp_size, kp_type=kp_type,
                                          max_distance=max_distance, m=m, implementation=implementation, ncores=threads)

        self.results[kp_type.name] = [bf_results[0], bf_results[1]]

    def get_results(self) -> dict:
        """
        returns the dictionary with the queried KP metrics for the given set of nodes
        :return dict: results: a dictionary with the name of the KP metrics queried as keys and a list for each kp
        metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results