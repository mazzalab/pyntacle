from .cython_metrics import cython_greedy, cython_bruteforce, SetScorer, OPENMP

import numpy as np
from time import time

import math
import warnings
import igraph as ig
import pandas as pd

# How many equally-scoring node sets a brute-force run reports. Symmetric networks
# routinely have thousands of them, so the list is capped while the count that comes
# back with it stays exact.
DEFAULT_MAX_TIES = 100

CYTHON_UNSUPPORTED_DIRECTED = (
    "The compiled metric kernels only support undirected networks. Re-run without "
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

    The kernels build their CSR view from this O(E) edge list.
    Zero-weight edges are dropped (a zero weight is not an edge). The unweighted
    flag lets the kernels use a BFS instead of Dijkstra.
    """
    n = graph.vcount()
    edges = np.asarray(graph.get_edgelist(), dtype=np.int32).reshape(-1, 2)

    if "weight" in graph.es.attributes():
        w = np.asarray(graph.es["weight"], dtype=float)
    else:
        w = np.ones(edges.shape[0], dtype=float)

    if w.size and np.any(w < 0.):
        # Dijkstra is silently wrong on negative lengths, and on an undirected
        # graph no shortest path exists at all; load signed weights with
        # --weight-type signed, which turns them into positive lengths
        raise ValueError("ERROR: negative edge length reached the shortest-path kernels; "
                         "load signed weights with --weight-type signed.")

    if w.size and not np.all(w != 0.):
        keep = w != 0.
        edges = edges[keep]
        w = w[keep]

    edges = np.ascontiguousarray(edges, dtype=np.int32)
    w = np.ascontiguousarray(w, dtype=float)
    unweighted = bool(w.size == 0 or np.all(w == 1.0))
    return edges, w, n, unweighted


def _finalize(score, oper, nodes=None):
    """Turn the group-closeness kernel's -1 failure signal into a warning plus 0.

    Group closeness is the only kernel with a failure signal. Every other score
    is returned as computed: dF, in particular, is negative when the distances
    in the network are below 1.
    """
    if oper == "closeness" and score is not None and score < 0:
        warnings.warn(
            f"Node set {nodes if nodes is not None else ''} cannot reach the rest "
            "of the network with the requested distance type. Returning 0.",
            RuntimeWarning, stacklevel=3)
        return 0.0
    return score


def cython_wrapper_greedy(graph, k_size, oper, distance_type='min', mdist=1, n_threads=1, seed=None):

    _check_undirected(graph)

    node_names = graph.vs()["name"]
    node_indices =  graph.iNodes
    df_tmp = pd.DataFrame({"name":node_names, "indices":node_indices})

    # shuffle keeping names aligned with indices; the seed makes the starting
    # set, and so the local optimum reached, reproducible
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

    # indices back to names
    found_k = np.asarray(found_k)
    found_k = [node_names[i] for i in found_k]

    return found_k, _finalize(found_score, oper, found_k)

class KernelScorer:
    """Scores node sets of one network with one metric.

    The compiled view of the network and its all-pairs distances are built once,
    with n_threads threads, and reused by every call, so a search that scores
    many sets (the gradient descent) pays for them once. Names not in the
    network are ignored.
    """

    def __init__(self, graph, oper, distance_type, mdist, n_threads):
        _check_undirected(graph)
        self.oper = oper
        self._index = dict(zip(graph.vs()["name"], graph.iNodes))
        edges, w, self._n, unweighted = _edges(graph)
        self._kernel = SetScorer(edges, w, self._n, select_operation(oper), mdist,
                                 select_distance_type(distance_type), n_threads, unweighted)

    def __call__(self, nodes):
        in_set = np.zeros(self._n, dtype=bool)
        in_set[[self._index[x] for x in nodes if x in self._index]] = True
        K_indices = np.flatnonzero(in_set).astype(np.int32)
        notK_indices = np.flatnonzero(~in_set).astype(np.int32)
        return _finalize(self._kernel.score(K_indices, notK_indices), self.oper, nodes)


def cython_wrapper_info(graph, nodes, oper, distance_type, mdist, n_threads):
    return KernelScorer(graph, oper, distance_type, mdist, n_threads)(nodes)

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

    K_indices = np.arange(k_size).astype(np.int32)  # placeholder, filled by the kernel

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

    # indices back to names
    found_k = np.asarray(found_k)
    found_k = [node_names[i] for i in found_k]
    tied_sets = [[node_names[i] for i in indices] for indices in tied_indices]

    return found_k, _finalize(found_score, oper, found_k), tied_sets, int(n_optimal)
