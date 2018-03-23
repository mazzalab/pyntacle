"""
Brute-force search for the best kp-set.
This algorithm makes all possible sets of nodes of a specified size and applies the KP-algorithm on them.
It hence selects the KPP-set with the best score.
"""

import itertools

from igraph import Graph
from algorithms.key_player import KeyPlayer, _KeyplayerAttribute
from exceptions.illegal_kppset_size_error import IllegalKppsetSizeError
from tools.graph_utils import *
from config import *

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


class BruteforceSearch:
    """
    Brute-force search for the best kp-set **[EXPAND]**
    """

    __graph = None
    """:type: Graph"""

    def __init__(self, graph: Graph):
        """
        Initializes a graph for brute-force search of the best KP-set
        
        :param Graph graph: Graph provided in input
        :raises IllegalGraphSizeError: if the graph does not contain vertices or edges
        """
        self.logger = log

        if graph.vcount() < 1:
            self.logger.fatal("This graph does not contain vertices")
            raise IllegalGraphSizeError("This graph does not contain vertices")
        elif graph.ecount() < 1:
            self.logger.fatal("This graph does not contain edges")
            raise IllegalGraphSizeError("This graph does not contain edges")
        else:
            self.__graph = graph
            GraphUtils(graph=self.__graph).graph_checker()

    def bruteforce_fragmentation(self, kpp_size, kpp_type) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best disrupts the graph.
        It generates all the possible kpp-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the kpp-set.
        The best kpp-set will be the one that maximizes the fragmentation of the graph.
        
        :param kpp_size: the size of the kpp-set
        :type kpp_size: int
        :param kpp_type: Either KeyplayerAttribute.DF or KeyplayerAttribute.F
        :type kpp_type: KeyplayerAttribute.name
        :return: - S: **[EXPAND]**
                 - best_fragmentation_score: **[EXPAND]**
        :raises TypeError: When the kpp-set size is not an integer number
        :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.F or KeyplayerAttribute.DF
        """
        if not isinstance(kpp_size, int):
            self.logger.error("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
            raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))

        elif kpp_type != _KeyplayerAttribute.F and kpp_type != _KeyplayerAttribute.DF:
            self.logger.error(
                "The kpp_type argument ('{}') must be of type KeyplayerAttribute.F or KeyplayerAttribute.DF".format(
                    kpp_type))
            raise TypeError(
                "The kpp_type argument ('{}') must be of type KeyplayerAttribute.F or KeyplayerAttribute.DF".format(
                    kpp_type))

        elif kpp_size >= self.__graph.vcount():
            self.logger.error("The kpp_size must be strictly less than the graph size")
            raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")

        else:
            self.logger.info("Brute-force search of the best kpp-set of size {}".format(kpp_size))

            kppset_score_pairs = {}
            """: type: dic{(), float}"""

            # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
            node_indices = self.__graph.vs.indices
            allS = itertools.combinations(node_indices, kpp_size)

            for S in allS:
                temp_graph = self.__graph.copy()
                temp_graph.delete_vertices(S)
                kp = KeyPlayer(graph=temp_graph)
                if kpp_type == _KeyplayerAttribute.F:
                    kpp_func = kp.F
                else:
                    kpp_func = kp.DF

                kppset_score_pairs[tuple(S)] = kpp_func(recalculate=True)

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            S = list(maxKpp)
            best_fragmentation_score = kppset_score_pairs[maxKpp]

            final = self.__graph.vs(S)["name"]
            self.logger.info("The best kpp-set of size {} is {} with score {}".format(kpp_size, final,
                                                                                      best_fragmentation_score))
            return S, best_fragmentation_score  # TODO: Handle cases of dead heat kpp-set

    def bruteforce_reachability(self, kpp_size, kpp_type, m=None) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best reaches all other nodes over the graph.
        It generates all the possible kpp-sets and calculates their reachability scores.
        The best kpp-set will be the one that best reaches all other nodes of the graph.
        
        .. note:: **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
            
            **dR**: min = 0 (unreachable); max = 1 (total reachability)
        
        :param int kpp_size: size of the kpp-set
        :param int m: maximum path length between the kpp-set and the other nodes of the graph
        :param KeyplayerAttribute.name kpp_type: Either KeyplayerAttribute.mreach or KeyplayerAttribute.dR
        :raises TypeError: When the kpp-set size is greater than the graph size
        :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.mreach or KeyplayerAttribute.dR
        """
        if not isinstance(kpp_size, int):
            self.logger.error("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
            raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))

        elif kpp_size >= self.__graph.vcount():
            self.logger.error("The kpp_size must be strictly less than the graph size")
            raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")

        elif kpp_type != _KeyplayerAttribute.DR and kpp_type != _KeyplayerAttribute.MREACH:
            self.logger.error(
                "The kpp_type argument ('{}') must be of type KeyplayerAttribute.dR or KeyplayerAttribute.MREACH".format(
                    kpp_type))
            raise TypeError(
                "The kpp_type argument ('{}') must be of type KeyplayerAttribute.dR or KeyplayerAttribute.MREACH".format(
                    kpp_type))

        else:
            self.logger.info("Brute-force search of the best kpp-set of size {}".format(kpp_size))

            orig_graph = self.__graph.copy()  # for safety
            kppset_score_pairs = {}
            """: type: dic{(), float}"""

            # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
            node_indices = self.__graph.vs.indices
            allS = itertools.combinations(node_indices, kpp_size)

            for S in allS:
                kp = KeyPlayer(graph=orig_graph)
                if kpp_type == _KeyplayerAttribute.MREACH:
                    reachability_score = kp.mreach(m, index_list=list(S), recalculate=True)
                else:
                    reachability_score = kp.DR(index_list=list(S), recalculate=True)

                kppset_score_pairs[tuple(S)] = reachability_score

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            S = list(maxKpp)
            best_reachability_score = kppset_score_pairs[maxKpp]

            final = self.__graph.vs(S)["name"]
            self.logger.info("The best kpp-set of size {} is {} with score {}".format(kpp_size, final,
                                                                                      best_reachability_score))
            return S, best_reachability_score  # TODO: Handle cases of dead heat kpp-set