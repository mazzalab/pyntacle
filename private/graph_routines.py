"""Python decorators for consistency check of graph and graph's elements"""

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


from tools.graph_utils import *
from functools import wraps
from collections import Counter


def check_graph_consistency(func: object) -> object:
    """
    It checks the structural integrity of a graph
    :param func: The decorated function
    :return: The function in input if the check was successful
    """
    @wraps(func)
    def func_wrapper(graph, *args, **kwargs):
        if not isinstance(graph, Graph):
            raise WrongArgumentError("The input graph is not an instance of igraph.Graph")

        if graph.vcount() == 0:
            raise IllegalGraphSizeError('The input graph does not contain any vertex')

        # if graph.ecount() < 1:
        #     raise IllegalGraphSizeError("Input Graph does not have any edges")

        if "name" not in graph.attributes():
            raise MissingAttributeError("Graph must have a \"name\" attribute")

        if "name" not in graph.vs.attributes():
            raise MissingAttributeError("Input vertices don't have a \"name\" attribute")
        else:
            if None in graph.vs["name"]:
                raise MissingAttributeError("The 'name' attribute must be assigned to all nodes of the graph")

            counter = Counter(graph.vs["name"])
            duplicates = [v for k, v in counter.items() if v > 1]
            if duplicates:
                raise MissingAttributeError("The 'name' attribute is duplicated for [{}] nodes".format(duplicates))

        if Graph.is_directed(graph):
            raise UnsupportedGraphError("The input graph is directed. Pyntacle currently supports undirected graphs")

        if not Graph.is_simple(graph):
            raise UnsupportedGraphError(
                "The input graph contains self loops or multiple edges. Pyntacle currently supports simple graphs")

        return func(graph, *args, **kwargs)
    return func_wrapper


def vertex_doctor(func):
    """
    It decorates functions with at a *graph* and a *node* or a list/tuple of *nodes* as parameters.
    It checks that the specified nodes are all contained in the graph
    :param func: The decorated function
    :return: The function in input if the check was successful
    """
    @wraps(func)
    def func_wrapper(graph, nodes=None, *args, **kwargs):
        if nodes:
            all_names_in_graph = graph.vs['name']

            if isinstance(nodes, str):
                nodes = [nodes]
            elif isinstance(nodes, tuple):
                nodes = list(nodes)
            elif not isinstance(nodes, list):
                raise TypeError("The 'node' parameter must be of type string, list or tuple")

            if not all(isinstance(node, str) for node in nodes):
                raise TypeError("Node names must be string type")

            if any(node not in all_names_in_graph for node in nodes):
                remaining = list(set(nodes) - set(all_names_in_graph))
                if len(remaining) > 0:
                    raise KeyError('The nodes: {} are not present in the input graph'.format(remaining))

        return func(graph, nodes, *args, **kwargs)

    return func_wrapper
