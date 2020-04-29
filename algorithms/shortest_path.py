__author__ = ["Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = "Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = ["Release", "Stable"]
__date__ = u"26/11/2018"
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
from internal.graph_routines import check_graph_consistency, vertex_doctor
from exceptions.wrong_argument_error import WrongArgumentError


class ShortestPath:
    r"""
    This class contains a series of operations revolved around the shortest paths computation of a network, from their
    computation to their processing to obtain relevant statistics by modelling the shortest path distribution for each
    node
    """

    @staticmethod
    @jit(nopython=True, parallel=True)
    def __chunks(l: list, n: int):
        # chunks = [l[x:x + 100] for x in range(0, len(l), n)]
        for i in range(0, len(l), n):
            yield l[i:i + n]

    # @profile #uncomment to time the shortest path search when changes are made
    @staticmethod
    def get_shortestpaths(graph: Graph, nodes: int or list or None =None, cmode: CmodeEnum = CmodeEnum.igraph) -> np.ndarray:
        r"""
        Returns the *shortest paths*, the minimum least distance between a node :math:`i` and any node :math:`j` of the
        input graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes  in the graph. When :py:class:`None`, it returns the shortest paths for all nodes in the graph, sorted by index. Otherwise, a single node ``name`` or a list of node ``name`` s can be passed.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`.

        :return numpy.ndarray: a matrix stored in a numpy array, the number of rows corresponding to the input nodes, while the number of columns is the size of the graph. Each row contains a series of integer values representing the distance from any input node to every other node in the input graph. The rows are sorted by vertex ``index`` if ``nodes`` is :py:class:`None`, or in the same order in which they are given otherwise. :warning: disconnected nodes  exhibit a distance greater than the size of the graph

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        :raise: ValueError: if ``cmode`` is not one of ther valid :class:`~pyntacle.tools.enums.GroupCentralityEnum`
        """

        if cmode == CmodeEnum.igraph:
            sps = ShortestPath.shortest_path_length_igraph(graph=graph, nodes=nodes)
            sps = [[graph.vcount() + 1 if isinf(x) else x for x in y] for y in sps]
            sps = np.array(sps) #convert to a numpy array
            return sps

        elif cmode == CmodeEnum.cpu or cmode == CmodeEnum.gpu:
            if virtual_memory().free < (graph.vcount() ** 2) * 2:  # the rightmost "2" is int16/8
                sys.stdout.write(u"WARNING: Memory seems to be low; loading the graph given as input could fail.\n")

            graph_size = graph.vcount() + 1
            # np.set_printoptions(linewidth=graph_size * 10)
            adjmat = np.array(graph.get_adjacency().data, dtype=np.uint16, copy=True)
            adjmat[adjmat == 0] = np.uint16(graph_size) #replace infinite distances with vcount +1
            np.fill_diagonal(adjmat, 0) ##replace the diagonal with 0s

            if cmode == CmodeEnum.cpu:
                if nodes is None:
                    sps = ShortestPath.shortest_path_length_cpu(adjmat=adjmat)
                else:
                    sps = ShortestPath.shortest_path_length_cpu(adjmat=adjmat)
                    nodes = gUtil(graph=graph).get_node_indices(nodes=nodes)
                    sps = sps[nodes, :]
                return sps

            elif cmode == CmodeEnum.gpu:
                if cmode == CmodeEnum.gpu and cuda.current_context().get_memory_info().free < (graph.vcount() ** 2) * 2:
                    sys.stdout.write(
                        u"WARNING: GPU Memory seems to be low; loading the graph given as input could fail.\n")

                if nodes is None:
                    nodes = list(range(0, graph.vcount()))
                else:
                    nodes = gUtil(graph=graph).get_node_indices(nodes)

                if "shortest_path_gpu" not in sys.modules:
                    from algorithms.shortest_path_gpu import shortest_path_gpu

                N = adjmat.shape[0]
                threadsperblock = (32, 32)
                blockspergrid_x = math.ceil(N / threadsperblock[0])
                blockspergrid_y = math.ceil(N / threadsperblock[1])
                blockspergrid = (blockspergrid_x, blockspergrid_y)

                sps = np.array(adjmat, copy=True, dtype=np.uint16)
                # copy sps from host to device
                d_sps = cuda.to_device(sps)

                for k in range(0, N):
                    shortest_path_gpu[blockspergrid, threadsperblock](d_sps, k, N)

                # copy sps back from device to host
                d_sps.copy_to_host(sps)

                if len(nodes) < graph.vcount():
                    sps = sps[nodes, :]

                return sps

    @staticmethod
    def get_shortestpath_count(graph: Graph, nodes: str or list or None, cmode: CmodeEnum) -> np.ndarray:
        r"""
        Returns the number of shortest paths (*shortest path counts*) for a node, a list of nodes or all nodes in the
        graph in a numpy array of positive integers.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the counts of shortest paths. When :py:class:`None`, the counts are computed for all nodes in the graph. Otherwise, a single node (identified using the ``name`` attribute) or a list of node names can be passed.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths counts. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search wrapped in :func:`~pyntacle.algorithms.shortest_path.ShortestPath.shortest_path_length_igraph`

        :return numpy.ndarray: a matrix stored in a :py:class:`numpy.ndarray`, the number of rows corresponding to the length of the input nodes and the number of columns being the size of the graph. The nodes are sorted by index if ``nodes`` is :py:class:`None`, or they are in the same order in which they're presented otherwise.

        :raise: ValueError: if ``cmode`` is not one of the valid :class:`~pyntacle.tools.enums.GroupCentralityEnum`
        """

        if cmode == CmodeEnum.igraph:
            count_all = ShortestPath.shortest_path_count_igraph(graph, nodes)
            count_all = np.array(count_all)
            return count_all
        else:
            if virtual_memory().free < (graph.vcount() ** 2) * 2:  # the rightmost "2" is int16/8
                sys.stdout.write(u"WARNING: Memory seems to be low; loading the graph given as input could fail.")

            adj_mat = np.array(graph.get_adjacency().data, dtype=np.uint16, copy=True)
            adj_mat[adj_mat == 0] = adj_mat.shape[0]

            if cmode == CmodeEnum.cpu:
                count_all = ShortestPath.shortest_path_count_cpu(adj_mat)

                if nodes:
                    nodes_idx = gUtil(graph=graph).get_node_indices(nodes=nodes)
                    count_all = count_all[nodes_idx, :]

                return count_all
            elif cmode == CmodeEnum.gpu:
                if cuda.current_context().get_memory_info().free < (graph.vcount() ** 2) * 2:
                    sys.stdout.write(
                        u"WARNING: GPU Memory seems to be low; loading the graph given as input could fail.")

                if nodes is None:
                    nodes = list(range(0, graph.vcount()))
                else:
                    nodes = gUtil(graph=graph).get_node_indices(nodes)

                if "shortest_path_count_gpu" not in sys.modules:
                    from algorithms.shortest_path_gpu import shortest_path_count_gpu

                count_all = np.copy(adj_mat)
                tpb = threadsperblock
                blockspergrid = math.ceil(graph.vcount() / tpb)
                shortest_path_count_gpu[blockspergrid, tpb](adj_mat, count_all)

                if len(nodes) < graph.vcount():
                    count_all = count_all[nodes, :]

                return count_all
            else:
                raise ValueError(u"The specified 'computing mode' is invalid. Choose from: {}".format(list(CmodeEnum)))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def shortest_path_length_igraph(graph: Graph, nodes=None) -> list:
        r"""
        Compute the *shortest paths*  between any pairs of nodes of an undirected graph. The shortest path is
        defined as the minimum distance from an node :math:`i`to every other node :math:`j`in a graph.
        :py:func:`igraph.Graph.shortest_paths` method from igraph, that alternate the Djikstra's algorithm for a handful
        of nodes to a brute-force shortest path implementation for all nodes.

        .. note:: The distance between two disconnected nodes is represented as  infinite (a :py:class:`math.inf` object).

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to compute the centrality index. When :py:class:`None`, it computes the radiality reach for all nodes in the graph. Otherwise, a single node  (identified using the ``name`` attribute) or a list of node names can be passed to compute radiality reach only for the subset of node of interest.

        :return list: a list of lists equals to the size of the input nodes and sorted by node ``index`` if ``nodes`` is :py:class:`None` or in the same order on which vertex name are provided, Each sublist stores positive integers representing the geodesics among nodes, or infinite if the nodes are disconnected.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        """

        return graph.shortest_paths(source=nodes) if nodes else graph.shortest_paths()

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def shortest_path_count_igraph(graph: Graph, nodes=None or str or list) -> np.ndarray:
        r"""
        Compute the *shortest paths* from any pairs of nodes of an undirected graph using the and returns a matrix
        (represented as a numpy array) storing the path lengths in the upper triangular part and the geodesics counts
        in the lower triangular part.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes on which to count the number of shortest paths. When :py:class:`None`, the counts are computed for the whole graph. Otherwise, a single node  (identified using the ``name`` attribute) or a list of node names can be passed to compute radiality reach only for the subset of node of interest.

        :return numpy.ndarray: A :math:`NxN` numpy array, where :math:`N` is the number of vertices in a graph. The path lengths are in the upper triangular part of the array and the geodesics counts in the lower triangular part. The order of the node list in input is preserved if ``nodes`` is not :py:class:`None`.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
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
    def shortest_path_length_cpu(adjmat: np.ndarray) -> np.ndarray:
        r"""
        Calculate the shortest path lengths of a graph for a single node, a set of nodes or all nodes in the graph using
        `Floyd-Warshall Implementation <https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm>`_. The formula
        is implemented using `Numba <http://numba.pydata.org/>`_ for just-in-time (JIT) compilation and run on
        multiple CPU processors.

        :param numpy.ndarray adjmat: a squared :py:class:`numpy.ndarray` of positive integers and equals to the size of the graph, storing the adjacency matrix representation of the graph. Disconnected nodes in the matrix are represented as the total number of nodes in the graph + 1, while the diagonal must contain zeroes.

        :return numpy.ndarray: a numpy array of shortest path lengths :warning: if nodes are disconnected, the distance is not represented as infinite but as the :math:`N + 1`, :math:`N` being the size of the graph.
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
    def shortest_path_count_cpu(adjmat: np.ndarray) -> np.ndarray:
        r"""
        Compute the *shortest paths* from any pairs of nodes of an undirected graph using the
        Dijkstra's algorithm. The method is implemented using `Numba <http://numba.pydata.org/>`_
        for just-in-time compilation and run on multiple CPU processors.

        .. warning:: This method by default forces the search of the shortest paths on all machine cores

        :param numpy.ndarray adjmat: the adjacency matrix of a graph. Absence of links is represented with a number that equals the total number of nodes in the graph + 1.

        :return numpy.ndarray: A :math:`NxN` numpy array, where *n* is the number of *nodes*. The path lengths are in the upper triangular part of the array and the geodesics counts in the lower triangular part. The order of the node list in input is preserved.
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
            raise WrongArgumentError(u"Parameter error", "The function parameters do not have the same shape")

    @staticmethod
    @check_graph_consistency
    def average_global_shortest_path_length(graph: Graph, cmode=CmodeEnum.igraph) -> float:
        r"""
        Compute the global *average shortest path length* as defined in https://en.wikipedia.org/wiki/Average_path_length

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return float: a positive float value representing the average shortest path length for the graph

        :raise KeyError: if ``cmode`` is not one of the valid :class:`~pyntacle.tools.enums.CmodeEnum`
        """

        if not isinstance(cmode, CmodeEnum):
            raise KeyError(u"'cmode' not valid, must be one of the following: {}".format(list(CmodeEnum)))
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
        r"""
        Compute the average shortest paths issuing from each node in input or of all nodes in the graph if None provided.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes. When :py:class:`None`, the counts are computed for the whole graph. Otherwise, a single node  (identified using the ``name`` attribute) or a list of node names can be passed to perform computations for the subset of node(s) of interest.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths counts. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search wrapped in :func:`~pyntacle.algorithms.shortest_path.ShortestPath.shortest_path_length_igraph`

        :return: a list of average shortest path lengths, one for each node provided in input

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
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
            avg_sps = np.nanmean(sps, axis=1)
            avg_sps = avg_sps.tolist()

        return avg_sps

    @staticmethod
    @check_graph_consistency
    def median_global_shortest_path_length(graph: Graph) -> float:
        r"""
        Compute the median shortest path length across all shortest paths of all node in the graph.
        This is useful if one needs to estimate the trend of the shortest path distances.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: the median shortest path length across all shortest path distances
        """
        sps = ShortestPath.shortest_path_length_igraph(graph=graph)
        sps = np.array(sps)

        return float(np.median(sps[sps != 0]))

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def median_shortest_path_lengths(graph: Graph, nodes=None, cmode=CmodeEnum.igraph) -> list:
        r"""
        Compute the median among all the possible shortest paths for a single node, a lists of nodes or all nodes in the graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param None,str,list nodes: The input nodes. When :py:class:`None`, it computes the median shortest path for each node in the graph. Otherwise, a single node  (identified using the ``name`` attribute) or a list of node names can be passed to compute the measure for a subset of node of interest
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.


        :return list: the median shortest path. If the node is an isolate, :py:class:'nan' will be returned. The list is ordered by index if ``nodes`` is :py:class:`None` or the same order in which nodes are given.

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
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
            median_sps = np.nanmedian(sps, axis=1)
            median_sps = median_sps.tolist()

        return median_sps
