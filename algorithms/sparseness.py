__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """


import math
from internal.graph_routines import check_graph_consistency

class Sparseness:
    r"""
    A set of metrics to measure the global *sparseness* of graphs.
    Read the section *Tools for estimating the divisibility of networks* of the paper entitled  `Estimating the
    divisibility of complex biological networks by sparseness indices <https://doi.org/10.1093/bib/bbp060>`_
    for a quick overview of sparseness, its relevance in network analysis and the different strategies
    that are used to estimate it.
    """

    @staticmethod
    @check_graph_consistency
    def completeness_naive(graph) -> float:
        r"""
        Compute the first, naive version of the *completeness* index as conceived by
        `Mazza et al. <https://doi.org/10.1093/bib/bbp060>`_. In this formulation, completeness is defined as
        the ratio between the number of non-zero (:math:`E`) and zero :math:`V` entries in the
        adjacency matrix of a graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float: The naive computation of the completeness index
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
        r"""
        A rigorous refinement of the *completeness* index published in `Mazza et al. <https://doi.org/10.1093/bib/bbp060>`_.
        It can be applied to matrix not necessarily squared and is calculated as:

        |br| :math:`\rho=\sqrt{k -1}  \cdot \frac{k}{z -1}`
        |br| where :math:`k = m \cdot n` , :math:`m` is the number of rows, :math:`n` is the number of columns and
        :math:`z` is the number of zero elements of the graph adjacency matrix.

        |br| We refer to the paper entitled `Estimating the global density of graphs by a sparseness index <https://doi.org/10.1016/j.amc.2013.08.040>`_
        for more details on the boundaries of this index.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

        :return float : The completeness index
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
    def compactness(graph, correct: bool = False) -> float:
        r"""
        It computes the *compactness* index described by `Randić and DeAlba <https://pubs.acs.org/doi/abs/10.1021/ci970241z?journalCode=jcics1>`_
        as:
        |br| :math:`rho = \frac{N^2}{2E} -1 \cdot 1-\frac{1}{N}` for undirected graphs and
        |br|
        |br| :math:`rho = \frac{N^2}{E} -1 \cdot 1-\frac{1}{N}` for directed networks,
        |br| where :math:`N` is the number of nodes of the graph and :math:`E` is the total number of edges.
        **note** add correct formulation

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page
        :param bool: correct whether to use the original implementation by Randić and deAlba or a *correct* version, in which the the inverse  of the number of nodes over all possible edges is used

        :return float: The compactness index
        """

        if graph.is_directed():
            e = graph.ecount()
        else:
            e = graph.ecount() * 2

        node_tot = graph.vcount()
        addend_left = (math.pow(node_tot, 2) / e) - 1
        addend_right = 1 - (1 / node_tot)
        if correct:
            compactness = math.pow(addend_left, -1) * math.pow(addend_right, -1)
        else:
            compactness = addend_left * addend_right

        return round(compactness, 5)
