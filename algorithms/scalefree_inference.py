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

""" This module uses igraph' s builtin function to determine wether the power law fit for an `igraph.Graph` object"""

from config import *
from tools.misc.graph_routines import *
from igraph import statistics as st


class FitPowerLaw:

    @staticmethod
    @check_graph_consistency
    def alpha(graph, xmin=None) -> float:
        """
        Find the alpha of the power law of a Graph Object (the coefficient used to assume a graph
        follows a Scale.Free Topology)
        :param float xmin: at what "x" on the degree distribution the power law will be fitted
        :return: a float representing the fitted power low distribution of the graph
        """

        if xmin is not None and xmin is not isinstance(xmin,(int,float)) and xmin < 0:
            raise ValueError("\"xmin\" must be a float greater than 0")

        degree = graph.degree()

        alpha = st.power_law_fit(degree, xmin=xmin).alpha

        return alpha
