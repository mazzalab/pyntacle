__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t.mazza@css-mendel.it>
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

import sys
from tools.add_attributes import AddAttributes
from algorithms.local_topology import LocalTopology
from algorithms.global_topology import GlobalTopology
from algorithms.shortest_path import ShortestPath
from algorithms.sparseness import Sparseness
from algorithms.keyplayer import KeyPlayer
from tools.enums import *
from math import isinf
from igraph import Graph
from internal.graph_routines import check_graph_consistency
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw


def get_cmode(graph):
    if 'implementation' in graph.attributes():
        return graph["implementation"]
    else:
        return CmodeEnum.igraph


def transform_nodes(nodes):
    r""" Turns a single node name to a list of size 1. Useful for group centrality metrics when using a single node name"""

    if isinstance(nodes, str):
        nodes = [nodes]

    nodes.sort() #sort node names list lexicographically

    return nodes

def add_gc_attributes(graph: Graph, attr_name: str, attr: dict, readd=False):
    r"""
    Reserved method for adding group centrality indices to the whole graph
    """

    if not isinstance(graph, Graph) is not Graph:
        raise TypeError(u"`graph` argument is not a igraph.Graph")

    if not isinstance(attr_name, str):
        raise TypeError(u"Attribute name is not a string")

    if not isinstance(attr, dict):
        raise TypeError(u"`attr` is not a dict")
    if attr_name not in graph.attributes() or graph[attr_name] is None or readd:
        sys.stdout.write("Initializing '{}' attribute.\n".format(attr_name))
        AddAttributes.add_graph_attribute(graph, attr_name, attr)
    else:
        sys.stdout.write("Updating the '{}' attribute.\n".format(attr_name))
        graph[attr_name].update(attr)

