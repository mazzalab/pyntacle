__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
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

import algorithms.local_topology_NEW as lt
from misc.graph_routines import check_graph_consistency
from misc.enums import implementations as imps

from statistics import mean

#todo add pyntacle documentation link for minimum requirements in igraph

class GlobalTopology:
    """
    GlobalTopology Computes metrics at a global level for a given igraph.Graph object
    """
    @staticmethod
    @check_graph_consistency
    def diameter(graph) -> int:
        """
        Method that returns the diameter of a graph. The diameter is defined as the maximum among all eccentricites
        in a graph. If the graph consists of isolates, we defined  the diameter as zero (the inverse of infinity).
        If the input graph has more than one component, the longest shortest path for
        the largest component is returned. If you're interested in finding the diameter of a single component,
        you should subset your graph first.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return:an integer representing the graph's diameter
        """
        return graph.diameter()


    @staticmethod
    @check_graph_consistency
    def radius(graph) -> int:
        """
        Method that returns the radius of a graph. The radius  of a graph is defined as the minimum among
        all eccentricites in a graph. If the graph consists of more than one component, the radius of the smallest
        component is returned (If the graph has isolates, the radius is zero,the inverse of infinity).
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return:  an integer representing the graph's radius
        """

        return int(graph.radius())


    @staticmethod
    @check_graph_consistency
    def components(graph) -> int:
        """
        Returns the number of components in a graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: an integer representing the number of components in a graph
        """
        return len(graph.components())


    @staticmethod
    @check_graph_consistency
    def density(graph) -> float:
        """
        Computes the density of a graph. The density of a graph is defined as the ratio between the 2(number of edges)
        in the input graph and the number of possible edges in a graph (number of nodes(number of nodes -1))
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the graph's density
        """

        return round(graph.density(), 5)


    @staticmethod
    @check_graph_consistency
    def pi(graph) -> float:
        """
        Returs the pi of a graph. Pi is defined as the ratio between the total edges and the diameter.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the graph's pi
        """
        return round(graph.ecount()/graph.diameter(), 5)


    @staticmethod
    @check_graph_consistency
    def average_clustering_coefficient(graph) -> float:
        """
        Computes the average clustering coefficient among all nodes in a graph (the mean of the clustering coefficient
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the graph's global transitivity (clustering coefficient)
        of all nodes in the graph)
        """
        return round(graph.transitivity_avglocal_undirected(), 5)


    @staticmethod
    @check_graph_consistency
    def weighted_clustering_coefficient(graph) -> float:
        """
        Computes the weighted clustering coefficient among all nodes in a graph. The Weighted clustering coefficient is
        defined as the average (mean) of each node's clustering coefficient weighted by its degree.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the graph's weighted clustering coefficient
        """
        return round(graph.transitivity_undirected(), 5)


    @staticmethod
    @check_graph_consistency
    def average_degree(graph) -> float:
        """
        Returns the average degree of the input graph. The average degree is the mean of the degree for each node in
        the graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the average degree of the input graph
        """
        return round(mean(graph.degree()), 5)


    @staticmethod
    @check_graph_consistency
    def average_closeness(graph) -> float:
        """
        Returns the average closeness of the input graph. This is done by computing the mean of each node's closeness
        (the sum of the length of the shortest path between each node and all the other nodes in the graph)
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the average closeness of a graph
        """

        return round(mean(lt.LocalTopology.closeness(graph=graph)), 5)


    @staticmethod
    @check_graph_consistency
    def average_eccentricity(graph) -> float:
        """
        Returns the average eccentricity of the input graph. This is done by computing the mean of each
        node's eccentricity (the maximum distance from each node to all other nodes in the graph)
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the average eccentricity of a graph
        """

        return round(mean(lt.LocalTopology.eccentricity(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality(graph, implementation=imps.igraph) -> float:
        """
        Computes the average radiality, defined as the mean for all the radiality values for each node in the graph.
        **WARNING** Average Radiality doesn't work when the graph has more than one component
        (some of the distances will be infinite, hence the average radiality will always be -inf).
        For that purpose, we recommend using the *average_radiality_reach()* method that uses a modified version
        of the radiality. Otherwise, we recommend to subset your graph using igraph to take the component you need the
        radiality for.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param implementation: the implementation that will be used to computed radiality. Choices are
        **igraph:* uses the igraph implementation
        **parallel_CPU:* uses the Floyd-Warshall algorithm implemented in numba CPU
        **parallel_GPU:* uses the Floyd-Warshall algorithm implemented in numba- GPU (requires CUDA-compatible
        nVidia graphics)
        :return: a float representing the average of the radiality of all nodes in the graph.
        """
        return round(mean(lt.LocalTopology.radiality(graph, nodes=None, implementation=implementation)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality_reach(graph, implementation=imps.igraph) -> float:
        """
        Computes the average radiality reach, defined as the mean for all the radiality  reach values for each node
        in the graph. Radiality Reach is defined here as the radiality for each node in each component weighted for the
        ratio of the number of nodes in that component over all nodes in the graph. Isolated nodes has 0 radiality
        reach by defninition. This is done to ensure that the radiality for each component is weighted on the
        contribution of the component in the graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :param implementation: the implementation that will be used to computed radiality. Choices are
        **igraph:* uses the igraph implementation
        **parallel_CPU:* uses the Floyd-Warshall algorithm implemented in numba CPU
        **parallel_GPU:* uses the Floyd-Warshall algorithm implemented in numba- GPU (requires CUDA-compatible
        nVidia graphics)
        :return: a float representing the average of the radiality reach of all nodes in the graph.
        """
        return round(mean(lt.LocalTopology.radiality_reach(graph=graph, nodes=None, implementation=implementation)), 5)

    @staticmethod
    @check_graph_consistency
    def average_shortest_path_length(graph, implementation=imps.igraph):
        """
        :param graph:
        :param implementation:
        :return:
        """
        #todo complete this when all the shortest path length are done

        if not isinstance(implementation, imps):
            raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(imps)))

        if implementation == imps.igraph:
            from igraph import Graph
            avg_sp = Graph.average_path_length(graph,directed=False,unconn=False)
            return avg_sp

        elif implementation == imps.gpu:
            pass
        elif implementation == imps.cpu:
            pass
