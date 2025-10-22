# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy, memset
from cython.cimports.libc.stdio cimport printf

cdef double INF = 1e9  # Use a large number to represent infinity


cdef void floyd_warshall(double* short_path, int n) noexcept nogil:
    cdef int i, j, k
    cdef double direct
    cdef double via_k

    for k from 0 <= k < n:
        for i from 0 <= i < n:
            for j from 0<= j < n:
                direct = short_path[i * n + j]
                via_k = short_path[i * n + k] + short_path[k * n + j]
                if via_k < direct:
                    short_path[i * n + j] = via_k

    return 


############### HEAP STRUCTURE ###############

cimport cython
from libc.stdlib cimport malloc, free

cdef struct MinHeap:
    int size
    int capacity
    int* vert    # vertex at each heap index
    double* dist # distance at each heap index
    int* pos     # position of each vertex in heap

cdef MinHeap* createMinHeap(int capacity) noexcept nogil:
    cdef MinHeap* h = <MinHeap*>malloc(sizeof(MinHeap))
    if not h:
        return NULL
    h.size = 0
    h.capacity = capacity
    h.vert = <int*>malloc(capacity * sizeof(int))
    h.dist = <double*>malloc(capacity * sizeof(double))
    h.pos  = <int*>malloc(capacity * sizeof(int))
    if not h.vert or not h.dist or not h.pos:
        free(h.vert); free(h.dist); free(h.pos); free(h)
        abort()
    return h

@cython.inline
cdef void swap_heap(MinHeap* h, int i, int j) noexcept nogil:
    # swap distances
    cdef double tmpd = h.dist[i]
    h.dist[i] = h.dist[j]
    h.dist[j] = tmpd
    # swap vertices
    cdef int tmpv = h.vert[i]
    h.vert[i] = h.vert[j]
    h.vert[j] = tmpv
    # update positions
    h.pos[h.vert[i]] = i
    h.pos[h.vert[j]] = j

cdef void heapify_down(MinHeap* h, int idx) noexcept nogil:
    cdef int n = h.size
    cdef int left, right, smallest
    while True:
        left = 2*idx + 1
        right = left + 1
        smallest = idx
        if left < n and h.dist[left] < h.dist[smallest]:
            smallest = left
        if right < n and h.dist[right] < h.dist[smallest]:
            smallest = right
        if smallest == idx:
            break
        swap_heap(h, idx, smallest)
        idx = smallest

cdef int extractMin(MinHeap* h) noexcept nogil:
    # returns vertex with min distance
    cdef int root_vert = h.vert[0]
    # move last to root
    h.size -= 1
    h.vert[0] = h.vert[h.size]
    h.dist[0] = h.dist[h.size]
    h.pos[h.vert[0]] = 0
    heapify_down(h, 0)
    return root_vert

cdef void decreaseKey(MinHeap* h, int v, double newdist) noexcept nogil:
    cdef int i = h.pos[v]
    cdef int parent
    h.dist[i] = newdist
    # sift up
    while i > 0:
        parent = (i - 1) // 2
        if h.dist[i] >= h.dist[parent]:
            break
        swap_heap(h, i, parent)
        i = parent

cdef int isInMinHeap(MinHeap* h, int v) noexcept nogil:
    return h.pos[v] < h.size

cdef void insertNode(MinHeap* h, int v, double d) noexcept nogil:
    cdef int i = h.size
    cdef int parent
    h.size += 1
    h.vert[i] = v
    h.dist[i] = d
    h.pos[v] = i
    # sift up
    while i > 0:
        parent = (i - 1) // 2
        if h.dist[i] >= h.dist[parent]:
            break
        swap_heap(h, i, parent)
        i = parent

cdef void freeMinHeap(MinHeap* h) noexcept nogil:
    if not h: return
    free(h.vert)
    free(h.dist)
    free(h.pos)
    free(h)


############### HEAP STRUCTURE ###############

