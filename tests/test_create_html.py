"""Regression tests for create_html.create_local_html.

Covers the local-metrics HTML report rewrite:
  * the report used to embed a dense (n, n) adjacency matrix as a JS literal
    and scan it with a nested forEach to build links -- both an O(n^2) memory
    and CPU cost that scaled with n regardless of how sparse the graph was;
  * str({grafo.removed}) crashed with "unhashable type: list" any time
    -r/--remove was combined with the local command, since grafo.removed is a
    list of names, not a hashable value;
  * there was no size-based fallback at all: a large graph got the same
    animated D3 force layout as a 10-node graph, with no guard against
    handing the browser something it can't render smoothly.
"""
import json

import igraph as ig
import pandas as pd
import pytest

from GraphTacle import Graphtacle
import create_html
from create_html import (
    create_local_html, _LOCAL_LIVE_MAX_NODES, _LOCAL_STATIC_MAX_NODES,
    create_keyplayer_html, _KP_STATIC_MAX_NODES,
    create_groupcentrality_html, _GC_STATIC_MAX_NODES,
)


def _graphtacle(g, name="test"):
    n = g.vcount()
    names = [str(i) for i in range(n)]
    return Graphtacle(n, g.get_edgelist(), names, list(names), [1.0] * g.ecount(),
                       False, "edgelist", None, True, name, "keyplayer")


def _metrics_df(g):
    return pd.DataFrame({
        "Node Name": g.vs["label"],
        "Degree": g.degree(),
        "Betweenness": g.betweenness(weights=g.es["weight"]),
        "Closeness": g.closeness(weights=g.es["weight"]),
    })


def test_never_calls_get_adjacency(tmp_path):
    """The dense-matrix constructor must not be on the hot path at all."""
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    df = _metrics_df(g)
    calls = []
    original = ig.Graph.get_adjacency

    def spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    ig.Graph.get_adjacency = spy
    try:
        create_local_html(df, g, str(tmp_path))
    finally:
        ig.Graph.get_adjacency = original

    assert not calls, "create_local_html still builds a dense adjacency matrix"


