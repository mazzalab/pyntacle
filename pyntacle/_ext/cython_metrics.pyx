# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.parallel import parallel, prange, threadid
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy, memset
from cython.cimports.libc.stdio cimport printf
from cython.cimports.libc.math cimport fabs, fmax

from . cimport kp_metrics
from . cimport group_metrics
from . cimport utils
from . cimport cython_igraph


# Example: operation_selector defined in Cython and using memoryviews.
cdef double operation_selector(int operation, int[:, :] edges, double[:] wvec, int n, int* K_indices, int* notK_indices,  int k, int mdist, double* floWar, int dist_type, utils.CSR* csr, utils.Scratch* scratch, bint unweighted) noexcept nogil:

    cdef double result = 0

    # F: flood fill on the pre-built CSR, no igraph and no allocation
    if operation == 0:
        result = kp_metrics.get_fragmentation(csr, scratch, K_indices, k)

    # dF: one source at a time into the per-thread scratch row
    elif operation == 1:
        result = kp_metrics.get_distance_fragmentation(csr, scratch, K_indices, k, unweighted)

    # dR
    elif operation == 2:
        result = kp_metrics.get_distance_weighted_reach(floWar, K_indices, notK_indices, k, n)

    # mReach (floWar holds HOP distances for this operation)
    elif operation == 3:
        result = kp_metrics.m_reach(floWar, K_indices, notK_indices, k, n, mdist)

    # gD: adjacency read off the CSR, membership mask refreshed into the scratch
    elif operation == 4:
        utils.mark_group(scratch, K_indices, k)
        result = group_metrics.get_group_degree(csr, scratch.in_K, notK_indices, k, n)

    # gB: rebuilt igraph from the edge list per candidate (as before, no dense matrix)
    elif operation == 5:
        result = group_metrics.get_group_betweenness(edges, wvec, n, K_indices, notK_indices, k)

    # gC
    elif operation == 6:
        result  = group_metrics.get_group_closeness( floWar, K_indices, notK_indices, k, n, dist_type)

    return result


cdef double* build_all_dist(int[:, :] edges, double[:] wvec, int n, utils.CSR* csr, int op) except? NULL:
    """All-pairs distances for the metrics that can hoist them out of the loop.

    m-reach (op 3) is defined in hops, so it gets an unweighted BFS matrix; dR
    and group closeness get the weighted one. Returns NULL when the operation
    needs no matrix.
    """
    cdef double* all_dist
    cdef utils.Scratch* tmp
    cdef int i

    if op != 2 and op != 3 and op != 6:
        return NULL

    all_dist = <double*> malloc((<size_t> n) * n * sizeof(double))
    if all_dist == NULL:
        raise MemoryError(
            f"cannot allocate the {n}x{n} distance matrix "
            f"({(<size_t> n) * n * 8 / 1e9:.1f} GB)")

    if op == 3:
        tmp = utils.scratch_alloc(n)
        if tmp == NULL:
            free(all_dist)
            raise MemoryError("cannot allocate the traversal scratch buffers")
        memset(tmp.in_K, 0, n * sizeof(char))
        with nogil:
            for i in range(n):
                utils.csr_bfs_row(csr, i, tmp.in_K, all_dist + (<size_t> i) * n, tmp.stack)
        utils.scratch_free(tmp)
    else:
        if cython_igraph.igraph_dijkstra(edges, wvec, n, all_dist) != 0:
            free(all_dist)
            raise RuntimeError(
                "igraph refused to compute the shortest-path matrix. The most "
                "common cause is a directed network: the compiled kernels only "
                "support undirected graphs.")

    return all_dist


