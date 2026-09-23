# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string import memset
from cython.cimports.libc.string cimport memcpy
from cython.cimports.libc.stdio cimport printf
from libc.stdlib cimport qsort
from libc.math cimport INFINITY, isinf

from . cimport utils
from . cimport cython_igraph

cdef int cmp_ints(const void *a, const void *b) noexcept nogil:
    return (<int*>a)[0] - (<int*>b)[0]
    
cdef double get_group_degree(utils.CSR* g, char* in_K, int* notK_indices, int k, int n) noexcept nogil:
    """Fraction of non-group nodes adjacent to at least one group member.

    Each non-group node counts once, however many group members it touches; the
    missing break used to inflate the score past 1 (1.323 on Zachary, against
    0.903 from the reference Python implementation, which de-duplicates via set).

    Reads adjacency straight off the CSR now: `in_K` is the membership mask the
    caller has already refreshed for this candidate set, so a non-group node is
    counted the moment one of its CSR neighbours is a group member -- exactly
    what testing `adj[notK, k] != 0` used to mean, without the dense matrix.
    """
    cdef int i, e, notK_node
    cdef double gDegree = 0.

    for i from 0 <= i < (n - k):
        notK_node = notK_indices[i]

        for e from g.indptr[notK_node] <= e < g.indptr[notK_node + 1]:
            if in_K[g.indices[e]]:
                gDegree += 1.
                break

    gDegree = gDegree / (n - k)

    return gDegree


cdef double get_group_betweenness(int[:, :] edges, double[:] wvec, int n, int* K_indices, int* notK_indices, int k) noexcept nogil:
    cdef double betweenness

    qsort(notK_indices, n - k, sizeof(int), cmp_ints)

    betweenness = cython_igraph.igraph_betweenness(edges, wvec, n, K_indices, notK_indices, k)

    if betweenness < 0.:  # igraph refused the graph; propagate the failure
        return -1.

    return betweenness/((n - k)*(n - k - 1))


cdef double get_group_closeness(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int dist_type) noexcept nogil:
    """Non-group node count divided by the total group-to-node distance.

    Unreachable pairs are skipped rather than compared against a sentinel: the
    guards used to test against a hardcoded 1e9 while igraph hands back a real
    IEEE infinity, so on a disconnected graph the mean and max variants silently
    collapsed to 0.0.

    Returns -1 when no non-group node can be reached at all, which the caller
    turns into an explicit warning instead of a division by zero.
    """
    cdef int i, j
    cdef double gCloseness = 0.0

    cdef int k_node, notK_node
    cdef int reachable
    cdef double d
    cdef double dJk = 0.0

    for i from 0 <= i < (n - k):  # Iterate over non-K nodes
        notK_node = notK_indices[i]
        reachable = 0

        # mean
        if dist_type == 0:
            dJk = 0.
            for j from 0 <= j < k:
                k_node = K_indices[j]
                d = all_dist[notK_node*n + k_node]
                if not isinf(d):
                    dJk += d
                    reachable += 1

            if reachable > 0:
                dJk = dJk / reachable

        # max
        elif dist_type == 1:
            dJk = 0.
            for j from 0 <= j < k:
                k_node = K_indices[j]
                d = all_dist[notK_node*n + k_node]
                if not isinf(d):
                    reachable += 1
                    if d > dJk:
                        dJk = d

        # min
        elif dist_type == 2:
            dJk = INFINITY
            for j from 0 <= j < k:
                k_node = K_indices[j]
                d = all_dist[notK_node*n + k_node]
                if not isinf(d):
                    reachable += 1
                    if d < dJk:
                        dJk = d

        if reachable == 0:
            continue

        gCloseness += dJk

    if gCloseness <= 0.:
        return -1.

    # Compute group closeness centrality
    return (n - k) / gCloseness
