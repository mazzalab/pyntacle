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

import random
from algorithms.keyplayer_NEW import KeyPlayer as kp
from misc.graph_routines import *
from exceptions.illegal_kppset_size_error import IllegalKppsetSizeError

"""
This Module covers the Greedy optimization algorithms for optimal kp-set calculation
"""

#from enum import Enum


class GreedyOptimization:
    """
    Greedy optimization algorithms for optimal kp-set calculation
    """
    @staticmethod
    def kpp_neg_greedy(graph, kpp_size, kpp_type, seed=None, max_sp=None, implementation="pyntacle") -> (list, float):
        """
        It iteratively searches for a kpp-set of a predefined vertex set size, removes it and measures the residual
        fragmentation score.
        The best kpp-set will be that that maximizes the fragmentation.

        Args:
            graph (igraph.Graph): an igraph.Graph object. The graph should have specific properties.
                Please see the `Minimum requirements` specifications in pyntacle's manual
                ciao sono AKKAPO
            test (int): test de prova

        Returns:
            KPSET(list), KPVALUE(float)

                * ciccio (int): intero de prova
                * ciccio2 (float): float de prova
        """


        if not isinstance(kpp_size, int):
            raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))

        elif kpp_size >= graph.vcount():
            raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")

        kp_choices = ["F", "dF"]

        if not isinstance(kpp_type, str):
            raise ValueError("\"kpp_type\" must be a string, {} found".format(type(kpp_type)-__name__))

        if kpp_type not in kp_choices:
            raise ValueError("KP Metrics available are \"F\" and \"dF\", invalid option specified {}".format(kpp_type))

        implementations = ["igraph", "pyntacle", "auto"]

        if implementation not in implementations:
            raise ValueError("{0} is not valid. Available options are {1}".format(implementation, ",".format(implementations)))

        if seed is not None:
            if not isinstance(seed, int):
                raise ValueError("seed must be an integer")

            else:
                random.seed = seed

        if max_sp is not None and not isinstance(max_sp, int) and max_sp > 1 and max_sp <= graph.vcount():
            raise ValueError("\"max_sp\" must be an integer greater than one and lesser tan the total number of nodes")

        # Definition of the starting S and notS sets
        node_indices = graph.vs.indices

        random.shuffle(node_indices)
        S = node_indices[0:kpp_size]
        """:type: list[int] """
        S.sort()

        notS = set(node_indices).difference(set(S))
        """:type: list[int] """

        temp_graph = graph.copy()
        temp_graph.delete_vertices(S)

        if kpp_type == "F":
            fragmentation_score = kp.F(graph=graph)

        else:
            fragmentation_score = kp.dF(graph=graph, implementation=implementation, max_sp=max_sp)

        kppset_score_pairs_history = {}
        """:type: dic{(), float}"""
        kppset_score_pairs_history[tuple(S)] = fragmentation_score

        optimal_set_found = False

        while not optimal_set_found:
            kppset_score_pairs = {}
            """:type: dic{(), float}"""

            for si in S:
                temp_kpp_set = S.copy()
                temp_kpp_set.remove(si)

                for notsi in notS:
                    temp_kpp_set.append(notsi)
                    temp_kpp_set.sort()  # necessary to avoid repetitions
                    temp_kpp_set_tuple = tuple(temp_kpp_set)

                    if temp_kpp_set_tuple in kppset_score_pairs_history:
                        kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple]

                    else:
                        temp_graph = graph.copy()
                        temp_graph.delete_vertices(temp_kpp_set)


                        #todo placeholder
                        try:
                            kp.set_graph(temp_graph, shallow_copy=True)

                        except IllegalGraphSizeError:
                            # This occurs whenever removing nodes deletes all edges, thus causing max fragmentation
                            kppset_score_pairs[temp_kpp_set_tuple] = 1  # 1 = Max fragmentation
                            kppset_score_pairs_history[temp_kpp_set_tuple] = 1  # 1 = Max fragmentation

                        else:
                            temp_kpp_func_value = kpp_func(recalculate=True)
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
