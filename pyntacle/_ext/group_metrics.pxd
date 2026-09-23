# group_metrics.pyx functions

from . cimport utils

cdef double get_group_degree(utils.CSR* g, char* in_K, int* notK_indices, int k, int n) noexcept nogil

cdef double get_group_betweenness(int[:, :] edges, double[:] wvec, int n, int* K_indices, int* notK_indices, int k) noexcept nogil

cdef double get_group_closeness(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int dist_type) noexcept nogil
