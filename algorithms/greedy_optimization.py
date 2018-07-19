"""
Greedy optimization algorithms for optimal kp-set calculation using Key-Players metrics designed by Borgatti as
described in Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21.
https://doi.org/10.1007/s10588-006-7084-x
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "26/04/2018"
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

import random
from functools import partial
from tools.misc.graph_routines import *
from tools.enums import KpposEnum, KpnegEnum, CmodeEnum
from tools.graph_utils import GraphUtils as gu
from algorithms.keyplayer import KeyPlayer as kp
from algorithms.shortest_path import ShortestPath as sp
from exceptions.wrong_argument_error import WrongArgumentError
from tools.misc.kpsearch_utils import greedy_search_initializer


class GreedyOptimization:
    """
    Greedy optimization algorithms for optimal kp-set calculation using Key-Players metrics designed by Borgatti as
    described in Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21.
    https://doi.org/10.1007/s10588-006-7084-x
    """

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def fragmentation(graph, kpp_size, kpp_type: KpnegEnum, seed=None, max_distance=None, implementation=CmodeEnum.igraph) -> (list, float):
        """
        It searches for the best kpp-set of a predefined size, removes it and measures the residual
        fragmentation score for a specified KP-Neg metric.
        The best kpp-set will be that which maximizes the fragmentation when the nodes are removed from the graph.
        Available KP-Neg choices:
        * KpnegEnum.F: min = 0 (the network is complete); max = 1 (all nodes are isolates)
        * KpnegEnum.dF: min = 0 (the network is complete); max = 1 (all nodes are isolates)

        Args:
            graph (igraph.Graph): The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.

            kpp_size (int): the size of the kp-set
            kpp_type (KpnegEnum): a *KpnegEnum* enumerators. *F*, and *dF* options are available.
            seed (int): a seed to allow repeatability. Default is None
            max_distance (int): an integer specifying the maximum distance after that two nodes will be considered
            disconnected. Useful when searching for short-range interactions.
            implementation (CmodeEnum): an enumerator ranging from:
            * **`cmode.igraph`**: shortest paths computed by iGraph
            * **`cmode.cpu`**: Dijkstra algorithm implemented for multicore CPU
            * **`cmode.gpu`**: Dijkstra algorithm implemented for GPU-enabled graphics cards
            **CAUTION**: this will not work if the GPU is not present or CUDA compatible.

        Returns:
            KP-set (list), KP-value (float)
                * kp-set (list): a list containing the node names of the optimal KP-Neg set found
                * kp-value (float): a float number representing the kp score of the graph when the set is removed
        """

        num_nodes = graph.vcount()
        num_edges = graph.ecount()
        max_edges = num_nodes * (num_edges - 1)

        #todo reminder che l'implementazione è automatica
        if kpp_type == KpnegEnum.F or kpp_type == KpnegEnum.dF:
            if num_edges == 0:  # TODO: check if this case if possible, given the decorator "check_graph_consistency"
                return [], 1.0
            elif num_edges == max_edges:
                return [], 0.0
            else:
                node_indices = graph.vs.indices
                random.shuffle(node_indices)

                S = node_indices[0:kpp_size]
                S.sort()
                notS = set(node_indices).difference(set(S))

                temp_graph = graph.copy()
                temp_graph.delete_vertices(S)
                if kpp_type == KpnegEnum.F:
                    type_func = partial(kp.F, graph=graph)
                elif kpp_type == KpnegEnum.dF:
                    type_func = partial(kp.dF, graph=graph, max_distance=max_distance, implementation=implementation)
                else:
                    raise KeyError("'kpp_type' not valid. It must be one of the following: {}".format(list(KpnegEnum)))

                fragmentation_score = type_func(graph=graph)
                kppset_score_pairs_history = {tuple(S): fragmentation_score}
                optimal_set_found = False

                while not optimal_set_found:
                    kppset_score_pairs = {}

                    for si in S:
                        temp_kpp_set = S.copy()
                        temp_kpp_set.remove(si)

                        for notsi in notS:
                            temp_kpp_set.append(notsi)
                            temp_kpp_set.sort()
                            temp_kpp_set_tuple = tuple(temp_kpp_set)

                            if temp_kpp_set_tuple in kppset_score_pairs_history:
                                kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple]

                            else:
                                temp_graph = graph.copy()
                                temp_graph.delete_vertices(temp_kpp_set)
                                temp_kpp_func_value = type_func(graph=temp_graph)
                                kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value
                                kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value

                            temp_kpp_set.remove(notsi)

                    maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
                    max_fragmentation = kppset_score_pairs[maxKpp]

                    #todo Tommaso: how do we handle the case in which there is no optimal fragmentation score that
                    # maximizes the initial fragmentation score?
                    if max_fragmentation > fragmentation_score:
                        S = list(maxKpp)
                        notS = set(node_indices).difference(set(S))
                        fragmentation_score = max_fragmentation
                    else:
                        optimal_set_found = True

                final = graph.vs(S)["name"]
                sys.stdout.write("A optimal kpp-set of size {} is {} with score {}\n".format(kpp_size, final,
                                                                                 fragmentation_score))
                return final, round(fragmentation_score, 5)

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer #todo solve the m problem in this decorator
    def reachability(graph, kpp_size, kpp_type: KpposEnum, seed=None, max_distance=None, m=None, implementation=CmodeEnum.igraph) -> (list, float):
        """
        It searches for the best kpp-set of a predefined size that exhibit maximal reachability for a specified
        KP-Pos metric. Available KP-Pos choices:
        * m-reach: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
        * dR: min = 0 (unreachable); max = 1 (full reachability)

        Args:
            graph (igraph.Graph): The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.

            kpp_size (int): the size of the kp-set
            kpp_type (KpposEnum): a *KpposEnum* enumerators. *mreach*, and *dR* options are available.
            seed (int): a seed to allow repeatability. Default is None
            max_distance (int): an integer specifying the maximum distance after that two nodes will be considered
            disconnected. Useful when searching for short-range interactions.
            m (int): maximum path length between the kpp-set and the other nodes of the graph
            implementation (CmodeEnum): an enumerator ranging from:
            * **`cmode.igraph`**: shortest paths computed by iGraph
            * **`cmode.cpu`**: Dijkstra algorithm implemented for multicore CPU
            * **`cmode.gpu`**: Dijkstra algorithm implemented for GPU-enabled graphics cards
            **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        Returns:
            KP-set (list), KP-value (float)
                * kp-set (list): a list containing the node names of the optimal KP-Pos set found
                * kp-value (float): a float number representing the kp score of the graph
        """

        node_indices = graph.vs.indices
        random.shuffle(node_indices)
        S = node_indices[0:kpp_size]
        S_names = graph.vs(S)["name"]
        S.sort()
        notS = set(node_indices).difference(set(S))

        utils = gu(graph=graph)
        if kpp_type == KpposEnum.mreach and m is None:
            raise WrongArgumentError("'m' is required for the mreach algorithm")
        elif kpp_type == KpposEnum.mreach:
            if not isinstance(m, int) or m <= 0:
                raise TypeError({"'m' must be a positive integer value"})
            else:
                if implementation != CmodeEnum.igraph:
                    sps = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
                    type_func = partial(kp.mreach, graph=graph, nodes=S_names, m=m, max_distance=max_distance,
                                        implementation=implementation, sp_matrix=sps)
                else:
                    type_func = partial(kp.mreach, graph=graph, nodes=S_names, m=m, max_distance=max_distance,
                                        implementation=implementation)
        elif kpp_type == KpposEnum.dR:
            if implementation != CmodeEnum.igraph:
                sps = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
                type_func = partial(kp.dR, graph=graph, nodes=S_names, max_distance=max_distance,
                                    implementation=implementation, sp_matrix=sps)
            else:
                type_func = partial(kp.dR, graph=graph, nodes=S_names, max_distance=max_distance,
                                    implementation=implementation)
        else:
            raise KeyError("'kpp_type' not valid. It must be one of the following: {}".format(list(KpposEnum)))

        reachability_score = type_func()
        kppset_score_pairs_history = {tuple(S): reachability_score}

        optimal_set_found = False
        while not optimal_set_found:
            kppset_score_pairs = {}

            for si in S:
                temp_kpp_set = S.copy()
                temp_kpp_set.remove(si)

                for notsi in notS:
                    temp_kpp_set.append(notsi)
                    temp_kpp_set.sort()
                    temp_kpp_set_tuple = tuple(temp_kpp_set)

                    if temp_kpp_set_tuple in kppset_score_pairs_history:
                        kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple]

                    else:
                        temp_kpp_set_names = utils.get_node_names(index_list=temp_kpp_set)
                        temp_kpp_func_value=type_func(graph=graph, nodes=temp_kpp_set_names, max_distance=max_distance,
                                                      implementation=implementation)
                        kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value
                        kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value

                    temp_kpp_set.remove(notsi)

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            max_reachability = kppset_score_pairs[maxKpp]

            if max_reachability > reachability_score:
                S = list(maxKpp)
                notS = set(node_indices).difference(set(S))
                reachability_score = max_reachability
            else:
                optimal_set_found = True
        final = graph.vs(S)["name"]
        sys.stdout.write("A optimal kpp-set of size {} is {} with score {}\n".format(kpp_size, final,
                                                                                   reachability_score))
        return final, round(reachability_score, 5)
