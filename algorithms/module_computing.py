from igraph import Graph, VertexClustering

from algorithms import key_player
from algorithms import sparseness
from algorithms.greedy_optimization import GreedyOptimization
from utils import modules_utils
from config import *

'''
this module computes KPP-POS, KPP-NEG, completeness and compactness for a group of modules
'''

__author__ = "Daniele Capocefalo, Tommaso Mazza"
__copyright__ = "Copyright 2016, The Dedalus Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "14 November 2016"
__license__ = u"""
  Copyright (C) 20016-2017  Tommaso Mazza <t,mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc.,  51 Franklin Street, Fifth Floor, Boston, MA
  02110-1301 USA
  """


class ComputeModuleMetrics(object):
    logger = None

    def __init__(self, modules: VertexClustering, graph: Graph, minset=None):
        '''
        implement all the necessary step to check a graph object
        :param modules: a VertexClustering object outputted by one of the several methods of iGraph for module
        clustering see iGraph manual for more information
        '''
        self.modules = list(modules)
        self.graph = graph

        self.logger = log
        self.inner = modules_utils.ModuleUtils(graph=self.graph, modules=self.modules)
        if not minset:
            self.subgraphs = self.inner.get_subgraphs()
        else:
            self.subgraphs = self.inner.get_subgraphs(minset=minset)

        self.graph = graph

    def get_subgraphs(self):
        return self.subgraphs

    def modules_sparseness(self, measure: sparseness.SparsenessAttribute):
        '''
        function that computes the module sparseness
        :param measure: either "completeness" or completeness, according to the measure you're trying to implement
        :param minset: minimum module size on which to recompute completeness
        :param recalculate: whether to recompute completeness o
        '''

        # TODO: implement recalculate?
        if measure == sparseness.SparsenessAttribute.completeness:
            for i, subg in enumerate(self.subgraphs):
                self.inner.add_subgraph_attribute(attrind=i, attrname="completeness",
                                                  attribute=sparseness.Sparseness(subg).completeness())

        elif measure == sparseness.SparsenessAttribute.compactness:
            for i, subg in enumerate(self.subgraphs):
                self.inner.add_subgraph_attribute(attrind=i, attrname="compactness",
                                                  attribute=sparseness.Sparseness(subg).compactness())

        else:
            self.logger.error("measure you specified cannot be computed")
            raise ValueError("measure is not present")

    def weighted_completeness(self, module_ind, method: str):
        '''
        weight each completeness or compactness index to each module
        :return:
        '''
        # TODO : implement a weighted measure of completeness
        pass

    def raw_greedy_optimization(self, modules, kp_measure: key_player.KeyplayerAttribute, kpp_size: int):
        if not kp_measure in key_player.KeyplayerAttribute.__members__:
            self.logger.error("Measure is not implemented")
            raise ValueError("KP measure is not present")

        if isinstance(modules, int):
            self.logger.info("Computing greedy optimization for single modules")
            kp = GreedyOptimization(graph=self.subgraphs[modules])

            # self.inner.add_subgraph_attribute(attrind=modules, attrname=kp_measure,attr


        elif isinstance(modules, list):
            self.logger.info("module list found")
            for mod in modules:
                if not isinstance(mod, int):
                    self.logger.error("module list must be made of integers")
                    raise ValueError("element is not an int")
                    # TODO multiple greedy optimization for each module
