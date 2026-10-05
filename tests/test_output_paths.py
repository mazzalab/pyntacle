"""Commands that write a network back out (set, extract, convert, generate).

Every file goes to -o and nothing to the working directory; the network is
written in the input format; a bad request stops with a one-line error, not a
traceback.
"""
import os
import subprocess
import sys

import pandas as pd
import pytest

from conftest import PKG_DIR

PYTHON = sys.executable
MAIN = os.path.join(PKG_DIR, "main.py")

FIRST = "N1\tN2\tWeight\nA\tB\t0.5\nB\tC\t0.25\nC\tA\t2\nX\tY\t1\nY\tZ\t1\n"
SECOND = "N1\tN2\tWeight\nA\tB\t9\nC\tD\t3\n"


def run(tmp_path, *argv):
    cwd = tmp_path / "cwd"
    out = tmp_path / "out"
    cwd.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)
    proc = subprocess.run([PYTHON, MAIN, *argv, "-o", str(out)], capture_output=True, text=True, cwd=cwd)
    return proc, out, sorted(os.listdir(cwd))


@pytest.fixture
def files(tmp_path):
    first, second = tmp_path / "first.tsv", tmp_path / "second.tsv"
    first.write_text(FIRST)
    second.write_text(SECOND)
    return str(first), str(second)


def read_edges(path):
    # an edge list whose weights are all 1 is written without a weight column
    df = pd.read_csv(path, sep="\t")
    return {tuple(sorted(r[:2])): (r[2] if len(r) > 2 else 1.0) for r in df.itertuples(index=False)}


@pytest.mark.parametrize("operation,edges", [
    ("union", {("A", "B"): 0.5, ("B", "C"): 0.25, ("A", "C"): 2.0, ("X", "Y"): 1.0, ("Y", "Z"): 1.0,
               ("C", "D"): 3.0}),
    ("intersection", {("A", "B"): 0.5}),
    ("difference", {("B", "C"): 0.25, ("A", "C"): 2.0, ("X", "Y"): 1.0, ("Y", "Z"): 1.0}),
])
def test_set_writes_the_weighted_result_into_the_output_directory(tmp_path, files, operation, edges):
    proc, out, leaked = run(tmp_path, "set", operation, "-t", "edgelist", "-i", files[0],
                            "-i2", files[1], "-w", "--no-plot")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert leaked == []
    network = out / f"first_{operation}_second.tsv"
    assert read_edges(network) == edges
    assert (out / f"report_first_{operation}_second_set.tsv").exists()


def test_union_keeps_every_component(tmp_path, files):
    proc, out, _ = run(tmp_path, "set", "union", "-t", "edgelist", "-i", files[0], "-i2", files[1], "--no-plot")
    assert proc.returncode == 0, proc.stderr
    assert "2 component(s)" in proc.stdout


def test_an_empty_set_result_is_a_clean_error(tmp_path, files):
    proc, out, leaked = run(tmp_path, "set", "difference", "-t", "edgelist", "-i", files[0],
                            "-i2", files[0], "--no-plot")
    assert proc.returncode == 1
    assert "ERROR: the difference of the two networks has no edges" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert leaked == [] and os.listdir(out) == []


@pytest.mark.parametrize("flags,name,nodes", [
    (["-l"], "largest_component", {"A", "B", "C"}),
    (["-sc", "2"], "selected_subgraph", {"X", "Y", "Z"}),
    (["-l", "-n", "2"], "largest_subgraphs", {"A", "B", "C", "X", "Y", "Z"}),
    (["-n", "1"], "removed_subgraphs", {"A", "B", "C"}),
    (["-nl", "Z"], "selected_by_nodes", {"X", "Y", "Z"}),
])
def test_extract_writes_into_the_output_directory(tmp_path, files, flags, name, nodes):
    proc, out, leaked = run(tmp_path, "extract", "-t", "edgelist", "-i", files[0], "-w", *flags, "--no-plot")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert leaked == []
    edges = read_edges(out / f"first_extract_{name}.tsv")
    assert {v for e in edges for v in e} == nodes


@pytest.mark.parametrize("flags,message", [
    (["-sc", "3"], "-sc must be between 1 and 2"),
    (["-nl", "Q"], "nodes not in the network: Q"),
])
def test_extract_rejects_a_bad_request_without_a_traceback(tmp_path, files, flags, message):
    proc, _, _ = run(tmp_path, "extract", "-t", "edgelist", "-i", files[0], *flags, "--no-plot")
    assert proc.returncode == 1
    assert message in proc.stderr
    assert "Traceback" not in proc.stderr


def test_convert_writes_into_the_output_directory(tmp_path, files):
    proc, out, leaked = run(tmp_path, "convert", "-t", "edgelist", "-i", files[0], "-w", "-to", "sif",
                            "-fo", "converted")
    assert proc.returncode == 0, proc.stderr
    assert leaked == []
    assert "Network file:" in proc.stdout
    assert (out / "converted.sif").exists()


@pytest.mark.parametrize("argv,name", [
    (["erdos-renyi", "-n", "20", "-e", "30"], "erdos_renyi_n20_e30.tsv"),
    (["tree", "-n", "15", "-c", "2"], "tree_n15_e14.tsv"),
    (["barabasi", "-n", "30", "-a", "2"], None),
    (["watts-strogatz", "-s", "20", "-nei", "2", "-p", "0.1"], "watts_strogatz_n20_e40.tsv"),
    (["lattice", "-dim", "4,4"], "lattice_n16_e24.tsv"),
])
def test_generate_names_its_file_and_writes_into_the_output_directory(tmp_path, argv, name):
    proc, out, leaked = run(tmp_path, "generate", *argv, "-t", "edgelist")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert leaked == []
    written = os.listdir(out)
    assert len(written) == 1
    if name:
        assert written == [name]


def test_watts_strogatz_rewires_with_a_fractional_probability(tmp_path):
    # with -p truncated to 0 the ring lattice would come back unchanged
    proc, out, _ = run(tmp_path, "generate", "watts-strogatz", "-s", "200", "-nei", "2", "-p", "0.5",
                       "-t", "edgelist")
    assert proc.returncode == 0, proc.stderr
    df = pd.read_csv(out / "watts_strogatz_n200_e400.tsv", sep="\t")
    ring = {tuple(sorted((i, (i + d) % 200))) for i in range(200) for d in (1, 2)}
    edges = {tuple(sorted((int(a[1:]) - 1, int(b[1:]) - 1))) for a, b in zip(df.V1, df.V2)}
    assert len(edges - ring) > 50


def test_generate_without_its_required_flags_is_a_clean_error(tmp_path):
    proc, _, _ = run(tmp_path, "generate", "tree", "-n", "10", "-t", "edgelist")
    assert proc.returncode == 1
    assert "ERROR: generate tree needs -c" in proc.stderr


def test_writing_commands_refuse_directed_input(tmp_path, files):
    proc, _, _ = run(tmp_path, "extract", "-t", "edgelist", "-i", files[0], "-l", "-d")
    assert proc.returncode == 1
    assert "writes undirected networks only" in proc.stderr
