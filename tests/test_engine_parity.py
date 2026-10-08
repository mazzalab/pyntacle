"""The Cython engine and the pure-Python engine must agree on every metric.

Both engines are shipped and both are reachable from the CLI, so a divergence is
a silently wrong published number. The Python engine is the reference: it is the
historical behaviour.
"""
import math

import pytest

from pyntacle.algorithms.greedy import operation_selector as python_metric
from pyntacle._ext.wrapper import cython_wrapper_info

KP_METRICS = ["F", "dF", "dR", "mreach"]
GROUP_METRICS = ["degree", "betweenness", "closeness"]
ALL_METRICS = KP_METRICS + GROUP_METRICS

GRAPHS = ["zachary", "er_connected", "three_components", "weighted_path", "star"]

TOL = 1e-3


def pick_k(graph, size=3):
    """Deterministic K: the `size` highest-degree nodes, ties broken by index."""
    order = sorted(range(graph.vcount()),
                   key=lambda i: (-graph.degree(i), i))
    return [graph.vs[i]["name"] for i in order[:size]]


def cython_metric(graph, oper, nodes, distance_type="min", mdist=2):
    return cython_wrapper_info(graph, nodes, oper, distance_type=distance_type,
                               mdist=mdist, n_threads=1)


@pytest.mark.parametrize("metric", ALL_METRICS)
@pytest.mark.parametrize("graph_name", GRAPHS)
def test_engines_agree(request, graph_name, metric):
    graph = request.getfixturevalue(graph_name)
    nodes = pick_k(graph)

    py = python_metric(graph, metric, nodes, distance_type="min", mdist=2)
    cy = cython_metric(graph, metric, nodes, distance_type="min", mdist=2)

    assert math.isfinite(py), f"python engine returned {py} for {metric}"
    assert math.isfinite(cy), f"cython engine returned {cy} for {metric}"
    assert abs(py - cy) < TOL, (
        f"{metric} on {graph_name}: python={py!r} cython={cy!r} "
        f"(delta={abs(py - cy)!r})"
    )


@pytest.mark.parametrize("distance_type", ["min", "mean", "max"])
@pytest.mark.parametrize("graph_name", GRAPHS)
def test_group_closeness_agrees_for_every_distance_type(request, graph_name, distance_type):
    graph = request.getfixturevalue(graph_name)
    nodes = pick_k(graph)

    py = python_metric(graph, "closeness", nodes, distance_type=distance_type)
    cy = cython_metric(graph, "closeness", nodes, distance_type=distance_type)

    assert math.isfinite(py), f"python engine returned {py}"
    assert math.isfinite(cy), f"cython engine returned {cy}"
    assert abs(py - cy) < TOL, (
        f"closeness/{distance_type} on {graph_name}: python={py!r} cython={cy!r}"
    )


def _group_betweenness_by_enumeration(graph, nodes):
    """Every shortest path listed and checked for an inner group node."""
    group = {graph.vs.find(name=x).index for x in nodes}
    others = [v for v in range(graph.vcount()) if v not in group]
    total = 0.0
    for a, u in enumerate(others):
        paths = graph.get_all_shortest_paths(u, to=others[a + 1:], weights=graph.es["weight"])
        by_target = {}
        for p in paths:
            by_target.setdefault(p[-1], []).append(p)
        for v, ps in by_target.items():
            if v != u:
                total += sum(1 for p in ps if group & set(p[1:-1])) / len(ps)
    m = len(others)
    return 2 * total / (m * (m - 1))


@pytest.mark.parametrize("seed", range(6))
def test_group_betweenness_counts_weighted_shortest_paths(seed):
    # the python engine compared path lengths in hops, so on a weighted network it
    # subtracted the wrong counts and could even return a negative score
    import random
    import igraph as ig
    from conftest import make_graphtacle
    rng = random.Random(seed)
    g = ig.Graph.Erdos_Renyi(n=10, p=0.35, directed=False)
    graph = make_graphtacle(g, weights=[float(rng.randint(1, 3)) for _ in range(g.ecount())])
    nodes = rng.sample(graph.vs["name"], 3)
    expected = _group_betweenness_by_enumeration(graph, nodes)
    assert python_metric(graph, "betweenness", nodes) == pytest.approx(expected, abs=1e-12)
    assert cython_metric(graph, "betweenness", nodes) == pytest.approx(expected, abs=1e-12)
