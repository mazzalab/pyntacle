__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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


from tools.add_attributes import AddAttributes
from algorithms.local_topology import LocalTopology
from algorithms.global_topology import GlobalTopology
from algorithms.shortest_path import ShortestPath
from algorithms.sparseness import Sparseness
from algorithms.keyplayer import KeyPlayer
from tools.enums import *
from math import isinf
from internal.graph_routines import check_graph_consistency
from internal.shortest_path_modifications import ShortestPathModifier
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw


def get_cmode(graph):
    if '__implementation' in graph.attributes():
        return graph["__implementation"]
    else:
        return CmodeEnum.igraph
    
    
class Octopus:
    r"""
    Octopus is a Pyntacle swiss knife tool aimed at using Pyntacle tools and metrics and import them directly into the
    :py:class:`igraph.Graph` object as graph, node or edge attribute.
    """

    # Global properties
    @staticmethod
    @check_graph_consistency
    def add_diameter(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.diameter` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute``diameter``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph ,GlobalAttributeEnum.diameter.name, GlobalTopology.diameter(graph))

    @staticmethod
    @check_graph_consistency
    def add_radius(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.radius` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph ``radius``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.radius.name, GlobalTopology.radius(graph))

    @staticmethod
    @check_graph_consistency
    def add_components(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.components` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph ``components``

        .. note:: this method adds the **number** of components, not the components themselves

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.components.name, GlobalTopology.components(graph))

    @staticmethod
    @check_graph_consistency
    def add_density(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.density` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``density``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.density.name, GlobalTopology.density(graph))

    @staticmethod
    @check_graph_consistency
    def add_pi(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.PI` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``PI``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.pi.name, GlobalTopology.pi(graph))

    @staticmethod
    @check_graph_consistency
    def add_average_clustering_coefficient(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_clustering_coefficient` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_clustering_coefficient``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_clustering_coefficient.name,
                                                  GlobalTopology.average_clustering_coefficient(graph))

    @staticmethod
    @check_graph_consistency
    def add_weighted_clustering_coefficient(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.weighted_clustering_coefficient` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``weighted_clustering_coefficient``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.weighted_clustering_coefficient.name,
                                                  GlobalTopology.weighted_clustering_coefficient(graph))

    @staticmethod
    @check_graph_consistency
    def add_average_degree(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_degree` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_degree``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_degree.name,
                                                  GlobalTopology.average_degree(graph))

    @staticmethod
    @check_graph_consistency
    def add_average_closeness(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_closeness` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_closeness``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_closeness.name,
                                                  GlobalTopology.average_closeness(graph))

    @staticmethod
    @check_graph_consistency
    def add_average_eccentricity(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_eccentricity` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_eccentricity``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_eccentricity.name,
                                                  GlobalTopology.average_eccentricity(graph))

    @staticmethod
    @check_graph_consistency
    def add_average_radiality(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_radiality` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_radiality``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        cmode = get_cmode(graph)
        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_radiality.name,
                                                  GlobalTopology.average_radiality(graph, cmode))

    @staticmethod
    @check_graph_consistency
    def add_average_radiality_reach(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_radiality_reach` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_radiality_reach``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        cmode = get_cmode(graph)
        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_radiality_reach.name,
                                                  GlobalTopology.average_radiality_reach(graph, cmode))

    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.shortest_path.ShortestPath.average_shortest_path_length` method in
        :class:`~pyntacle.algorithm.shortest_path.ShortestPath` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_shortest_path_length``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        cmode = get_cmode(graph)
        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.average_shortest_path_length.name,
                                                  ShortestPath.average_global_shortest_path_length(
                                                      graph, cmode))

    @staticmethod
    @check_graph_consistency
    def add_completeness_naive(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.sparseness.Sparseness.completeness_naive` method in
        :class:`~pyntacle.algorithm.sparseness.Sparseness` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``completeness_naive``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.completeness_naive.name,
                                                  Sparseness.completeness_naive(graph))

    @staticmethod
    @check_graph_consistency
    def add_completeness(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.sparseness.Sparseness.completeness_naive` method in
        :class:`~pyntacle.algorithm.sparseness.Sparseness` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``completeness_naive``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.completeness.name,
                                                  Sparseness.completeness(graph))

    @staticmethod
    @check_graph_consistency
    def add_compactness(graph, correct: bool =False):
        r"""
        Wraps the :func:`~pyntacle.algorithms.sparseness.Sparseness.compactness` method in
        :class:`~pyntacle.algorithm.sparseness.Sparseness` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``compactness``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        """
        AddAttributes.add_graph_attributes(graph, GlobalAttributeEnum.compactness.name,
                                                  Sparseness.compactness(graph, correct=correct))

    # Local properties
    @staticmethod
    @check_graph_consistency
    def add_degree(graph, nodes: str or list or None =None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.degree` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``degree``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no betweenness assigned will still exhibit a ``betweenness`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.degree.name,
                                                 LocalTopology.degree(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def add_betweenness(graph, nodes: str or list or None=None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.betweenness` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``betweenness``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no betweenness assigned will still exhibit a ``betweenness`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.betweenness.name,
                                                 LocalTopology.betweenness(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def add_clustering_coefficient(graph, nodes: str or list or None=None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.clustering_coefficient` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``clustering_coefficient``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no clustering coefficient assigned will still exhibit a ``clustering_coefficient`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.clustering_coefficient.name,
                                                 LocalTopology.clustering_coefficient(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def add_closeness(graph, nodes: str or list or None=None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.closeness` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``closeness``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no closeness assigned will still exhibit a ``clustering_coefficient`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.closeness.name,
                                                 LocalTopology.closeness(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def add_eccentricity(graph, nodes: str or list or None=None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.eccentricity` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``eccentricity``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no eccentricity assigned will still exhibit a ``eccentricity`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.eccentricity.name,
                                                 LocalTopology.eccentricity(graph, nodes), nodes)

    @staticmethod
    @check_graph_consistency
    def add_radiality(graph, nodes: str or list or None=None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``radiality``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality assigned will still exhibit a ``radiality`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        cmode = get_cmode(graph)
        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.radiality.name,
                                                 LocalTopology.radiality(graph, nodes, cmode),
                                                 nodes)

    @staticmethod
    @check_graph_consistency
    def add_radiality_reach(graph, nodes: str or list or None=None):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.radiality_reach` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``radiality_reach``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality reach assigned will still exhibit a ``radiality_reach`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """

        cmode = get_cmode(graph)
        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.radiality_reach.name,
                                                 LocalTopology.radiality_reach(graph, nodes, cmode), nodes)

    @staticmethod
    @check_graph_consistency
    def add_eigenvector_centrality(graph, nodes: str or list or None=None, scaled: bool=False):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.eigenvector_centrality` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``eigenvector_centrality``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality reach assigned will still exhibit a ``eigenvector_centrality`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        :param bool scaled: a boolean value to scale the eigenvector centrality using the reciprocal of the eigenvector :math:`\frac{1}{eigenvector}`. ``False` by default.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.eigenvector_centrality.name,
                                                 LocalTopology.eigenvector_centrality(graph, nodes, scaled),
                                                 nodes)

    @staticmethod
    @check_graph_consistency
    def add_pagerank(graph, nodes: str or list or None=None, weights: float or int or None =None, damping: float =0.85):
        r"""
        Wraps the :func:`~pyntacle.algorithms.local_topology.LocalTopology.pagerank` method in
        :class:`~pyntacle.algorithms.local_topology.LocalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object vertices, under the attribute name ``pagerank``.

        .. note:: The metric can be added either to all nodes on the graph or to a subset of nodes. In the latter, nodes with no radiality reach assigned will still exhibit a ``eigenvector_centrality`` attribute, but it will be empty.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        :param list, None weights: a list of float numbers less or equal than the total number of edges. The order of the list shoould match the indices of the edge elements of the input graph. Defaults to :py:class:`None` (no weights added).
        :param float damping: positive float representing the probability to reset the random walk distribution at each pagerank iteration. Default is 0.85.
        """

        if nodes is None:
            nodes = graph.vs["name"]
        if "weights" in graph.es.attributes():
            weights = graph.es["weights"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.pagerank.name,
                                                 LocalTopology.pagerank(graph, nodes, weights, damping),
                                                 nodes)

    @staticmethod
    @check_graph_consistency
    def add_shortest_paths(graph, nodes: str or list or None=None):
        r"""
        Computes the shortest paths for a node, a group of nodes or all nodes in the :py:class:`igraph.Graph` object by wrapping the
        :func:`~algorithms.shortest_path.ShortestPath.get_shortestpaths` methods in :class:`~pyntacle.algorithms.shortest_path.ShortestPath`
        The shortest paths are added under the vertex attribute ``shortest_paths`` as a :py:class:`list`. The list will
        contain a of positive integers, sorted by vertex index, representing  the geodesic distance among a node :math:`i`
        and any other node :math:`j` in the graph :math:`G`.

        .. note:: The list index corresponding to node :math:`i` will have distance :math:`0`.
        .. note:: the distance between disconnected nodes is a :py:class:`math.inf`, as the distance between disconnected nodes is infinite by definition

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)

        if nodes is None:
            nodes = graph.vs["name"]

        tot_nodes = graph.vcount()

        distances = ShortestPath.get_shortestpaths(graph, nodes, cmode=cmode).astype(float)
        distances[distances >= tot_nodes + 1] = float("inf")
        distances = distances.tolist() #convert to a list of lists
        #cast everything not infinite to integer
        distances = [[int(x) if not isinf(x) else x for x in y] for y in distances]

        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.shortest_paths.name, distances, nodes)

    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph, nodes: str or list or None=None):
        r"""
        Computes the average shortest path length for a node, a group of nodes or all nodes in the input :py:class:`igraph.Graph` object  by wrapping the
        :func:`~algorithms.shortest_path.ShortestPath.average_shortest_path_lengths` methods in :class:`~pyntacle.algorithms.shortest_path.ShortestPath`
        The averages are added under the vertex attribute ``average_shortest_path_lengths`` as a :py:class:`float`.
        The distance from  any input node to itself (0 by definition) is pruned.

        .. note:: if there is no path between nodes in the graphs, their average shortest path length will be :py:class:`~math.inf`

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)
        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.average_shortest_path_length.name,
                                                 ShortestPath.average_shortest_path_lengths(graph, nodes, cmode),
                                                 nodes)

    @staticmethod
    @check_graph_consistency
    def add_median_shortest_path_length(graph, nodes: str or list or None=None):
        r"""
        Computes the median shortest path length for a node, a group of nodes or all nodes in the input :py:class:`igraph.Graph` object  by wrapping the
        :func:`~algorithms.shortest_path.ShortestPath.median_shortest_path_lengths` methods in :class:`~pyntacle.algorithms.shortest_path.ShortestPath`
        The median value for each vertex is added under the attribute ``median_shortest_path_lengths`` as a :py:class:`int`. The distance from  any input node to itself (0 by definition) is pruned.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)
        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes.add_node_attributes(graph, LocalAttributeEnum.median_shortest_path_length.name,
                                                 ShortestPath.median_shortest_path_lengths(graph, nodes, cmode),
                                                 nodes)

    # Topology metrics
    @staticmethod
    @check_graph_consistency
    def add_F(graph):
        r"""
        Wraps the :func:`~algorithms.keyplayer.KeyPlayer.F` method that quantifies the *fragmentation* status of the
        network (the input :py:class:`igraph.Graph` object) and embed it in the graph under the graph attribute ``F``. For detailed
        information on the nature of the F index, please refer to the `Key Player Metrics Guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.1>`_on Pyntacle official website.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        AddAttributes.add_graph_attributes(graph, KpnegEnum.F.name, KeyPlayer.F(graph))

    @staticmethod
    @check_graph_consistency
    def add_dF(graph, max_distance: int or None=None):
        r"""
        Wraps the :func:`~algorithms.keyplayer.KeyPlayer.dF` method that quantifies the *distance-based-fragmentation* status of the
        network (the input :py:class:`igraph.Graph` object) and embed it in the graph under the graph attribute ``F``. For detailed
        information on the nature of the dF index, please refer to the `Key Player Metrics Guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.2>`_
        on Pyntacle official website.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        cmode = get_cmode(graph)
        AddAttributes.add_graph_attributes(graph, KpnegEnum.dF.name, KeyPlayer.dF(graph, cmode=cmode,
                                                                                  max_distance=max_distance))

    @staticmethod
    @check_graph_consistency
    def add_kp_F(graph, nodes: str or list or None):
        r"""
        Removes a single nodes or a group of nodes, (identified by the vertex ``name`` attribute) belonging to the input graph and computes the resulting *fragmentation* (*F*) index index by means of the :func:`~algorithms.keyplayer.KeyPlayer.dF` Pyntacle  method when these nodes are removed.

        The fragmentation status after node removal is then wrapped in the ``F_kpinfo`` graph attribute, a dictionary whose keys are tuple storing the vertex ``name``(s) and the corresponding value is the F metric of the resulting graph when the nodes are removed.

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `Key Player Metrics Guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.1>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KpnegEnum.F)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpnegEnum.F.name + '_kpinfo', {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dF(graph, nodes: str or list or None, max_distance=None):
        r"""
        Removes a single nodes or a group of nodes, (identified by the vertex ``name`` attribute) belonging to the input graph and computes the resulting *distance-based fragmentation* (*dF*) index by means of the :func:`~algorithms.keyplayer.KeyPlayer.dF` Pyntacle  method when these nodes are removed.

        The fragmentation status after node removal is then wrapped in the ``dF_kpinfo`` graph attribute, a dictionary whose keys are tuple storing the vertex ``name``(s) and the corresponding value is the dF value of the resulting graph when the nodes are removed.

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `Key Player Metrics Guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.1.2>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        cmode = get_cmode(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KpnegEnum.dF, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpnegEnum.dF.name + '_kpinfo',
            {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dR(graph, nodes: str or list or None, max_distance=None):
        r"""
        Computes the distance-weighted reach (*dR*) for a given *key player* set (kp-set). Nodes are identified by the vertex ``name`` attribute and must belong to the input graph and computes the resulting dR value of these nodes in the graph by means of the :func:`~algorithms.keyplayer.KeyPlayer.dR` Pyntacle  method.

        The fragmentation status after node removal is then wrapped in the ``dR_kpinfo`` graph attribute, a dictionary whose keys are tuple storing the vertex ``name``(s) and the corresponding value is value is the dR for the input nodes.

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `Key Player Metrics Guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.3.2>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """

        cmode = get_cmode(graph)

        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KpposEnum.dR, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpposEnum.dR.name + '_kpinfo',
            {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_mreach(graph, nodes: str or list or None, m: int or None=None, max_distance: int or None=None):
        r"""
        Computes the *m-reach* metric for a given *key player* set (kp-set). Nodes are identified by the vertex ``name`` attribute and must belong to the input graph and computes the resulting dR value of these nodes in the graph by means of the :func:`~algorithms.keyplayer.KeyPlayer.dR` Pyntacle  method.

        The fragmentation status after node removal is then wrapped in the ``mreach_kpinfo`` graph attribute, a dictionary whose keys are tuple storing the vertex ``name``(s) and the corresponding value is the mreach for the input nodes

        This method encompasses the same procedure performed by the ``pyntacle key-player kp-info`` command on Pyntacle command line.

        For detailed information on the nature of the dF index, please refer to the `Key Player Metrics Guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html#2.3.2>`_

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param int m: The number of steps of the m-reach algorithm.
        :param str,list,None nodes: the vertex ``name`` attribute corresponding to node names. If :py:class:`None`, it adds the selected metric to all nodes in the graph. Otherwise, it can be either a string specifying a single node name or a list of strings, each one representing a node in the graph.
        """
        cmode = get_cmode(graph)

        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KpposEnum.mreach, m=m, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_kpinfo'.format(str(m))
        AddAttributes.add_graph_attributes(graph,
            attr_name, {tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][1]})

    # Greedy optimization
    @staticmethod
    @check_graph_consistency
    def add_GO_F(graph, k: int, seed: int or None=None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *fragmentation* (*F*) index. It does so by wrapping the :func:`~algorithms.greedy_optimization.GreedyOptimization.fragmentation`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``F_greedy``
        This dictionary contains as keys tuples storing the found node names (the vertex ``name`` attribute for each node)
        and the corresponding F value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(k, KpnegEnum.F, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpnegEnum.F.name + '_greedy', {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dF(graph, k: int, max_distance: int or None=None, seed: int or None=None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *distance-based fragmentation* (*dF*) index. It does so by wrapping the :func:`~algorithms.greedy_optimization.GreedyOptimization.fragmentation`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``dF_greedy``
        This dictionary contains as keys tuples storing the found node names (the vertex ``name`` attribute for each node)
        and the corresponding dF value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param k:
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(k, KpnegEnum.dF, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpnegEnum.dF.name + '_greedy',
            {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dR(graph, k: int, max_distance: int or None=None, seed: int or None=None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *distance-weighted reach* (*dR*) index. It does so by wrapping the :func:`~algorithms.greedy_optimization.GreedyOptimization.reachability`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``dR_greedy``
        This dictionary contains as keys tuples storing the found node names (the vertex ``name`` attribute for each node)
        and the corresponding dR value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param int,None seed: optional, a positive integer that can be used to replicate the greedy optimization run. If :py:class:`~None` (default), the greedy optimization may return different results at each run.
        """

        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(k, KpposEnum.dR, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpposEnum.dR.name + '_greedy',
            {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_mreach(graph, k: int, m: int or None=None, max_distance: int or None=None, seed: int or None=None):
        r"""
        Performs a greedily-optimized search on the input graph to search the optimal *key-player* set (kp-set) of nodes of size :math:`k` for the
        *distance-weighted reach* (*m-reach*) index. It does so by wrapping the :func:`~algorithms.greedy_optimization.GreedyOptimization.reachability`
        Pyntacle method. It then stores the found node(s) in a dictionary that is embedded in the graph attribute ``mreach_greedy``
        This dictionary contains as keys tuples storing the found node names (the vertex ``name`` attribute for each node)
        and the corresponding m-reach value for that group of nodes. Since greedily-optimized search can generate different
        results for the same :math:`k`, a seed can be passed to perform the replicate the result.

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the m-reach index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int m: The number of steps of the m-reach algorithm.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        :param seed:
        """
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(k, KpposEnum.mreach, m=m, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_greedy'.format(str(m))
        AddAttributes.add_graph_attributes(graph,
            attr_name, {tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][1]})

    # Brute-force optimization
    @staticmethod
    @check_graph_consistency
    def add_BF_F(graph, k: int, max_distance: int or None=None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set(s) of nodes of size :math:`k` for the
        *fragmentation* (*F*) index. It does so by wrapping the :func:`~algorithms.bruteforce_search.BruteforceSearch.fragmentation`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``F_bruteforce``
        This dictionary contains as keys tuples of tuple, each one storing the vertex ``name`` attribute of all the
        nodes of each set that achieve the best value for F and the corresponding F value for the set(s).

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the F index and the brute-force search.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """

        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(k, KpnegEnum.F, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpnegEnum.F.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.F.name][0]): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_BF_dF(graph, k: int, max_distance: int or None=None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set(s) of nodes of size :math:`k` for the
        *distance-based fragmentation* (*dF*) index. It does so by wrapping the :func:`~algorithms.bruteforce_search.BruteforceSearch.fragmentation`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``dF_bruteforce``
        This dictionary contains as keys tuples of tuple, each one storing the vertex ``name`` attribute of all the
        nodes of each set that achieve the best value for dF and the corresponding dF value for the set(s).

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the dF index and the brute-force search.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(k, KpnegEnum.dF, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpnegEnum.dF.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.dF.name][0]): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_BF_dR(graph, k: int, max_distance: int or None=None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp)set(s) of nodes of size :math:`k` for the
        *distance-weighted reach* (*dR*) index. It does so by wrapping the :func:`~algorithms.bruteforce_search.BruteforceSearch.reachability`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``dR_bruteforce``
        This dictionary contains as keys tuples of tuple, each one storing the vertex ``name`` attribute of all the
        nodes of each set that achieve the best value for dR and the corresponding dR value for the set(s).

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the dR index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """

        kpobj = bfw(graph=graph)
        kpobj.run_reachability(k, KpposEnum.dR, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes.add_graph_attributes(graph,
            KpposEnum.dR.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.dR.name][0]): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_BF_mreach(graph, k: int, m: int or None=None, max_distance: int or None=None):
        r"""
        Performs a brute-force search on the input graph to search the best *key player* (kp) set(s)  of nodes of size :math:`k` for the
        *m-reach* index. It does so by wrapping the :func:`~algorithms.bruteforce_search.BruteforceSearch.reachability`
        Pyntacle method. It then stores the found set(s) in a dictionary that is embedded in the graph attribute ``mreach_bruteforce``
        This dictionary contains as keys tuples of tuple, each one storing the vertex ``name`` attribute of all the
        nodes of each set that achieve the best value for dR and the corresponding m-reach value for the set(s).

        We recommend visiting the ` Key Player Guide <pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_ on Pyntacle official
        website for an overview of the dR index and the greedy optimization.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param int k: the size of the kp-set. Must be a positive integer.
        :param int m: The number of steps of the m-reach algorithm.
        :param int,None max_distance: The maximum shortest path length over which two nodes are considered unreachable. Default is :py:class:`None` (distances are preserved).
        """
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(k, KpposEnum.mreach, max_distance=max_distance, m=m)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_bruteforce'.format(str(m))
        AddAttributes.add_graph_attributes(graph,
            attr_name,
            {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.mreach.name][0]): results_dict[KpposEnum.mreach.name][1]})

    # todo mauro - missing octopus metrics:
    # todo global metrics:
    # todo median_global_shortest_path_length
    # todo average_global_shortest_path_length
    # todo group centrality metrics:
    # todo add_group_degree
    # todo add_group_betweenness
    # todo add_group_closeness
    # todo add_GO_group_degree
    # todo add_GO_group_betweenness
    # todo add_GO_group_closeness
    # todo add_BF_group_closeness
    # todo add_BF_group_degree
    # todo add_BF_group_betweenness
