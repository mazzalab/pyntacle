"""Regression tests for percolation.py.

Covers the bugs found in the sanity check (see project memory
project_pyntacle_percolation.md):
  * run_percolation() built a dense (n, n) adjacency (`A`) that was never
    used for anything but a redundant shape check;
  * edge thresholds / open-edge flags were dense (n, n) matrices, and
    open_neighbors was built with an O(n^2) scan over one of them --
    the exact memory wall the CSR rewrite killed for the compiled kernels,
    reintroduced here in pure Python;
  * states_over_time appended a full state.copy() (length n) every step,
    with no CLI way to cap the step count -- O(n) per step, O(n^2) overall
    at default settings, even though nothing downstream read the per-step
    arrays themselves (only their count, or a single snapshot).

No tests existed for this module before this file.
"""
import gc
import tracemalloc

import numpy as np
import igraph as ig
import pytest

from percolation import run_percolation, summarize_percolation_results, \
    save_percolation_html_from_results_igraph, save_percolation_html_v2


def _cycle_with_weights():
    """4-node cycle, weights in [0,1], matches the numbers hand-verified
    against the CLI: A-B=0.4, B-C=0.6, C-D=0.9, D-A=0.2."""
    g = ig.Graph(4)
    g.add_edges([(0, 1), (1, 2), (2, 3), (3, 0)])
    g.es["weight"] = [0.4, 0.6, 0.9, 0.2]
    g.vs["label"] = ["A", "B", "C", "D"]
    return g


def _sparse_random(n=3000, m=9000, seed=0):
    rng_g = ig.Graph.Erdos_Renyi(n=n, m=m)
    g = rng_g.components().giant()
    g.vs["label"] = [str(i) for i in range(g.vcount())]
    return g


# ---------- no dense (n, n) adjacency is ever built ----------

def test_run_percolation_never_calls_get_adjacency():
    """The dense-matrix constructor must not be on the hot path at all."""
    g = _sparse_random(n=200, m=600)
    calls = []
    original = ig.Graph.get_adjacency

    def spy(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    ig.Graph.get_adjacency = spy
    try:
        run_percolation(g, Pstar=0.5, tau=4, seed_node=0)
    finally:
        ig.Graph.get_adjacency = original

    assert not calls, "run_percolation still builds a dense adjacency matrix"


def test_memory_footprint_stays_below_dense_bound():
    """A sparse 3000-node graph must not allocate anywhere near the dense n^2 matrix."""
    g = _sparse_random(n=3000, m=9000)
    n = g.vcount()

    gc.collect()
    tracemalloc.start()
    run_percolation(g, Pstar=0.5, tau=4, seed_node=0)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    dense_bytes = n * n * 8  # one float64 (n, n) matrix
    assert peak < dense_bytes / 2, (
        f"peak allocation {peak / 1e6:.1f} MB approaches the dense "
        f"{dense_bytes / 1e6:.1f} MB matrix -- it is still being built somewhere")


# ---------- edge_thresholds / open_edges are length-E, not (n, n) ----------

def test_edge_arrays_are_length_E_not_dense():
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)

    E = g.ecount()
    assert len(results["edges"]) == E
    assert results["edge_thresholds"].shape == (E,)
    assert results["open_edges"].shape == (E,)
    assert "states_over_time" not in results  # replaced by n_steps + snapshot_state


def test_weighted_thresholds_match_hand_calculated_open_edges():
    """A-B=0.4, B-C=0.6, C-D=0.9, D-A=0.2, P*=0.5 -> A-B and D-A open, rest blocked."""
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)

    open_by_pair = {
        frozenset(e): bool(is_open)
        for e, is_open in zip(results["edges"], results["open_edges"])
    }
    assert open_by_pair[frozenset((0, 1))] is True   # A-B, 0.4 <= 0.5
    assert open_by_pair[frozenset((1, 2))] is False  # B-C, 0.6 >  0.5
    assert open_by_pair[frozenset((2, 3))] is False  # C-D, 0.9 >  0.5
    assert open_by_pair[frozenset((3, 0))] is True   # D-A, 0.2 <= 0.5


def test_summarize_results_blocked_and_usable_counts():
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)
    summary = summarize_percolation_results(g, results)

    assert "blocked p_th≥P* = 2" in summary
    assert "usable Δt<τ_r = 2" in summary
    assert "Final reached (ever infected): 3 / 4" in summary


# ---------- open_neighbors (O(V+E) build) matches a naive dense reference ----------

@pytest.mark.parametrize("directed", [False, True])
def test_open_neighbors_matches_naive_dense_reference(directed):
    from percolation import _build_open_neighbors

    rng = np.random.default_rng(42)
    n = 40
    g = ig.Graph.Erdos_Renyi(n=n, m=100, directed=directed)
    edges = g.get_edgelist()
    open_mask = rng.random(len(edges)) < 0.5

    got = _build_open_neighbors(n, edges, open_mask, directed)

    # naive dense reference, built independently of the function under test
    dense = np.zeros((n, n), dtype=bool)
    for (i, j), is_open in zip(edges, open_mask):
        if not is_open:
            continue
        dense[i, j] = True
        if not directed:
            dense[j, i] = True

    for u in range(n):
        expected = np.where(dense[u, :])[0]
        assert sorted(got[u].tolist()) == sorted(expected.tolist())


# ---------- single-snapshot capture (states_over_time removal) ----------

def test_snapshot_infected_captures_one_state_at_right_step():
    g = _cycle_with_weights()
    results = run_percolation(
        g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True,
        snapshot_infected=2,
    )
    assert results["snapshot_state"] is not None
    assert results["snapshot_time"] == 1
    # A (seed) and D infected by t=1 via the open D-A edge; A itself infected at t=0
    assert results["snapshot_state"][0] == 1  # A infected
    assert results["snapshot_state"][3] == 1  # D infected


