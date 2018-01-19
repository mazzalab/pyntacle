"""
Abstract exporter class for undirected graphs with known topologies.
"""

import abc
from config import *
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


class IGraphExporter(object):
    __metaclass__ = abc.ABCMeta

    graph = None
    """:type: Graph"""

    def __init__(self, graph: Graph):
        self.graph = graph
        self.logger = log

    @abc.abstractmethod
    def export_graph(self, file_name: str, sep):
        """
        The abstract exporter method
        
        :param file_name: Name of the output file
        :param sep: desired separator 
        """
        return
