""""
It serialize and exports a Graph object to file, as adjacency list
"""

import os

from igraph import Graph
from config import *
from exception.notagraph_error import NotAGraphError
from io_stream.igraph_exporter import IGraphExporter

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


class GraphToEdgeList(IGraphExporter):
    """
    It serializes and exports a Graph object to file, as adjacency list
    """

    def __init__(self, graph: Graph):
        # IGraphExporter.__init__(self, graph)
        # super(GraphToEdgeList, self).__init__(graph)
        self.graph = graph
        self.logger = log
        if not isinstance(graph, Graph):
            raise NotAGraphError("Object is not a graph")

    def export_graph(self, file_name: str, sep=None, header=False):
        """
        It exports a Graph object to a textual file, as adjacency list
        
        :param file_name: The name of the file where print the adjacency matrix to
        """
        directory = os.path.dirname(file_name)
        if sep == None:
            sep = "\t"

        if not directory:
            file_name = os.getcwd() + os.path.sep + file_name
        elif not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        adjlist = list(self.graph.get_adjlist())
        with open(file_name, "w") as outfile:

            self.logger.info("Formatting the graph and writing to file ...")

            if header:
                outfile.write("Node_Name\tNode_Name\n")

            for i, ver in enumerate(adjlist):
                # print(ver)
                if "name" not in self.graph.vs.attributes():
                    outfile.writelines([str(i) + sep + str(x) + "\n" for x in adjlist[i]])
                else:
                    if len(self.graph.vs(i)["name"]) > 1:
                        raise IOError("there is more than one node with the same name, cannot identify unique nodes")
                    else:
                        outfile.writelines(
                            [self.graph.vs(i)["name"][0] + sep + x + "\n" for x in self.graph.vs(ver)["name"]])

            self.logger.info("File written to the file: %s" % file_name)