cpdef cython_greedy(int[:] K_indices, int[:] notK_indices, int[:, :] edges, double[:] wvec, int n, int operation, int mdist, int dist_type, int num_threads, bint unweighted=False):

    cdef int op = operation
    cdef int k = K_indices.shape[0]
    cdef int n_k = notK_indices.shape[0]

    cdef bint optimal_set_found
    cdef double optimization_score

    # define all indices
    cdef int idx
    cdef int k_idx
    cdef int i_idx
    cdef int i, j, w

    cdef double max_val
    cdef int max_index

    cdef int* candidate_set
    cdef int* not_candidate_set
    cdef utils.Scratch* scratch

    cdef double* all_dist = NULL
    cdef double* candidate_results = NULL
    cdef int* k_tmp = NULL
    cdef int* notk_tmp = NULL
    cdef utils.Scratch* main_scratch = NULL
    cdef utils.CSR* csr = NULL
    # Heap cell rather than a plain int: a variable assigned inside a `parallel`
    # block becomes thread-private, so the flag would never reach this scope.
    cdef int* alloc_failed = NULL

    csr = utils.csr_from_edges(edges, wvec, n)
    if csr == NULL:
        raise MemoryError("cannot build the CSR view of the network")

    try:
        alloc_failed = <int*> malloc(sizeof(int))
        if alloc_failed == NULL:
            raise MemoryError("cannot allocate the worker failure flag")
        alloc_failed[0] = 0
        candidate_results = <double*> malloc((<size_t> k * n_k) * sizeof(double))
        k_tmp = <int*> malloc(k * sizeof(int))
        notk_tmp = <int*> malloc(n_k * sizeof(int))
        main_scratch = utils.scratch_alloc(n)
        if candidate_results == NULL or k_tmp == NULL or notk_tmp == NULL or main_scratch == NULL:
            raise MemoryError("cannot allocate the greedy working buffers")

        memcpy(k_tmp, &K_indices[0], k * sizeof(int))
        memcpy(notk_tmp, &notK_indices[0], n_k * sizeof(int))

        # Distances that do not depend on the candidate set are computed once here
        # rather than per candidate.
        all_dist = build_all_dist(edges, wvec, n, csr, op)

        optimization_score = operation_selector(operation,
                                                edges, wvec, n,
                                                k_tmp,
                                                notk_tmp,
                                                k, mdist,
                                                all_dist,
                                                dist_type,
                                                csr, main_scratch, unweighted)

        optimal_set_found = False

        while not optimal_set_found:
            with nogil, parallel(num_threads=num_threads):

                # For each thread copy the K set, plus its own traversal scratch.
                # Allocated once per parallel region, not once per candidate.
                candidate_set = <int*> malloc(k * sizeof(int))
                not_candidate_set = <int*> malloc(n_k * sizeof(int))
                scratch = utils.scratch_alloc(n)

                if candidate_set == NULL or not_candidate_set == NULL or scratch == NULL:
                    alloc_failed[0] = 1
                else:
                    # Loop over all candidate replacements in parallel.
                    for idx in prange(k * n_k, schedule="static"):

                        # Determine which element of K_indices to replace and with which element from notK_indices.
                        k_idx = idx // n_k  # element in K_indices
                        i_idx = idx % n_k     # element in notK_indices

                        # reset the sets to default
                        memcpy(candidate_set, &K_indices[0], k * sizeof(int))
                        memcpy(not_candidate_set, &notK_indices[0], n_k * sizeof(int))

                        # swap element
                        candidate_set[k_idx] = notK_indices[i_idx]
                        not_candidate_set[i_idx] = K_indices[k_idx]

                        candidate_results[idx] = operation_selector(operation,
                                                                    edges, wvec, n,
                                                                    candidate_set,
                                                                    not_candidate_set,
                                                                    k, mdist,
                                                                    all_dist,
                                                                    dist_type,
                                                                    csr, scratch, unweighted)

                free(candidate_set)
                free(not_candidate_set)
                utils.scratch_free(scratch)

            if alloc_failed[0]:
                raise MemoryError("a worker thread could not allocate its scratch buffers")

            # Find the best candidate so far.
            max_val = candidate_results[0]
            max_index = 0

            for i in range(1, k * n_k):
                if candidate_results[i] > max_val:
                    max_val = candidate_results[i]
                    max_index = i

            if max_val > optimization_score:

                k_idx = max_index // n_k
                i_idx = max_index % n_k

                # swap elements
                max_index = K_indices[k_idx] # uso come appoggio
                K_indices[k_idx] = notK_indices[i_idx]
                notK_indices[i_idx] = max_index

                optimization_score = max_val

            else:

                optimal_set_found = True

    finally:
        free(alloc_failed)
        free(candidate_results)
        free(k_tmp)
        free(notk_tmp)
        free(all_dist)
        utils.scratch_free(main_scratch)
        utils.csr_free(csr)

    return K_indices, round(optimization_score, 3)


