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
from pyntacle.utility import round_report

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
    table = pd.read_csv(io.StringIO(text[text.index("Group Centrality\t"):]), sep="\t")
    assert set(table["Group Centrality"]) <= {"A", "D"}
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


def report_header(path, first):
    line = next(l for l in path.read_text().splitlines() if l.startswith(first + "\t"))
    return line.split("\t")


@pytest.mark.parametrize("argv,report,header", [
    (["keyplayer", "kp-finder", "-a", "greedy", "--seed", "1"],
     "report_net_keyplayer_finder_all_greedy.tsv", ["Operation", "Key-player", "Score"]),
    (["keyplayer", "kp-finder", "-a", "brute_force"],
     "report_net_keyplayer_finder_all_brute_force.tsv", ["Operation", "SetID", "Key-player", "Score"]),
    (["groupcentrality", "gc-finder", "-a", "greedy", "--seed", "1"],
     "report_net_groupcentrality_finder_all_greedy.tsv", ["Operation", "Group Centrality", "Score"]),
    (["groupcentrality", "gc-finder", "-a", "gradient_descent", "--seed", "1"],
     "report_net_groupcentrality_finder_all_gradient_descent.tsv", ["Operation", "Group Centrality", "Score"]),
    (["groupcentrality", "gc-finder", "-a", "brute_force"],
     "report_net_groupcentrality_finder_all_brute_force.tsv", ["Operation", "SetID", "Group Centrality", "Score"]),
])
def test_finder_reports_share_the_info_column_names(net, tmp_path, argv, report, header):
    # finders wrote operation/score and gc greedy Groupcentrality, info Operation/Score
    proc = run(*argv[:2], "-t", "edgelist", "-i", net, "-k", "2", *argv[2:], "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert report_header(tmp_path / report, "Operation") == header


def test_global_reports_transitivity_as_global_clustering_coefficient(net, tmp_path):
    proc = run("global", "-t", "edgelist", "-i", net, "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert "Global clustering coefficient" in proc.stdout
    assert "Weighted clustering coefficient" not in proc.stdout


def test_global_report_keeps_small_values(tmp_path):
    # 3 fixed decimals printed the density of a 3000-node ring, 2/2999, as 0.001
    net = tmp_path / "ring.tsv"
    n = 3000
    net.write_text("N1\tN2\n" + "".join(f"v{i}\tv{(i + 1) % n}\n" for i in range(n)))
    proc = run("global", "-t", "edgelist", "-i", str(net), "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    report = (tmp_path / "report_ring_global.tsv").read_text()
    assert "Density\t0.000667\n" in report


def test_round_report_keeps_three_significant_digits_below_a_hundredth():
    df = pd.DataFrame({"Measure": list("abcdef"),
                       "Score": [0.00024, 36.417123, 0.0, -0.0123456, float("inf"), float("nan")],
                       "Count": [1, 2, 3, 4, 5, 6]})
    out = round_report(df)
    assert out["Score"].tolist()[:5] == [0.00024, 36.417, 0.0, -0.0123, float("inf")]
    assert pd.isna(out["Score"].iloc[5])
    assert out["Count"].tolist() == [1, 2, 3, 4, 5, 6]


@pytest.mark.parametrize("argv", [
    ["gc-finder", "-k", "2", "-a", "greedy", "--seed", "1"],
    ["gc-finder", "-k", "2", "-a", "brute_force"],
    ["gc-finder", "-k", "2", "-a", "brute_force", "-oper", "degree"],
    ["gc-finder", "-k", "2", "-a", "gradient_descent", "--seed", "1", "-oper", "closeness"],
    ["gc-info", "-n", "A,X"],
])
def test_groupcentrality_figure_highlights_the_set(net, tmp_path, argv):
    # the figure used to draw every node red, with no set marked
    proc = run("groupcentrality", argv[0], "-t", "edgelist", "-i", net, *argv[1:], "-f", "png", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    figure = next(l.split(": ", 1)[1] for l in proc.stdout.splitlines() if l.startswith("Figure: "))
    assert figure.endswith(".png") and os.path.getsize(figure) > 0


def test_plot_node_sets_draws_one_disc_per_set_holding_a_node(tmp_path, monkeypatch):
    import igraph as ig
    from pyntacle import GraphTacle as gt
    sizes = []
    real = gt.plt.scatter
    monkeypatch.setattr(gt.plt, "scatter", lambda *a, **k: (sizes.append(k.get("s")), real(*a, **k))[1])
    g = ig.Graph.Formula("A-B, B-C, C-D")
    gt.Graphtacle.plot_node_sets(g, [("degree", ["A", "B"]), ("closeness", ["B", "C"])], str(tmp_path / "f.png"))
    # base layer, then degree (A alone, B in two sets: widest disc), then closeness (B nested, C alone)
    assert [sorted(s) if hasattr(s, "__len__") else s for s in sizes] == [100, [300, 600], [300, 300]]
