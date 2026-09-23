# cython: language_level=3

cdef struct CSR:
    int n
    int* indptr
    int* indices
    double* w

# Per-thread working memory. Allocated once per parallel region, not once per
# candidate: the old dF kernel malloc'd n*n doubles for every combination it
# scored, which dominated the brute-force runtime.
cdef struct Scratch:
    int n
    double* dist
    int* heap
    int* heap_pos
    int* stack
    char* visited
    char* in_K
    long* comp_size

cdef void index_to_combination(long long index, int n, int k, int* out_comb, int* out_comp) noexcept nogil

cdef CSR* csr_alloc(double[:, :] adj) noexcept nogil
cdef CSR* csr_from_edges(int[:, :] edges, double[:] w, int n) noexcept nogil
cdef void csr_free(CSR* g) noexcept nogil

cdef Scratch* scratch_alloc(int n) noexcept nogil
cdef void scratch_free(Scratch* s) noexcept nogil
cdef void mark_group(Scratch* s, int* K_indices, int k) noexcept nogil

cdef int csr_components(CSR* g, char* in_K, long* sizes, int* stack, char* visited) noexcept nogil
cdef void csr_bfs_row(CSR* g, int src, char* in_K, double* dist, int* queue) noexcept nogil
cdef void csr_dijkstra_row(CSR* g, int src, char* in_K, double* dist, int* heap, int* heap_pos) noexcept nogil
