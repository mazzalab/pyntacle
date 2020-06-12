__author__ = ["Tommaso Mazza"]
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.2"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"07/06/2020"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """

from config import *
import itertools
import numpy as np
from algorithms.keyplayer import KeyPlayer
from algorithms.local_topology import LocalTopology
from algorithms.shortest_path import ShortestPath as sp
from exceptions.wrong_argument_error import WrongArgumentError
from tools.enums import KpposEnum, KpnegEnum, CmodeEnum, GroupCentralityEnum, GroupDistanceEnum
from internal.group_search_utils import bruteforce_search_initializer
from igraph import Graph
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import math


def crunch_fragmentation_combinations(graph: Graph, node_names_list: list, kpp_type: KpnegEnum,
                                      max_distance: int, cmode: CmodeEnum) -> dict:
    """
    Internal method to deal with the processing of all the node set combinations
    """
    kppset_score_pairs_partial = {}

    for node_names in node_names_list:
        temp_graph = graph.copy()
        temp_graph.delete_vertices(node_names)

        if temp_graph.ecount() == 0:
            kppset_score_pairs_partial[node_names] = 1  # maximum fragmentation reached
            return kppset_score_pairs_partial

        elif kpp_type == KpnegEnum.F:
            kppset_score_pairs_partial[node_names] = KeyPlayer.F(temp_graph)

        elif kpp_type == KpnegEnum.dF:
            kppset_score_pairs_partial[node_names] = KeyPlayer.dF(graph=temp_graph, max_distance=max_distance,
                                                                  cmode=cmode)
        else:
            raise KeyError(
                u"The parameter 'kp_type' is not valid. It must be one of the following: {}".format(
                    list(KpnegEnum)))

    return kppset_score_pairs_partial


def crunch_reachability_combinations(graph: Graph, node_names_list: list, kp_type: KpposEnum, max_distance: int,
                                     m: int, cmode: CmodeEnum) -> dict:
    kppset_score_pairs = {}

    for node_names in node_names_list:
        if kp_type == KpposEnum.mreach:
            if cmode != CmodeEnum.igraph:
                sp_matrix = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=None)
                reachability_score = KeyPlayer.mreach(graph=graph, nodes=node_names, m=m, max_distance=max_distance,
                                                      cmode=cmode, sp_matrix=sp_matrix)
            else:
                reachability_score = KeyPlayer.mreach(graph=graph, nodes=node_names, m=m, max_distance=max_distance,
                                                      cmode=cmode)
        elif kp_type == KpposEnum.dR:
            if cmode != CmodeEnum.igraph:
                sp_matrix = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=None)
                reachability_score = KeyPlayer.dR(graph=graph, nodes=node_names, max_distance=max_distance,
                                                  cmode=cmode, sp_matrix=sp_matrix)
            else:
                reachability_score = KeyPlayer.dR(graph=graph, nodes=node_names, max_distance=max_distance,
                                                  cmode=cmode)
        else:
            raise KeyError(
                u"The parameter 'kp_type' is not valid. It must be one of the following: {}".format(list(KpposEnum)))

        kppset_score_pairs[node_names] = reachability_score
    return kppset_score_pairs


