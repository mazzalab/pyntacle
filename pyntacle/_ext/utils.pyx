# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True

# Combinatorial unranking plus the CSR graph kernels used by the hot path.
#
# F and dF used to go through igraph for every candidate, which meant an
# igraph_matrix_init, an O(n^2) matrix fill and a full graph construction per
# combination -- 89 us and 3850 us per candidate respectively at n=200, against
# 0.4-0.8 us for the metrics that hoist their APSP out of the loop. These kernels
# work straight off a CSR built once, with caller-provided scratch buffers, so
# nothing is allocated inside the loop.

from cython.cimports.libc.stdlib cimport malloc, free
from cython.cimports.libc.string cimport memset
from libc.math cimport INFINITY


cdef inline long long binomial(long long n, long long k) noexcept nogil:
    cdef long long res = 1
    cdef long long i

    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    if k > n - k:
        k = n - k

    for i from 1 <= i < k+1:
        res = res * (n - k + i) // i

    return res


cdef void index_to_combination(long long index, int n, int k, int* out_comb,  int* out_comp) noexcept nogil:

    cdef long long remaining = k
    cdef long long current_index = index
    cdef long long start = 0
    cdef long long count
    cdef int pos = 0
    cdef int x # The candidate element we are checking

    while remaining > 0:
        # Linearly scan for the correct element for the current position
        for x from start <= x < n:
            # How many combinations are there if we pick `x`?
            # We would need to choose `remaining - 1` elements from the set
            # of size `n - x - 1`.
            count = binomial(n - x - 1, remaining - 1)

            if current_index < count:
                # We found it. The index falls within the block of combinations
                # that start with the current prefix followed by `x`.
                out_comb[pos] = x
                pos += 1
                start = x + 1 # The next element must be larger
                remaining -= 1
                break  # Exit the inner for-loop to find the next element
            else:
                # The combination we're looking for comes later.
                # Subtract this block of combinations and check the next element.
                current_index -= count

    if out_comp != NULL:
        generate_complement_from_combination(out_comb, k, n, out_comp)


cdef void generate_complement_from_combination(int* combination, int k, int n, int* complement) noexcept nogil:

    cdef int comp_pos = 0
    cdef int comb_idx = 0
    cdef int i

    for i from 0 <= i < n:
        if comb_idx < k and i == combination[comb_idx]:
            comb_idx += 1
        else:
            complement[comp_pos] = i
            comp_pos += 1


# ---------------------------------------------------------------------------
# CSR construction
# ---------------------------------------------------------------------------

cdef CSR* csr_alloc(double[:, :] adj) noexcept nogil:
    """Build a CSR view of a dense adjacency matrix. NULL on allocation failure.

    A zero cell means "no edge", which is the same convention igraph's weighted
    adjacency constructor uses; zero-weight edges are rejected at load time
    precisely because the two are indistinguishable here.
    """
    cdef int n = adj.shape[0]
    cdef int i, j, nnz = 0

    for i from 0 <= i < n:
        for j from 0 <= j < n:
            if adj[i, j] != 0.:
                nnz += 1

    cdef CSR* g = <CSR*> malloc(sizeof(CSR))
    if g == NULL:
        return NULL

    g.n = n
    g.indptr = <int*> malloc((n + 1) * sizeof(int))
    g.indices = <int*> malloc((nnz if nnz > 0 else 1) * sizeof(int))
    g.w = <double*> malloc((nnz if nnz > 0 else 1) * sizeof(double))
    if g.indptr == NULL or g.indices == NULL or g.w == NULL:
        csr_free(g)
        return NULL

    cdef int pos = 0
    for i from 0 <= i < n:
        g.indptr[i] = pos
        for j from 0 <= j < n:
            if adj[i, j] != 0.:
                g.indices[pos] = j
                g.w[pos] = adj[i, j]
                pos += 1
    g.indptr[n] = pos

    return g


