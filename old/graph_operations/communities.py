__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
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

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
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
    def __init__(self, modules: list):
        r"""
        Implements all the necessary step to check a graph object and add the reserved attribute ```module```, an
        integer used to distinguish a community from one another.
        If a graph attribute with that name already exists, it will be overwritten.

        :param list modules:a list of :py:class:`~igraph.Graph` objects found using :class:`~pyntacle.graph_operations_communities.CommunityFinder`

        """

        for i, elem in enumerate(modules):
            if "module" in elem.attributes():

                sys.stdout.write(
                    u"Attribute 'module' already exist in the {} subgraph, will overwrite\n".format(str(i)))

            elem["module"] = i  # this should traceroute the module back to its original number

        self.modules = modules

    def filter_subgraphs(self, min_nodes=None, max_nodes=None, min_components=None, max_components=None):
        r"""
        Filters the found communities according to the number of nodes, edges and components they yeld.

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
        Returns the list of graph modules (a list of :py:class:`igraph.Graph` objects).

        :return list: a list made :py:class:`igraph.Graph`, each element storing a an induced subgraph representing a community of the graph of origin
        """
        return self.modules

    def label_modules_in_graph(self, graph: Graph):
        r"""
        Adds to each node and edge of a py:class:`~igraph.Graph` object
        an attribute named ``module`` at vertex and edge level to retrace each node and edge to the original community

        : warning:: the ``graph`` must be the original py:class:`~igraph.Graph` object that has been used in community detection

        #. a name will be assigned to the reserved ``module`` vertex and edge attribute

        :param igraph.Graph graph: The original :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :raise ValueError: if the ``graph`` does not correspond to the original graph in which modules were found.
        """

        GraphUtils(graph=graph).check_graph()
        for i, elem in enumerate(self.modules):
            if elem["name"] != graph["name"]:
                raise ValueError(u"Module {} does not come from the input Graph".format(i))

            if not set(elem.vs()["name"]).issubset(set(graph.vs()["name"])):
                raise ValueError(u"Module {} does not come from the input Graph".format(i))

            if elem.vcount() > graph.vcount() or elem.ecount() > graph.ecount():
                raise ValueError(u"Module {} does not come from the input Graph".format(i))

        for i, subgraph in enumerate(self.modules):

            if "module" in subgraph.vs.attributes():
                sys.stdout.write(
                    u"Module {} already have a 'module' vertex attribute name, will overwrite\n".format(i))
                subgraph.vs["module"] = None

            if "module" in subgraph.es.attributes():
                sys.stdout.write(
                    u"Module {} already have a 'module' edge attribute name, will overwrite\n".format(i))
                subgraph.es["module"] = None

            node_names = subgraph.vs()["name"]
            edge_names = subgraph.es()["adjacent_nodes"]
            select_nodes = graph.vs().select(name_in=node_names)
            graph.vs(select_nodes.indices)["module"] = i
            select_edges = graph.es().select(adjacent_nodes_in=edge_names)
            graph.es(select_edges.indices)["module"] = i