class Octopus:
    r"""
    Octopus is a Pyntacle swiss knife tool aimed at using Pyntacle tools and metrics and import them directly into the
    :py:class:`igraph.Graph` object as graph, node or edge attribute.
    """

    # Global properties
    @staticmethod
    @check_graph_consistency
    def diameter(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.diameter` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute``diameter``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write("Calculating diameter and storing in the graph '{}' attribute.\n".format(GlobalAttributeEnum.diameter.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.diameter.name, GlobalTopology.diameter(graph))
        #sys.stdout.write("Diameter successfully added to graph.\n")

    @staticmethod
    @check_graph_consistency
    def radius(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.radius` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph ``radius``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating radius and storing in the graph '{}' attribute.\n".format(GlobalAttributeEnum.radius.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.radius.name, GlobalTopology.radius(graph))
        #sys.stdout.write("Radius successfully added to graph.\n")

    @staticmethod
    @check_graph_consistency
    def components(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.components` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph ``components``.

        .. note:: this method adds the **number** of components, not the components themselves

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating number of components and storing in the graph '{}' attribute.\n".format(GlobalAttributeEnum.components.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.components.name, GlobalTopology.components(graph))

    @staticmethod
    @check_graph_consistency
    def density(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.density` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``density``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating density and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.density.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.density.name, GlobalTopology.density(graph))

    @staticmethod
    @check_graph_consistency
    def pi(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.PI` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``PI``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating pi and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.pi.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.pi.name, GlobalTopology.pi(graph))

    @staticmethod
    @check_graph_consistency
    def average_clustering_coefficient(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_clustering_coefficient` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_clustering_coefficient``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the average clustering coefficient and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_clustering_coefficient.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_clustering_coefficient.name,
                                          GlobalTopology.average_clustering_coefficient(graph))

    @staticmethod
    @check_graph_consistency
    def weighted_clustering_coefficient(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.weighted_clustering_coefficient` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``weighted_clustering_coefficient``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the weighted clustering coefficient and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.weighted_clustering_coefficient.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.weighted_clustering_coefficient.name,
                                          GlobalTopology.weighted_clustering_coefficient(graph))

    @staticmethod
    @check_graph_consistency
    def average_degree(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_degree` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_degree``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the average degree and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_degree.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_degree.name,
                                          GlobalTopology.average_degree(graph))

    @staticmethod
    @check_graph_consistency
    def average_closeness(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_closeness` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_closeness``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the average closeness and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_closeness.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_closeness.name,
                                          GlobalTopology.average_closeness(graph))

    @staticmethod
    @check_graph_consistency
    def average_eccentricity(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_eccentricity` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_eccentricity``

        .. note: if the attribute already exists in  the input graph, it will be overwritten.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the average eccentricity and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_eccentricity.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_eccentricity.name,
                                          GlobalTopology.average_eccentricity(graph))

    @staticmethod
    @check_graph_consistency
    def average_radiality(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_radiality` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_radiality``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        cmode = get_cmode(graph)
        sys.stdout.write(
            "Calculating the average radiality and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_radiality.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_radiality.name,
                                          GlobalTopology.average_radiality(graph, cmode))

    @staticmethod
    @check_graph_consistency
    def average_radiality_reach(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_radiality_reach` method in
        :class:`~pyntacle.algorithms.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_radiality_reach``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        cmode = get_cmode(graph)

        sys.stdout.write(
            "Calculating the average radiality reach and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_radiality_reach.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_radiality_reach.name,
                                          GlobalTopology.average_radiality_reach(graph, cmode))

    @staticmethod
    @check_graph_consistency
    def average_global_shortest_path_length(graph: Graph):
        r"""
        Adds the average among all geodesics of the input :py:class:`~igraph.Graph` object by means of the
        :func:`~pyntacle.algorithms.shortest_path.ShortestPaths.average_global_shortest_path_length`
        and store the value (a :py:class:`float`)
        in the ``average_global_shortest_path_length`` attribute at graph level.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param graph::param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        cmode = get_cmode(graph)
        sys.stdout.write(
            "Calculating the average among all graph geodesics and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.average_global_shortest_path_length.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.average_global_shortest_path_length.name,
                                          ShortestPath.average_global_shortest_path_length(graph, cmode))

    @staticmethod
    @check_graph_consistency
    def median_global_shortest_path_length(graph: Graph):
        r"""
        Adds the median value of all the possible shortest path lengths in the input :py:class:'igraph.Graph' object by
        wrapping the :func:`~pyntacle.algorithms.shortest_path.ShortestPaths.median_global_shortest_path_length` method in
        the :class:`~pyntacle.algorithms` module. It adds the median value as a graph attribute named ``median_global_shortest_path_length``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param graph::param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the median among all graph geodesics and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.median_global_shortest_path_length.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.median_global_shortest_path_length.name,
                                          ShortestPath.median_global_shortest_path_length(graph))

    @staticmethod
    @check_graph_consistency
    def completeness_naive(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.sparseness.Sparseness.completeness_naive` method in
        :class:`~pyntacle.algorithms.sparseness.Sparseness` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``completeness_naive``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        sys.stdout.write(
            "Calculating the naive version of completeness and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.completeness_naive.name))

        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.completeness_naive.name,
                                          Sparseness.completeness_naive(graph))

    @staticmethod
    @check_graph_consistency
    def completeness(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.sparseness.Sparseness.completeness_naive` method in
        :class:`~pyntacle.algorithms.sparseness.Sparseness` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``completeness_naive``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the most recent version of completeness and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.completeness.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.completeness.name,
                                          Sparseness.completeness(graph))

    @staticmethod
    @check_graph_consistency
    def compactness(graph: Graph, correct: bool = False):
        r"""
        Wraps the :func:`~pyntacle.algorithms.sparseness.Sparseness.compactness` method in
        :class:`~pyntacle.algorithms.sparseness.Sparseness` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``compactness``.

        .. note: if the attribute already exists in  the input graph, it will be overwritten

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating compactness and storing in the graph '{}' attribute.\n".format(
                GlobalAttributeEnum.compactness.name))
        AddAttributes.add_graph_attribute(graph, GlobalAttributeEnum.compactness.name,
                                          Sparseness.compactness(graph, correct=correct))

    # Local properties
    @staticmethod
    @check_graph_consistency
    def degree(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.degree` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``degree``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no degree assigned will still hold a ``degree`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating degree for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.degree.name))
        else:
            sys.stdout.write(
                "Calculating degree for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.degree.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.degree.name,
                                         LocalTopology.degree(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def group_degree(graph: Graph, nodes: list or str):
        r"""
        Computes the *group degree* by means of the :func:`~pyntacle.algorithms.local_topology.LocalTopology.group_degree`
        for a set of nodes of the input :py:class:`~igraph.Graph` object. It adds the group degree value for the
        input set of nodes as a graph attribute named ``group_degree_info``. This attribute stores a :py:class:`dict`
        whose ``key``s are tuples, each sorted alphanumerically by vertex ``name`` and the corresponding ``value`` is a
        :py:class:`float` representing the corresponding group degree value for the input nodes.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list, str nodes: a list of strings representing the node name (the vertex ``name`` attribute) matching node names in the graph, or a string representing a single node name.
        """
        nodes = transform_nodes(nodes)
        attr_name = "_".join([GroupCentralityEnum.group_degree.name, "info"])

        sys.stdout.write(
            "Calculating group degree for node set {} and storing in the vertex '{}' attribute.\n".format
            (",".join(nodes), attr_name))

        add_gc_attributes(graph, attr_name,
                         {tuple(sorted(nodes)): LocalTopology.group_degree(graph, nodes)})


    @staticmethod
    @check_graph_consistency
    def betweenness(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.betweenness` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``betweenness``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no betweenness assigned will still hold a ``betweenness`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating (un-normalized) betweenness for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.betweenness.name))

        else:
            sys.stdout.write(
                "Calculating (un-normalized) betweenness for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.betweenness.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.betweenness.name,
                                         LocalTopology.betweenness(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def group_betweenness(graph: Graph, nodes: list or str):
        r"""
        Computes the *group betweenness* by means of the :func:`~pyntacle.algorithms.local_topology.LocalTopology.group_betweenness` Pyntacle method
        for a set of nodes of the input :py:class:`~igraph.Graph` object. It adds the group betweenness value for the
        input set of nodes as a graph attribute named ``group_betweenness_info``. This attribute stores a :py:class:`dict`
        whose ``key``s are tuples, each sorted alphanumerically by vertex ``name`` and the corresponding ``value`` is a
        :py:class:`float` representing the corresponding group betweenness value for the input nodes.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list, str nodes: a list of strings representing the node name (the vertex ``name`` attribute) matching node names in the graph, or a string representing a single node name.
        """
        cmode = get_cmode(graph)

        nodes = transform_nodes(nodes)

        attr_name = "_".join([GroupCentralityEnum.group_betweenness.name, "info"])

        sys.stdout.write(
            "Calculating group betweenness for node set {} and storing in the vertex '{}' attribute.\n".format
            (",".join(nodes), attr_name))

        add_gc_attributes(graph, attr_name,
                         {tuple(sorted(nodes)): LocalTopology.group_betweenness(graph=graph, nodes=nodes, cmode=cmode)})

    @staticmethod
    @check_graph_consistency
    def clustering_coefficient(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.clustering_coefficient` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``clustering_coefficient``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no clustering coefficient assigned will still hold a ``clustering_coefficient`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating clustering coefficient for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.clustering_coefficient.name))

        else:
            sys.stdout.write(
                "Calculating clustering coefficient for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.clustering_coefficient.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.clustering_coefficient.name,
                                         LocalTopology.clustering_coefficient(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def closeness(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.closeness` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``closeness``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no closeness assigned will still hold a ``clustering_coefficient`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating closeness for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.closeness.name))

        else:
            sys.stdout.write(
                "Calculating closeness for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.closeness.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.closeness.name,
                                         LocalTopology.closeness(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def group_closeness(graph: Graph, nodes: str or list, distance: GroupDistanceEnum = GroupDistanceEnum.minimum):
        r"""
        Computes the *group closeness* by means of the :func:`~pyntacle.algorithms.local_topology.LocalTopology.group_closeness` Pyntacle method
        for a set of nodes of the input :py:class:`~igraph.Graph` object. The group closeness can be computed using three possible criterions for defining the distance from the node set to the rest of the graph:

            * *minimum*: the least possible distance the node set and the rest of the graph
            * *mean*: the average distance (shortest path) between any vertex in the node set and the rest of the graph
            * *maximum*: the maximum possible shortest path between the node set and the rest of the graph.

        These options are stored in the :class:`~pyntacle.tools.enums.GroupDistanceEnum`, and passed through the ``distance`` argument.

        The group closeness value is then added as a graph attribute, ``group_closeness_DISTANCE_info`` where DISTANCE is one of the 3 possible distances specified above.
        This attributes contains a :py:class:`dict`  whose ``key``s are tuples, sorted alphanumerically by vertex ``name`` and the corresponding ``value`` is a
        :py:class:`float` representing the corresponding group closenessvalue for the input nodes.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param list, str nodes: a list of strings representing the node name (the vertex ``name`` attribute) matching node names in the graph, or a string representing a single node name.
        :param distance: the criterion to use for defining the distance between the node set and the rest of the graph. Must be one of the option in :class:`~pyntacle.tools.enums.GroupDistanceEnum`. Defaults to ``GroupDistanceEnum.minimum``.
        """
        nodes = transform_nodes(nodes)
        cmode = get_cmode(graph)
        gc_name = "_".join([GroupCentralityEnum.group_closeness.name, distance.name, "info"])

        sys.stdout.write(
            "Calculating group closeness with a {} distance for node set {} and storing in the vertex '{}' attribute.\n"
                .format(",".join(nodes), gc_name, distance.name))

        add_gc_attributes(graph, gc_name ,
                         {tuple(sorted(nodes)): LocalTopology.group_closeness(graph, nodes, distance, cmode)})

    @staticmethod
    @check_graph_consistency
    def eccentricity(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.eccentricity` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``eccentricity``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no eccentricity assigned will still hold a ``eccentricity`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating eccentricity for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.eccentricity.name))

        else:
            sys.stdout.write(
                "Calculating eccentricity for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.eccentricity.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.eccentricity.name,
                                         LocalTopology.eccentricity(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def radiality(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``radiality``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality assigned will still hold a ``radiality`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        cmode = get_cmode(graph)
        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating radiality for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.radiality.name))

        else:
            sys.stdout.write(
                "Calculating radiality for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.radiality.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.radiality.name,
                                         LocalTopology.radiality(graph, nodes, cmode),
                                         nodes)

    @staticmethod
    @check_graph_consistency
    def radiality_reach(graph: Graph, nodes: str or list or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality_reach` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``radiality_reach``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality reach assigned will still hold a ``radiality_reach`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        cmode = get_cmode(graph)
        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating radiality reach for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.radiality_reach.name))

        else:
            sys.stdout.write(
                "Calculating radiality reach for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.radiality_reach.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.radiality_reach.name,
                                         LocalTopology.radiality_reach(graph, nodes, cmode), nodes)

    @staticmethod
    @check_graph_consistency
    def eigenvector_centrality(graph: Graph, nodes: str or list or None = None, scaled: bool = False):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.eigenvector_centrality` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``eigenvector_centrality``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality reach assigned will still hold a ``eigenvector_centrality`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        :param bool scaled: a boolean value to scale the eigenvector centrality using the reciprocal of the eigenvector :math:`\frac{1}{eigenvector}`. ``False` by default.
        """

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating eigenvector centrality for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.eigenvector_centrality.name))

        else:
            sys.stdout.write(
                "Calculating eigenvector centrality for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.eigenvector_centrality.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.eigenvector_centrality.name,
                                         LocalTopology.eigenvector_centrality(graph, nodes, scaled),
                                         nodes)

    @staticmethod
    @check_graph_consistency
    def pagerank(graph: Graph, nodes: str or list or None = None, weights: float or int or None = None,
                 damping: float = 0.85):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.pagerank` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``pagerank``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality reach assigned will still hold a ``eigenvector_centrality`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        :param list, None weights: a list of float numbers less or equal than the total number of edges. The order of the list shoould match the indices of the edge elements of the input graph. Defaults to :py:class:`None` (no weights added).
        :param float damping: positive float representing the probability to reset the random walk distribution at each pagerank iteration. Default is 0.85.
        """

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating pagerank index for nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.pagerank.name))

        else:
            sys.stdout.write(
                "Calculating pagerank index for all nodes and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.pagerank.name))
            nodes = graph.vs["name"]

        if "weights" in graph.es.attributes():
            sys.stdout.write("Adding edge weights under the `weights` attribute.\n")
            weights = graph.es["weights"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.pagerank.name,
                                         LocalTopology.pagerank(graph, nodes, weights, damping),
                                         nodes)

    @staticmethod
    @check_graph_consistency
    def shortest_paths(graph: Graph, nodes: str or list or None = None):
        r"""
        Computes the shortest paths for a node, a group of nodes or all nodes in the :py:class:`igraph.Graph` object by wrapping the
        :func:`~pyntacle.algorithms.shortest_path.ShortestPath.get_shortestpaths` methods in :class:`~pyntacle.algorithms.shortest_path.ShortestPath`
        The shortest paths are added under the vertex attribute ``shortest_paths`` as a :py:class:`list`. The list will
        contain a of positive integers, sorted by vertex index, representing  the geodesic distance among a node :math:`i`
        and any other node :math:`j` in the graph :math:`G`.

        .. note:: The list index corresponding to node :math:`i` will have distance :math:`0`.
        .. note:: the distance between disconnected nodes is a :py:class:`math.inf`, as the distance between disconnected nodes is infinite by definition
        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes that will not be considered for shortest path calculations will still hold a ``shortest_path`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating geodesics stemming from nodes {} and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.shortest_paths.name))

        else:
            sys.stdout.write(
                "Calculating geodesics for all nodes  in the graph and storing in the vertex '{}' attribute.\n".format(
                    LocalAttributeEnum.shortest_paths.name))
            nodes = graph.vs["name"]

        tot_nodes = graph.vcount()

        distances = ShortestPath.get_shortestpaths(graph, nodes, cmode=cmode).astype(float)
        distances[distances >= tot_nodes + 1] = float("inf")
        distances = distances.tolist()  # convert to a list of lists
        # cast everything not infinite to integer
        distances = [[int(x) if not isinf(x) else x for x in y] for y in distances]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.shortest_paths.name, distances, nodes)

    @staticmethod
    @check_graph_consistency
    def average_shortest_path_length(graph: Graph, nodes: str or list or None = None):
        r"""
        Computes the average shortest path length for a node, a group of nodes or all nodes in the input :py:class:`igraph.Graph` object  by wrapping the
        :func:`~pyntacle.algorithms.shortest_path.ShortestPath.average_shortest_path_lengths` methods in :class:`~pyntacle.algorithms.shortest_path.ShortestPath`
        The averages are added under the vertex attribute ``average_shortest_path_lengths`` as a :py:class:`float`.
        The distance from  any input node to itself (0 by definition) is pruned.

        .. note:: if there is no path between nodes in the graphs, their average shortest path length will be :py:class:`~math.inf`
        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes that will not be considered will still hold a ``average_shortest_path`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)
        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating the average distance among each of the nodes {} and the rest of the graph and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.average_shortest_path_length.name))

        else:
            sys.stdout.write(
                "Calculating the average distance each node and the rest of the graph and storing in the vertex '{}' attribute.\n".format
                (LocalAttributeEnum.average_shortest_path_length.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.average_shortest_path_length.name,
                                         ShortestPath.average_shortest_path_lengths(graph, nodes, cmode),
                                         nodes)

    @staticmethod
    @check_graph_consistency
    def median_shortest_path_length(graph: Graph, nodes: str or list or None = None):
        r"""
        Computes the median shortest path starting from a node, a group of nodes or all nodes in a the input :py:class:`igraph.Graph` object towards every other node in the same graph by wrapping the
        :func:`~pyntacle.algorithms.shortest_path.ShortestPath.median_shortest_path_lengths` methods in :class:`~pyntacle.algorithms.shortest_path.ShortestPath`
        The median value for each vertex is added under the attribute ``median_shortest_path_lengths`` as a :py:class:`int`. The distance from  any input node to itself (0 by definition) is pruned.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes that will not be considered for shortest path calculations assigned will still hold a ``median_shortest_path`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)

        if nodes is not None:
            nodes = transform_nodes(nodes)
            sys.stdout.write(
                "Calculating the median distance among each of the nodes {} and the rest of the graph and storing in the vertex '{}' attribute.\n".format
                (",".join(nodes), LocalAttributeEnum.median_shortest_path_length.name))

        else:
            sys.stdout.write(
                "Calculating the median distance each node and the rest of the graph and storing in the vertex '{}' attribute.\n".format
                (LocalAttributeEnum.median_shortest_path_length.name))
            nodes = graph.vs["name"]

        AddAttributes.add_node_attribute(graph, LocalAttributeEnum.median_shortest_path_length.name,
                                         ShortestPath.median_shortest_path_lengths(graph, nodes, cmode),
                                         nodes)

    @staticmethod
    @check_graph_consistency
    def F(graph: Graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.keyplayer.KeyPlayer.F` method that quantifies the *fragmentation* status of the
        network (the input :py:class:`igraph.Graph` object) and embed it in the graph under the graph attribute ``F``. For detailed
        information on the nature of the F index, please refer to the `group centrality guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.1>`_on Pyntacle official website.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        sys.stdout.write(
            "Calculating the Fragmentation status of the graph using the F index and storing in the graph '{}' attribute.\n".format(
                KpnegEnum.F.name))

        AddAttributes.add_graph_attribute(graph, KpnegEnum.F.name, KeyPlayer.F(graph))

    @staticmethod
    @check_graph_consistency
    def dF(graph: Graph, max_distance: int or None = None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.keyplayer.KeyPlayer.dF` method that quantifies the *distance-based-fragmentation* status of the
        network (the input :py:class:`igraph.Graph` object) and embed it in the graph under the graph attribute ``F``. For detailed
        information on the nature of the dF index, please refer to the `group centrality guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.2>`_
        on Pyntacle official website.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        cmode = get_cmode(graph)
        sys.stdout.write(
            "Calculating the Fragmentation status of the graph using the dF (distance-based fragmentation) index and storing in the graph '{}' attribute.\n".format(
                KpnegEnum.F.name))

        AddAttributes.add_graph_attribute(graph, KpnegEnum.dF.name, KeyPlayer.dF(graph, cmode=cmode,
                                                                                 max_distance=max_distance))

    @staticmethod
    @check_graph_consistency
    def kp_F(graph: Graph, nodes: list or str):
        r"""
        Removes a single nodes or a group of nodes, (identified by the vertex ``name`` attribute) belonging to the
        input graph and computes the resulting *fragmentation* (*F*) status of the graph by means of the
        :func:`~pyntacle.algorithms.keyplayer.KeyPlayer.dF` Pyntacle  method when these nodes are removed.

        The fragmentation status after node removal is then wrapped in the ``F_info`` graph attribute, a dictionary
        whose ``key``s are tuple storing the vertex ``name``(s) (sorted alphanumerically) and the corresponding ``value``
        is the F metric of the resulting graph when the nodes are removed.

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `group centrality guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.1>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list nodes: the vertex ``name`` attribute corresponding to node names. It can be either a string specifying a single node name or a list of strings, each one representing a node in the input graph.
        """

        nodes = transform_nodes(nodes)
        kp_name = KpnegEnum.F.name + '_info'
        sys.stdout.write(
            "Removing node set {} from the graph, measuring fragmentation using the F index and storing in the graph '{}' attribute.\n".format(
                ",".join(nodes),
                kp_name))

        kpobj = kpw(graph=graph, nodes=nodes)
        kpobj.run_fragmentation(KpnegEnum.F)
        results_dict = kpobj.get_results()

        add_gc_attributes(graph,
                         kp_name,
                         {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def kp_dF(graph: Graph, nodes: str or list, max_distance=None):
        r"""
        Removes a single nodes or a group of nodes, (identified by the vertex ``name`` attribute) belonging to the input
        graph and computes the resulting *distance-based fragmentation* (*dF*) index by means of the :func:`pyntacle.algorithms.keyplayer.KeyPlayer.dF`
        Pyntacle  method when these nodes are removed.

        The fragmentation status after node removal is then wrapped in the ``dF_info`` graph attribute, a dictionary
        whose ``key``s are tuple (sorted alphanumerically) storing the vertex ``name``(s) and the corresponding ``value``
        is the dF value of the resulting graph when the nodes are removed.

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `group centrality guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.2>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list nodes: the vertex ``name`` attribute corresponding to node names. It can be either a string specifying a single node name or a list of strings, each one representing a node in the input graph.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        cmode = get_cmode(graph)
        nodes = transform_nodes(nodes)
        kp_name = KpnegEnum.dF.name + '_info'
        sys.stdout.write(
            "Removing node set {} from the graph, measuring fragmentation using the dF index and storing in the graph '{}' attribute.\n".format(
                ",".join(nodes),
                kp_name))
        kpobj = kpw(graph=graph, nodes=nodes)
        kpobj.run_fragmentation(KpnegEnum.dF, max_distance=max_distance, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph,
                         kp_name,
                         {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def kp_dR(graph: Graph, nodes: str or list, max_distance=None):
        r"""
        Computes the distance-weighted reach (*dR*) for a given *key player* set (kp-set).
        by means of the :func:`~pyntacle.algorithms.keyplayer.KeyPlayer.dR` Pyntacle  method.

        The fragmentation status after node removal is then wrapped in the ``dR_info`` graph attribute,
        a dictionary whose ``key``s are tuple (sorted alphanumerically) storing the vertex ``name``(s)
        and the corresponding ``value`` is the dR for the input set of nodes.

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `group centrality guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.3.2>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list nodes: the vertex ``name`` attribute corresponding to node names. It can be either a string specifying a single node name or a list of strings, each one representing a node in the input graph.each one representing a node in the graph.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """

        cmode = get_cmode(graph)
        nodes = transform_nodes(nodes)
        kp_name = KpposEnum.dR.name + '_info'

        sys.stdout.write(
            "Measuring reachability of the node set {} using the dR index and storing in the graph '{}' attribute.\n".format(
                ",".join(nodes), kp_name))

        kpobj = kpw(graph=graph, nodes=nodes)
        kpobj.run_reachability(KpposEnum.dR, max_distance=max_distance, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, kp_name,
                         {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def kp_mreach(graph: Graph, nodes: str or list, m: int, max_distance: int or None = None):
        r"""
        Computes the *m-reach* metric for a given *key player* set (kp-set). Nodes are identified by the vertex ``name`` attribute and must belong to the input graph and computes the resulting dR value of these nodes in the graph by means of the :func:`~pyntacle.algorithms.keyplayer.KeyPlayer.dR` Pyntacle  method.

        The fragmentation status after node removal is then wrapped in the ``mreach_m_kpinfo`` graph attribute, where ``m`` is the maximum m-reach distance.

        This attribute points to a dictionary whose keys are tuple storing the vertex ``name``(s) and the corresponding value is the m-reach for the input nodes

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `group centrality guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.3.2>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param int m: The number of steps of the m-reach algorithm.
        :param str,list nodes: the vertex ``name`` attribute corresponding to node names. It can be either a string specifying a single node name or a list of strings, each one representing a node in the input graph.
        """
        cmode = get_cmode(graph)

        nodes = transform_nodes(nodes)

        kpobj = kpw(graph=graph, nodes=nodes)
        kpobj.run_reachability(KpposEnum.mreach, m=m, max_distance=max_distance, cmode=cmode)
        results_dict = kpobj.get_results()
        kp_name = KpposEnum.mreach.name + '_{}_info'.format(str(m))

        sys.stdout.write(
            "Measuring reachability of the node set {} using m-reach with a a max distance of {} and storing in the graph '{}' attribute.\n".format(
                ",".join(nodes), m, kp_name))

        add_gc_attributes(graph,
                         kp_name, {
                             tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][
                                 1]})

    # Greedy optimization
    @staticmethod
    @check_graph_consistency
    def GO_F(graph: Graph, k: int, seed: int or None = None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *fragmentation* (*F*) index. It does so by wrapping the :func:`~algorithms.greedy_optimization.GreedyOptimization.fragmentation`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``F_greedy``
        This dictionary contains tuples storing the found node names (the vertex ``name`` attribute for each node) as ``key``s
        and the corresponding F value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """
        kpobj = gow(graph=graph)
        kp_name = KpnegEnum.F.name + '_greedy'
        sys.stdout.write("Finding an optimal node set of size {} for the fragmentation index {} with a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(k, KpnegEnum.F.name,kp_name))
        kpobj.run_fragmentation(k, KpnegEnum.F, seed=seed)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph,kp_name,
                         {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def GO_dF(graph: Graph, k: int, max_distance: int or None = None, seed: int or None = None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *distance-based fragmentation* (*dF*) index. It does so by wrapping the :func:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization.fragmentation`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``dF_greedy``
        This dictionary contains tuples storing the found node names (the vertex ``name`` attribute for each node) as ``key``s
        and the corresponding dF value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the greedy optimization.

        .. warning:: This method is computationally-intensive and can take a lot of time according to the graph size and the :math:`k` size.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: The size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kp_name = KpnegEnum.dF.name + '_greedy'
        sys.stdout.write(
            "Finding an optimal node set of size {} for the fragmentation index {} with a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(
                k, KpnegEnum.dF.name, kp_name))
        kpobj.run_fragmentation(k, KpnegEnum.dF, max_distance=max_distance, seed=seed, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph,
                         kp_name,
                         {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def GO_dR(graph: Graph, k: int, max_distance: int or None = None, seed: int or None = None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *distance-weighted reach* (*dR*) index. It does so by wrapping the :func:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization.reachability`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``dR_greedy``
        This dictionary tuples storing the found node names (the vertex ``name`` attribute for each node) as ``key``s
        and the corresponding dR value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: The size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kp_name = KpposEnum.dR.name + '_greedy'
        sys.stdout.write(
            "Finding an optimal node set of size {} for the reachability index {} with a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(
                k, KpposEnum.dR.name, kp_name))
        kpobj.run_reachability(k, KpposEnum.dR, max_distance=max_distance, seed=seed, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, kp_name,
                         {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def GO_mreach(graph: Graph, k: int, m: int or None = None, max_distance: int or None = None,
                  seed: int or None = None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *distance-weighted reach* (*m-reach*) index. It does so by wrapping the :func:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization.reachability`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``mreach_m_greedy``,
        where ``m`` is the maximum m-reach distance.
        This dictionary contains tuples storing the found node names (the vertex ``name`` attribute for each node) as ``key``s
        and the corresponding m-reach value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the m-reach index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int m: the number of steps of the m-reach algorithm.
        :param int,None max_distance: the maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param seed: :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kp_name = KpposEnum.mreach.name + '_{}_greedy'.format(str(m))
        sys.stdout.write(
            "Finding an optimal node set of size {} for reachability index m-reach with a distance of {} using a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(
                k, m, kp_name))
        kpobj.run_reachability(k, KpposEnum.mreach, m=m, max_distance=max_distance, seed=seed, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph,kp_name, {
                             tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][
                                 1]})

    @staticmethod
    @check_graph_consistency
    def GO_group_degree(graph: Graph, k: int, seed: int or None = None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal node set of size :math:`k` for  group
        degree. It does so by wrapping the :func:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization.groupcentrality`
        Pyntacle method. It then stores the found node set in a dictionary that is embedded in the graph attribute ``group_degree_greedy``.

        This dictionary has ``key``s corresponding to the found node set as a :py:class:`tuple` of node names (the vertex ``name`` attribute)
        and the corresponding group degree score as ``value``. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the node set. Must be a positive integer.
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        kpobj = gow(graph=graph)
        kpobj.run_groupcentrality(k, GroupCentralityEnum.group_degree, seed=seed)
        gc_name = GroupCentralityEnum.group_degree.name + '_greedy'
        sys.stdout.write(
            "Finding an optimal node set of size {} for the group degree index using a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(
                k, gc_name))
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, gc_name  ,
                         {tuple(sorted(results_dict[GroupCentralityEnum.group_degree.name][0])):
                              results_dict[GroupCentralityEnum.group_degree.name][1]})

    @staticmethod
    @check_graph_consistency
    def GO_group_betweeness(graph: Graph, k: int, seed: int or None = None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal node set of size :math:`k` for  group
        betweenness. It does so by wrapping the :func:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization.groupcentrality`
        Pyntacle method . It then stores the found node set in a dictionary that is embedded in the graph attribute ``group_betweenness_greedy``.

        This dictionary has ``key``s corresponding to the found node set as a :py:class:`tuple` of node names (the vertex ``name`` attribute)
        and the corresponding group betweenness score as ``value``. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the node set. Must be a positive integer.
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        gc_name = GroupCentralityEnum.group_betweenness.name + '_greedy'
        sys.stdout.write(
            "Finding an optimal node set of size {} for the group betweenness index using a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(
                k, gc_name))
        kpobj.run_groupcentrality(k, GroupCentralityEnum.group_betweenness, seed=seed, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, gc_name,
                         {tuple(sorted(results_dict[GroupCentralityEnum.group_betweenness.name][0])):
                              results_dict[GroupCentralityEnum.group_betweenness.name][1]})

    @staticmethod
    @check_graph_consistency
    def GO_group_closeness(graph: Graph, k: int, seed: int or None = None,
                           distance: GroupDistanceEnum = GroupDistanceEnum.minimum):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal node set of size :math:`k` for  group
        closeness. It does so by wrapping the :func:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization.groupcentrality`
        Pyntacle method. It then stores the found node set in a dictionary that is embedded in the graph attribute ``group_betweenness_DISTANCE_greedy``.
        where DISTANCE is one of the possible :class:`~pyntacle.tools.enums.GroupDistanceEnums` that is necessary to compute the distance
        between the :math:`k` set and the rest of the graph.
        This dictionary has ``key``s corresponding to the found node set as a :py:class:`tuple` of node names (the vertex ``name`` attribute)
        and the corresponding group betweenness score as ``value``. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the node set. Must be a positive integer.
        :param distance: the criterion to use for defining the distance between the node set and the rest of the graph. Must be one of the option in :class:`~pyntacle.tools.enums.GroupDistanceEnum`. Defaults to ``GroupDistanceEnum.minimum``.
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        gc_name = GroupCentralityEnum.group_closeness.name + "_" + distance.name + '_greedy'
        sys.stdout.write(
            "Finding an optimal node set of size {} for the group closensss index calculated with a {} distance using a greedily-optimized search and storing the set and its value in the '{}' attribute.\n".format(
                k, distance.name, gc_name))
        kpobj.run_groupcentrality(k, GroupCentralityEnum.group_betweenness, seed=seed, cmode=cmode, distance=distance)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, gc_name,
                         {tuple(sorted(results_dict[GroupCentralityEnum.group_closeness.name][0])):
                              results_dict[GroupCentralityEnum.group_closeness.name][1]})

    # Brute-force optimization
    @staticmethod
    @check_graph_consistency
    def BF_F(graph: Graph, k: int, max_distance: int or None = None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set (or sets) of nodes of size :math:`k` for the
        *fragmentation* (*F*) index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.fragmentation`
        Pyntacle method. It then stores the found sets in a dictionary that is embedded in the graph attribute ``F_bruteforce``
        This dictionary contains tuples of tuples, each storing the node names (the vertex ``name`` attribute for
        each node) of each possible solution as ``key``and the maximum F index achieved for the given :math:`k` as ``value``.

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the brute-force search.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """

        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(k, KpnegEnum.F, max_distance=max_distance)
        kp_name = KpnegEnum.F.name + '_bruteforce'
        sys.stdout.write(
            "Finding the best node set(s) of size {} for fragmentation index {} using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, KpnegEnum.F.name, kp_name))
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, KpnegEnum.F.name + '_bruteforce',
                         {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.F.name][0]):
                              results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def BF_dF(graph: Graph, k: int, max_distance: int or None = None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set (or sets) of nodes of size :math:`k` for the
        *distance-based fragmentation* (*dF*) index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.fragmentation`
        Pyntacle method. It then stores the found sets in a dictionary that is embedded in the graph attribute ``dF_bruteforce``.
        This dictionary contains tuples of tuples, each storing the node names (the vertex ``name`` attribute for
        each node) as ``key`s and the maximum dF value for the given :math:`k` as ``value``

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the dF index and the brute-force search.

        .. warning:: This method is computationally-intensive and can take a lot of time according to the graph size and the :math:`k` size.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """

        cmode = get_cmode(graph)
        kpobj = bfw(graph=graph)
        kp_name = KpnegEnum.dF.name + '_bruteforce'
        sys.stdout.write(
            "Finding the best node set(s) of size {} for fragmentation index {} using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, KpnegEnum.dF.name, kp_name))
        kpobj.run_fragmentation(k, KpnegEnum.dF, max_distance=max_distance, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, kp_name,
                         {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.dF.name][0]):
                              results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def BF_dR(graph: Graph, k: int, max_distance: int or None = None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set (or sets) of nodes of size :math:`k` for the
        *distance-weighted reach* (*dR*) index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.reachability`
        Pyntacle method. It then stores the found sets in a dictionary that is embedded in the graph attribute ``dR_bruteforce``
        This dictionary contains tuples of tuples, each storing the node names (the vertex ``name`` attribute for
        each node) of each possible solution as ``key``, containing all the possible solution of a ``k`` size that maximize the dR index, and the
        maximum dR index achieved as ``value``

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the dR index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        cmode = get_cmode(graph)
        kpobj = bfw(graph=graph)
        kp_name = KpnegEnum.dR.name + '_bruteforce'
        sys.stdout.write(
            "Finding the best node set(s) of size {} for reachability index {} using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, KpnegEnum.dR.name, kp_name))
        kpobj.run_reachability(k, KpposEnum.dR, max_distance=max_distance, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, kp_name,
                         {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.dR.name][0]):
                              results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def BF_mreach(graph: Graph, k: int, m: int or None = None, max_distance: int or None = None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set (or sets)  of nodes of size :math:`k` for the
        *m-reach* index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.reachability`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``mreach_bruteforce_m``,
        where *m* is the maximum m-reach distance. This attribute points to a dictionary whose ``key``s are tuple of tuples each storing the node names (the vertex ``name`` attribute for
        each node) of each possible solution and the maximum m-reach value achieved as ``value``

        We recommend visiting the `Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the dR index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int m: The number of steps of the m-reach algorithm.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        cmode = get_cmode(graph)
        kpobj = bfw(graph=graph)
        kp_name = KpposEnum.mreach.name + '_{}_bruteforce'.format(str(m))
        sys.stdout.write(
            "Finding the best node set(s) of size {} for reachability index m-reach with a maximum distance of {} using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, m, kp_name))
        kpobj.run_reachability(k, KpposEnum.mreach, max_distance=max_distance, m=m, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, kp_name,
                         {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.mreach.name][0]):
                              results_dict[KpposEnum.mreach.name][1]})

    @staticmethod
    @check_graph_consistency
    def BF_group_degree(graph: Graph, k: int):
        r"""
        Performs a brute-force search on the input graph to search the best node set (or sets) of size :math:`k` for the
        *group degree* index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.group_centrality`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``group_degree_bruteforce``,
        This dictionary contains tuples of tuples as ``key``s, each storing the node names (the vertex ``name`` attribute)
        of all the sets that achieve the best group degree score and the group degree score as ``value``.

        :param graph: igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param k: the size of the node set. Must be a positive integer."""

        kpobj = bfw(graph=graph)
        gc_name = GroupCentralityEnum.group_degree.name + '_bruteforce'
        sys.stdout.write(
            "Finding the best node set(s) of size {} for group degree using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, gc_name))
        kpobj.run_groupcentrality(k, GroupCentralityEnum.group_degree)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, gc_name,
                         {tuple(tuple(sorted(x)) for x in results_dict[GroupCentralityEnum.group_degree.name][0]):
                              results_dict[GroupCentralityEnum.group_degree.name][1]})

    @staticmethod
    @check_graph_consistency
    def BF_group_betweenness(graph: Graph, k: int):
        r"""
        Performs a brute-force search on the input graph to search the best node set (or sets) of size :math:`k` for the
        *group betweenness* index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.group_centrality`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``group_betweenness_bruteforce``,
        This dictionary contains tuples of tuples as ``key``s, each storing the node names (the vertex ``name`` attribute)
        of all the sets that achieve the best group betweenness score, and the group betweenness score as ``value``.

        :param graph: igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param k: the size of the node set. Must be a positive integer.
        """

        cmode = get_cmode(graph)
        kpobj = bfw(graph=graph)
        gc_name = GroupCentralityEnum.group_betweenness.name + '_bruteforce'
        sys.stdout.write(
            "Finding the best node set(s) of size {} for group betweenness using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, gc_name))
        kpobj.run_groupcentrality(k, GroupCentralityEnum.group_betweenness, cmode=cmode)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, GroupCentralityEnum.group_betweenness.name + '_bruteforce',
                         {tuple(tuple(sorted(x)) for x in results_dict[GroupCentralityEnum.group_betweenness.name][0]):
                              results_dict[GroupCentralityEnum.group_betweenness.name][1]})

    @staticmethod
    @check_graph_consistency
    def BF_group_closeness(graph: Graph, k: int, distance: GroupDistanceEnum = GroupDistanceEnum.minimum):
        r"""
        Performs a brute-force search on the input graph to search the best node set (or sets) of size :math:`k` for the
        *group_closeness* index. It does so by wrapping the :func:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch.group_centrality`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``group_closeness_DISTANCE__bruteforce``,
        where DISTANCE is the appropriate :class:`~pyntacle.tools.enums.GroupDistanceEnum` used for computing group closeness.
        This dictionary contains tuples of tuples as ``key``s, each storing the node names (the vertex ``name`` attribute)
        of all the sets that achieve the best group closeness score, and the group closeness score as ``value``.

        :param graph: igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param k: the size of the node set. Must be a positive integer.
        :param distance: the criterion to use for defining the distance between the node set and the rest of the graph. Must be one of the option in :class:`~pyntacle.tools.enums.GroupDistanceEnum`. Defaults to ``GroupDistanceEnum.minimum``.
        """
        cmode = get_cmode(graph)
        kpobj = bfw(graph=graph)
        gc_name = GroupCentralityEnum.group_closeness.name + "_" + distance.name + '_bruteforce'
        sys.stdout.write(
            "Finding the best node set(s) of size {} for group closeness with a {} distance using a brute-force search and storing the set(s) and its value in the '{}' attribute.\n".format(
                k, distance.name, gc_name))
        kpobj.run_groupcentrality(k, GroupCentralityEnum.group_closeness, cmode=cmode, distance=distance)
        results_dict = kpobj.get_results()
        add_gc_attributes(graph, gc_name,
                         {tuple(tuple(sorted(x)) for x in results_dict[GroupCentralityEnum.group_closeness.name][0]):
                              results_dict[GroupCentralityEnum.group_closeness.name][1]})
