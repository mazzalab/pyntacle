import pickle
import os
from config import *
from exception.notagraph_error import NotAGraphError
from exception.illegal_graph_size_error import IllegalGraphSizeError
from igraph import Graph

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

class GraphToBinary():
    logger = None

    def __init__(self, graph):
        self.logger = log
        if type(graph) is not Graph:
            raise NotAGraphError("object is not a graph")

        if graph.vcount() < 1:
            raise IllegalGraphSizeError("Object does not have edges")
        elif graph.ecount() < 1:
            raise IllegalGraphSizeError("Graph has no nodes")
        else:
            self.graph = graph

    def save(self, file_name):
        '''
        Take a graph object already instanced and save it to a binary file
        
        :param outfile: an output file
        '''
        if os.path.isdir(os.path.dirname(file_name)):
            self.logger.info("writing graph to file %s" % file_name)
            pickle.dump(self.graph, open(file_name, "wb"))
