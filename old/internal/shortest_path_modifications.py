""" Utility methods to edit the shortest paths matrix"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t.mazza@css-mendel.it>
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

import numpy as np


class ShortestPathModifier:
    @staticmethod
    def set_max_distances_nparray(shortest_paths: np.ndarray, max_distance: int) -> np.ndarray:
        r"""
        Set all distances greater than 'max_distance' to infinite (number of nodes in the graph plus one).
        The number of nodes is the first size of the numpy array

        :param np.ndarray shortest_paths: the input numpy.ndarray
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :return: a `np.ndarray` with values exceeding 'max_distance' set to infinite (number of nodes in the graph
        plus one).
        """

        sp = np.array(shortest_paths, copy=True)
        sp[sp > max_distance] = np.shape(sp)[0]
        return sp

    @staticmethod
    def set_max_distances_igraph(shortest_paths, max_distance: int) -> list:
        r"""
        Take an input list of distances and set distances greater than max_sp to `inf` (a `math.inf` object)

        :param list shortest_paths: the list of shortest paths outputted by the `shortest_path()` method in igraph
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :return: a list of lists (same as igraph) containing the modified shortest path, with `inf` used if nodes are
        disconnected
        """

        sp = [[float("inf") if x > max_distance else x for x in y] for y in shortest_paths]
        return sp
