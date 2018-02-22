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

"""
This Module covers the Greedy optimization algorithms for optimal kp-set calculation using Key-Players metrics developed by Borgatti
"""

import random
from algorithms.keyplayer_NEW import KeyPlayer as kp
from misc.graph_routines import *
from exceptions.illegal_kppset_size_error import IllegalKppsetSizeError
from misc.enums import KPPOSchoices, KPNEGchoices, SP_implementations
from misc.kpfinding_utils import kpchecker


class GreedyOptimization:
    """
    Greedy optimization algorithms for optimal kp-set calculation
    """
    @staticmethod
    @check_graph_consistency
    @kpchecker
    def kpp_neg_greedy(graph, kpp_size, kpp_type, seed=None, max_sp=None) -> (list, float):
        """
        It iteratively searches for a kpp-set of a predefined vertex set size, removes it and measures the residual
        fragmentation score.
        The best kpp-set will be that that maximizes the fragmentation when the nodes are removed from the graph.

        Args:
            graph (igraph.Graph): an igraph.Graph object. The graph should have specific properties.
                Please see the `Minimum requirements` specifications in pyntacle's manual

            kpp_size (int): the size of the optimal set found for the selected integer
            kpp_type (KPNEGchoices): a KPNEGchoices enumerators. right now, F, and "dF" are available.

        Returns:
            KPSET(list), KPVALUE(float)

                * kpset (list): a list containing the node names of the optimal KPNEG set found
                * kpvalue (float): float representing the kp score for the graph when the set is removed
        """
        if seed is not None:
            random.seed(seed)

        #todo reminder che l'implementazione è automatica

        # Definition of the starting S and notS sets
        node_indices = graph.vs.indices #retrieve the node indices of the whole graph

        random.shuffle(node_indices) #shuffle the node indices in order to subset each time a different starting set
        S = node_indices[0:kpp_size] #initial node set
        """:type: list[int] """
        S.sort() #sort the starting set in order to retrieve its size afterwards

        notS = set(node_indices).difference(set(S)) #all the other indices in the graph that will be scanned
        """:type: list[int] """

        # temporary copy of the graph from which the vertices that are selected as starting kpset will be removed
        temp_graph = graph.copy()
        temp_graph.delete_vertices(S)

        if kpp_type == KPNEGchoices.f:
            fragmentation_score = kp.F(graph=graph) #initial scores

        else:
            # call the initial graph score here using automatic implementation for SPs
            fragmentation_score = kp.dF(graph=graph, max_sp=max_sp)

        kppset_score_pairs_history = {} #a dictionary that stores score pairs
        """:type: dic{(), float}"""
        kppset_score_pairs_history[tuple(S)] = fragmentation_score #keep track of the initial kp scores after the initial set is removed

        optimal_set_found = False #this becomes True when the maximum fragmentation is achieved

        while not optimal_set_found:
            kppset_score_pairs = {} #create a dictionary of solutions {tuple of solutions: score}
            """:type: dic{(), float}"""

            for si in enumerate(S):  #loop through all the node indices of the initial query
                temp_kpp_set = S.copy()  #copy the list of original indices
                temp_kpp_set.remove(si)  #remove the node of the current loop iteration

                for notsi in notS: #iterate all over the nodes not in the starting KPSET
                    temp_kpp_set.append(notsi) #create a new KPSET by replacing the input node (si) with all the pther nodes
                    temp_kpp_set.sort()  #necessary to avoid repetitions, we track the indices of the initial KP Set
                    temp_kpp_set_tuple = tuple(temp_kpp_set)  #convert the set to tuple

                    if temp_kpp_set_tuple in kppset_score_pairs_history:  #if we already passed through this kpset, then:
                        kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple] #append this pair to the history of this kpset (1st for loop)

                    else: #compute the KPNEG metrics for this new set
                        temp_graph = graph.copy()
                        temp_graph.delete_vertices(temp_kpp_set)

                        if kpp_type == KPNEGchoices.F:
                            temp_kpp_func_value = kp.F(graph=temp_graph)  # initial scores

                        else:
                            temp_kpp_func_value = kp.dF(graph=temp_graph, max_sp=max_sp)

                        kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value
                        kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value

                    temp_kpp_set.remove(notsi)

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            max_fragmentation = kppset_score_pairs[maxKpp]

            if max_fragmentation > fragmentation_score:
                S = list(maxKpp)
                notS = set(node_indices).difference(set(S))
                fragmentation_score = max_fragmentation
            else:
                optimal_set_found = True

        final = graph.vs(S)["name"]
        print ("A optimal kpp-set of size {} is {} with score {}".format(kpp_size, final,
                                                                         fragmentation_score))
        return S, fragmentation_score

    # @staticmethod
    # def optimize_kpp_pos(self, kpp_size, kpp_type, m=None, seed=None) -> (list, float):
    #     """
    #     It iteratively searches for a kpp-set of a predefined dimension, with maximal reachability.
    #     m-reach: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
    #     dR: min = 0 (unreachable); max = 1 (total reachability)
    #
    #     :param int kpp_size: size of the kpp-set
    #     :param int m: maximum path length between the kpp-set and the other nodes of the graph
    #     :param KeyplayerAttribute.name kpp_type: Either KeyplayerAttribute.mreach or KeyplayerAttribute.dR
    #     :return: - S: **[EXPAND]**
    #              - reachability_score: **[EXPAND]**
    #     :raises TypeError: When the kpp-set size is greater than the graph size
    #     :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.mreach or KeyplayerAttribute.dR
    #     """
    #     if seed is not None:
    #         if not isinstance(seed, int):
    #             raise ValueError("seed must be an integer")
    #
    #         else:
    #             seed(seed)
    #
    #     if not isinstance(kpp_size, int):
    #         self.logger.error("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
    #         raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
    #
    #     elif kpp_size >= self.__graph.vcount():
    #         self.logger.error("The kpp_size must be strictly less than the graph size")
    #         raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")
    #
    #     elif kpp_type != _KeyplayerAttribute.DR and kpp_type != _KeyplayerAttribute.MREACH:
    #         self.logger.error(
    #             "The kpp_type argument ('{}') must be of type KeyplayerAttribute.dR or KeyplayerAttribute.MREACH".format(
    #                 kpp_type))
    #         raise TypeError(
    #             "The kpp_type argument ('{}') must be of type KeyplayerAttribute.dR or KeyplayerAttribute.MREACH".format(
    #                 kpp_type))
    #
    #     else:
    #         self.logger.info("Greedily-optimized search of a kpp-set of size {}".format(kpp_size))
    #
    #         # Definition of the starting S and notS sets
    #         node_indices = self.__graph.vs.indices
    #         random.shuffle(node_indices)
    #         S = node_indices[0:kpp_size]
    #         """:type : list[int] """
    #         S.sort()
    #         notS = set(node_indices).difference(set(S))
    #         """:type : list[int] """
    #
    #         orig_graph = self.__graph.copy()
    #         kp = KeyPlayer(graph=orig_graph)
    #         if kpp_type == _KeyplayerAttribute.MREACH:
    #             reachability_score = kp.mreach(m, index_list=S, recalculate=True)
    #         else:
    #             reachability_score = kp.DR(index_list=S, recalculate=True)
    #
    #         kppset_score_pairs_history = {}
    #         """: type: dic{(), float}"""
    #         kppset_score_pairs_history[tuple(S)] = reachability_score
    #
    #         optimal_set_found = False
    #         while not optimal_set_found:
    #             kppset_score_pairs = {}
    #             """: type: dic{(), float}"""
    #
    #             for si in S:
    #                 temp_kpp_set = S.copy()
    #                 temp_kpp_set.remove(si)
    #
    #                 for notsi in notS:
    #                     temp_kpp_set.append(notsi)
    #                     temp_kpp_set.sort()
    #                     temp_kpp_set_tuple = tuple(temp_kpp_set)
    #                     if temp_kpp_set_tuple in kppset_score_pairs_history:
    #                         kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple]
    #                     else:
    #                         if kpp_type == _KeyplayerAttribute.MREACH:
    #                             temp_kpp_func_value = kp.mreach(m, temp_kpp_set, recalculate=True)
    #                         else:
    #                             temp_kpp_func_value = kp.DR(temp_kpp_set, recalculate=True)
    #
    #                         kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value
    #                         kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value
    #
    #                     temp_kpp_set.remove(notsi)
    #
    #             maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
    #             max_reachability = kppset_score_pairs[maxKpp]
    #
    #             if max_reachability > reachability_score:
    #                 S = list(maxKpp)
    #                 notS = set(node_indices).difference(set(S))
    #                 reachability_score = max_reachability
    #             else:
    #                 optimal_set_found = True
    #         final = self.__graph.vs(S)["name"]
    #         self.logger.info("A optimal kpp-set of size {} is {} with score {}".format(kpp_size, final,
    #                                                                                    reachability_score))
    #         return S, reachability_score
