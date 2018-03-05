"""
Calculator of key players, as from http://rd.springer.com/article/10.1007/s10588-006-7084-x
"""
from enum import Enum
from igraph import *
from algorithms.global_topology import GlobalTopology
from algorithms.local_topology import LocalTopology
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.wrong_argument_error import WrongArgumentError
from config import *

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


class _KeyplayerAttribute(Enum):
    F = 0
    DF = 1
    MREACH = 2
    DR = 3


class KeyPlayer:
    """
    **[EXPAND]**
    """
    __graph = None
    """:type: Graph"""

    def __init__(self, graph):
        """
        Initializes a graph for key players calculation
        
        :param Graph graph: Graph provided in input
        :raises IllegalGraphSizeError: if graph does not contain vertices or edges
        """
        self.logger = log

        if graph.vcount() < 1:
            self.logger.fatal("This graph does not contain vertices")
            raise IllegalGraphSizeError("This graph does not contain vertices")
        elif graph.ecount() < 1:
            self.logger.fatal("This graph does not contain edges")
            raise IllegalGraphSizeError("This graph does not contain edges")
        else:
            self.__graph = graph

    def get_graph(self) -> Graph:
        """
        Returns the graph
        
        :return: A Graph data structure
        """
        return self.__graph

    def set_graph(self, graph, shallow_copy=True):
        """
        Replaces the internal graph object with a copy of the new in input
        
        :param igraph.Graph graph: igraph.Graph object provided in input
        :param bool shallow_copy: Flag determining shallow or deep copy of attributes of the graph
        :raises IllegalGraphSizeError: if graph does not contain vertices or edges
        """

        if graph.vcount() < 1:
            self.logger.fatal("This graph does not contain vertices")
            raise IllegalGraphSizeError("This graph does not contain vertices")
        elif graph.ecount() < 1:
            self.logger.fatal("This graph does not contain edges")
            raise IllegalGraphSizeError("This graph does not contain edges")
        else:
            if shallow_copy:
                self.__graph = graph.copy()
                for elem in self.__graph.attributes():
                    del self.__graph[elem]

            self.logger.info("New graph set")

    def F(self, recalculate=False) -> float:
        """
        Calculates the first version of the KPP-NEG (equation 4)
        Since nodes within a component are mutually reachable, and since components of a graph can be enumerated
        extremely efficiently, the F measure (equation 3 of the paper) can be computed more economically by rewriting
        it in terms of the sizes (sk) of each component (indexed by k).
        F = 1 => Maximum fragmentation. All nodes are isolate
        F = 0 => No fragmentation. The graph has one component
        
        :param bool recalculate: If True, F is recalculated regardless of whether it had been already computed
        :return: The F measure of the graph
        """
        self.logger.info("Calculating the F of the graph")
        if recalculate or _KeyplayerAttribute.F.name not in self.__graph.attributes():
            num_nodes = self.__graph.vcount()
            #print(num_nodes)

            bp = GlobalTopology(self.__graph)
            components = bp.components(recalculate=True)
            # print("components kp OLD")
            # print(components)
            # input()

            f_num = sum(len(sk) * (len(sk) - 1) for sk in components)
            f_denum = num_nodes * (num_nodes - 1)

            f = 1 - (f_num / f_denum)
            self.__graph[_KeyplayerAttribute.F.name] = f

        return self.__graph[_KeyplayerAttribute.F.name]

    def DF(self, recalculate=False) -> float:
        """
        Calculates the KPP-NEG (equation 9)
        F = 1 => Maximum fragmentation. All nodes are isolates
        
        :param bool recalculate: If True, F is recalculated regardless if it had been already computed
        :return: The DF measure of the graph
        """
        self.logger.info("Calculating the DF of the graph")

        if recalculate or _KeyplayerAttribute.DF.name not in self.__graph.attributes():
            number_nodes = self.__graph.vcount()
            df_denum = number_nodes * (number_nodes - 1)
            lt = LocalTopology(self.__graph)

            shortest_path_lengths = lt.shortest_path_igraph(recalculate=True)
            # print(shortest_path_lengths)
            df_num = 0

            for i in range(number_nodes):
                for j in range(i + 1, number_nodes):
                    # print(shortest_path_lengths[i][j])
                    df_num += 1 / shortest_path_lengths[i][j]

            df_num *= 2

            self.__graph[_KeyplayerAttribute.DF.name] = 1 - (df_num / df_denum)
        return self.__graph[_KeyplayerAttribute.DF.name]

    def mreach(self, m: int, index_list: list, recalculate=False) -> float:
        """
        Calculates the m-reach (equation 12). The m-reach is defined as a count of the number of unique nodes reached
        by any member of the kp-set in m links or less.
        
        :param int m: Maximum number of links allowed between the kp-set and the other nodes
        :param bool recalculate: If True, m-reach is recalculated regardless if it had been already computed
        :param list[int] index_list: List of node indices belonging to the kp-set
        :return: The m-reach measure of the graph
        :raises WrongArgumentError: When the input node index does not exist
        """
        if index_list is not None and set(index_list) > set(self.__graph.vs.indices):
            self.logger.error("The input node index '{}' does not exist in the graph".format(index_list))
            raise WrongArgumentError("The input node index '{}' does not exist in the graph".format(index_list))
        else:
            self.logger.info("Calculating the m-reach of the kp-set {}".format(index_list))
            if recalculate or _KeyplayerAttribute.MREACH.name not in self.__graph.vs.attributes() \
                    or None in self.__graph.vs[index_list][_KeyplayerAttribute.MREACH.name]:
                mreach = 0
                """:type: int"""

                lt = LocalTopology(self.__graph)
                shortest_path_lengths = lt.shortest_path_igraph(index_list=index_list, recalculate=True)

                vminusk = list(set(self.__graph.vs.indices) - set(index_list))
                for j in vminusk:
                    for spl in shortest_path_lengths:
                        if spl[j] <= m:
                            mreach += 1
                            break

                self.__graph.vs[index_list][_KeyplayerAttribute.MREACH.name] = mreach

                return mreach
            else:
                return self.__graph.vs[index_list[0]][_KeyplayerAttribute.MREACH.name]

    def DR(self, index_list, recalculate=False) -> float:
        """
        Calculates the distance-weighted reach (equation 14). The distance-weighted reach can be defined as the sum
        of the reciprocals of distances from the kp-set S to all nodes, where the distance from the set to a node is
        defined as the minimum distance.
        
        :param bool recalculate: If True, distance-weighted reach is recalculated regardless of whether it was already computed
        :param list[int] index_list: List of node indices belonging to the kp-set
        :return: The distance-weighted reach measure of the graph
        :raises WrongArgumentError: When the input node index does not exist
        """
        if index_list is not None and set(index_list) > set(self.__graph.vs.indices):
            self.logger.error("The input node index '{}' does not exist in the graph".format(index_list))
            raise WrongArgumentError("The input node index '{}' does not exist in the graph".format(index_list))
        else:
            self.logger.info("Calculating the distance-weighted reach of the kp-set {}".format(index_list))

            if recalculate or _KeyplayerAttribute.DR.name not in self.__graph.vs[index_list].attributes() \
                    or None in self.__graph.vs[index_list][_KeyplayerAttribute.DR.name]:

                lt = LocalTopology(self.__graph)
                shortest_path_lengths = lt.shortest_path(index_list=index_list, recalculate=True)

                dr_num = 0
                """:type: float"""
                vminusk = set(self.__graph.vs.indices) - set(index_list)
                """distance from each node to the subset"""
                for j in vminusk:
                    dKj = min(spl[j] for spl in shortest_path_lengths)
                    dr_num += 1 / dKj
                dr = dr_num / float(self.__graph.vcount())
                self.__graph.vs[index_list][_KeyplayerAttribute.DR.name] = dr
                return dr
            else:
                return self.__graph.vs[index_list[0]][_KeyplayerAttribute.DR.name]

