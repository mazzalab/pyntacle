__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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
from algorithms.local_topology import LocalTopology
from exceptions.wrong_argument_error import WrongArgumentError
from internal.graph_routines import check_graph_consistency
from internal.group_search_utils import greedy_search_initializer

class GreedyOptimization:
    r"""
    Greedy optimization algorithms for optimal calculation of nodes that achieve best group centrality metrics such
    defined `here <https://doi.org/10.1080/0022250X.1999.9990219>`_ or the *key player* metrics described
    `here <https://doi.org/10.1007/s10588-006-7084-x>`_
    """

    @staticmethod
    def __update_iteration(graph, temp_kpp_set: list, type_func):
        if type_func.func == kp.F or type_func.func == kp.dF:
            temp_graph = graph.copy()
            temp_graph.delete_vertices(temp_kpp_set)

            if temp_graph.ecount == 0:
                return 1

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
    def fragmentation(graph, k: int, metric: KpnegEnum, seed: int or None =None, max_distance: int or None =None,
                      cmode=CmodeEnum.igraph) -> (list, float):
        r"""
        It searches for the best *key player* (*kp*) set of a predefined size :math:`k`, removes it and measures the residual
        fragmentation score for a specified negative *key player* (*kp-neg*) set. For a quick view of key player indices,
        we recommend reading our `introductory guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_
        The optimal kp set will be the one that have the higher fragmentation score even if no switching from the set
        :math:`k` to the rest of the nodes in the graph :math:`N-k`.

        | Available kp-neg metrics:

            * **F**: min = 0 (the network is complete); max = 1 (all nodes are isolates)
            * **dF**: min = 0 (the network is complete); max = 1 (all nodes are isolates)

        .. warning:: fragmentation-based searches may require long times on very large graphs (:math:`N > 1000`)

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param KpnegEnum metric: on of the available :class:`~pyntacle.tools.enums.KpnegEnum`
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        :param int,None max_distance: optional, define a maximum shortest path after which two nodes will be considered disconnected. Default is  :py:class:`~None` (no maximum distance is set)
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return tuple: a tuple storing in ``[0]`` a list containing the node ``name`` attribute of the optimal *kp-set* and in ``[1]``  the optimal *kp-neg* value for the selected metric

        :raise KeyError: when an invalid :class:`~pyntacle.tools.enums.KpnegEnum` is given
        :raise TypeError: if ``k`` is not a positive integer
        :raise ValueError: if ``seed`` is not a positive integer or if ``max_distance`` is not  :py:class:`None` or a positive integer
        :raise IllegalKpsetSizeError: if ``k`` is equal or greater to the graph size
        """

        if metric == KpnegEnum.F or metric == KpnegEnum.dF:
            if max_distance is not None and not isinstance(max_distance, int) and max_distance > 1 and max_distance <= graph.vcount():
                raise ValueError(u"'max_distance' must be an integer greater than one and lesser than the total number of nodes")

            node_indices = graph.vs.indices
            random.shuffle(node_indices)

            S = node_indices[0:k]

            if graph.vcount() - k == 1:  # a size that leaves only one node left, a g-k < 1 is dealt by the decorator
                S.sort()
                final = graph.vs(S)["name"]
                sys.stdout.write(
                    u"A node set of size {} leaves only one node, returning the maximum {} score (1) and a random node set {}. \n".format(
                        k, metric.name, final))
                return final, 1

            S.sort()

            if metric == KpnegEnum.F:
                type_func = partial(kp.F)
            else:
                type_func = partial(kp.dF, max_distance=max_distance, cmode=cmode)

            final, fragmentation_score = GreedyOptimization.__optimization_loop(graph, S, type_func)

            final = graph.vs(S)["name"]
            sys.stdout.write(
                u"Optimal group: {}\n Group size = {}\n Metric = {}\n Score = {}\n".format(
                    "{" + str(final).replace("'", "")[1:-1] + "}",
                    k,
                    metric.name.replace("_", " "),
                    fragmentation_score))

            return final, round(fragmentation_score, 5)

        else:
            raise KeyError(
                u"The parameter 'metric' is not valid. It must be one of the following: {}".format(list(KpnegEnum)))

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def reachability(graph, k: int, metric: KpposEnum, seed=None, max_distance: int=None, m=None,
                     cmode=CmodeEnum.igraph) -> (list, float):
        r"""
        It searches for the best *key player* (*kp*) set of a predefined size :math:`k`, also defined as positive key
        players (*kp-pos*) using reachability indices, described in Pyntacle
        `introductory guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_
        The optimal kp set will be the one that have the higher reachability if no switching of nodes from the set
        :math:`k` to the rest of the nodes in the graph :math:`N-k` can improve the selected reachability score.

        | Available reachability indices:

            * **m-reach**: min = 0 (unreachable); max = :math:`N - k` (graph is totally reached)
            * **dR**: min = 0 (the *k* set is disconnected from the rest of the graph); max = 1 (full reachability of the set)

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param KpposEnum metric: on of the available :class:`~pyntacle.tools.enums.KpposEnum`
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        :param int,None max_distance: optional, define a maximum shortest path after which two nodes will be considered disconnected. Default is  :py:class:`~None` (no maximum distance is set)
        :param int m: The number of steps of the m-reach algorithm. Required if the the required metrics is the :func:`~tools.enums.KPPosEnum.mreach`
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return tuple: a tuple storing in ``[0]`` a list containing the node ``name`` attribute of the optimal *kp-set* and in ``[1]``  the optimal *kp-pos* value for the selected metric

        :raise KeyError: when an invalid :class:`~pyntacle.tools.enums.KpposEnum` is given
        :raise TypeError: if ``k`` is not a positive integer
        :raise ValueError: if ``seed`` is not a positive integer or if ``max_distance`` is not  :py:class:`None` or a positive integer lesser than the total number of nodes minus one
        :raise IllegalKpsetSizeError: if ``k`` is equal or greater to the graph size
        """

        if metric == KpposEnum.mreach or metric == KpposEnum.dR:

            if max_distance is not None and not isinstance(max_distance, int) and max_distance > 1 and max_distance <= graph.vcount():
                raise ValueError(u"'max_distance' must be an integer greater than one and lesser than the total number of nodes")

            if metric == KpposEnum.mreach and m is None:
                raise WrongArgumentError("The parameter 'm' is required for m-reach algorithm")
            elif metric == KpposEnum.mreach and (not isinstance(m, int) or m <= 0):
                raise TypeError(u"The parameter 'm' must be a positive integer value")
            else:

                node_indices = graph.vs.indices
                random.shuffle(node_indices)

                S = node_indices[0:k]
                S.sort()
                S_names = graph.vs(S)["name"]

                if metric == KpposEnum.mreach:
                    if cmode != CmodeEnum.igraph:
                        sps = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=None)
                        type_func = partial(kp.mreach, nodes=S_names, m=m, max_distance=max_distance,
                                            cmode=cmode, sp_matrix=sps)
                    else:
                        type_func = partial(kp.mreach, nodes=S_names, m=m, max_distance=max_distance,
                                            cmode=cmode)
                else:
                    if cmode != CmodeEnum.igraph:
                        sps = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=None)
                        type_func = partial(kp.dR, nodes=S_names, max_distance=max_distance,
                                            cmode=cmode, sp_matrix=sps)
                    else:
                        type_func = partial(kp.dR, nodes=S_names, max_distance=max_distance,
                                            cmode=cmode)

                final, reachability_score = GreedyOptimization.__optimization_loop(graph, S, type_func)

                final = graph.vs(S)["name"]
                sys.stdout.write(
                    u"Optimal group: {}\n Group size = {}\n Metric = {}\n Score = {}\n".format(
                        "{" + str(final).replace("'", "")[1:-1] + "}",
                        k,
                        metric.name.replace("_", " "),
                        reachability_score))

                return final, round(reachability_score, 5)
        else:
            raise KeyError(
                u"The parameter 'metric' is not valid. It must be one of the following: {}".format(list(KpposEnum)))

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def group_centrality(graph, k: int, metric: GroupCentralityEnum, seed: int or None =None,
                         distance_type: GroupDistanceEnum = GroupDistanceEnum.minimum,
                         cmode=CmodeEnum.igraph,) -> (list, float):
        r"""
        It searches and finds the optimal set of nodes of a predefined size that exhibits the maximum group centrality
        value. It generates all the possible sets of nodes and calculates their group centrality value.
        | Available centrality metrics are :func:`~pyntacle.algorithms.local_topology.LocalTopology.group_degree`,
        :func:`~pyntacle.algorithms.local_topology.LocalTopology.group_closeness` and
        :func:`~pyntacle.algorithms.local_topology.LocalTopology.group_betweenness`.
        The best sets will be those with maximum centrality score.

        | Group Centrality measures available:

            * **group degree**: min = 0 (lowest centrality); max = 1 (highest centrality)
            * **group closeness**: min = 0 (lowest centrality); max = 1 (highest centrality)
            * **group betweenness**: min = 0 (lowest centrality); max = 1 (highest centrality)

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page
        :param int k: a positive integer, the size of the group of nodes to be found
        :param GroupCentralityEnum metric: The centrality algorithm to be computed. It can be any of the :class:`~pyntacle.tools.enums.GroupCentralityEnum`
        :param cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        :param GroupDistanceEnum distance_type: The definition of distance between any non-group and group nodes. It can be any value of the enumerator :class:`~pyntacle.tools.enums.GroupDistanceEnum`. By default, the minimum least distance :math:`D` between the group :math:`k` and the rest of the graph :math:`N-k` is used

        :return tuple: a tuple storing in ``[0]`` a list containing the node ``name`` attribute of the optimal *kp-set* and in ``[1]``  the optimal *kp-neg* value for the selected metric

        :raise KeyError: when an invalid :class:`~pyntacle.tools.enums.GroupCentralityEnum` is given
        :raise TypeError: if ``k`` is not a positive integer
        :raise ValueError: if ``seed`` is not a positive integer or if ``max_distance`` is not  :py:class:`None` or a positive integer lesser than the total number of nodes minus one
        :raise IllegalKpsetSizeError: if ``k`` is equal or greater to the graph size
        """

        if metric == GroupCentralityEnum.group_degree:
            type_func = partial(LocalTopology.group_degree, graph=graph)
        elif metric == GroupCentralityEnum.group_betweenness:
            np_counts = sp.get_shortestpath_count(graph, nodes=None, cmode=cmode)
            type_func = partial(LocalTopology.group_betweenness, graph=graph, cmode=cmode, np_counts=np_counts)
        elif metric == GroupCentralityEnum.group_closeness:
            type_func = partial(LocalTopology.group_closeness, graph=graph, cmode=cmode, distance=distance_type)
        else:
            raise KeyError(
                u"The parameter 'metric' is not valid. It must be one of the following: {}".format(list(GroupCentralityEnum)))

        node_indices = graph.vs.indices
        random.shuffle(node_indices)
        S = node_indices[0:k]
        S.sort()

        final, group_score = GreedyOptimization.__optimization_loop(graph, S, type_func)

        final = graph.vs(S)["name"]

        metrics_distance_str = metric.name.replace("_", " ") \
            if metric != GroupCentralityEnum.group_closeness \
            else metric.name.replace("_", " ") + " - Distance function = " + distance_type.name
        sys.stdout.write(
            u"Optimal group: {}\n Group size = {}\n Metric = {}\n Score = {}\n".format(
                "{" + str(final).replace("'", "")[1:-1] + "}",
                k,
                metrics_distance_str,
                group_score))

        return final, round(group_score, 5)
