__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
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

"""Generate Network with a specified toipology and make them pyntacle-ready"""

import random
from igraph import Graph
from tools.add_attributes import AddAttributes as ad
from misc.generators_utils import *

class Generator:

    @staticmethod
    @generatorscanner
    def Random(params, name="Random", seed=None) -> Graph:
        """
        Generate a Random Network by wrapping the Erdos-Renyi generator provided by igraph and makes it ready to be used
        for pyntacle. Node `name` attribute will be the relative index (represented as string), while the graph name it
        is assigned as a combination of
        #. the `name` parameter (default is "Random")
        #. the number of nodes
        #.the number of edges
        #. a random string of 10 characters that makes the graph unique.
        :param list params: a list of two arguments. The first parameter is the number of nodes, the second parameter
        can be either a `float` betweeen 0 and 1 or an `int`. If it's a float , it will be considered as rewiring
        probability. Otherwise, it will be considered the number of edges in the Random Graph.
        :param name: optional, if you want to assign a name to the `name` graph attribute. Default is **"Random"**
        :param int seed: optional: provide a seed to the random generator
        :return igraph.Graph: an `igraph,Graph` object already initialized to be used for pyntacle's methods
        """
        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("\"Seed must be an integer, {} found".format(type(seed).__name__))

        else:
            random.seed(seed)

        if not (len(params) == 2):
            raise ValueError('Wrong number of parameters for Erdos-Renyi graph generation')

        if isinstance(params[1], float) and 0 <= params[1] <= 1:
            graph = Graph.Erdos_Renyi(params[0], p=params[1])
        elif isinstance(params[1], int) and params[1] > 1:
            graph = Graph.Erdos_Renyi(params[0], m=params[1])

        else:
            raise ValueError('Second parameter is not a positive float or a positive integer greater than 1')
        ad(graph=graph).graph_initializer(graph_name=(randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))

        return graph

    @staticmethod
    @generatorscanner
    def ScaleFree(params, name="Scale_Free", seed=None) -> Graph:
        """
        Generates a Scale-Free Network according to the Lazslo-Barabasi model by wrapping the Scale free network
        generator provided by igraph.
        :param  list params: a list of two elements: the first element is the number of nodes of the graph,
        the second element is the average number of incoming/outcoming edges per node
        :param str name: optional, if you want to assign a name to the `name` graph attribute. Default is **"Scale_Free"**
        :param int seed: optional: provide a seed to the random generator
        :return igraph.Graph: an `igraph,Graph` object already initialized to be used for pyntacle's methods
        """

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("\"seed must be an integer, {} found".format(type(seed).__name__))
        else:
            random.seed(seed)

        if not (len(params) == 2):
            raise ValueError('Wrong number of parameters for Scale-free graph generation')
        elif not (isinstance(params[0], int) and isinstance(params[1], int)):
            raise TypeError('Wrong parameter type(s) for Scale-free graph generation')
        elif not (0 < params[0] and 0 < params[1]):
            raise ValueError('The value of one or more parameters is not allowed')
        else:
            graph = Graph.Barabasi(params[0], params[1])
            ad(graph=graph).graph_initializer(graph_name=(
            randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))

            return graph

    @staticmethod
    @generatorscanner
    def SmallWorld(params, name="SmallWorld", seed=None) -> Graph:
        """
        Generates a Small World Network by wrapping the `Watts_Strogatz` function of `igraph`. `igraph` creates first
        a lattice
        :param list params:a list of 4 arguments #. the number of vertices #. the number of children each `parent` node
        will exhibit. #. the dimension of the lattice across all dimensions (we recommend to keep this parameter low)
        #. the distance between each node pair to consider them as connected. and #. the node rewiring probability (a
        `float` between 0 and 1).
        :param str name: optional, if you want to assign a name to the `name` graph attribute. Default is **"Small_World"**
        :param int seed: optional: provide a seed to the random generator
        :return igraph.Graph: an `igraph,Graph` object already initialized to be used for pyntacle's methods
        """
        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("\"seed must be an integer, {} found".format(type(seed).__name__))
        else:
            random.seed(seed)

        if not (len(params) == 4):
            raise ValueError('Wrong number of parameters for Small-world graph generation (4 params needed)')
        elif not (isinstance(params[0], int)
                  and isinstance(params[1], int)
                  and isinstance(params[2], int)
                  and isinstance(params[3], float)):

            raise TypeError('Wrong parameter type(s) for Small-world graph generation')
        elif not (0 < params[0] and 0 < params[1] and 0 < params[2] and 0 <= params[3] <= 1):
            raise ValueError('The value of one or more parameters is not allowed')

        else:
            graph = Graph.Watts_Strogatz(params[0], params[1], params[2], params[3])

            ad(graph=graph).graph_initializer(graph_name=(
            randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))

            return graph

    @staticmethod
    @generatorscanner
    def Tree(params, name="Tree", seed=None) -> Graph:
        """
        Generates a Network that Follows a Tree scheme, as described in http://mathworld.wolfram.com/Tree.html. Each
        vertex wil have as many `children` vertices specifed by the second value in the "param" argument. This is a
        wrapper to the `Tree` method of `igraph`
        :param params: a list of two arguments: #1. the toal number of nodes and #.the number of *children* each *parent*
        node will have
        :param str name: optional, if you want to assign a name to the `name` graph attribute. Default is **"Tree"**
        :param int seed: optional: provide a seed to the random generator
        :return igraph.Graph: an `igraph,Graph` object already initialized to be used for pyntacle's methods
        """
        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("\"seed must be an integer, {} found".format(type(seed).__name__))
        else:
            random.seed(seed)

        if not (len(params) == 2):
            raise ValueError('Wrong number of parameters for Tree generation')
        elif not (isinstance(params[0], int) and isinstance(params[1], int)):
            raise TypeError('Wrong parameter type(s) for Tree generation')
        elif not (0 < params[0] and 0 < params[1]):
            raise ValueError('The value of one or more parameters is not allowed')
        else:
            graph = Graph.Tree(params[0], params[1])
            ad(graph=graph).graph_initializer(graph_name=(
            randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))
            return graph