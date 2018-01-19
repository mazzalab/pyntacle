# import os
# from pyntacle.io_stream.adjacencymatrix_to_graph import AdjacencyMatrixToGraph
from pyntacle.algorithms.local_topology import LocalTopology
from pyntacle.graph_generator.graph_igraph_generator import ErdosRenyiGenerator
from numba import jit, cuda
import numpy as np
import time
from igraph import Graph


def initialization(graph):
    graph[graph == 0] = graph.shape[0] + 1  # set zero values to the max possible path length + 1
    np.fill_diagonal(graph, 0)  # set diagonal values to 0 (no distance from itself)


@cuda.jit
def floyd_warshall_numba_gpu(graph):
    tx = cuda.threadIdx.x  # Thread id in a 1D block
    ty = cuda.blockIdx.x   # Block id in a 1D grid
    bw = cuda.blockDim.x   # Block width, i.e. number of threads per block

    pos = tx + ty * bw
    if pos < graph.size:  # Check array boundaries
        an_array[pos] += 1

    if graph[i, j] > graph[i, k] + graph[k, j]:
        graph[i, j] = graph[i, k] + graph[k, j]


    v = len(graph)
    for k in range(0, v):
        for i in range(0, v):
            for j in range(0, v):
                if graph[i, j] > graph[i, k] + graph[k, j]:
                    graph[i, j] = graph[i, k] + graph[k, j]


@jit(nopython=True, parallel=True)
def floyd_warshall_numba(graph):
    v = len(graph)
    for k in range(0, v):
        for i in range(0, v):
            for j in range(0, v):
                if graph[i, j] > graph[i, k] + graph[k, j]:
                    graph[i, j] = graph[i, k] + graph[k, j]


def floyd_warshall_plain(graph):
    v = len(graph)
    for k in range(0,v):
        for i in range(0,v):
            for j in range(0,v):
                if graph[i,j] > graph[i,k] + graph[k,j]:
                    graph[i,j] = graph[i,k] + graph[k,j]


if __name__ == "__main__":
    # g = AdjacencyMatrixToGraph().import_graph(
    #     file_name=os.path.join(os.getcwd(), "test_graph.txt"),
    #     header=True,
    #     separator="\t")
    # """:type : igraph.Graph"""

    gen = ErdosRenyiGenerator()
    g = gen.generate([3000, 0.7])
    """:type : Graph"""

    A = g.get_adjacency()
    graph = np.array(A.data)

    # t1 = time.time()
    # initialization(graph)
    # floyd_warshall_plain(graph)
    # print("plain wct: {} sec".format(time.time()-t1))
    # print(graph)

    t1 = time.time()
    initialization(graph)
    floyd_warshall_numba(graph)
    print("numba wct: {} sec".format(time.time() - t1))
    # print(graph)

    t1 = time.time()
    lc = LocalTopology(g)
    matrix_shape = graph.shape
    graph = lc.shortest_path()
    print("igraph wct: {} sec".format(time.time() - t1))
    graph = np.array(graph).reshape(matrix_shape)
    # print(graph)
