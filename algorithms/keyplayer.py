""" Compute Key-Player metrics, as described in Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21.
https://doi.org/10.1007/s10588-006-7084-x"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.3"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "24/04/2018"
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


import numpy as np
from tools.enums import CmodeEnum
from tools.graph_utils import GraphUtils as gu
from algorithms.shortest_path import ShortestPath as sp
from private.graph_routines import check_graph_consistency, vertex_doctor
from private.shortest_path_modifications import ShortestPathModifier
from exceptions.wrong_argument_error import WrongArgumentError

class KeyPlayer:
    """
    Compute the Key-Player values for the importance metrics described in [Ref]_
    [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
    """

    @staticmethod
    @check_graph_consistency
    def F(graph) -> float:
        """
        Calculate the *F* metrics, which is a KPP-Neg measure, as described by the equation 4 in [Ref]_
        Since nodes within a component are mutually reachable, and since components of a graph can be enumerated
        extremely efficiently, the F measure can be computed more economically by rewriting it in terms of the
        sizes (sk) of each component (indexed by k).
        **F = 1* => Maximum fragmentation. All nodes are isolate
        **F = 0* => No fragmentation. The graph is complete
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: The F measure of the graph as a float value ranging from 0.0 to 1.0
        """

        num_nodes = graph.vcount()
        max_edges = num_nodes * (num_nodes - 1)

        if graph.ecount() == 0:
            return 1.0

        elif graph.ecount() == max_edges:
            return 0.0

        else:
            components = graph.components()

            f_num = sum(len(sk) * (len(sk) - 1) for sk in components)

            f_denum = max_edges
            f = 1 - (f_num / f_denum)

            return round(f, 5)

    @staticmethod
    @check_graph_consistency
    def dF(graph, implementation=CmodeEnum.igraph, max_distance=None) -> float:
        """
        Calculate the *dF*, which is a KPP-Neg measure, as described by the equation 9 in [Ref]_.
        DF is a measure of node connectivity and measures how nodes in the graph can be reached.
        The dF value ranges from 0 to 1, where:
        **dF = 1* => Maximum fragmentation. All nodes are isolate
        **dF = 0* => No fragmentation. The graph is complete
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param CmodeEnum.igraph implementation: Computation of the shortest paths is deferred
        to the following implementations:
        *`imps.auto`: the most performing implementation is automatically chosen according to the geometry of graph
        *`imps.igraqh`: (default) use the default shortest path implementation in igraph (run on a single computing core)
        *`imps.pyntacle`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors or NVIDIA-enabled GPU graphic cards. This method returns a matrix (`:type np.ndarray:`) of shortest
        paths. Infinite distances actually equal the total number of vertices plus one.
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :return: The DF measure of the graph as a float value ranging from 0.0 to 1.0
        """

        num_nodes = graph.vcount()
        num_edges = graph.ecount()
        if num_edges == 0:  # TODO: check if this case if possible, given the decorator "check_graph_consistency"
            return 1.0
        elif num_edges == num_nodes * (num_edges - 1):
            return 0.0
        else:
            #  TODO: implementation "auto" should consider graph parameters and use the correct implementation
            #  TODO: and the GPU/MULTICORE one
            if not isinstance(implementation, CmodeEnum):
                raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(CmodeEnum)))
            elif max_distance:
                if not isinstance(max_distance, int):
                    raise TypeError("'max_distance' must be an integer value greater than one")
                elif max_distance < 1:
                    raise ValueError("'max_distance' must be an integer value greater than one")
                elif max_distance > graph.vcount():
                    raise ValueError("'max_distance' must be less or equal than the number of nodes in the graph")

            if implementation == CmodeEnum.igraph:
                return KeyPlayer.__dF_Borgatti(graph=graph, max_distance=max_distance)
            else:
                return KeyPlayer.__dF_pyntacle(graph=graph, max_distance=max_distance, implementation=implementation)

    @staticmethod
    def __dF_Borgatti(graph, max_distance=None) -> float:
        """
        Internal method for calculating the *DF* value of a graph using the igraph implementation of the shortest paths.
        This implements, literally, the equation 9 in Borgatti's paper.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :return: The DF measure of the graph as a float value ranging from 0.0 to 1.0
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)
        shortest_path_lengths = sp.shortest_path_length_igraph(graph=graph)

        if max_distance:
            shortest_path_lengths = ShortestPathModifier.set_list_to_inf(
                shortest_path_lengths, max_distance=max_distance)

        df_num = 0
        for i in range(number_nodes):
            df_num += sum([float(1 / shortest_path_lengths[i][j]) for j in range(i + 1, number_nodes)])

        df_num *= 2
        df = 1 - (df_num / df_denum)

        return round(df, 5)

    @staticmethod
    def __dF_pyntacle(graph, max_distance=None, implementation=CmodeEnum.cpu) -> float:
        """
        Internal method for calculating the *DF* value of a graph using HPC implementations of the shortest paths.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :return: The DF measure of the graph as a float value ranging from 0.0 to 1.0
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)
        shortest_path_lengths = sp.get_shortestpaths(graph=graph, nodes=None, cmode=implementation)

        if max_distance:
            shortest_path_lengths = ShortestPathModifier.set_nparray_to_inf(
                shortest_path_lengths, max_distance=max_distance)

        rec = shortest_path_lengths[np.triu_indices(shortest_path_lengths.shape[0], k=1)]
        rec = rec.astype(dtype=float)
        rec[rec == (float(number_nodes + 1))] = float("inf")
        rec = np.reciprocal(rec[rec <= number_nodes], dtype=np.float32)  # TODO: let's check this type: np.float32 or float16 ?

        df_num = np.sum(rec)
        df_num *= 2
        df = 1 - float(df_num / df_denum)

        return round(df, 5)

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def mreach(graph, nodes: list, m: int, max_distance: int=None, implementation=CmodeEnum.igraph, sp_matrix=None) -> int:
        """
        Calculates the m-reach ([Ref]_, equation 12). The m-reach is defined as a count of the number of unique nodes
        reached by any member of the kp-set in m links or less.
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for.
        :param int m: an integer (greater than zero) representing the maximum m-reach distance
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :param CmodeEnum.igraph implementation: Computation of the shortest paths is deferred
        to the following implementations:
        *`imps.auto`: the most performing implementation is automatically chosen according to the geometry of graph
        *`imps.igraqh`: (default) use the default shortest path implementation in igraph (run on a single computing core)
        *`imps.pyntacle`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors or NVIDIA-enabled GPU graphic cards. This method returns a matrix (`:type np.ndarray:`) of shortest
        paths. Infinite distances actually equal the total number of vertices plus one.
        :param np.ndarray sp_matrix: if *implementation* is either cpu or gpu, you can pass a precomputed matrix of
        shortest paths instead of recomputing it. If None, the matrix of the shortest paths will be recomputed
        :return: An integer representing the number of nodes reached by the input node(s) in m steps or less
        """

        if not isinstance(m, int):
            raise TypeError("'m' must be an integer value")

        elif m < 1:
            raise ValueError("'m' must be greater than zero")

        elif m >= graph.vcount() + 1:
            raise ValueError("'m' must be less or equal than the total number of vertices")

        if not isinstance(implementation, CmodeEnum):
            raise KeyError("'implementation' not valid. It must be one of the following: {}".format(list(CmodeEnum)))

        if max_distance:
                if not isinstance(max_distance, int):
                    raise TypeError("'max_distance' must be an integer value greater than one")
                if max_distance < 1:
                    raise ValueError("'max_distance' must be an integer value greater than one")
        else:
            index_list = gu(graph=graph).get_node_indices(node_names=nodes)

            if implementation == CmodeEnum.igraph:
                shortest_path_lengths = sp.shortest_path_length_igraph(graph, nodes=nodes)
            else:
                if not sp_matrix:
                    shortest_path_lengths = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=nodes)
                else:
                    if not isinstance(sp_matrix, np.ndarray):
                        raise ValueError("'sp_matrix' must be a numpy.ndarray instance")
                    elif sp_matrix.shape[0] != graph.vcount():
                        raise WrongArgumentError("The dimension of 'sp matrix' is different from the total "
                                                 "number of nodes")
                    else:
                        shortest_path_lengths = sp_matrix[index_list, :]

        if max_distance:
            shortest_path_lengths = ShortestPathModifier.set_nparray_to_inf(shortest_path_lengths, max_distance)

        mreach = 0
        vminusk = set(graph.vs.indices) - set(index_list)
        for j in vminusk:
            for spl in shortest_path_lengths:
                if spl[j] <= m:
                    mreach += 1
                    break

        return mreach

    @staticmethod
    @check_graph_consistency
    @vertex_doctor
    def dR(graph, nodes, max_distance=None, implementation=CmodeEnum.igraph, sp_matrix=None) -> float:
        """
        Calculates the distance-weighted reach ([Ref]_, equation 14). The distance-weighted reach can be defined as the
        sum of the reciprocals of distances from the kp-set S to all nodes, where the distance from the set to a node is
        defined as the minimum distance (minimum shortest path distance).
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param nodes: Nodes which computing the index for.
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :param CmodeEnum.igraph implementation: Computation of the shortest paths is deferred
        to the following implementations:
        *`imps.auto`: the most performing implementation is automatically chosen according to the geometry of graph
        *`imps.igraqh`: (default) use the default shortest path implementation in igraph (run on a single computing core)
        *`imps.pyntacle`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors or NVIDIA-enabled GPU graphic cards. This method returns a matrix (`:type np.ndarray:`) of shortest
        paths. Infinite distances actually equal the total number of vertices plus one.
        :param np.ndarray sp_matrix: if *implementation* is either cpu or gpu, you can pass a precomputed matrix of
        shortest paths instead of recomputing it. If None, the matrix of the shortest paths will be recomputed
        :return: An integer representing the distance-weighted reach measure of the graph
        """

        if not isinstance(implementation, CmodeEnum):
            raise KeyError("'implementation' not valid. It must be one of the following: {}".format(list(CmodeEnum)))
        elif max_distance:
                if not isinstance(max_distance, int):
                    raise TypeError("'max_distance' must be an integer value greater than one")
                elif max_distance < 1:
                    raise ValueError("'max_distance' must be an integer greater than one")
        else:
            index_list = gu(graph=graph).get_node_indices(node_names=nodes)

            if implementation == CmodeEnum.igraph:
                shortest_path_lengths = sp.shortest_path_length_igraph(graph=graph, nodes=nodes)
            else:
                if sp_matrix is None:
                    shortest_path_lengths = sp.get_shortestpaths(graph=graph, nodes=nodes, cmode=implementation)
                else:
                    if not isinstance(sp_matrix, np.ndarray):
                        raise ValueError("'sp_matrix' must be a numpy.ndarray instance")
                    elif sp_matrix.shape[0] != graph.vcount():
                        raise WrongArgumentError("The dimension of 'sp matrix' is different from the total number of nodes")
                    else:
                        shortest_path_lengths = sp_matrix[index_list, :]

            if max_distance:
                shortest_path_lengths = ShortestPathModifier.set_nparray_to_inf(sp_matrix, max_distance)

            dr_num = 0
            vminusk = set(graph.vs.indices) - set(index_list)
            for j in vminusk:
                dKj = min(spl[j] for spl in shortest_path_lengths)
                dr_num += 1 / dKj

            dr = dr_num / float(graph.vcount())
            return dr
