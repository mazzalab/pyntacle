""""
This class parses a serialized graph (adjacency matrix) and converts it into a Graph
"""

import numpy as np
from igraph import *
from config import *
from exception.unproperlyformattedfile_error import UnproperlyFormattedFileError
from exception.wrong_argument_error import WrongArgumentError
from io_stream.igraph_importer import IGraphImporter
from utils import adjmatrix_utils
from utils.add_attributes import AddAttributes

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "03 / 11 / 2016"
__creator__ = "Tommaso Mazza"
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


class AdjacencyMatrixToGraph(IGraphImporter):
    """
    This class parses a serialized graph and converts it into a Graph
    """

    def __init__(self):
        # super(AdjacencyMatrixToGraph, self).__init__()
        self.logger = log

    def import_graph(self, file_name: str, header: bool, separator: str) -> Graph:
        """
        It imports a serialized graph as adjacency matrix and converts it into a Graph object
        
        :param separator: The string that separates the matrix elements in a row
        :param header: Whether a header line is present in the file
        :param file_name: The name of the adjacency matrix file
        :param check_direct: if you want to check if the matrix is squared or not
        :return: The converted graph
        :raises IOError: When the input file does not exist
        :raises WrongArgumentError: When the input file does not contain the specified separator
        :raises UnproperlyformattedfileError: when the input file is not formatted as an adjacency matrix
        """
        if not os.path.isfile(file_name):
            raise IOError("File not found error")
        else:
            # graph = Graph()
            """:type: Graph"""
            # check if adjacency matrix is squared

            if not adjmatrix_utils.AdjmUtils(file=file_name, header=header, separator=separator).is_squared():
                raise UnproperlyFormattedFileError("Matrix is not squared")

            with open(file_name, "r") as adjmatrix:
                iterator = iter(adjmatrix.readline, '')

                first_line = next(iterator, None).rstrip()
                if separator not in first_line:
                    raise WrongArgumentError(
                        'The specified separator "{}" is not present in the adjacency matrix file'.format(separator))
                else:
                    self.logger.info("Reading the adjacency matrix")
                    n_cols = len(first_line.split(separator))

            if header:
                try:
                    f = np.loadtxt(file_name, skiprows=1, usecols=(tuple(range(1, n_cols))), delimiter=separator)
                except:
                    raise UnproperlyFormattedFileError("File is not parsable by numpy")
                node_names = open(file_name).readlines()[0].rstrip().split(separator)[1:]
                # node_names = f.astype(int).astype(str)[0, 1:]
                # print(node_names)
            else:
                f = np.loadtxt(file_name, delimiter=separator)
                node_names = [str(x) for x in list(range(0, len(f)))]

            # print(f)
            graph = Graph.Adjacency(f.tolist(), mode='undirected')
            graph = Graph.simplify(graph, loops=True, multiple=False)

            # add standard attributes to graph
            AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file_name))[0], node_names=node_names)

            self.logger.info("Adjacency matrix imported")
            return graph
