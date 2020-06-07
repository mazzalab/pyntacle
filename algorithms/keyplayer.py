__author__ = ["Tommaso Mazza"]
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.2"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"07/06/2020"
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


import numpy as np
import igraph
from tools.enums import CmodeEnum
from tools.graph_utils import GraphUtils as gu
from algorithms.shortest_path import ShortestPath as sp
from internal.shortest_path_modifications import ShortestPathModifier
from exceptions.wrong_argument_error import WrongArgumentError


class KeyPlayer:
    """ Compute Key-Player metrics, as described in
    `Borgatti, S.P. Comput Math Organiz Theor (2006) 12: 21. <https://doi.org/10.1007/s10588-006-7084-x>`_"""

    @staticmethod
    def F(graph: igraph.Graph) -> float:
        r"""
        Calculate the *F*  (*fragmentation*) index, a negative key player (*kp-neg*) measure, as described by the equation 4 in
        `The original article on key players <https://doi.org/10.1007/s10588-006-7084-x>`_
        Since nodes within a component are mutually reachable, and since components of a graph can be enumerated
        extremely efficiently, the F measure can be computed more economically by rewriting it in terms of the
        sizes (:math:`s_k`) of each component (indexed by k). F ranges from 0 to 1:

            * **F** = 1 => Maximum fragmentation. All nodes are isolate
            * **F** = 0 => No fragmentation. The graph has only one component

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: The F status of the input graph
        """
        if len(graph.components()) == 1: #graph is complete
            f = 0

        else:
            num_nodes = graph.vcount()
            f_denum = (num_nodes * (num_nodes - 1))

            components = graph.components()

            f_num = sum(len(sk) * (len(sk) - 1) for sk in components)

            f = 1 - (f_num / f_denum)

        return round(f, 5)

    @staticmethod
    def dF(graph:igraph.Graph, cmode:CmodeEnum =CmodeEnum.igraph, max_distance=None) -> float:
        r"""
        Calculate the *dF* (*distance-based fragmentation*), a negative *key player* measure described by the
        equation 9 in `The original article on key players <https://doi.org/10.1007/s10588-006-7084-x>`_.

        The dF is a measure of node connectivity and measures the impact of geodesics in the overall fragmentation
        status of the graph.

        | The dF value ranges from 0 to 1, where:

            * **dF** = 1 => Maximum fragmentation. All nodes are isolate
            * **dF** = 0 => No fragmentation. The graph is complete

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths required dstance based fragmentation. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).

        :return float: The DF measure of the graph as a float value ranging from 0.0 to 1.0

        :raise ValueError: if ``max_distance`` is not an integer greater than zero and lesser than the total number of vertices in the graph minus one
        :raise KeyError: if ``cmode`` is not one of the possible values in :class:`~pyntacle.tools.enums.CmodeEnum`
        """

        num_nodes = graph.vcount()
        num_edges = graph.ecount()

        if num_edges == (num_nodes * (num_nodes - 1))/2: #graph is complete, dF is 0
            return 0.0

        else:
            if max_distance is not None:
                if not isinstance(max_distance, int):
                    raise TypeError("'max_distance', if provided, must be an integer")
                elif max_distance < 1:
                    raise ValueError("'max_distance' must be >= 1 ")
                elif max_distance > graph.vcount():
                    raise ValueError("'max_distance' must be <= the size of the graph")

            if cmode == CmodeEnum.igraph:
                return KeyPlayer.__dF_Borgatti(graph=graph, max_distance=max_distance)
            else:
                return KeyPlayer.__dF_pyntacle(graph=graph, max_distance=max_distance, cmode=cmode)

    @staticmethod
    def __dF_Borgatti(graph: igraph.Graph, max_distance: int or None =None) -> float:
        r"""
        Internal method for calculating the *DF* value of a graph using the igraph implementation of the shortest paths.
        This implements, literally, the equation 9 in Borgatti's paper.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (no maximum distance allowed)

        :return float: The DF measure of the graph as a float value ranging from 0.0 to 1.0
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)
        shortest_path_lengths = sp.shortest_path_length_igraph(graph=graph)

        if max_distance:
            shortest_path_lengths = ShortestPathModifier.set_max_distances_igraph(
                shortest_path_lengths, max_distance=max_distance)

        df_num = 0
        for i in range(number_nodes):
            df_num += sum([float(1 / shortest_path_lengths[i][j]) for j in range(i + 1, number_nodes)])

        df_num *= 2
        df = 1 - (df_num / df_denum)

        return round(df, 5)

    @staticmethod
    def __dF_pyntacle(graph: igraph.Graph, max_distance: int or None=None, cmode: CmodeEnum =CmodeEnum.cpu) -> float:
        r"""
        Internal method for calculating the *DF* value of a graph using parallel implementations of the shortest paths.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved)
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths required dstance based fragmentation. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return float: The DF measure of the graph as a float value ranging from 0.0 to 1.0
        """

        number_nodes = graph.vcount()
        df_denum = number_nodes * (number_nodes - 1)
        shortest_path_lengths = sp.get_shortestpaths(graph=graph, nodes=None, cmode=cmode)

        if max_distance:
            shortest_path_lengths = ShortestPathModifier.set_max_distances_nparray(
                shortest_path_lengths, max_distance=max_distance)

        rec = shortest_path_lengths[np.triu_indices(shortest_path_lengths.shape[0], k=1)]
        rec = rec.astype(dtype=float)
        rec[rec == (float(number_nodes + 1))] = float("inf")
        rec = np.reciprocal(rec[rec <= number_nodes], dtype=np.float32)

        df_num = np.sum(rec)
        df_num *= 2
        df = 1 - float(df_num / df_denum)

        return round(df, 5)

    @staticmethod
    def mreach(graph: igraph.Graph, nodes: list or str or None, m: int, max_distance: int or None =None, cmode:CmodeEnum =CmodeEnum.igraph, sp_matrix: np.ndarray =None) -> int:

        r"""
        Calculate the *m-reach* , a positive *key player* measure  (*kp-pos*) described by the
        equation 12 in `The original article on key players <https://doi.org/10.1007/s10588-006-7084-x>`_.
        The m-reach  returns the number of nodes that are reached by a set of nodes in :math:`m` steps or less, where
        :math:`m` is the minimum least distance between any node in a set :math:`k` and the rest of the graph :math:`N-k`.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list nodes: a list of strings that matches the node ``name`` attribute of the selected nodes.
        :param int m: an integer (greater than zero) representing the maximum m-reach distance.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved)
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths required dstance based fragmentation. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.
        :param None, np.ndarray sp_matrix:  A :math:`NxN` (:math:`N` being the size of the graph) :py:class:`numpy.ndarray` storing integers representing the distances between nodes. :warning: Disconected nodes **must** be represented as a distance greater than :math:`N`. If provided, ``cmode`` is ignored and the shortest paths are derived from the matrix directly. default is py:class:`None`.

        :return int: An integer representing the number of nodes reached by the input node(s) in *m* steps or less

        :raise: KeyError: if ``cmode`` is not one of the valid :class:`~pyntacle.tools.enums.CmodeEnum`
        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute, or when ``m`` is not a :py:class:`int`
        :raise ValueError: when any of the node ``name`` attribute passed to the function is not present in the input graph, if ``m`` is lesser than 0 or greater than the size of the graph or if a provided ``sp_matrix`` is not :py:class:`None` or a :py:class:`numpy.ndarray` storing integers
        """
        if not isinstance(m, int):
            raise TypeError(u"'m' must be an integer")

        elif m < 1 or m >= graph.vcount() + 1:
            raise ValueError(u"'m' must be greater than zero and less or equal than the total number of vertices")

        if max_distance:
                if not isinstance(max_distance, int):
                    raise TypeError(u"'max_distance' must be an integer value greater than one")
                if max_distance < 1:
                    raise ValueError(u"'max_distance' must be an integer value greater than one")
        else:
            index_list = gu(graph=graph).get_node_indices(nodes=nodes)

            if cmode == CmodeEnum.igraph:
                shortest_path_lengths = sp.shortest_path_length_igraph(graph, nodes=nodes)
            else:
                if not sp_matrix:
                    shortest_path_lengths = sp.get_shortestpaths(graph=graph, cmode=cmode, nodes=nodes)
                else:
                    if not isinstance(sp_matrix, np.ndarray):
                        raise ValueError(u"'sp_matrix' must be a numpy.ndarray instance")
                    elif sp_matrix.shape[0] != graph.vcount():
                        raise WrongArgumentError(u"The dimension of 'sp matrix' is different from the total "
                                                 "number of nodes")
                    else:
                        shortest_path_lengths = sp_matrix[index_list, :]

        if max_distance:
            shortest_path_lengths = ShortestPathModifier.set_max_distances_nparray(shortest_path_lengths, max_distance)

        mreach = 0
        vminusk = set(graph.vs.indices) - set(index_list)
        for j in vminusk:
            for spl in shortest_path_lengths:
                if spl[j] <= m:
                    mreach += 1
                    break

        return mreach

    @staticmethod
    def dR(graph: igraph.Graph, nodes: list, max_distance: int or None =None, cmode: CmodeEnum=CmodeEnum.igraph, sp_matrix: np.ndarray or None =None) -> float:
        r"""
        Calculates the *dR* (*distance-weighted reach*) (described by the
        equation 14 in `The original article on key players <https://doi.org/10.1007/s10588-006-7084-x>`_), a positive
        key player (*kp-pos*) measure. The distance-weighted reach can be defined as the sum of the reciprocals of
        distances from the kp-set :math:`k` to all nodes, where the distance from the set to a node is defined as
        the minimum distance (minimum shortest path distance).  dR ranges from 0 to 1, where:

            * **dR** = 1 => Maximal reachability. The set :math:`k` is directly tied to the rest of the graph
            * **dR** = 0 => No reachability. The set :math:`k` is completely disconnected to the graph

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list nodes: a list of strings that matches the node ``name`` attribute of the selected nodes.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved)
        :param None, np.ndarray sp_matrix:  A :math:`NxN` (:math:`N` being the size of the graph) :py:class:`numpy.ndarray` storing integers representing the distances between nodes. :warning: Disconected nodes **must** be represented as a distance greater than :math:`N`. If provided, ``cmode`` is ignored and the shortest paths are derived from the matrix directly. default is py:class:`None`.

        :return float : the distance-weighted reach measure of the graph

        :raise TypeError: when ``nodes`` is a list of strings matching the vertex ``name`` attribute
        :raise KeyError: when any of the node ``name`` attribute passed to the function is not present in the input graph
        :raise ValueError: when any of the node ``name`` attribute passed to the function is not present in the input graph or if a provided ``sp_matrix`` is not :py:class:`None` or a :py:class:`numpy.ndarray` storing integers
        """

        if max_distance:
                if not isinstance(max_distance, int):
                    raise TypeError(u"'max_distance' must be an integer value greater than one")
                elif max_distance < 1:
                    raise ValueError(u"'max_distance' must be an integer greater than one")
        else:
            index_list = gu(graph=graph).get_node_indices(nodes=nodes)

            if cmode == CmodeEnum.igraph:
                shortest_path_lengths = sp.shortest_path_length_igraph(graph=graph, nodes=nodes)
            else:
                if sp_matrix is None:
                    shortest_path_lengths = sp.get_shortestpaths(graph=graph, nodes=nodes, cmode=cmode)
                else:
                    if not isinstance(sp_matrix, np.ndarray):
                        raise ValueError(u"'sp_matrix' must be a numpy.ndarray instance")
                    elif sp_matrix.shape[0] != graph.vcount():
                        raise WrongArgumentError(u"The dimension of 'sp matrix' is different from the total number of nodes")
                    else:
                        shortest_path_lengths = sp_matrix[index_list, :]

            if max_distance:
                shortest_path_lengths = ShortestPathModifier.set_max_distances_nparray(sp_matrix, max_distance)

            dr_num = 0
            vminusk = set(graph.vs.indices) - set(index_list)
            for j in vminusk:
                dKj = min(spl[j] for spl in shortest_path_lengths)
                dr_num += 1 / dKj

            dr = round(dr_num / float(graph.vcount()), 5)
            return dr
