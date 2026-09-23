cdef int igraph_dijkstra(int[:, :] edges, double[:] w, int n, double* distances) noexcept nogil;

cdef int igraph_components(double[:,:] adj_matrix, long* comp_size, int* k_set, int k) noexcept nogil;

cdef double igraph_betweenness(int[:, :] edges, double[:] w, int n, int* k_set, int* notk_set, int k) noexcept nogil;
