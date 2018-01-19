'''
this module import a sif file into n igraph graph
'''
from config import *
import os

from igraph import Graph

from io_stream.igraph_importer import IGraphImporter
from utils.add_attributes import AddAttributes

from utils.graph_utils import GraphUtils

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


class SifToGraph(IGraphImporter):
    """
    This class parses a simple interaction format (SIF) and converts it into an igraph.Graph object
    """
    logger = None

    def __init__(self):
        # super(SifToGraph, self).__init__()
        self.logger = log

    def import_graph(self, file_name: str, header: bool, sep: str) -> Graph:
        """
        It imports a serialized graph as sif file and converts it into a Graph object
        
        :param sep: The string that separates the list elements in a row
        :param header: Whether a header line is present in the file
        :param file_name: The name of the adjacency list file
        :rtype: Graph: The converted graph
        :raises IOError: When the input file does not exist
        :raises WrongArgumentError: When the input file does not contain the specified separator
        :raises UnproperlyformattedfileError: when the input file is not formatted as an edge list
        """

        if not os.path.isfile(file_name):
            raise IOError("File not found error")

        graph = Graph()
        """:type: Graph"""
        graph.vs["name"] = []

        sif_list = [line.rstrip('\n').split(sep) for line in open(file_name, "r")]

        """:type: list[str]"""

        if header:
            self.logger.info(
                "storing second column of header as edge attribute \"__sif_interaction\". Interaction name can be found in the graph attribute \"__sif_interaction_name\"")
            graph["__sif_interaction_name"] = sif_list[0][1]
            graph.es()["__sif_interaction"] = None
            del sif_list[0]

        else:
            graph["__sif_interaction_name"] = None

        for i, elem in enumerate(sif_list):

            if len(elem) == 0:
                pass  # this should be an empty line

            elif len(elem) == 1:  # add the single node as isolate
                if elem[0] not in graph.vs()["name"]:
                    graph.add_vertex(name=elem[0])

            elif len(elem) == 3:

                # print(elem)
                first = elem[0]
                second = elem[2]

                if first not in graph.vs()["name"]:
                    graph.add_vertex(name=first)

                if second not in graph.vs()["name"]:
                    graph.add_vertex(name=second)

                if not graph.are_connected(first, second):
                    graph.add_edge(source=first, target=second, __sif_interaction=elem[1])

                else:
                    self.logger.warning(
                        "an edge already exist between node {0} and node {1}. This should not happen, as Dedalus only supports simple graphs.\n Attribute \"__sif_interaction\n Will skip line {2}".format(
                            first, second, i))
                    node_ids = GraphUtils(graph=graph).get_node_indices(node_names=[first, second])
                    graph.es(graph.get_eid(node_ids[0], node_ids[1]))["__sif_interaction"] = elem[1]


            elif len(elem) >= 4:
                first = elem[0]
                interaction = elem[1]
                other_nodes = elem[2:]

                if first not in graph.vs()["name"]:
                    graph.add_vertex(name=first)

                for n in other_nodes:
                    if n not in graph.vs()["name"]:
                        graph.add_vertex(name=n)
                    if not graph.are_connected(first, n):
                        graph.add_edge(source=first, target=n, __sif_interaction=interaction)

                    else:
                        self.logger.warning(
                            "an edge already exist between node {0} and node {1}. This should not happen, as Dedalus only supports simple graphs.\n Attribute \"__sif_interaction\n will be override".format(
                                first, n))
                        node_ids = GraphUtils(graph=graph).get_node_indices(node_names=[first, n])
                        graph.es(graph.get_eid(node_ids[0], node_ids[1]))["__sif_interaction"] = interaction

            else:
                self.logger.warning("line {} is malformed, hence it will be skipped".format(i))

                # print(g.vs()["name"])

        # add missing attribute to graph
        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file_name))[0])

        '''
        define graph as undirected
        '''
        graph = Graph.as_undirected(graph)
        self.logger.info("Sif File imported")
        return graph
