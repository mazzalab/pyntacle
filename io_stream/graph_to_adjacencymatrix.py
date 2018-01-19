""""
It serialize and exports a Graph object to file, as adjacency matrix
"""

import os

from igraph import Graph
from config import *
from exception.notagraph_error import NotAGraphError
from io_stream.igraph_exporter import IGraphExporter
import pandas as pd
from numpy import savetxt
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


class GraphToAdjacencyMatrix(IGraphExporter):
    """
    It serializes and exports a Graph object to file, as adjacency matrix
    """

    def __init__(self, graph: Graph):
        # IGraphExporter.__init__(self, graph)
        self.graph = graph
        self.logger = log
        if not isinstance(graph, Graph):
            raise NotAGraphError("Object is not a graph")

    def export_graph(self, file_name: str, sep=None, header=False):
        """
        It exports a Graph object to a textual file, as adjacency matrix
        
        :param file_name: The name of the file where print the adjacency matrix to
        :param sep: desired separator (default is "\t")
        """
        directory = os.path.dirname(file_name)

        if sep == None:
            sep = "\t"

        if not directory:
            file_name = os.getcwd() + os.path.sep + file_name
        elif not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        adjmatrix = list(self.graph.get_adjacency())
        if header:
            nameslist = [name for name in self.graph.vs()["name"]]
            adjmatrix = pd.DataFrame(adjmatrix, columns=nameslist)
            adjmatrix.insert(0, column='', value=nameslist)
            adjmatrix.to_csv(file_name, sep=sep, header=True, index=False)
        else:
            savetxt(file_name, adjmatrix, delimiter=sep, fmt='%1i')

        self.logger.info("File written to the file: %s" % file_name)