cpdef cython_info(int[:] K_indices, int[:] notK_indices, int[:, :] edges, double[:] wvec, int n, int operation, int mdist, int dist_type, int num_threads, bint unweighted=False):

    cdef int op = operation
    cdef int k = K_indices.shape[0]
    cdef int n_k = notK_indices.shape[0]

    cdef double optimization_score

    cdef double* all_dist = NULL
    cdef int* k_tmp = NULL
    cdef int* notk_tmp = NULL
    cdef utils.Scratch* scratch = NULL
    cdef utils.CSR* csr = NULL

    csr = utils.csr_from_edges(edges, wvec, n)
    if csr == NULL:
        raise MemoryError("cannot build the CSR view of the network")

    try:
        k_tmp = <int*> malloc(k * sizeof(int))
        notk_tmp = <int*> malloc(n_k * sizeof(int))
        scratch = utils.scratch_alloc(n)
        if k_tmp == NULL or notk_tmp == NULL or scratch == NULL:
            raise MemoryError("cannot allocate the working buffers")

        memcpy(k_tmp, &K_indices[0], k * sizeof(int))
        memcpy(notk_tmp, &notK_indices[0], n_k * sizeof(int))

        all_dist = build_all_dist(edges, wvec, n, csr, op)

        optimization_score = operation_selector(operation,
                                                edges, wvec, n,
                                                k_tmp,
                                                notk_tmp,
                                                k, mdist,
                                                all_dist,
                                                dist_type,
                                                csr, scratch, unweighted)
    finally:
        free(k_tmp)
        free(notk_tmp)
        free(all_dist)
        utils.scratch_free(scratch)
        utils.csr_free(csr)

    return round(optimization_score, 3)


