"""The CSR kernels must give the same answer whatever file the network came from.

The parity suite builds its graphs in memory, so it never exercises the four
importers (``matrix``, ``edgelist``, ``sif``, ``dot``) nor the weighted/unweighted
switch that decides between the BFS and the Dijkstra kernel. This module writes
one and the same network out in every supported format and asserts that every
metric comes back identical -- and equal to the pure-Python reference.

Node identity is carried by *name*, not by index: the importers order the
vertices differently (the matrix keeps the row order of the file, the edge list
the order of first appearance), so an index-based comparison would be
meaningless. That difference is precisely what the test is here to catch.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyntacle"))

from GraphTacle import Graphtacle  # noqa: E402
from _ext.wrapper import cython_wrapper_info  # noqa: E402
from algorithms.key_player import keyplayer_kpInfo  # noqa: E402
from algorithms.group_centrality import groupcentrality_gcInfo  # noqa: E402

# One connected 8-node network, written below in every supported format.
NODES = ["A", "B", "C", "D", "E", "F", "G", "H"]
EDGES = [("A", "B", 1.0), ("A", "C", 2.0), ("B", "C", 3.0), ("B", "D", 1.0),
         ("C", "E", 2.0), ("D", "E", 4.0), ("D", "F", 1.0), ("E", "G", 2.0),
         ("F", "G", 3.0), ("G", "H", 1.0)]
K = ["B", "E"]
MDIST = 2

KP_OPERATIONS = ["F", "dF", "dR", "mreach"]
GC_OPERATIONS = ["degree", "betweenness", "closeness"]


# --------------------------------------------------------------------------
# Writers -- one per importer.
# --------------------------------------------------------------------------

def write_edgelist(path, weighted):
    with open(path, "w") as fh:
        fh.write("V1\tV2\tweight\n")
        for u, v, w in EDGES:
            fh.write(f"{u}\t{v}\t{w if weighted else 1.0}\n")


def write_sif(path, weighted):
    with open(path, "w") as fh:
        fh.write("V1\tInteraction\tV2\tweight\n")
        for u, v, w in EDGES:
            fh.write(f"{u}\tpp\t{v}\t{w if weighted else 1.0}\n")


def write_matrix(path, weighted):
    lookup = {}
    for u, v, w in EDGES:
        value = w if weighted else 1.0
        lookup[(u, v)] = value
        lookup[(v, u)] = value
    with open(path, "w") as fh:
        fh.write("\t" + "\t".join(NODES) + "\n")
        for u in NODES:
            row = [str(lookup.get((u, v), 0.0)) for v in NODES]
            fh.write(u + "\t" + "\t".join(row) + "\n")


def write_dot(path, weighted):
    with open(path, "w") as fh:
        fh.write("graph G {\n")
        for node in NODES:
            fh.write(f"    {node};\n")
        for u, v, w in EDGES:
            fh.write(f"    {u} -- {v} [weight={w if weighted else 1.0}];\n")
        fh.write("}\n")


WRITERS = {
    "edgelist": write_edgelist,
    "sif": write_sif,
    "matrix": write_matrix,
    "dot": write_dot,
}


def has_pygraphviz():
    try:
        import pygraphviz  # noqa: F401
        return True
    except ImportError:
        return False


ALL_FORMATS = [
    pytest.param(fmt, marks=pytest.mark.skipif(fmt == "dot" and not has_pygraphviz(),
                                               reason="pygraphviz not installed"))
    for fmt in WRITERS
]


def load(tmp_path, fmt, weighted):
    path = os.path.join(str(tmp_path), f"net_{fmt}_{'w' if weighted else 'u'}")
    WRITERS[fmt](path, weighted)
    return Graphtacle.from_file(path, "keyplayer", fmt, sep="\t", header=True,
                                directed=False, weight=weighted)


def cython_scores(graph):
    scores = {}
    for oper in KP_OPERATIONS:
        scores[oper] = cython_wrapper_info(graph, K, oper, distance_type="min",
                                           mdist=MDIST, n_threads=1)
    for oper in GC_OPERATIONS:
        scores[oper] = cython_wrapper_info(graph, K, oper, distance_type="min",
                                           mdist=-1, n_threads=1)
    return scores


def python_scores(graph):
    scores = {oper: keyplayer_kpInfo(graph, K, oper, mdist=MDIST) for oper in KP_OPERATIONS}
    for oper in GC_OPERATIONS:
        scores[oper] = groupcentrality_gcInfo(graph, K, oper, distance_type="min")
    return scores


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

@pytest.mark.parametrize("weighted", [False, True], ids=["unweighted", "weighted"])
@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_graph_survives_the_round_trip_through_every_importer(tmp_path, fmt, weighted):
    """Same topology in, same topology out: the importers must not add or drop edges."""
    graph = load(tmp_path, fmt, weighted)

    assert sorted(graph.vs["name"]) == sorted(NODES)
    assert graph.ecount() == len(EDGES)

    edges_by_name = {frozenset((graph.vs[e.source]["name"], graph.vs[e.target]["name"]))
                     for e in graph.es}
    assert edges_by_name == {frozenset((u, v)) for u, v, _ in EDGES}

    if weighted:
        loaded = {frozenset((graph.vs[e.source]["name"], graph.vs[e.target]["name"])): e["weight"]
                  for e in graph.es}
        for u, v, w in EDGES:
            assert loaded[frozenset((u, v))] == pytest.approx(w)


@pytest.mark.parametrize("weighted", [False, True], ids=["unweighted", "weighted"])
@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_cython_scores_do_not_depend_on_the_input_format(tmp_path, fmt, weighted):
    """The CSR kernels see a vertex order that varies per importer; scores must not."""
    reference = cython_scores(load(tmp_path, "edgelist", weighted))
    got = cython_scores(load(tmp_path, fmt, weighted))

    for oper in reference:
        assert got[oper] == pytest.approx(reference[oper], abs=1e-3), (
            f"{oper} differs between edgelist and {fmt} "
            f"({'weighted' if weighted else 'unweighted'})")


@pytest.mark.parametrize("weighted", [False, True], ids=["unweighted", "weighted"])
@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_engines_agree_on_files_loaded_from_disk(tmp_path, fmt, weighted):
    """Parity between the compiled kernels and the Python reference, from real files."""
    graph = load(tmp_path, fmt, weighted)
    fast = cython_scores(graph)
    slow = python_scores(graph)

    for oper in fast:
        assert fast[oper] == pytest.approx(slow[oper], abs=1e-3), (
            f"{oper}: cython={fast[oper]} python={slow[oper]} "
            f"[{fmt}, {'weighted' if weighted else 'unweighted'}]")


@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_weighting_actually_changes_the_distance_based_metrics(tmp_path, fmt):
    """Guards against the weights being silently dropped on the way to the kernels.

    With every weight equal to 1 the engine takes the BFS path and with mixed
    weights the Dijkstra one; if a loader lost the weights the two would agree.
    dF and dR are distance-based, so they have to move.
    """
    unweighted = cython_scores(load(tmp_path, fmt, False))
    weighted = cython_scores(load(tmp_path, fmt, True))

    assert unweighted["dF"] != pytest.approx(weighted["dF"], abs=1e-3)
    assert unweighted["dR"] != pytest.approx(weighted["dR"], abs=1e-3)


@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_unit_weights_reproduce_the_unweighted_result(tmp_path, fmt):
    """A file whose weights are all 1.0 must score exactly like an unweighted one.

    This is the BFS/Dijkstra switch: `_adjacency()` flags the graph as unweighted
    only when every weight is 1, and the two kernels have to agree on that input.
    """
    parsed_as_weighted = cython_scores(load(tmp_path, fmt, False))

    path = os.path.join(str(tmp_path), f"unit_{fmt}")
    WRITERS[fmt](path, False)
    unit = Graphtacle.from_file(path, "keyplayer", fmt, sep="\t", header=True,
                                directed=False, weight=True)
    scores = cython_scores(unit)

    for oper in scores:
        assert scores[oper] == pytest.approx(parsed_as_weighted[oper], abs=1e-3), oper
