"""The compiled kernels must not materialise a dense n x n adjacency.

The wrapper used to hand the kernels ``graph.get_adjacency(...).data`` -- an
n-by-n Python list of lists, then an n-by-n numpy copy. At n=20k that is a
3.2 GB wall (twice that with the igraph copy) for a graph that may have only a
few edges per node. The kernels build their CSR and their igraph view from an
edge list instead, so the footprint has to track E, not n squared.
"""
import gc
import tracemalloc

import igraph as ig
import pytest

from _ext.wrapper import cython_wrapper_info
from GraphTacle import Graphtacle


def _sparse_graphtacle(n, m, name="big"):
    g = ig.Graph.Erdos_Renyi(n=n, m=m)
    names = [str(i) for i in range(n)]
    return Graphtacle(n, g.get_edgelist(), names, list(names),
                      [1.0] * g.ecount(), False, "edgelist", None, True,
                      name, "keyplayer")


def test_wrapper_does_not_call_get_adjacency(zachary):
    """The dense-adjacency constructor must not be on the hot path at all."""
    calls = []
    original = ig.Graph.get_adjacency

    def spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    ig.Graph.get_adjacency = spy
    try:
        cython_wrapper_info(zachary, ["0", "1", "2"], "F",
                            distance_type="min", mdist=1, n_threads=1)
    finally:
        ig.Graph.get_adjacency = original

    assert not calls, "the wrapper still builds a dense adjacency matrix"


@pytest.mark.parametrize("oper", ["F", "dF", "dR", "closeness"])
def test_footprint_stays_below_the_dense_matrix(oper):
    """A sparse 2000-node graph must not allocate anything near the 32 MB matrix."""
    n, m = 2000, 6000
    g = _sparse_graphtacle(n, m)
    nodes = ["0", "1", "2"]

    gc.collect()
    tracemalloc.start()
    cython_wrapper_info(g, nodes, oper, distance_type="min", mdist=1, n_threads=1)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    dense_bytes = n * n * 8  # 32 MB
    assert peak < dense_bytes / 2, (
        f"{oper}: peak python allocation {peak / 1e6:.1f} MB approaches the "
        f"dense {dense_bytes / 1e6:.1f} MB matrix -- it is still being built")
