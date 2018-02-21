# external libraries
import logging
import os
import pickle  # for working with binary files
import re

from misc.binarycheck import is_binary_file
# pyntacle libraries
from igraph import Graph
from config import *
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.wrong_argument_error import WrongArgumentError
from utils.add_attributes import AddAttributes
from utils.graph_utils import GraphUtils

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


class BinaryToGraph():
    def __init__(self):

        self.logger = log

    def load_graph(self, file_name):

        """
        Use the "pickle" library to load_graph graph into a file, perform several checks
        
        :param file_name: Path to the binary file
        :return: an iGraph.Graph object
        """

        if not os.path.exists(file_name):
            raise FileNotFoundError("input file path does not exists")

        '''
        check if file is a binary
        '''
        if not is_binary_file(file_name):
            raise WrongArgumentError("file is not a binary")

        graph = pickle.load(open(file_name, "rb"))
        self.logger.info("loading file %s from binary" % file_name)
        if not isinstance(graph, Graph):
            raise IOError("binary is not a graph object")

        else:
            if graph.ecount() < 1 and graph.vcount() < 2:
                raise IllegalGraphSizeError("Graph must contain at least 2 nodes linked by one edge")

            else:
                AddAttributes(graph=graph).graph_initializer(
                    graph_name=os.path.splitext(os.path.basename(file_name))[0])

                if Graph.is_directed(graph):
                    '''
                    define graph as undirected
                    '''

                    self.logger.info("Converting graph to undirect")
                    graph = Graph.as_undirected(graph)

                GraphUtils(graph=graph).graph_checker()

                return graph
