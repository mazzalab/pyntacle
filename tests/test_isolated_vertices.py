"""Trailing isolated vertices must survive every internal graph copy.

Half the codebase rebuilds a plain igraph view of the network with

    ig.Graph(directed=False, vertex_attrs={...}, edges=grafo.get_edgelist(), ...)

Without an explicit ``n``, igraph sizes the new graph from the highest endpoint
in the edge list, so any vertex whose index is above that -- i.e. any *trailing*
isolate -- is dropped, and the vertex-attribute lists are silently truncated to
match. An all-zero last row in an adjacency matrix is exactly that case, and it
is not exotic: it is what a gene with no measured interaction looks like.

The compiled kernels are unaffected (they read the dense adjacency built by the
Graphtacle itself, which does pass ``n``), so the symptom is the two engines
disagreeing on a network that loads and prints perfectly.
"""
import os
import sys

import igraph as ig
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "pyntacle"))

from GraphTacle import Graphtacle  # noqa: E402
from _ext.wrapper import cython_wrapper_info  # noqa: E402
from algorithms.key_player import keyplayer_kpInfo, prune_graph  # noqa: E402
from algorithms.group_centrality import groupcentrality_gcInfo  # noqa: E402
from utility import components_by_nodes  # noqa: E402


@pytest.fixture
def triangle_plus_isolate():
    """A-B-C triangle plus a disconnected D, which is the *last* vertex."""
    g = ig.Graph(4)
    g.add_edges([(0, 1), (0, 2), (1, 2)])
    names = ["A", "B", "C", "D"]
    return Graphtacle(4, g.get_edgelist(), names, list(names), [1.0, 1.0, 1.0],
                      False, "edgelist", None, True, "iso", "keyplayer")


def test_prune_graph_keeps_the_isolate(triangle_plus_isolate):
    pruned = prune_graph(triangle_plus_isolate, ["A"])
    assert sorted(pruned.vs["name"]) == ["B", "C", "D"]


def test_keyplayer_engines_agree_with_a_trailing_isolate(triangle_plus_isolate):
    for oper in ["F", "dF", "dR", "mreach"]:
        fast = cython_wrapper_info(triangle_plus_isolate, ["A"], oper,
                                   distance_type="min", mdist=2, n_threads=1)
        slow = keyplayer_kpInfo(triangle_plus_isolate, ["A"], oper, mdist=2)
        assert fast == pytest.approx(slow, abs=1e-3), f"{oper}: cython={fast} python={slow}"


def test_groupcentrality_engines_agree_with_a_trailing_isolate(triangle_plus_isolate):
    for oper in ["degree", "betweenness", "closeness"]:
        fast = cython_wrapper_info(triangle_plus_isolate, ["A"], oper,
                                   distance_type="min", mdist=-1, n_threads=1)
        slow = groupcentrality_gcInfo(triangle_plus_isolate, ["A"], oper, distance_type="min")
        assert fast == pytest.approx(slow, abs=1e-3), f"{oper}: cython={fast} python={slow}"


def test_components_by_nodes_sees_the_isolate(triangle_plus_isolate):
    """D is a component of its own, so asking for it must return it.

    components_by_nodes keeps only the components containing one of the
    requested names and returns the union as a single graph. Before the copy
    kept its vertex count, D was not in the graph at all and asking for it
    yielded nothing.
    """
    graph, _df = components_by_nodes(triangle_plus_isolate, ["A", "D"])
    assert "D" in graph.vs["name"], f"isolate missing: {graph.vs['name']}"
    assert sorted(graph.vs["name"]) == ["A", "B", "C", "D"]


def test_radiality_reach_covers_every_vertex(triangle_plus_isolate):
    """radiality_reach returns one value per vertex; a lost isolate shortens the list."""
    values = triangle_plus_isolate.radiality_reach()
    assert len(values) == triangle_plus_isolate.vcount()


def test_isolate_is_only_lost_when_it_is_the_last_vertex(triangle_plus_isolate):
    """Documents the shape of the bug: a leading isolate survives, a trailing one does not.

    Keeps the regression honest -- a fix that only reorders vertices would pass
    the tests above while leaving the real defect in place.
    """
    g = ig.Graph(4)
    g.add_edges([(1, 2), (1, 3), (2, 3)])  # vertex 0 is the isolate this time
    leading = ig.Graph(directed=False, edges=g.get_edgelist())
    assert leading.vcount() == 4, "a leading isolate was never at risk"