cpdef cython_bruteforce(int[:, :] edges, double[:] wvec, int n, int[:] K_indices, int operation, int mdist, int dist_type, long long comb_num, int num_threads, bint unweighted=False, int max_ties=100):

    cdef int op = operation
    cdef int k = K_indices.shape[0]
    # define all indices
    cdef long long idx
    cdef int i, j

    cdef long long max_index = 0
    cdef double max_score = 0.
    cdef double score
    # Thread-private inside the parallel block: assigned there, never read here.
    cdef double best
    cdef double eps
    cdef int tid

    # Ties: several node sets routinely reach the same optimum, and reporting one
    # of them silently discards the rest of the answer. Each worker keeps the
    # indices of the sets sitting at its own best score, capped at max_ties, plus
    # an uncapped counter so the report can say "showing 100 of 4711".
    cdef long long* tie_buf = NULL
    cdef int* tie_count = NULL
    cdef long long* tie_total = NULL
    cdef long long total_ties = 0
    cdef int n_collected = 0

    cdef int* k_set
    cdef int* not_k_set
    cdef utils.Scratch* scratch

    cdef double* all_dist = NULL
    cdef double* candidate_results = NULL
    cdef long long* candidate_index = NULL
    cdef utils.CSR* csr = NULL
    # Heap cell rather than a plain int: a variable assigned inside a `parallel`
    # block becomes thread-private, so the flag would never reach this scope.
    cdef int* alloc_failed = NULL

    csr = utils.csr_from_edges(edges, wvec, n)
    if csr == NULL:
        raise MemoryError("cannot build the CSR view of the network")

    try:
        alloc_failed = <int*> malloc(sizeof(int))
        if alloc_failed == NULL:
            raise MemoryError("cannot allocate the worker failure flag")
        alloc_failed[0] = 0
        if max_ties < 1:
            max_ties = 1
        candidate_results = <double*> malloc(num_threads * sizeof(double))
        candidate_index = <long long*> malloc(num_threads * sizeof(long long))
        tie_buf = <long long*> malloc(<size_t> num_threads * max_ties * sizeof(long long))
        tie_count = <int*> malloc(num_threads * sizeof(int))
        tie_total = <long long*> malloc(num_threads * sizeof(long long))
        if (candidate_results == NULL or candidate_index == NULL
                or tie_buf == NULL or tie_count == NULL or tie_total == NULL):
            raise MemoryError("cannot allocate the brute-force result buffers")

        # zero-init: a thread that runs no prange iterations (comb_num < num_threads),
        # or whose first candidate is compared before any write, would otherwise read
        # uninitialized memory. All metric scores are >= 0, so 0 is a safe floor.
        # tie_count stays 0 until a candidate actually wins, which is what keeps a
        # network where everything scores 0 behaving as it did before ties existed.
        for i in range(num_threads):
            candidate_results[i] = 0.
            candidate_index[i] = 0
            tie_count[i] = 0
            tie_total[i] = 0

        all_dist = build_all_dist(edges, wvec, n, csr, op)

        with nogil, parallel(num_threads=num_threads):

            # For each thread copy the K set, plus its own traversal scratch
            k_set = <int*> malloc(k * sizeof(int))
            not_k_set = <int*> malloc((n - k) * sizeof(int))
            scratch = utils.scratch_alloc(n)

            if k_set == NULL or not_k_set == NULL or scratch == NULL:
                alloc_failed[0] = 1
            else:
                # Loop over all candidate replacements in parallel.
                for idx in prange(comb_num, schedule="static"):

                    utils.index_to_combination(idx, n, k, k_set, not_k_set)

                    score =  operation_selector(operation,
                                                edges, wvec, n,
                                                k_set,
                                                not_k_set,
                                                k, mdist,
                                                all_dist,
                                                dist_type,
                                                csr, scratch, unweighted)

                    tid = threadid()
                    best = candidate_results[tid]
                    # Candidates reach the same optimum through different traversal
                    # orders, so their scores agree to rounding, not to the bit.
                    eps = 1e-9 * fmax(1., fabs(best))

                    if score > best + eps:
                        candidate_results[tid] = score
                        candidate_index[tid] = idx
                        tie_buf[tid * max_ties] = idx
                        tie_count[tid] = 1
                        tie_total[tid] = 1
                    elif tie_count[tid] > 0 and fabs(score - best) <= eps:
                        tie_total[tid] = tie_total[tid] + 1
                        if tie_count[tid] < max_ties:
                            tie_buf[tid * max_ties + tie_count[tid]] = idx
                            tie_count[tid] = tie_count[tid] + 1

            free(k_set)
            free(not_k_set)
            utils.scratch_free(scratch)

        if alloc_failed[0]:
            raise MemoryError("a worker thread could not allocate its scratch buffers")

        for i from 0 <= i < num_threads:
            if i == 0:
                max_score = candidate_results[i]
                max_index = candidate_index[i]
            elif candidate_results[i] > max_score:
                max_score = candidate_results[i]
                max_index = candidate_index[i]

        # Gather the sets sitting at the global optimum. Threads that never beat
        # the 0 floor (tie_count == 0) are skipped: on a network where nothing
        # scores, the answer stays what it always was -- combination 0, score 0,
        # reported as a single set.
        eps = 1e-9 * fmax(1., fabs(max_score))
        collected = []
        for i from 0 <= i < num_threads:
            if tie_count[i] > 0 and fabs(candidate_results[i] - max_score) <= eps:
                total_ties = total_ties + tie_total[i]
                for j from 0 <= j < tie_count[i]:
                    if n_collected < max_ties:
                        collected.append(tie_buf[<size_t> i * max_ties + j])
                        n_collected = n_collected + 1

        if n_collected == 0:
            collected = [max_index]
            n_collected = 1
            total_ties = 1
        else:
            max_index = <long long> collected[0]

        k_set = <int*> malloc(k * sizeof(int))
        if k_set == NULL:
            raise MemoryError("cannot allocate the winning combination buffer")
        tie_sets = []
        for i from 0 <= i < n_collected:
            utils.index_to_combination(<long long> collected[i], n, k, k_set, NULL)
            tie_sets.append([k_set[j] for j in range(k)])
        utils.index_to_combination(max_index, n, k, k_set, NULL)
        for i from 0 <= i < k:
            K_indices[i] = k_set[i]
        free(k_set)

    finally:
        free(alloc_failed)
        free(candidate_results)
        free(candidate_index)
        free(tie_buf)
        free(tie_count)
        free(tie_total)
        free(all_dist)
        utils.csr_free(csr)

    # No rounding here: the report writer decides how many decimals to show, and
    # rounding at the source cost precision that Pyntacle 1.3.2 reported.
    return K_indices, max_score, tie_sets, total_ties
