"""Awkward but legitimate input files, end to end through the CSR kernels.

test_input_formats.py covers the happy path (one clean network in four formats).
This module covers what real files actually look like: no header row, a comma
separator, isolated vertices, a disconnected network, self-loops and duplicated
rows -- plus the inputs that must be *refused* rather than silently mangled.
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "pyntacle"))

from GraphTacle import Graphtacle  # noqa: E402
from _ext.wrapper import cython_wrapper_info  # noqa: E402
from algorithms.key_player import keyplayer_kpInfo  # noqa: E402


def write(tmp_path, name, text):
    path = os.path.join(str(tmp_path), name)
    with open(path, "w") as fh:
        fh.write(text)
    return path


def score(graph, K, oper="dF", mdist=2):
    return cython_wrapper_info(graph, K, oper, distance_type="min", mdist=mdist, n_threads=1)


# --------------------------------------------------------------------------
# Files that must load and score correctly
# --------------------------------------------------------------------------

def test_edgelist_without_header(tmp_path):
    """header=False names the columns V1/V2/weight internally; the graph must still build."""
    path = write(tmp_path, "noheader.txt", "A\tB\t1.0\nB\tC\t2.0\nC\tD\t1.0\n")
    graph = Graphtacle.from_file(path, "keyplayer", "edgelist", sep="\t", header=False,
                                 directed=False, weight=True)

    assert sorted(graph.vs["name"]) == ["A", "B", "C", "D"]
    assert graph.ecount() == 3
    assert score(graph, ["B"]) == pytest.approx(
        keyplayer_kpInfo(graph, ["B"], "dF", mdist=2), abs=1e-3)


def test_comma_separated_edgelist(tmp_path):
    """A CSV is as common as a TSV; sep is a user-supplied flag, not an assumption."""
    path = write(tmp_path, "commas.csv", "V1,V2,weight\nA,B,1.0\nB,C,2.0\nC,D,1.0\n")
    graph = Graphtacle.from_file(path, "keyplayer", "edgelist", sep=",", header=True,
                                 directed=False, weight=True)

    assert graph.ecount() == 3
    assert sorted(graph.vs["name"]) == ["A", "B", "C", "D"]


def test_unweighted_edgelist_has_only_two_columns(tmp_path):
    """The two-column case takes a different branch in import_edgeList."""
    path = write(tmp_path, "twocol.txt", "V1\tV2\nA\tB\nB\tC\nC\tD\n")
    graph = Graphtacle.from_file(path, "keyplayer", "edgelist", sep="\t", header=True,
                                 directed=False, weight=False)

    assert graph.ecount() == 3
    assert score(graph, ["B"]) == pytest.approx(
        keyplayer_kpInfo(graph, ["B"], "dF", mdist=2), abs=1e-3)


def test_matrix_with_an_isolated_vertex(tmp_path):
    """An all-zero row is a real vertex; dropping it would shift every index.

    The adjacency matrix is the only format that can express an isolated vertex,
    and the CSR builder has to give it an empty neighbour range rather than
    skipping it.
    """
    path = write(tmp_path, "isolate.mat",
                 "\tA\tB\tC\tD\n"
                 "A\t0\t1\t1\t0\n"
                 "B\t1\t0\t1\t0\n"
                 "C\t1\t1\t0\t0\n"
                 "D\t0\t0\t0\t0\n")
    graph = Graphtacle.from_file(path, "keyplayer", "matrix", sep="\t", header=True,
                                 directed=False, weight=False)

    assert graph.vcount() == 4, "the isolated vertex D must survive the import"
    assert graph.ecount() == 3
    assert score(graph, ["A"]) == pytest.approx(
        keyplayer_kpInfo(graph, ["A"], "dF", mdist=2), abs=1e-3)


def test_disconnected_network_from_file(tmp_path):
    """Two components: the flood-fill in F and the infinite distances in dF."""
    path = write(tmp_path, "disc.txt",
                 "V1\tV2\nA\tB\nB\tC\nC\tA\nD\tE\nE\tF\n")
    graph = Graphtacle.from_file(path, "keyplayer", "edgelist", sep="\t", header=True,
                                 directed=False, weight=False)

    assert not graph.is_connected()
    for oper in ["F", "dF", "dR", "mreach"]:
        fast = score(graph, ["B"], oper)
        slow = keyplayer_kpInfo(graph, ["B"], oper, mdist=2)
        assert fast == pytest.approx(slow, abs=1e-3), oper


def test_self_loops_are_collapsed_not_left_on_the_diagonal(tmp_path):
    """A self-loop lands on the adjacency diagonal and the kernels would read it as an edge."""
    path = write(tmp_path, "loops.txt",
                 "V1\tV2\nA\tA\nA\tB\nB\tC\nC\tD\n")
    graph = Graphtacle.from_file(path, "keyplayer", "edgelist", sep="\t", header=True,
                                 directed=False, weight=False)

    assert not any(e.source == e.target for e in graph.es), "self-loop survived the import"
    assert graph.ecount() == 3
    assert score(graph, ["B"]) == pytest.approx(
        keyplayer_kpInfo(graph, ["B"], "dF", mdist=2), abs=1e-3)


def test_duplicated_rows_are_collapsed_to_one_edge(tmp_path):
    """A repeated row would make the adjacency cell read as a weight of 2."""
    path = write(tmp_path, "dupes.txt",
                 "V1\tV2\nA\tB\nA\tB\nB\tC\nC\tD\n")
    graph = Graphtacle.from_file(path, "keyplayer", "edgelist", sep="\t", header=True,
                                 directed=False, weight=False)

    assert graph.ecount() == 3, "parallel edge survived the import"
    assert score(graph, ["B"]) == pytest.approx(
        keyplayer_kpInfo(graph, ["B"], "dF", mdist=2), abs=1e-3)


# --------------------------------------------------------------------------
# Files that must be refused
# --------------------------------------------------------------------------

def test_zero_weight_edge_is_refused(tmp_path):
    """0 means "no edge" in the adjacency view, so a 0-weight edge is ambiguous."""
    path = write(tmp_path, "zero.txt",
                 "V1\tV2\tweight\nA\tB\t1.0\nB\tC\t0.0\nC\tD\t1.0\n")
    with pytest.raises(ValueError, match="(?i)weight"):
        Graphtacle.from_file(path, "keyplayer", "edgelist", sep="\t", header=True,
                             directed=False, weight=True)


def test_unknown_file_type_is_refused(tmp_path):
    path = write(tmp_path, "x.txt", "A\tB\n")
    with pytest.raises(TypeError):
        Graphtacle.from_file(path, "keyplayer", "graphml", sep="\t", header=True)


def test_directed_file_gives_a_python_error_not_a_core_dump(tmp_path):
    """Runs out of process: the failure mode being guarded against killed the runner."""
    path = write(tmp_path, "dir.txt", "V1\tV2\nA\tB\nB\tC\nC\tD\n")
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from GraphTacle import Graphtacle\n"
        "from _ext.wrapper import cython_wrapper_info\n"
        "g = Graphtacle.from_file(%r, 'keyplayer', 'edgelist', sep='\\t', header=True, directed=True)\n"
        "try:\n"
        "    cython_wrapper_info(g, ['B'], 'dF', distance_type='min', mdist=2, n_threads=1)\n"
        "except ValueError:\n"
        "    print('VALUEERROR')\n"
    ) % (os.path.join(REPO_ROOT, "pyntacle"), path)

    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)

    assert result.returncode == 0, f"process died with {result.returncode}: {result.stderr[-500:]}"
    assert "VALUEERROR" in result.stdout
