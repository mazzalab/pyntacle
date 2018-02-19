'''
this module implements several implementations of a sparseness index as proposed by two publications
'''

from enum import Enum
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
import igraph
import math
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


class _SparsenessAttribute(Enum):
    completeness_legacy = 0
    compactness = 1
    completeness = 2


class Sparseness:
    '''
    Computes the completeness index of a graph or subgraph according to two different theories proposed
    '''
    __graph = None
    """:type: Graph"""
    logger = None
    """:type: Logger"""

    def __init__(self, graph):
        """
        Initializes a graph for local properties calculation

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

    def get_graph(self):
        """
        Returns the graph

        :return: - A Graph data structure
        """
        return self.__graph

    def set_graph(self, graph, deepcopy=False):
        """
        Replaces the internal graph object with a new one

        :param igraph.Graph graph: igraph.Graph object provided in input
        :param bool deepcopy: Flag determining shallow or deep copy of attributes of the graph
        """
        if not deepcopy:
            for elem in graph.attributes():
                del graph[elem]
        self.__graph = graph

    def name_to_id(self, node_name):
        """
        Retrieves the node index given the node name or index
        """
        if not isinstance(node_name, str) and isinstance(node_name, int):
            return -1
        else:
            if isinstance(node_name, str):
                return self.__graph.select(node_id=node_name)[0].index
            return node_name

    def completeness_legacy(self, recalculate=False):
        '''
        Compute the completeness index as described by Mazza et al for an undirected graph.
        Completeness is defined as the total number of edges / the total number of nonedges among all possible edges

        :param recalculate: boolean; whether to recalculate the index or not for the whole graph
        :return: The completeness index of the graph
        '''
        self.logger.info("computing the completeness as described by Mazza et al")
        if recalculate or _SparsenessAttribute.completeness_legacy not in self.__graph.attributes():
            # get the total number of nonzero elements in an adjacency matrix
            num = self.__graph.ecount()  # total number of real edges
            tote = (self.__graph.vcount() * (self.__graph.vcount() - 1)) / 2
            denom = tote - self.__graph.ecount()  # total number of non-edges
            if denom == 0:
                raise ZeroDivisionError("the graph is complete, thus the completeness index is out of bound")

            self.__graph[_SparsenessAttribute.completeness_legacy.name] = num / denom

        return self.__graph[_SparsenessAttribute.completeness_legacy.name]

    def compactness(self, recalculate=False):
        '''
        We implement here the compactness index as described by Randìc and DeAlba (J. Chem. Inf. Comput. Sci., 1999)

        :param recalculate: boolean; whether to recalculate the index or not for the whole graph
        :return: The compactness value for the whole graph
        '''
        self.logger.info("computing the compactness as described by Randìc et al")

        if recalculate or _SparsenessAttribute.compactness not in self.__graph.attributes():
            # first part of the equation: (square of the nodes/edges*2)-1
            a = math.pow(self.__graph.vcount(), 2)
            b = self.__graph.ecount() * 2
            numa = a / b - 1
            numa = math.pow(numa, -1)
            # second part of the equation (1-1/total number of nodes)
            numb = 1 - (1 / self.__graph.vcount())
            numb = math.pow(numb, -1)
            # finally
            self.__graph[_SparsenessAttribute.compactness.name] = numa * numb

        return self.__graph[_SparsenessAttribute.compactness.name]

    def completeness(self, recalculate=False):
        '''
        We implement the denseness measure as implemented by XXX in Applied Mathematics **[EXPAND]**

        :param recalculate: boolean; whether to recalculate the index or not for the whole graph
        :return: The completeness value for the whole graph
        '''
        if recalculate or _SparsenessAttribute.completeness not in self.__graph.attributes():
            root_k = self.__graph.vcount()  # k is a dimension of the adjacency matrix (so the square of the vcount)
            k = math.pow(root_k, 2)
            first_part = root_k - 1  # (root(k)-1)
            z = k - (self.__graph.ecount() * 2)  # number of zeros in the matrix
            second_part = (k / z) - 1
            denseness = first_part * second_part
            self.__graph[_SparsenessAttribute.completeness.name] = denseness

        return self.__graph[_SparsenessAttribute.completeness.name]