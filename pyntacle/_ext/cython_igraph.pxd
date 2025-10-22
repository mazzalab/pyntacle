cdef int igraph_dijkstra(double[:,:] adj_matrix, double* distances, int* k_set, int k ) noexcept nogil;

cdef int igraph_components(double[:,:] adj_matrix, long* comp_size, int* k_set, int k) noexcept nogil;

cdef double igraph_betweenness(double[:,:] adj_matrix, int* k_set, int* notk_set, int k) noexcept nogil;

