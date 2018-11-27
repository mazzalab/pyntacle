"""
Brute-force search optimization algorithms for the best set of nodes, according to a number of metrics.
This algorithm generates all possible combinations of nodes, with a specified size, and applies the Borgatti's
fragmentation or reachability algorithms, as described in
https://doi.org/10.1007/s10588-006-7084-x, or it computes degree, closeness or betweenness group-centrality, as
described in https://doi.org/10.1080/0022250X.1999.9990219. Finally, it selects the sets with the best score.
"""

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

from config import *
import itertools
import numpy as np
from functools import partial
from algorithms.keyplayer import KeyPlayer
from algorithms.local_topology import LocalTopology
from algorithms.shortest_path import ShortestPath as sp
from exceptions.wrong_argument_error import WrongArgumentError
from tools.enums import KpposEnum, KpnegEnum, CmodeEnum, GroupCentralityEnum, GroupDistanceEnum
from private.graph_routines import check_graph_consistency
from private.kpsearch_utils import bruteforce_search_initializer
from igraph import Graph
import multiprocessing as mp


def crunch_fragmentation_combinations(graph: Graph, kpp_type: KpnegEnum,
                                      max_distance: int, implementation: CmodeEnum, node_names: list) -> dict:
    kppset_score_pairs_partial = {}
    temp_graph = graph.copy()
    temp_graph.delete_vertices(node_names)

    if kpp_type == KpnegEnum.F:
        kppset_score_pairs_partial[node_names] = KeyPlayer.F(temp_graph)

    elif kpp_type == KpnegEnum.dF:
        kppset_score_pairs_partial[node_names] = KeyPlayer.dF(graph=temp_graph, max_distance=max_distance,
                                                              implementation=implementation)
    else:
        raise KeyError(
            "The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpnegEnum)))

    return kppset_score_pairs_partial


def crunch_reachability_combinations(graph: Graph, kp_type: KpposEnum, m: int,
                                     max_distance: int, implementation: CmodeEnum, allS: list) -> dict:
    kppset_score_pairs = {}
    if kp_type == KpposEnum.mreach:
        if implementation != CmodeEnum.igraph:
            sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
            reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distance=max_distance,
                                                  implementation=implementation, sp_matrix=sp_matrix)
        else:
            reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distance=max_distance,
                                                  implementation=implementation)
    elif kp_type == KpposEnum.dR:
        if implementation != CmodeEnum.igraph:
            sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
            reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distance=max_distance,
                                              implementation=implementation, sp_matrix=sp_matrix)
        else:
            reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distance=max_distance,
                                              implementation=implementation)

    else:
        raise KeyError(
            "The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpposEnum)))

    kppset_score_pairs[allS] = reachability_score
    kppset_score_pairs[allS] = reachability_score
    return kppset_score_pairs


def crunch_groupcentrality_combinations(graph: Graph, gc_enum: GroupCentralityEnum,
                                        distance_type: GroupDistanceEnum,
                                        cmode: CmodeEnum, np_counts: np.ndarray, node_names: list) -> dict:
    score_pairs_partial = {}

    if gc_enum == GroupCentralityEnum.group_degree:
        score = LocalTopology.group_degree(graph, nodes=node_names)
    elif gc_enum == GroupCentralityEnum.group_closeness:
        score = LocalTopology.group_closeness(graph, node_names, distance=distance_type, cmode=cmode)
    elif gc_enum == GroupCentralityEnum.group_betweenness:
        if np_counts.size == 0:
            np_counts = sp.get_shortestpath_count(graph, nodes=None, cmode=cmode)
        score = LocalTopology.group_betweenness(graph, node_names, cmode=cmode, np_counts=np_counts)
    else:
        raise WrongArgumentError("{} function not yet implemented.".format(gc_enum.name))

    score_pairs_partial[tuple(node_names)] = score
    return score_pairs_partial


class BruteforceSearch:
    """
    Brute-force search for the best set of nodes using either parallel or single core implementations.
    It returns all the best sets for a given centrality metrics.
    """

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def fragmentation(graph: Graph, kp_size: int, kpp_type: KpnegEnum, max_distance: int = None,
                      cmode: CmodeEnum = CmodeEnum.igraph, parallel: bool = False, ncores: int = None) -> (
            list, float):
        """
        It searches and finds the kp-set of a predefined size that maximally disrupts the graph.
        It generates all the possible kp-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the kp-set. The best kp-set will be the one that maximizes the
        fragmentation of the graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param int kp_size: the size of the kp-set to be found
        :param KpnegEnum kp_type: the fragmentation algorithm to be applied
        :param int max_distance: the maximum shortest path length over which two nodes are considered unreachable
        :param CmodeEnum.igraph cmode: Computation of the shortest paths is deferred
        to the following implementations:
        *`implementation.auto`: the most performing computing mode is automatically chosen according to the properties of graph
        *`implementation.igraqh`: (default) use the shortest paths implementation provided by igraph
        *`implementation.cpu`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors). This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually
        equal the total number of vertices plus one.
        *`implementation.gpu`: compute shortest paths using the Floyd-Warshall algorithm designed for NVIDIA-enabled GPU graphic
        cards. This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually equal
        the total number of vertices plus one.
        :param bool parallel: whether to use multicore processors to run the algorithm iterations in parallel
        :param int ncores: Positive integer specifying the number of computing . If `None` (default) the number of
        cores will be set to the maximum number of available cores -1
        :return: a tuple containing (left) a list of all kp-sets with maximum group centrality score; (right) the maximum
        achieved score.
        """

        kpset_score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]
        allS = itertools.combinations(node_names, kp_size)

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            elif not isinstance(ncores, int) or ncores < 1:
                raise TypeError("'ncores' must be a positive integer value")

            sys.stdout.write(
                "Brute-force search of the best kp-set of size {} using {} cores\n".format(kp_size, ncores))

            pool = mp.Pool(ncores)
            for partial_result in pool.imap_unordered(
                    partial(crunch_fragmentation_combinations, graph, kpp_type, max_distance, cmode), allS):
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

            pool.close()
            pool.join()
        else:
            sys.stdout.write("Brute-force search of the best kp-set of size {}\n".format(kp_size))

            for S in allS:
                partial_result = crunch_fragmentation_combinations(graph=graph, kpp_type=kpp_type,
                                                                   max_distance=max_distance,
                                                                   implementation=cmode, node_names=S)
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

        maxKpp = max(kpset_score_pairs.values())
        final = [list(x) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == maxKpp]
        maxKpp = round(maxKpp, 5)
        sys.stdout.write(
            "Best group{}: {}\n Group{} size = {}\n Metric = {}\n Score = {}\n".format("s" if len(final) > 1 else "",
                                                                                       "{" + str(final).replace("'",
                                                                                                                "")[
                                                                                             1:-1] + "}",
                                                                                       "s" if len(final) > 1 else "",
                                                                                       kp_size,
                                                                                       kpp_type.name.replace("_", " "),
                                                                                       maxKpp))
        return final, maxKpp

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def reachability(graph, kp_size, kpp_type: KpposEnum, max_distance=None, m=None, cmode=CmodeEnum.igraph,
                     parallel=False, ncores=None) -> (list, float):
        """
        It searches and finds the kp-set of a predefined size that best reaches all other nodes in the graph.
        It generates all the possible kp-sets and calculates their reachability scores.
        The best kp-set will be the one that best reaches all other nodes of the graph.
        **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
        **dR**: min = 0 (unreachable); max = 1 (total reachability)

        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param int kp_size: the size of the kp-set to be found
        :param KpposEnum kp_type: any option of the *KpposEnum* enumerators
        :param int max_distance: the maximum shortest path length over which two nodes are considered unreachable
        :param int m: The number of steps of the m-reach algorithm
        :param CmodeEnum.igraph cmode: Computation of the shortest paths is deferred
        to the following implementations:
        *`implementation.auto`: the most performing computing mode is automatically chosen according to the properties of graph
        *`implementation.igraqh`: (default) use the shortest paths implementation provided by igraph
        *`implementation.cpu`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors). This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually
        equal the total number of vertices plus one.
        *`implementation.gpu`: compute shortest paths using the Floyd-Warshall algorithm designed for NVIDIA-enabled GPU graphic
        cards. This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually equal
        the total number of vertices plus one.
        :param bool parallel: whether to use multicore processors to run the algorithm iterations in parallel
        :param int ncores: Positive integer specifying the number of computing . If `None` (default) the number of
        cores will be set to the maximum number of available cores -1
        :return: a tuple containing (left) a list of all kp-sets with maximum group centrality score; (right) the maximum
        achieved score.
        """

        if kpp_type == KpposEnum.mreach and m is None:
            raise WrongArgumentError("The parameter m must be specified")
        if kpp_type == KpposEnum.mreach and isinstance(m, int) and m <= 0:
            raise TypeError("The parameter m must be a positive integer value")

        kpset_score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]
        allS = itertools.combinations(node_names, kp_size)

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            elif not isinstance(ncores, int) or ncores < 1:
                raise TypeError("'ncores' must be a positive integer value")

            sys.stdout.write(
                "Brute-force search of the best kp-set of size {} using {} cores\n".format(kp_size, ncores))

            pool = mp.Pool(ncores)
            for partial_result in pool.imap_unordered(
                    partial(crunch_reachability_combinations, graph, kpp_type, m, max_distance, cmode), allS):
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

            pool.close()
            pool.join()
        else:
            sys.stdout.write("Brute-force search of the best kp-set of size {}\n".format(kp_size))
            for S in allS:
                partial_result = crunch_reachability_combinations(graph=graph, kp_type=kpp_type, m=m,
                                                                  max_distance=max_distance,
                                                                  implementation=cmode, allS=S)
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

        _group_score = max(kpset_score_pairs.values())  # take the maximum value
        final = [list(x) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == _group_score]
        _group_score = round(_group_score, 5)

        sys.stdout.write(
            "Best group{}: {}\n Group{} size = {}\n Metric = {}{}\n Score = {}\n".format("s" if len(final) > 1 else "",
                "{" + str(final).replace("'","")[1:-1] + "}",
                "s" if len(final) > 1 else "",
                kp_size,
                kpp_type.name.replace("_"," "),
                ", m=" + str(m) if kpp_type == KpposEnum.mreach else "",
                _group_score))
        return final, _group_score

    @staticmethod
    @check_graph_consistency
    # @bruteforce_search_initializer  TODO: If needed, add this search initializer
    def group_centrality(graph, group_size, gc_enum: GroupCentralityEnum, distance_type: GroupDistanceEnum = GroupDistanceEnum.minimum,
                         cmode=CmodeEnum.igraph, parallel=False, ncores=None) -> (list, float):
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

        score_pairs = {}
        """: type: dic{(), float}"""

        node_names = graph.vs["name"]
        allS = itertools.combinations(node_names, group_size)
        np_counts = sp.get_shortestpath_count(graph, nodes=None, cmode=cmode)

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            elif not isinstance(ncores, int) or ncores < 1:
                raise TypeError("'ncores' must be a positive integer value")

            sys.stdout.write("Brute-force search of the best group of nodes of size {} using {} cores\n".format(
                group_size, ncores))

            pool = mp.Pool(ncores)
            for partial_result in pool.imap_unordered(
                    partial(crunch_groupcentrality_combinations, graph, gc_enum, distance_type, cmode, np_counts),
                    allS):
                score_pairs = {**score_pairs, **partial_result}

            pool.close()
            pool.join()

        else:
            sys.stdout.write("Brute-force search of the best group of nodes of size {}\n".format(group_size))

            for node_names_iter in allS:
                score_pair_partial = crunch_groupcentrality_combinations(graph, gc_enum, distance_type,
                                                                         cmode, np_counts, node_names_iter)
                score_pairs = {**score_pairs, **score_pair_partial}

        _group_score = max(score_pairs.values())  # take the maximum value
        final = [list(x) for x in score_pairs.keys() if score_pairs[x] == _group_score]
        _group_score = round(_group_score, 5)

        metrics_distance_str = gc_enum.name.replace("_", " ") \
            if gc_enum != GroupCentralityEnum.group_closeness \
            else gc_enum.name.replace("_", " ") + " - Distance function = " + distance_type.name
        sys.stdout.write(
            "Best group{}: {}\n Group{} size = {}\n Metric = {}\n Score = {}\n".format("s" if len(final) > 1 else "",
                                                                                       "{" + str(final).replace("'",
                                                                                                                "")[
                                                                                             1:-1] + "}",
                                                                                       "s" if len(final) > 1 else "",
                                                                                       group_size,
                                                                                       metrics_distance_str,
                                                                                       _group_score))

        return final, _group_score