def test_snapshot_node_on_seed_captures_at_t0():
    g = _cycle_with_weights()
    results = run_percolation(
        g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True,
        snapshot_node="A",
    )
    assert results["snapshot_time"] == 0
    assert results["snapshot_state"][0] == 1


def test_no_snapshot_requested_leaves_it_none():
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)
    assert results["snapshot_state"] is None
    assert results["snapshot_time"] is None


def test_snapshot_infected_rejects_non_positive():
    g = _cycle_with_weights()
    with pytest.raises(ValueError):
        run_percolation(g, Pstar=0.5, tau=4, seed_node=0, snapshot_infected=0)


# ---------- max_steps is actually respected ----------

def test_max_steps_caps_the_simulation():
    g = _cycle_with_weights()
    results = run_percolation(
        g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True, max_steps=1,
    )
    assert results["n_steps"] <= 1


# ---------- HTML builder runs end-to-end without crashing ----------

def test_html_builder_runs_without_crashing(tmp_path):
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)
    out = str(tmp_path / "perc.html")
    path = save_percolation_html_from_results_igraph(g, results, filename=out)
    assert path == out
    content = tmp_path.joinpath("perc.html").read_text(encoding="utf-8")
    assert "percoFig" in content


def test_directed_graph_runs_end_to_end_without_crashing(tmp_path):
    """-d/--directed is a real CLI flag on this subcommand; open_edges/open_neighbors
    must not silently assume undirected (only _build_open_neighbors treats
    direction specially -- this exercises the full run_percolation ->
    summarize -> HTML pipeline on a directed graph, not just that helper)."""
    g = ig.Graph(4, directed=True)
    g.add_edges([(0, 1), (1, 2), (2, 3), (3, 0)])  # A->B->C->D->A
    g.es["weight"] = [0.4, 0.6, 0.9, 0.2]
    g.vs["label"] = ["A", "B", "C", "D"]

    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)

    # A->B (0.4) is open and traversable from seed A; B->C/C->D are blocked
    # (0.6, 0.9 > 0.5); D->A (0.2) is open but points the wrong way for A to
    # reach D, so only B is ever infected.
    assert results["activation_time"][1] == 1  # B
    assert np.isnan(results["activation_time"][2])  # C never reached
    assert np.isnan(results["activation_time"][3])  # D never reached

    summary = summarize_percolation_results(g, results)
    assert "Final reached (ever infected): 2 / 4" in summary

    out = str(tmp_path / "perc_directed.html")
    path = save_percolation_html_from_results_igraph(g, results, filename=out)
    assert path == out


def test_html_builder_handles_isolated_seed_with_no_spread(tmp_path):
    """Regression: infection_edges == {} used to fall back to a dense-matrix
    reconstruction that no longer exists -- must not crash on zero spread."""
    g = ig.Graph(3)  # no edges at all
    g.vs["label"] = ["A", "B", "C"]
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0)
    assert results["infection_edges"] == {}

    out = str(tmp_path / "perc_isolated.html")
    path = save_percolation_html_from_results_igraph(g, results, filename=out)
    assert path == out


# ---------- save_percolation_html_v2 ----------------------------------------
#
# A copy of save_percolation_html_from_results_igraph kept separate so the
# original is never touched while this one is iterated on (see
# project_pyntacle_percolation_html_v2 memory). First addition: an epidemic
# curve (S/I/R counts vs t) below the network animation, since active_counts/
# susceptible_counts/recovered_counts were already computed by run_percolation
# but never plotted anywhere in the original HTML.

def test_v2_runs_without_crashing_and_does_not_touch_the_original(tmp_path):
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)

    out_v1 = str(tmp_path / "perc_v1.html")
    out_v2 = str(tmp_path / "perc_v2.html")
    path_v1 = save_percolation_html_from_results_igraph(g, results, filename=out_v1)
    path_v2 = save_percolation_html_v2(g, results, filename=out_v2)

    assert path_v1 == out_v1 and path_v2 == out_v2
    v1_content = tmp_path.joinpath("perc_v1.html").read_text(encoding="utf-8")
    v2_content = tmp_path.joinpath("perc_v2.html").read_text(encoding="utf-8")
    assert "percoFig" in v1_content and "percoCurve" not in v1_content
    assert "percoFig" in v2_content and "percoCurve" in v2_content


def test_v2_epidemic_curve_embeds_all_three_sir_series(tmp_path):
    g = _cycle_with_weights()
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0, use_edge_weights_as_pth=True)
    out = str(tmp_path / "perc_v2.html")
    save_percolation_html_v2(g, results, filename=out)
    html = tmp_path.joinpath("perc_v2.html").read_text(encoding="utf-8")

    assert '"name":"Susceptible"' in html
    assert '"name":"Infected"' in html
    assert '"name":"Recovered"' in html
    # full (unsampled) time axis, one point per simulated step -- not the
    # possibly-subsampled `times` used for the network animation frames
    assert len(results["active_counts"]) == results["n_steps"] + 1


def test_v2_handles_isolated_seed_with_no_spread(tmp_path):
    """Same zero-spread regression the original is covered for -- the
    epidemic curve must still render (a flat Infected=0 line) rather than
    crash on an empty infection_edges dict."""
    g = ig.Graph(3)
    g.vs["label"] = ["A", "B", "C"]
    results = run_percolation(g, Pstar=0.5, tau=4, seed_node=0)
    out = str(tmp_path / "perc_v2_isolated.html")
    path = save_percolation_html_v2(g, results, filename=out)
    assert path == out
