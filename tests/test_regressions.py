"""One test per finding from the 2026-07-23 sanity check.

Each test carries the reproduction that exposed the bug, so a regression fails
here rather than in someone's analysis.
"""
import math
import os
import subprocess
import sys
import textwrap

import igraph as ig
import pytest

from conftest import make_graphtacle, PKG_DIR, REPO_ROOT

from GraphTacle import Graphtacle
import algorithms.greedy as greedy
import algorithms.stochastic_gradient_descent as sgd
from algorithms.key_player import keyplayer_kpInfo
from _ext.wrapper import cython_wrapper_info

PYTHON = sys.executable


# ---------------------------------------------------------------- P0 crashes

def test_directed_graph_is_rejected_not_aborted():
    """A directed graph must raise, not SIGABRT the interpreter.

    cython_igraph.pyx hardcodes IGRAPH_ADJ_UNDIRECTED while wrapper.py feeds it an
    asymmetric adjacency matrix; igraph's default error handler then abort()s from
    inside a nogil block, killing the process with exit 134 and no traceback.

    Run out-of-process: if the bug is present it takes the test runner down too.
    """
    script = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {PKG_DIR!r})
        import igraph as ig
        from GraphTacle import Graphtacle
        from _ext.wrapper import cython_wrapper_info

        gd = ig.Graph(4, directed=True)
        gd.add_edges([(0, 1), (1, 2), (2, 3)])
        G = Graphtacle(4, gd.get_edgelist(), list("abcd"), list("abcd"),
                       [1.0] * 3, True, "edgelist", None, True, "d", "keyplayer")
        try:
            cython_wrapper_info(G, ["a"], "dR", "min", 1, 1)
        except ValueError as exc:
            print("RAISED_VALUEERROR")
            sys.exit(0)
        print("NO_ERROR_RAISED")
        sys.exit(1)
    """)
    proc = subprocess.run([PYTHON, "-c", script], capture_output=True, text=True,
                          cwd=REPO_ROOT, timeout=120)
    assert proc.returncode != -6 and "Aborted" not in proc.stderr, (
        f"process aborted (rc={proc.returncode}); stderr:\n{proc.stderr}"
    )
    assert "RAISED_VALUEERROR" in proc.stdout, (
        f"rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )


def test_sgd_operation_selector_handles_dF(zachary):
    """gradient_descent + dF raised KeyError: 'Attribute does not exist'.

    stochastic_gradient_descent.operation_selector built the temp graph without
    edge_attrs={"weight": ...}, then distance_fragmentation_Borgatti read
    grafo.es["weight"].
    """
    result = sgd.operation_selector(zachary, "dF", ["0", "33"], mdist=2)
    assert math.isfinite(result)


def test_keyplayer_kpInfo_handles_dF(zachary):
    """Same missing-weight bug on the keyplayer_kpInfo path."""
    result = keyplayer_kpInfo(zachary, ["0", "33"], "dF")
    assert math.isfinite(result)


def test_keyplayer_kpInfo_all_handles_dF(zachary):
    scores = keyplayer_kpInfo(zachary, ["0", "33"], "all", mdist=2)
    assert set(scores) == {"F", "dF", "dR", "mreach"}
    for name, value in scores.items():
        assert math.isfinite(value), f"{name} = {value}"


# ------------------------------------------------------------ P1 wrong numbers

@pytest.mark.parametrize("distance_type", ["min", "mean", "max"])
def test_group_closeness_on_disconnected_graph_is_not_silently_zero(
        three_components, distance_type):
    """INF was hardcoded to 1e9 while igraph returns a real IEEE inf, so the
    `!= INF` guards never fired and mean/max returned 0.0 with no warning."""
    nodes = ["0", "4"]
    cy = cython_wrapper_info(three_components, nodes, "closeness",
                             distance_type=distance_type, mdist=2, n_threads=1)
    assert cy > 0.0, (
        f"closeness/{distance_type} collapsed to {cy} on a 3-component graph"
    )


@pytest.mark.parametrize("scale", [0.1, 1.0, 10.0])
def test_mreach_is_hop_based_not_weight_based(scale):
    """m-reach counts nodes within `m` HOPS. Scaling every weight uniformly must
    not change it; before the fix Zachary m=2 went 32 -> 32 -> 0 for x0.1/x1/x10."""
    g = ig.Graph.Famous("Zachary")
    graph = make_graphtacle(g, weights=[scale] * g.ecount())
    cy = cython_wrapper_info(graph, ["0", "33"], "mreach", "min", 2, 1)
    assert cy == 32.0, f"weights x{scale} changed m-reach to {cy}"


@pytest.mark.parametrize("scale", [0.1, 1.0, 10.0])
def test_group_degree_never_exceeds_one(scale):
    """group degree is a fraction of non-group nodes adjacent to the group, so it
    is bounded by 1. The Cython kernel counted a node once per adjacent group
    member instead of once, yielding 1.323 on Zachary."""
    g = ig.Graph.Famous("Zachary")
    graph = make_graphtacle(g, weights=[scale] * g.ecount())
    cy = cython_wrapper_info(graph, ["0", "33", "2"], "degree", "min", 2, 1)
    assert 0.0 <= cy <= 1.0, f"group degree out of range: {cy}"


def test_zero_weight_edge_is_rejected(tmp_path):
    """A 0-weight edge is indistinguishable from an absent edge once the graph is
    handed to igraph as a weighted adjacency matrix: path 0-1-2-3 with the middle
    weight at 0 was seen as two components by the Cython engine and one by igraph."""
    edgelist = tmp_path / "zero_weight.tsv"
    edgelist.write_text("V1\tV2\tweight\n0\t1\t1.0\n1\t2\t0.0\n2\t3\t1.0\n")
    with pytest.raises(ValueError, match="(?i)zero"):
        Graphtacle.from_file(str(edgelist), "keyplayer", "edgelist",
                             sep="\t", header=True, directed=False, weight=True)


@pytest.mark.parametrize("metric", ["completeness_naive", "completeness", "compactness"])
@pytest.mark.parametrize("builder", [ig.Graph.Ring, ig.Graph.Full])
def test_density_metrics_are_orientation_consistent(metric, builder):
    """All three metrics count adjacency-matrix non-zeros, so one network must
    score the same whether it is expressed as undirected or as directed-mutual.

    completeness_naive and compactness had their directed/undirected branches
    swapped relative to completeness, which is the one that was already right.
    """
    g = builder(10)
    undirected = make_graphtacle(g)
    directed = make_graphtacle(g.as_directed(mode="mutual"), directed=True)

    assert getattr(undirected, metric)(directed=False) == pytest.approx(
        getattr(directed, metric)(directed=True)), (
        f"{metric} depends on how the same network is oriented"
    )


def test_radiality_stays_positive_on_weighted_graph():
    """radiality mixed a weighted mean distance with an UNWEIGHTED diameter, so on
    a graph with weights well above 1 it went negative and lost all meaning."""
    g = ig.Graph(6)
    g.add_edges([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    graph = make_graphtacle(g, weights=[10.0, 25.0, 5.0, 30.0, 15.0])
    values = graph.radiality()
    assert all(v > 0 for v in values), f"negative radiality: {values}"


def test_shortestpath_count_does_not_overflow():
    """get_shortestpath_count used np.int16; a layered graph easily exceeds 32767
    geodesics between one pair and the count wrapped around to a negative number."""
    m = 200  # m*m = 40000 distinct s->t geodesics, above the int16 ceiling
    g = ig.Graph(2 * m + 2)
    s, t = 2 * m, 2 * m + 1
    edges = [(s, i) for i in range(m)]
    edges += [(i, m + j) for i in range(m) for j in range(m)]
    edges += [(m + j, t) for j in range(m)]
    g.add_edges(edges)
    graph = make_graphtacle(g)
    counts = graph.get_shortestpath_count()
    assert counts.min() >= 0, "negative geodesic count -> integer overflow"


# ------------------------------------------------------------------ P3 hygiene

def test_removing_every_edge_yields_maximal_fragmentation(star):
    """`if temp_grafo.ecount == 0` compared a bound method to 0 and was always
    False. Removing the star centre deletes every edge, so F must be 1."""
    assert greedy.operation_selector(star, "F", ["0"], mdist=1) == pytest.approx(1.0)
    assert sgd.operation_selector(star, "F", ["0"], mdist=1) == pytest.approx(1.0)


def test_graph_instances_do_not_share_state(zachary, star):
    """removed/sub_func/outdir were class attributes assigned via `Graphtacle.x =`,
    so every instance saw the last write. The `set` command keeps two graphs alive."""
    zachary.nameSub_function("finder_F")
    star.nameSub_function("info_dR")
    zachary.remove_node(["1"])
    star.remove_node(["7"])
    assert zachary.sub_func == "finder_F"
    assert star.sub_func == "info_dR"
    assert zachary.removed == ["1"]
    assert star.removed == ["7"]


def test_export_file_is_idempotent(zachary, tmp_path):
    """export_file assigned the report path back to self.name, so a second call
    produced report_report_<name>."""
    import pandas as pd
    df = pd.DataFrame({"a": [1, 2]})
    zachary.export_file(df, str(tmp_path))
    zachary.export_file(df, str(tmp_path))
    produced = sorted(p.name for p in tmp_path.iterdir())
    assert produced == ["report_zachary_keyplayer.tsv"], produced


def test_greedy_is_reproducible_with_a_seed(zachary):
    """greedy picks its starting set with an unseeded pandas sample(frac=1.0)."""
    from algorithms.greedy import call_greedy
    first = call_greedy(zachary, 3, "F", seed=1234)
    second = call_greedy(zachary, 3, "F", seed=1234)
    assert first == second


@pytest.mark.parametrize("oper", ["F", "dF", "mreach"])
def test_cython_greedy_is_reproducible_with_a_seed(zachary, oper):
    """Same for the compiled engine, which is the one the CLI actually runs.

    The greedy search only finds a local optimum, so an unseeded start makes two
    identical commands disagree on which of several equally-scoring sets they
    report -- exactly what the CLI did before the seed was threaded through.
    """
    from _ext.wrapper import cython_wrapper_greedy
    first = cython_wrapper_greedy(zachary, 3, oper, mdist=2, n_threads=1, seed=1234)
    second = cython_wrapper_greedy(zachary, 3, oper, mdist=2, n_threads=1, seed=1234)
    assert first == second


def test_cli_remove_node_survives_the_graphtacle_rebuild(tmp_path):
    """Regression: -r's node list used to vanish from every downstream report.

    main.py stamps `g.removed` via remove_node(), then deletes those vertices
    and rebuilds `g` with Graphtacle.re() -- but re() calls __init__, which
    resets self.removed = None on the *new* instance, silently discarding it.
    Every report (HTML/TSV) then printed "Removed nodes: None" even though -r
    was passed and the vertices really were gone.
    """
    edgelist = tmp_path / "toy.tsv"
    edgelist.write_text("A\tB\nB\tC\nC\tD\nD\tA\nA\tC\n")
    outdir = tmp_path / "out"
    outdir.mkdir()

    proc = subprocess.run(
        [PYTHON, os.path.join(PKG_DIR, "main.py"), "keyplayer", "kp-finder",
         "-t", "edgelist", "-i", str(edgelist), "-nh", "-r", "A",
         "-a", "greedy", "--seed", "1", "-o", str(outdir)],
        capture_output=True, text=True, cwd=PKG_DIR,
    )
    assert proc.returncode == 0, proc.stderr

    html_path = outdir / "toy_NoNodes_keyplayer.html"
    assert html_path.exists(), f"expected report not found; stderr:\n{proc.stderr}"
    html = html_path.read_text(encoding="utf-8")
    assert "Removed nodes: ['A']" in html
    assert "Removed nodes: None" not in html


def test_cli_groupcentrality_html_gets_correct_operation_nodeset_score(tmp_path):
    """Regression: groupcentrality's df went straight to create_groupcentrality_html
    with whatever column names/shapes each algorithm branch happened to produce
    ("Group Centrality" vs "Groupcentrality" vs a copy-pasted "Key-player" column,
    and -- for a single operation -- one row per found node instead of one row
    per metric), none of which matched the Operation/NodeSet/Score contract the
    report's JS actually reads. The metric-select/highlight feature was silently
    broken for every real run, exactly like the keyplayer report before its fix.
    """
    edgelist = tmp_path / "toy.tsv"
    edgelist.write_text("A\tB\nB\tC\nC\tD\nD\tA\nA\tC\n")
    outdir = tmp_path / "out"
    outdir.mkdir()

    # "all": every algorithm branch must produce one row per metric with a
    # NodeSet list-cell, not the raw operation/score column names.
    proc = subprocess.run(
        [PYTHON, os.path.join(PKG_DIR, "main.py"), "groupcentrality", "gc-finder",
         "-t", "edgelist", "-i", str(edgelist), "-nh", "-k", "2",
         "-a", "greedy", "--seed", "1", "-o", str(outdir)],
        capture_output=True, text=True, cwd=PKG_DIR,
    )
    assert proc.returncode == 0, proc.stderr
    html = (outdir / "toy_groupcentrality.html").read_text(encoding="utf-8")
    assert '"Operation": "degree"' in html
    assert '"Operation": "betweenness"' in html
    assert '"Operation": "closeness"' in html
    assert "var GCINFO = " in html

    # single operation: must collapse to one row (Operation/NodeSet/Score),
    # not one row per found node with the score broadcast onto every row.
    proc = subprocess.run(
        [PYTHON, os.path.join(PKG_DIR, "main.py"), "groupcentrality", "gc-finder",
         "-t", "edgelist", "-i", str(edgelist), "-nh", "-k", "2", "-oper", "degree",
         "-a", "brute_force", "-o", str(outdir)],
        capture_output=True, text=True, cwd=PKG_DIR,
    )
    assert proc.returncode == 0, proc.stderr
    html = (outdir / "toy_groupcentrality.html").read_text(encoding="utf-8")
    import re
    gcinfo = re.search(r"var GCINFO = (\[.*?\]);", html).group(1)
    import json as _json
    records = _json.loads(gcinfo)
    assert len(records) == 1
    assert records[0]["Operation"] == "degree"
    assert isinstance(records[0]["NodeSet"], list) and len(records[0]["NodeSet"]) == 2


def test_cli_threads_the_seed_into_the_cython_engine():
    """main.py must pass `seed` to every cython_wrapper_greedy call site."""
    import inspect
    import re

    source = inspect.getsource(sys.modules["__main__"]) if False else open(
        os.path.join(PKG_DIR, "main.py")).read()

    calls = re.findall(r"cython_wrapper_greedy\((?:[^()]|\([^()]*\))*\)", source)
    assert calls, "no cython_wrapper_greedy call sites found in main.py"
    unseeded = [c for c in calls if "seed" not in c]
    assert not unseeded, f"call sites without a seed: {unseeded}"
