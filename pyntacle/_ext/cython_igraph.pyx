# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.parallel import parallel, prange, threadid
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy
from cython.cimports.libc.stdio cimport printf

from igraph_bindings cimport (

    igraph_int_t,

    igraph_matrix_t,
    igraph_vector_t,
    igraph_t,

    igraph_matrix_init,
    igraph_matrix_destroy,

    igraph_vector_init,
    igraph_vector_destroy,
    igraph_matrix_set,

    igraph_destroy,

    igraph_weighted_adjacency,
    igraph_empty,
    igraph_add_edges,

    IGRAPH_ADJ_UNDIRECTED,
    IGRAPH_LOOPS_ONCE,
    IGRAPH_ALL,
    IGRAPH_WEAK,

    igraph_vector_get,
    igraph_vector_set,
    igraph_vector_size,

    igraph_vector_int_init,
    igraph_vector_int_get,
    igraph_vector_int_set,
    igraph_vector_int_destroy,
    igraph_vector_int_size,
    igraph_vector_int_t,
    igraph_vector_int_copy_to,
    
    igraph_connected_components,
    igraph_distances_dijkstra,
    igraph_vss_all,

    igraph_matrix_get,
    igraph_matrix_copy_to,

    igraph_get_all_shortest_paths_dijkstra,

    igraph_vs_t,
    igraph_vs_vector,
    igraph_vs_destroy,

    igraph_vector_int_list_t,
    igraph_vector_int_list_init,
    igraph_vector_int_list_destroy,
    igraph_vector_int_list_get_ptr,

    igraph_error_handler_ignore,
    igraph_set_error_handler
)


cpdef init_igraph_error_handler():
    """Stop libigraph from abort()ing the interpreter on a bad input.

    The kernels call igraph from inside `nogil` blocks, where the default
    handler would abort the process. With the ignore handler a failing call
    returns a non-zero code, which the wrappers turn into a Python error.
    """
    igraph_set_error_handler(igraph_error_handler_ignore)


cdef int build_igraph_from_edges(igraph_t* graph, igraph_vector_t* weights,
                                 int[:, :] edges, double[:] w, int n) noexcept nogil:
    """Build an undirected weighted igraph graph from an edge list, in O(E) memory.

    The weight vector is filled in edge order, so it stays aligned with
    igraph's own edge ids.

    On success `graph` and `weights` are initialised and owned by the caller; on
    failure everything allocated here is torn down and a non-zero code returned.
    """
    cdef int e
    cdef int m = edges.shape[0]
    cdef igraph_vector_int_t edge_vec

    if igraph_vector_int_init(&edge_vec, 2 * m) != 0:
        return 1

    for e from 0 <= e < m:
        igraph_vector_int_set(&edge_vec, 2 * e, edges[e, 0])
        igraph_vector_int_set(&edge_vec, 2 * e + 1, edges[e, 1])

    if igraph_empty(graph, n, False) != 0:
        igraph_vector_int_destroy(&edge_vec)
        return 1

    if igraph_add_edges(graph, &edge_vec, NULL) != 0:
        igraph_vector_int_destroy(&edge_vec)
        igraph_destroy(graph)
        return 1

    igraph_vector_int_destroy(&edge_vec)

    if igraph_vector_init(weights, m) != 0:
        igraph_destroy(graph)
        return 1

    for e from 0 <= e < m:
        igraph_vector_set(weights, e, w[e])

    return 0


cdef int igraph_dijkstra(int[:, :] edges, double[:] w, int n, double* distances) noexcept nogil:

    cdef igraph_t graph
    cdef igraph_vector_t weights
    cdef igraph_matrix_t dist_matrix

    if build_igraph_from_edges(&graph, &weights, edges, w, n) != 0:
        return 1

    if igraph_matrix_init(&dist_matrix, n, n) != 0:
        igraph_vector_destroy(&weights)
        igraph_destroy(&graph)
        return 1

    if igraph_distances_dijkstra(&graph, &dist_matrix, igraph_vss_all(), igraph_vss_all(), &weights, IGRAPH_ALL) != 0:
        printf("Failed to compute distances using Dijkstra's algorithm!")
        igraph_matrix_destroy(&dist_matrix)
        igraph_vector_destroy(&weights)
        igraph_destroy(&graph)
        return 1

    # symmetric matrix: row-major and column-major layouts coincide
    igraph_matrix_copy_to(&dist_matrix, distances)

    igraph_matrix_destroy(&dist_matrix)
    igraph_vector_destroy(&weights)
    igraph_destroy(&graph)

    return 0

cdef int igraph_components(double[:,:] adj_matrix, long* size_comp, int* k_set, int k) noexcept nogil:

    cdef int i, j
    cdef igraph_int_t comp_size
    cdef igraph_t graph
    cdef igraph_vector_t weights
    cdef igraph_matrix_t ig_adj_matrix
    cdef igraph_vector_int_t csize


    cdef igraph_int_t ig_n = adj_matrix.shape[0]

    result = igraph_matrix_init(&ig_adj_matrix, ig_n, ig_n)
    if result != 0: # IGRAPH_SUCCESS is usually 0
        printf("Failed to initialize igraph_matrix_t: %d !", result)
        return -1

    for i from 0 <= i < ig_n:
        for j from 0 <= j < ig_n:
            igraph_matrix_set(&ig_adj_matrix, i, j, adj_matrix[i, j])

    if k_set != NULL:
        for i from 0 <= i < k:
            for j from 0 <= j < ig_n:
                igraph_matrix_set(&ig_adj_matrix,  k_set[i], j, 0.)  # Set the weights to 0 for the k_set vertices
                igraph_matrix_set(&ig_adj_matrix,  j, k_set[i], 0.)  # Set the weights to 0 for the k_set vertices

    # failures return a negative code (1 is a legitimate component count)
    if igraph_vector_init(&weights, 0)  != 0:
        printf("Failed to initialize igraph_vector_t for weights!")
        igraph_matrix_destroy(&ig_adj_matrix)
        return -1

    if igraph_weighted_adjacency(&graph, &ig_adj_matrix, IGRAPH_ADJ_UNDIRECTED, &weights, IGRAPH_LOOPS_ONCE) != 0:
        printf("Failed to create weighted adjacency matrix!")
        igraph_vector_destroy(&weights)
        igraph_matrix_destroy(&ig_adj_matrix)
        return -1

    # initialize csize
    if igraph_vector_int_init(&csize, 0) != 0:
        printf("Failed to initialize csize vector!")
        igraph_vector_destroy(&weights)
        igraph_matrix_destroy(&ig_adj_matrix)
        igraph_destroy(&graph)
        return -1

    if igraph_connected_components(&graph, NULL, &csize, &comp_size, IGRAPH_WEAK) != 0:
        printf("Failed to compute connected components!")
        igraph_vector_destroy(&weights)
        igraph_vector_int_destroy(&csize)
        igraph_matrix_destroy(&ig_adj_matrix)
        igraph_destroy(&graph)
        return -1

    igraph_vector_int_copy_to(&csize, size_comp)
    
    igraph_matrix_destroy(&ig_adj_matrix)
    igraph_vector_destroy(&weights)
    igraph_vector_int_destroy(&csize)
    igraph_destroy(&graph)

    return comp_size
