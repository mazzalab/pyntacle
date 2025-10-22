# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.parallel import parallel, prange, threadid
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy
from cython.cimports.libc.stdio cimport printf

from igraph_bindings cimport (

    igraph_setup,

    IGRAPH_ROW_MAJOR,
    IGRAPH_COLUMN_MAJOR,

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
    
    IGRAPH_ADJ_UNDIRECTED,
    IGRAPH_LOOPS_ONCE,
    IGRAPH_ALL,
    IGRAPH_WEAK,
    
    igraph_vector_get,
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
    igraph_vector_int_list_get_ptr
)


cdef int igraph_dijkstra(double[:,:] adj_matrix, double* distances, int* k_set, int k) noexcept nogil:

    cdef int i, j

    cdef igraph_t graph
    cdef igraph_vector_t weights
    cdef igraph_matrix_t ig_adj_matrix

    cdef igraph_int_t ig_n = adj_matrix.shape[0]

    igraph_setup()

    result = igraph_matrix_init(&ig_adj_matrix, ig_n, ig_n)
    if result != 0: # IGRAPH_SUCCESS is usually 0
        printf("Failed to initialize igraph_matrix_t: %d !", result)
        return 1

    for i from 0 <= i < ig_n:
        for j from 0 <= j < ig_n:
            igraph_matrix_set(&ig_adj_matrix, i, j, adj_matrix[i, j])

    if k_set != NULL:
        # printf("Setting weights for k_set vertices:\n\n\n")
        for i from 0 <= i < k:
            for j from 0 <= j < ig_n:
                igraph_matrix_set(&ig_adj_matrix,  k_set[i], j, 0.)  # Set the weights to 0 for the k_set vertices
                igraph_matrix_set(&ig_adj_matrix,  j, k_set[i], 0.)  # Set the weights to 0 for the k_set vertices

    if igraph_vector_init(&weights, 0)  != 0:
        printf("Failed to initialize igraph_vector_t for weights!")
        igraph_matrix_destroy(&ig_adj_matrix)
        return 1


    if igraph_weighted_adjacency(&graph, &ig_adj_matrix, IGRAPH_ADJ_UNDIRECTED, &weights, IGRAPH_LOOPS_ONCE) != 0:
        printf("Failed to create weighted adjacency matrix!")
        igraph_vector_destroy(&weights)
        igraph_matrix_destroy(&ig_adj_matrix)
        return 1

    # printf("Weight vector:\n")
    # for i from 0 <= i < igraph_vector_size(&weights):
    #     printf("weights[%d] = %f\n", i, igraph_vector_get(&weights, i))
    
    if igraph_distances_dijkstra(&graph, &ig_adj_matrix, igraph_vss_all(), igraph_vss_all(), &weights, IGRAPH_ALL) != 0:
        printf("Failed to compute distances using Dijkstra's algorithm!")
        igraph_vector_destroy(&weights)
        igraph_matrix_destroy(&ig_adj_matrix)
        igraph_destroy(&graph)
        return 1

    # Copy the distances from the igraph matrix to the output array
    igraph_matrix_copy_to(&ig_adj_matrix, distances, IGRAPH_ROW_MAJOR)

    # printf("Distance matrix initialized with size: %ld x %ld\n", ig_n, ig_n)
    # for i from 0 <= i < ig_n:
    #     for j from 0 <= j < ig_n:
    #         printf("dist[%d][%d] = %f\n", i, j, distances[i * ig_n + j])


    igraph_matrix_destroy(&ig_adj_matrix)
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

    igraph_setup()

    result = igraph_matrix_init(&ig_adj_matrix, ig_n, ig_n)
    if result != 0: # IGRAPH_SUCCESS is usually 0
        printf("Failed to initialize igraph_matrix_t: %d !", result)
        return 1

    for i from 0 <= i < ig_n:
        for j from 0 <= j < ig_n:
            igraph_matrix_set(&ig_adj_matrix, i, j, adj_matrix[i, j])

    if k_set != NULL:
        for i from 0 <= i < k:
            for j from 0 <= j < ig_n:
                igraph_matrix_set(&ig_adj_matrix,  k_set[i], j, 0.)  # Set the weights to 0 for the k_set vertices
                igraph_matrix_set(&ig_adj_matrix,  j, k_set[i], 0.)  # Set the weights to 0 for the k_set vertices

    if igraph_vector_init(&weights, 0)  != 0:
        printf("Failed to initialize igraph_vector_t for weights!")
        igraph_matrix_destroy(&ig_adj_matrix)
        return 1

    if igraph_weighted_adjacency(&graph, &ig_adj_matrix, IGRAPH_ADJ_UNDIRECTED, &weights, IGRAPH_LOOPS_ONCE) != 0:
        printf("Failed to create weighted adjacency matrix!")
        igraph_vector_destroy(&weights)
        igraph_matrix_destroy(&ig_adj_matrix)
        return 1

    # initialize csize
    if igraph_vector_int_init(&csize, 0) != 0:
        printf("Failed to initialize csize vector!")
        igraph_vector_destroy(&weights)
        igraph_matrix_destroy(&ig_adj_matrix)
        return 1

    if igraph_connected_components(&graph, NULL, &csize, &comp_size, IGRAPH_WEAK) != 0:
        printf("Failed to compute connected components!")
        igraph_vector_destroy(&weights)
        igraph_vector_int_destroy(&csize)
        igraph_matrix_destroy(&ig_adj_matrix)
        igraph_destroy(&graph)
        return 1

    igraph_vector_int_copy_to(&csize, size_comp)
    
    igraph_matrix_destroy(&ig_adj_matrix)
    igraph_vector_destroy(&weights)
    igraph_vector_int_destroy(&csize)
    igraph_destroy(&graph)

    return comp_size


