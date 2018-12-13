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
from internal.graph_routines import check_graph_consistency
from internal.group_search_utils import bruteforce_search_initializer
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
                                                              cmode=implementation)
    else:
        raise KeyError(
            u"The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpnegEnum)))

    return kppset_score_pairs_partial


def crunch_reachability_combinations(graph: Graph, kp_type: KpposEnum, m: int,
                                     max_distance: int, implementation: CmodeEnum, allS: list) -> dict:
    kppset_score_pairs = {}
    if kp_type == KpposEnum.mreach:
        if implementation != CmodeEnum.igraph:
            sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
            reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distance=max_distance,
                                                  cmode=implementation, sp_matrix=sp_matrix)
        else:
            reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distance=max_distance,
                                                  cmode=implementation)
    elif kp_type == KpposEnum.dR:
        if implementation != CmodeEnum.igraph:
            sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
            reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distance=max_distance,
                                              cmode=implementation, sp_matrix=sp_matrix)
        else:
            reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distance=max_distance,
                                              cmode=implementation)

    else:
        raise KeyError(
            u"The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpposEnum)))

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
    r"""
    Brute-force search optimization algorithms for the best set of nodes, according to a number of metrics.
    This algorithm generates all possible combinations of nodes, with a specified size, and applies the Borgatti's
    fragmentation or reachability algorithms, as described in
    `the original paper on Key Players <https://doi.org/10.1007/s10588-006-7084-x>`_, or it computes degree, closeness or betweenness group-centrality, as
    described `here <https://doi.org/10.1080/0022250X.1999.9990219>`_. Finally, it selects the sets with the best score.
    """

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def fragmentation(graph: Graph, k: int, metric: KpnegEnum, max_distance: int = None,
                      cmode: CmodeEnum = CmodeEnum.igraph, parallel: bool = False, ncores: int = None) -> (
            list, float):
        r"""
        It searches and finds the *key player* (*kp*) set, or sets, of a predefined size that maximally disrupts the graph.
        It generates all the possible kp-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the kp-set. The best kp-set(s) will be the one that maximizes the
        fragmentation of the graph.
        Available metrics that are used to score fragmentation are:

            * **F**: min = 0 (graph is complete); max = 1 (all nodes are isolates)
            * **dF**: min = 0 (graph is complete); max = 1 (all nodes are isolates)

        .. warning:: fragmentation-based searches may require long times on very large graphs (:math:`N > 1000`)


        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set to be found
        :param KpnegEnum kp_type: any available option of the enumerators :class:`~pyntacle.tools.enums.KpnegEnum`
        :param int,None max_distance: optional, define a maximum shortest path after which two nodes will be considered disconnected. Default is  :py:class:`~None` (no maximum distance is set)
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~stools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param bool parallel: whether to use multicore processors to run the algorithm iterations in parallel
        :param int ncores: Positive integer specifying the number of computing . If ``None`` (default) the number of cores will be set to the maximum number of available cores -1

        :return tuple: a tuple of two elements containing in the first position a list of all kp-sets with maximum fragmentation, and the maximum achieved score in the second element.

        :raises TypeError: if ``ncores`` is not a positive integer greater than one
        :raises KeyError: when a ``kp_type`` is not one listed in  :func:`~pyntacle.tools.enums.KpnegEnum`
        """

        kpset_score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]
        allS = itertools.combinations(node_names, k)

        if max_distance is not None and not isinstance(max_distance, int) and max_distance > 1 and max_distance <= graph.vcount():
            raise ValueError(u"'max_distance' must be an integer greater than one and lesser than the total number of nodes")

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            elif not isinstance(ncores, int) or ncores < 1:
                raise TypeError(u"'ncores' must be a positive integer value")

            sys.stdout.write(
                u"Brute-force search of the best kp-set of size {} using {} cores\n".format(k, ncores))

            pool = mp.Pool(ncores)
            for partial_result in pool.imap_unordered(
                    partial(crunch_fragmentation_combinations, graph, metric, max_distance, cmode), allS):
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

            pool.close()
            pool.join()
        else:
            sys.stdout.write(u"Brute-force search of the best kp-set of size {}\n".format(k))

            for S in allS:
                partial_result = crunch_fragmentation_combinations(graph=graph, kpp_type=metric,
                                                                   max_distance=max_distance,
                                                                   implementation=cmode, node_names=S)
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

        maxKpp = max(kpset_score_pairs.values())
        final = [list(x) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == maxKpp]
        maxKpp = round(maxKpp, 5)
        sys.stdout.write(
            u"Best group{}: {}\n Group{} size = {}\n Metric = {}\n Score = {}\n".format("s" if len(final) > 1 else "",
                                                                                       "{" + str(final).replace("'",
                                                                                                                "")[
                                                                                             1:-1] + "}",
                                                                                       "s" if len(final) > 1 else "",
                                                                                       k,
                                                                                       metric.name.replace("_", " "),
                                                                                       maxKpp))
        return final, maxKpp

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def reachability(graph, k, metric: KpposEnum, max_distance=None, m=None, cmode=CmodeEnum.igraph,
                     parallel=False, ncores=None) -> (list, float):
        r"""
        It searches and finds the *key player* (*kp*) set, or sets, of a predefined size that best reaches all other nodes in the graph.
        It generates all the possible kp-sets and calculates their reachability scores.
        The best kp-set will be the one that best reaches all other nodes of the graph.
        Available metrics that are used to score reachability are:

            * **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
            * **dR**: min = 0 (unreachable); max = 1 (total reachability)

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set to be found
        :param KpposEnum metric: any available option of the enumerators :class:`~pyntacle.tools.enums.KpposEnum`
        :param int,None max_distance: optional, define a maximum shortest path after which two nodes will be considered disconnected. Default is  :py:class:`~None` (no maximum distance is set)
        :param int m: The number of steps of the m-reach algorithm
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param bool parallel: whether to use multicore processors to run the algorithm iterations in parallel.
        :param int ncores: Positive integer specifying the number of computing . If :type:`None` (default) the number of cores will be set to the maximum number of available cores -1

        :return tuple: a tuple of two elements containing in the first position a list of all kp-sets with maximum reachability score, and the maximum achieved score for reschability in the second element.

        :raises TypeError: if ``ncores`` is not a positive integer greater than one
        :raises KeyError: when a ``kp_type`` is not one listed in  :func:`~pyntacle.tools.enums.KpposEnum`
        """

        if max_distance is not None and not isinstance(max_distance, int) and max_distance > 1 and max_distance <= graph.vcount():
            raise ValueError(u"'max_distance' must be an integer greater than one and lesser than the total number of nodes")

        if metric == KpposEnum.mreach and m is None:
            raise WrongArgumentError(u"The parameter m must be specified")
        if metric == KpposEnum.mreach and isinstance(m, int) and m <= 0:
            raise TypeError(u"The parameter m must be a positive integer value")

        kpset_score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]
        allS = itertools.combinations(node_names, k)

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            elif not isinstance(ncores, int) or ncores < 1:
                raise TypeError(u"'ncores' must be a positive integer value")

            sys.stdout.write(
                u"Brute-force search of the best kp-set of size {} using {} cores\n".format(k, ncores))

            pool = mp.Pool(ncores)
            for partial_result in pool.imap_unordered(
                    partial(crunch_reachability_combinations, graph, metric, m, max_distance, cmode), allS):
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

            pool.close()
            pool.join()

        else:
            sys.stdout.write(u"Brute-force search of the best kp-set of size {}\n".format(k))
            for S in allS:
                partial_result = crunch_reachability_combinations(graph=graph, kp_type=metric, m=m,
                                                                  max_distance=max_distance,
                                                                  implementation=cmode, allS=S)
                kpset_score_pairs = {**kpset_score_pairs, **partial_result}

        _group_score = max(kpset_score_pairs.values())  # take the maximum value
        final = [list(x) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == _group_score]
        _group_score = round(_group_score, 5)

        sys.stdout.write(
            u"Best group{}: {}\n Group{} size = {}\n Metric = {}{}\n Score = {}\n".format("s" if len(final) > 1 else "",
                                                                                         "{" + str(final).replace("'",
                                                                                                                  "")[
                                                                                               1:-1] + "}",
                                                                                         "s" if len(final) > 1 else "",
                                                                                         k,
                                                                                         metric.name.replace("_",
                                                                                                               " "),
                                                                                         ", m=" + str(
                                                                                             m) if metric == KpposEnum.mreach else "",
                                                                                         _group_score))
        return final, _group_score

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def group_centrality(graph: Graph, k: int, metric: GroupCentralityEnum,cmode: CmodeEnum = CmodeEnum.igraph,
                         distance_type: GroupDistanceEnum = GroupDistanceEnum.minimum,
                         parallel: bool = False, ncores: int = None) -> (
            list, float):
        r"""
        It searches and finds the sets of nodes of a predefined size that exhibit the maximum group centrality value.
        It generates all the possible sets of nodes and calculates their group centrality value. Available centrality
        metrics are: *group degree*, *group closeness* and *group betweenness*. The best sets will be those with maximum
        centrality score.

            * **group degree**: *min* = 0 (lowest centrality); *max* = 1 (highest centrality)
            * **group closeness**: *min* = 0 (lowest centrality); *max* = 1 (highest centrality)
            * **group betweenness**: *min* = 0 (lowest centrality); *max* = 1 (highest centrality)

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the group of nodes to be found
        :param GroupCentralityEnum metric: The centrality algorithm to be computed. It can be any value of the enumerator :class:`~pyntacle.tools.enums.GroupCentralityEnum`
        :param GroupDistanceEnum distance_type: The definition of distance between any non-group and group nodes. It can be any value of the enumerator :class:`~pyntacle.tools.enums.GroupDistanceEnum`. By default, the minimum least distance :math:`D` between the group :math:`k` and the rest of the graph :math:`N-k` is used
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param bool parallel: whether to use multicore processors to run the algorithm iterations in parallel
        :param int ncores: Positive integer specifying the number of computing . If `None` (default) the number of cores will be set to the maximum number of available cores -1

        :return tuple: a tuple of two elements containing in the first position a list of node set(s) with maximum group centrality score, and the maximum achieved score for reschability in the second element.

        :raise TypeError: if ``ncores`` is not a positive integer greater than one
        """

        score_pairs = {}
        """: type: dic{(), float}"""

        node_names = graph.vs["name"]
        allS = itertools.combinations(node_names, k)
        np_counts = sp.get_shortestpath_count(graph, nodes=None, cmode=cmode)

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            elif not isinstance(ncores, int) or ncores < 1:
                raise TypeError(u"'ncores' must be a positive integer value")

            sys.stdout.write(u"Brute-force search of the best group of nodes of size {} using {} cores\n".format(
                k, ncores))

            pool = mp.Pool(ncores)
            for partial_result in pool.imap_unordered(
                    partial(crunch_groupcentrality_combinations, graph, metric, distance_type, cmode, np_counts),
                    allS):
                score_pairs = {**score_pairs, **partial_result}

            pool.close()
            pool.join()

        else:
            sys.stdout.write(u"Brute-force search of the best group of nodes of size {}\n".format(k))

            for node_names_iter in allS:
                score_pair_partial = crunch_groupcentrality_combinations(graph, metric, distance_type,
                                                                         cmode, np_counts, node_names_iter)
                score_pairs = {**score_pairs, **score_pair_partial}

        _group_score = max(score_pairs.values())  # take the maximum value
        final = [list(x) for x in score_pairs.keys() if score_pairs[x] == _group_score]
        _group_score = round(_group_score, 5)

        metrics_distance_str = metric.name.replace("_", " ") \
            if metric != GroupCentralityEnum.group_closeness \
            else metric.name.replace("_", " ") + " - Distance function = " + distance_type.name
        sys.stdout.write(
            u"Best group{}: {}\n Group{} size = {}\n Metric = {}\n Score = {}\n".format("s" if len(final) > 1 else "",
                                                                                       "{" + str(final).replace("'",
                                                                                                                "")[
                                                                                             1:-1] + "}",
                                                                                       "s" if len(final) > 1 else "",
                                                                                       k,
                                                                                       metrics_distance_str,
                                                                                       _group_score))

        return final, _group_score
