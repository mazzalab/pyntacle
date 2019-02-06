__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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


from config import *
from igraph import Graph
from tools.graph_utils import GraphUtils


class CommunityFinder:
    r"""
    A series of algorithms, mostly borrowed from :py:class:`igraph` to perform community finding on a network of interest.
    """


    def __init__(self, graph: Graph):
        r"""
        Initialize the py:class:`~igraph.Graph` object and prepare it to be used for community detection algorithms

        :param graph: :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
        logger = None
        #check that graph is properly set
        GraphUtils(graph=graph).check_graph()
        self.graph = graph
        self.logger = log
        self.mods = []

    @property
    def get_modules(self):
        r"""
        Returns the modules found  as a list of :py:class:`igraph.Graph` objects.

        :return list: a list storing a series of :py:class:`igraph.Graph` objects, each one representing the subgraphs of the original graphs.
        """

        return self.mods

    def fastgreedy(self, weights=None, n: int or None=None):
        r"""
        A wrapper around the `community_fastgreedy igraph method <http://igraph.org/python/doc/igraph.Graph-class.html#community_fastgreedy>`,
        which in turn is an implementation of the method proposed by `Newman and Clauset <https://doi.org/10.1103/PhysRevE.70.066111>`_.

        This algorithm tries to optimize a quality function called *modularity* in a greedy manner. Initially, every vertex belongs
        to a separate community, and communities are merged iteratively such that each merge is locally optimal
        (i.e. yields the largest increase in the current value of modularity).
        The algorithm stops when it is not possible to increase the modularity any more.
        It runs almost in linear time on sparse graphs.

        :param list, str None weights: either edge attribute name of an attribute storing edge weights or a list containing edge weights. If ``None``, edges are considered unweighted.
        :param int, None n: A positive integer. If specified, it represents the desired number of output communities that will be produced. Default is ``None`` (report all communities found)
        :raise ValueError: if the ``weights`` argument is not a list of numericals or there is no attribute named *weights* associated to graph edges. Ther exception is also raised if the ``n`` argument is not a positive integer
        """


        modules = self.graph.community_fastgreedy(weights=weights)
        if not isinstance(n, int) and n is not None:
            raise ValueError(u"'n' must be a positive integer")
        else:
            modules = modules.as_clustering(n=n)
            self.mods = modules.subgraphs()

    def infomap(self):
        r"""
        A wrapper around the `community_infomap  igraph method <http://igraph.org/python/doc/igraph.Graph-class.html#community_infomap>`_
        which in turn is an implementation of `Rosvall and Bergstrom <https://www.pnas.org/content/105/4/1118>`_
        algorithm for detecting communities in sparse, real-world networks by means of random walks and  measures of information flows
        among the network.

        .. note:: The infomap algorithm wrapped here is the simplistic form. For a better take on  the infomap algorithm, we recommend to use the `official infomap package <https://mapequation.github.io/infomap/>`_ developed by edler and Rosvall.
        """

        temp_modules = self.graph.community_infomap(edge_weights=None, vertex_weights=None, trials=10)
        self.mods = temp_modules.subgraphs()

    def leading_eigenvector(self):
        r"""
        A wrapper around the `leading_eigenvector igraph method <http://igraph.org/python/doc/igraph.Graph-class.html#community_leading_eigenvector>`_
        which in turn is an implementation of `Newman's leading eigenvector <https://doi.org/10.1103/PhysRevE.74.036104>`_
        algorithm for detecting communities in  real world networks.

        This is the proper implementation of the recursive, divisive algorithm: each split is done by maximizing
        the modularity score of the original network.
        """

        temp_modules = self.graph.community_leading_eigenvector()
        self.mods = temp_modules.subgraphs()

    def community_walktrap(self, weights: str or list or None =None, steps: int=3, n: int=None):
        r"""
        A wrapper around the `community_infomap igraph method <http://igraph.org/python/doc/igraph.Graph-class.html#community_walktrap>`_
        which in turn is an implementation of the algorithm proposed by `Latapy & Pons <https://arxiv.org/abs/physics/0512106>`_,
        based on random walks.
        The algorithm is based on the idea that short random walks are able to spot nodes that altogether stays in the same community.

        :param list, str None weights: either edge attribute name of an attribute storing edge weights or a list containing edge weights. If ``None``, edges are considered unweighted.
        :param int steps: A positive integers that specifies the  maximum length of random walks. Default is 3.
        :param int, None n: A positive integer. If specified, it represents the desired number of output communities that will be produced. Default is ``None`` (report all communities found)
        :raise ValueError: if the ``weights`` argument is not a list of numericals or there is no attribute named *weights* associated to graph edges. Ther exception is also raised if the ``n`` argument is not a positive integer
        """

        if weights is None:
            vertex_dendogram = self.graph.community_walktrap(steps=steps)
            modules = vertex_dendogram.as_clustering()
            self.mods = modules.subgraphs()
        else:
            if not isinstance(weights, list) or ('weights' not in self.graph.es.attributes() and not isinstance(self.graph.es["weights"], list)) :
                raise ValueError(u"'weights' must be either a list or an edge graph attribute present in graph")

            else:
                vertex_dendogram = self.graph.community_walktrap(steps=steps, weights=weights)

                if n <= 0 or not isinstance(n, type(None)):
                    raise ValueError(u"'n' must be either 'None' or a positive integer")

                else:
                    modules = vertex_dendogram.as_clustering(n=None)
                    self.mods = modules.subgraphs()

class ModuleUtils():
    r"""
    A set of utilities to perform a wide array of operations from the communities found with :class:`~pyntacle.graph_operations_modules_finder.CommunityFinder`
    """

    logger = None

    def __init__(self, modules: list, graph: Graph, algorithm: str):
        r"""
        Implements all the necessary step to check a graph object and add the reserved attribute "module_number" to
        each submodule in order to retrace it back. If a graph attribute with that name already exists, it will be
        overwritten

        :param modules:a list of graphs already divided by the CommunityFinder class
        :param graph: the input graph used  to find get_modules
        :param str algorithm: the name of the algorithm used to perform community detection
        """

        self.logger = log

        GraphUtils(graph=graph).check_graph()

        self.graph = graph

        for i, elem in enumerate(modules):
            if elem.vcount() == 0:
                self.logger.warning(u"Module {} is empty, and therefore will be discarded".format(i))
                del (modules[i])

            if elem["name"] != graph["name"]:
                raise ValueError(u"Module {} does not come from the input Graph".format(i))

            if not set(elem.vs()["name"]).issubset(set(graph.vs()["name"])):
                raise ValueError(u"Module {} does not come from the input Graph".format(i))

            if elem.vcount() > graph.vcount() or elem.ecount() > graph.ecount():
                raise ValueError(u"Module {} does not come from the input Graph".format(i))
            if "module_number" in graph.attributes():

                self.logger.info(
                    u"Attribute \"module_number\" already exist in the module {}, will be overwritten".format(str(i)))

            elem["module_number"] = i  # this should traceroute the module back to its original number

        self.modules = modules

        #checks that the input graph is properly formatted

        if not isinstance(algorithm, str):
            raise TypeError("\"algorithm\" must be a string, {} found".format(type(algorithm).__name__))

        else:
            self.algorithm = algorithm

    def filter_subgraphs(self, min_nodes=None, max_nodes=None, min_components=None, max_components=None):
        r"""

        :param min_nodes: minimum set size. Default is None (no component will be filtered according to this criteria)
        :param max_nodes: maximum set size. Default is None (no component will be filtered according to this criteria)
        :param min_components: minimum number of components that graph must have. Default is None (no component will be filtered according to this criteria)
        :param max_components: maximum number of components that graph must have. Default is None (no component will be filtered according to this criteria)
        """

        if min_nodes is not None and min_nodes < 0:
            raise ValueError(u"minset must be a positive integer")

        if max_nodes is not None and max_nodes < 1:
            raise ValueError(u"maxset must be a positive integer greater than one")

        if max_components is not None and max_components < 1:
            raise ValueError(u"max_components must be a positive integer greater than one")

        if min_components is not None and min_components < 1:
            raise ValueError(u"min_components must be a positive integer greater than one ")

        info = [str(x) if x is not None else "NA" for x in (min_nodes, max_nodes, min_components, max_components)]

        sys.stdout.write(
            u"Filtering subgraphs according to the specified criteria, enlisted above:\nminimum number of nodes per module: {0}\nmaximum number of nodes per module: {1}\nminimum number of components: {2}\nmaximum number of components: {3}\n".format(
                *info))

        if not all(x == None for x in [min_nodes, max_nodes, min_components, max_components]):
            self.modules = list(filter(lambda x: x.vcount() > min_nodes if min_nodes is not None else x, self.modules))
            self.modules = list(filter(lambda x: x.vcount() < max_nodes if max_nodes is not None else x, self.modules))
            self.modules = list(
                filter(lambda x: len(x.components()) > min_components if min_components is not None else x,
                       self.modules))
            self.modules = list(
                filter(lambda x: len(x.components()) < max_components if max_components is not None else x,
                       self.modules))

    def get_modules(self) -> list:
        r"""
        Returns the list of graph get_modules (a list of igraph.Graph objects)

        :return list: a list of :py:class:`igraph.Graps`, each one storing a module of an initial network.
        """
        return self.modules

    def add_modules_info(self):
        r"""
        Adds all the information regarding the get_modules to each subgraph found using community detection algorithms.
        These information are, specifically:

        #. a hidden attribute named "__module_algorithm" that store the type of algorithm that was used to identify the community
        #. a hidden attribute named "__origin_graph" the first element of the graph["name"] attribute (ideally, the name of the input graph)

        """

        if len(self.graph["name"]) > 1:
            self.logger.warning(
                u"graph attribute \"name\" must be unique, found {} instead, will use first name only.".format(
                    ",".join[self.graph["name"]]))

        self.logger.info(u"adding algorithm used to each module in the \"__module_algorithm\" internal attribute")
        self.logger.info(u"adding original graph name to each module in the \"__origin_graph\" internal attribute")

        for subgraph in self.modules:
            if "__module_algorithm" not in subgraph.attributes():
                subgraph["__module_algorithm"] = self.algorithm

            if "__origin_graph" not in subgraph.attributes():
                subgraph["__origin_graph"] = self.graph["name"][0]

    def label_modules_in_graph(self):
        r"""
        Add to each node and edge an attribute that trace it to each module (a way to distinguish each components).
        Specifically, two reserved attributed will be filled in each of the elemenf in `get_modules`:

        #. a ``__module`` name will be assigned to the reserved ``__module`` attribute for each  subgraph, node and edge the element in the get_modules was found into. specifying the name of the module (usually a string representing a positive integer)
        #. a ``__algorithm`` attribute will be assigned to each subgraph, node, and edge attributes showing the name of the algorithm that was passed to the ModuleUtils() class specifying the name of the algorithm that was used to find communities.
        """

        self.logger.info(u"Adding attribute \"__module\" to each node")

        for i, subgraph in enumerate(self.modules):

            if "__module" in subgraph.vs.attributes():
                self.logger.warning(
                    u"module {} already have a \"__module\" vertex attribute name, will overwrite it".format(i))
                subgraph.vs["__module"] = None

            if "__algorithm" in subgraph.vs.attributes():
                self.logger.warning(
                    u"module {} already have a \"__algorithm\" vertex attribute name, will overwrite it".format(i))
                subgraph.vs["__algorithm"] = None

            if "__module" in subgraph.es.attributes():
                self.logger.warning(
                    u"module {} already have a \"__module\" edge attribute name, will overwrite it".format(i))
                subgraph.es["__module"] = None

            if "__algorithm" in subgraph.es.attributes():
                self.logger.warning(
                    u"module {} already have a \"__algorithm\" edge attribute name, will overwrite it".format(i))
                subgraph.es["__algorithm"] = None

            node_names = subgraph.vs()["name"]
            edge_names = subgraph.es()["adjacent_nodes"]
            select_nodes = self.graph.vs().select(name_in=node_names)

            if len(node_names) != len(select_nodes):
                different_nodes = list(set(node_names) - set([x["name"] for x in select_nodes]))
                self.logger.warning(u"Nodes ({}) not found in input graph".format(", ".join(different_nodes)))

            else:
                self.graph.vs(select_nodes.indices)["__module"] = i
                self.graph.vs(select_nodes.indices)["__algorthm"] = self.algorithm

            select_edges = select_nodes = self.graph.es().select(adjacent_nodes_in=edge_names)
            if len(edge_names) != len(select_edges):
                different_nodes = list(set(edge_names) - set([x["name"] for x in select_edges]))
                self.logger.warning(
                    u"edges {} not found in input graph".format(",".join("--".join(list(different_nodes)))))

            else:
                self.graph.es(select_nodes.indices)["__module"] = i
                self.graph.es(select_nodes.indices)["__algorithm"] = self.algorithm