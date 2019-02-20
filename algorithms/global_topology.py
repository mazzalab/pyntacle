"""Compute several global topology metrics for a given graph"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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
from internal.graph_routines import check_graph_consistency
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
        r"""
        Returns the *diameter* of a graph.
        The diameter is the maximum among all eccentricites in a graph. If the graph consists of isolates,
        the diameter is set to zero. If the input graph has more than one component, the longest shortest path for
        the largest component is returned. If one is interested in finding the diameter of a single component, an induced subgraph retaining the component **must** be set.

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :return int: an integer value representing the graph's diameter
        """
        return graph.diameter()

    @staticmethod
    @check_graph_consistency
    def radius(graph: Graph) -> int:
        r"""
        Returns the *radius* of a graph.
        The radius of a graph is the minimum among all eccentricites in a graph. If the graph consists of
        more than one component, the radius of the smallest component is returned. If the graph has isolates,
        the radius is zero.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return int: an integer value representing the graph's radius
        """

        return int(graph.radius())

    @staticmethod
    @check_graph_consistency
    def components(graph: Graph) -> int:
        r"""
        Returns the number of *components* in a graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return int: a positive integer ranging between 1  and *N*, the size of the graph. The maximum value is achieved when the graph consists of isolates.
        """
        return len(graph.components())

    @staticmethod
    @check_graph_consistency
    def density(graph: Graph) -> float:
        r"""
        Computes the *density* of a graph. The density of a graph is defined as the ratio between the actual number of edges :math:`E` and the number of possible
        edges in the graph, :math:`\frac{N(N-1)}{2}`, where :math:`N` is the size of the graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: a positive float value tha ranges between 0 (all isolates) and 1 (graph is complete)
        """

        return round(graph.density(), 5)

    @staticmethod
    @check_graph_consistency
    def pi(graph: Graph) -> float:
        r"""
        Returns *Pi*, the ratio between the total number of edges and the diameter.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: a positive float, the graph's pi
        """
        return round(graph.ecount()/graph.diameter(), 5)

    @staticmethod
    @check_graph_consistency
    def average_clustering_coefficient(graph: Graph) -> float:
        r"""
        Computes the *average clustering coefficient* among all nodes in a graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: a positive float ranging from 0 (all nodes are isolates) tro 1 (graph is complete)
        """
        return round(graph.transitivity_avglocal_undirected(), 5)

    @staticmethod
    @check_graph_consistency
    def weighted_clustering_coefficient(graph: Graph) -> float:
        u"""
        Computes the *weighted clustering coefficient* among all nodes in a graph, defined as the average of each node's clustering coefficient weighted by their degree values.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: a positive float representing the graph's weighted clustering coefficient
        """
        return round(graph.transitivity_undirected(), 5)

    @staticmethod
    @check_graph_consistency
    def average_degree(graph: Graph) -> float:
        r"""
        Returns the *average degree* of the input graph.
        The average degree is the mean of the degree of each node in the graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: a positive float value representing the average degree of the input graph
        """
        return round(mean(graph.degree()), 5)

    @staticmethod
    @check_graph_consistency
    def average_closeness(graph: Graph) -> float:
        u"""
        Returns the *average closeness* of the input graph. This is computed as the mean of each node's closeness.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: a float value representing the average closeness of a graph
        """

        return round(mean(LocalTopology.closeness(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_eccentricity(graph: Graph) -> float:
        u"""
        Returns the *average eccentricity* of the input graph.
        This is done by computing the mean of each node's eccentricity.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return: a float value representing the average eccentricity of a graph
        """

        return round(mean(LocalTopology.eccentricity(graph=graph)), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality(graph: Graph, cmode=CmodeEnum.igraph) -> float:
        r"""
        Computes the *average radiality*, the mean of all node radiality values. See :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality`

        .. warning::  The average radiality calculation is :py:class:`math.inf` if the graph has two or more components, as disconnected nodes have an infinite distance by definition.  For that purpose, we recommend using the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_radiality_reach` method, or subset the graph to take only a component of interest..

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths necessary for each radiality value. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return float: the average of the radiality of all nodes in the graph.

        :raise KeyError: if cmode is not one of the available cmode enumerators
        """
        print(cmode)
        if not isinstance(cmode, CmodeEnum):
            raise KeyError(u"'cmode' not valid, must be one of the following: {}".format(list(CmodeEnum)))
        rad =LocalTopology.radiality(graph, nodes=None, cmode=cmode)

        return round(mean(rad), 5)

    @staticmethod
    @check_graph_consistency
    def average_radiality_reach(graph: Graph, cmode=CmodeEnum.igraph) -> float:
        r"""
        Computes the *average radiality reach*, the mean for all the radiality reach values for each node in the graph. See :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality_reach`.
        Radiality Reach is a modified version of radiality that computes inter-component radiality when the graph has more than one component. If the graph is composed of one component, the average radiality reach equals the average radiality.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param cmodeEnum cmode: the implementation that will be used to compute the shortest paths for each radiality reach value. See :class:`~pyntacle.tools.enums.CmodeEnum`. Default is the igraph brute-force shortest path search.

        :return float: a float representing the average of the radiality reach of all nodes in the graph.

        :raise KeyError: if cmode is not one of the available cmode enumerators
        """

        if not isinstance(cmode, CmodeEnum):
            raise KeyError(u"'cmode' not valid, must be one of the following: {}".format(list(CmodeEnum)))

        return round(mean(LocalTopology.radiality_reach(graph=graph, nodes=None, cmode=cmode)), 5)
