import random
import igraph as ig

## our import
#from brute_force import *

def groupcentrality_gcInfo(grafo, node_names, operation, distance_type="min"):
    
    np_counts = grafo.get_shortestpath_count()
    np_paths = grafo.get_shortestpaths()

    gc_d={} # degree
    gc_b={} # betweenness
    gc_c={} # closeness
    gcset_score_pairs = {}

    temp_grafo = ig.Graph(directed=False,vertex_attrs={"name":grafo.vs["name"],"label": grafo.vs["label"]},edges=grafo.get_edgelist())
    temp_grafo.delete_vertices(node_names)

    if operation == "all":
        gc_d = grafo.group_degree(nodes=node_names)
        if np_counts is None or np_counts.size == 0:
            np_counts = grafo.get_shortestpath_count()
        gc_b = grafo.group_betweenness(np_counts=np_counts,nodes=node_names)
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
        if np_counts is None or np_counts.size == 0:
            np_counts = grafo.get_shortestpath_count()
        score = grafo.group_betweenness(np_counts=np_counts,nodes=node_names)
        gcset_score_pairs = score
    else:
        raise WrongArgumentError("{} function not yet implemented.".format(operation))

    return gcset_score_pairs


        

    












            
