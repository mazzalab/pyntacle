# group_metrics.pyx functions

cdef double get_group_degree(double[:, :] adj, int* K_indices, int* notK_indices, int k, int n) noexcept nogil

cdef double get_group_betweenness(double[:,:] adj, int* K_indices, int* notK_indices, int k) noexcept nogil

cdef double get_group_closeness(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int dist_type) noexcept nogil
