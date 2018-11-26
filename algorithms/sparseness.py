"""
Measure the global sparseness of graphs.
Read the section "TOOLS FOR ESTIMATING THE DIVISIBILITY OF NETWORKS" of the paper entitled "Estimating the
divisibility of complex biological networks by sparseness indices" available at
https://doi.org/10.1093/bib/bbp060 for a quick overview
"""


__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "13/04/2018"
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


import math
from private.graph_routines import check_graph_consistency

class Sparseness:
    @staticmethod
    @check_graph_consistency
    def completeness_naive(graph) -> float:
        """
        Compute the naive version of the completeness index, as described by Mazza *et al.* [Ref]_.
        They define completeness as the the ratio between the number of non-zero *E* and zero *V* entries in the
        adjacency matrix of a graph.
        [Ref] https://doi.org/10.1093/bib/bbp060
        :param igraph.Graph graph: an igraph.Graph object.
        :return: The naive computation of the completeness index
        """

        # total number of non-zero elements (E)
        if graph.is_directed():
            num = graph.ecount()
        else:
            num = graph.ecount()*2

        # total number of possible edges (self-loops excluded)
        node_tot = graph.vcount()
        if graph.is_directed():
            maxe = (node_tot * (node_tot - 1)) / 2
        else:
            maxe = node_tot * (node_tot - 1)

        # total number of non-edges (V)
        denom = maxe - num
        if denom == 0:
            return 1
        else:
            completeness = num / denom
            return round(completeness, 5)

    @staticmethod
    @check_graph_consistency
    def completeness(graph) -> float:
        """
        This is a rigorous refinement of the completeness index published in [Ref1]_. It can be applied to matrix
        not necessarily squared and is calculated as:
        *rho = (SQRT(k) -1) * (k/z -1)*, where *k = m*n*, *m* = number of rows, *n* = number of columns and
        *z* = number of zero elements of a matrix.
        We refer to the paper entitled "Estimating the global density of graphs by a sparseness index" [Ref2]_
        for details
        [Ref1] https://doi.org/10.1093/bib/bbp060
        [Ref2] https://doi.org/10.1016/j.amc.2013.08.040
        :param igraph.Graph graph: an igraph.Graph object.
        :return: The completeness index
        """

        node_tot = graph.vcount()
        k = math.pow(node_tot, 2)
        # (SQRT(k) -1)
        addend_left = node_tot - 1
        # number of zeros in the matrix
        if graph.is_directed():
            z = k - graph.ecount()
        else:
            z = k - (graph.ecount() * 2)

        #  If the graph is complete
        if z == 0:
            return 1
        else:
            addend_right = (k / z) - 1
            completeness = addend_left * addend_right
            return round(completeness, 5)

    @staticmethod
    @check_graph_consistency
    def compactness(graph) -> float:
        """
        It computes the *compactness* index described by Randić and DeAlba [Ref]_ as:
        (Undirected graphs) rho = ((n^2 / 2E) -1) * (1- 1/n)
        (Directed graphs) rho = ((n^2 / E) -1) * (1- 1/n), where n is the number of nodes of the graph and
        E is the total number of edges.
        [Ref]https://pubs.acs.org/doi/abs/10.1021/ci970241z?journalCode=jcics1
        :param igraph.Graph graph: an igraph.Graph object.
        :return: The compactness index
        """

        if graph.is_directed():
            e = graph.ecount()
        else:
            e = graph.ecount() * 2

        node_tot = graph.vcount()
        addend_left = (math.pow(node_tot, 2) / e) - 1
        addend_right = 1 - (1 / node_tot)
        compactness = addend_left * addend_right

        return round(compactness, 5)
