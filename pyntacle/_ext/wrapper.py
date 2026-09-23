from .cython_metrics import cython_greedy, cython_info, cython_bruteforce
from .cython_igraph import init_igraph_error_handler

import numpy as np
from time import time

import math
import warnings
import igraph as ig
import pandas as pd

# libigraph aborts the process by default when a call fails, and the kernels call
# it from inside nogil blocks -- a directed network used to end the run with
# exit 134 and no traceback. Swap in the returning handler at import time so the
# wrappers below can turn a failure into a Python exception.
init_igraph_error_handler()

# How many equally-scoring node sets a brute-force run reports. Symmetric networks
# routinely have thousands of them, so the list is capped while the count that comes
# back with it stays exact.
DEFAULT_MAX_TIES = 100

CYTHON_UNSUPPORTED_DIRECTED = (
    "The compiled metric kernels only support undirected networks: they build the "
    "graph through igraph's undirected weighted-adjacency constructor, which "
    "rejects the asymmetric matrix a directed graph produces. Re-run without "
    "--directed, or use the 'local', 'global' or 'set' commands."
)


def select_operation(oper):
    if oper == "F":
        return 0
    elif oper == "dF":
        return 1
    elif oper == "dR":
        return 2
    elif oper == "mreach":
        return 3
    elif oper == "degree":
        return 4
    elif oper == "betweenness":
        return 5
    elif oper == "closeness":
        return 6
    else:
        raise KeyError(u"Choose the correct operation")

def select_distance_type(distance_type):
    if distance_type == "mean":
        return 0
    elif distance_type == "max":
        return 1
    elif distance_type == "min":
        return 2
    else:
        raise KeyError(u"Choose the correct distance type")


def _check_undirected(graph):
    if graph.is_directed():
        raise ValueError(CYTHON_UNSUPPORTED_DIRECTED)


def _edges(graph):
    """Edge list, weights, vertex count and a flag telling whether every weight is 1.

    The kernels rebuild their CSR and igraph views from this O(E) edge list, so a
    large sparse network is no longer forced through a dense n x n adjacency --
    that matrix was 3.2 GB at n=20k (twice that with igraph's own copy) however
    few edges the graph actually had.

    Zero-weight edges are dropped here, reproducing the old dense convention where
    a 0 cell was indistinguishable from "no edge". The unweighted flag lets the
    kernels pick a BFS over a Dijkstra, which is both faster and the correct
    choice for the hop-based metrics.
    """
    n = graph.vcount()
    edges = np.asarray(graph.get_edgelist(), dtype=np.int32).reshape(-1, 2)

    if "weight" in graph.es.attributes():
        w = np.asarray(graph.es["weight"], dtype=float)
    else:
        w = np.ones(edges.shape[0], dtype=float)

    if w.size and not np.all(w != 0.):
        keep = w != 0.
        edges = edges[keep]
        w = w[keep]

    edges = np.ascontiguousarray(edges, dtype=np.int32)
    w = np.ascontiguousarray(w, dtype=float)
    unweighted = bool(w.size == 0 or np.all(w == 1.0))
    return edges, w, n, unweighted


def _finalize(score, oper, nodes=None):
    """Turn the kernels' -1 failure signal into a warning plus a neutral score."""
    if score is not None and score < 0:
        if oper == "closeness":
            warnings.warn(
                f"Node set {nodes if nodes is not None else ''} cannot reach the rest "
                "of the network with the requested distance type. Returning 0.",
                RuntimeWarning, stacklevel=3)
        else:
            warnings.warn(f"The '{oper}' kernel could not score this network. Returning 0.",
                          RuntimeWarning, stacklevel=3)
        return 0.0
    return score


