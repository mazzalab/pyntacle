""" Compute several global topology metrics of a given graph """

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.3"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "26/04/2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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

from algorithms.local_topology import LocalTopology
from private.graph_routines import check_graph_consistency
from statistics import mean
from igraph import Graph
from tools.enums import CmodeEnum


class GlobalTopology:
    """
    Compute several global topology metrics of a given graph
    """

    @staticmethod
    @check_graph_consistency
    def diameter(graph: Graph) -> int:
        """
        Return the *diameter* of a graph.
        The diameter is defined as the maximum among all eccentricites in a graph. If the graph consists of isolates,
        we set the diameter to zero. If the input graph has more than one component, the longest shortest path for
        the largest component is returned. If one is interested in finding the diameter of a single component,
        one should subset the graph in asvance.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: an integer value representing the graph's diameter
        """
        return graph.diameter()

    @staticmethod
    @check_graph_consistency
    def radius(graph: Graph) -> int:
        """
        Return the *radius* of a graph.
        The radius of a graph is defined as the minimum among all eccentricites in a graph. If the graph consists of
        more than one component, the radius of the smallest component is returned. If the graph has isolates,
        the radius is zero.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: an integer value representing the graph's radius
        """

        return int(graph.radius())

    @staticmethod
    @check_graph_consistency
    def components(graph: Graph) -> int:
        """
        Return the number of *components* in a graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: an integer value representing the number of components in a graph
        """
        return len(graph.components())

    @staticmethod
    @check_graph_consistency
    def density(graph: Graph) -> float:
        """
        Compute the *density* of a graph.
        The density of a graph is defined as the ratio between the actual number of edges and the number of possible
        edges in the graph (n*(n-1))
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the graph's density
        """

        return round(graph.density(), 5)

    @staticmethod
    @check_graph_consistency
    def pi(graph: Graph) -> float:
        """
        Return the *pi* of a graph.
        Pi is defined as the ratio between the total number of edges and the diameter.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the graph's pi
        """
        return round(graph.ecount()/graph.diameter(), 5)

    @staticmethod
    @check_graph_consistency
    def average_clustering_coefficient(graph: Graph) -> float:
        """
        Compute the *average clustering coefficient* among all nodes in a graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the graph's mean clustering coefficient
        """
        return round(graph.transitivity_avglocal_undirected(), 5)

    @staticmethod
    @check_graph_consistency
    def weighted_clustering_coefficient(graph: Graph) -> float:
        """
        Compute the *weighted clustering coefficient* among all nodes in a graph.
        The weighted clustering coefficient is defined as the average of each node's clustering coefficient
        weighted by their degree values.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the graph's weighted clustering coefficient
        """
        return round(graph.transitivity_undirected(), 5)

    @staticmethod
    @check_graph_consistency
    def average_degree(graph: Graph) -> float:
        """
        Return the *average degree* of the input graph.
        The average degree is the mean of the degree of each node in the graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the average degree of the input graph
        """
        return round(mean(graph.degree()), 5)

    @staticmethod
    @check_graph_consistency
    def average_closeness(graph: Graph) -> float:
        """
        Return the *average closeness* of the input graph.
        This is computed as the mean of each node's closeness.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the average closeness of a graph
        """

        return round(mean(LocalTopology.closeness(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_eccentricity(graph: Graph) -> float:
        """
        Returns the *average eccentricity* of the input graph.
        This is done by computing the mean of each node's eccentricity.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :return: a float value representing the average eccentricity of a graph
        """

        return round(mean(LocalTopology.eccentricity(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality(graph: Graph, cmode=CmodeEnum.igraph) -> float:
        """
        Compute the *average radiality*, defined as the mean of all node radiality values.
        **WARNING** The average radiality calculation does not work when the graph has more than one component
        (some of the distances will be infinite, hence the average radiality would always be -inf).
        For that purpose, we recommend using the *average_radiality_reach()* method that calculates a modified version
        of the radiality. Otherwise, we recommend to subset your graph to take the components you need the
        radiality for.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param cmode: the implementation that will be used to compute the radiality. Choices are:
        **CmodeEnum.igraph:* uses the igraph implementation of the shortest path calculation
        **CmodeEnum.cpu:* uses a Floyd-Warshall algorithm optimized for multicore computing
        **CmodeEnum.gpu:* uses a Floyd-Warshall algorithm optimized for CUDA-enabled GPUs (requires CUDA-compatible
        nVIDIA graphics graphics)
        :return: a float value representing the average of the radiality of all nodes in the graph.
        """

        return round(mean(LocalTopology.radiality(graph, nodes=None, cmode=cmode)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality_reach(graph: Graph, cmode=CmodeEnum.igraph) -> float:
        """
        Computes the average radiality reach, defined as the mean for all the radiality  reach values for each node
        in the graph. Radiality Reach is defined here as the radiality for each node in each component weighted for the
        ratio of the number of nodes in that component over all nodes in the graph. Isolated nodes has 0 radiality
        reach by defninition. This is done to ensure that the radiality for each component is weighted on the
        contribution of the component in the graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param cmode: the implementation that will be used to computed radiality. Choices are
        **igraph:* uses the igraph implementation
        **parallel_CPU:* uses the Floyd-Warshall algorithm implemented in numba CPU
        **parallel_GPU:* uses the Floyd-Warshall algorithm implemented in numba- GPU (requires CUDA-compatible
        nVidia graphics)
        :return: a float representing the average of the radiality reach of all nodes in the graph.
        """
        if not isinstance(cmode, CmodeEnum):
            raise KeyError("'cmode' not valid, must be one of the following: {}".format(list(CmodeEnum)))

        return round(mean(LocalTopology.radiality_reach(graph=graph, nodes=None, cmode=cmode)), 5)
