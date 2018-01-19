"""
Calculator of global properties of graphs
"""
from enum import Enum
from math import isinf
import numpy as np
from igraph import Graph, VertexClustering
from config import *
from algorithms import local_topology
from utils.graph_utils import *

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "27 October 2016"
__license__ = """"
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


class _GlobalAttribute(Enum):
    diameter = 0
    radius = 1
    average_path_length = 2
    component = 3
    density = 4
    pi = 5
    clustering_coefficient = 6
    weighted_clustering_coefficient = 7
    average_degree = 8
    average_radiality = 9
    average_radiality_reach = 10
    average_closeness = 11
    average_eccentricity = 12


class GlobalTopology:
    """
    Calculator of global properties of graphs **[EXPAND]**
    """

    __graph = None
    """:type: Graph"""
    logger = None
    """:type: Logger"""

    def __init__(self, graph):
        """
        Initializes a graph for global properties calculation
        
        :param Graph graph: Graph provided in input
        :raises IllegalGraphSizeError: if graph does not contain vertices or edges
        """
        self.logger = log

        self.__graph_utils = GraphUtils(graph=graph)
        self.__graph_utils.graph_checker()

        self.__graph = graph

    def get_graph(self) -> Graph:
        """
        Returns the graph
        
        :return: A Graph data structure
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

    def diameter(self, recalculate=False) -> int:
        """
        Calculates the graph diameter
        
        :param bool recalculate: If True, the diameter is recalculated regardless if it had been already computed
        :return: The diameter of the graph
        """
        self.logger.info("Calculating the diameter of the graph")
        if recalculate or _GlobalAttribute.diameter.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.diameter.name] = self.__graph.diameter(directed=False)
        return self.__graph[_GlobalAttribute.diameter.name]

    def radius(self, recalculate=False) -> int:
        """
        Calculates the graph radius
        
        :param bool recalculate: If True, the radius is recalculated regardless if it had been already computed
        :return: The radius of the graph
        """
        self.logger.info("Calculating the radius of the graph")
        if recalculate or _GlobalAttribute.radius.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.radius.name] = self.__graph.radius()
        return self.__graph[_GlobalAttribute.radius.name]

    def average_path_length(self, recalculate=False) -> float:
        """
        Calculates the average shortest path of a graph
        
        :param bool recalculate: If True, the average shortest path is recalculated regardless if it had been already computed
        :return: The average path length of the graph
        """
        self.logger.info("Calculating the average path length of the graph")
        if recalculate or _GlobalAttribute.average_path_length.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.average_path_length.name] = self.__graph.average_path_length(directed=False)
        return self.__graph[_GlobalAttribute.average_path_length.name]

    def components(self, recalculate=False) -> VertexClustering:
        """
        Calculates clusters (connected components) for a given graph
        
        :param bool recalculate: If True, the components are recalculated regardless if they had been already computed
        :return: A VertexClustering data structure containing the clustering of the vertex set of a graph
        """
        self.logger.info("Calculating the components of the graph")
        if recalculate or _GlobalAttribute.component.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.component.name] = self.__graph.components()
        return self.__graph[_GlobalAttribute.component.name]

    def density(self, loops=True, recalculate=False) -> int:
        """
        Calculates the density of the graph
        
        :param bool loops: Whether to take loops into consideration
        :param bool recalculate: If True, the density is recalculated regardless if it had been already computed
        :return: The density (or the reciprocity) of the graph
        """
        self.logger.info("Calculating the density of the graph")
        if recalculate or _GlobalAttribute.density.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.density.name] = self.__graph.density(loops)
        return self.__graph[_GlobalAttribute.density.name]

    def clustering_coefficient(self, recalculate=False) -> float:
        """
        Calculates the global transitivity (clustering coefficient) of the graph
        
        :param bool recalculate: If True, the clustering coefficient is recalculated regardless if it had been already computed
        :return: The transitivity of the graph
        """
        self.logger.info("Calculating the clustering coefficient of the graph")
        if recalculate or _GlobalAttribute.clustering_coefficient.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.clustering_coefficient.name] = self.__graph.transitivity_avglocal_undirected()
        return self.__graph[_GlobalAttribute.clustering_coefficient.name]

    def pi(self, recalculate=False) -> float:
        """
        Pi is defined as the ratio between the total paths length and the diameter
        
        :param bool recalculate: If True, the Pi value is recalculated regardless if it had been already computed
        :return: The Pi of the graph
        """
        self.logger.info("Calculating the Pi of the graph")
        if recalculate or _GlobalAttribute.pi.name not in self.__graph.attributes():
            d = self.__graph.diameter()
            edges_number = self.__graph.ecount()
            self.__graph[_GlobalAttribute.pi.name] = edges_number / d
        return self.__graph[_GlobalAttribute.pi.name]

    def weighted_clustering_coefficient(self, recalculate=False) -> float:
        """
        Computes the weighted clustering coefficient, defined as the average of each node's
        clustering coefficient weighted by its degree
        
        :param bool recalculate: If True, the weighted clustering coefficient is recalculated regardless if it had been already computed
        :return: The weighted clustering coefficient
        """
        self.logger.info("Calculating the weighted clustering coefficient of the graph")
        if recalculate or _GlobalAttribute.weighted_clustering_coefficient.name not in self.__graph.attributes():
            self.__graph[_GlobalAttribute.weighted_clustering_coefficient.name] = self.__graph.transitivity_undirected()
        return self.__graph[_GlobalAttribute.weighted_clustering_coefficient.name]

    def average_degree(self, recalculate=False) -> float:
        """
            Computes the average degree at a global level (divide each nodes's degree by the total number of nodes)
            
            :param bool recalculate: If True, the average degree is recalculated regardless if it had been already computed
            :return: The average degree
        """
        self.logger.info("Calculating the average degree of the graph")
        if recalculate or _GlobalAttribute.average_degree.name not in self.__graph.attributes():
            degr = local_topology.LocalTopology(graph=self.__graph).degree(recalculate=True)
            # print(degr)
            self.__graph[_GlobalAttribute.average_degree.name] = np.mean(degr)
            # print (self.__graph[GlobalAttribute.average_degree])
        return self.__graph[_GlobalAttribute.average_degree.name]

    def average_radiality(self, recalculate=False) -> float:
        """
            Computes the average radiality at a global level (divide each nodes's radiality by the total number of nodes)
            
            :param bool recalculate: If True, the average radiality is recomputed regardless if it had been already computed
            :return: The average radiality
        """

        self.logger.info("Calculating the average radiality of the graph")

        if recalculate or _GlobalAttribute.average_radiality.name not in self.__graph.attributes():

            rad = local_topology.LocalTopology(graph=self.__graph).radiality(recalculate=True)
            rad = [x for x in rad if not isinf(x)] #remove all the infinite value for float component
            if len(rad) > 0:

                self.__graph[_GlobalAttribute.average_radiality.name] = np.mean(rad)
            else:
                self.__graph[_GlobalAttribute.average_radiality.name] = 0

        return self.__graph[_GlobalAttribute.average_radiality.name]

    def average_radiality_reach(self, recalculate=False) -> float:
        """
            Computes the radiality reach at a global level (divide each nodes's radiality reach by the total number of nodes)
            
            :param bool recalculate: If True, the average radiality reach is recomputed regardless if it had been already computed
            :return: The average radiality
        """

        self.logger.info("Calculating the average radiality  reach of the graph")
        if recalculate or _GlobalAttribute.average_radiality_reach.name not in self.__graph.attributes():

            rad_r = local_topology.LocalTopology(graph=self.__graph).radiality_reach(recalculate=True)

            if len(rad_r) > 0:

                self.__graph[_GlobalAttribute.average_radiality_reach.name] = np.mean(rad_r)

            else:
                self.__graph[_GlobalAttribute.average_radiality_reach.name] = 0


        return self.__graph[_GlobalAttribute.average_radiality_reach.name]

    def average_closeness(self, recalculate=False) -> float:
        """
            Computes the average closeness at a global level (divide each nodes's closeness by the total number of nodes)
            
            :param bool recalculate: If True, the average closeness is recomputed regardless if it had been already computed
            :return: The average closeness
        """

        self.logger.info("Calculating the average closeness of the graph")
        if recalculate or _GlobalAttribute.average_closeness.name not in self.__graph.attributes():
            clo = local_topology.LocalTopology(graph=self.__graph).closeness(recalculate=True)
            self.__graph[_GlobalAttribute.average_closeness.name] = np.mean(clo)
            # print (self.__graph[GlobalAttribute.average_degree])
        return self.__graph[_GlobalAttribute.average_closeness.name]

    def average_eccentricity(self, recalculate=False) -> float:
        """
            Computes the average eccentricity at a global level (divide each nodes's eccentricity by the total number of nodes)
            
            :param bool recalculate: If True, the average eccentricity is recomputed regardless if it had been already computed
            :return: The average eccentricity
        """

        self.logger.info("Calculating the average eccentricity of the graph")
        if recalculate or _GlobalAttribute.average_eccentricity.name not in self.__graph.attributes():
            ecc = local_topology.LocalTopology(graph=self.__graph).eccentricity(recalculate=True)
            self.__graph[_GlobalAttribute.average_eccentricity.name] = np.mean(ecc)
            # print (self.__graph[GlobalAttribute.average_degree])
        return self.__graph[_GlobalAttribute.average_eccentricity.name]
