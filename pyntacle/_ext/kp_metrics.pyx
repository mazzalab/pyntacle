# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy, memset
from cython.cimports.libc.stdio cimport printf
from libc.math cimport INFINITY, isinf

from . cimport utils
from . cimport cython_igraph


cdef double m_reach(double* hop_dist, int* K_indices, int* notK_indices, int k, int n, int mdist) noexcept nogil:
    """Number of non-group nodes within `mdist` HOPS of the group.

    `hop_dist` is deliberately an unweighted distance matrix: m-reach is defined
    on the number of steps. Feeding it Dijkstra distances made the score depend
    on the weight scale -- uniformly multiplying every weight by 10 took Zachary
    from 32 down to 0.
    """
    cdef int i, j
    cdef int k_node, notK_node
    cdef double mReach = 0.

    for i from 0 <= i < (n - k):
        notK_node = notK_indices[i]

        for j from 0 <= j < k:
            k_node = K_indices[j]

            if hop_dist[notK_node * n + k_node] <= mdist:
                mReach += 1
                break  # this node is reached; do not count it again

    return mReach


cdef double get_distance_weighted_reach(double* all_dist, int* K_indices, int* notK_indices, int k, int n) noexcept nogil:
    """KPP-Pos dR: mean inverse distance from the group to everything else.

    Normalised by n, matching the reference Python implementation in
    algorithms/key_player.py. Dividing by (n - k) instead used to make the two
    engines disagree (0.952 against 0.868 on Zachary).

    Borgatti additionally credits the k group members themselves with a distance
    of 0; that term is left out here so the score keeps matching the numbers
    Pyntacle has always reported.
    """
    cdef int i, j
    cdef int k_node, notK_node
    cdef double dR = 0
    cdef double min_sp

    for i from 0 <= i < (n - k):

        notK_node = notK_indices[i]

        min_sp = INFINITY

        for j from 0 <= j < k:

            # need to find the min between all sp between a notK and K
            k_node = K_indices[j]

            if min_sp > all_dist[notK_node * n + k_node]:
                min_sp = all_dist[notK_node * n + k_node]

        # an unreachable node contributes no reach at all
        if not isinf(min_sp) and min_sp > 0.:
            dR += 1. / min_sp

    return dR / n


cdef double get_fragmentation(utils.CSR* g, utils.Scratch* s, int* K_indices, int k) noexcept nogil:
    """KPP-Neg F: 1 - P(two random nodes of V \\ K are in the same component).

    Flood fill over the CSR built once by the caller. This used to construct a
    whole igraph graph from a dense n x n matrix for every candidate.
    """
    cdef int n = g.n
    cdef int i, comp_num
    cdef double component_f = 0.
    cdef double denom = (<double> (n - k)) * ((n - k) - 1)

    utils.mark_group(s, K_indices, k)
    comp_num = utils.csr_components(g, s.in_K, s.comp_size, s.stack, s.visited)

    if comp_num <= 1 or denom <= 0.:
        return 0.

    for i from 0 <= i < comp_num:
        component_f += (<double> s.comp_size[i]) * (s.comp_size[i] - 1)

    return 1. - (component_f / denom)


cdef double get_distance_fragmentation(utils.CSR* g, utils.Scratch* s, int* K_indices, int k, bint unweighted) noexcept nogil:
    """KPP-Neg dF: 1 - the harmonic sum of pairwise distances over V \\ K.

    One source at a time, accumulating into a single row of length n. The old
    kernel malloc'd an n x n matrix per candidate and ran a full igraph Dijkstra
    into it; at n=200 that was 3850 us per combination.
    """
    cdef int n = g.n
    cdef int i, j
    cdef double df_num = 0.
    cdef double sum_sp
    cdef double d
    cdef double df_denum = (<double> (n - k)) * ((n - k) - 1)

    if df_denum <= 0.:
        return 0.

    utils.mark_group(s, K_indices, k)

    for i from 0 <= i < n:
        if s.in_K[i]:
            continue

        if unweighted:
            utils.csr_bfs_row(g, i, s.in_K, s.dist, s.stack)
        else:
            utils.csr_dijkstra_row(g, i, s.in_K, s.dist, s.heap, s.heap_pos)

        sum_sp = 0.
        for j from i + 1 <= j < n:
            if s.in_K[j]:
                continue
            d = s.dist[j]
            if not isinf(d) and d > 0.:
                sum_sp += 1. / d

        df_num += sum_sp

    df_num *= 2

    return 1 - (df_num / df_denum)
