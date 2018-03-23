__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
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

"""
Compute Local Topology metrics for all nodes in the graph or for a set of nodes
"""
from config import *
from math import isinf
from numba import cuda, jit, prange
import numpy as np
import statistics
from misc.graph_routines import *
from misc.enums import SP_implementations as imps
from misc.enums import GraphType
from misc.shortest_path_modifications import *
from tools.graph_utils import GraphUtils as ut
from misc.implementation_seeker import implementation_seeker


class LocalTopology:
    """
    LocalTopology Computes information at a local level. Information is computed either for a single node or (if not
    specified) for the whole node set in a network
    """

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def degree(graph: Graph, nodes=None) -> list:
        """
        Computes the degree for a single node, a list of nodes or for all nodes in the Graph. The degree is defined as
        the number of incident edges to a single nodes.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :return: a list of integers, the length being the number of input nodes. Each integer represent the degree
        of the input nodes
        """

        if nodes is None:
            return graph.degree()
        else:
            return graph.degree(nodes)

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def betweenness(graph: Graph, nodes=None) -> list:
        """
        Computes the betwenness for a single node, a list of nodes or for all nodes in the Graph.
        The degree is defined as the ratio of the number of shortest path that passes through the node
        over all shortest paths.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :return: a list of floats, the length being the number of input nodes. Each float represent the betweenness
        of the input node
        """

        if nodes is None:
            return graph.betweenness()

        else:
            return graph.betweenness(nodes)

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def clustering_coefficient(graph: Graph, nodes=None) -> list:
        """
        Computes the clustering coefficient for a single node, a list of nodes or for all nodes in the Graph.
        The clustering coefficient is defined as the number of triangles formed among the node's neighbours over the
        possible number of triangles that would be present if the input node(s) and its neighbours were a clique.
        If the degree of the input node(s) is less than two, the clustering coefficient of these nodes is set to zero.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :return: a list of floats, the length being the number of input nodes. Each float represent the clustering
        coefficient of the input node
        """
        if nodes is None:
            return graph.transitivity_local_undirected(mode="zero")
        else:
            return graph.transitivity_local_undirected(vertices=nodes, mode="zero")

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def closeness(graph: Graph, nodes=None) -> list:
        """
        Computes the clustering coefficient for a single node, a list of nodes or for all nodes in the Graph.
        The closeness is defined as the sum of the length of the shortest paths passing through the node(s)
        over all the length of all shortest paths in the graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :return: a list of floats, the length being the number of input nodes. Each float represent the closeness
        of the input node
        """

        if nodes is None:
            return graph.closeness()
        else:
            return graph.closeness(vertices=nodes)

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def eccentricity(graph: Graph, nodes=None) -> list:
        """
        Computes the eccentricity for a single node, a list of nodes or for all nodes in the Graph.
        The eccentricity is defined as the maximum of all the distances (shortest path) between the node(s)
        and all other nodes in the graph. The eccentricity of two disconnected nodes is defined as zero.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :return: a list of integers, the length being the number of input nodes. Each float represent the closeness
        of the input node
        """

        if nodes is None:
            return [int(x) for x in graph.eccentricity()]
        else:
            return [int(x) for x in graph.eccentricity(vertices=nodes)]

    @staticmethod
    def __radiality_inner__(graph: Graph, nodes=None, implementation=imps.auto) -> list:
        """
        inner class that handles the radiality calculus (without throwing any error)
        """
        if not isinstance(implementation, imps):
            raise KeyError(
                "Implementation specified does not exists. Please choose among the following options {}".format(
                    ",".join(list(imps.__members__))))
        else:

            diameter = graph.diameter()
            num_nodes = graph.vcount()
            rad = []  # list that will store radiality values

            if implementation == imps.auto:
                implementation = implementation_seeker(graph)

            if implementation == imps.igraph:
                sps = LocalTopology.shortest_path_igraph(graph, nodes=nodes)  # recall the shortest path function here

            elif implementation == imps.cpu:
                sps = LocalTopology.shortest_path_pyntacle(graph=graph, nodes=nodes,
                                                           mode=GraphType.undirect_unweighted,
                                                           implementation=implementation.cpu)
                sps = sps.tolist()  # reconvert to a list of lists
                sps = [[float('inf') if x == (graph.vcount()+1) else x for x in y] for y in sps]

            else: #GPU case
                sps = LocalTopology.shortest_path_pyntacle(graph=graph, nodes=nodes,
                                                           mode=GraphType.undirect_unweighted,
                                                           implementation=implementation.gpu)
                sps = sps.tolist()  # reconvert to a list of lists
                sps = [[float('inf') if x == (graph.vcount() + 1) else x for x in y] for y in sps]

            for sp in sps:  # loop through the shortest path of each node name
                partial_sum = 0
                for sp_length in sp:
                    if sp_length != 0:
                        partial_sum += diameter + 1 - sp_length

                rad.append(round(float(partial_sum / (num_nodes - 1)), 5))

            return rad

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def radiality(graph: Graph, nodes=None, implementation=imps.auto) -> list:
        """
        Computes the radiality for a single node, a list of nodes or for all nodes in the Graph. The radiality of a node
        (v) is calculated by computing the shortest path between the node v and all other nodes in the graph. The value
        of each path is then subtracted by the value of the diameter + 1 and the resulting values are summated and
        weighted over the total number of nodes -1. Finally, the obtained value is divided for the number of nodes -1
        (n-1).
        **WARNING:** Radiality works well when a graph is connected. If the node is disconnected, the radiality is
        always *-inf*. If the graph is  made of at least two components, we highly recommend using the *radiality_reach*
        method we implemented here
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the degree is returned for all node names.if None (default), the degree is computed for the whole graph.
        :param imps implementation: the way you prefer to compute the shortest path for the whole graph. choices are:
        * **`igraph`**: uses the Dijsktra's algorithm implemented from igraph
        * **`parallel_CPU`**: uses a parallel CPU implementation of the Floyd Warshall algorithm using numba
        * **`parallel_GPU`**: uses a parallel GPU implementation of the Floyd Warshall algorithm using numba
        **CAUTION:**(requires NVIDIA graphics compatible with CUDA)
        :return: a list of floats, the length being the number of input nodes. Each float represent the closeness
        of the input node
        """
        return LocalTopology.__radiality_inner__(graph=graph, nodes=nodes, implementation=implementation)

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def radiality_reach(graph: Graph, nodes=None, implementation=imps.auto) -> list:
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
        :param Enum.implementation implementation: the way you prefer to compute the shortest path for the whole graph. choices are:
        * *'igraph'*: uses the Dijsktra's algorithm implemented from igraph
        * *'parallel_CPU'*: uses a parallel CPU implementation of the Floyd-Warshall algorithm using numba
        * *'parallel_GPU'*: uses a parallel GPU implementation of the Floyd-Warshall algorithm using numba
        **(requires NVIDIA graphics compatible with CUDA)**
        :return: a list of floats, the length being the number of input nodes. Each float represent the closeness
        of the input node
        """

        comps = graph.components()  # define each case
        if len(comps) == 1:
            return LocalTopology.radiality(graph=graph, nodes=nodes, implementation=implementation)

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
                        rad = LocalTopology.__radiality_inner__(graph=subg, nodes=nodes,implementation=implementation.auto)

                        # rebalance radiality by weighting it over the total number of nodes
                        for i, elem in enumerate(rad):
                            rad[i] = elem * (part_nodes / tot_nodes)

                    for i, ind in enumerate(c):
                        res[ind] = rad[i]

                return res

            else:

                res = [None] * len(nodes)

                inds = ut(graph=graph).get_node_indices(nodes)

                for c in comps:
                    if any(x in c for x in inds):
                        node_names = list(set(nodes) & set(graph.vs(c)["name"]))
                        subg = graph.induced_subgraph(vertices=c)
                        part_nodes = subg.vcount()
                        rad = LocalTopology.__radiality_inner__(graph=subg, nodes=node_names,
                                                              implementation=implementation)
                        for i, elem in enumerate(rad):
                            rad[i] = elem * (part_nodes / tot_nodes)

                        for i, elem in enumerate(node_names):
                            orig_index = nodes.index(elem)
                            res[orig_index] = rad[i]
                return res

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
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
            inds = ut(graph=graph).get_node_indices(nodes)
            evcent_values = list(graph.evcent(directed=False, scale=scaled)[i] for i in inds)
            return evcent_values

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
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
            nodes = ut(graph).get_node_indices(nodes)

        return graph.pagerank(vertices=nodes, damping=damping, directed=False, weights=weights, implementation="arpack")

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    #todo check if i can see the environment variables so I don't have to recall cuda.is_available() every time
    def shortest_path_pyntacle(graph: Graph, nodes=None, mode=GraphType.undirect_unweighted,
                               implementation=imps.cpu) -> np.ndarray:
        """
        We implement here a few ways to determine the shortest paths in a graph for a single node, a group of nodes or
        all nodes in a graph. The shortest path search is performed using the Floyd-Warhsall algorithm and the numba
        library for HPC computing in order to parallelize the search as quickly as possible. Currently we support the
        use
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the shortest path between the input nodes and all other nodes in the graph is returned for all node names.
        If None (default), the degree is computed for the whole graph.
        :param GraphType mode: an enumerator containing the type of node to be implemented. Choices are:
        * **`graph_type.undirect_unweighted`**: perform shortest path search for an unweighted and undirect graph
        (default).
        * **`graph_type.undirect_weighted`**: shortest path for a weighted undirect network. In this case, the reserved
        attribute "__weight" at the edge level must be present and filled. **TO BE IMPLEMENTED**
        * **`graph_type_direct_unweighted`**: unweighted direct graph **TO BE IMPLEMENTED**
        * **`graph type_direct_weighted`**: weighted directed graph. In this case, the reserved attribute "__weight"
        at the edge level must be present and filled. **TO BE IMPLEMENTED**
        :param implementation :an enumerator containing the type of parallelization that will be used. Choices are:
        * **`implementation.cpu`**: parallelize the SP search using the maximum number of threads available on the CPU
        * **`implementation.gpu`**: parallelize the SP search using a GPU implementation and nVidia Graphics.
        **TO BE IMPLEMENTED**
        **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        * **`implementation.auto`**: performs the shortest path using criteria defined by us, according to the machine
        specifications and the graph topology.
        :return: a numpy array storing the shortest path matrix for a single node, a list of nodes or all nodes in the
        graph
        """

        if implementation == imps.auto:
            raise ValueError("Implementation \"auto\" not available here, you must have already decided your implementation"
                             "before caling this method")

        #todo mauro this should be handle outside this
        if implementation == imps.gpu:

            if not cuda.is_available():
                implementation = imps.cpu

            else:
                if sys.modules.get("algorithms.shortestpath_GPU", "Not imported") == "Not imported":
                    from algorithms.shortestpath_GPU import SPGpu

        if mode == GraphType.undirect_unweighted:

            if implementation == imps.igraph:
                sys.stdout.write("using igraph implementation instead of our implementations\n")
                sps = LocalTopology.shortest_path_igraph(graph=graph, nodes=nodes)
                sps = [[graph.vcount()+1 if isinf(x) else x for x in y] for y in sps]
                sps = np.array(sps)
                return sps

            else:
                if nodes is None:

                    adjmat = np.array(list(graph.get_adjacency()), dtype=int)
                    adjmat[adjmat == 0] = graph.vcount() + 1  # set zero values to the max possible path length + 1
                    np.fill_diagonal(adjmat, 0)  # set diagonal values to 0 (no distance from itself)

                    if implementation == implementation.cpu:
                        sps = LocalTopology.__shortest_path_CPU__(adjmat=adjmat)
                        return sps

                    elif implementation == implementation.gpu:
                        if nodes is None:
                            nodes = list(range(0, graph.vcount()))

                        else:
                            nodes = ut(graph=graph).get_node_indices(nodes)

                        # create the result vector filled with 'inf' (the total number of nodes + 1)
                        result = np.full_like(adjmat, graph.vcount()+1, dtype=np.uint16)
                        SPGpu.shortest_path_GPU(adjmat, nodes, result) #todo is there any case in which the shortest path GPU is not imported?

                        np.fill_diagonal(result, 0) #fill the diagonal of the result object with zeros

                        if len(nodes) < graph.vcount():
                            result = result[nodes, :]

                        #LocalTopology.__shortest_path_GPU__(adjmat, nodes, result)
                        return result

                    else:
                        sys.stdout.write(
                            "Implementation {} not available at the time, please come back soon "
                            "for the modifed version".format(implementation.name))
                        sps = LocalTopology.__shortest_path_CPU__(adjmat=adjmat, nodes=nodes)
                        return sps

                else:
                    sys.stdout.write("Not yet available for a subset of nodes in the graph\n")
                    sys.exit(0)

        else:
            sys.stdout.write("Shortest path for {} not yet implemented, come back soon!\n".format(mode.name))
            sys.exit(0)

    @staticmethod
    @jit(nopython=True, parallel=True, cache=True)
    def __shortest_path_CPU__(adjmat, nodes=None) -> np.ndarray:
        """
        Calculate the shortest paths of a graph for aa single nodes, a set of nodes or all nodes in the graph using
        'Floyd-Warshall Implementation <https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm>'_. The forumla
        is implemented using the numba library and allows for parallelization using CPU cores.
        :param np.ndarray adjmat: a numpy.ndarray containing the adjacency matrix of a graph. Disconnected nodes in the
        matrix are represented as the total number of nodes in the graph + 1, while the diagonal must contain zeroes.
        Default is True (a numpy array is returned)
        :return: a numpy array
        """
        # todo Tom: gestire nodi singoli e gruppi di nodi
        # todo Tom controlla i prange

        v = adjmat.shape[0]
        if nodes is None:
            for k in range(0, v):
                for i in prange(v):
                    for j in range(0, v):
                        if adjmat[i, j] <= 2:
                            continue
                        if adjmat[i, j] > adjmat[i, k] + adjmat[k, j]:
                            adjmat[i, j] = adjmat[i, k] + adjmat[k, j]
        else:
            for k in range(0, v):
                for i in nodes:
                    for j in range(0, v):
                        if adjmat[i, j] <= 2:
                            continue
                        if adjmat[i, j] > adjmat[i, k] + adjmat[k, j]:
                            adjmat[i, j] = adjmat[i, k] + adjmat[k, j]

        return adjmat

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def shortest_path_igraph(graph: Graph, nodes=None) -> list:
        """
        Computes the shortest path for a single node, a list of nodes or for all nodes in the Graph using the Dijkstra's
        implementation of the igraph Package (works on a single CPU core). The shortest path is the minimum distance
        from the input node to every other node in the graph. The distance between two disconnected nodes is represented
        as *'inf'* (a *math.inf* object).
        :param graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the shortest path between the input nodes and all other nodes in the graph is returned for all node names.
        If None (default), the degree is computed for the whole graph.
        :param numpy: a **Boolean** that allows to output a list of lists or a 'numpy array object
        <https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.array.html>'_. Default is **False**,
        while it's **True** for the other shortest path implementations.
        :return: a list of lists, the length being the number of input nodes. Each list contains a series of integers
        representing the distance from the input node(s) to every other node in the graph.
        """

        if nodes is None:
            sp = graph.shortest_paths()

        else:
            sp = graph.shortest_paths(source=nodes)
        return sp

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def average_shortest_path_length(graph: Graph, nodes=None, implementation=imps.auto) -> list:
        """
        Computes the average of connected shortest path for each a single node, a lists of nodes or all nodes in the
        'igraph.Graph' object if 'None' (default).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the shortest path between the input nodes and all other nodes in the graph is returned for all node names.
        If None (default), the degree is computed for the whole graph.
        :param implementation :an enumerator containing the type of parallelization that will be used. Choices are:
        * **`implementation.cpu`**: parallelize the SP search using the maximum number of threads available on the CPU
        * **`implementation.gpu`**: parallelize the SP search using a GPU implementation and nVidia Graphics.
        **TO BE IMPLEMENTED**
        **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        * **`implementation.auto`**: performs the shortest path using criteria defined by us, according to the machine
        specifications and the graph topology.
        :return: a list of floats with the average shortest path lists of each connected nodes. If a node is an isolate, 'nan' will be returned.
        """
        if implementation == imps.auto:
            implementation  = implementation_seeker()

        if implementation == imps.igraph:
            sps = LocalTopology.shortest_path_igraph(graph=graph, nodes=nodes)
            avg_sps = []
            for elem in sps:
                elem = [x for x in elem if not(isinf(x)) and x > 0]
                if len(elem) > 0:
                    avg_sps.append(sum(elem) / float(len(elem)))
                else:
                    avg_sps.append(float("nan"))
        else: #np array
            sps = LocalTopology.shortest_path_pyntacle(graph=graph, nodes=nodes)
            sps[sps == 0] = np.nan
            var = sps[sps > graph.vcount()] == np.nan
            avg_sps = np.nanmean(var, axis=0)
            avg_sps = avg_sps.tolist()

        return avg_sps

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def median_shortest_path_length(graph: Graph, nodes=None, implementation=imps.auto) -> list:
        """
        Computes the median among connected shortest path for each a single node, a lists of nodes or all nodes in the
        'igraph.Graph' object if 'None' (default).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: if a node name, returns the degree of the input node. If a list of node names,
        the shortest path between the input nodes and all other nodes in the graph is returned for all node names.
        If None (default), the degree is computed for the whole graph.
        :param implementation :an enumerator containing the type of parallelization that will be used. Choices are:
        * **`implementation.cpu`**: parallelize the SP search using the maximum number of threads available on the CPU
        * **`implementation.gpu`**: parallelize the SP search using a GPU implementation and nVidia Graphics.
        **TO BE IMPLEMENTED**
        **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        * **`implementation.auto`**: performs the shortest path using criteria defined by us, according to the machine
        specifications and the graph topology.
        :return: a list of floats with the median shortest path(s) of each connected nodes. If a node is an isolate, 'nan' will be returned.
        """

        if implementation == imps.auto:
            implementation = implementation_seeker()

        if implementation == imps.igraph:
            sps = LocalTopology.shortest_path_igraph(graph=graph, nodes=nodes)
            avg_sps = []
            for elem in sps:
                elem = [x for x in elem if not (isinf(x)) and x > 0] #remove disconnected nodes and diagonal
                if len(elem) > 0:
                    avg_sps.append(statistics.median(elem))
                else:
                    avg_sps.append(float("nan"))

        else:  # np array
            sps = LocalTopology.shortest_path_pyntacle(graph=graph, nodes=nodes)
            sps[sps == 0] = np.nan
            var = sps[sps > graph.vcount()] == np.nan
            avg_sps = np.nanmedian(var, axis=0)
            avg_sps = avg_sps.tolist()

        return avg_sps

# todo missing stuff:
# todo shortest path cpu: single nodes or group of nodes
# todo shortest path gpu: single nodes or group of nodes
# todo all the other graphs
# todo automatic implementation becomes global
# todo missing methods:
# todo Mauro: specify numpy maximum allocation in RAM (in "Requirements")
# todo Mauro. specify number of cores (COU) for numba