cdef double igraph_betweenness(double[:,:] adj_matrix, int* k_set, int* notk_set, int k) noexcept nogil:

    cdef int i, j, w, z, y, node
    cdef int tot_geodesics
    cdef double geodesic_group
    cdef double betweenness = 0.
    cdef igraph_t graph
    cdef igraph_vector_t weights
    cdef igraph_matrix_t ig_adj_matrix

    cdef igraph_int_t ig_n = adj_matrix.shape[0]

    cdef igraph_vector_int_list_t vertices
    cdef igraph_vector_int_t nrgeo
    cdef igraph_vector_int_t *geodesic_ptr
    cdef igraph_vs_t to
    cdef igraph_vector_int_t subset

    igraph_setup()

    igraph_matrix_init(&ig_adj_matrix, ig_n, ig_n)

    for i from 0 <= i < ig_n:
        for j from 0 <= j < ig_n:
            igraph_matrix_set(&ig_adj_matrix, i, j, adj_matrix[i, j])

    igraph_vector_init(&weights, 0) 

    igraph_weighted_adjacency(&graph, &ig_adj_matrix, IGRAPH_ADJ_UNDIRECTED, &weights, IGRAPH_LOOPS_ONCE)
 
    igraph_vector_int_list_init(&vertices, 0);
    igraph_vector_int_init(&nrgeo, 0);

    for i from 0 <= i < (ig_n - k - 1):  # -1 because last node has no remaining destinations
        # Create vector selector starting from position i+1
        igraph_vector_int_init(&subset, (ig_n - k - i - 1))
        
        # Copy remaining vertices
        for j from 0 <= j < (ig_n - k - i - 1):
            igraph_vector_int_set(&subset, j, notk_set[i + 1 + j])

        igraph_vs_vector(&to, &subset)
        igraph_get_all_shortest_paths_dijkstra(&graph, &vertices, NULL, &nrgeo, notk_set[i], to, &weights, IGRAPH_ALL)
        igraph_vs_destroy(&to)

        tot_geodesics = 0

        # for each destination node in the subset
        for j from 0 <= j < igraph_vector_int_size(&subset):
            
            geodesic_group = 0.
            node = igraph_vector_int_get(&subset, j)

            # for each geodesic path found
            for w from 0 <= w < igraph_vector_int_get(&nrgeo, node):
                geodesic_ptr = igraph_vector_int_list_get_ptr(&vertices, tot_geodesics)
                tot_geodesics += 1
                
                # for each vertex in the geodesic path
                for z from 0 <= z < igraph_vector_int_size(geodesic_ptr):

                    for y from 0 <= y < k:
                        if igraph_vector_int_get(geodesic_ptr, z) == k_set[y]:
                            geodesic_group += 1.
                            break

            betweenness += geodesic_group / igraph_vector_int_get(&nrgeo, node)

        igraph_vector_int_destroy(&subset)

    igraph_vector_int_list_destroy(&vertices)
    igraph_matrix_destroy(&ig_adj_matrix)
    igraph_vector_destroy(&weights)
    igraph_vector_int_destroy(&nrgeo)
    igraph_destroy(&graph)

    return betweenness