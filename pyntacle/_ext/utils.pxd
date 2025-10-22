cdef void floyd_warshall(double* short_path, int n) noexcept nogil

cdef void dijkstra(double[:, :] adj_matrix, int src, int* pred, int* pred_count, double* dist) noexcept nogil

cdef void count_paths_through_group(int node, int src, int* k_nodes, int k, int n, int* pred, int* pred_count, bint found, int* res) noexcept nogil

cdef void apsp_dijkstra(double[:, :] adj_matrix, double* all_dist, int n) noexcept nogil

cdef void index_to_combination(long long index, int n, int k, int* out_comb, int* out_comp) noexcept nogil
