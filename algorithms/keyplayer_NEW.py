__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "14 November 2016"
__license__ = u"""
  Copyright (C) 20016-2017  Tommaso Mazza <t,mazza@css-mendel.it>
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

import algorithms.local_topology_NEW as lt
from misc.graph_routines import *
from utils.graph_utils import GraphUtils as gu
from misc.sps_operations import *
import numpy as np


# todo add Pyntacle documentation link shwing minim requirements for the igraph object to be used in within this module

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

        num_nodes = graph.vcount()

        components = graph.components()

        f_num = sum(len(sk) * (len(sk) - 1) for sk in components)
        f_denum = num_nodes * (num_nodes - 1)

        f = 1 - (f_num / f_denum)

        return round(f, 5)

    @staticmethod
    @check_graph_consistency
    def dF(graph, implementation="auto", max_sp=None) -> float:
        """
        A measure for computing the dF (a KPP-NEG Measure) ([Ref]_ equation 9). The DF is a measure of node connectivity
        among the graph and it's a measure of how nodes in the graph can be reached.
        The dF value ranges from 0 to 1, where:
        **dF = 1* => Maximum fragmentation. All nodes are isolate
        **dF = 0* => No fragmentation. The graph has one component
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param graph an igraph.Graph object that is checked at the beginning to be pyntacle compatible. See Pyntacle
        Documentation for the minimim requirements for this object.
        :param int max_sp: The maximum shortest path length after which two nodes are considered disconnected
        :param str implementation: computes the shortest path using one of the two provided methods in LocalTopology
        choices are:
        *`igraqh`: use the default shortest path implementation in igraph (performs on a single core)
        *`pyntacle` (default): computes sp using Floyd-Warshal algorithm with HPC computing in order to get a matrix
        (represented as a `:type np.ndarray:`) with all the shortest path in the graph. the distance between two
        disconnected nodes is represented as the total number of vertices plus one and is then reconverted internally to
        a `:type math.inf:` object
        :return: The DF measure of the graph (float)
        """
        # todo implementation "auto" should consider graph parameters and use the correct implementation among the classical
        # todo and the GPU/CPU one

        choices = ["igraph", "pyntacle", "auto"]
        if not isinstance(implementation, str):
            raise TypeError("\"implementation\" must be a string")

        if implementation not in choices:
            raise KeyError("{0} is not a valid choice for implementation. valid options are {1}".format(implementation,
                                                                                                        ",".join(
                                                                                                            choices)))
        if max_sp is not None :
                if not isinstance(max_sp, int):
                    raise TypeError("\"max_sp\" must be an integer greater than one")

                if max_sp >= 1:
                    raise ValueError("\"max_sp\" must be an integer greater than one")

        if implementation == "igraph":
            return KeyPlayer.__dF_Borgatti(graph=graph, max_sp=max_sp)

        elif implementation == "pyntacle":
            return KeyPlayer.__dF_pyntacle(graph=graph, max_sp=max_sp)

        else:
            sys.stdout.write("automatic dF implementation not yet supported\n. Please come back soon!")
            sys.exit(0)
            # todo automatic implementation of dF here

    @staticmethod
    def __dF_Borgatti(graph, max_sp=None) -> float:
        """
        reserved method for calculating the DF of a graph using standard igraph methods for the computation of
        the shortest path. This is literally the equation 9 in Borgatti's paper.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param int max_sp: The maximum shortest path length after which two nodes are considered disconnected
        :return: a float representing the dF value for the selected graph
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)
        shortest_path_lengths = lt.LocalTopology.shortest_path_igraph(graph)

        if max_sp is not None:
            shortest_path_lengths = ShortestPathModifier.igraph_sp_to_inf(shortest_path_lengths, max_sp=max_sp)

        df_num = 0

        for i in range(number_nodes):
            for j in range(i + 1, number_nodes):
                # print(shortest_path_lengths[i][j])
                df_num += 1 / shortest_path_lengths[i][j]

        df_num *= 2
        df = 1 - (df_num / df_denum)

        return round(df, 5)

    @staticmethod
    def __dF_pyntacle(graph, max_sp=None) -> float:
        """
        Implement the DF search using parallel computing we implemented in `LocalTopology.shortest_path_pyntacle` in
        order to speed up shortest path  search using either CPU or HPU accelerations (if nVidia compatible graphics
        are present).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param int max_sp: The maximum shortest path length after which two nodes are considered disconnected
        :return: a float representing the dF value for the input graph.
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)

        shortest_path_lengths = lt.LocalTopology.shortest_path_pyntacle(graph=graph, nodes=None,
                                                                        mode=lt.GraphType.undirect_unweighted,
                                                                        implementation=lt.implementation.auto)

        if max_sp is not None:
            shortest_path_lengths = ShortestPathModifier.np_array_to_inf(shortest_path_lengths, max_sp=max_sp)

        rec = shortest_path_lengths[np.triu_indices(shortest_path_lengths.shape[0], k=1)]
        ''':type: np.ndarray'''
        rec = rec.astype(dtype=float)
        rec[rec==(float(graph.vcount()+1))] = float("inf")
        rec = np.reciprocal(rec[rec<=graph.vcount()],dtype=np.float32)

        df_num = np.sum(rec)
        df_num *= 2
        df = 1 - (df_num / df_denum)

        return round(df, 5)

    @staticmethod
    @check_graph_consistency
    @vertexdoctor
    def mreach(graph, nodes, m, max_sp=None, implementation="auto") -> int:
        """
        Calculates the m-reach ([Ref]_, equation 12). The m-reach is defined as a count of the number of unique nodes
        reached by any member of the kp-set in m links or less.
        [Ref] Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. https://doi.org/10.1007/s10588-006-7084-x
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param int m: an integer (greater than zero) representing the maximum m-reach distance
        :param nodes: a single node (as a string) or a list of nodes of the graph (required)
        :param int max_sp: the maximum distance after that two nodes are considered disconnected
        :param str implementation: computes the shortest path using one of the two provided methods in LocalTopology
        choices are:
        *`igraqh`: use the default shortest path implementation in igraph (performs on a single core)
        *`pyntacle` (default): computes sp using Floyd-Warshal algorithm with HPC computing in order to get a matrix
        (represented as a `:type np.ndarray:`) with all the shortest path in the graph. the distance between two
        disconnected nodes is represented as the total number of vertices plus one and is then reconverted internally to
        a `:type math.inf:` object
        :return: an integer representing the number of nodes reached by the inpu node(s) in  m steps or less
        """
        if not isinstance(m, int):
            raise TypeError("\"m\" must be an integer")
        if m < 1:
            raise ValueError("\"m\" must be greater than zero")
        elif m >= graph.vcount() +1:
            raise ValueError("\"m\" must be lesser than the total number of vertices plus one")

        choices = ["igraph", "pyntacle", "auto"]
        if not isinstance(implementation, str):
            raise TypeError("\"implementation\" must be a string")

        if implementation not in choices:
            raise KeyError("{0} is not a valid choice for implementation. valid options are {1}".format(implementation,
                                                                                                        ",".join(
                                                                                                            choices)))

        if max_sp is not None :
                if not isinstance(max_sp, int):
                    raise TypeError("\"max_sp\" must be an integer greater than one")

                if max_sp >= 1:
                    raise ValueError("\"max_sp\" must be an integer greater than one")

        if implementation == "igraph":
            shortest_path_lengths = lt.LocalTopology.shortest_path_igraph(graph=graph)

            if max_sp is not None:
                shortest_path_lengths = ShortestPathModifier.igraph_sp_to_inf(shortest_path_lengths, max_sp)

        elif implementation == "pyntacle":
            shortest_path_lengths = lt.LocalTopology.shortest_path_pyntacle(graph=graph)

            if max_sp is not None:
                shortest_path_lengths = ShortestPathModifier.np_array_to_inf(shortest_path_lengths,max_sp)

        else:
            sys.stdout.write("\"auto\" implementation not yet done, please come back later\n")
            sys.exit()
            #todo add automatic implementation even here

        mreach = 0

        index_list = gu(graph=graph).get_node_indices(node_names=nodes)
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
    def dR(graph, nodes, max_sp=None, implementation="auto") -> float:
        """
        Calculates the distance-weighted reach ([Ref]_, equation 14). The distance-weighted reach can be defined as the
        sum of the reciprocals of distances from the kp-set S to all nodes, where the distance from the set to a node is
        defined as the minimum distance (minimum shortest path distance).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param nodes: a single node (as a string) or a list of nodes of the graph (required)
        :param int max_sp: the maximum distance after that two nodes are considered disconnected
        :param str implementation: computes the shortest path using one of the two provided methods in LocalTopology
        choices are:
        *`igraqh`: use the default shortest path implementation in igraph (performs on a single core)
        *`pyntacle` (default): computes sp using Floyd-Warshal algorithm with HPC computing in order to get a matrix
        (represented as a `:type np.ndarray:`) with all the shortest path in the graph. the distance between two
        disconnected nodes is represented as the total number of vertices plus one and is then reconverted internally to
        a `:type math.inf:` object
        :return: a float representing he distance-weighted reach measure of the graph
        """

        choices = ["igraph", "pyntacle", "auto"]
        if not isinstance(implementation, str):
            raise TypeError("\"implementation\" must be a string")

        if implementation not in choices:
            raise KeyError("{0} is not a valid choice for implementation. valid options are {1}".format(implementation,
                                                                                                        ",".join(
                                                                                                            choices)))
        if max_sp is not None :
                if not isinstance(max_sp, int):
                    raise TypeError("\"max_sp\" must be an integer greater than one")

                if max_sp >= 1:
                    raise ValueError("\"max_sp\" must be an integer greater than one")

        if implementation == "igraph":
            shortest_path_lengths = lt.LocalTopology.shortest_path_igraph(graph=graph)

            if max_sp is not None:
                shortest_path_lengths = ShortestPathModifier.igraph_sp_to_inf(shortest_path_lengths, max_sp)

        elif implementation == "pyntacle":
            shortest_path_lengths = lt.LocalTopology.shortest_path_pyntacle(graph=graph)

            if max_sp is not None:
                shortest_path_lengths = ShortestPathModifier.np_array_to_inf(shortest_path_lengths,max_sp)

        else:
            sys.stdout.write("\"auto\" implementation not yet done, please come back later\n")
            sys.exit()
            #todo add automatic implementation even here

        index_list = gu(graph=graph).get_node_indices(node_names=nodes)
        dr_num = 0
        vminusk = set(graph.vs.indices) - set(index_list)

        for j in vminusk:
            dKj = min(spl[j] for spl in shortest_path_lengths)
            dr_num += 1 / dKj

        dr = dr_num / float(graph.vcount())
        return dr
