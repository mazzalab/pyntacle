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


from cmds.cmds_utils.communities_utils import *


class CommunityFinder:
    r"""
    A series of algorithms, mostly borrowed from :py:class:`igraph` to perform community finding on a network of interest.
    """
    logger = None

    def __init__(self, graph: Graph):
        r"""
        Initialize the py:class:`~igraph.Graph` object and prepare it to be used for community detection algorithms

        :param graph: :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        """
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
        A wrapper around the `community_infomap  igraph method <http://igraph.org/python/doc/igraph.Graph-class.html#community_infomap>`
        which in turn is an implementation of `Rosvall and Bergstrom <https://www.pnas.org/content/105/4/1118>`_
        algorithm for detecting communities in sparse, real-world networks by means of random walks and  measures of information flows
        among the network.
        """

        temp_modules = self.graph.community_infomap(edge_weights=None, vertex_weights=None, trials=10)
        self.mods = temp_modules.subgraphs()

    def leading_eigenvector(self):
        r"""
        A wrapper around the `leading_eigenvector  igraph method <http://igraph.org/python/doc/igraph.Graph-class.html#community_leading_eigenvector>`
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