cdef CSR* csr_from_edges(int[:, :] edges, double[:] w, int n) noexcept nogil:
    """Build a CSR straight from an undirected edge list. NULL on alloc failure.

    Reproduces exactly what csr_alloc would produce from the dense weighted
    adjacency, without ever materialising the n x n matrix: an off-diagonal edge
    (i, j) becomes the symmetric pair i->j and j->i, a self-loop (i, i) a single
    i->i entry. Zero-weight edges are skipped, matching the dense convention
    where a 0 cell means "no edge". Parallel edges are kept as separate CSR
    entries; the traversals tolerate them (BFS/flood-fill via the visited guard,
    Dijkstra via the relaxation test).
    """
    cdef int m = edges.shape[0]
    cdef int e, i, j, nnz = 0

    # First pass: count the directed entries each retained edge contributes.
    for e from 0 <= e < m:
        if w[e] == 0.:
            continue
        if edges[e, 0] == edges[e, 1]:
            nnz += 1
        else:
            nnz += 2

    cdef CSR* g = <CSR*> malloc(sizeof(CSR))
    if g == NULL:
        return NULL

    g.n = n
    g.indptr = <int*> malloc((n + 1) * sizeof(int))
    g.indices = <int*> malloc((nnz if nnz > 0 else 1) * sizeof(int))
    g.w = <double*> malloc((nnz if nnz > 0 else 1) * sizeof(double))
    if g.indptr == NULL or g.indices == NULL or g.w == NULL:
        csr_free(g)
        return NULL

    # Second pass: per-vertex out-degree, then prefix-sum into indptr.
    cdef int* deg = <int*> malloc(n * sizeof(int))
    if deg == NULL:
        csr_free(g)
        return NULL
    memset(deg, 0, n * sizeof(int))

    for e from 0 <= e < m:
        if w[e] == 0.:
            continue
        i = edges[e, 0]
        j = edges[e, 1]
        deg[i] += 1
        if i != j:
            deg[j] += 1

    cdef int pos = 0
    for i from 0 <= i < n:
        g.indptr[i] = pos
        pos += deg[i]
    g.indptr[n] = pos

    # Third pass: scatter neighbours using a moving cursor per row.
    cdef int* cursor = <int*> malloc(n * sizeof(int))
    if cursor == NULL:
        free(deg)
        csr_free(g)
        return NULL
    for i from 0 <= i < n:
        cursor[i] = g.indptr[i]

    for e from 0 <= e < m:
        if w[e] == 0.:
            continue
        i = edges[e, 0]
        j = edges[e, 1]
        g.indices[cursor[i]] = j
        g.w[cursor[i]] = w[e]
        cursor[i] += 1
        if i != j:
            g.indices[cursor[j]] = i
            g.w[cursor[j]] = w[e]
            cursor[j] += 1

    free(deg)
    free(cursor)
    return g


cdef void csr_free(CSR* g) noexcept nogil:
    if g == NULL:
        return
    free(g.indptr)
    free(g.indices)
    free(g.w)
    free(g)


# ---------------------------------------------------------------------------
# Per-thread scratch
# ---------------------------------------------------------------------------

cdef Scratch* scratch_alloc(int n) noexcept nogil:
    cdef Scratch* s = <Scratch*> malloc(sizeof(Scratch))
    if s == NULL:
        return NULL

    s.n = n
    s.dist = <double*> malloc(n * sizeof(double))
    s.heap = <int*> malloc(n * sizeof(int))
    s.heap_pos = <int*> malloc(n * sizeof(int))
    s.stack = <int*> malloc(n * sizeof(int))
    s.visited = <char*> malloc(n * sizeof(char))
    s.in_K = <char*> malloc(n * sizeof(char))
    s.comp_size = <long*> malloc(n * sizeof(long))

    if (s.dist == NULL or s.heap == NULL or s.heap_pos == NULL or s.stack == NULL
            or s.visited == NULL or s.in_K == NULL or s.comp_size == NULL):
        scratch_free(s)
        return NULL

    return s


cdef void scratch_free(Scratch* s) noexcept nogil:
    if s == NULL:
        return
    free(s.dist)
    free(s.heap)
    free(s.heap_pos)
    free(s.stack)
    free(s.visited)
    free(s.in_K)
    free(s.comp_size)
    free(s)


cdef void mark_group(Scratch* s, int* K_indices, int k) noexcept nogil:
    """Refresh the membership mask for the candidate set K."""
    cdef int i
    memset(s.in_K, 0, s.n * sizeof(char))
    for i from 0 <= i < k:
        s.in_K[K_indices[i]] = 1


# ---------------------------------------------------------------------------
# Traversals on V \ K
# ---------------------------------------------------------------------------

