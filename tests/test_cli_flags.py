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
    (["keyplayer", "kp-finder", "-k", "12"], "ERROR: -k is at most 10 here: the set must leave at least 2 of the 12 nodes outside it"),
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


def test_round_report_keeps_three_significant_digits_below_a_tenth():
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


def report_table(path):
    """The data table of a report: the lines after its last blank line."""
    return pd.read_csv(io.StringIO(open(path).read().rstrip("\n").split("\n\n")[-1]), sep="\t")


def report_path(proc):
    return next(l.split(": ", 1)[1] for l in proc.stdout.splitlines() if l.startswith("Report: "))


def test_brute_force_group_closeness_honours_the_distance_type(tmp_path):
    # brute force used to score every -v as min
    fig8 = os.path.join(os.path.dirname(PKG_DIR), "examples", "figure_8.egl")
    scores = {}
    for v in ["min", "max"]:
        for algo in ["brute_force", "greedy"]:
            proc = run("groupcentrality", "gc-finder", "-t", "edgelist", "-i", fig8, "-k", "2", "-a", algo,
                       "-oper", "closeness", "-v", v, "--seed", "4", "--no-plot", "-o", str(tmp_path / f"{v}{algo}"))
            assert proc.returncode == 0, proc.stderr
            scores[v, algo] = report_table(report_path(proc))["closeness"].max()
    assert scores["max", "brute_force"] < scores["min", "brute_force"]
    assert scores["max", "brute_force"] >= scores["max", "greedy"]


@pytest.mark.parametrize("command", [["keyplayer", "kp-finder", "-oper", "F"],
                                     ["groupcentrality", "gc-finder", "-oper", "betweenness"]])
