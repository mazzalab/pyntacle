"""Python decorators for consistency check of graph and graph's elements"""

__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
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


from tools.graph_utils import *
from functools import wraps
# from collections import Counter
# from tools.graph_utils import GraphUtils as gu


def check_graph_consistency(func):
    r"""
    It checks the structural integrity of a graph

    :param func: The decorated function
    :return: The function in input if the check was successful
    """
    @wraps(func)
    def func_wrapper(graph, *args, **kwargs):
        from tools.graph_utils import GraphUtils
        # GraphUtils(graph).check_graph()

        return func(graph, *args, **kwargs)
    return func_wrapper


def vertex_doctor(func):
    r"""
    It decorates functions with at a *graph* and a *node* or a list/tuple of *nodes*.
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