cdef int csr_components(CSR* g, char* in_K, long* sizes, int* stack, char* visited) noexcept nogil:
    """Sizes of the connected components of V \\ K. Returns how many there are.

    Iterative flood fill, O(V + E). Replaces a full igraph graph construction per
    candidate, which is where the brute-force F cost came from.
    """
    cdef int n = g.n
    cdef int i, v, u, e, top
    cdef int ncomp = 0
    cdef long size

    memset(visited, 0, n * sizeof(char))

    for i from 0 <= i < n:
        if visited[i] or in_K[i]:
            continue

        size = 0
        top = 0
        stack[top] = i
        top += 1
        visited[i] = 1

        while top > 0:
            top -= 1
            v = stack[top]
            size += 1
            for e from g.indptr[v] <= e < g.indptr[v + 1]:
                u = g.indices[e]
                if in_K[u] or visited[u]:
                    continue
                visited[u] = 1
                stack[top] = u
                top += 1

        sizes[ncomp] = size
        ncomp += 1

    return ncomp


cdef void csr_bfs_row(CSR* g, int src, char* in_K, double* dist, int* queue) noexcept nogil:
    """Hop distances from `src` over V \\ K; unreachable stays INFINITY."""
    cdef int n = g.n
    cdef int i, v, u, e
    cdef int head = 0, tail = 0

    for i from 0 <= i < n:
        dist[i] = INFINITY

    if in_K[src]:
        return

    dist[src] = 0.
    queue[tail] = src
    tail += 1

    while head < tail:
        v = queue[head]
        head += 1
        for e from g.indptr[v] <= e < g.indptr[v + 1]:
            u = g.indices[e]
            if in_K[u] or dist[u] != INFINITY:
                continue
            dist[u] = dist[v] + 1.
            queue[tail] = u
            tail += 1


cdef inline void heap_swap(int* heap, int* heap_pos, int a, int b) noexcept nogil:
    cdef int va = heap[a]
    cdef int vb = heap[b]
    heap[a] = vb
    heap[b] = va
    heap_pos[vb] = a
    heap_pos[va] = b


cdef inline void heap_up(int* heap, int* heap_pos, double* dist, int idx) noexcept nogil:
    cdef int parent
    while idx > 0:
        parent = (idx - 1) // 2
        if dist[heap[parent]] <= dist[heap[idx]]:
            break
        heap_swap(heap, heap_pos, parent, idx)
        idx = parent


cdef inline void heap_down(int* heap, int* heap_pos, double* dist, int idx, int size) noexcept nogil:
    cdef int left, right, smallest
    while True:
        left = 2 * idx + 1
        right = left + 1
        smallest = idx
        if left < size and dist[heap[left]] < dist[heap[smallest]]:
            smallest = left
        if right < size and dist[heap[right]] < dist[heap[smallest]]:
            smallest = right
        if smallest == idx:
            break
        heap_swap(heap, heap_pos, smallest, idx)
        idx = smallest


cdef void csr_dijkstra_row(CSR* g, int src, char* in_K, double* dist, int* heap, int* heap_pos) noexcept nogil:
    """Weighted distances from `src` over V \\ K; unreachable stays INFINITY.

    Indexed binary heap. Weights are strictly positive (zero weights are refused
    at load time), so a settled vertex is never relaxed again.
    """
    cdef int n = g.n
    cdef int i, v, u, e
    cdef int size = 0
    cdef double nd

    for i from 0 <= i < n:
        dist[i] = INFINITY
        heap_pos[i] = -1

    if in_K[src]:
        return

    dist[src] = 0.
    heap[0] = src
    heap_pos[src] = 0
    size = 1

    while size > 0:
        v = heap[0]
        heap_pos[v] = -1
        size -= 1
        if size > 0:
            heap[0] = heap[size]
            heap_pos[heap[0]] = 0
            heap_down(heap, heap_pos, dist, 0, size)

        for e from g.indptr[v] <= e < g.indptr[v + 1]:
            u = g.indices[e]
            if in_K[u]:
                continue
            nd = dist[v] + g.w[e]
            if nd < dist[u]:
                dist[u] = nd
                if heap_pos[u] == -1:
                    heap[size] = u
                    heap_pos[u] = size
                    size += 1
                    heap_up(heap, heap_pos, dist, size - 1)
                else:
                    heap_up(heap, heap_pos, dist, heap_pos[u])
