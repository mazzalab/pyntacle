import numpy as np
import igraph as ig
import random

from utility import plain_copy

# from Algorithm.multicore.cudaext import cuda_floyd

def prune_graph(grafo, node_names):
    """Return a plain igraph copy of ``grafo`` with ``node_names`` removed.

    Edge weights are carried over: dF is a weighted metric, and building the copy
    without them made ``grafo.es["weight"]`` raise KeyError further down.
    ``plain_copy`` also keeps trailing isolated vertices, which the hand-rolled
    ``ig.Graph(edges=...)`` this used to be dropped -- that made F and dF come
    back lower than the Cython engine's on any network ending in an isolate.
    """
    temp_grafo = plain_copy(grafo, directed=False)
    temp_grafo.delete_vertices(node_names)
    return temp_grafo


def edge_weights_or_none(grafo):
    """Weight list of ``grafo``, or None when the graph carries no weights.

    igraph reads None as "unweighted", which is the right fallback: raising
    KeyError instead just moved the failure to the caller.
    """
    if "weight" not in grafo.es.attributes():
        return None
    return grafo.es["weight"]


# negative
def fragmentation(grafo):
    """Compute KPP-Neg fragmentation (F) of a graph.

    F measures how fragmented a graph is: it equals 1 minus the probability
    that two randomly chosen nodes belong to the same connected component.

    Args:
        grafo: An igraph Graph object (typically the residual graph after
            removing the key-player set).

    Returns:
        float: F score in [0, 1]. 0 = fully connected; 1 = maximally fragmented.
    """
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

    shortest_path_lengths = grafo.distances(weights=edge_weights_or_none(grafo), mode=ig.ALL)


    # n = adj.shape[0]  # Number of vertices
    # shortest_path_lengths = adj.copy()  # Initialize distance matrix with adjacency matrix

    df_num = 0
    for i in range(number_nodes):
        df_num += sum([float(1 / shortest_path_lengths[i][j]) for j in range(i + 1, number_nodes)])

    df_num *= 2 
    df = 1 - (df_num / df_denum)

    return df

#negative
def distance_fragmentation(grafo):
    """Compute KPP-Neg distance-fragmentation (dF) of a graph.

    dF is the complement of the harmonic sum of pairwise inverse distances.
    It equals 0 for a complete graph and approaches 1 as the graph fragments.

    Args:
        grafo: An igraph Graph object.

    Returns:
        float: dF score in [0, 1].
    """
                                                               
    num_nodes = grafo.vcount()
    num_edges = grafo.ecount()

    # a complete graph has n(n-1)/2 edges when undirected and n(n-1) when directed
    max_edges = num_nodes * (num_nodes - 1)
    if not grafo.is_directed():
        max_edges /= 2

    if num_edges == max_edges:  # graph is complete, dF is 0
        return 0.0

    return distance_fragmentation_Borgatti(grafo)


# positive
def distance_weighted_reach(grafo, nodes=None):
    """Compute KPP-Pos distance-weighted reach (dR) for a set of nodes.

    dR measures how well a node set can reach the rest of the graph through
    short paths. For each non-group node j, the contribution is 1/d(K, j)
    where d(K, j) is the shortest distance from the group K to j.

    Args:
        grafo: An igraph Graph object.
        nodes: List of node indices forming the key-player set. If None,
            uses all nodes.

    Returns:
        float: dR score in [0, 1]. Higher = better reach.
    """
    if nodes==None: nodes=[v.index for v in grafo.vs]

    # An unreachable node contributes no reach at all. The old code replaced inf
    # with vcount()+1, which credited the group with 1/(n+1) of reach towards
    # nodes it cannot reach -- and that sentinel is not even an upper bound on a
    # weighted graph, where a finite distance can exceed n+1.
    sps = np.array(grafo.distances(nodes, weights=edge_weights_or_none(grafo)),
                   dtype=float)

    dr_num = 0.0
    vminusk = set(grafo.vs.indices) - set(nodes)
    for j in vminusk:
        dKj = sps[:, j].min()
        if np.isfinite(dKj) and dKj > 0:
            dr_num += 1.0 / dKj

    return dr_num / float(grafo.vcount())
    


# positive
def reachability(grafo, mdist, nodes=None):
    """Compute KPP-Pos m-reach for a set of nodes.

    m-reach counts the number of distinct non-group nodes reachable from
    the group K within at most ``mdist`` hops.

    Args:
        grafo: An igraph Graph object.
        mdist (int): Maximum path length m. Must satisfy 1 <= m < vcount.
        nodes: List of node indices forming the key-player set. If None,
            uses all nodes.

    Returns:
        int: Number of non-group nodes reachable within m hops.

    Raises:
        ValueError: If mdist is out of valid range.
    """
        
    if mdist < 1 or mdist >= grafo.vcount() + 1:
        raise ValueError(u"'m' must be greater than zero and less or equal than the total number of vertices")
    
    if nodes==None:nodes=[v.index for v in grafo.vs]

    # m-reach is defined in hops, so the distances are deliberately unweighted
    shortest_path_lengths = grafo.distances(nodes)

    mreach = 0
    vminusk = set(grafo.vs.indices) - set(nodes)
    for j in vminusk:
        for spl in shortest_path_lengths:
            if spl[j] <= mdist:
                mreach += 1
                break

    return mreach




def keyplayer_kpInfo(grafo, node_names, operation, mdist=None): ## kp-finder invece necessità di brute-force quindi è li il codice per kp-finder
    kppset_score_pairs = {}
    temp_grafo = prune_graph(grafo, node_names)

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
