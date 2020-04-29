__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = "Tommaso Mazza"
__email__ = "t.mazza@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t,mazza@css-mendel.it>
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

from numba import cuda, int32, uint16
import numpy as np
from config import threadsperblock


@cuda.jit(device=True)
def cuda_min(a: int32, b: int32):
    return a if a < b else b

@cuda.jit('void(uint16[:, :], int32, int32)')
def shortest_path_gpu(adjmat: np.ndarray, k:np.int32, N:int32):
    r"""
    Calculate all the shortest paths of a graph, represented as adjacency matrix, using the `Floyd-Warshall <https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm>`_ algorithm.
    The overall calculation is delegated to the GPU, if available, through the NUMBA python package.

    :param np.ndarray adjmat: a numpy.ndarray containing the adjacency matrix of the graph . Infinite distance is represented as the length of the longest possible path within the graph +1. The diagonal of the matrix holds zero values.
    """

    i = cuda.threadIdx.x + cuda.blockIdx.x * cuda.blockDim.x
    j = cuda.threadIdx.y + cuda.blockIdx.y * cuda.blockDim.y
    if i < N and j < N:
        posIK = adjmat[i, k]
        posKJ = adjmat[k, j]
        if posIK != N + 1 and posKJ != N + 1:
            posIJ = adjmat[i, j]
            if posIJ == N + 1:
                adjmat[i, j] = posIK + posKJ
            else:
                adjmat[i, j] = cuda_min(posIK + posKJ, posIJ)


@cuda.jit('void(uint16[:, :], uint16[:, :])')
def shortest_path_count_gpu(adjmat, count):
    r"""
    Calculate the shortest path lengths of a graph using the
    Floyd-Warshall algorithm with path count. The overall calculation is delegated to the GPU, if available, through
    the Numba library.

    :param np.ndarray adjmat: the adjacency matrix of a graph. Absence of links is represented with a number that equals the total number of nodes in the graph + 1. This object will be modified during the computation.
    :param np.ndarray count: the adjacency matrix of a graph. After the overall computation it will contain the path lengths are in the upper triangular part of the array and the geodesics counts in the lower triangular part.
    """

    i = cuda.grid(1)
    graph_size = adjmat.shape[0]

    if i < graph_size:  # Check array boundaries
        for k in range(0, graph_size):
            for j in range(0, graph_size):
                if k != j and k != i and i != j:
                    posIJ = adjmat[i, j]
                    posIK = adjmat[i, k]
                    posKY = adjmat[k, j]

                    if posIJ == posIK + posKY:
                        count[i, j] += count[i, k] * count[k, j]
                    elif posIJ > posIK + posKY:
                        adjmat[i, j] = posIK + posKY
                        count[i, j] = count[i, k] * count[k, j]

    for j in range(i + 1, graph_size):
        count[j, i] = adjmat[i, j]
