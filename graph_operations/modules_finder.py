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

# pyntacle libraries
from utils.modules_utils import *
from config import *

"""This tool uses the embedded methods in `igraph` to call several community finding algorithms and returns a list of 
subgraph obtained from the input graph"""


class CommunityFinder:
    logger = None

    def __init__(self, graph: Graph):

        GraphUtils(graph=graph).graph_checker()  # perform check on input Graph
        self.__graph = graph
        self.logger = log

        self.__modules = []

    def fastgreedy(self, weights=None, n=None):
        '''
        **[EXPAND]**
        
        :param weights: edge attribute name or a list containing edge weight
        :param n: if specified, Desired number of modules to be outputted
        '''

        self.logger.info("Computing Fastgreedy module search")
        if weights is not None:
            self.logger.info("Using provided weights")

        modules = Graph.community_fastgreedy(self.__graph, weights=weights)
        if not isinstance(n, int) and n is not None:
            raise ValueError("\"n\" must be an integer")
        else:
            modules = modules.as_clustering(n=n)
            self.__modules = modules.subgraphs()

    def infomap(self):

        self.logger.info("Running Community Infomap")
        modules = Graph.community_infomap(self.__graph)
        self.__modules = modules.subgraphs()

    def leading_eigenvector(self):
        modules = Graph.community_leading_eigenvector(self.__graph)
        # print(modules)
        # print(modules.subgraphs())
        self.logger.info("Modules_created")
        self.__modules = modules.subgraphs()

    def community_walktrap(self, weights=None, steps=3, n=None):
        '''
        **[EXPAND]**

        :param weights:
        :param steps:
        :return:
        '''

        if weights is None:
            vertex_dendogram = Graph.community_walktrap(self.__graph, steps=steps)
            modules = vertex_dendogram.as_clustering()
            self.__modules = modules.subgraphs()

        else:
            if not isinstance(weights, list) or weights not in self.__graph.es().attributes:
                raise ValueError("Weights must be either a list or an edge graph attribute present in graph")

            else:
                vertex_dendogram = Graph.community_walktrap(self.__graph, steps=steps, weights=weights)
                if not isinstance(n, int) and n is not None:
                    raise ValueError("\"n\" must be an integer")
                else:
                    modules = vertex_dendogram.as_clustering(n=None)
                    self.__modules = modules.subgraphs()

    def get_modules(self):
        if not self.__modules:
            raise ValueError("modules were not called")
        else:
            return self.__modules
