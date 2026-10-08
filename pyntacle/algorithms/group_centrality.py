import random
import igraph as ig

from pyntacle.utility import plain_copy


def groupcentrality_gcInfo(grafo, node_names, operation, distance_type="min"):
    
    np_paths = grafo.get_shortestpaths()

    gc_d={} # degree
    gc_b={} # betweenness
    gc_c={} # closeness
    gcset_score_pairs = {}

    temp_grafo = plain_copy(grafo, directed=False, with_weights=False)
    temp_grafo.delete_vertices(node_names)

    if operation == "all":
        gc_d = grafo.group_degree(nodes=node_names)
        gc_b = grafo.group_betweenness(node_names)
        if np_paths is None or np_paths.size == 0:
            np_paths = grafo.get_shortestpaths()
        gc_c = grafo.group_closeness(nodes=node_names, np_paths=np_paths, distance_type=distance_type)
        gcset_score_pairs={"Degree":gc_d, "Closeness":gc_c, "Betweenness":gc_b}

    elif operation == "degree":
        score = grafo.group_degree(nodes=node_names)
        gcset_score_pairs = score
    elif operation == "closeness":
        if np_paths is None or np_paths.size == 0:
            np_paths = grafo.get_shortestpaths()
        score = grafo.group_closeness(nodes=node_names, np_paths=np_paths, distance_type=distance_type)
        gcset_score_pairs = score
    elif operation == "betweenness":
        score = grafo.group_betweenness(node_names)
        gcset_score_pairs = score
    else:
        raise WrongArgumentError("{} function not yet implemented.".format(operation))

    return gcset_score_pairs


        

    












            
