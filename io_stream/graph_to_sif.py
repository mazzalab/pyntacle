""""
It serialize and exports a Graph object to file, as simple interaction format (sif)
"""

# external libraries
import os
import sys
from config import *

# pyntacle Libraries
from igraph import Graph
from utils.graph_utils import GraphUtils as gu
from exception.notagraph_error import NotAGraphError
from io_stream.igraph_exporter import IGraphExporter

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The pyntacle Project"
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


class GraphToSif(IGraphExporter):
    """
    It serializes and exports a Graph object to file, as adjacency list
    """
    logger = None

    def __init__(self, graph: Graph):
        # IGraphExporter.__init__(self, graph)
        # super(GraphToSif, self).__init__(graph)
        self.graph = graph

        self.logger = log

        if not isinstance(graph, Graph):
            raise NotAGraphError("Object is not a graph")

        # create a copy of the graph
        #check that graph is compatible with our standards
        gu(graph=graph).graph_checker()  #check for output compatibility


        self.graph = Graph.copy(self.graph)


    def export_graph(self, file_name: str, sep=None, header=False):
        """
        It exports a Graph object to a textual file, as sif file
        
        :param file_name: The name of the file where print the adjacency matrix to
        :param sep: a separator to separe edges. If none, "\t" will be used
        """

        directory = os.path.dirname(file_name)

        if sep == None:
            sep = "\t"

        if not directory:
            file_name = os.path.join(os.getcwd(), file_name)

        if not os.path.exists(directory):
            raise NotADirectoryError("Output directory does not exist")

        self.logger.info("Writing sif file at {}".format(file_name))

        with open(file_name, "w") as outfile:
            self.logger.info("Writing the input graph to sif file at path {}".format(file_name))

            if header:
                self.logger.info("Writing header")

                if "__sif_interaction_name" not in self.graph.attributes() or self.graph[
                    "__sif_interaction_name"] is None:
                    head = "\t".join(["Node1", "Interaction", "Node2"]) + "\n"

                else:
                    head = "\t".join(["Node1", self.graph["__sif_interaction_name"], "Node2"]) + "\n"

                outfile.write(head)

            # keep  track of the connected indices
            nodes_done_list = []

            for edge in self.graph.es():

                if "name" in self.graph.vs.attributes() or len(self.graph.vs(edge.source)["name"]) == 1 or len(
                        self.graph.vs(edge.target)["name"]) == 1:
                    source = edge.source
                    target = edge.target

                    if source not in nodes_done_list:
                        nodes_done_list.append(source)

                    if target not in nodes_done_list:
                        nodes_done_list.append(target)

                    if edge["__sif_interaction"] is None:

                        outfile.write(sep.join([self.graph.vs(source)["name"][0], "interacts_with",
                                                self.graph.vs(target)["name"][0]]) + "\n")

                    else:

                        outfile.write(sep.join([self.graph.vs(source)["name"][0], edge["__sif_interaction"],
                                                self.graph.vs(target)["name"][0]]) + "\n")

                else:
                    # print(type(self.graph.vs(edge.target)["name"]))
                    raise ValueError(
                        "vertex \"name\" attribute is unproperly formatted. Cannot interpret him. Quitting")

            # remove vertices from graph in order to write remaining vertices
            remaining_nodes = list(set(self.graph.vs().indices) - set(nodes_done_list))

            for i in remaining_nodes:
                outfile.write(self.graph.vs(i)["name"][0] + "\n")

            self.logger.info("Graph written to the file: %s" % file_name)


