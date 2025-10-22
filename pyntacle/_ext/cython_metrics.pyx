# cython: boundscheck=False, wraparound=False, language_level=3, cdivision=True
from cython.parallel import parallel, prange, threadid
from cython.cimports.libc.stdlib cimport abort, malloc, free
from cython.cimports.libc.string cimport memcpy
from cython.cimports.libc.stdio cimport printf

from . cimport kp_metrics
from . cimport group_metrics
from . cimport utils
from . cimport cython_igraph

cdef double INF = 1e9  # Use a large number to represent infinity


# Example: operation_selector defined in Cython and using memoryviews.
cdef double operation_selector(int operation, double[:, :] adj, int* K_indices, int* notK_indices,  int k, int mdist, double* floWar, int dist_type) noexcept nogil:
    
    cdef int k_node    
    cdef double result = 0
    cdef int i
    cdef int n = adj.shape[0]

    # F w/ assp
    if operation == 0:
        result = kp_metrics.get_fragmentation(adj, K_indices, k)

    # dF w/ assp
    elif operation == 1:
        result = kp_metrics.get_distance_fragmentation(adj, K_indices, k)

    # dR
    elif operation == 2:
        result = kp_metrics.get_distance_weighted_reach(floWar, K_indices, notK_indices, k, n)

    # mReach 
    elif operation == 3:
        result = kp_metrics.m_reach(floWar, K_indices, notK_indices, k, n, mdist)

    # gD w/ assp
    elif operation == 4:
        result = group_metrics.get_group_degree(adj, K_indices, notK_indices, k, n)
    
    # gB w/ assp
    elif operation == 5:
        result = group_metrics.get_group_betweenness(adj, K_indices, notK_indices, k)

    # gC 
    elif operation == 6:
        result  = group_metrics.get_group_closeness( floWar, K_indices, notK_indices, k, n, dist_type)

    return result

cpdef cython_greedy(int[:] K_indices, int[:] notK_indices, double[:, :] adj, int operation, int mdist, int dist_type, int num_threads):

    cdef int op = operation
    cdef int n = adj.shape[0]
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
    
    cdef double* all_dist = NULL

    cdef double* candidate_results = <double*> malloc((k * n_k) * sizeof(double))

    cdef int* k_tmp = <int*> malloc((k) * sizeof(int))
    memcpy(k_tmp, &K_indices[0], k * sizeof(int))

    cdef int* notk_tmp = <int*> malloc(n_k * sizeof(int))
    memcpy(notk_tmp, &notK_indices[0], n_k * sizeof(int))

    # printf("\nVediamo se ha copiato k_tmp:")
    # for test_idx in range(k):
    #     printf("%d ", K_indices[test_idx])
    # printf("\n\n")

    # Compute the shortest path matrix, this greatly speeds up the computation
    # not elegant but very efficient
    if op == 2 or op == 3 or op == 6:
        
        all_dist = <double*> malloc((n*n) * sizeof(double))
        
        if cython_igraph.igraph_dijkstra(adj, all_dist, NULL, 0) != 0:
            printf("Failed to compute shortest path matrix!\n")

        # printf("\nMatrice delle distanze:\n")
        # for i from 0 <= i < n:
        #     printf("riga %d: ", i)
        #     for j from 0 <= j < n:
        #         printf("%f ", all_dist[i*n + j])
        #     printf("\n")
        # printf("\n\n")
    
    optimization_score = operation_selector(operation, 
                                            adj, 
                                            k_tmp, 
                                            notk_tmp, 
                                            k, mdist, 
                                            all_dist,
                                            dist_type)

    free(k_tmp)
    free(notk_tmp)

    # printf("\nVediamo optimization_score:")
    # printf("%f\n", optimization_score)

    optimal_set_found = False


    while not optimal_set_found:
        with nogil, parallel(num_threads=num_threads):

            # For each thread copy the K set 
            candidate_set = <int*> malloc(k * sizeof(int))
            not_candidate_set = <int*> malloc(n_k * sizeof(int))

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

                # printf("swapped %d, with %d\n", K_indices[k_idx], notK_indices[i_idx])
                # printf("After swap candidate_set:\n")
                # printf("candidate_set:\n")
                # for j from 0 <= j <k:
                #     printf("%d ", candidate_set[j])
                # printf("\nNoTcandidate_set:\n")
                # for j from 0 <= j < n-k:
                #     printf("%d ", not_candidate_set[j])
                # printf("\n\n")

                candidate_results[idx] = operation_selector(operation, 
                                                            adj, 
                                                            candidate_set, 
                                                            not_candidate_set, 
                                                            k, mdist, 
                                                            all_dist,
                                                            dist_type)

                # printf("\nscore: %f", candidate_results[idx])
                # printf("\nscore: %d", idx)

            free(candidate_set)
            free(not_candidate_set)


        # Find the best candidate so far.
        max_val = candidate_results[0] 
        max_index = 0

        for i in range(1, k * n_k):
            if candidate_results[i] > max_val:
                max_val = candidate_results[i]
                max_index = i
        
        # printf("\nmax_val: %f\n", max_val)
        # printf("optimization_score: %f\n\n", optimization_score )

        if max_val > optimization_score:
            
            k_idx = max_index // n_k  
            i_idx = max_index % n_k 
            
            # swap elements
            max_index = K_indices[k_idx] # uso come appoggio 
            K_indices[k_idx] = notK_indices[i_idx]
            notK_indices[i_idx] = max_index
        

            # printf("\nUpdated set K:")
            # for j in range(k):
                    
            #     printf("%d ", K_indices[j])

            # printf("\n")

            # printf("New set not K: ")
            # for i in range(n_k):
            #     printf("%d ", notK_indices[i])
            # printf("\n\n")

            optimization_score = max_val

        else:
            
            optimal_set_found = True
    

    free(candidate_results)

    if all_dist != NULL:
        free(all_dist)
  

    # printf("the set of indices that where found is:\n")
    # for i from 0 <= i < k:
    #     printf("%d ", K_indices[i])
    # printf("\n\n")
    # printf("Optimization score found:\n")
    # printf("%f", optimization_score)

    return K_indices, round(optimization_score, 3)


