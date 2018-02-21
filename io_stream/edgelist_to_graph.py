""""
This class parses a serialized graph (adjacency list) and converts it into a Graph
"""
# external libraries
from igraph import *
import pandas as pd

# pyntacle Libraries
from exceptions.wrong_argument_error import WrongArgumentError
from io_stream.igraph_importer import IGraphImporter
from utils import edgelist_utils
from utils.add_attributes import AddAttributes
from config import *

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

class EdgeListToGraph(IGraphImporter):
    """
    This class parses a serialized graph (adjacency list) and converts it into a Graph
    """

    def __init__(self):
        # super(EdgeListToGraph, self).__init__()
        self.logger = log

    def import_graph(self, file_name: str, header: bool, separator: str) -> Graph:
        """
        It imports a serialized graph as adjacency list and converts it into a Graph object
        
        :param separator: The string that separates the list elements in a row
        :param header: Whether a header line is present in the file
        :param file_name: The name of the adjacency list file
        :return: Graph: The converted graph
        :raises IOError: When the input file does not exist
        :raises WrongArgumentError: When the input file does not contain the specified separator
        :raises UnproperlyformattedfileError: when the input file is not formatted as an edge list
        """

        if not os.path.exists(file_name):
            raise IOError("File not found error")


        eglutils = edgelist_utils.EglUtils(file=file_name, header=header, separator=separator)

        if not eglutils.is_pyntacle_ready():
            raise ValueError("Edgelist is a multigraph or there is some direct edge")

        graph = Graph()
        """:type: Graph"""
        graph.vs["name"] = []

        self.logger.info("Reading the edge list")

        if header:

            adj = pd.read_csv(file_name, sep=separator, header=0)

        else:
            adj = pd.read_csv(file_name, sep=separator, header= None)

        """:type: pandas dataframe"""


        #remove duplicates:
        adj.values.sort()
        adj = adj.drop_duplicates()

        #add all vertices to graph
        graph.add_vertices(list(set(adj[0].tolist() + adj[1].tolist())))
        graph.add_edges([tuple(x) for x in adj.values])


        # add missing attribute to graph
        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file_name))[0])

        self.logger.info("Edge list imported")
        return graph
