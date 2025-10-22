# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string import memset
from cython.cimports.libc.string cimport memcpy
from cython.cimports.libc.stdio cimport printf
from libc.stdlib cimport qsort

from . cimport utils
from . cimport cython_igraph

cdef double INF = 1e9 # Use a large number to represent infinity

cdef int cmp_ints(const void *a, const void *b) noexcept nogil:
    return (<int*>a)[0] - (<int*>b)[0]
    
cdef double get_group_degree(double[:, :] adj, int* K_indices, int* notK_indices, int k, int n) noexcept nogil:

    cdef int i, j
    cdef int k_node, notK_node
    cdef double gDegree = 0.

    for i from 0 <= i < (n-k):
        notK_node = notK_indices[i]

        for j from 0 <= j < k: 
            k_node = K_indices[j]

            if adj[ notK_node, k_node] > 0.:
                gDegree += 1.
    
    gDegree = gDegree / (n - k)

    return gDegree 


cdef double get_group_betweenness(double[:, :] adj, int* K_indices, int* notK_indices, int k) noexcept nogil:
    cdef int n = adj.shape[0]
    cdef double betweenness
    cdef int i, j

    qsort(notK_indices, n-k, sizeof(int), cmp_ints)

    # for i from 0 <= i <k:
    #     printf("K node %d: %d\n", i, K_indices[i])
    
    # for i from 0 <= i < (n - k):
    #     printf("notK node %d: %d\n", i, notK_indices[i])

    betweenness = cython_igraph.igraph_betweenness(adj, K_indices, notK_indices, k)

    return betweenness/((n - k)*(n - k - 1))


cdef double get_group_closeness(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int dist_type) noexcept nogil:
    
    cdef int i, j
    cdef double gCloseness = 0.0

    cdef int k_node, notK_node

    cdef double dJk = 0.0

    for i from 0 <= i < (n - k):  # Iterate over non-K nodes
        notK_node = notK_indices[i]

        # mean
        if dist_type == 0:
            dJk = 0.
            for j from 0 <= j < k:
                k_node = K_indices[j]
                if all_dist[notK_node*n + k_node] != INF:
                    dJk += all_dist[notK_node*n + k_node]
            
            dJk = dJk / k

        # max
        elif dist_type == 1:
            dJk = 0.
            for j from 0 <= j < k:
                k_node = K_indices[j]
                if all_dist[notK_node*n + k_node] != INF:
                    if all_dist[notK_node*n + k_node] > dJk:
                        dJk = all_dist[notK_node*n + k_node]

        # min
        elif dist_type == 2:
            dJk = INF
            for j from 0 <= j < k:
                k_node = K_indices[j]

                if all_dist[notK_node*n + k_node] < dJk:
                    dJk = all_dist[notK_node*n + k_node]

        if dJk == INF:
            dJk = 0.

        gCloseness += dJk

    # Compute group closeness centrality
    gCloseness = (n - k) / gCloseness 

    return gCloseness
