import numpy as np
import igraph as ig
import random
from math import isinf

# from Algorithm.multicore.cudaext import cuda_floyd

# negative
def fragmentation(grafo):

    components = grafo.components()
    if len(components) == 1: #graph is complete
            f = 0
    else:
        num_nodes = grafo.vcount()
        f_denum = (num_nodes * (num_nodes - 1))
        f_num = sum(len(sk) * (len(sk) - 1) for sk in components)
        f = 1 - (f_num / f_denum)

    return f



def distance_fragmentation_Borgatti(grafo):   #### per adesso NON utilizzata
        
    number_nodes = grafo.vcount()
    df_denum = number_nodes * (number_nodes - 1)

    # adj = grafo.get_adjacency(attribute=None, default=0)

    # adj = np.array(adj.data, dtype=float)
    # adj[adj == 0.] = np.inf
    # np.fill_diagonal(adj, 0.)

    # it's not weighted?
    shortest_path_lengths = grafo.shortest_paths(weights=grafo.es["weight"],mode=ig.ALL)  


    # n = adj.shape[0]  # Number of vertices
    # shortest_path_lengths = adj.copy()  # Initialize distance matrix with adjacency matrix

    df_num = 0
    for i in range(number_nodes):
        df_num += sum([float(1 / shortest_path_lengths[i][j]) for j in range(i + 1, number_nodes)])

    df_num *= 2 
    df = 1 - (df_num / df_denum)

    return df

#negative 
def distance_fragmentation(grafo, unit_process=True):   #### dF
                                                               
    num_nodes = grafo.vcount()
    num_edges = grafo.ecount()

    if num_edges == (num_nodes * (num_nodes - 1))/2: #graph is complete, dF is 0
        return 0.0

    else:
        if unit_process:
            return distance_fragmentation_Borgatti(grafo)
        elif unit_process == "cpu" or unit_process == "gpu":
            print("Not implemented yet")
            #return distance_fragmentation_multicore(grafo) 
        else: 
            raise TypeError(u"'cpu or gpu' are the available options if the multicore flag is activated") 


# positive
def distance_weighted_reach(grafo, nodes=None, unit_process=True): ####  dR
    if nodes==None: nodes=[v.index for v in grafo.vs]
    if unit_process:
        sps = grafo.shortest_paths(nodes)
        sps = [[grafo.vcount() + 1 if isinf(x) else x for x in y] for y in sps]
        sps = np.array(sps) #convert to a numpy array
        dr_num = 0
        vminusk = set(grafo.vs.indices) - set(nodes)
        for j in vminusk:
            dKj = min(spl[j] for spl in sps)
            dr_num += 1 / dKj
        
        return dr_num / float(grafo.vcount())
    elif unit_process == "cpu" or unit_process == "gpu":
        print("Not implemented yet")
        #return distance_weighted_reach_multicore()
    else: 
        raise TypeError(u"'cpu or gpu' are the available options if the multicore flag is activated") 
    


# positive
# m: for the "m-reach" metrics, a positive integer greater than one representing the maximum distance
def reachability(grafo, mdist, nodes=None, unit_process=True):
        
    if mdist < 1 or mdist >= grafo.vcount() + 1:
        raise ValueError(u"'m' must be greater than zero and less or equal than the total number of vertices")
    
    if unit_process:
        if nodes==None:nodes=[v.index for v in grafo.vs]

        shortest_path_lengths = grafo.shortest_paths(nodes)

        mreach = 0
        vminusk = set(grafo.vs.indices) - set(nodes)
        for j in vminusk:
            for spl in shortest_path_lengths:
                if spl[j] <= mdist:
                    mreach += 1
                    break
    else:
        print("Not implemented yet")

    return mreach




def keyplayer_kpInfo(grafo, node_names, operation, mdist=None): ## kp-finder invece necessità di brute-force quindi è li il codice per kp-finder
    kppset_score_pairs = {}
    temp_grafo = ig.Graph(directed=False,vertex_attrs={"name":grafo.vs["name"],"label": grafo.vs["label"]},edges=grafo.get_edgelist())
    temp_grafo.delete_vertices(node_names)

    if operation=="all":
        ksp_f = fragmentation(temp_grafo)  ## negative
        ksp_df = distance_fragmentation(temp_grafo)  ## negative
        nodes = []
        for i in list(node_names): 
            nodes.append(grafo.vs.find(name=i).index)
        ksp_dr = distance_weighted_reach(grafo,nodes)  ## positive
        ksp_reach = reachability(grafo,mdist,nodes) ##positive
        kppset_score_pairs={"F":ksp_f,"dF":ksp_df,"dR":ksp_dr,"mreach":ksp_reach}
    elif operation=="F":
        kppset_score_pairs = fragmentation(temp_grafo)  ## negative
    elif operation=="dF":
        kppset_score_pairs = distance_fragmentation(temp_grafo)  ## negative
    elif operation=="dR":
        nodes = []
        for i in list(node_names): 
            nodes.append(grafo.vs.find(name=i).index)
        kppset_score_pairs = distance_weighted_reach(grafo,nodes)  ## positive
    elif operation=="mreach":
        nodes = []
        for i in list(node_names): 
            nodes.append(grafo.vs.find(name=i).index)
        kppset_score_pairs = reachability(grafo,mdist,nodes) ##positive
    else:
        raise TypeError(u"'all | F | dF | dR | mreach' are the available options if the multicore flag -oper is activated, default all") 
    return kppset_score_pairs
