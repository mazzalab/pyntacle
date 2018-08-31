"""
Several implementation to compute shortest paths of a graph
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.1.0"
__maintainer__ = "Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = ["Release", "Stable"]
__date__ = "31/08/2018"
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


import sys, math
from config import threadsperblock
import statistics
import numpy as np
from igraph import Graph
from math import isinf, ceil
from numba import jit, prange, cuda
from psutil import virtual_memory
from tools.enums import CmodeEnum
from tools.graph_utils import GraphUtils as gUtil
from tools.misc.graph_routines import check_graph_consistency, vertex_doctor
from exceptions.wrong_argument_error import WrongArgumentError


class ShortestPath:

    # @profile
    # todo check if i can see the environment variables so I don't have to recall cuda.is_available() every time
    @staticmethod
    def get_shortestpaths(graph, nodes, cmode: CmodeEnum) -> np.ndarray:
        """
        Compute the *shortest paths* starting from a node or of a list of nodes of an undirected graph using the
        implementation modes specified in the input parameter *cmode*
        :param graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :param cmode: an enumerator ranging from:
        * **`cmode.igraph`**: shortest paths computed by iGraph
        * **`cmode.cpu`**: Dijkstra algorithm implemented for multicore CPU
        * **`cmode.gpu`**: Dijkstra algorithm implemented for GPU-enabled graphics cards
        **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        :return: a np.ndarray, the first size being the number of input nodes. Each row contains a series of
        integer values representing the distance from any input node to every other node in the graph.
        The order of the node list in input is preserved in the np.ndarray.
        """

        if cmode == CmodeEnum.igraph:
            sps = ShortestPath.shortest_path_length_igraph(graph=graph, nodes=nodes)
            sps = [[graph.vcount() + 1 if isinf(x) else x for x in y] for y in sps]
            sps = np.array(sps)
            return sps
        elif cmode == CmodeEnum.cpu or cmode == CmodeEnum.gpu:
            if virtual_memory().free < (graph.vcount() ** 2) * 2:  # the rightmost "2" is int16/8
                sys.stdout.write("WARNING: Memory seems to be low; loading the graph given as input could fail.")

            graph_size = graph.vcount() + 1
            # np.set_printoptions(linewidth=graph_size * 10)
            adjmat = np.array(graph.get_adjacency().data, dtype=np.uint16, copy=True)
            adjmat[adjmat == 0] = np.uint16(graph_size)
            np.fill_diagonal(adjmat, 0)

            if cmode == CmodeEnum.cpu:
                if nodes is None:
                    sps = ShortestPath.shortest_path_length_cpu(adjmat=adjmat)
                else:
                    sps = ShortestPath.shortest_path_length_cpu(adjmat=adjmat)
                    nodes = gUtil(graph=graph).get_node_indices(node_names=nodes)
                    sps = sps[nodes, :]
                return sps

            elif cmode == CmodeEnum.gpu:
                if cmode == CmodeEnum.gpu and cuda.current_context().get_memory_info().free < (graph.vcount() ** 2) * 2:
                    sys.stdout.write(
                        "WARNING: GPU Memory seems to be low; loading the graph given as input could fail.")

                if nodes is None:
                    nodes = list(range(0, graph.vcount()))
                else:
                    nodes = gUtil(graph=graph).get_node_indices(nodes)

                if "shortest_path_gpu" not in sys.modules:
                    from algorithms.shortestpath_gpu import shortest_path_gpu

                    sps = np.array(adjmat, copy=True, dtype=np.uint16)
                    blockspergrid = ceil(adjmat.shape[0] / threadsperblock)
                    shortest_path_gpu[blockspergrid, threadsperblock](sps)

                    if len(nodes) < graph.vcount():
                        sps = sps[nodes, :]

                    return sps
        else:
            raise ValueError("The specified 'computing mode' is invalid. Choose from: {}".format(list(CmodeEnum)))

    @staticmethod
    def get_shortestpath_count(graph, nodes, cmode: CmodeEnum) -> np.ndarray:
        """
        Compute the *shortest paths* starting from a node or of a list of nodes of an undirected graph using the
        implementation modes specified in the input parameter *cmode*
        :param graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :param cmode: an enumerator ranging from:
        * **`cmode.igraph`**: shortest paths computed by iGraph
        * **`cmode.cpu`**: Dijkstra algorithm implemented for multicore CPU
        * **`cmode.gpu`**: Dijkstra algorithm implemented for GPU-enabled graphics cards
        **CAUTION**: this will not work if the GPU is not present or CUDA compatible.
        :return: a np.ndarray, the first size being the number of input nodes. Each row contains a series of
        integer values representing the distance from any input node to every other node in the graph.
        The order of the node list in input is preserved in the np.ndarray.
        """

        if cmode == CmodeEnum.igraph:
            count_all = ShortestPath.shortest_path_count_igraph(graph, nodes)
            count_all = np.array(count_all)
            return count_all
        else:
            if virtual_memory().free < (graph.vcount() ** 2) * 2:  # the rightmost "2" is int16/8
                sys.stdout.write("WARNING: Memory seems to be low; loading the graph given as input could fail.")

            adj_mat = np.array(graph.get_adjacency().data, dtype=np.uint16, copy=True)
            adj_mat[adj_mat == 0] = adj_mat.shape[0]

            if cmode == CmodeEnum.cpu:
                count_all = ShortestPath.shortest_path_count_cpu(adj_mat)

                if nodes:
                    nodes_idx = gUtil(graph=graph).get_node_indices(node_names=nodes)
                    count_all = count_all[nodes_idx, :]

                return count_all
            elif cmode == CmodeEnum.gpu:
                if cuda.current_context().get_memory_info().free < (graph.vcount() ** 2) * 2:
                    sys.stdout.write(
                        "WARNING: GPU Memory seems to be low; loading the graph given as input could fail.")

                if nodes is None:
                    nodes = list(range(0, graph.vcount()))
                else:
                    nodes = gUtil(graph=graph).get_node_indices(nodes)

                if "shortest_path_count_gpu" not in sys.modules:
                    from algorithms.shortestpath_gpu import shortest_path_count_gpu

                count_all = np.copy(adj_mat)
                tpb = threadsperblock
                blockspergrid = math.ceil(graph.vcount() / tpb)
                shortest_path_count_gpu[blockspergrid, tpb](adj_mat, count_all)

                if len(nodes) < graph.vcount():
                    count_all = count_all[nodes, :]

                return count_all
            else:
                raise ValueError("The specified 'computing mode' is invalid. Choose from: {}".format(list(CmodeEnum)))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def shortest_path_length_igraph(graph: Graph, nodes=None) -> list:
        """
        Compute the *shortest paths* lengths between any pairs of nodes of an undirected graph, using the
        Dijkstra's algorithm. The shortest path is defined as the minimum distance from an input node to every other
        node in a graph. The distance between two disconnected nodes is infinite.
        :param graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: a list of lists, the first size being the number of input nodes. Each list contains a series of
        integer values representing the distance from any input node to every other node in the graph.
        The order of the node list in input is preserved.
        """

        return graph.shortest_paths(source=nodes) if nodes else graph.shortest_paths()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def shortest_path_count_igraph(graph: Graph, nodes=None) -> np.ndarray:
        """
        Compute the *shortest paths* from any pairs of nodes of an undirected graph using the
        Dijkstra's algorithm and returns the path lengths in the upper triangular part and the geodesics counts in the
        lower triangular part.
        :param graph: an igraph.Graph object. The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for. It can be an individual node or a list of nodes. When *None*
        (default), the index is computed for all nodes of the graph.
        :return: A nxn numpy array, where *n* is the number of *nodes*. The path lengths are in the upper triangular
        part of the array and the geodesics counts in the lower triangular part. The order of the node list in input is
        preserved.
        """

        if nodes:
            loop_nodes = nodes
        else:
            loop_nodes = graph.vs()
        loop_nodes_size = len(loop_nodes)

        spaths = np.zeros(shape=(loop_nodes_size, loop_nodes_size), dtype=np.int16)

        for node in loop_nodes:
            temp_row = np.zeros(shape=loop_nodes_size)
            temp_col = np.zeros(shape=loop_nodes_size)

            sp = graph.get_all_shortest_paths(v=node)
            for s in sp:
                if len(s) > 1:
                    last = s[-1]
                    temp_row[last] += 1
                    temp_col[last] = len(s) - 1
                else:
                    row_col_index = s[0]

            spaths[row_col_index, row_col_index:loop_nodes_size] = temp_row[row_col_index:loop_nodes_size]
            spaths[row_col_index:loop_nodes_size, row_col_index] = temp_col[row_col_index:loop_nodes_size]

        return spaths

    @staticmethod
    @jit(nopython=True, parallel=True)
    def shortest_path_length_cpu(adjmat) -> np.ndarray:
        """
        Calculate the shortest path lengths of a graph for a single node, a set of nodes or all nodes in the graph using
        'Floyd-Warshall Implementation <https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm>'_. The forumla
        is implemented using Numba for just-in-time compilation and run on multiple CPU processors.
        :param np.ndarray adjmat: a numpy.ndarray containing the adjacency matrix of a graph. Disconnected nodes in the
        matrix are represented as the total number of nodes in the graph + 1, while the diagonal must contain zeroes.
        :return: a numpy array of shortest path lengths
        """

        v = adjmat.shape[0]
        for k in range(0, v):
            for i in prange(v):
                for j in range(0, v):
                    if adjmat[i, j] <= 2:
                        continue
                    if adjmat[i, j] > adjmat[i, k] + adjmat[k, j]:
                        adjmat[i, j] = adjmat[i, k] + adjmat[k, j]

        return adjmat

    @staticmethod
    @jit(nopython=True, parallel=True)
    def shortest_path_count_cpu(adjmat) -> np.ndarray:
        """
        Compute the *shortest paths* from any pairs of nodes of an undirected graph using the
        Dijkstra's algorithm. The method is implemented using Numba for just-in-time compilation and run
        on multiple CPU processors.
        :param np.ndarray adjmat: the adjacency matrix of a graph. Absence of links is represented with a number
        that equals the total number of nodes in the graph + 1.
        :return: A nxn numpy array, where *n* is the number of *nodes*. The path lengths are in the upper triangular
        part of the array and the geodesics counts in the lower triangular part. The order of the node list in input is
        preserved.
        """

        v = adjmat.shape[0]

        count = np.copy(adjmat)
        for i in prange(v):
            for j in prange(v):
                if count[i, j] == v:
                    count[i, j] = 0

        dist = np.copy(adjmat)
        for k in range(0, v):
            for i in prange(v):
                for j in range(0, v):
                    if k != j and k != i and i != j:
                        if dist[i, j] == dist[i, k] + dist[k, j]:
                            count[i, j] += count[i, k] * count[k, j]
                        elif dist[i, j] > dist[i, k] + dist[k, j]:
                            dist[i, j] = dist[i, k] + dist[k, j]
                            count[i, j] = count[i, k] * count[k, j]

        dist_count = np.copy(count)
        for i in prange(0, v):
            for j in prange(i+1, v):
                dist_count[j, i] = dist[i, j]

        return dist_count

    @staticmethod
    @jit(nopython=True, parallel=True)
    def subtract_count_dist_matrix(count_all: np.ndarray, count_nogroup: np.ndarray) -> np.ndarray:
        if count_all.shape[0] == count_all.shape[1] == count_nogroup.shape[0] == count_nogroup.shape[1]:
            v = count_all.shape[0]
            res = np.copy(count_all)

            for i in prange(v):
                for j in prange(i, v):
                    if count_all[j, i] == count_nogroup[j, i]:
                        res[i, j] = count_all[i, j] - count_nogroup[i, j]

            return res
        else:
            raise WrongArgumentError("Parameter error", "The function parameters do not have the same shape")

    @staticmethod
    @check_graph_consistency
    def average_global_shortest_path_length(graph: Graph, cmode=CmodeEnum.igraph) -> float:
        """
        Compute the global *average shortest path length* as defined in https://en.wikipedia.org/wiki/Average_path_length
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual. If the graph as more than one component, the average
        shortest path length is the sum of each component's shortest path length (both directions are counted) divided
        by the total number of components. Isolated nodes counts as single components, but their distance to all other
        nodes in the graph is 0.
        :param cmode: the implementation that will be used to compute the average shortest path length value.
        Choices are:
        **igraph:* uses the igraph implementation
        **parallel_CPU:* uses the Floyd-Warshall algorithm implemented in Numba for multicore processors
        **parallel_GPU:* uses the Floyd-Warshall algorithm implemented in Numba for GPU devices (requires
        CUDA-compatible nVIDIA graphic cards)
        :return: a positive float value representing the average shortest path length for the graph
        """

        if not isinstance(cmode, CmodeEnum):
            raise KeyError("'cmode' not valid, must be one of the following: {}".format(list(CmodeEnum)))
        elif cmode == CmodeEnum.igraph:
            avg_sp = Graph.average_path_length(graph, directed=False, unconn=False)
            return round(avg_sp, 5)
        else:
            if len(graph.components()) == 1:
                sp = ShortestPath.get_shortestpaths(graph=graph, nodes=None, cmode=cmode)
                sp[sp == graph.vcount() + 1] = 0

                all_possible_edges = graph.vcount() * (graph.vcount() - 1)
                agspl = float(np.sum(np.divide(sp, all_possible_edges)))
                return round(agspl, 5)
            else:
                comps = graph.components()
                sum = 0
                for elem in comps:
                    subg = graph.induced_subgraph(elem)
                    if subg.ecount() > 0:
                        sp = ShortestPath.get_shortestpaths(graph=subg, nodes=None, cmode=cmode)
                        sp[sp == subg.vcount() + 1] = 0
                        sum += np.sum(sp)
                return round(sum / len(comps), 5)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def average_shortest_path_lengths(graph: Graph, nodes=None, cmode=CmodeEnum.igraph) -> list:
        """
        Compute the average shortest paths issuing from each node in input or of all nodes in the graph if None provided.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: if a node name, returns the shortest paths of the input node. If a list of node names is provided,
        the shortest paths between the input nodes and all other nodes in the graph are returned for all node names.
        If None (default), the degree is computed for all nodes in the graph.
        :param cmode: the implementation that will be used to compute the average shortest path length value.
        Choices are:
        **igraph:* uses the igraph implementation
        **parallel_CPU:* uses the Floyd-Warshall algorithm implemented in Numba for multicore processors
        **parallel_GPU:* uses the Floyd-Warshall algorithm implemented in Numba for GPU devices (requires
        CUDA-compatible nVIDIA graphic cards)
        :return: a list of average shortest path lengths, one for each node provided in input
        """

        if cmode == CmodeEnum.igraph:
            sps = ShortestPath.shortest_path_length_igraph(graph=graph, nodes=nodes)
            avg_sps = []
            for elem in sps:
                elem = [x for x in elem if not (isinf(x)) and x > 0]
                if len(elem) > 0:
                    avg_sps.append(sum(elem) / float(len(elem)))
                else:
                    avg_sps.append(float("nan"))
        else:
            sps = ShortestPath.get_shortestpaths(graph=graph, nodes=nodes, cmode=cmode)
            sps = sps.astype(np.float)
            sps[sps > graph.vcount()] = np.nan
            sps[sps == 0] = np.nan
            avg_sps = np.nanmean(sps, axis=1)  # TODO: check axis = 0 or 1
            avg_sps = avg_sps.tolist()

        return avg_sps

    @staticmethod
    @check_graph_consistency
    def median_global_shortest_path_length(graph: Graph) -> float:
        """
        Compute the median shortest path length across all shortest paths in the graph. This is useful if one needs
        to estimate the trend of the shortest path distances.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: the median shortest path length across all shortest path distances
        """
        sps = ShortestPath.shortest_path_length_igraph(graph=graph)  # TODO: Include other implementations
        sps = np.array(sps)

        return float(np.median(sps[sps != 0]))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def median_shortest_path_lengths(graph: Graph, nodes=None, cmode=CmodeEnum.igraph) -> list:
        """
        Compute the median among the shortest paths for each a single node, a lists of nodes or all nodes in the graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: if a node name, returns the median shortest paths of the input nodes. If a list of node names is
        provided, the shortest path between the input nodes and all other nodes in the graph is returned for all nodes.
        If None (default), the median shortest paths are computed for the whole graph.
        :param cmode: the implementation that will be used to compute the average shortest path length value.
        Choices are:
        **igraph:* uses the igraph implementation
        **parallel_CPU:* uses the Floyd-Warshall algorithm implemented in Numba for multicore processors
        **parallel_GPU:* uses the Floyd-Warshall algorithm implemented in Numba for GPU devices (requires
        CUDA-compatible nVIDIA graphic cards)
        :return: a list of float values corresponding to the median shortest paths of each input node.
        If a node is an isolate, 'nan' will be returned.
        """

        if cmode == CmodeEnum.igraph:
            sps = ShortestPath.shortest_path_length_igraph(graph=graph, nodes=nodes)
            median_sps = []
            for elem in sps:
                elem = [x for x in elem if not (isinf(x)) and x > 0]  # remove disconnected nodes and diagonal
                if len(elem) > 0:
                    median_sps.append(statistics.median(elem))
                else:
                    median_sps.append(float("nan"))

        else:
            sps = ShortestPath.get_shortestpaths(graph=graph, nodes=nodes, cmode=cmode)
            sps = sps.astype(np.float)

            sps[sps > graph.vcount()] = np.nan
            sps[sps == 0] = np.nan
            median_sps = np.nanmedian(sps, axis=1)  # TODO: check axis = 0 or 1
            median_sps = median_sps.tolist()

        return median_sps
