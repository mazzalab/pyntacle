# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string import memset
from cython.cimports.libc.string cimport memcpy
from cython.cimports.libc.stdio cimport printf
from libc.math cimport INFINITY, isinf, fabs, fmax

from . cimport utils

cdef double get_group_degree(utils.CSR* g, char* in_K, int* notK_indices, int k, int n) noexcept nogil:
    """Fraction of non-group nodes adjacent to at least one group member.

    Each non-group node counts once, however many group members it touches.
    `in_K` is the membership mask the caller has refreshed for this candidate
    set; a non-group node counts as soon as one of its CSR neighbours is in it.
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


cdef double get_group_betweenness(utils.CSR* g, utils.Scratch* s, int k, int n, bint unweighted) noexcept nogil:
    """Share of the shortest paths between non-group nodes that pass through the group.

    For every pair (u, v) of non-group nodes joined by a path, the pair adds
    the fraction of its shortest paths with an inner node in the group; the
    sum is divided by the (n - k)(n - k - 1) / 2 pairs, so a group on every
    shortest path scores 1. Shortest paths are counted, never
    listed: from each source one traversal of the whole network settles the
    vertices in distance order, then one pass over that order gives sigma (the
    number of shortest paths) and sigma_avoid (the number that avoid the
    group, zero on group members) as sums over shortest-path predecessors.
    Counts are doubles, exact up to 2**53. `s.in_K` holds the candidate set.
    """
    cdef int src, v, u, e, i, reached
    cdef double total = 0.
    cdef double dv, tol, sig, avoid
    cdef double* dist = s.dist
    cdef double* sigma = s.sigma
    cdef double* sigma_avoid = s.sigma_avoid
    cdef int* order = s.stack

    if n - k < 2:
        return 0.

    for src from 0 <= src < n:
        if s.in_K[src]:
            continue
        reached = utils.csr_sssp_order(g, src, unweighted, dist, order, s.heap, s.heap_pos)
        for i from 0 <= i < reached:
            sigma[order[i]] = 0.
            sigma_avoid[order[i]] = 0.
        sigma[src] = 1.
        sigma_avoid[src] = 1.

        for i from 1 <= i < reached:
            v = order[i]
            dv = dist[v]
            # Dijkstra sums lengths in different orders along different
            # paths: equal lengths agree to rounding, not to the bit
            tol = 1e-10 * fmax(1., dv)
            sig = 0.
            avoid = 0.
            for e from g.indptr[v] <= e < g.indptr[v + 1]:
                u = g.indices[e]
                if unweighted:
                    if dist[u] != dv - 1.:
                        continue
                elif fabs(dist[u] + g.w[e] - dv) > tol:
                    continue
                sig += sigma[u]
                avoid += sigma_avoid[u]
            sigma[v] = sig
            sigma_avoid[v] = 0. if s.in_K[v] else avoid

        # each unordered pair once, from its lower-numbered end
        for i from 1 <= i < reached:
            v = order[i]
            if v > src and not s.in_K[v] and sigma[v] > 0.:
                total += 1. - sigma_avoid[v] / sigma[v]

    return 2. * total / ((<double> (n - k)) * (n - k - 1))


cdef double get_group_closeness(double* all_dist, int* K_indices, int* notK_indices, int k, int n, int dist_type) noexcept nogil:
    """Reached non-group nodes divided by their total distance from the group,
    scaled by the share of non-group nodes reached (Wasserman-Faust); on a
    connected network this is the non-group node count over the total distance.

    Unreachable pairs (infinite distance) are skipped.

    Returns -1 when no non-group node can be reached at all, which the caller
    turns into an explicit warning instead of a division by zero.
    """
    cdef int i, j
    cdef double gCloseness = 0.0

    cdef int k_node, notK_node
    cdef int reachable
    cdef double d
    cdef double dJk = 0.0
    cdef int reached = 0

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
        reached += 1

    if gCloseness <= 0.:
        return -1.

    return (<double> reached / (n - k)) * (reached / gCloseness)