def crunch_groupcentrality_combinations(graph: Graph, node_names_list: list, np_counts: np.ndarray,
                                        np_paths: np.ndarray, gc_enum: GroupCentralityEnum,
                                        distance_type: GroupDistanceEnum, cmode: CmodeEnum) -> dict:
    score_pairs_partial = {}

    for node_names in node_names_list:
        if gc_enum == GroupCentralityEnum.group_degree:
            score = LocalTopology.group_degree(graph, nodes=node_names)
        elif gc_enum == GroupCentralityEnum.group_closeness:
            if np_paths is None or np_paths.size == 0:
                np_paths = sp.get_shortestpaths(graph, nodes=None, cmode=cmode)
            score = LocalTopology.group_closeness(graph, node_names, distance=distance_type, np_paths=np_paths)
        elif gc_enum == GroupCentralityEnum.group_betweenness:
            # if graph.ecount() == 0:
            #     score = 0
            if np_counts is None or np_counts.size == 0:
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
    @bruteforce_search_initializer
    def fragmentation(graph: Graph, k: int, metric: KpnegEnum, max_distance: int = None,
                      cmode: CmodeEnum = CmodeEnum.igraph, nprocs: int = None) -> (list, float):
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
        :param int nprocs: Positive integer specifying the number of cores used to perform parallel computation. If :type:`None` (default) the number of cores will be set to the maximum number of available cores -1.

        :return tuple: a tuple of two elements containing in the first position a list of all kp-sets with maximum fragmentation, and the maximum achieved score in the second element.

        :raises TypeError: if ``nprocs`` is not a positive integer greater than 1
        :raises KeyError: when a ``kp_type`` is not one listed in  :func:`~pyntacle.tools.enums.KpnegEnum`
        """

        kpset_score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]

        if max_distance is not None and (
                not isinstance(max_distance, int) or max_distance <= 1 or max_distance > graph.vcount()):
            raise ValueError(
                u"'max_distance' must be an integer value between 1 and the total number of nodes")
        if not nprocs:
            nprocs = mp.cpu_count() - 1
        elif not isinstance(nprocs, int) or nprocs < 1:
            raise TypeError(u"'nprocs' must be a positive integer value")

        allS = list(itertools.combinations(node_names, k))

        if graph.vcount() - k == 1:  # in this case, only a node isolate exists, hence the F and dF already reach their maximum value (1)
            sys.stdout.write(
                u"The `k` size ({}) is such that the removal of any set always returns a node isolate. Returning all the node sets and the maximum {} value (1)\n".format(
                    k, metric.name))
            return allS, 1

        # Generate all combinations of size k

        sys.stdout.write(u"Evaluating {} possible solutions\n".format(len(allS)))

        if nprocs > 1:
            sys.stdout.write(u"Brute-force search of the best kp-set of size {} using {} cores\n".format(k, nprocs))

            # Create chunks
            chunklen = math.ceil(len(allS) / nprocs)
            chunks = [allS[i * chunklen:(i + 1) * chunklen] for i in range(nprocs)]

            with ProcessPoolExecutor(max_workers=nprocs) as executor:
                future_dict = {executor.submit(crunch_fragmentation_combinations, graph, chunk, metric,
                                               max_distance, cmode): chunk for chunk in chunks}
                for future in as_completed(future_dict):
                    chunk = future_dict[future]
                    try:
                        partial_result = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' % (chunk, exc))
                    else:
                        # print('%r page is %d bytes' % (chunk, len(data)))
                        kpset_score_pairs = {**kpset_score_pairs, **partial_result}
        else:
            # Do not paralellize iterations through the use of multi-processes
            sys.stdout.write(u"Brute-force search of the best kp-set of size {}\n".format(k))

            chunks = allS
            partial_result = crunch_fragmentation_combinations(graph=graph, node_names_list=chunks,
                                                               kpp_type=metric,
                                                               max_distance=max_distance,
                                                               cmode=cmode)

            kpset_score_pairs = {**kpset_score_pairs, **partial_result}

        maxKpp = max(kpset_score_pairs.values())
        final = [sorted(list(x)) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == maxKpp]
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
    @bruteforce_search_initializer
    def reachability(graph, k, metric: KpposEnum, max_distance=None, m=None, cmode=CmodeEnum.igraph, nprocs=None) -> (
    list, float):
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
        :param int m: The number of steps of the m-reach algorithm. Required if the the required metrics is the :func:`~tools.enums.KPPosEnum.mreach`
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param int nprocs: Positive integer specifying the number of processes to be spawned. If :type:`None` (default) the number of cores will be set to the maximum number of available cores -1.

        :return tuple: a tuple of two elements containing in the first position a list of all kp-sets with maximum reachability score, and the maximum achieved score for reschability in the second element.

        :raises TypeError: if ``nprocs`` is not a positive integer greater than one
        :raises KeyError: when a ``kp_type`` is not one listed in  :func:`~pyntacle.tools.enums.KpposEnum`
        """

        kpset_score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]

        if max_distance is not None and (
                not isinstance(max_distance, int) or max_distance <= 1 or max_distance > graph.vcount()):
            raise ValueError(
                u"'max_distance' must be an integer value between 1 and the total number of nodes")
        if not nprocs:
            nprocs = mp.cpu_count() - 1
        elif not isinstance(nprocs, int) or nprocs < 1:
            raise TypeError(u"'nprocs' must be a positive integer value")
        if metric == KpposEnum.mreach and m is None:
            raise WrongArgumentError(u"The parameter 'm' must be specified")
        if metric == KpposEnum.mreach and isinstance(m, int) and m <= 0:
            raise TypeError(u"The parameter 'm' must be a positive integer value")

        # Generate all combinations of size k
        allS = list(itertools.combinations(node_names, k))
        sys.stdout.write(u"Evaluating {} possible solutions\n".format(len(allS)))

        if nprocs > 1:
            sys.stdout.write(u"Brute-force search of the best kp-set of size {} using {} cores\n".format(k, nprocs))

            # Create chunks
            chunklen = math.ceil(len(allS) / nprocs)
            chunks = [allS[i * chunklen:(i + 1) * chunklen] for i in range(nprocs)]

            with ProcessPoolExecutor(max_workers=nprocs) as executor:
                future_dict = {executor.submit(crunch_reachability_combinations, graph, chunk, metric,
                                               max_distance, m, cmode): chunk for chunk in chunks}
                for future in as_completed(future_dict):
                    chunk = future_dict[future]
                    try:
                        partial_result = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' % (chunk, exc))
                    else:
                        kpset_score_pairs = {**kpset_score_pairs, **partial_result}
        else:
            # Do not paralellize iterations through the use of multi-processes
            sys.stdout.write(u"Brute-force search of the best kp-set of size {}\n".format(k))

            chunks = allS
            partial_result = crunch_reachability_combinations(graph=graph, node_names_list=chunks,
                                                              kp_type=metric,
                                                              max_distance=max_distance,
                                                              m=m,
                                                              cmode=cmode)
            kpset_score_pairs = {**kpset_score_pairs, **partial_result}

        _group_score = max(kpset_score_pairs.values())
        final = [sorted(list(x)) for x in kpset_score_pairs.keys() if kpset_score_pairs[x] == _group_score]
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
    @bruteforce_search_initializer
    def group_centrality(graph: Graph, k: int, metric: GroupCentralityEnum, cmode: CmodeEnum = CmodeEnum.igraph,
                         distance_type: GroupDistanceEnum = GroupDistanceEnum.minimum, nprocs: int = None) -> (
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
        :param int nprocs: Positive integer specifying the number of cores used to perform parallel computation. If :type:`None` (default) the number of cores will be set to the maximum number of available cores -1.

        :return tuple: a tuple of two elements containing in the first position a list of node set(s) with maximum group centrality score, and the maximum achieved score for reschability in the second element.

        :raise TypeError: if ``nprocs`` is not a positive integer greater than one
        """

        score_pairs = {}
        """: type: dic{(), float}"""
        node_names = graph.vs["name"]

        if not nprocs:
            nprocs = mp.cpu_count() - 1
        elif not isinstance(nprocs, int) or nprocs < 1:
            raise TypeError(u"'nprocs' must be a positive integer value")

        # Generate all combinations of size k
        allS = list(itertools.combinations(node_names, k))
        sys.stdout.write(u"Evaluating {} possible solutions\n".format(len(allS)))

        # Pre-calculate all shortest paths count and shortest paths
        np_counts = sp.get_shortestpath_count(graph, nodes=None, cmode=cmode)
        np_paths = sp.get_shortestpaths(graph, nodes=None, cmode=cmode)

        if nprocs > 1:
            sys.stdout.write(
                u"Brute-force search of the best group of nodes of size {} using {} cores\n".format(k, nprocs))

            # Create chunks
            chunklen = math.ceil(len(allS) / nprocs)
            chunks = [allS[i * chunklen:(i + 1) * chunklen] for i in range(nprocs)]

            with ProcessPoolExecutor(max_workers=nprocs) as executor:
                future_dict = {executor.submit(crunch_groupcentrality_combinations, graph, chunk,
                                               np_counts, np_paths, metric, distance_type, cmode): chunk for chunk in
                               chunks}
                for future in as_completed(future_dict):
                    chunk = future_dict[future]
                    try:
                        partial_result = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' % (chunk, exc))
                    else:
                        score_pairs = {**score_pairs, **partial_result}

        else:
            # Do not paralellize iterations through the use of multi-processes
            sys.stdout.write(u"Brute-force search of the best group of nodes of size {}\n".format(k))

            chunks = allS
            partial_result = crunch_groupcentrality_combinations(graph=graph, node_names_list=chunks,
                                                                 np_counts=np_counts,
                                                                 np_paths=np_paths,
                                                                 gc_enum=metric, distance_type=distance_type,
                                                                 cmode=cmode)
            score_pairs = {**score_pairs, **partial_result}

        _group_score = max(score_pairs.values())  # take the maximum value
        final = [sorted(list(x)) for x in score_pairs.keys() if score_pairs[x] == _group_score]

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