cdef void apsp_dijkstra(double[:, :] adj_matrix, double* all_dist, int n) noexcept nogil:
    """
    Computes all shortest paths for a weighted undirected graph using Dijkstra's algorithm.
    
    Parameters:
    - adj_matrix: 2D array representing the adjacency matrix of the graph.
    - all_dist: 2D array to store the shortest path distances between all pairs of nodes.
    """
    cdef int src, i, u, v

    # initialize
    cdef MinHeap* heap = createMinHeap(n)
    # memset(all_dist, INF, n*n*sizeof(double))
    
    # Iterate over all nodes as source nodes
    for src in range(n):
                
        for i in range(n):
            all_dist[n*src + i] = INF  # infinity
            insertNode(heap, i, all_dist[n*src + i])
        
        # set source
        all_dist[n*src + src] = 0.0
        decreaseKey(heap, src, 0.0)

        while heap.size>0:
            u = extractMin(heap)
            # relax edges u -> v
            for v in range(n):
                if adj_matrix[u][v] != 0. and isInMinHeap(heap, v) and all_dist[n*src + u] + adj_matrix[u][v] < all_dist[n*src + v]:
                    all_dist[n*src + v] = all_dist[n*src + u] + adj_matrix[u][v]
                    decreaseKey(heap, v, all_dist[n*src + v])
        
        # clear heap size for next source
        heap.size = 0
    
    freeMinHeap(heap)



cdef void dijkstra(double[:, :] adj_matrix, int src,  int* pred, int* pred_count, double* dist) noexcept nogil:

    cdef int n = adj_matrix.shape[0]
    cdef MinHeap* heap = createMinHeap(n)

    # initialize
    cdef int i, u
    for i in range(n):
        dist[i] = INF  # infinity
        pred_count[i] = 0
        insertNode(heap, i, dist[i])

    # set source
    dist[src] = 0.0
    pred_count[src] = 1
    decreaseKey(heap, src, dist[src])

    while heap.size>0:
        
        u = extractMin(heap)
        
        for i in range(n):
            if adj_matrix[u][i] != 0. and isInMinHeap(heap, i) and dist[u] + adj_matrix[u][i] < dist[i]:
                
                # dist[i] = dist[u] + adj_matrix[u][i]

                # for j from 0 <= j < pred_count[u]:
                #     pred[i * n + j] = u
                # pred_count[i] = pred_count[u]
                
                # decreaseKey(minHeap, i, dist[i])
                dist[i] = dist[u] + adj_matrix[u, i]
                pred_count[i] = 0
                pred[i * n + pred_count[i]] = u
                pred_count[i] += 1
                decreaseKey(heap, i, dist[i])

            elif adj_matrix[u][i] != 0. and isInMinHeap(heap, i) and dist[u] + adj_matrix[u][i] == dist[i]:
                pred[i * n + pred_count[i]] = u
                pred_count[i] += 1
                # for j from pred_count[i] <= j < pred_count[i] + pred_count[u]:
                #     pred[i * n + j] = u
                # pred_count[i] += pred_count[u]

    freeMinHeap(heap)


cdef void count_paths_through_group(int node, int src, int* k_nodes, int k, int n, int* pred, int* pred_count, bint found, int* res) noexcept nogil:

    cdef int j, i, p
    cdef int total = 0, group_total = 0
    cdef int[2] local

    # If the current node is in the group, mark that we found a group node.
    for j from 0 <= j < k:     
        if node == k_nodes[j]:
            found = True
            break
    
    # Base case: when reaching the source, return 1 if we have seen a group node, else 0.
    if node == src:
        total = 1
        group_total = 1 if found else 0
        res[0] = total
        res[1] = group_total
        
        return 
    
    # Recursively count paths through all predecessors of the current node.
    for i from 0 <= i <pred_count[node]:
        p = pred[node* n + i]

        # printf("will count recursively %d for node%d - current pred is: %d\n", pred_count[node], node, p)

        count_paths_through_group(p, src, k_nodes, k, n, pred, pred_count, found, &local[0])
        total += local[0]
        group_total += local[1]
    
    res[0] = total
    res[1] = group_total
    
    return 



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

# cdef void index_to_combination(long long index, int n, int k, int* out_comb, int* out_comp) noexcept nogil:

#     cdef long long total = binomial(n, k)
#     cdef long long remaining = k
#     cdef long long current_index = index
#     cdef long long start = 0
#     cdef long long lo, hi, mid, count
#     cdef int pos = 0
#     printf("\nStart:")
#     while remaining > 0:
#         printf("Remaining: %lld\n", remaining)
#         lo = start
#         hi = n - remaining
#         # binary search for smallest x
#         while lo < hi:
#             mid = (lo + hi) // 2
#             count = binomial(n - mid - 1, remaining - 1)
#             printf(f"count=%lld\n", count)
#             printf(f"current_index=%lld\n", current_index)
#             if current_index < count:
#                 hi = mid
#             else:
#                 lo = mid + 1
#                 current_index -= count

#         out_comb[pos] = lo
#         pos += 1
#         start = lo + 1
#         remaining -= 1
#     printf("\n\n")
#     # generate_complement_from_combination(out_comb, k, n, out_comp)


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
