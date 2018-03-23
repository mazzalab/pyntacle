__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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

""" This is the shortest path calculation using GPU that should be imported if the GPU is available"""

from config import *
from numba import cuda,jit, uint16
import numpy as np

class SPGpu:
#todo rewrite to work only on upper or lower triangular matrix
    @staticmethod
    @cuda.jit(argtypes='uint16[:, :], uint16[:, :]')
    def shortest_path_GPU(adjmat, result):
        """
        Calculate the shortest paths of a graph for aa single nodes, a set of nodes or all nodes in the graph using
        'Floyd-Warshall Implementation <https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm>'_. The formula
        is implemented using the numba library and allows for parallelization using GPU on CUDA compatible graphics.
        :param np.ndarray adjmat: a numpy.ndarray containing the graph stored in an adjacency. Disconnected nodes in the
        matrix are represented as the total number of nodes in the graph + 1, while the diagonal must contain zeroes
        (no self loops allowed).
        :param nodes: a list containing the indices of the input adjacency matrix corresponding to the query nodes
        :param result: a `np.ndarray` object that will store the result. The maximum size of the array is equal to the
        *shape* of the input adjacency matrix
        :return:
        """
        posx, posy = cuda.grid(2)
        graph_size = result.shape[0]
        if posx < graph_size and posy < graph_size:  # Check array boundaries
            min_path = result[posx, posy]

            posXY = min_path

            if posXY > 2:
                # if posy in nodes:
                for k in range(0, adjmat.shape[0]):
                    posXK = adjmat[posx, k]
                    posKY = adjmat[k, posy]

                    if posXY > posXK + posKY:
                        min_path = posXK + posKY

                    if min_path == 2:
                        break

                result[posx, posy] = min_path