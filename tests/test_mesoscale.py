"""Regression + golden tests for the mesoscale metrics (mesoscale.py).

Covers the bugs found in the sanity check:
  * the self-loop warning fired on every graph (inverted `== 0` guard);
  * the weighted / unweighted warning messages were swapped;
  * gtom() used the non-existent igraph attribute `graph.directed`;
  * ti()/gtom() materialised a dense (k, n, n) cube when a running sum plus
    the last slice is all the algorithm needs.

The golden values were captured from the pre-refactor implementation, so any
change to the numbers the algorithm produces will trip these tests.
"""
import io
import contextlib
import tracemalloc
import warnings

import numpy as np
import igraph as ig
import pytest

from GraphTacle import Graphtacle
from mesoscale import ti, gtom


def _g(edges, n, weights=None, directed=False):
    names = [str(i) for i in range(n)]
    w = weights if weights is not None else [1.0] * len(edges)
    return Graphtacle(n, edges, names, list(names), list(w),
                      directed, "edgelist", None, True, "t", "mesoscale")


def _run(fn, *args, **kwargs):
    """Call a mesoscale function, returning (result, captured_stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = fn(*args, **kwargs)
    return res, buf.getvalue()


# --------------------------------------------------------------------------
# self-loop warning: only when the graph actually has a self-loop
# --------------------------------------------------------------------------

def test_ti_no_selfloop_no_warning():
    g = _g([(0, 1), (1, 2), (2, 3)], 4)
    _, out = _run(ti, g, 2, weighted=False, weight_attr=None, threshold=0.0)
    assert "self-loop" not in out.lower()


def test_gtom_no_selfloop_no_warning():
    g = _g([(0, 1), (1, 2), (2, 3)], 4)
    _, out = _run(gtom, g, 2)
    assert "self-loop" not in out.lower()


def test_ti_selfloop_emits_warning_and_ignores_it():
    # self-loop on node 0; the metric must warn AND drop the loop (diagonal 0)
    g = _g([(0, 0), (0, 1), (1, 2), (2, 3)], 4)
    df, out = _run(ti, g, 2, weighted=False, weight_attr=None, threshold=0.0)
    assert "self-loop" in out.lower()
    assert np.all(np.isfinite(df.iloc[:, :4].values))


# --------------------------------------------------------------------------
# the weighted / unweighted messages must match the mode they are printed in
# --------------------------------------------------------------------------

def test_ti_warning_message_matches_weighted_mode():
    g = _g([(0, 0), (0, 1), (1, 2), (2, 3)], 4)
    _, out = _run(ti, g, 2, weighted=True, weight_attr="weight", threshold=0.0)
    assert "Weighted Topological Importance" in out


def test_ti_warning_message_matches_unweighted_mode():
    g = _g([(0, 0), (0, 1), (1, 2), (2, 3)], 4)
    _, out = _run(ti, g, 2, weighted=False, weight_attr=None, threshold=0.0)
    assert "self-loop" in out.lower()
    assert "Weighted Topological Importance" not in out


# --------------------------------------------------------------------------
# gtom must not depend on the Graphtacle-only `directed` attribute
# --------------------------------------------------------------------------

def test_gtom_accepts_plain_igraph():
    g = ig.Graph([(0, 1), (1, 2), (2, 3)])
    g.vs["label"] = [str(i) for i in range(4)]
    g.iNodes = list(range(4))
    _, out = _run(gtom, g, 2)  # must not raise AttributeError on `.directed`


# --------------------------------------------------------------------------
# directed input must be treated as undirected (documented mesoscale policy):
# both metrics symmetrise the adjacency, so a directed graph gives the SAME
# numbers as the same edges built undirected -- and both announce it.
# --------------------------------------------------------------------------

def _numeric(df):
    return df.select_dtypes("number").values


def test_gtom_directed_equals_undirected():
    edges = [(0, 1), (1, 2), (2, 0)]           # directed cycle == undirected triangle
    d, _ = _run(gtom, _g(edges, 3, directed=True), 2)
    u, _ = _run(gtom, _g(edges, 3, directed=False), 2)
    assert np.allclose(_numeric(d), _numeric(u))


def test_ti_directed_equals_undirected():
    edges = [(0, 1), (1, 2), (2, 0)]
    kw = dict(weighted=False, weight_attr=None, threshold=0.0)
    d, _ = _run(ti, _g(edges, 3, directed=True), 2, **kw)
    u, _ = _run(ti, _g(edges, 3, directed=False), 2, **kw)
    assert np.allclose(_numeric(d), _numeric(u))


def test_ti_weighted_directed_equals_undirected():
    edges = [(0, 1), (1, 2), (2, 0)]
    kw = dict(weighted=True, weight_attr="weight", threshold=0.0)
    d, _ = _run(ti, _g(edges, 3, weights=[2.0, 3.0, 1.0], directed=True), 2, **kw)
    u, _ = _run(ti, _g(edges, 3, weights=[2.0, 3.0, 1.0], directed=False), 2, **kw)
    assert np.allclose(_numeric(d), _numeric(u))


def test_ti_directed_announces_undirected():
    # gtom already prints an undirected note; ti must too, so the directed
    # user is told their graph was symmetrised.
    edges = [(0, 1), (1, 2), (2, 0)]
    _, out = _run(ti, _g(edges, 3, directed=True), 2,
                  weighted=False, weight_attr=None, threshold=0.0)
    assert "undirected" in out.lower()


# --------------------------------------------------------------------------
# golden numbers -- these lock the algorithm output across the refactor
# --------------------------------------------------------------------------

def test_ti_golden_unweighted_path():
    g = _g([(0, 1), (1, 2), (2, 3), (3, 4)], 5)
    df, _ = _run(ti, g, 3, weighted=False, weight_attr=None, threshold=0.5)
    assert np.allclose(df["TI_3"].values,
                       [0.583333, 1.333333, 1.166667, 1.333333, 0.583333], atol=1e-5)
    assert np.allclose(df["TO_3"].values, [0, 0, 0, 0, 0])
    assert np.allclose(df.iloc[0, :5].values,
                       [0.166667, 0.291667, 0.083333, 0.041667, 0.0], atol=1e-5)


def test_ti_golden_threshold_nonzero():
    g = _g([(0, 1), (1, 2), (2, 3), (0, 2), (1, 3)], 4)
    df, _ = _run(ti, g, 2, weighted=False, weight_attr=None, threshold=0.05)
    assert np.allclose(df["TI_2"].values, [0.777778, 1.222222, 1.222222, 0.777778], atol=1e-5)
    assert np.allclose(df["TO_2"].values, [1.0, 1.0, 1.0, 1.0])


def test_ti_golden_weighted():
    g = _g([(0, 1), (1, 2), (2, 3)], 4, weights=[2.0, 1.0, 3.0])
    df, _ = _run(ti, g, 2, weighted=True, weight_attr="weight", threshold=0.0)
    assert np.allclose(df["WI_2"].values, [0.75, 1.125, 1.25, 0.875], atol=1e-6)


def test_gtom_golden_path():
    g = _g([(0, 1), (1, 2), (2, 3), (3, 4)], 5)
    df, _ = _run(gtom, g, 3)
    assert np.allclose(df.iloc[0].values, [1.0, 1.0, 0.5, 0.5, 0.75], atol=1e-6)
    assert np.isclose(np.trace(df.values), 5.0)
    assert np.allclose(df.values, df.values.T)  # symmetric


# --------------------------------------------------------------------------
# memory: no dense (k, n, n) cube -- peak must NOT grow with k
# --------------------------------------------------------------------------

def _peak(fn, g, k, **kwargs):
    tracemalloc.start()
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fn(g, k, **kwargs)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


@pytest.mark.parametrize("fn,kwargs", [
    (ti, dict(weighted=False, weight_attr=None, threshold=0.0)),
    (gtom, {}),
])
def test_mesoscale_memory_independent_of_k(fn, kwargs):
    # The old code stored every step in a (k, n, n) cube, so its peak grew
    # linearly with k. The refactor keeps only a running sum plus the last
    # slice, so a 6x-deeper propagation must not cost meaningfully more memory.
    n = 400
    g0 = ig.Graph.Erdos_Renyi(n=n, m=3 * n)
    g0.simplify()
    names = [str(i) for i in range(n)]
    g = Graphtacle(n, g0.get_edgelist(), names, list(names), [1.0] * g0.ecount(),
                   False, "edgelist", None, True, "t", "mesoscale")
    shallow = _peak(fn, g, 2, **kwargs)
    deep = _peak(fn, g, 12, **kwargs)
    # a k-scaling cube would make deep ~6x shallow; flat memory keeps it ~1x
    assert deep < 1.3 * shallow, (
        f"peak grew with k: k=2 {shallow/1e6:.1f}MB -> k=12 {deep/1e6:.1f}MB")
