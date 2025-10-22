# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy, memset
from cython.cimports.libc.stdio cimport printf

from . cimport utils
from . cimport cython_igraph

cdef double INF = 1e9  # Use a large number to represent infinity

cdef double m_reach(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int mdist) noexcept nogil:

    cdef int i, j
    cdef int k_node, notK_node
    cdef double mReach = 0.
    cdef bint* visited = <bint*> malloc(n * sizeof(bint))
    memset(visited, 0, n * sizeof(bint))

    for j from 0 <= j < k: 
        k_node = K_indices[j]

        for i from 0 <= i < (n-k):
            notK_node = notK_indices[i]


            if all_dist[notK_node * n + k_node] <= mdist and not visited[i]:
                visited[i] = 1
                mReach += 1

    free(visited)

    return mReach 

cdef double get_distance_weighted_reach(double* all_dist, int* K_indices, int* notK_indices, int k, int n) noexcept nogil:

    cdef int i, j
    cdef int k_node, notK_node
    cdef double dR = 0
    cdef double min_sp 

    for i from 0 <= i < (n-k):
        
        notK_node = notK_indices[i]

        # find the vertex key player that we are testing
        min_sp = INF

        for j from 0 <= j < k: 
            
            # need to find the min between all sp between a notK and K 
            k_node = K_indices[j]

            if min_sp > all_dist[notK_node * n + k_node]:
                min_sp = all_dist[notK_node * n + k_node]

        dR += 1./min_sp
    
    # add the shortest distances from the set itself
    # for i from 0 <= i < k:
    #     dR += 1.

    dR = dR / (n - k)

    return dR

cdef double get_fragmentation(double[:, :] adj_matrix, int* K_indices, int k) noexcept nogil:
    
    cdef int n = adj_matrix.shape[0]
    cdef int i, j, cur_node, comp_num
    cdef int comp_size
    cdef double component_f = 0.
    cdef int component_num = 0
    cdef double f

    cdef long* size_comp = <long*> malloc((n) * sizeof(long))
    
    comp_num = cython_igraph.igraph_components(adj_matrix, size_comp, K_indices, k)

    for i from 0 <= i < comp_num:
        component_f += (size_comp[i] * (size_comp[i] - 1))

    # Free the allocated stack memory.
    free(size_comp)
    if component_num == 1:
        f = 0.
    else:
        f = 1. - (component_f / ((n-k) * ((n-k) - 1)))
    return f

cdef double get_distance_fragmentation(double[:, :] adj, int* K_indices, int k) noexcept nogil:
    
    cdef int n = adj.shape[0]
    cdef int i, j
    cdef double dF
    cdef double df_denum
    cdef double df_num
    cdef double sum_sp

    cdef double* shortest_path_lengths = <double*> malloc((n*n) * sizeof(double))

    if cython_igraph.igraph_dijkstra(adj, shortest_path_lengths, K_indices, k) != 0:
        printf("Failed to compute shortest path matrix!\n")

    df_num = 0
    for i from 0 <= i <n:
        sum_sp = 0
        for j from i+1 <= j < n:
            # if shortest_path_lengths[i*n + j] == 0.:
            #     sum_sp += (1. / INF)
            #     printf("Shortest path between %d and %d is 0, setting to INF\n", i, j)
            # else:
            sum_sp += (1. / shortest_path_lengths[i*n + j])
        
        df_num += sum_sp

    free(shortest_path_lengths)

    df_num *= 2 

    df_denum = (n - k) * ((n-k) - 1)

    dF = 1 - (df_num / df_denum)

    return dF
