"""Flags with a bad value stop with a one-line error; the runs they guard work.

Each case here was a traceback, a crash or a silently wrong run before:
numeric flags were read as strings or not range-checked, an input in the
working directory sent the HTML report to the filesystem root, and
gradient_descent ran to its time limit on any network.
"""
import io
import os
import shutil
import subprocess
import sys
import time

import pandas as pd
import pytest

from conftest import PKG_DIR

PYTHON = sys.executable
MAIN = os.path.join(PKG_DIR, "main.py")

# two components: a chain of three triangles (A..I) and a path X-Y-Z
NET = ("N1\tN2\nA\tB\nB\tC\nC\tA\nC\tD\nD\tE\nE\tF\nF\tD\nF\tG\nG\tH\nH\tI\nI\tG\n"
       "X\tY\nY\tZ\n")


@pytest.fixture
def net(tmp_path):
    path = tmp_path / "net.tsv"
    path.write_text(NET)
    return str(path)


def run(*argv, cwd=None):
    return subprocess.run([PYTHON, MAIN, *argv], capture_output=True, text=True, cwd=cwd)


def clean_error(proc, message):
    assert proc.returncode != 0
    assert message in proc.stderr, proc.stderr
    assert "Traceback" not in proc.stderr


@pytest.mark.parametrize("argv,message", [
    (["keyplayer", "kp-finder", "-k", "0"], "-k/--k_size: '0' is not a positive integer"),
    (["keyplayer", "kp-finder", "-k", "abc"], "-k/--k_size: 'abc' is not a positive integer"),
    (["keyplayer", "kp-finder", "-np", "0"], "-np/--nprocs: '0' is not a positive integer"),
    (["keyplayer", "kp-finder", "-m", "0"], "-m/--mdist: '0' is not a positive integer"),
    (["local", "-f", "jpg"], "argument -f/--format: invalid choice: 'jpg'"),
    (["communities", "fastgreedy", "-n", "abc"], "-n/--minNodes: 'abc' is not a positive integer"),
    (["communities", "percolation", "-k", "1"], "-k/--communitySize: '1' is not an integer of at least 2"),
    (["percolation", "-P", "2"], "-P/--PrInf: '2' is not a number between 0 and 1"),
    (["percolation", "-tau", "abc"], "-tau/--tau: 'abc' is not a positive number"),
    (["extract", "-n", "-1"], "-n/--ncomponents: '-1' is not a positive integer"),
    (["keyplayer", "kp-finder", "--seed", "-1"], "--seed: '-1' is not an integer between 0 and 2**32 - 1"),
    (["percolation", "--seed", "-1"], "--seed: '-1' is not an integer between 0 and 2**32 - 1"),
])
def test_a_bad_flag_value_is_refused_by_the_parser(net, tmp_path, argv, message):
    proc = run(argv[0], "-t", "edgelist", "-i", net, *argv[1:], "-o", str(tmp_path / "out"))
    clean_error(proc, message)


@pytest.mark.parametrize("argv,message", [
    (["keyplayer", "kp-finder", "-k", "12"], "ERROR: -k must be smaller than the number of nodes (12)"),
    (["communities", "fastgreedy", "-nc", "50"], "ERROR: -nc must be at most the number of nodes (12)"),
    (["communities", "fastgreedy", "-n", "50"], "ERROR: no community passes the size filters"),
    (["percolation", "-n", "Q"], "ERROR: Seed node 'Q' not found"),
    (["local", "-c", "red"], "ERROR: -c names nodes not in the network: red"),
])
def test_a_request_the_network_cannot_meet_is_a_clean_error(net, tmp_path, argv, message):
    proc = run(argv[0], "-t", "edgelist", "-i", net, *argv[1:], "-o", str(tmp_path / "out"))
    clean_error(proc, message)


def test_generate_refuses_more_edges_than_the_network_holds(tmp_path):
    proc = run("generate", "erdos-renyi", "-t", "edgelist", "-n", "5", "-e", "400", "-o", str(tmp_path))
    clean_error(proc, "ERROR: -e is at most 10 for 5 nodes")


