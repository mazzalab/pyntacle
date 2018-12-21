__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
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

import random
from igraph import Graph
from tools.add_attributes import AddAttributes as ad
from internal.io_utils import generatorscanner, randomword


class Generator:
    r"""Generate :py:class:`igraph.Graph` simulated network objects that follow  different topologies and  turn them into
    Pyntacle-ready networks to be used for simulations or testing"""

    @staticmethod
    @generatorscanner
    def Random(params: list, name: str="Random", seed: int or None=None) -> Graph:
        r"""
        Generates a `random <https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93R%C3%A9nyi_model>`_ network by wrapping
        the igraph  `random <https://igraph.org/python/doc/igraph.GraphBase-class.html#Erdos_Renyi>`_
        generator provided by igraph and makes it ready to be used for Pyntacle.

        The vertex ``name`` attribute will be the relative index (represented as string), while the graph ``name`` is
        assigned as a combination of:

        #. the ``name`` parameter (default is "Random")
        #. the number of nodes
        #. the number of edges
        #. a random string of 10 characters to makes the graph ``name`` unique.

        :param list params: a list of two arguments:

            #. the number of nodes
            #. either a :py:class:`float` betweeen 0 and 1 or a :py:class`int`. In the first case, it will be considered as rewiring probability. Otherwise, it will be considered the number of edges in the resulting :py:class:`igraph.Graph`.

        :param name: optional, the value that will be assigned to the graph ``name`` attribute. Default is **"Random"**
        :param int, None seed: optional: provide a seed to the random generator

        :return igraph.Graph: a py:class:`igraph.Graph` object arranged randomly, initialized for Pyntacle usage

        :raise TypeError: if one of the elements in ``params`` is not one of the allowed types
        :raise ValueError: if ``params`` is not a list of size 4 and if any of its vlaues its outside their domain
        """

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError(u"'Seed must be an integer, {} found".format(type(seed).__name__))

        else:
            random.seed(seed)

        if not (len(params) == 2):
            raise ValueError(u'Wrong number of parameters for Erdos-Renyi graph generation')

        if not isinstance(params[0], int):
            raise TypeError(u"The elem `0` of `param` is not an integer, {} found".format(type(params[0]).__name__))

        if params[0] <= 1:
            raise ValueError(u"The number of nodes must be greater than 1")

        if isinstance(params[1], float) and 0 <= params[1] <= 1:
            graph = Graph.Erdos_Renyi(params[0], p=params[1])
        elif isinstance(params[1], int) and params[1] > 1:
            graph = Graph.Erdos_Renyi(params[0], m=params[1])

        else:
            raise ValueError(u'Second parameter is not a positive float or a positive integer greater than 1')
        ad(graph=graph).graph_initializer(graph_name=(randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))

        return graph

    @staticmethod
    @generatorscanner
    def ScaleFree(params: list, name: str="Scale_Free", seed:int or None=None) -> Graph:
        r"""
        Generates a scale-free network according to the `Barabasi-Albert model  <https://en.wikipedia.org/wiki/Barab%C3%A1si%E2%80%93Albert_model>`_
        by wrapping the igraph `scale-free generator <https://igraph.org/python/doc/igraph.GraphBase-class.html#Barabasi>`_

        The vertex ``name`` attribute will be the relative index (represented as string), while the graph ``name`` is
        assigned as a combination of:

        #. the ``name`` parameter (default is "Scale_Free")
        #. the number of nodes
        #. the number of edges
        #. a random string of 10 characters to makes the graph ``name`` unique.

        :param list params: a list of two elements:

            #. the number of nodes of the graph
            #. the average number of edges per node

        :param name: optional, the value that will be assigned to the graph ``name`` attribute. Default is **"Scale_Free"**
        :param int, None seed: optional: provide a seed to the network generator in order to reproduce the same network over time. Defaults to :py:class:`None` (no seed is set).

        :return igraph.Graph: a py:class:`igraph,Graph` object that follow a scale-free topology, initialized for Pyntacle usage.

        :raise TypeError: if one of the elements in ``params`` is not one of the allowed types
        :raise ValueError: if ``params`` is not a list of size 4 and if any of its vlaues its outside their domain
        """

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError(u"'seed must be an integer, {} found".format(type(seed).__name__))
        else:
            random.seed(seed)

        if params[0] <= 1:
            raise ValueError(u"The number of nodes ('params[0]') must be greater than 1")

        if params[1] < 1:
            raise ValueError(u"`params[1]` must be greater than one")

        if not (len(params) == 2):
            raise ValueError(u'Wrong number of parameters for Scale-free graph generation')

        elif not (isinstance(params[0], int) and isinstance(params[1], int)):
            raise TypeError(u'Wrong parameter type(s) for Scale-free graph generation')

        else:
            graph = Graph.Barabasi(params[0], params[1])
            ad(graph=graph).graph_initializer(graph_name=(
            randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))

            return graph

    @staticmethod
    @generatorscanner
    def SmallWorld(params: list, name:str ="SmallWorld", seed: int or None=None) -> Graph:
        r"""
        Generates a small-world network by wrapping the igraph `Watts_Strogatz <https://igraph.org/python/doc/igraph.GraphBase-class.html#Watts_Strogatz>`_method.
        In brief, a :math:`n \cdot m` `lattice <https://en.wikipedia.org/wiki/Lattice_graph>` where :math:`n` is the dimension of the lattice and :math:`m` is the size of the lattice among all dimensions.

        This lattice is generated such as two nodes are connected by a path of length :math:`k`. Finally a rewiring probability :math:`p` adds disorder to the lattice to create a more tight or relaxed small-world network.

        .. warning:: we recommend keeping the size of the initial lattice low. Large lattices may cause memory issues.

        :param list: a list of 4 arguments

            #. the size of the initial lattice :math:`n`.
            #. the dimension of the lattice across all spaces :math:`m`.
            #. the distance :math:`k` between each node pair to consider them as connected (a positive integer).
            #. the node rewiring probability :math:`p` (a py:class:`float` between 0 and 1).

        :param str name: optional, if you want to assign a name to the `name` graph attribute. Default is **"Small_World"**
        :param int, None seed: optional: provide a seed to the network generator in order to reproduce the same network over time. Defaults to :py:class:`None` (no seed is set).

        :return igraph.Graph: a py:class:`igraph,Graph` object that follow a small-world topology, initialized for Pyntacle usage

        :raise TypeError: if one of the elements in ``params`` is not one of the allowed types
        :raise ValueError: if ``params`` is not a list of size 4 and if any of its vlaues its outside their domain
        """

        if seed is not None:
            # print("THIS IS THE SEED", seed)
    
            if not isinstance(seed, int):
                raise TypeError("'seed' must be an integer, {} found".format(type(seed).__name__))

        else:
            # print("THIS IS THE SEED (ELSE)", seed)
    
            random.seed(seed)

        if not (len(params) == 4):
            raise ValueError(u'Wrong number of parameters for Small-world graph generation (4 params needed)')
        elif not (isinstance(params[0], int)
                  and isinstance(params[1], int)
                  and isinstance(params[2], int)
                  and isinstance(params[3], float)):

            raise TypeError(u'Wrong parameter type(s) for Small-world graph generation')
        elif not (0 < params[0] and 0 < params[1] and 0 < params[2] and 0 <= params[3] <= 1):
            raise ValueError(u'The value of one or more parameters is not allowed')

        else:
            graph = Graph.Watts_Strogatz(params[0], params[1], params[2], params[3])

            ad(graph=graph).graph_initializer(graph_name=(
            randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))

            return graph

    @staticmethod
    @generatorscanner
    def Tree(params: list, name: str="Tree", seed: int or None=None) -> Graph:
        r"""
        Generates a Network that Follows a `Tree <https://en.wikipedia.org/wiki/Tree_(graph_theory)>`_ topology, as
        described in the `Wolfram Alpha documentation <http://mathworld.wolfram.com/Tree.html>`_.

        Each vertex wil have as many children vertices specified by the second value in the ``param`` argument.

        This is a wrapper to the igraph `Tree <https://igraph.org/python/doc/igraph.GraphBase-class.html#Tree>`_ method

        :param params: a list of two arguments:

            #. the total number of nodes for the resulting :py:class:`igraph.Graph` object
            #. the number of *children* each *parent* node will have

        :param str name: optional, if you want to assign a name to the ``name`` graph attribute. Default is *Tree*.
        :param int, None seed: optional: provide a seed to the network generator in order to reproduce the same network over time. Defaults to :py:class:`None` (no seed is set).

        :return igraph.Graph: a py:class:`igraph,Graph` object that follow a Tree hierarchy, initialized for Pyntacle usage

        :raise TypeError: if one of the elements in ``params`` is not one of the allowed types
        :raise ValueError: if ``params`` is not a list of size 4 and if any of its vlaues its outside their domain
        """

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError(u"'seed' must be an integer, {} found".format(type(seed).__name__))
        else:
            random.seed(seed)

        if not (len(params) == 2):
            raise ValueError(u'Wrong number of parameters for Tree generation')
        elif not (isinstance(params[0], int) and isinstance(params[1], int)):
            raise TypeError(u'Wrong parameter type(s) for Tree generation')
        elif not (0 < params[0] and 0 < params[1]):
            raise ValueError(u'The value of one or more parameters is not allowed')
        else:
            graph = Graph.Tree(params[0], params[1])
            ad(graph=graph).graph_initializer(graph_name=(
            randomword(10, prefix="_".join([name, str(graph.vcount()), str(graph.ecount())]))))
            return graph