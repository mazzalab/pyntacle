"""Per-candidate cost regression for the brute-force kernels.

Baseline measured 2026-07-23 on the unfixed tree (1 thread, ER m=3n):

    n      F         dF
    50     10.3 us   200 us
    100    26.5 us   905 us
    200    88.7 us   3850 us

The cause was that F and dF rebuilt the whole igraph graph from a dense n x n
matrix for every candidate, and dF additionally malloc'd n*n doubles per
candidate. dR and degree, which hoist the APSP out of the loop, cost 0.4-0.8 us.

Run with:  pytest tests/test_perf.py --runslow -s
"""
import time

import igraph as ig
import pytest

from conftest import make_graphtacle
from _ext.wrapper import cython_wrapper_bruteforce

# n -> max microseconds per candidate
F_BUDGET = {50: 3.0, 100: 5.0, 200: 10.0}
DF_BUDGET = {50: 80.0, 100: 300.0, 200: 1200.0}


def _bruteforce_us_per_candidate(n, oper, k=2):
    g = ig.Graph.Erdos_Renyi(n=n, m=n * 3)
    graph = make_graphtacle(g)
    combinations = n * (n - 1) // 2
    start = time.perf_counter()
    cython_wrapper_bruteforce(graph, k, oper, mdist=2, n_threads=1)
    elapsed = time.perf_counter() - start
    return elapsed / combinations * 1e6


@pytest.mark.slow
@pytest.mark.parametrize("n", sorted(F_BUDGET))
def test_fragmentation_cost_per_candidate(n):
    us = _bruteforce_us_per_candidate(n, "F")
    print(f"\n  F  n={n:4d}  {us:8.2f} us/candidate  (budget {F_BUDGET[n]} us)")
    assert us < F_BUDGET[n]


@pytest.mark.slow
@pytest.mark.parametrize("n", sorted(DF_BUDGET))
def test_distance_fragmentation_cost_per_candidate(n):
    us = _bruteforce_us_per_candidate(n, "dF")
    print(f"\n  dF n={n:4d}  {us:8.2f} us/candidate  (budget {DF_BUDGET[n]} us)")
    assert us < DF_BUDGET[n]


@pytest.mark.slow
def test_bruteforce_on_400_nodes_completes():
    """This case did not finish inside 600 s on the unfixed tree; it now takes ~210 s.

    dF still needs a full all-pairs traversal of the residual graph for every one
    of the 79 800 candidates, which is the floor for the metric as defined -- the
    fix removed the per-candidate graph rebuild and the n*n allocation on top of
    it, not the APSP itself. The budget below is set from measurement, and this
    is single-threaded: -np divides it.
    """
    start = time.perf_counter()
    g = ig.Graph.Erdos_Renyi(n=400, m=1200)
    graph = make_graphtacle(g)
    cython_wrapper_bruteforce(graph, 2, "dF", mdist=2, n_threads=1)
    elapsed = time.perf_counter() - start
    print(f"\n  dF n=400 k=2 total {elapsed:.1f}s")
    assert elapsed < 300
