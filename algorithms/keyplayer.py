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

""" Utilities to compute KP Metrics described by Borgatti"""

from config import *
import algorithms.local_topology as lt
from tools.misc.graph_routines import *
from tools.misc.enums import SP_implementations
from tools.graph_utils import GraphUtils as gu
from tools.misc.shortest_path_modifications import *
import numpy as np

class KeyPlayer:
    """
    computes the KeyPlayer values for the 4 metrics described in [Ref]_
    [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
    """

    @staticmethod
    @check_graph_consistency
    def F(graph) -> float:
        """
        Calculates the first version of the F (a KPP-NEG Measure)([Ref]_, equation 4)
        Since nodes within a component are mutually reachable, and since components of a graph can be enumerated
        extremely efficiently, the F measure (equation 3 of the paper) can be computed more economically by rewriting
        it in terms of the sizes (sk) of each component (indexed by k).
        **F = 1* => Maximum fragmentation. All nodes are isolate
        **F = 0* => No fragmentation. The graph has one component
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param graph an igraph.Graph object that is checked at the beginning to be pyntacle compatible. See Pyntacle
        Documentation for the minimim requirements for this object.
        :return: The F measure of the graph as a float ranging between 0.0 and 1.0, where 0 is maximal disconnection
        (each node is an isolate) and 1 is maximum connection (the graph is complete)
        """
        # sys.stdout.write("\n############## Running F ##############\n")
        if graph.ecount() == 0: #maximum F
            return 1.0

        # elif graph.clique_number() == graph.vcount():
        #     return 0.0  #maximum F: it's a clique

        else:
            num_nodes = graph.vcount()

            components = graph.components()

            f_num = sum(len(sk) * (len(sk) - 1) for sk in components)
            f_denum = num_nodes * (num_nodes - 1)
            f = 1 - (f_num / f_denum)

            return round(f, 5)

    @staticmethod
    @check_graph_consistency
    def dF(graph, implementation=SP_implementations.igraph, max_distances=None) -> float:
        """
        A measure for computing the dF (a KPP-NEG Measure) ([Ref]_ equation 9). The DF is a measure of node connectivity
        among the graph and it's a measure of how nodes in the graph can be reached.
        The dF value ranges from 0 to 1, where:
        **dF = 1* => Maximum fragmentation. All nodes are isolate
        **dF = 0* => No fragmentation. The graph has one component
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param graph an igraph.Graph object that is checked at the beginning to be pyntacle compatible. See Pyntacle
        Documentation for the minimim requirements for this object.
        :param int max_distances: The maximum shortest path length after which two nodes are considered disconnected
        :param imps implementation: computes the shortest path using one of the two provided methods in LocalTopology
        choices are:
        *`imps.auto`: automatic implementation (default) chooses the best implementation according to the graph properties
        *`imps.igraqh`: use the default shortest path implementation in igraph (performs on a single core)
        *`imps.pyntacle` (default): computes sp using Floyd-Warshall algorithm with HPC computing in order to get a matrix
        (represented as a `:type np.ndarray:`) with all the shortest path in the graph. the distance between two
        disconnected nodes is represented as the total number of vertices plus one and is then reconverted internally to
        a `:type math.inf:` object
        :return: The DF measure of the graph (float)
        """
        # todo implementation "auto" should consider graph parameters and use the correct implementation among the classical
        # todo and the GPU/CPU one
        #print("df, USING IMPLEMENTATION", implementation)

        if not isinstance(implementation, SP_implementations):
            raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(SP_implementations)))


        if max_distances is not None:
                if not isinstance(max_distances, int):
                    raise TypeError("\"max_sp\" must be an integer greater than one")

                if not max_distances >= 1:
                    raise ValueError("\"max_sp\" must be an integer greater than one")

                if max_distances > graph.vcount():
                    raise ValueError("\"max_sp\" must be less or equal to the number of nodes in the graph")
            
        if graph.ecount() == 0: #maximum F
            return 1.0

        else:
            if implementation == SP_implementations.igraph:
                return KeyPlayer.__dF_Borgatti(graph=graph, max_distances=max_distances)

            else:
                return KeyPlayer.__dF_pyntacle(graph=graph, max_distances=max_distances, implementation=implementation)

    @staticmethod
    def __dF_Borgatti(graph, max_distances=None) -> float:
        """
        reserved method for calculating the DF of a graph using standard igraph methods for the computation of
        the shortest path. This is literally the equation 9 in Borgatti's paper.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param int max_distances: The maximum shortest path length after which two nodes are considered disconnected
        :return: a float representing the dF value for the selected graph
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)
        shortest_path_lengths = lt.LocalTopology.shortest_path_igraph(graph)

        if max_distances is not None:
            shortest_path_lengths = ShortestPathModifier.igraph_sp_to_inf(shortest_path_lengths, max_distances=max_distances)

        df_num = 0

        for i in range(number_nodes):
            for j in range(i + 1, number_nodes):
                # print(shortest_path_lengths[i][j])
                df_num += 1 / shortest_path_lengths[i][j]

        df_num *= 2
        df = 1 - (df_num / df_denum)

        return round(df, 5)

    @staticmethod
    def __dF_pyntacle(graph, max_distances=None, implementation=SP_implementations.igraph) -> float:
        """
        Implement the DF search using parallel computing we implemented in `LocalTopology.shortest_path_pyntacle` in
        order to speed up shortest path  search using either CPU or HPU accelerations (if nVidia compatible graphics
        are present).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param int max_distances: The maximum shortest path length after which two nodes are considered disconnected
        :return: a float representing the dF value for the input graph.
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)

        shortest_path_lengths = lt.LocalTopology.shortest_path_pyntacle(graph=graph, nodes=None,
                                                                        mode=lt.GraphType.undirect_unweighted,
                                                                        implementation=implementation)

        if max_distances is not None:
            shortest_path_lengths = ShortestPathModifier.np_array_to_inf(shortest_path_lengths, max_distances=max_distances)

        rec = shortest_path_lengths[np.triu_indices(shortest_path_lengths.shape[0], k=1)]
        rec = rec.astype(dtype=float)
        rec[rec==(float(graph.vcount()+1))] = float("inf")
        rec = np.reciprocal(rec[rec<=graph.vcount()], dtype=np.float32)

        df_num = np.sum(rec)
        """:type: int"""
        df_num *= 2
        df = 1 - (df_num / df_denum)

        return round(df, 5)

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def mreach(graph, nodes, m, max_distances=None, implementation=SP_implementations.igraph, sp_matrix=None) -> int:
        """
        Calculates the m-reach ([Ref]_, equation 12). The m-reach is defined as a count of the number of unique nodes
        reached by any member of the kp-set in m links or less.
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param int m: an integer (greater than zero) representing the maximum m-reach distance
        :param nodes: a single node (as a string) or a list of nodes of the graph *(the ones stored  in the graph.vs["name"] object)* **(required)**
        :param int max_distances: the maximum distance after that two nodes are considered disconnected
        :param SP_implementations implementation: computes the shortest path using one of the two provided methods in LocalTopology
        choices are:
        *`imps.auto`: automatic implementation (default) chooses the best implementation according to the graph properties
        *`imps.igraqh`: use the default shortest path implementation in igraph (performs on a single core)
        *`imps.pyntacle` (default): computes sp using Floyd-Warshall algorithm with HPC computing in order to get a matrix
        :param np.ndarray sp_matrix: if implementation is either cpu or gpu, you can pass the matrix of shortest paths instead of recomputing it. if None, the matrix of the shortest paths will be recomputed
        :return: an integer representing the number of nodes reached by the inpu node(s) in  m steps or less
        """
        print("mreach, USING IMPLEMENTATION", implementation)

        if not isinstance(m, int):
            raise TypeError("\"m\" must be an integer")
        if m < 1:
            raise ValueError("\"m\" must be greater than zero")
        elif m >= graph.vcount() + 1:
            raise ValueError("\"m\" must be lesser than the total number of vertices plus one")

        if not isinstance(implementation, SP_implementations):
            raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(SP_implementations)))

        if max_distances is not None:
                if not isinstance(max_distances, int):
                    raise TypeError("\"max_sp\" must be an integer greater than one")

                if max_distances >= 1:
                    raise ValueError("\"max_sp\" must be an integer greater than one")

        index_list = gu(graph=graph).get_node_indices(node_names=nodes)

        if implementation == SP_implementations.igraph:
            shortest_path_lengths = lt.LocalTopology.shortest_path_igraph(graph=graph, nodes=nodes)

            if max_distances is not None:
                shortest_path_lengths = ShortestPathModifier.igraph_sp_to_inf(shortest_path_lengths, max_distances)

        else:
            if sp_matrix is None:
                shortest_path_lengths = lt.LocalTopology.shortest_path_pyntacle(graph=graph, implementation=implementation, nodes=nodes)

            else:
                if not isinstance(sp_matrix, np.ndarray):
                    raise ValueError("\"sp_matrix\" must be a numpy.ndarray object")
                elif sp_matrix.shape[0] != graph.vcount():
                    raise WrongArgumentError("Dimension of the \"sp matrix\" is different to the total number of nodes")

                else:
                    shortest_path_lengths = sp_matrix[index_list, :]

            if max_distances is not None:
                shortest_path_lengths = ShortestPathModifier.np_array_to_inf(shortest_path_lengths, max_distances)

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
    @vertexdoctor
    def dR(graph, nodes, max_distances=None, implementation=SP_implementations.igraph, sp_matrix=None) -> float:
        """
        Calculates the distance-weighted reach ([Ref]_, equation 14). The distance-weighted reach can be defined as the
        sum of the reciprocals of distances from the kp-set S to all nodes, where the distance from the set to a node is
        defined as the minimum distance (minimum shortest path distance).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: a single node (as a string) or a list of nodes of the graph *(the ones stored  in the
        graph.vs["name"] object)* **(required)**
        :param int max_distances: the maximum distance after that two nodes are considered disconnected
        :param SP_implementations implementation: computes the shortest path using one of the two provided methods in LocalTopology
        choices are:
        *`imps.auto`: automatic implementation (default) chooses the best implementation according to the graph properties
        *`imps.igraqh`: use the default shortest path implementation in igraph (performs on a single core)
        *`imps.pyntacle` (default): use the result provided by the LocalTopology.shortest_path_pyntacle (must be called separately)
        :param np.ndarray sp_matrix: if implementation is either cpu or gpu, you can pass the matrix of shortest paths instead of recomputing it. if None, the matrix of the shortest paths will be recomputed
        :return: a float representing he distance-weighted reach measure of the graph
        """
        print("dr, USING IMPLEMENTATION", implementation)

        if not isinstance(implementation, SP_implementations):
            raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(SP_implementations)))

        if max_distances is not None :
                if not isinstance(max_distances, int):
                    raise TypeError("\"max_sp\" must be an integer greater than one")

                if max_distances >= 1:
                    raise ValueError("\"max_sp\" must be an integer greater than one")

        index_list = gu(graph=graph).get_node_indices(node_names=nodes)

        if implementation == SP_implementations.igraph:
            shortest_path_lengths = lt.LocalTopology.shortest_path_igraph(graph=graph, nodes=nodes)

            if max_distances is not None:
                shortest_path_lengths = ShortestPathModifier.igraph_sp_to_inf(shortest_path_lengths, max_distances)

            dr_num = 0
            vminusk = set(graph.vs.indices) - set(index_list)
            for j in vminusk:
                dKj = min(spl[j] for spl in shortest_path_lengths)
                dr_num += 1 / dKj

            dr = dr_num / float(graph.vcount())
            return dr

        else: #we must provide a full matrix of shortest paths BEFORE searching for the single nodes
            if sp_matrix is None:
                shortest_path_lengths = lt.LocalTopology.shortest_path_pyntacle(graph=graph, nodes=nodes, implementation=implementation)

            else:
                if not isinstance(sp_matrix, np.ndarray):
                    raise ValueError("\"sp_matrix\" must be a numpy.ndarray object")
                elif sp_matrix.shape[0] != graph.vcount():
                    raise WrongArgumentError("Dimension of the \"sp matrix\" is different to the total number of nodes")
                else:
                    shortest_path_lengths = sp_matrix[index_list,:]

            if max_distances is not None:
                shortest_path_lengths = ShortestPathModifier.np_array_to_inf(sp_matrix, max_distances)

            dr_num = 0
            vminusk = set(graph.vs.indices) - set(index_list)
            for j in vminusk:
                dKj = min(spl[j] for spl in shortest_path_lengths)
                dr_num += 1 / dKj

            dr = dr_num / float(graph.vcount())
            return dr

