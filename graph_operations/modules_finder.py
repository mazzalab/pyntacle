"""
Community finding algorithms borrowed from iGraph
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "28/04/2018"
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


from tools.modules_utils import *


class CommunityFinder:
    """
    *Community finding* algorithms borrowed from iGraph, which return a list of subgraphs from the input graph
    """

    logger = None

    def __init__(self, graph: Graph):
        GraphUtils(graph=graph).check_graph()
        self.__graph = graph
        self.logger = log
        self.__modules = []

    @property
    def modules(self):
        return self.__modules

    def fast_greedy(self, weights=None, n=None):
        """
        Community structure based on the greedy optimization of modularity.
        This algorithm merges individual nodes into communities in a way that greedily maximizes the modularity score
        of the graph. This algorithm is said to run almost in linear time on sparse graphs.
        (http://igraph.org/python/doc/igraph.Graph-class.html#community_fastgreedy)
        :param weights: edge attribute name or a list containing edge weights
        :param n: if specified, it represents the desired number of modules to be computed
        """

        if weights is not None:
            self.logger.info("Computing Fastgreedy module search using provided weights")
        else:
            self.logger.info("Computing Fastgreedy module search")

        modules = self.__graph.community_fastgreedy(weights=weights)
        if not isinstance(n, int) and n is not None:
            raise ValueError("'n' must be an integer value")
        else:
            modules = modules.as_clustering(n=n)
            self.__modules = modules.subgraphs()

    def infomap(self):
        """
        Finds the community structure of the network according to the Infomap method of Martin Rosvall and Carl T.
        (http://igraph.org/python/doc/igraph.Graph-class.html#community_infomap)
        """

        self.logger.info("Running Community Infomap")
        temp_modules = self.__graph.community_infomap(edge_weights=None, vertex_weights=None, trials=10)
        self.__modules = temp_modules.subgraphs()

    def leading_eigenvector(self):
        """
        Newman's *leading eigenvector* method for detecting community structure.
        This is the proper implementation of the recursive, divisive algorithm: each split is done by maximizing
        the modularity regarding the original network.
        (http://igraph.org/python/doc/igraph.Graph-class.html#community_leading_eigenvector)
        """

        self.logger.info("Calculating the leading eigenvectors")
        temp_modules = self.__graph.community_leading_eigenvector()
        self.__modules = temp_modules.subgraphs()

    def community_walktrap(self, weights=None, steps: int=3, n: int=None):
        """
        Community detection algorithm of Latapy & Pons, based on random walks.
        The basic idea of the algorithm is that short random walks tend to stay in the same community.
        The result of the clustering will be represented as a dendrogram.
        (http://igraph.org/python/doc/igraph.Graph-class.html#community_walktrap)
        :param weights: name of an edge attribute or a list containing edge weights
        :param steps: length of random walks to perform
        :param n: if specified, it represents the desired number of modules to be computed
        """

        if weights is None:
            vertex_dendogram = self.__graph.community_walktrap(steps=steps)
            modules = vertex_dendogram.as_clustering()
            self.__modules = modules.subgraphs()
        else:
            if not isinstance(weights, list) or 'weights' not in self.__graph.es.attributes():
                raise ValueError("Weights must be either a list or an edge graph attribute present in graph")

            else:
                vertex_dendogram = self.__graph.community_walktrap(steps=steps, weights=weights)
                if not isinstance(n, int) and n is not None:
                    raise ValueError("'n' must be an integer value")
                else:
                    modules = vertex_dendogram.as_clustering(n=None)
                    self.__modules = modules.subgraphs()
