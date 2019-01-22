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


from tools.enums import CmodeEnum, GroupDistanceEnum
from tools.graph_utils import GraphUtils as gUtil
from algorithms.shortest_path import ShortestPath
from internal.graph_routines import check_graph_consistency, vertex_doctor
from igraph import Graph
import numpy as np
import itertools
from math import inf, isinf

class LocalTopology:
    r"""
    A series of indices to assess centrality for single nodes or groups of nodes
    """

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def degree(graph: Graph, nodes: str or list or None=None) -> list:
        r"""
        Computes the *degree*, the number of of incident edges to a node, for all nodes :math:`N` in the graph or for a selected subset of nodes in the graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`__ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the degree for all nodes in the graph. Otherwise, Otherwise, a node name (the vertex ``name`` attribute) or a list them can be provided to compute degree for a subset of vertices.

        :return list: a list of positive integers representing the node(s) degree(s)s. If ``nodes`` is :py:class:`None`, it returns a sequence of degree ordered by node ``index``, otherwise returns the degree of the input node(s). The order of the node list in input is preserved if the measure is computed for a subset of nodes.

        :raise TypeError: if any type other than the ones supported is passed to `nodes``
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph.
        """

        return graph.degree(nodes) if nodes else graph.degree()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def group_degree(graph: Graph, nodes: list) -> float:
        r"""
        Computes the *group degree* for a subset of nodes in the input graph. This measure is an extension of the degree
        that counts the number of non-group nodes (:math:`N-k`) that are connected to group members (:math:`k`).
        Group degree is then normalized by dividing the tgotal number of incident edges of the group by :math:`N-k`

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list nodes: A list of  node ``name``s of the nodes that are used to compute group degree

        :return float: The normalized group degree centrality

        :raise TypeError: when ``nodes`` is not one of the valid types
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph.
        """

        gu = gUtil(graph)
        nodes_ind = gu.get_node_indices(nodes)

        selected_neig = graph.neighborhood(nodes, order=1, mode="all")
        flat_list = [item for sublist in selected_neig for item in sublist if item not in nodes_ind]
        normalized_score = len(set(flat_list)) / (len(graph.vs) - len(nodes))

        return round(normalized_score, 5)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def betweenness(graph: Graph, nodes=None) -> list:
        r"""
        Computes the *betweenness*, the ratio of the number of shortest paths that pass through a  node :math:`i`
        over all the possible shortest paths in the graph :math:`G`. Betweenness can be computed for all nodes :math:`N` in the
        graph or for a selected subset of nodes in the graph.

        .. note:: The betweenneess is returned **unnormalized**, as normalization requires to know all the betweenness values for all nodes. To normalize, you can compute betwenness for each node and then use the following formula: :math:`\frac{betwenness(i) - min(G)}{max(betweenness(G) - min(betwennness(G))}`

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the betweenness for all nodes in the graph. Otherwise, a single node ``name`` or a list of node ``name``s can be passed to compute betweenness only for the subset of nodes

        :return list: a list of floats, the length being the number of input nodes. Each float represents the betweenness of the input nodes. The order of the node list in input is preserved if the measure is computed for a subset of nodes.

        :raise TypeError: when ``nodes`` is not one of the valid types
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        return graph.betweenness(nodes, directed=False) if nodes else graph.betweenness(directed=False)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def group_betweenness(graph: Graph, nodes: list, cmode: CmodeEnum=CmodeEnum.igraph, np_counts: np.ndarray=None) -> float:
        r"""
        Computes the betweenness centrality of a group of nodes :math:`k`.
        The *group betweenness* indicates the proportion of geodesics connecting pairs of non-group members that
        pass through the group :math:`k`. This measure is computed as follows:

            #. Count the number of geodesics between every pair of non-group members, yielding a node-by-node matrix of counts
            #. Delete all ties involving group members and redo the calculation, creating a new node-by-node matrix of counts
            #. Divide each cell in the new matrix by the corresponding cell in the first matrix
            #. Take the sum of all these ratios.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param np.ndarray,None np_counts: Optional: a :py:class:`numpy.ndarray` of positive integers representing a :math`NxN` squared matrix storing shortest paths between any pair of nodes of the graph. Passing this argument would make the overall calculation faster. Recommended for large Graps (:math:`N>1000`)
        :param list nodes: A list of  node ``name``s of the nodes that are used to compute group betweenness

        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search. Will be ignored if ``np_cpunts`` is provided

        :return float: The normalized group betweenness centrality, obtained by dividing the group betweenness by the number of non-group nodes.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute or ``np_counts`` is not either a :py:class:`numpy.ndarray` or is empty
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        # Count geodesics of the original graph
        if np_counts is not None:
            if not isinstance(np_counts, np.ndarray):
                raise TypeError("np_counts must be None or a nump.nparray, {} found".format(type(np_counts).__name__))

            if not all(x == graph.vcount() for x in np_counts.shape):
                raise ValueError("np_counts must be squared and of the same size of the graph ({})".format(graph.vcount()))

            count_all = np_counts

        else:
            count_all = ShortestPath.get_shortestpath_count(graph, nodes=None, cmode=cmode)

        # Get the corresponding node indices
        nodes_index = gUtil(graph).get_node_indices(nodes)

        # Count geodesics that do not pass through the group
        del_edg = [graph.incident(vertex=nidx) for nidx in nodes_index]
        del1 = set(list(itertools.chain(*del_edg)))

        graph_notgroup = graph.copy()
        graph_notgroup.delete_edges(del1)
        count_notgroup = ShortestPath.get_shortestpath_count(graph_notgroup, nodes=None, cmode=cmode)

        # Count geodesics that do pass through the group
        count_group = ShortestPath.subtract_count_dist_matrix(count_all, count_notgroup)

        # Divide the number of geodesics (g(C) / g)
        group_btw_temp = np.divide(count_group, count_all,
                                   out=np.zeros_like(count_group, dtype=np.float),
                                   where=count_all != 0)

        # discard group-nodes (set group nodes' rows and columns to zero)
        group_btw_temp[nodes_index] = 0
        group_btw_temp[:, nodes_index] = 0

        # sum not-nan counts upper triangular matrix (SUM u<v)
        group_btw = np.sum(np.triu(group_btw_temp, 0), dtype=np.float) / 2

        # normalization
        graph_size = len(graph.vs)
        group_size = len(nodes_index)
        group_btw = (2 * group_btw) / ((graph_size - group_size) * (graph_size - group_size - 1))

        return round(group_btw, 5)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def clustering_coefficient(graph: Graph, nodes: list or str or None=None) -> list:
        r"""
        Returns the *clustering coefficient* of a single node, a list of nodes or for all nodes of he input graph.
        The clustering coefficient is the number of triangles formed among the node's neighbours over the
        possible number of triangles that the node and its neighbours would form if they were a clique. It ranges from
        0 and 1. High value of clustering coefficient indicates that the vertex is highly connected to its neighborhood,
        and vice-versa.

        .. note:: If the degree of the input node is less than two, the clustering coefficient of these nodes is set to zero.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the clustering coefficient for all nodes in the graph. Otherwise, a single node ``name`` or a list of node ``name``s can be passed to compute the clustering coefficient only for the subset of nodes

        :return list: a list of floats, the length being the number of input nodes. Each float value represents the clustering coefficient of the input nodes. The order of the node list in input is preserved.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        return graph.transitivity_local_undirected(vertices=nodes, mode="zero") \
            if nodes \
            else graph.transitivity_local_undirected(mode="zero")

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def closeness(graph: Graph, nodes: list or str or None=None) -> list:
        r"""
        The *closeness* of a single node, a list of nodes or for all nodes of the input graph.
        The closeness is the  reciprocal of the sum of all geodesic distances (shortest paths) passing
        through a node. The highest the closeness, the "closest" is the node to the rest of the graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the closeness for all nodes in the graph. Otherwise, a single node ``name`` or a list of node ``name``s can be passed to compute the closeness only for the subset of nodes

        :return: a list of floats, the length being the number of input nodes. Each float value represents the closeness of the input node. The order of the node list in input is preserved if the measure is computed for a subset of nodes.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        return graph.closeness(vertices=nodes) if nodes else graph.closeness()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def group_closeness(graph: Graph, nodes: list, distance: GroupDistanceEnum=GroupDistanceEnum.minimum, cmode: CmodeEnum=CmodeEnum.igraph,
                        np_paths: np.ndarray or None=None) -> float:
        r"""
        Computes the closeness centrality for a group of nodes, rather than a single-node resolution as in
        :func:`~pyntacle.algorithms.local_topology.LocalTopology.closeness`. The *group closeness* is defined as the sum
        of the distances from the group to all vertices outside the group.
        As with individual closeness, this produces an inverse measure of closeness as larger numbers indicate
        less centrality.

        This definition deliberately leaves unspecified how distance from the group to an outside
        vertex is to be defined. `Everett and Borgatti <https://doi.org/10.1080/0022250X.1999.9990219>`_
        propose to consider the set :math:`D` of all distances from a single vertex to a set of vertices.

        The distance from the vertex to the set can be defined as either the *maximum*
        the *minimum* or the *mean* of values in :math:`D`. Following `Freeman convention <http://dx.doi.org/10.1016/0378-8733(78)90021-7>`_, we can normalize
        group closeness by dividing the distance score into the number of non-group members, with the result
        that larger numbers indicate greater centrality.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list nodes: A list of node ``name``\s (the vertex ``name`` attribute) of the nodes belonging to the group
        :param GroupDistanceEnum distance: The definition of distance between any non-group and group nodes. It can be any value of the enumerator :class:`~pyntacle.tools.enums.GroupDistanceEnum`. By default, the minimum least distance :math:`D` between the group :math:`k` and the rest of the graph :math:`N-k` is used
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths required for group closeness. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search. Will be ignored if ``np_cpunts`` is provided
        :param np.ndarray,None np_paths: a :py:class:`numpy.ndarray` of positive integers representing a :math`NxN` squared matrix storing shortest paths between any pair of nodes of the graph. Passing this argument would make the overall calculation faster. Recommended for large Graps (:math:`N>1000`)

        :return float: The normalized group closeness centrality, obtained by dividing the group closeness by the number of non-group nodes.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        MAX_PATH_LENGHT = len(graph.vs) + 1

        if not isinstance(distance, GroupDistanceEnum):
            raise TypeError("'distance' is not one of the appropriate GroupDistanceEnum, {} found".format(type(distance).__name__))

        if not isinstance(np_paths, (type(None), np.ndarray)):
            raise TypeError("'np_paths' is not one NoneType or a numpy array")

        if distance == GroupDistanceEnum.maximum:
            def dist_func(x: list) -> int: return max(x)
        elif distance == GroupDistanceEnum.minimum:
            def dist_func(x: list) -> int: return min(x)
        elif distance == GroupDistanceEnum.mean:
            def dist_func(x: list): return sum(x) / len(x)
        #todo Tommaso, we never use this piece of code, can we remove it? I commented it
        else:
            # MIN is the default choice
            # def dist_func(x: list) -> int: return min(x)
            raise ValueError(u"'distance' is not one of the appropriate GroupDistanceEnum")

        #added by Daniele - recompute shortest paths
        if np_paths is None:
            np_paths = ShortestPath.get_shortestpaths(graph=graph, cmode=cmode)


        group_indices = gUtil(graph).get_node_indices(nodes)
        nongroup_nodes = list(set(graph.vs["name"]) - set(nodes))
        nongroup_nodes_indices = gUtil(graph).get_node_indices(nongroup_nodes)
        # nongroup_np_paths2 = ShortestPath.get_shortestpaths(graph, nongroup_nodes, cmode=cmode)
        nongroup_np_paths = np_paths.take(nongroup_nodes_indices, axis=0)
        # assert (nongroup_np_paths == nongroup_np_paths2).all(), "Error"

        group_closeness = 0
        for np_path in nongroup_np_paths:
            temp_list = [elem for elem in np_path[group_indices] if elem != MAX_PATH_LENGHT]
            if temp_list:
                group_closeness += dist_func(temp_list)

        normalized_score = len(nongroup_nodes) / group_closeness
        return round(normalized_score, 5)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def eccentricity(graph: Graph, nodes: list or str or None=None) -> list:
        r"""
        Computes the *eccentricity*, the maximum of all the distances (shortest paths) between the input node
        and all other nodes in the graph for a single node, a list of nodes  or all nodes in the input graph.

        .. note:: The eccentricity of any two disconnected nodes is defined as zero.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the eccentricity for all nodes in the graph. Otherwise, a node name (the vertex ``name`` attribute) or a list them can be provided to compute eccentricity only for a subset of nodes

        :return list: a list of positive integers, the length being the number of input nodes. Each value represents the eccentricity of the input node. If a list of node ``name``\s is passed, the order of the node list in input is preserved.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        return list(map(int, graph.eccentricity(vertices=nodes))) if nodes else list(map(int, graph.eccentricity()))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def radiality(graph: Graph, nodes: list or str or None=None, cmode: CmodeEnum=CmodeEnum.igraph) -> list:
        r"""
        Compute the *radiality* index of a node, a list of nodes or all nodes of an undirected graph.
        The radiality of a vertex :math:`i` is an index that assign high centrality to nodes that are at a short
        distance to every other node :math:`j` in its reachable neighbors with respect to the graph :func:`~pyntacle.algorithms.global_topology.GlobalTopology.diameter`

        It is calculated by first computing the shortest paths between *i* and all other nodes
        in the graph. The length of each path is then subtracted from the diameter +1. The resulting values are
        then added and divided by the number of nodes -1 (:math:`N-1`).

        The radiality should be always compared to the :func:`~pyntacle.algorithms.local_topology.LocalTopology.closeness`
        and to the :func:`~pyntacle.algorithms.local_topology.LocalTopology.eccentricity`:
        a node with high eccentricity + high closeness + high radiality is a consistent indication of a
        high central position in the graph.

        .. warning:: Radiality is informative if the input graph has only one component. as the distance between two disconnected nodes is infinite by definition, the radiality for a graph with two components is always infinite, as some nodes are disconnected. Hence, we recommend using our modified version of radiality, :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality_reach`. alternatively, we recommend to subset the graph taking only the component of interest.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute radiality. When :py:class:`None`, it computes the degree for all nodes in the graph. Otherwise, a single node ``name`` or a list of node ``name``s can be passed to compute degree only for the subset of nodes
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths required for radiality. It can be nay of the :class:`~pyntacle.tools.enums.CmodeEnum` options. Default is the igraph brute-force shortest path search.

        :return: a list of floats, the length being the number of input nodes. Each float represents the radiality of the input node. The order of the node list in input is preserved.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        diameter_plus_one = graph.diameter() + 1
        num_nodes_minus_one = graph.vcount() - 1
        rad_list = []

        sps = ShortestPath.get_shortestpaths(graph, nodes=nodes, cmode=cmode)
        inf_set = graph.vcount() + 1  # the infinite distances that will come out from sps
        sps = sps.astype(float) #infinite value are float and numpy cannot modify the np.ndarray type
        sps[sps == inf_set] = inf

        for sp in sps: #Cycle through numpy rows

            partial_sum = sum(diameter_plus_one - distance for distance in sp if distance != 0)
            rad_list.append(round(float(partial_sum / num_nodes_minus_one), 5))

        return rad_list

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def radiality_reach(graph: Graph, nodes: list or str or None =None, cmode: CmodeEnum=CmodeEnum.igraph) -> list:
        r"""
        Compute the *radiality-reach* of a node or of a list of nodes of an undirected graph.
        The radiality-reach is a weighted version of the canonical radiality measure and it is recommended for
        graphs with multiple components. Specifically, if a graph has more than one components, we calculate the
        radiality for each node inside the component, then we multiply the radiality value by the proportion of nodes
        of that component over all nodes in the graph.
        Hence, the radiality-reach of a graph with only one component will be equal to the radiality, while nodes in
        a graph with two disconnected components will exhibit radiality values for each components and weighted over the
        contribution of that component to the whole graph.

        .. note:: the radiality reach of node isolates is zero by definition

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the centrality index. When :py:class:`None`, it computes the radiality reach for all nodes in the graph. Otherwise, a single node  (identified using the ``name`` attribute) or a list of node names can be passed to compute radiality reach only for the subset of node of interest
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths required for each radiality reach value. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return list: a list of floats, the length being the number of input nodes. Each float represents the radiality-reach of the input node. The order of the node list in input is preserved.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """
        comps = graph.components()  # define the cases
        if len(comps) == 1:
            return LocalTopology.radiality(graph=graph, nodes=nodes, cmode=cmode)
        else:
            tot_nodes = graph.vcount()
            if nodes is None:
                result = [None] * tot_nodes

                for c in comps:
                    subg = graph.induced_subgraph(vertices=c)

                    if subg.ecount() == 0:  # isolates do not have a radiality-reach value by definition
                        rad = [0]
                    else:
                        part_nodes = subg.vcount()
                        rad = LocalTopology.radiality(graph=subg, nodes=nodes, cmode=cmode)

                        # rebalance radiality by weighting it over the total number of nodes
                        proportion_nodes = part_nodes / tot_nodes
                        rad = [r * proportion_nodes for r in rad]

                    for i, ind in enumerate(c):
                        result[ind] = rad[i]

                return result
            else:
                result = [None] * len(nodes)
                inds = gUtil(graph=graph).get_node_indices(nodes)

                for c in comps:
                    if any(x in c for x in inds):
                        node_names = list(set(nodes) & set(graph.vs(c)["name"]))
                        subg = graph.induced_subgraph(vertices=c)
                        part_nodes = subg.vcount()
                        rad = LocalTopology.radiality(graph=subg, nodes=node_names, cmode=cmode)

                        proportion_nodes = part_nodes / tot_nodes
                        rad = [r * proportion_nodes for r in rad]

                        for i, elem in enumerate(node_names):
                            orig_index = nodes.index(elem)
                            result[orig_index] = rad[i]
                return result

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def eigenvector_centrality(graph: Graph, nodes: list, scaled: bool=False):
        r"""
        Calculate the *eigenvector centrality* for a single node, a list of nodes or all nodes in the input graph.
        The eigenvector centrality is a measure of the influence of a node in a network with respect to its neighbours.
        Relative scores are assigned to all nodes in the network based on the concept that connections to high-scoring
        nodes contribute more to the score of the node in question than equal connections to low-scoring nodes.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the degree for all nodes in the graph. Otherwise, a single node ``name`` or a list of node ``name``s can be passed to compute degree only for the subset of nodes
        :param bool scaled: a boolean value to scale the eigenvector centrality using the reciprocal of the eigenvector (1/eigenvector). ``False` by default.

        :return list: a list of floats, the length being the number of input nodes. Each float represents the eigenvector of the input node. The order of the node list in input is preserved if a subset of nodes is provided.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        :raise ValueError: if ``scaled`` is not a :py:class:`bool`
        """
        if not isinstance(scaled, bool):
            raise ValueError("'scaled' must be a boolean value (True or False)")
        elif nodes is None:
            evcent = graph.evcent(directed=False, scale=scaled)
            return [round(e, 5) for e in evcent]
        else:
            inds = gUtil(graph=graph).get_node_indices(nodes)
            evcent = graph.evcent(directed=False, scale=scaled)
            evcent_values = [round(evcent[i], 5) for i in inds]
            return evcent_values

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def pagerank(graph: Graph, nodes: list or str or None =None, weights:list =None, damping: float=0.85) -> list:
        r"""
        The notorious `Google PageRank <http://infolab.stanford.edu/~backrub/google.html>`_ algorithm that can be calculated for
        a single node, a list of nodes or for all nodes of the input graph.
        The PageRank algorithm is a modified version of the :func:`~pyntacle.algorithms.local_topology.LocalTopology.eigenvector_centrality`.
        The importance of a node is here a function of the number of issuing edges and the importance of the neighbour nodes.
        A likelihood distribution is computed to check what is the chance that a random walk passes through the
        selected node(s). The higher is the centrality  value of the node, the higher is the probability of passing through it.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page
        :param None,str,list nodes: The input nodes on which to compute the selected index. When :py:class:`None`, it computes the pagerank for all nodes in the graph. Otherwise, a single node ``name`` or a list of them can be passed to compute degree only for a selected subset of nodes
        :param list, None weights: a list of float numbers less or equal than the total number of edges. The order of the list shoould match the indices of the edge elements of the input graph. Defaults to :py:class:`None` (no weights added).

        :return list: a list of numeric values, the length being the number of input nodes. Each values represents the PageRank of the input node. The order of the node list in input is preserved.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute or ``weights`` is not a list
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        :raise ValueError: if ``damping`` is not a positive float or if ``weights`` does not floats or integers
        """
        if weights is not None:
            if not isinstance(weights, list):
                raise TypeError(u"'weights' must be a list")
            if not all(isinstance(x, (float, type(None))) for x in weights):
                raise ValueError(u"'weights' must be a list of floats")
            if len(weights) > graph.ecount():
                raise ValueError(u"The 'weights' must be equal or less than the total number of edges")

        if not (isinstance(damping, (float, int)) or (damping < 0)):
            raise ValueError(u"Damping factor must be a float >= 0")

        if nodes is not None:
            nodes = gUtil(graph).get_node_indices(nodes)

        return graph.pagerank(vertices=nodes, damping=damping, directed=False, weights=weights, implementation="arpack")
