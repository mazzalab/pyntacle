"""
Generator classes of undirected graphs with known topologies.
Envisioned models are: Erdos-Renyi, Scale-free, Tree and Small-world
"""
import random
import string

# external libraries
from igraph import Graph
from config import *
from exception.illegal_argument_number_error import IllegalArgumentNumberError
# Dedalus Libraries
from utils.add_attributes import AddAttributes

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The Dedalus Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 October 2016"
__license__ = u"""
  Copyright (C) 20016-2017  Tommaso Mazza <t,mazza@css-mendel.it>
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


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class ErdosRenyiGenerator:
    """
    Class generator of Erdos-Renyi-based random graphs with a specified number of nodes and a probability of wiring
    """

    def __init__(self):
        self.logger = log

    def generate(self, parameters):
        """
        It generates a random graph based on the Erdos-Renyi model
        
        :param parameters: List of two parameters. 1: (int) the number of vertices, 2: a(float) if specifying the probability of nodes connection, else an (int) if specifying the number of edges
        :return: The generated igraph.Graph object
        :raises TypeError: if the type of the input parameters is not correct
        :raises ValueError: if the value of the input parameters is not correct
        """
        if not (len(parameters) == 2):
            raise IllegalArgumentNumberError('Wrong number of parameters for Erdos-Renyi graph generation')
        elif not (isinstance(parameters[0], int) and isinstance(parameters[1], (float, int))):
            raise TypeError('Wrong parameter type(s) for Erdos-Renyi graph generation')


        elif not (0 < parameters[0] and 0 <= parameters[1]):
            raise ValueError('The value of one or more parameters is not allowed')

        else:
            if isinstance(parameters[1], float) and 0 <= parameters[1] <= 1:
                self.logger.info(
                    "Creating an Erdos-Renyi random graph using a probability rewiring of {} ".format(parameters[1]))
                graph = Graph.Erdos_Renyi(parameters[0], p=parameters[1])

            elif isinstance(parameters[1], int) and parameters[1] > 1:
                self.logger.info("Creating an Erdos-Renyi random graph using  a total number of edges of {}".format(
                    str(parameters[1])))
                graph = Graph.Erdos_Renyi(parameters[0], m=parameters[1])

            else:
                raise ValueError('second parameter is not a  positive float or an integer > 1')

            graph_name = "_".join(["Random", str(graph.vcount()), str(graph.ecount()), randomword(10)])

            AddAttributes(graph=graph).graph_initializer(graph_name=graph_name)

            return graph


class BarabasiAlbertGenerator:
    """
    Class generator of Erdos-Renyi-based random graphs with a specified number of nodes and a probability of wiring
    """

    def __init__(self):
        self.logger = log

    def generate(self, parameters):
        """
        It generates a graph based on the Barabasi-Albert model
        
        :param parameters: List of two parameters. 1: (int) the number of vertices, 2: (int) the number of outgoing edges
        :return: The generated igraph.Graph object
        """
        if not (len(parameters) == 2):
            raise IllegalArgumentNumberError('Wrong number of parameters for Scale-free graph generation')
        elif not (isinstance(parameters[0], int) and isinstance(parameters[1], int)):
            raise TypeError('Wrong parameter type(s) for Scale-free graph generation')
        elif not (0 < parameters[0] and 0 < parameters[1]):
            raise ValueError('The value of one or more parameters is not allowed')
        else:
            self.logger.info("Creating a (scale-free) graph based on the Barabasi-Albert model")
            graph = Graph.Barabasi(parameters[0], parameters[1])

            graph_name = "_".join(["Scale-Free", str(graph.vcount()), str(graph.ecount()), randomword(10)])

            AddAttributes(graph=graph).graph_initializer(graph_name=graph_name)

            return graph


class TreeGenerator:
    """
    Class generator of a Tree with a specified number of nodes and children of each node
    """

    def __init__(self):
        self.logger = log

    def generate(self, parameters):
        """
        It generates a tree in which almost all vertices have the same number of children
        
        :param parameters: List of two parameters. 1: (int) the number of vertices, 2: (int) the number of children of a vertex in the graph
        :return: The generated igraph.Graph object
        """
        if not (len(parameters) == 2):
            raise IllegalArgumentNumberError('Wrong number of parameters for Tree generation')
        elif not (isinstance(parameters[0], int) and isinstance(parameters[1], int)):
            raise TypeError('Wrong parameter type(s) for Tree generation')
        elif not (0 < parameters[0] and 0 < parameters[1]):
            raise ValueError('The value of one or more parameters is not allowed')
        else:
            self.logger.info("Creating a tree in which almost all vertices have the same number of children")
            graph = Graph.Tree(parameters[0], parameters[1])

            graph_name = "_".join(["Tree", str(graph.vcount()), str(graph.ecount()), randomword(10)])

            AddAttributes(graph=graph).graph_initializer(graph_name=graph_name)

            return graph


class SmallWorldGenerator:
    """
    Class generator of Watts_Strogatz -based random graphs with a specified dimension of the lattice, the size of the
    lattice along all dimensions, a value giving the distance (number of steps) within which two vertices
    will be connected and a rewiring probability
    """

    def __init__(self):
        self.logger = log

    def generate(self, parameters):
        """
        It generates a graph based on the Watts_Strogatz model
        
        :param parameters: List of 4 parameters. 1: (int) the dimension of the lattice, 2: (int) the size of the lattice along all dimensions, 3: (int) value giving the distance (number of steps) within which two vertices will be connected, 4: (float) rewiring probability
        :return: The generated igraph.Graph object
        """
        if not (len(parameters) == 4):
            raise IllegalArgumentNumberError('Wrong number of parameters for Small-world graph generation')
        elif not (isinstance(parameters[0], int) and isinstance(parameters[1], int) and isinstance(parameters[2],
                                                                                                   int) and isinstance(
            parameters[3], float)):
            raise TypeError('Wrong parameter type(s) for Small-world graph generation')
        elif not (0 < parameters[0] and 0 < parameters[1] and 0 < parameters[2] and 0 <= parameters[3] <= 1):
            raise ValueError('The value of one or more parameters is not allowed')
        else:
            self.logger.info("Creating a Small-world graph")
            graph = Graph.Watts_Strogatz(parameters[0], parameters[1], parameters[2], parameters[3])

            graph_name = "_".join(["Small-World", str(graph.vcount()), str(graph.ecount()), randomword(10)])

            AddAttributes(graph=graph).graph_initializer(graph_name=graph_name)

            return graph
