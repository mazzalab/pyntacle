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

""" **a series of decorators to improve the usability of some pyntacle's function, like 
checking if the `igraph.Graph` object is compatible with pyntacle's specifications, verify the presence of nodes 
in the input graph, give elapsed time of execution and so on"""

from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.unsupported_graph_error import UnsupportedGrapherror
from exceptions.wrong_argument_error import WrongArgumentError
from config import *
from utils.graph_utils import *
import time
from functools import wraps
# todo recheck all the init properties of an igraph Graph (in IO)

def check_graph_consistency(func):
    """
    Decorator for the checking the structural integrity of a graph
    General properties of an accepted Graph

    :param func:
    :return: the function (usually a static method) ready to be used for an igraph.Graph object
    """
    @wraps(func)
    def func_wrapper(graph, *args, **kwargs):
        if not isinstance(graph, Graph):
            raise WrongArgumentError("input is not an igraph.Graph object")

        if graph.vcount() == 0:
            raise IllegalGraphSizeError('Input graph does not contain any vertex')

        # if graph.ecount() < 1:
        #     raise IllegalGraphSizeError("Input Graph does not have any edges")

        if "name" not in graph.attributes():
            raise MissingAttributeError("Graph must have a \"graph_name\" attribute")

        if "name" not in graph.vs.attributes():
            raise MissingAttributeError("Input graph does not have a \"name\" attribute")
        else:
            if None in graph.vs("name"):
                raise UnsupportedGrapherror("\"name\" vertex attribute contains None values, all \"name\"s should "
                                            "be initialized")

            if len(graph.vs["name"]) != len(set(graph.vs["name"])):
                raise UnsupportedGrapherror("\"name\" vertex attribute should be unique to each vertex")

        if Graph.is_directed(graph):
            raise UnsupportedGrapherror("Graph is direct; Pyntacle only supports direct graphs")

        if not Graph.is_simple(graph):
            raise UnsupportedGrapherror(
                "Input Graph contains self loops or multiple edges. Pyntacle only supports simple graphs.")

        return func(graph, *args, **kwargs)

    return func_wrapper


def vertexdoctor(func):
    """
    Decorator for check whether the node name exists in a Graph and if the nodes are consisten within the graph
    :param func: a function that takes in input a node name
    :return: the function (usually a static method) ready to be used for an igraph.Graph object
    """
    @wraps(func)
    def func_wrapper(graph, nodes=None, *args, **kwargs):
        if nodes is not None:

            if not isinstance(nodes, (str, list)):
                raise TypeError('Node name must be a string or a list of strings')

            else:
                if isinstance(nodes, list):

                    if not all(isinstance(x, str) for x in nodes):
                        raise TypeError('Node name list must contain only strings')

                    else:
                        remains = list(set(nodes) - set(graph.vs["name"]))

                        if len(remains) > 0:
                            raise KeyError('{} are not present in the input graph'.format(remains))

                        if len(nodes) > graph.vcount():
                            raise WrongArgumentError(
                                "input node list is greater than the number of vertieces in the input graph (input nodes are {}, graph vertices are {1})".format(
                                len(nodes), graph.vcount()))
                else:
                    if nodes not in graph.vs['name']:
                        raise KeyError('{} is not present in vertex names'.format(nodes))
                    nodes = [nodes] #put it into a list directly

        return func(graph, nodes, *args, **kwargs)

    return func_wrapper