def test_output_embeds_edge_list_not_dense_matrix(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    df = _metrics_df(g)
    create_local_html(df, g, str(tmp_path))
    html = (tmp_path / "zachary_local.html").read_text(encoding="utf-8")

    edges_json = json.dumps(g.get_edgelist())
    assert edges_json in html
    assert "var EDGES = " in html
    assert "forceSimulation" in html


def test_removed_nodes_does_not_crash(tmp_path):
    """Regression: str({grafo.removed}) raised TypeError for a list value."""
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    g.remove_node(["0", "1"])
    df = _metrics_df(g)

    create_local_html(df, g, str(tmp_path))  # must not raise

    html = (tmp_path / "zachary_local.html").read_text(encoding="utf-8")
    assert "Removed nodes: ['0', '1']" in html


def test_no_removed_nodes_reports_none(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    df = _metrics_df(g)
    create_local_html(df, g, str(tmp_path))
    html = (tmp_path / "zachary_local.html").read_text(encoding="utf-8")
    assert "Removed nodes: None" in html


def test_small_graph_gets_live_animated_interactive_view(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    assert g.vcount() <= _LOCAL_LIVE_MAX_NODES
    df = _metrics_df(g)
    create_local_html(df, g, str(tmp_path))
    html = (tmp_path / "zachary_local.html").read_text(encoding="utf-8")

    assert "var LIVE_ANIMATED = true;" in html
    assert 'id="export-svg-btn"' in html
    assert 'id="export-png-btn"' in html
    assert 'id="edge-toggle"' in html
    assert 'id="metric-min"' in html and 'id="metric-max"' in html
    assert 'id="node-popup"' in html
    assert '<div class="warning-banner"' not in html


def test_medium_graph_gets_static_settled_view(tmp_path, monkeypatch):
    """Above _LOCAL_LIVE_MAX_NODES but within the static cap: still interactive,
    but the layout is settled once instead of continuously animated."""
    monkeypatch.setattr(create_html, "_LOCAL_LIVE_MAX_NODES", 5)
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")  # 34 nodes > 5
    assert g.vcount() <= create_html._LOCAL_STATIC_MAX_NODES
    df = _metrics_df(g)
    create_local_html(df, g, str(tmp_path))
    html = (tmp_path / "zachary_local.html").read_text(encoding="utf-8")

    assert "var LIVE_ANIMATED = false;" in html
    assert 'id="export-svg-btn"' in html  # still a real network view, not the fallback


def test_oversized_graph_falls_back_to_table_only(tmp_path, monkeypatch):
    """Above the static cap: no D3 network at all, table + warning banner instead."""
    monkeypatch.setattr(create_html, "_LOCAL_STATIC_MAX_NODES", 5)
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")  # 34 nodes > 5
    df = _metrics_df(g)
    create_local_html(df, g, str(tmp_path))
    html = (tmp_path / "zachary_local.html").read_text(encoding="utf-8")

    assert '<div class="warning-banner"' in html
    assert 'id="metrics-table"' in html
    assert "forceSimulation" not in html
    assert "var EDGES" not in html  # no point embedding edges with no graph to draw


def test_node_names_with_html_special_characters_are_not_double_embedded_raw(tmp_path):
    """Node/metric values reach the popup via textContent in the JS, not string
    concatenation into innerHTML -- this just pins that the raw JSON payload
    (which is safe, JSON-escaped) is what's embedded, not a hand-built HTML string."""
    g = ig.Graph(2)
    g.add_edges([(0, 1)])
    g.vs["name"] = ["<b>A</b>", "B"]
    g.vs["label"] = ["<b>A</b>", "B"]
    g.es["weight"] = [1.0]
    gt = Graphtacle(2, g.get_edgelist(), g.vs["name"], g.vs["label"], [1.0], False,
                     "edgelist", None, True, "special", "keyplayer")
    df = pd.DataFrame({"Node Name": gt.vs["label"], "Degree": gt.degree()})

    create_local_html(df, gt, str(tmp_path))  # must not raise
    html = (tmp_path / "special_local.html").read_text(encoding="utf-8")
    assert json.dumps(["<b>A</b>", "B"]) in html


# --- create_keyplayer_html ---------------------------------------------------
#
# df_metrics must have exactly the columns Operation/KeySet/Score, one row per
# key-player metric -- KeySet is a plain list of node names (every algorithm in
# this codebase returns exactly one optimal set per metric, never several
# candidates, so there is nothing to browse beyond picking the metric). Covers
# the same dense-matrix/removed-nodes bug classes as create_local_html, plus
# the metric-highlight feature the report exists for.

def _kp_all_df():
    return pd.DataFrame({
        "Operation": ["F", "dF", "dR", "mreach"],
        "KeySet": [["0", "1"], ["0", "1"], ["2", "3"], ["33"]],
        "Score": [0.4, 0.5, 0.6, 0.3],
    })


def test_keyplayer_never_calls_get_adjacency(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    calls = []
    original = ig.Graph.get_adjacency

    def spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    ig.Graph.get_adjacency = spy
    try:
        create_keyplayer_html(_kp_all_df(), g, str(tmp_path), "zachary")
    finally:
        ig.Graph.get_adjacency = original

    assert not calls, "create_keyplayer_html still builds a dense adjacency matrix"


def test_keyplayer_output_embeds_edge_list_and_keyinfo(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    create_keyplayer_html(_kp_all_df(), g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_keyplayer.html").read_text(encoding="utf-8")

    assert json.dumps(g.get_edgelist()) in html
    assert "var EDGES = " in html
    assert '"Operation": "dR"' in html
    assert '"KeySet": ["2", "3"]' in html


def test_keyplayer_removed_nodes_does_not_crash(tmp_path):
    """Regression: str({grafo.removed}) raised TypeError for a list value."""
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    g.remove_node(["0", "1"])

    create_keyplayer_html(_kp_all_df(), g, str(tmp_path), "zachary")  # must not raise

    html = (tmp_path / "zachary_keyplayer.html").read_text(encoding="utf-8")
    assert "Removed nodes: ['0', '1']" in html


def test_keyplayer_single_metric_shape(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    df = pd.DataFrame({"Operation": ["F"], "KeySet": [["0", "1", "2"]], "Score": [0.42]})
    create_keyplayer_html(df, g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_keyplayer.html").read_text(encoding="utf-8")

    assert '"Operation": "F"' in html
    assert '"KeySet": ["0", "1", "2"]' in html


def test_keyplayer_small_graph_gets_interactive_view(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    create_keyplayer_html(_kp_all_df(), g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_keyplayer.html").read_text(encoding="utf-8")

    assert "forceSimulation" in html
    assert 'id="metric-select"' in html
    assert 'id="score-display"' in html
    assert 'id="set-display"' in html
    assert 'id="export-svg-btn"' in html
    assert 'id="export-png-btn"' in html
    # no filtering UI -- explicitly out of scope for this report
    assert 'id="metric-min"' not in html
    assert 'id="metric-max"' not in html
    assert '<div class="warning-banner"' not in html


def test_keyplayer_oversized_graph_falls_back_to_table_only(tmp_path, monkeypatch):
    monkeypatch.setattr(create_html, "_KP_STATIC_MAX_NODES", 5)
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")  # 34 nodes > 5
    create_keyplayer_html(_kp_all_df(), g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_keyplayer.html").read_text(encoding="utf-8")

    assert '<div class="warning-banner"' in html
    assert "forceSimulation" not in html
    assert "var EDGES" not in html
    assert "0, 1" in html  # KeySet rendered in the fallback table


# --- create_groupcentrality_html ----------------------------------------------
#
# df_metrics must have exactly the columns Operation/NodeSet/Score, one row per
# group-centrality metric -- NodeSet is a plain list of node names (same
# one-optimal-set-per-metric contract as create_keyplayer_html, and the same
# dense-matrix/removed-nodes bug classes).

def _gc_all_df():
    return pd.DataFrame({
        "Operation": ["Degree", "Betweenness", "Closeness"],
        "NodeSet": [["0", "1"], ["0", "33"], ["2", "3"]],
        "Score": [0.4, 120.5, 0.6],
    })


def test_groupcentrality_never_calls_get_adjacency(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    calls = []
    original = ig.Graph.get_adjacency

    def spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    ig.Graph.get_adjacency = spy
    try:
        create_groupcentrality_html(_gc_all_df(), g, str(tmp_path), "zachary")
    finally:
        ig.Graph.get_adjacency = original

    assert not calls, "create_groupcentrality_html still builds a dense adjacency matrix"


def test_groupcentrality_output_embeds_edge_list_and_gcinfo(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    create_groupcentrality_html(_gc_all_df(), g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_groupcentrality.html").read_text(encoding="utf-8")

    assert json.dumps(g.get_edgelist()) in html
    assert "var EDGES = " in html
    assert '"Operation": "Betweenness"' in html
    assert '"NodeSet": ["0", "33"]' in html


def test_groupcentrality_removed_nodes_does_not_crash(tmp_path):
    """Regression: str({grafo.removed}) raised TypeError for a list value."""
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    g.remove_node(["0", "1"])

    create_groupcentrality_html(_gc_all_df(), g, str(tmp_path), "zachary")  # must not raise

    html = (tmp_path / "zachary_groupcentrality.html").read_text(encoding="utf-8")
    assert "Removed nodes: ['0', '1']" in html


def test_groupcentrality_single_metric_shape(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    df = pd.DataFrame({"Operation": ["Degree"], "NodeSet": [["0", "1", "2"]], "Score": [0.42]})
    create_groupcentrality_html(df, g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_groupcentrality.html").read_text(encoding="utf-8")

    assert '"Operation": "Degree"' in html
    assert '"NodeSet": ["0", "1", "2"]' in html


def test_groupcentrality_small_graph_gets_interactive_view(tmp_path):
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")
    create_groupcentrality_html(_gc_all_df(), g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_groupcentrality.html").read_text(encoding="utf-8")

    assert "forceSimulation" in html
    assert 'id="metric-select"' in html
    assert 'id="score-display"' in html
    assert 'id="set-display"' in html
    assert 'id="export-svg-btn"' in html
    assert 'id="export-png-btn"' in html
    # no filtering UI -- explicitly out of scope for this report, same as keyplayer
    assert 'id="metric-min"' not in html
    assert 'id="metric-max"' not in html
    assert '<div class="warning-banner"' not in html


def test_groupcentrality_oversized_graph_falls_back_to_table_only(tmp_path, monkeypatch):
    monkeypatch.setattr(create_html, "_GC_STATIC_MAX_NODES", 5)
    g = _graphtacle(ig.Graph.Famous("Zachary"), name="zachary")  # 34 nodes > 5
    create_groupcentrality_html(_gc_all_df(), g, str(tmp_path), "zachary")
    html = (tmp_path / "zachary_groupcentrality.html").read_text(encoding="utf-8")

    assert '<div class="warning-banner"' in html
    assert "forceSimulation" not in html
    assert "var EDGES" not in html
    assert "0, 1" in html  # NodeSet rendered in the fallback table
