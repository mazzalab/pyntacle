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

"""
Give a measure of sparseness of a graph using 3 different metrics studied in the past few years
"""

import math
from misc.graph_routines import *


class Sparseness:
    @staticmethod
    @check_graph_consistency
    def completeness_Mazza(graph) -> float:
        """
        Compute the completeness index as described by Mazza *et al.* [Ref]_for an undirect unweighted graph.
        They define completeness as the total number of edges over all possible edges minus the number of non-edges
        (so the number of zeros in the adjacency matrix)
        [Ref] https://doi.org/10.1093/bib/bbp060
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the completeness index of the graph
        """
        # get the total number of nonzero elements in an adjacency matrix
        num = graph.ecount()  # total number of real edges
        tote = (graph.vcount() * (graph.vcount() - 1)) / 2
        denom = tote - graph.ecount()  # total number of non-edges
        if denom == 0:
            raise ZeroDivisionError("the graph is complete, thus the completeness index is out of bound")

        completeness = num / denom

        return round(completeness, 5)

    @staticmethod
    @check_graph_consistency
    def completeness_XXX(graph) -> float:
        """
        We implement the completeness measure as implemented by **XXX** in [Ref]_ to give a measure of sparsness of a
        graph. We refer to the paper by **XXX** to explain how this compacteness is computed.
        [Ref] **Applied Mathematics DOI**
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return:
        """
        #todo change this here and in enums
        root_k = graph.vcount()  # k is a dimension of the adjacency matrix (so the square of the vcount)
        k = math.pow(root_k, 2)
        first_part = root_k - 1  # (root(k)-1)
        z = k - (graph.ecount() * 2)  # number of zeros in the matrix
        second_part = (k / z) - 1
        completeness = first_part * second_part

        return round(completeness, 5)

    @staticmethod
    @check_graph_consistency
    def compactness(graph) -> float:
        """
        Computes the compactness index described by Randìc and DeAlba [Ref]_ in order to mathematically estimate the
        sparseness of the graph. Compacteness is evaluates by theking the square of the number of vertices in a graph
        over the total number of connected vertices minus one and multiplying it by one minus the reciprocal of the
        total number of edges in the graph.
        [Ref]https://pubs.acs.org/doi/abs/10.1021/ci970241z?journalCode=jcics1
        :param igraph.Graph graph: an igraph.Graph object. The graph should have specific properties. Please see the
        "Minimum requirements" specifications in pyntacle's manual
        :return: a float representing the compactness index of the graph
        """
        # first part of the equation: (square of the nodes/edges*2)-1
        a = math.pow(graph.vcount(), 2)
        b = graph.ecount() * 2
        numa = a / b - 1
        numa = math.pow(numa, -1)
        # second part of the equation (1-1/total number of nodes)
        numb = 1 - (1 / graph.vcount())
        numb = math.pow(numb, -1)
        # finally
        compactness = numa * numb

        return round(compactness, 5)
