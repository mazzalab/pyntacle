"""
Compute local topology metrics of nodes
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


from tools.enums import CmodeEnum, GroupDistanceEnum
from tools.graph_utils import GraphUtils as gUtil
from algorithms.shortest_path import ShortestPath
from private.graph_routines import check_graph_consistency, vertex_doctor
from igraph import Graph
import numpy as np

class LocalTopology:
    """
    Compute local centrality measures of all or selected nodes of a given graph.
    """

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def degree(graph: Graph, nodes=None) -> list:
        """
        Compute the *degree* of a node or of a list of nodes of an undirected graph. The degree is defined as
        the number of incident edges to a node.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of integers, the length being the number of input nodes. Each integer represent the degree
        of the input nodes. The order of the node list in input is preserved.
        """

        return graph.degree(nodes) if nodes else graph.degree()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def group_degree(graph: Graph, nodes: list) -> float:
        """
        Computes the degree centrality of a group of nodes.
        It is defined as the  number  of  non-group  nodes  that are connected to group members.
        Multiple ties to the same node are counted only once.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param list nodes: A list of names of the nodes belonging to the group
        :return: The normalized group degree centrality, obtained by dividing the group degree by the number of
        non-group nodes.
        """

        selected_neig = graph.neighborhood(nodes, order=1, mode="all")
        flat_list = [item for sublist in selected_neig for item in sublist if item not in nodes]
        normalized_score = len(set(flat_list)) / (len(graph.vs) - len(nodes))

        return round(normalized_score, 2)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def betweenness(graph: Graph, nodes=None) -> list:
        """
        Compute the *betweenness* of a node or of a list of nodes of an undirected graph.
        The betweenness is defined as the ratio of the number of shortest paths that pass through the node
        over all shortest paths in the graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of floats, the length being the number of input nodes. Each float represents the betweenness
        of the input nodes. The order of the node list in input is preserved.
        """

        return graph.betweenness(nodes, directed=False) if nodes else graph.betweenness(directed=False)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def group_betweenness(graph: Graph, nodes: list, cmode: CmodeEnum=CmodeEnum.igraph, np_counts: np.ndarray=None) -> float:
        """
        Computes the betweenness centrality of a group of nodes.
        The *group betweenness* indicates the proportion of geodesics connecting pairs of non-group members that
        pass through the group. One way to compute this measure is as follows: (a) count the number of geodesics
        between every pair of non-group members, yielding a node-by-node matrix of counts, (b) delete all ties involving
        group members and redo the calculation, creating a new node-by-node matrix of counts, (c) divide each cell in
        the new matrix by the corresponding cell in the first matrix, and (d) take the sum of all these ratios.

        :param np.ndarray np_counts: numpy array containing shortest paths numbers connecting any pair of nodes of the graph.
        Passing this argument would make the overall calculation faster.
        :param igraph.Graph graph: an igraph.Graph object. The graph must hold specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param list nodes: A list of names of the nodes belonging to the group
        :param CmodeEnum cmode: Computation of the shortest paths is deferred to the following implementations:
        *`cmode.auto`: the most performing computing mode is automatically chosen according to the properties of graph
        *`cmode.igraqh`: (default) use the shortest paths implementation provided by igraph
        *`cmode.cpu`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors). This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually
        equal the total number of vertices plus one.
        *`cmode.gpu`: compute shortest paths using the Floyd-Warshall algorithm designed for NVIDIA-enabled GPU graphic
        cards. This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually equal
        the total number of vertices plus one.
        :return: The normalized group betweenness centrality, obtained by dividing the group betweenness by the number
        of non-group nodes.
        """

        # Count geodesics of the original graph
        if np_counts.size is not None:
            count_all = np_counts
        else:
            count_all = ShortestPath.get_shortestpath_count(graph, nodes=None, cmode=cmode)

        # Get the corresponding node indices
        nodes_index = gUtil(graph).get_node_indices(nodes)

        # Count geodesics that do not pass through the group
        del_edg = [graph.incident(vertex=nidx) for nidx in nodes_index]
        del1 = set(del_edg[0] + del_edg[1])
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

        return round(group_btw, 2)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def clustering_coefficient(graph: Graph, nodes=None) -> list:
        """
        Compute the *clustering coefficient* of a node or of a list of nodes of an undirected graph.
        The clustering coefficient is defined as the number of triangles formed among the node's neighbours over the
        possible number of triangles that would be present if the input node and its neighbours were a clique.
        If the degree of the input node is less than two, the clustering coefficient of these nodes is set to zero.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of floats, the length being the number of input nodes. Each float value represents the
        clustering coefficient of the input nodes. The order of the node list in input is preserved.
        """

        return graph.transitivity_local_undirected(vertices=nodes, mode="zero") \
            if nodes \
            else graph.transitivity_local_undirected(mode="zero")

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def closeness(graph: Graph, nodes=None) -> list:
        """
        Computes the *closeness* of a node or of a list of nodes of an undirected graph.
        The closeness is defined as the sum of the length of the shortest paths passing through the node
        over the length of all shortest paths in the graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of floats, the length being the number of input nodes. Each float value represents the closeness
        of the input node. The order of the node list in input is preserved.
        """

        return graph.closeness(vertices=nodes) if nodes else graph.closeness()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def group_closeness(graph: Graph, nodes: list, distance: GroupDistanceEnum=GroupDistanceEnum.minimum,
                        cmode: CmodeEnum=CmodeEnum.igraph) -> float:
        """
        Computes the closeness centrality of a group of nodes.
        The *group closeness* is defined as the sum of the distances from the group to all vertices outside the group.
        As with individual closeness, this produces an inverse measure of closeness as larger numbers indicate
        less centrality. This definition deliberately leaves unspecified how distance from the group to an outside
        vertex is to be defined. Everett and Borgatti propose to consider the set D of all distances from a single
        vertex to a set of vertices. The distance from the vertex to the set can be defined as either the maximum in D,
        the minimum in D or the mean of values in D. Following Freeman’s (1979) convention, we can normalize
        group closeness by dividing the distance score into the number of non-group members, with the result
        that larger numbers indicate greater centrality.
        :param CmodeEnum cmode: Computation of the shortest paths is deferred to the following implementations:
        *`cmode.auto`: the most performing computing mode is automatically chosen according to the properties of graph
        *`cmode.igraqh`: (default) use the shortest paths implementation provided by igraph
        *`cmode.cpu`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors). This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually
        equal the total number of vertices plus one.
        *`cmode.gpu`: compute shortest paths using the Floyd-Warshall algorithm designed for NVIDIA-enabled GPU graphic
        cards. This method returns a matrix (`:type np.ndarray:`) of shortest paths. Infinite distances actually equal
        the total number of vertices plus one.
        :param distance: The definition of distance between any non-group and group nodes. It can be any value
        of the enumerator GroupDistanceEnum
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param list nodes: A list of names of the nodes belonging to the group
        :return: The normalized group closeness centrality, obtained by dividing the group closeness by the number of
        non-group nodes.
        """

        MAX_PATH_LENGHT = len(graph.vs) + 1

        if distance == GroupDistanceEnum.maximum:
            def dist_func(x: list) -> int: return max(x)
        elif distance == GroupDistanceEnum.minimum:
            def dist_func(x: list) -> int: return min(x)
        elif distance == GroupDistanceEnum.mean:
            def dist_func(x: list): return sum(x) / len(x)
        else:
            # MIN is the default choice
            def dist_func(x: list) -> int: return min(x)

        group_indices = gUtil(graph).get_node_indices(nodes)
        nongroup_nodes = list(set(graph.vs["name"]) - set(nodes))
        np_paths = ShortestPath.get_shortestpaths(graph, nongroup_nodes, cmode=cmode)

        group_closeness = 0
        for np_path in np_paths:
            temp_list = [elem for elem in np_path[group_indices] if elem != MAX_PATH_LENGHT]
            if temp_list:
                group_closeness += dist_func(temp_list)

        normalized_score = len(nongroup_nodes) / group_closeness
        return round(normalized_score, 2)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def eccentricity(graph: Graph, nodes=None) -> list:
        """
        Computes the *eccentricity* of a node or of a list of nodes of an undirected graph.
        The eccentricity is defined as the maximum of all the distances (shortest paths) between the input node
        and all other nodes in the graph. The eccentricity of any two disconnected nodes is defined as zero.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of integers, the length being the number of input nodes. Each value represents the eccentricity
        of the input node. The order of the node list in input is preserved.
        """

        return list(map(int, graph.eccentricity(vertices=nodes))) if nodes else list(map(int, graph.eccentricity()))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def radiality(graph: Graph, nodes=None, cmode: CmodeEnum=CmodeEnum.igraph) -> list:
        """
        Compute the *radiality* of a node or of a list of nodes of an undirected graph.
        The radiality of a node *v* is calculated by first computing the shortest path between *v* and all other nodes
        in the graph. The length of each path is then subtracted from the diameter +1. The resulting values are
        then added and divided by the number of nodes -1 (n-1).
        **WARNING:** Radiality works well with connected graph. If a node is isolated, its radiality is
        always *-inf*. If a graph is made of more than one component, we recommend using the *radiality_reach*
        method.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :param cmode: The available computing modes of the shortest paths. Choices are:
        * **`igraph`**: use the Dijsktra's algorithm implemented in iGraph
        * **`parallel_CPU`**: use a parallel implementation of the Floyd-Warshall algorithm running on CPU using Numba
        * **`parallel_GPU`**: use a parallel implementation of the Floyd-Warshall algorithm running on GPU using Numba
        **CAUTION:**(requires NVIDIA-compatible graphics cards)
        :return: a list of floats, the length being the number of input nodes. Each float represents the radiality
        of the input node. The order of the node list in input is preserved.
        """

        diameter_plus_one = graph.diameter() + 1
        num_nodes_minus_one = graph.vcount() - 1
        rad_list = []

        sps = ShortestPath.get_shortestpaths(graph, nodes=nodes, cmode=cmode)
        for sp in sps:
            partial_sum = sum(diameter_plus_one - distance for distance in sp if distance != 0)
            rad_list.append(round(float(partial_sum / num_nodes_minus_one), 5))

        return rad_list

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def radiality_reach(graph: Graph, nodes=None, cmode: CmodeEnum=CmodeEnum.igraph) -> list:
        """
        Compute the *radiality-reach* of a node or of a list of nodes of an undirected graph.
        The radiality-reach is a weighted version of the canonical radiality measure and it is recommended for
        disconnected graphs. Specifically, if a graph has more than one components, we calculate the radiality for each
        node within its component, then we multiply the radiality value by the proportion of nodes of that component
        over all nodes in the graph. Hence, the radiality-reach of a graph with only one component will be equal to the
        radiality, while a graph with several components will have several radiality values.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :param cmode: The available computing modes of the shortest paths. Choices are:
        * **`igraph`**: use the Dijsktra's algorithm implemented in iGraph
        * **`parallel_CPU`**: use a parallel implementation of the Floyd-Warshall algorithm running on CPU using Numba
        * **`parallel_GPU`**: use a parallel implementation of the Floyd-Warshall algorithm running on GPU using Numba
        **CAUTION:**(requires NVIDIA-compatible graphics cards)
        :return: a list of floats, the length being the number of input nodes. Each float represents the radiality-reach
        of the input node. The order of the node list in input is preserved.
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
    def eigenvector_centrality(graph, nodes, scaled=False):
        """
        Calculate the *eigenvector* centrality of a node or of a list of nodes of an undirected graph.
        The eigenvector centrality is defined as the contribution of the leading eigenvector for a node among all the
        other nodes in the graph. It measures the importance of a node with respect to its neighbours.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :param bool scaled: a boolean value to scale the eigenvector centrality using the reciprocal of the eigenvector
        (1/eigenvector). Default is False.
        :return: a list of floats, the length being the number of input nodes. Each float represents the eigenvector
        of the input node. The order of the node list in input is preserved.
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
    def pagerank(graph: Graph, nodes=None, weights=None, damping=0.85) -> list:
        """
        Compute the *Google PageRank* algorithm of a node or of a list of nodes of an undirected graph.
        The PageRank algorithm is a modified version of the eigenvector centrality. The importance of a node is here a
        function of the number of issuing edges and the importance of the neighbour nodes. A likelihood distribution
        is computed to check what is the chance that a random walk passes through the selected node(s). The higher is
        the centrality of the node, the higher is the probability of passing through it.
        For more info, please refer to http://infolab.stanford.edu/~backrub/google.html
        :param graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the Pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :param weights: a list of float numbers less or equal than the total number of edges.
        :param damping: a damping factor representing the probability to reset the random walk distribution at each
        pagerank iteration. Default is 0.85.
        :return: a list of floats, the length being the number of input nodes. Each float represents the PageRank
        of the input node. The order of the node list in input is preserved.
        """
        if weights is not None:
            if not isinstance(weights, list):
                raise TypeError("'weights' must be a list of floats")
            if not all(isinstance(x, (float, type(None))) for x in weights):
                raise ValueError("'weights' must be a list of floats")
            if len(weights) > graph.ecount():
                raise ValueError("The 'weights' must be equal or less than the total number of edges")

        if not (isinstance(damping, (float, int)) or (damping < 0)):
            raise ValueError("Damping factor must be a float >= 0")

        if nodes is not None:
            nodes = gUtil(graph).get_node_indices(nodes)

        return graph.pagerank(vertices=nodes, damping=damping, directed=False, weights=weights, implementation="arpack")
