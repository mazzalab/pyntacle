# igraph_bindings.pxd
cdef extern from "igraph/igraph.h" nogil:
    
    ctypedef long igraph_int_t
    ctypedef int  igraph_error_t
    ctypedef double igraph_real_t

    cdef enum igraph_adjacency_t:
        IGRAPH_ADJ_DIRECTED,
        IGRAPH_ADJ_UNDIRECTED,
        IGRAPH_ADJ_MAX,
        IGRAPH_ADJ_MIN,
        IGRAPH_ADJ_PLUS,
        IGRAPH_ADJ_UPPER,
        IGRAPH_ADJ_LOWER

    cdef enum igraph_loops_t:
        IGRAPH_NO_LOOPS,
        IGRAPH_LOOPS_ONCE,
        IGRAPH_LOOPS_TWICE,

    cdef enum igraph_neimode_t:
        IGRAPH_OUT,
        IGRAPH_IN,
        IGRAPH_ALL

    cdef enum igraph_connectedness_t:
        IGRAPH_WEAK,
        IGRAPH_STRONG,

    cdef enum igraph_matrix_storage_t:
        IGRAPH_ROW_MAJOR,
        IGRAPH_COLUMN_MAJOR,

    igraph_error_t igraph_setup();

    # opaque types
    ctypedef struct igraph_t: pass
    ctypedef struct igraph_matrix_t: pass
    ctypedef struct igraph_vs_t: pass
    ctypedef struct igraph_vector_t: pass
    ctypedef struct igraph_vector_int_list_t: pass
    ctypedef struct igraph_vector_int_t: pass
    ctypedef struct igraph_vs_t: pass

    igraph_error_t igraph_matrix_init(
            igraph_matrix_t *m, igraph_int_t nrow, igraph_int_t ncol);

    void igraph_matrix_destroy(igraph_matrix_t *m);

    void igraph_matrix_set(
            igraph_matrix_t* m, igraph_int_t row, igraph_int_t col,
            igraph_real_t value);

    igraph_error_t igraph_weighted_adjacency(
        igraph_t *graph, 
        const igraph_matrix_t *adjmatrix, 
        igraph_adjacency_t mode,
        igraph_vector_t *weights, 
        igraph_loops_t loops
    );

    void igraph_destroy(igraph_t *graph);

    
    igraph_error_t igraph_vector_init(igraph_vector_t *v, igraph_int_t size);
    void igraph_vector_destroy(igraph_vector_t *v);
    igraph_int_t igraph_vector_size(const igraph_vector_t *v);

    igraph_error_t igraph_vector_int_init(igraph_vector_int_t *v, igraph_int_t size);
    void igraph_vector_int_destroy(igraph_vector_int_t *v);
    igraph_int_t igraph_vector_int_get(const igraph_vector_int_t *v, igraph_int_t pos);
    igraph_int_t igraph_vector_int_size(const igraph_vector_int_t *v);
    void igraph_vector_int_copy_to(const igraph_vector_int_t *v, igraph_int_t *to);
    void igraph_vector_int_set(igraph_vector_int_t *v, igraph_int_t pos, igraph_int_t value);

    igraph_error_t igraph_distances_dijkstra(const igraph_t *graph,
                                            igraph_matrix_t *res,
                                            const igraph_vs_t from_vs,
                                            const igraph_vs_t to,
                                            const igraph_vector_t *weights,
                                            igraph_neimode_t mode);

    igraph_vs_t igraph_vss_all();

    igraph_real_t igraph_matrix_get(const igraph_matrix_t *m, igraph_int_t row, igraph_int_t col);
    
    igraph_real_t igraph_vector_get(const igraph_vector_t *v, igraph_int_t pos);

    void igraph_matrix_copy_to(const igraph_matrix_t *m, igraph_real_t *to, igraph_matrix_storage_t storage);


    igraph_error_t igraph_vector_int_list_init(igraph_vector_int_list_t *v, igraph_int_t size);
    void igraph_vector_int_list_destroy(igraph_vector_int_list_t *v);
    igraph_vector_int_t *igraph_vector_int_list_get_ptr(const igraph_vector_int_list_t *v, igraph_int_t pos);

    igraph_error_t igraph_vs_vector(igraph_vs_t *vs, const igraph_vector_int_t *v);
    void igraph_vs_destroy(igraph_vs_t *vs);

    igraph_error_t igraph_get_all_shortest_paths_dijkstra(const igraph_t *graph,
        igraph_vector_int_list_t *vertices,
        igraph_vector_int_list_t *edges,
        igraph_vector_int_t *nrgeo,
        igraph_int_t from_vertex, igraph_vs_t to,
        const igraph_vector_t *weights,
        igraph_neimode_t mode); 

    igraph_error_t igraph_connected_components(
        const igraph_t *graph, igraph_vector_int_t *membership,
        igraph_vector_int_t *csize, igraph_int_t *no, igraph_connectedness_t mode);

    void igraph_vector_int_list_destroy(igraph_vector_int_list_t *v);

