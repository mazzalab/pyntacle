cimport cython
from cython.parallel cimport prange


cdef extern from "cuda/fw-kernel.h":
	void cudaBlockedFW(float* graphHost, const int nvertex)


def cuda_floyd(float [:] w_adj_matrix, int vertex_num):
		
	cudaBlockedFW(&w_adj_matrix[0], vertex_num)

	return list(w_adj_matrix)

