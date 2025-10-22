# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True

cdef double get_fragmentation(double[:, :] adj_matrix, int* K_indices, int k) noexcept nogil

cdef double get_distance_fragmentation(double[:, :] adj_matrix, int* K_indices, int k) noexcept nogil

cdef double get_distance_weighted_reach(double* all_dist, int* K_indices, int* notK_indices, int k, int n) noexcept nogil

cdef double m_reach(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int mdist) noexcept nogil