cpdef cython_info(int[:] K_indices, int[:] notK_indices, double[:, :] adj, int operation, int mdist, int dist_type, int num_threads):

    cdef int op = operation
    cdef int n = adj.shape[0]
    cdef int k = K_indices.shape[0]
    cdef int n_k = notK_indices.shape[0]

    cdef double optimization_score

    # define all indices
    cdef int i, j, w

    cdef double* all_dist = NULL

    cdef int* k_tmp = <int*> malloc((k) * sizeof(int))
    memcpy(k_tmp, &K_indices[0], k * sizeof(int))

    cdef int* notk_tmp = <int*> malloc(n_k * sizeof(int))
    memcpy(notk_tmp, &notK_indices[0], n_k * sizeof(int))

 
    if op == 2 or op == 3 or op == 6:
        
        all_dist = <double*> malloc((n*n) * sizeof(double))
        
        if cython_igraph.igraph_dijkstra(adj, all_dist, NULL, 0) != 0:
            printf("Failed to compute shortest path matrix!\n")

        # printf("\nMatrice delle distanze:\n")
        # for i from 0 <= i < n:
        #     printf("riga %d: ", i)
        #     for j from 0 <= j < n:
        #         printf("%f ", all_dist[i*n + j])
        #     printf("\n")
        # printf("\n\n")
    
    optimization_score = operation_selector(operation, 
                                            adj, 
                                            k_tmp, 
                                            notk_tmp, 
                                            k, mdist, 
                                            all_dist,
                                            dist_type)

    free(k_tmp)
    free(notk_tmp)

    optimal_set_found = False

    if all_dist != NULL:
        free(all_dist)
  
    # printf("the set of indices that where found is:\n")
    # for i from 0 <= i < k:
    #     printf("%d ", K_indices[i])
    # printf("\n\n")
    # printf("Optimization score found:\n")
    # printf("%f", optimization_score)

    return round(optimization_score, 3)



cpdef cython_bruteforce(double[:, :] adj, int[:] K_indices, int operation, int mdist, int dist_type, int comb_num, int num_threads):

    cdef int op = operation
    cdef int n = adj.shape[0]
    cdef int k = K_indices.shape[0]
    # define all indices
    cdef int idx
    cdef int i

    cdef int max_index = 0
    cdef double max_score = 0.
    cdef double score

    cdef int* k_set
    cdef int* not_k_set

    cdef double* all_dist = NULL

    cdef double* candidate_results = <double*> malloc(num_threads * sizeof(double))
    cdef int* candidate_index = <int*> malloc(num_threads * sizeof(int))

    # Compute the shortest path matrix, this greatly speeds up the computation
    # not elegant but very efficient
    if op == 2 or op == 3 or op == 6:
        
        all_dist = <double*> malloc((n*n) * sizeof(double))
        
        if cython_igraph.igraph_dijkstra(adj, all_dist, NULL, 0) != 0:
            printf("Failed to compute shortest path matrix!\n")


    with nogil, parallel(num_threads=num_threads):

        # For each thread copy the K set 
        k_set = <int*> malloc(k * sizeof(int))
        not_k_set = <int*> malloc((n - k) * sizeof(int))

        # Loop over all candidate replacements in parallel.
        for idx in prange(comb_num, schedule="static"):

            utils.index_to_combination(idx, n, k, k_set, not_k_set)

            score =  operation_selector(operation, 
                                        adj, 
                                        k_set, 
                                        not_k_set, 
                                        k, mdist, 
                                        all_dist,
                                        dist_type)

            if score > candidate_results[threadid()]:
                candidate_results[threadid()] = score
                candidate_index[threadid()] = idx

        free(k_set)
        free(not_k_set)


    for idx from 0 <= idx < num_threads:
        if idx == 0:
            max_score = candidate_results[idx]
            max_index = candidate_index[idx]
        elif candidate_results[idx] > max_score:
            max_score = candidate_results[idx]
            max_index = candidate_index[idx]

    free(candidate_results)
    free(candidate_index)

    if all_dist != NULL:
        free(all_dist)

    k_set = NULL
    k_set = <int*> malloc(k * sizeof(int))

    utils.index_to_combination(max_index, n, k, k_set, NULL)
    for idx from 0 <= idx < k:
        K_indices[idx] = k_set[idx]

    free(k_set)

    return K_indices, round(max_score, 3)
