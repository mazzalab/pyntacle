"""The Cython engine and the pure-Python engine must agree on every metric.

Both engines are shipped and both are reachable from the CLI, so a divergence is
a silently wrong published number. The Python engine is the reference: it is the
historical behaviour.
"""
import math

import pytest

from algorithms.greedy import operation_selector as python_metric
from _ext.wrapper import cython_wrapper_info

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
