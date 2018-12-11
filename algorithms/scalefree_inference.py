__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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

from igraph import statistics as st
from private.graph_routines import check_graph_consistency

class FitPowerLaw:
    r""" This module uses igraph' s builtin function to determine whether the power law fit for an ``igraph.Graph`` object"""

    @staticmethod
    @check_graph_consistency
    def alpha(graph, xmin=None) -> float:

        r"""
        Find the :math:`\alpha` of the `power law <https://en.wikipedia.org/wiki/Power_law>`_ of an
        :py:class:`~igraph.Graph` (the coefficient used to infer whether the graph topology can be
        approximated to a `scale-free <https://en.wikipedia.org/wiki/Scale-free_network>`_.

        .. note:: this method is recommended for graph of large size (:math:`N \geq 10000`)

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param float xmin: at what :math:`x` on the degree distribution the power law will be fitted. If not specified, will be automatically found.
        :return float: a float representing the fitted power low distribution of the graph
        :raise ValueError: if ``xmin`` is not a positive float
        """
        if xmin is not None and xmin is not isinstance(xmin,(int,float)) and xmin < 0:
            raise ValueError(u"\"xmin\" must be a float greater than 0")

        degree = graph.degree()

        alpha = st.power_law_fit(degree, xmin=xmin).alpha

        return alpha
