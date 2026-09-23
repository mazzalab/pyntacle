"""Brute-force search must report every node set that reaches the best score.

Pyntacle 1.3.2 enumerated all optimal sets; the rewritten kernel kept a single
winner per thread and dropped the rest, so a run on a symmetric network hid most
of the answer. These tests pin the recovered behaviour.
"""
import json
import os
import re
import subprocess
import sys

import igraph as ig
import pytest

from conftest import make_graphtacle, PKG_DIR

PYTHON = sys.executable

from _ext.wrapper import cython_wrapper_bruteforce, DEFAULT_MAX_TIES


def barbell():
    """Two triangles joined by a bridge.

    Node 2 and node 3 are the bridge endpoints: deleting either one splits the
    graph into a 2-node and a 3-node component, so both score the same F and
    nothing else scores at all. Exactly two optimal sets, known by hand.
    """
    g = ig.Graph(6)
    g.add_edges([(0, 1), (1, 2), (2, 0),
                 (3, 4), (4, 5), (5, 3),
                 (2, 3)])
    return make_graphtacle(g, name="barbell")


def cycle(n=10):
    return make_graphtacle(ig.Graph.Ring(n), name="cycle")


def test_bruteforce_returns_every_optimal_set():
    k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(barbell(), 1, "F")

    assert n_optimal == 2
    assert sorted(tuple(s) for s in tied_sets) == [("2",), ("3",)]
    assert score > 0


def test_first_returned_set_is_the_reported_one():
    k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(barbell(), 1, "F")

    assert list(k_set) == list(tied_sets[0])


def test_group_centrality_ties_are_reported_too():
    """The same kernel serves groupcentrality: both bridge nodes have degree 3."""
    k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(barbell(), 1, "degree")

    assert n_optimal == 2
    assert sorted(tuple(s) for s in tied_sets) == [("2",), ("3",)]


def test_tie_cap_truncates_the_list_but_not_the_count():
    graph = cycle(10)
    _, _, all_sets, all_count = cython_wrapper_bruteforce(graph, 2, "F", max_ties=1000)
    _, _, capped_sets, capped_count = cython_wrapper_bruteforce(graph, 2, "F", max_ties=2)

    assert len(all_sets) > 2, "cycle C10 must have more than two optimal pairs"
    assert len(capped_sets) == 2
    assert capped_count == all_count


def test_unique_optimum_reports_a_single_set():
    """A star has one best node at k=1; the tie machinery must not invent ties."""
    star = make_graphtacle(ig.Graph.Star(15, mode="undirected", center=0), name="star")

    k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(star, 1, "F")

    assert n_optimal == 1
    assert tied_sets == [["0"]]


def test_score_is_not_rounded_by_the_kernel():
    """The kernel used to round to 3 decimals, which cost precision old Pyntacle kept.

    Deleting two opposite nodes of C10 leaves two paths of 4 nodes, so
    F = 1 - (4*3 + 4*3) / (8*7) = 0.571428..., which 3 decimals truncate.
    """
    _, score, _, _ = cython_wrapper_bruteforce(cycle(10), 2, "F")

    assert score == pytest.approx(1 - 24 / 56, abs=1e-9)


def test_default_cap_is_a_sane_constant():
    assert DEFAULT_MAX_TIES == 100


# ----------------------------------------------------------------- CLI level

BARBELL_EDGELIST = "A\tB\nB\tC\nC\tA\nD\tE\nE\tF\nF\tD\nC\tD\n"


def _run(tmp_path, *argv):
    edgelist = tmp_path / "barbell.tsv"
    edgelist.write_text(BARBELL_EDGELIST)
    outdir = tmp_path / "out"
    outdir.mkdir(exist_ok=True)
    proc = subprocess.run(
        [PYTHON, os.path.join(PKG_DIR, "main.py"), *argv,
         "-t", "edgelist", "-i", str(edgelist), "-nh", "-o", str(outdir)],
        capture_output=True, text=True, cwd=PKG_DIR,
    )
    assert proc.returncode == 0, proc.stderr
    return outdir


def test_cli_keyplayer_report_lists_every_optimal_set(tmp_path):
    """C and D both fragment the barbell identically; the report must show both."""
    outdir = _run(tmp_path, "keyplayer", "kp-finder", "-k", "1", "-oper", "F",
                  "-a", "brute_force")

    report = (outdir / "report_barbell_keyplayer_finder_F_brute_force.tsv").read_text()

    assert "Optimal sets\t2" in report
    assert "SetID" in report
    body = report.split("SetID")[1]
    assert "C" in body and "D" in body


def test_cli_keyplayer_html_carries_the_tied_sets(tmp_path):
    outdir = _run(tmp_path, "keyplayer", "kp-finder", "-k", "1", "-oper", "F",
                  "-a", "brute_force")

    html = (outdir / "barbell_keyplayer.html").read_text(encoding="utf-8")
    records = json.loads(re.search(r"var KEYINFO = (\[.*?\]);", html).group(1))

    assert len(records) == 1
    assert records[0]["NOptimal"] == 2
    assert sorted(tuple(s) for s in records[0]["Ties"]) == [("C",), ("D",)]


def test_cli_groupcentrality_report_lists_every_optimal_set(tmp_path):
    """C and D are the only degree-3 nodes, so gc-finder ties them at k=1."""
    outdir = _run(tmp_path, "groupcentrality", "gc-finder", "-k", "1",
                  "-oper", "degree", "-a", "brute_force")

    report = (outdir / "report_barbell_groupcentrality_finder_degree_brute_force.tsv").read_text()

    assert "Optimal sets\t2" in report
    assert "SetID" in report


def test_cli_groupcentrality_html_carries_the_tied_sets(tmp_path):
    outdir = _run(tmp_path, "groupcentrality", "gc-finder", "-k", "1",
                  "-oper", "degree", "-a", "brute_force")

    html = (outdir / "barbell_groupcentrality.html").read_text(encoding="utf-8")
    records = json.loads(re.search(r"var GCINFO = (\[.*?\]);", html).group(1))

    assert records[0]["NOptimal"] == 2
    assert sorted(tuple(s) for s in records[0]["Ties"]) == [("C",), ("D",)]


def test_cli_max_ties_flag_caps_the_reported_list(tmp_path):
    """The flag is optional; when given it truncates the list, not the count."""
    outdir = _run(tmp_path, "keyplayer", "kp-finder", "-k", "1", "-oper", "F",
                  "-a", "brute_force", "--max-ties", "1")

    report = (outdir / "report_barbell_keyplayer_finder_F_brute_force.tsv").read_text()

    assert "Optimal sets\t2" in report
    assert "showing 1" in report


def test_cli_keyplayer_html_offers_a_set_selector(tmp_path):
    """Carrying the ties in the data is useless if the page cannot show them."""
    outdir = _run(tmp_path, "keyplayer", "kp-finder", "-k", "1", "-oper", "F",
                  "-a", "brute_force")

    html = (outdir / "barbell_keyplayer.html").read_text(encoding="utf-8")

    assert 'id="set-select"' in html
    assert 'getElementById("set-select").addEventListener' in html


def test_cli_groupcentrality_html_offers_a_set_selector(tmp_path):
    outdir = _run(tmp_path, "groupcentrality", "gc-finder", "-k", "1",
                  "-oper", "degree", "-a", "brute_force")

    html = (outdir / "barbell_groupcentrality.html").read_text(encoding="utf-8")

    assert 'id="set-select"' in html
    assert 'getElementById("set-select").addEventListener' in html