@pytest.mark.parametrize("algo", ["greedy", "gradient_descent"])
def test_python_engine_search_repeats_with_the_seed(tmp_path, command, algo):
    # the swaps were tried in set order, which changes with the hash seed of each run
    fig8 = os.path.join(os.path.dirname(PKG_DIR), "examples", "figure_8.egl")
    found = set()
    for h in ["1", "2", "3", "4"]:
        out = tmp_path / h
        proc = subprocess.run([PYTHON, MAIN, *command[:2], "-t", "edgelist", "-i", fig8, "-k", "3", "-a", algo,
                               *command[2:], "--engine", "python", "--seed", "7", "--no-plot", "-o", str(out)],
                              capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": h})
        assert proc.returncode == 0, proc.stderr
        found.add(open(report_path(proc)).read().split("\n\n")[-1])
    assert len(found) == 1, found


def test_gradient_descent_scores_with_the_given_scorer():
    import igraph as ig
    from conftest import make_graphtacle
    from pyntacle.algorithms.stochastic_gradient_descent import call_stochastic_gradient_descent
    calls = []
    g = make_graphtacle(ig.Graph.Famous("Zachary"))
    call_stochastic_gradient_descent(g, 2, "dR", mdist=2, seed=1, maxsec=5,
                                     scorer=lambda names, oper: calls.append(oper) or len(set(names) & {"0"}))
    assert calls and set(calls) == {"dR"}


NUMERIC = "N1\tN2\n1\t2\n2\t3\n3\t4\n4\t1\n4\t5\n0\t5\n"


@pytest.mark.parametrize("argv", [
    ["keyplayer", "kp-info", "-n", "0,1"],
    ["groupcentrality", "gc-info", "-n", "0,1"],
    ["local", "-r", "0", "-c", "1"],
    ["extract", "-nl", "0"],
    ["percolation", "-n", "0", "--snapshotNode", "1", "--seed", "1"],
])
def test_numeric_node_names_are_found_by_name(tmp_path, argv):
    # names like 0, 1 were read as numbers and -n "0,1" then matched nothing
    path = tmp_path / "numeric.tsv"
    path.write_text(NUMERIC)
    proc = run(argv[0], "-t", "edgelist", "-i", str(path), *argv[1:], "--no-plot", "-o", str(tmp_path / "out"))
    assert proc.returncode == 0, proc.stderr


def test_unweighted_matrix_reads_any_non_zero_cell_as_one_edge(tmp_path):
    # a cell of 2 used to become two parallel edges, which crashed local
    path = tmp_path / "m.txt"
    path.write_text("\tA\tB\tC\nA\t1\t2\t0\nB\t2\t0\t3\nC\t0\t3\t0\n")
    proc = run("local", "-t", "matrix", "-i", str(path), "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert "self-loop" in proc.stdout
    assert report_table(report_path(proc))["Degree"].tolist() == [1, 2, 1]


def test_asymmetric_matrix_needs_directed(tmp_path):
    path = tmp_path / "m.txt"
    path.write_text("\tA\tB\nA\t0\t1\nB\t0\t0\n")
    clean_error(run("local", "-t", "matrix", "-i", str(path), "-o", str(tmp_path)),
                "the matrix is not symmetric")


def test_a_network_without_edges_is_refused(tmp_path):
    path = tmp_path / "m.txt"
    path.write_text("\tA\tB\tC\nA\t0\t0\t0\nB\t0\t0\t0\nC\t0\t0\t0\n")
    clean_error(run("global", "-t", "matrix", "-i", str(path), "-o", str(tmp_path)),
                "ERROR: the network has no edges")


@pytest.mark.parametrize("command", [["keyplayer", "kp-info"], ["groupcentrality", "gc-info"]])
def test_info_set_must_leave_two_nodes_out(net, tmp_path, command):
    proc = run(*command, "-t", "edgelist", "-i", net, "-n", "A,B,C,D,E,F,G,H,I,X,Y", "-o", str(tmp_path))
    clean_error(proc, "the node set must leave at least 2 of the 12 nodes outside it")


def test_repeated_node_is_counted_once(net, tmp_path):
    proc = run("groupcentrality", "gc-info", "-t", "edgelist", "-i", net, "-n", "A, A,B", "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert set(report_table(report_path(proc))["Node-set"]) == {"['A', 'B']"}


def test_union_of_two_files_with_the_same_name(net, tmp_path):
    other = tmp_path / "b"
    other.mkdir()
    shutil.copy(net, other / "net.tsv")
    proc = run("set", "union", "-t", "edgelist", "-i", net, "-i2", str(other / "net.tsv"), "-f", "png",
               "-o", str(tmp_path / "out"))
    assert proc.returncode == 0, proc.stderr


def test_convert_keeps_every_digit_of_the_weights(tmp_path):
    path = tmp_path / "w.tsv"
    path.write_text("V1\tV2\tw\nA\tB\t0.123456789\nB\tC\t1e-05\n")
    for to in ["edgelist", "matrix", "sif", "dot"]:
        proc = run("convert", "-t", "edgelist", "-i", str(path), "-w", "-to", to, "-fo", f"c_{to}", "-o", str(tmp_path))
        assert proc.returncode == 0, proc.stderr
        text = open(next(l.split(": ", 1)[1] for l in proc.stdout.splitlines() if l.startswith("Network file: "))).read()
        assert "0.123456789" in text and "1e-05" in text, (to, text)


def test_convert_warns_when_isolated_nodes_cannot_be_written(tmp_path):
    path = tmp_path / "m.txt"
    path.write_text("\tA\tB\tZ\nA\t0\t1\t0\nB\t1\t0\t0\nZ\t0\t0\t0\n")
    proc = run("convert", "-t", "matrix", "-i", str(path), "-to", "sif", "-fo", "c", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert "cannot be written as sif and are left out (Z)" in proc.stdout


def test_snapshot_node_not_in_the_network_is_a_clean_error(net, tmp_path):
    clean_error(run("percolation", "-t", "edgelist", "-i", net, "--snapshotNode", "Q", "-o", str(tmp_path)),
                "--snapshotNode Q is neither a node name nor a node index (0 to 11)")


def test_clique_percolation_without_cliques_is_a_clean_error(tmp_path):
    path = tmp_path / "star.tsv"
    path.write_text("N1\tN2\nH\tA\nH\tB\nH\tC\n")
    clean_error(run("communities", "percolation", "-t", "edgelist", "-i", str(path), "-o", str(tmp_path)),
                "the network has no 3-clique")


def test_round_report_writes_no_negative_zero():
    assert str(round_report(pd.DataFrame({"x": [-0.0, 1.5]}))["x"].tolist()) == "[0.0, 1.5]"


def test_weighted_topological_importance_survives_an_isolated_node(tmp_path):
    # the isolated node's 0/0 made every weighted value NaN
    path = tmp_path / "m.txt"
    path.write_text("\tA\tB\tC\tZ\nA\t0\t2\t1\t0\nB\t2\t0\t1\t0\nC\t1\t1\t0\t0\nZ\t0\t0\t0\t0\n")
    proc = run("mesoscale", "-t", "matrix", "-i", str(path), "-w", "-k", "2", "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    weighted = open(report_path(proc)).read().split("Weighted Topological Importance\n")[1].split("\n\n")[0]
    assert "nan" not in weighted.lower() and "\t\t" not in weighted


def test_group_betweenness_of_a_star_centre_is_one(tmp_path):
    # every shortest path between two leaves crosses the centre; 1.3.2 reported 0.5
    path = tmp_path / "star.tsv"
    path.write_text("N1\tN2\nH\tA\nH\tB\nH\tC\nH\tD\n")
    for engine in ["cython", "python"]:
        proc = run("groupcentrality", "gc-finder", "-t", "edgelist", "-i", str(path), "-k", "1", "-a", "greedy",
                   "-oper", "betweenness", "--engine", engine, "--seed", "1", "--no-plot", "-o", str(tmp_path / engine))
        assert proc.returncode == 0, proc.stderr
        table = report_table(report_path(proc))
        assert table["Group Centrality"].tolist() == ["H"] and table["betweenness"].tolist() == [1.0]


def test_split_network_radiality_counts_only_the_nodes_reached(tmp_path):
    # unreachable nodes counted as distance 0, so a 2-node component outscored the hub
    path = tmp_path / "split.tsv"
    path.write_text("N1\tN2\nA\tB\nB\tC\nC\tA\nC\tD\nX\tY\n")
    proc = run("local", "-t", "edgelist", "-i", str(path), "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    radiality = dict(zip(*report_table(report_path(proc))[["Node Name", "Radiality"]].T.values))
    # diameter 2: A reaches B, C at 1 and D at 2 -> (3 * 3 - 4) / 5; X reaches Y at 1 -> (3 - 1) / 5
    assert radiality["A"] == pytest.approx(1.0) and radiality["X"] == pytest.approx(0.4)
    assert radiality["C"] > radiality["X"]


def test_an_isolated_node_has_closeness_zero(tmp_path):
    path = tmp_path / "m.txt"
    path.write_text("\tA\tB\tC\tZ\nA\t0\t1\t1\t0\nB\t1\t0\t1\t0\nC\t1\t1\t0\t0\nZ\t0\t0\t0\t0\n")
    proc = run("local", "-t", "matrix", "-i", str(path), "--no-plot", "-o", str(tmp_path / "l"))
    assert proc.returncode == 0, proc.stderr
    table = report_table(report_path(proc)).set_index("Node Name")
    assert table.loc["Z", "Closeness"] == 0.0 and table.loc["Z", "Radiality"] == 0.0
    proc = run("global", "-t", "matrix", "-i", str(path), "--no-plot", "-o", str(tmp_path / "g"))
    assert report_table(report_path(proc)).set_index("Measure").loc["Average Closeness", "Score"] == 0.75


def test_global_clustering_without_triples_is_zero(tmp_path):
    path = tmp_path / "pair.tsv"
    path.write_text("N1\tN2\nA\tB\nC\tD\n")
    proc = run("global", "-t", "edgelist", "-i", str(path), "--no-plot", "-o", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    scores = report_table(report_path(proc)).set_index("Measure")["Score"]
    assert scores["Average clustering coefficient"] == 0.0 and scores["Global clustering coefficient"] == 0.0
