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

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.diameter.name, GlobalTopology.diameter(graph))

    @staticmethod
    @check_graph_consistency
    def add_radius(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.radius` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph ``radius``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.radius.name, GlobalTopology.radius(graph))
        
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

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.components.name, GlobalTopology.components(graph))

    @staticmethod
    @check_graph_consistency
    def add_density(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.density` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``density``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.density.name, GlobalTopology.density(graph))
        
    @staticmethod
    @check_graph_consistency
    def add_pi(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.PI` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``PI``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.pi.name, GlobalTopology.pi(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_clustering_coefficient(graph):
        r"""
        Wraps the :func:`~pyntacle.algorithms.global_topology.GlobalTopology.average_clustering_coefficient` method in
        :class:`~pyntacle.algorithm.global_topology.GlobalTopology` and adds it to the input :py:class:`~igraph.Graph`
        object under the graph attribute ``average_clustering_coefficient``

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_clustering_coefficient.name,
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

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.weighted_clustering_coefficient.name,
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

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_degree.name,
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

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_closeness.name,
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

        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_eccentricity.name,
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
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_radiality.name,
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
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_radiality_reach.name,
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
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_shortest_path_length.name,
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
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.completeness_naive.name,
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
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.completeness.name,
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
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.compactness.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.degree.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.betweenness.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.clustering_coefficient.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.closeness.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.eccentricity.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.radiality.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.radiality_reach.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.eigenvector_centrality.name,
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
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.pagerank.name,
                                                 LocalTopology.pagerank(graph, nodes, weights, damping),
                                                 nodes)

    @staticmethod
    @check_graph_consistency
    def add_shortest_paths(graph, nodes: str or list or None=None):
        r"""

        :param graph:
        :param nodes:
        :return:
        """
        cmode = get_cmode(graph)

        if nodes is None:
            nodes = graph.vs["name"]

        tot_nodes = graph.vcount()

        distances = ShortestPath.get_shortestpaths(graph, nodes, cmode=cmode).astype(float)
        distances[distances >= tot_nodes +1] = float("inf")
        distances = distances.tolist() #convert to a list of lists
        #cast everything not infinite to integer
        distances = [[int(x) if not isinf(x) else x for x in y] for y in distances]

        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.shortest_paths.name, distances, nodes)

    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph, nodes: str or list or None=None):
        r"""

        :param graph:
        :param nodes:
        :return:
        """
        cmode = get_cmode(graph)
        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.average_shortest_path_length.name,
                                                 ShortestPath.average_shortest_path_lengths(graph, nodes, cmode),
                                                 nodes)

    @staticmethod
    @check_graph_consistency
    def add_median_shortest_path_length(graph, nodes: str or list or None=None):
        r"""

        :param graph:
        :param nodes:
        :return:
        """
        cmode = get_cmode(graph)
        if nodes is None:
            nodes = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.median_shortest_path_length.name,
                                                 ShortestPath.median_shortest_path_lengths(graph, nodes, cmode),
                                                 nodes)
   
    # Topology metrics
    @staticmethod
    @check_graph_consistency
    def add_F(graph):
        r"""

        :param graph:
        :return:
        """
        AddAttributes(graph).add_graph_attributes(KpnegEnum.F.name, KeyPlayer.F(graph))

    @staticmethod
    @check_graph_consistency
    def add_dF(graph, max_distance: int or None=None):
        r"""

        :param graph:
        :param max_distance:
        :return:
        """
        cmode = get_cmode(graph)
        AddAttributes(graph).add_graph_attributes(KpnegEnum.dF.name, KeyPlayer.dF(graph, cmode=cmode,
                                                                                  max_distance=max_distance))

    @staticmethod
    @check_graph_consistency
    def add_kp_F(graph, nodes: str or list or None):
        r"""

        :param graph:
        :param nodes:
        :return:
        """
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KpnegEnum.F)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.F.name + '_kpinfo', {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dF(graph, nodes: str or list or None, max_distance=None):
        r"""

        :param graph:
        :param nodes:
        :param max_distance:
        :return:
        """
        cmode = get_cmode(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KpnegEnum.dF, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.dF.name + '_kpinfo',
            {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dR(graph, nodes: str or list or None, max_distance=None):
        r"""

        :param graph:
        :param nodes:
        :param max_distance:
        :return:
        """

        cmode = get_cmode(graph)

        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KpposEnum.dR, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpposEnum.dR.name + '_kpinfo',
            {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_mreach(graph, nodes: str or list or None, m: int or None=None, max_distance: int or None=None):
        r"""

        :param graph:
        :param nodes:
        :param m:
        :param max_distance:
        :return:
        """
        cmode = get_cmode(graph)

        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KpposEnum.mreach, m=m, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_kpinfo'.format(str(m))
        AddAttributes(graph).add_graph_attributes(
            attr_name, {tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][1]})

    # Greedy optimization
    @staticmethod
    @check_graph_consistency
    def add_GO_F(graph, kp_size: int, seed: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param seed:
        :return:
        """
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kp_size, KpnegEnum.F, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.F.name + '_greedy', {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dF(graph, kp_size: int, max_distance: int or None=None, seed: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param max_distance:
        :param seed:
        :return:
        """
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kp_size, KpnegEnum.dF, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.dF.name + '_greedy',
            {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dR(graph, kp_size: int, max_distance: int or None=None, seed: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param max_distance:
        :param seed:
        :return:
        """
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kp_size, KpposEnum.dR, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpposEnum.dR.name + '_greedy',
            {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_mreach(graph, kp_size: int, m: int or None=None, max_distance: int or None=None, seed: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param m:
        :param max_distance:
        :param seed:
        :return:
        """
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kp_size, KpposEnum.mreach, m=m, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_greedy'.format(str(m))
        AddAttributes(graph).add_graph_attributes(
            attr_name, {tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][1]})
    
    # Brute-force optimization
    @staticmethod
    @check_graph_consistency
    def add_BF_F(graph, kp_size: int, max_distance: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param max_distance:
        :return:
        """
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kp_size, KpnegEnum.F, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.F.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.F.name][0]): results_dict[KpnegEnum.F.name][1]})
        
    @staticmethod
    @check_graph_consistency
    def add_BF_dF(graph, kp_size: int, max_distance: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param max_distance:
        :return:
        """
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kp_size, KpnegEnum.dF, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.dF.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.dF.name][0]): results_dict[KpnegEnum.dF.name][1]})
    
    @staticmethod
    @check_graph_consistency
    def add_BF_dR(graph, kp_size: int, max_distance: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param max_distance:
        :return:
        """
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kp_size, KpposEnum.dR, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpposEnum.dR.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.dR.name][0]): results_dict[KpposEnum.dR.name][1]})
        
    @staticmethod
    @check_graph_consistency
    def add_BF_mreach(graph, kp_size: int, m: int or None=None, max_distance: int or None=None):
        r"""

        :param graph:
        :param kp_size:
        :param m:
        :param max_distance:
        :return:
        """
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kp_size, KpposEnum.mreach, max_distance=max_distance, m=m)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_bruteforce'.format(str(m))
        AddAttributes(graph).add_graph_attributes(
            attr_name,
            {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.mreach.name][0]): results_dict[KpposEnum.mreach.name][1]})
