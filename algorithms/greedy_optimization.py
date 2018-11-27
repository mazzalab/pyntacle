"""
Greedy optimization algorithms for optimal kp-set calculation using Key-Players metrics as described in
https://doi.org/10.1007/s10588-006-7084-x or degree, closeness or betweenness group-centrality metrics, as described in
https://doi.org/10.1080/0022250X.1999.9990219
"""
from algorithms.local_topology import LocalTopology

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
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

import random
import sys
from functools import partial
from tools.enums import KpposEnum, KpnegEnum, CmodeEnum, GroupCentralityEnum, GroupDistanceEnum
from algorithms.keyplayer import KeyPlayer as kp
from algorithms.shortest_path import ShortestPath as sp
from exceptions.wrong_argument_error import WrongArgumentError
from private.graph_routines import check_graph_consistency
from private.kpsearch_utils import greedy_search_initializer

class GreedyOptimization:
    """
    Greedy optimization algorithms for optimal kp-set calculation using Key-Players metrics designed by Borgatti and as
    described in Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21.
    https://doi.org/10.1007/s10588-006-7084-x or degree, closeness or betweenness group-centrality metrics, as described
    in https://doi.org/10.1080/0022250X.1999.9990219
    """

    @staticmethod
    def __update_iteration(graph, temp_kpp_set: list, type_func):
        if type_func.func == kp.F or type_func.func == kp.dF:
            temp_graph = graph.copy()
            temp_graph.delete_vertices(temp_kpp_set)
            return type_func(graph=temp_graph)
        else:
            temp_S_names = graph.vs(temp_kpp_set)["name"]
            return type_func(graph=graph, nodes=temp_S_names)

    @staticmethod
    def __optimization_loop(graph, S: list, type_func):
        node_indices = graph.vs.indices
        notS = set(node_indices).difference(set(S))

        optimization_score = GreedyOptimization.__update_iteration(graph, S, type_func)
        kppset_score_pairs_history = {tuple(S): optimization_score}
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
                        temp_kpp_func_value = GreedyOptimization.__update_iteration(graph, temp_kpp_set, type_func)

                        kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value
                        kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value

                    temp_kpp_set.remove(notsi)

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            max_fragmentation = kppset_score_pairs[maxKpp]

            if max_fragmentation > optimization_score:
                S = list(maxKpp)
                notS = set(node_indices).difference(set(S))
                optimization_score = max_fragmentation
            else:
                optimal_set_found = True

        return S, optimization_score

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def fragmentation(graph, kp_size: int, kp_type: KpnegEnum, seed=None, max_distance: int=None,
                      cmode=CmodeEnum.igraph) -> (list, float):
        """
        It searches for the best kp-set of a predefined size, removes it and measures the residual
        fragmentation score for a specified KP-Neg metric.
        The best kp-set will be that which maximizes the fragmentation when the nodes are removed from the graph.
        Available KP-Neg choices:
        * KpnegEnum.F: min = 0 (the network is complete); max = 1 (all nodes are isolates)
        * KpnegEnum.dF: min = 0 (the network is complete); max = 1 (all nodes are isolates)
        Args:
            graph (igraph.Graph): The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
            kp_size (int): the size of the kp-set
            kp_type (KpnegEnum): a *KpnegEnum* enumerators. *F*, and *dF* options are available.
            seed (int): a seed to allow repeatability. Default is None
            max_distance (int): an integer specifying the maximum distance after that two nodes will be considered
            disconnected. Useful when searching for short-range interactions.
            cmode (CmodeEnum): an enumerator ranging from:
            * **`cmode.igraph`**: shortest paths computed by iGraph
            * **`cmode.cpu`**: Dijkstra algorithm implemented for multicore CPU
            * **`cmode.gpu`**: Dijkstra algorithm implemented for GPU-enabled graphics cards
            **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        Returns:
            KP-set (list), KP-value (float)
                * kp-set (list): a list containing the node names of the optimal set found
                * kp-value (float): a float number representing the kp score of the graph when the set is removed
        """


        # TODO: reminder che l'implementazione è automatica
        if kp_type == KpnegEnum.F or kp_type == KpnegEnum.dF:

            node_indices = graph.vs.indices
            random.shuffle(node_indices)

            S = node_indices[0:kp_size]
            S.sort()

            if kp_type == KpnegEnum.F:
                type_func = partial(kp.F)
            else:
                type_func = partial(kp.dF, max_distance=max_distance, implementation=cmode)

            final, fragmentation_score = GreedyOptimization.__optimization_loop(graph, S, type_func)

            final = graph.vs(S)["name"]
            sys.stdout.write(
                "Optimal group: {}\n Group size = {}\n Metric = {}\n Score = {}\n".format(
                    "{" + str(final).replace("'", "")[1:-1] + "}",
                    kp_size,
                    kp_type.name.replace("_", " "),
                    fragmentation_score))

            return final, round(fragmentation_score, 5)

        else:
            raise KeyError(
                "The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpnegEnum)))

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer  # todo solve the m problem in this decorator
    def reachability(graph, kp_size: int, kp_type: KpposEnum, seed=None, max_distance: int=None, m=None,
                     cmode=CmodeEnum.igraph) -> (list, float):
        """
        It searches for the best kpp-set of a predefined size that exhibit maximal reachability for a specified
        KP-Pos metric. Available KP-Pos choices:
        * m-reach: min = 0 (unreachable); max = size(graph) - kp_size (total reachability)
        * dR: min = 0 (unreachable); max = 1 (full reachability)
        Args:
            graph (igraph.Graph): The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
            kp_size (int): the size of the kp-set
            kp_type (KpposEnum): a *KpposEnum* enumerators. *mreach*, and *dR* options are available.
            seed (int): a seed to allow repeatability. Default is None
            max_distance (int): an integer specifying the maximum distance after that two nodes will be considered
            disconnected. Useful when searching for short-range interactions.
            m (int): maximum path length between the kpp-set and the other nodes of the graph
            cmode (CmodeEnum): an enumerator ranging from:
            * **`cmode.igraph`**: shortest paths computed by iGraph
            * **`cmode.cpu`**: Dijkstra algorithm implemented for multicore CPU
            * **`cmode.gpu`**: Dijkstra algorithm implemented for GPU-enabled graphics cards
            **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        Returns:
            KP-set (list), KP-value (float)
                * kp-set (list): a list containing the node names of the optimal set found
                * kp-value (float): a float number representing the kp score of the graph
        """

        if kp_type == KpposEnum.mreach or kp_type == KpposEnum.dR:
            if kp_type == KpposEnum.mreach and m is None:
                raise WrongArgumentError("The parameter 'm' is required for m-reach algorithm")
            elif kp_type == KpposEnum.mreach and (not isinstance(m, int) or m <= 0):
                raise TypeError({"The parameter 'm' must be a positive integer value"})
            else:

                node_indices = graph.vs.indices
                random.shuffle(node_indices)

                S = node_indices[0:kp_size]
                S.sort()
                S_names = graph.vs(S)["name"]

                if kp_type == KpposEnum.mreach:
                    if cmode != CmodeEnum.igraph:
                        sps = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=None)
                        type_func = partial(kp.mreach, nodes=S_names, m=m, max_distance=max_distance,
                                            implementation=cmode, sp_matrix=sps)
                    else:
                        type_func = partial(kp.mreach, nodes=S_names, m=m, max_distance=max_distance,
                                            implementation=cmode)
                else:
                    if cmode != CmodeEnum.igraph:
                        sps = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=None)
                        type_func = partial(kp.dR, nodes=S_names, max_distance=max_distance,
                                            implementation=cmode, sp_matrix=sps)
                    else:
                        type_func = partial(kp.dR, nodes=S_names, max_distance=max_distance,
                                            implementation=cmode)

                final, reachability_score = GreedyOptimization.__optimization_loop(graph, S, type_func)

                final = graph.vs(S)["name"]
                sys.stdout.write(
                    "Optimal group: {}\n Group size = {}\n Metric = {}\n Score = {}\n".format(
                        "{" + str(final).replace("'", "")[1:-1] + "}",
                        kp_size,
                        kp_type.name.replace("_", " "),
                        reachability_score))

                return final, round(reachability_score, 5)
        else:
            raise KeyError(
                "The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpposEnum)))

    @staticmethod
    @check_graph_consistency
    # @greedy_search_initializer  # TODO: adapt this decorator to the new functions
    def group_centrality(graph, group_size: int, gc_enum: GroupCentralityEnum, distance_type: GroupDistanceEnum = GroupDistanceEnum.minimum,
                         cmode=CmodeEnum.igraph) -> (list, float):
        """
        It searches and finds the sets of nodes of a predefined size that exhibit the maximum group centrality value.
        It generates all the possible sets of nodes and calculates their group centrality value. Available centrality
        metrics are: *group degree*, *group closeness* and *group betweenness*. The best sets will be those with maximum
        centrality score.
        **group degree**: min = 0 (lowest centrality); max = 1 (highest centrality)
        **group closeness**: min = 0 (lowest centrality); max = 1 (highest centrality)
        **group betweenness**: min = 0 (lowest centrality); max = 1 (highest centrality)
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param int group_size: the size of the group of nodes to be found
        :param GroupCentralityEnum gc_enum: The centrality algorithm to be computed. It can be any value of the
        enumerator  GroupCentralityEnum
        :param GroupDistanceEnum distance_type: The definition of distance between any non-group and group nodes.
        It can be any value of the enumerator GroupDistanceEnum
        :param CmodeEnum cmode: Computation of the shortest paths is deferred to the following implementations:
        *`cmode.auto`: the most performing computing mode is automatically chosen according to the properties of graph
        *`cmode.igraqh`: (default) use the shortest paths implementation provided by igraph
        *`cmode.cpu`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors). This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually
        equal the total number of vertices plus one.
        *`cmode.gpu`: compute shortest paths using the Floyd-Warshall algorithm designed for NVIDIA-enabled GPU graphic
        cards. This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually equal
        the total number of vertices plus one.
        :param bool parallel: whether to use multicore processors to run the algorithm iterations in parallel
        :param int ncores: Positive integer specifying the number of computing . If `None` (default) the number of
        cores will be set to the maximum number of available cores -1
        :return: a tuple containing (left) a list of all sets with maximum group centrality score; (right) the maximum
        achieved score.
        """

        if gc_enum == GroupCentralityEnum.group_degree:
            type_func = partial(LocalTopology.group_degree, graph=graph)
        elif gc_enum == GroupCentralityEnum.group_betweenness:
            np_counts = sp.get_shortestpath_count(graph, nodes=None, cmode=cmode)
            type_func = partial(LocalTopology.group_betweenness, graph=graph, cmode=cmode, np_counts=np_counts)
        elif gc_enum == GroupCentralityEnum.group_closeness:
            type_func = partial(LocalTopology.group_closeness, graph=graph, cmode=cmode, distance=distance_type)
        else:
            raise KeyError(
                "The parameter 'gc_enum' is not valid. It must be one of the following: {}".format(list(GroupCentralityEnum)))

        node_indices = graph.vs.indices
        random.shuffle(node_indices)
        S = node_indices[0:group_size]
        S.sort()

        final, group_score = GreedyOptimization.__optimization_loop(graph, S, type_func)

        final = graph.vs(S)["name"]
        metrics_distance_str = gc_enum.name.replace("_", " ") \
            if gc_enum != GroupCentralityEnum.group_closeness \
            else gc_enum.name.replace("_", " ") + " - Distance function = " + distance_type.name
        sys.stdout.write(
            "Optimal group: {}\n Group size = {}\n Metric = {}\n Score = {}\n".format(
                "{" + str(final).replace("'", "")[1:-1] + "}",
                group_size,
                metrics_distance_str,
                group_score))

        return final, round(group_score, 5)