def test_an_input_in_the_working_directory_writes_next_to_it(tmp_path):
    # outdir was "" here and the HTML report went to "/net_local.html"
    shutil.copy(os.path.join(os.path.dirname(__file__), "..", "examples", "figure_8.egl"), tmp_path / "net.egl")
    proc = run("local", "-t", "edgelist", "-i", "net.egl", cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert {"report_net_local.tsv", "net_local.html", "net_local.svg"} <= set(os.listdir(tmp_path))


def test_every_written_file_is_named_on_screen(net, tmp_path):
    out = tmp_path / "out"
    proc = run("keyplayer", "kp-finder", "-t", "edgelist", "-i", net, "-k", "2", "-o", str(out))
    assert proc.returncode == 0, proc.stderr
    named = {line.split(": ", 1)[1] for line in proc.stdout.splitlines()
             if line.split(": ", 1)[0] in ("Report", "HTML report", "Figure")}
    assert named == {str(out / f) for f in os.listdir(out)}


def test_gradient_descent_stops_at_a_local_optimum(net, tmp_path):
    # it used to run every operation to the -ms limit (4 x 120 s on any network)
    start = time.time()
    proc = run("keyplayer", "kp-finder", "-t", "edgelist", "-i", net, "-k", "2", "-a", "gradient_descent",
               "--seed", "1", "-ms", "60", "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert time.time() - start < 30


def test_community_filters_apply_to_the_report(tmp_path):
    # they used to drop communities from the figures only
    path = tmp_path / "net.tsv"
    path.write_text(NET + "P\tQ\n")
    proc = run("communities", "fastgreedy", "-t", "edgelist", "-i", str(path), "-n", "3", "--no-plot",
               "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert "Communities: 5 found, 4 kept by the filters" in proc.stdout
    text = (tmp_path / "report_net_communities.tsv").read_text()
    table = pd.read_csv(io.StringIO(text[text.index("Node\tCommunity"):]), sep="\t")
    assert "P" not in set(table["Node"]) and len(table) == 12
    assert sorted(table["Community"].unique()) == [1, 2, 3, 4]


def test_convert_writes_into_folders_named_in_the_output_name(net, tmp_path):
    proc = run("convert", "-t", "edgelist", "-i", net, "-to", "sif", "-fo", "sub/dir/net", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "sub" / "dir" / "net.sif").exists()


def test_global_average_path_length_is_finite_on_a_split_network(net, tmp_path):
    proc = run("global", "-t", "edgelist", "-i", net, "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    line = next(l for l in proc.stdout.splitlines() if "Average shortest path length" in l)
    assert float(line.split()[-1]) < float("inf")


def test_clique_percolation_reports_node_names(net, tmp_path):
    # the report listed vertex indices (0, 1, ...) instead of the names
    proc = run("communities", "percolation", "-t", "edgelist", "-i", net, "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    text = (tmp_path / "report_net_communities.tsv").read_text()
    table = pd.read_csv(io.StringIO(text[text.index("Node\tCommunity"):]), sep="\t")
    assert set(table["Node"]) == set("ABCDEFGHI")


@pytest.mark.parametrize("engine", ["cython", "python"])
def test_group_closeness_ranks_a_hub_above_an_isolated_pair(tmp_path, engine):
    # a set inside a small component used to score highest: unreachable nodes
    # counted in the numerator but not in the distances
    path = tmp_path / "split.tsv"
    path.write_text("N1\tN2\nA\tB\nB\tC\nC\tD\nD\tE\nE\tF\nF\tA\nA\tD\nX\tY\n")
    proc = run("groupcentrality", "gc-finder", "-t", "edgelist", "-i", str(path), "-k", "1", "-a", "greedy",
               "-oper", "closeness", "--engine", engine, "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    text = (tmp_path / "report_split_groupcentrality_finder_closeness_greedy.tsv").read_text()
    table = pd.read_csv(io.StringIO(text[text.index("Groupcentrality\t"):]), sep="\t")
    assert set(table["Groupcentrality"]) <= {"A", "D"}
    # 5 of the 7 other nodes reached, at distances 1,1,1,2,2: (5/7) * (5/7)
    assert table["closeness"].iloc[0] == pytest.approx(25 / 49, abs=1e-3)


def percolation_report(net, out, *seed):
    proc = run("percolation", "-t", "edgelist", "-i", net, *seed, "--no-plot", "-o", str(out))
    assert proc.returncode == 0, proc.stderr
    return proc.stdout, (out / "report_net_percolation.tsv").read_text()


def test_percolation_repeats_with_the_printed_seed(net, tmp_path):
    stdout, first = percolation_report(net, tmp_path / "a")
    seed = next(l for l in stdout.splitlines() if l.startswith("Random seed: ")).split()[-1]
    assert percolation_report(net, tmp_path / "b", "--seed", seed)[1] == first
    assert percolation_report(net, tmp_path / "c", "--seed", seed)[1] == first
