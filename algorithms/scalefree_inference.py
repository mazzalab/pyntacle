'''
this module covers the inference of a scale free fitted power law value given a network
'''
import os
from igraph import statistics as st
from igraph import Graph
from exception.notagraph_error import NotAGraphError
from algorithms.local_topology import LocalTopology
from config import *

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "14 November 2016"
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


class Fit_Power_Law():
    logger = None
    """:type: Logger"""

    def __init__(self, graph=None):
        self.logger = log

        if not graph:
            raise TypeError

        if type(graph) is not Graph:
            self.logger.fatal("Object is not a graph")
            raise NotAGraphError

        else:
            self.graph = graph

    def alpha(self, recalculate: bool, xmin=None):
        '''
        Find the alpha of the power law of a Graph Object
        
        :param xmin: level of the degree distribution toi start from
        '''
        if not recalculate or "alpha" not in self.graph.attributes():
            self.logger.info("computing alpha for this graph and storing as graph attribute")
            self.degr = LocalTopology(self.graph).degree()
            if not xmin:
                self.alpha = st.power_law_fit(self.degr).alpha

            else:
                self.alpha = st.power_law_fit(self.degr, xmin=xmin).alpha
            self.graph["alpha"] = self.alpha
        else:
            self.logger.info("Power fit is already in Graph attributes (\"alpha\")")
            return self.graph
