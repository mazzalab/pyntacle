"""
Compute several local topology metrics for a graph's nodes
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.4"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "14/04/2018"
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


from tools.misc.graph_routines import *
from tools.misc.enums import Cmode
from tools.graph_utils import GraphUtils as gUtil
from algorithms.shortest_path import ShortestPath


class LocalTopology:
    """
    Compute centrality measures locally to a graph. Methods are designed to work with all or selected nodes.
    """

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def degree(graph: Graph, nodes=None) -> list:
        """
        Compute the *degree* of a node or of a list of nodes of an undirected graph. The degree is defined as
        the number of incident edges to a node.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of integers, the length being the number of input nodes. Each integer represent the degree
        of the input nodes. The order of the node list in input is preserved.
        """

        return graph.degree(nodes) if nodes else graph.degree()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def betweenness(graph: Graph, nodes=None) -> list:
        """
        Compute the *betweenness* of a node or of a list of nodes of an undirected graph.
        The betweenness is defined as the ratio of the number of shortest paths that pass through the node
        over all shortest paths in the graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of floats, the length being the number of input nodes. Each float represents the betweenness
        of the input nodes. The order of the node list in input is preserved.
        """

        return graph.betweenness(nodes, directed=False) if nodes else graph.betweenness(directed=False)

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
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of floats, the length being the number of input nodes. Each float represents the clustering
        coefficient of the input nodes. The order of the node list in input is preserved.
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
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of floats, the length being the number of input nodes. Each float represents the closeness
        of the input node. The order of the node list in input is preserved.
        """

        return graph.closeness(vertices=nodes) if nodes else graph.closeness()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def eccentricity(graph: Graph, nodes=None) -> list:
        """
        Computes the *eccentricity* of a node or of a list of nodes of an undirected graph.
        The eccentricity is defined as the maximum of all the distances (shortest paths) between the input node
        and all other nodes in the graph. The eccentricity of any two disconnected nodes is defined as zero.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of integers, the length being the number of input nodes. Each value represents the eccentricity
        of the input node. The order of the node list in input is preserved.
        """

        return list(map(int, graph.eccentricity(vertices=nodes))) if nodes else list(map(int, graph.eccentricity()))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def radiality(graph: Graph, nodes=None, cmode: Cmode=Cmode.igraph) -> list:
        """
        Compute the *radiality* of a node or of a list of nodes of an undirected graph.
        The radiality of a node *v* is calculated by first computing the shortest path between *v* and all other nodes
        in the graph. The length of each path is then subtracted by the value of the diameter +. Resulting values are
        then summated and weighted over the total number of nodes -1. Finally, the obtained value is divided by the
        number of nodes -1 (n-1).
        **WARNING:** Radiality works well with connected graph. If a node is isolated, its radiality is
        always *-inf*. If a graph is made of more than one component, we recommend using the *radiality_reach*
        method.
        :param igraph.Graph graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
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

        diameter = graph.diameter()
        num_nodes = graph.vcount()
        rad_list = []

        sps = ShortestPath.get_shortestpaths(graph, nodes=nodes, cmode=cmode)
        for sp in sps:
            partial_sum = 0
            for sp_length in sp:
                if sp_length != 0:
                    partial_sum += diameter + 1 - sp_length

            rad_list.append(round(float(partial_sum / (num_nodes - 1)), 5))

        return rad_list

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def radiality_reach(graph: Graph, nodes=None, cmode=Cmode.igraph) -> list:
        """
        Computes the radiality reach for a single node, a list of nodes or for all nodes in the Graph.
        The radiality reach is a weighted measure of the canonical radiality and it is recommended for disconnected
        graphs. Specifically, if a graph has more than one components, we calculate the radiality for each node within
        its component, then we multiply the radiality value withe the proportion of te nodes of that component over all
        the nodes in the graph. The radiality reach of a graph with only one component will hence be equal to the
        radiality, while a graph with several components will have several radiality values.
        *if you want the radiality for a disconnected graph, we recommend to subset the original graph and then use
        the radiality() function containied in this module.*
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :param Enum.cmode cmode: the way you prefer to compute the shortest path for the whole graph. choices are:
        * *'igraph'*: uses the Dijsktra's algorithm implemented from igraph
        * *'parallel_CPU'*: uses a parallel CPU cmode of the Floyd-Warshall algorithm using numba
        * *'parallel_GPU'*: uses a parallel GPU cmode of the Floyd-Warshall algorithm using numba
        **(requires NVIDIA graphics compatible with CUDA)**
        :return: a list of floats, the length being the number of input nodes. Each float represent the closeness
        of the input node
        """
        comps = graph.components()  # define each case
        if len(comps) == 1:
            return LocalTopology.radiality(graph=graph, nodes=nodes, cmode=cmode)

        else:
            tot_nodes = graph.vcount()
            if nodes is None:
                res = [None] * tot_nodes

                for c in comps:
                    subg = graph.induced_subgraph(vertices=c)

                    if subg.ecount() < 1:  # isolates do not have a radiality_reach by definition
                        rad = [0]

                    else:
                        part_nodes = subg.vcount()
                        rad = LocalTopology.__radiality_inner__(graph=subg, nodes=nodes, implementation=cmode)

                        # rebalance radiality by weighting it over the total number of nodes
                        for i, elem in enumerate(rad):
                            rad[i] = elem * (part_nodes / tot_nodes)

                    for i, ind in enumerate(c):
                        res[ind] = rad[i]

                return res

            else:

                res = [None] * len(nodes)

                inds = gUtil(graph=graph).get_node_indices(nodes)

                for c in comps:
                    if any(x in c for x in inds):
                        node_names = list(set(nodes) & set(graph.vs(c)["name"]))
                        subg = graph.induced_subgraph(vertices=c)
                        part_nodes = subg.vcount()
                        rad = LocalTopology.__radiality_inner__(graph=subg, nodes=node_names,
                                                                implementation=cmode)
                        for i, elem in enumerate(rad):
                            rad[i] = elem * (part_nodes / tot_nodes)

                        for i, elem in enumerate(node_names):
                            orig_index = nodes.index(elem)
                            res[orig_index] = rad[i]
                return res

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def eigenvector_centrality(graph, nodes, scaled=False):
        """
        Calculates the eigenvector centrality for a single nodes, a group of selected nodes or all nodes in the graph.
        The eigenvector centrality is defined as the contribution of the leading eigenvector for a node among all the
        other nodes in its graph. It represents the importance of a node with respect to its neighbours.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the shortest path between the input nodes and all other nodes in the graph is returned for all node names.
        If None (default), the degree is computed for the whole graph.
        :param bool scaled: a Boolean to scale the eigenvector centrality using the reciprocal of the eigenvector
        (1/eigenvector). Default is False.
        :return: a list of floats, the length being the number of input nodes. Each value is the eigenvector centrality
        value for the selected node(s)..
        """
        if not isinstance(scaled, bool):
            raise ValueError("Scaled must be a boolean")

        if nodes is None:
            return graph.evcent(graph, directed=False, scale=scaled)
        else:
            inds = gUtil(graph=graph).get_node_indices(nodes)
            evcent_values = list(graph.evcent(directed=False, scale=scaled)[i] for i in inds)
            return evcent_values

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def pagerank(graph: Graph, nodes=None, weights=None, damping=0.85) -> list:
        """
        Computes the Google PageRank algorithm from the input node(s), or for all nodes in the graph if it's not
        specified. The PageRank algorithm is a modifed version of the eigenvector centrality. It highlights the
        importance of a node by means of the number of edges that connects him and if these edges come from neighbours
        with high centrality. A likelihood distribution is computed to check what is the chance that a random walk
        passes through the selected node(s). the higher is the centrality of the node, the higher is the probability of
        passing through it. for more info, please refer to http://infolab.stanford.edu/~backrub/google.html for more
        info.
        :param graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the shortest path between the input nodes and all other nodes in the graph is returned for all node names.
        If None (default), the degree is computed for the whole graph.
        :param weights: a list of floats minus or equal to the total number of edges.
        :param damping : a damping factor representing the probability to reset the random walk distribution at each
        pagerank iteration. Default is 0.85.
        :return: a list of floats representing the pagerank value for the selected node(s)
        """
        if weights is not None:
            if not isinstance(weights, list):
                raise TypeError("Weights must be a list of floats")

            if not all(isinstance(x, (float, type(None))) for x in weights):
                raise ValueError("Weights must be a list of floats")

            if len(weights) > graph.ecount():
                raise ValueError("Weights must be equal or inferior to the total number of edges")

        if not (isinstance(damping, (float, int)) and (0 <= damping)):
            raise ValueError("Damping factor must be a float >= 0")
        
        if nodes is not None:
            nodes = gUtil(graph).get_node_indices(nodes)

        return graph.pagerank(vertices=nodes, damping=damping, directed=False, weights=weights, implementation="arpack")
