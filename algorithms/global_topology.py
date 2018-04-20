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

""" Class for computing the Global Properties of a graph"""
import algorithms.local_topology as Lt
from tools.misc.graph_routines import check_graph_consistency
from statistics import mean
from igraph import Graph
from tools.enums import Cmode
import numpy as np

class GlobalTopology:
    """
    GlobalTopology Computes metrics at a global level for a given igraph.Graph object
    """
    @staticmethod
    @check_graph_consistency
    def diameter(graph: Graph) -> int:
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
    def radius(graph: Graph) -> int:
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
    def components(graph: Graph) -> int:
        """
        Returns the number of components in a graph.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: an integer representing the number of components in a graph
        """
        return len(graph.components())

    @staticmethod
    @check_graph_consistency
    def density(graph: Graph) -> float:
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
    def pi(graph: Graph) -> float:
        """
        Returs the pi of a graph. Pi is defined as the ratio between the total edges and the diameter.
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the graph's pi
        """
        return round(graph.ecount()/graph.diameter(), 5)

    @staticmethod
    @check_graph_consistency
    def average_clustering_coefficient(graph: Graph) -> float:
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
    def weighted_clustering_coefficient(graph: Graph) -> float:
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
    def average_degree(graph: Graph) -> float:
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
    def average_closeness(graph: Graph) -> float:
        """
        Returns the average closeness of the input graph. This is done by computing the mean of each node's closeness
        (the sum of the length of the shortest path between each node and all the other nodes in the graph)
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the average closeness of a graph
        """

        return round(mean(Lt.LocalTopology.closeness(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_eccentricity(graph: Graph) -> float:
        """
        Returns the average eccentricity of the input graph. This is done by computing the mean of each
        node's eccentricity (the maximum distance from each node to all other nodes in the graph)
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the average eccentricity of a graph
        """

        return round(mean(Lt.LocalTopology.eccentricity(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality(graph: Graph, implementation=Cmode.igraph) -> float:
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

        return round(mean(Lt.LocalTopology.radiality(graph, nodes=None, cmode=implementation)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality_reach(graph: Graph, implementation=Cmode.igraph) -> float:
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
        if not isinstance(implementation, Cmode):
            raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(Cmode)))

        return round(mean(Lt.LocalTopology.radiality_reach(graph=graph, nodes=None, cmode=implementation)), 5)

    @staticmethod
    @check_graph_consistency
    def average_shortest_path_length(graph: Graph, implementation=Cmode.igraph) -> float:
        """
        computes the  average shortest path length as defined in https://en.wikipedia.org/wiki/Average_path_length
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual. If the graph as more than one component, the average
        shortest path length is the sum of each component's shortest path length (both directins are counted) divide by
        by the total number of components. isolated nodes counts as a components but their distance to all other
        members in the graph is 0
        :param implementation: the way the shortest path will be computed. Implementations are stored in `misc.enums`
        The default implementation is `imps.auto`, which automatically identifies the best implementation based on both the graph structure and the hardware specifications
        :return: a positive float representing the average shortest path length of the igraph object
        """


        if not isinstance(implementation, Cmode):
            raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(Cmode)))

        if implementation == Cmode.igraph:
            avg_sp = Graph.average_path_length(graph,directed=False,unconn=False)
            return avg_sp

        else:
            #re-implement the average_path_length algorithm for a fully connected and a disconnected graph
            if GlobalTopology.components(graph) < 2:
                sp = Lt.LocalTopology.shortest_path_pyntacle(graph=graph, implementation=implementation)
                # set all the shortest path greater than the total number of nodes to 0
                sp[sp == graph.vcount() + 1] = 0
                return round(np.sum(np.divide(sp, (graph.vcount() * (graph.vcount() - 1)))), 5)

            else:
                comps = graph.components()
                sum = 0 #this will be averaged afterwards
                for elem in comps:
                    subg = graph.induced_subgraph(elem) #cdreate a subgraph with only the vertex returned by components()
                    if subg.ecount() > 0:
                        sp = Lt.LocalTopology.shortest_path_pyntacle(graph=subg, implementation=implementation)
                        sp[sp == subg.vcount() + 1] = 0
                        sum += np.sum(sp)
                return round(mean(sum, len(comps)),5)

    @staticmethod
    @check_graph_consistency
    def median_shortest_path_length(graph: Graph) -> float:
        """
        Computes the median shortest path length across all shortest paths obtained from 'LocalTopology'. This is useful
        if it is needed to estimate the trend of the shortest path distances
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual. If the graph as more than one component, the average
        shortest path length is the sum of each component's shortest path length (both directins are counted) divide by
        by the total number of components. isolated nodes counts as a components but their distance to all other
        members in the graph is 0
        :return: the median shortest path length across all shortest path distances
        """
        #if not isinstance(implementation, imps):
        #    raise KeyError("\"implementation\" not valid, must be one of the following: {}".format(list(imps)))

        sps = Lt.LocalTopology.shortest_path_igraph(graph=graph)
        sps = np.array(sps)

        return np.median(sps[sps != 0])