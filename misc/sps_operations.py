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

"""**Methods for shortest path operations**"""

import numpy as np
from config import *

class ShortestPathModifier:

    @staticmethod
    def np_array_to_inf(sp_pyntacle, max_sp) -> np.ndarray:
        """
        Set all distances greater than 'max_sp' to infinite (number of nodes in the graph plus one).
        the number of nodes if the first component of the shape of the numpy array (the rows of the adjacency matrix)
        :param np.ndarray sp_pyntacle: the input numpy.ndarray
        :param int max_sp: the maximum distShoance allowed in the `np.ndarray` of distances
        :return: a `np.ndarray` with each value modified by
        """
        sp_pyntacle[sp_pyntacle > max_sp] = np.shape(sp_pyntacle)[0]
        return sp_pyntacle

    @staticmethod
    def igraph_sp_to_inf(sp_igraph, max_sp) -> list:
        """
        Take an input list of distances and set distances greater than max_sp to `inf` (a `math.inf` object)
        :param list sp_igraph: the list of shortest path outputted by the `shortest_path()` method in igraph
        :param int max_sp: :param int max_sp: the maximum distance allowed in the `np.ndarray` of distances
        :return: a list of lists (same as igraph) containing the modified shortest path, with `inf` used if nodes are
        disconnected
        """
        sp_igraph = [[float("inf") if x > max_sp else x for x in y] for y in sp_igraph]
        return sp_igraph