def cython_wrapper_greedy(graph, k_size, oper, distance_type='min', mdist=1, n_threads=1, seed=None):

    _check_undirected(graph)

    node_names = graph.vs()["name"]
    node_indices =  graph.iNodes
    df_tmp = pd.DataFrame({"name":node_names, "indices":node_indices})

    ### shuffle keeping the name association with indices; random_state makes the
    ### starting set -- and therefore the local optimum reached -- reproducible
    shuffled_df = df_tmp.sample(frac=1.0, random_state=seed)

    selected=shuffled_df.iloc[:k_size]
    sorted_df=selected.sort_values(by="indices")

    K_indices = np.array(sorted_df["indices"]).astype(np.int32)

    notK_indices = set(node_indices).difference(set(sorted_df["indices"]))
    notK_indices = np.array(list(notK_indices)).astype(np.int32)

    edges, w, n, unweighted = _edges(graph)

    oper_idx = select_operation(oper)
    dist_idx = select_distance_type(distance_type)

    found_k, found_score = cython_greedy(K_indices, notK_indices, edges, w, n, operation=oper_idx, mdist=mdist, dist_type=dist_idx, num_threads=n_threads, unweighted=unweighted)

    # convert indices back to names:
    found_k = np.asarray(found_k)
    found_k = [node_names[i] for i in found_k]

    return found_k, _finalize(found_score, oper, found_k)

def cython_wrapper_info(graph, nodes, oper, distance_type, mdist, n_threads):

    _check_undirected(graph)

    node_names = graph.vs()["name"]
    node_indices =  graph.iNodes
    df_tmp = pd.DataFrame({"name":node_names, "indices":node_indices}).sort_values(by="indices")

    K_indices = df_tmp[df_tmp["name"].isin(nodes)]['indices'].to_numpy().astype(np.int32)

    notK_indices = df_tmp[~df_tmp["name"].isin(nodes)]['indices'].to_numpy().astype(np.int32)

    edges, w, n, unweighted = _edges(graph)

    oper_idx = select_operation(oper)
    dist_idx = select_distance_type(distance_type)

    found_score = cython_info(K_indices, notK_indices, edges, w, n, oper_idx, mdist, dist_idx, n_threads, unweighted)

    return _finalize(found_score, oper, nodes)

def cython_wrapper_bruteforce(graph, k_size, oper, distance_type='min', mdist=1, n_threads=1,
                              max_ties=DEFAULT_MAX_TIES):
    """Exhaustive search over every node set of size k_size.

    Returns ``(best_set, score, tied_sets, n_optimal)``. ``tied_sets`` holds every
    set found at ``score``, capped at ``max_ties`` entries and with ``best_set``
    first; ``n_optimal`` counts them all, cap included, so a truncated list can
    still be reported honestly.
    """

    _check_undirected(graph)

    node_names = graph.vs()["name"]

    K_indices = np.arange(k_size).astype(np.int32) # its just a placeholder, we will select the indices later

    edges, w, n, unweighted = _edges(graph)

    oper_idx = select_operation(oper)
    dist_idx = select_distance_type(distance_type)

    comb_num = math.comb(n, k_size)

    # The kernel indexes combinations with a signed 64-bit integer. Well before
    # that ceiling the search is computationally hopeless anyway, so reject it
    # early with a message that points at the alternatives.
    _MAX_BRUTEFORCE = 2_000_000_000
    if comb_num > _MAX_BRUTEFORCE:
        raise ValueError(
            f"Brute-force search space too large: C({n},{k_size}) = "
            f"{comb_num:.3e} combinations exceed the practical limit of "
            f"{_MAX_BRUTEFORCE:.0e}. Use the greedy or gradient_descent algorithm instead."
        )

    found_k, found_score, tied_indices, n_optimal = cython_bruteforce(edges, w, n, K_indices, operation=oper_idx, mdist=mdist, dist_type=dist_idx, comb_num=comb_num, num_threads=n_threads, unweighted=unweighted, max_ties=int(max_ties))

    # convert indices back to names:
    found_k = np.asarray(found_k)
    found_k = [node_names[i] for i in found_k]
    tied_sets = [[node_names[i] for i in indices] for indices in tied_indices]

    return found_k, _finalize(found_score, oper, found_k), tied_sets, int(n_optimal)
