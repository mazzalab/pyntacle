"""Edge weights mean different things to different metrics.

Shortest-path metrics read a weight as a length; clustering, eigenvector,
PageRank, community detection and mesoscale TI read it as the strength of a
tie; percolation reads it as a transmission threshold. The user declares what
the weights are (--weight-type) and every metric gets the view it needs:
es["weight"] always holds the distance, es["affinity"] the strength,
es["sign"] the sign of a signed weight. Negative weights are never folded
with abs() behind the user's back.
"""
import math
import os
import pickle
import subprocess
import sys

import igraph as ig
import pandas as pd
import pytest

from GraphTacle import Graphtacle
from utility import weight_views

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO_ROOT, "pyntacle", "main.py")


# ---------- weight_views ------------------------------------------------------

def test_distance_type_is_the_old_behaviour():
    v = weight_views([2.0, 0.5, 4.0], "distance", "inverse")
    assert v["distance"] == [2.0, 0.5, 4.0]
    assert v["affinity"] == [0.5, 2.0, 0.25]
    assert v["sign"] == [1, 1, 1]


@pytest.mark.parametrize("transform, expected", [
    ("inverse", [1 / 0.8, 1 / 0.25, 1.0]),
    ("one-minus", [0.2, 0.75, 1e-6]),
    ("neglog", [-math.log(0.8), -math.log(0.25), 1e-6]),
])
def test_affinity_transforms(transform, expected):
    v = weight_views([0.8, 0.25, 1.0], "affinity", transform)
    assert v["affinity"] == [0.8, 0.25, 1.0]
    assert v["distance"] == pytest.approx(expected)


def test_signed_keeps_the_sign_and_uses_the_magnitude():
    v = weight_views([-0.5, 0.25], "signed", "inverse")
    assert v["affinity"] == [0.5, 0.25]
    assert v["distance"] == pytest.approx([2.0, 4.0])
    assert v["sign"] == [-1, 1]


@pytest.mark.parametrize("wtype", ["distance", "affinity"])
def test_negative_weight_is_refused_with_the_fix(wtype):
    with pytest.raises(ValueError, match="--weight-type signed"):
        weight_views([0.5, -0.2], wtype, "inverse")


@pytest.mark.parametrize("transform", ["one-minus", "neglog"])
def test_bounded_transforms_refuse_strengths_above_one(transform):
    with pytest.raises(ValueError, match="inverse"):
        weight_views([0.5, 3.0], "affinity", transform)


def test_unknown_type_or_transform_is_refused():
    with pytest.raises(ValueError):
        weight_views([1.0], "similarity", "inverse")
    with pytest.raises(ValueError):
        weight_views([1.0], "affinity", "square")


# ---------- the views travel with the graph -----------------------------------

@pytest.fixture
def signed_file(tmp_path):
    path = tmp_path / "signed.txt"
    rows = [("A", "B", 0.9), ("B", "C", -0.6), ("C", "D", 0.3), ("A", "D", -0.2),
            ("D", "E", 0.8), ("E", "F", -0.7), ("C", "F", 0.4)]
    path.write_text("N1\tN2\tWeight\n" + "".join(f"{u}\t{v}\t{w}\n" for u, v, w in rows))
    return str(path)


def _load(path, wtype="signed", transform="inverse", func="local"):
    return Graphtacle.from_file(path, func, "edgelist", None, True, False, True,
                                weight_type=wtype, distance_transform=transform)


def test_from_file_builds_every_view(signed_file):
    g = _load(signed_file)
    eid = g.get_eid(g.vs.find(name="B").index, g.vs.find(name="C").index)
    assert g.es[eid]["raw_weight"] == -0.6
    assert g.es[eid]["affinity"] == 0.6
    assert g.es[eid]["weight"] == pytest.approx(1 / 0.6)
    assert g.es[eid]["sign"] == -1
    assert g.weight_info == {"type": "signed", "transform": "inverse"}


def test_without_a_weight_type_the_raw_weights_are_kept(signed_file):
    # file-writing commands (convert, set, extract) must not rewrite weights
    g = Graphtacle.from_file(signed_file, "convert", "edgelist", None, True, False, True)
    assert sorted(g.es["weight"]) == sorted([0.9, -0.6, 0.3, -0.2, 0.8, -0.7, 0.4])
    assert g.weight_info is None


def test_views_survive_node_removal_rebuild_and_pickle(signed_file):
    g = _load(signed_file)
    g.delete_vertices([g.vs.find(name="A").index])
    g2 = Graphtacle.re(g, "local", "edgelist", None, True, False, True, signed_file)
    g3 = pickle.loads(pickle.dumps(g2))
    for h in (g2, g3):
        assert h.weight_info == {"type": "signed", "transform": "inverse"}
        eid = h.get_eid(h.vs.find(name="E").index, h.vs.find(name="F").index)
        assert (h.es[eid]["sign"], h.es[eid]["affinity"]) == (-1, 0.7)
        assert h.es[eid]["weight"] == pytest.approx(1 / 0.7)


def test_affinities_fall_back_to_ones_when_unweighted(zachary):
    assert set(zachary.affinities()) == {1.0}


# ---------- CLI ---------------------------------------------------------------

def run_cli(*args):
    return subprocess.run([sys.executable, MAIN, *args], capture_output=True, text=True, timeout=300)


def _table(path, first_col):
    with open(path) as fh:
        lines = fh.readlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(first_col))
    return pd.read_csv(path, sep="\t", skiprows=start)


def _write(tmp_path, name, rows):
    path = tmp_path / name
    path.write_text("N1\tN2\tWeight\n" + "".join(f"{u}\t{v}\t{w}\n" for u, v, w in rows))
    return str(path)


EDGES = [("A", "B"), ("A", "C"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F"), ("D", "F"), ("F", "G")]
STRENGTH = [0.9, 0.2, 0.5, 0.8, 0.3, 0.6, 0.7, 0.4]


def _local(tmp_path, path, *flags):
    out = tmp_path / ("out_" + "_".join(f.strip("-") for f in flags))
    out.mkdir()
    res = run_cli("local", "-i", path, "-t", "edgelist", "-w", "-o", str(out), "--no-plot", *flags)
    assert res.returncode == 0, res.stdout[-1500:] + res.stderr[-1500:]
    name = os.path.splitext(os.path.basename(path))[0]
    return _table(str(out / f"report_{name}_local.tsv"), "Node Name").set_index("Node Name"), res


def test_affinity_input_equals_the_same_graph_given_as_distances(tmp_path):
    aff = _write(tmp_path, "aff.txt", [(u, v, a) for (u, v), a in zip(EDGES, STRENGTH)])
    dist = _write(tmp_path, "dist.txt", [(u, v, 1 / a) for (u, v), a in zip(EDGES, STRENGTH)])
    t_aff, _ = _local(tmp_path, aff, "-wt", "affinity")
    t_dist, _ = _local(tmp_path, dist, "-wt", "distance")
    pd.testing.assert_frame_equal(t_aff.sort_index(), t_dist.sort_index(), check_exact=False, rtol=1e-6)


def test_affinity_metrics_read_strength_not_distance(tmp_path):
    # a star whose centre is tied strongly to leaf S and weakly to the rest:
    # under affinity S must be the top leaf for PageRank, under the same numbers
    # read as distances it must be the bottom one
    rows = [("C", "S", 0.95)] + [("C", f"L{i}", 0.05) for i in range(5)]
    path = _write(tmp_path, "star.txt", rows)
    t_aff, _ = _local(tmp_path, path, "-wt", "affinity")
    t_dist, _ = _local(tmp_path, path, "-wt", "distance")
    leaves = [n for n in t_aff.index if n != "C"]
    assert t_aff.loc[leaves, "Pagerank"].idxmax() == "S"
    assert t_dist.loc[leaves, "Pagerank"].idxmin() == "S"


def test_negative_weight_without_signed_fails_loudly(tmp_path):
    path = _write(tmp_path, "neg.txt", [("A", "B", 0.5), ("B", "C", -0.4)])
    res = run_cli("local", "-i", path, "-t", "edgelist", "-w", "-o", str(tmp_path), "--no-plot")
    assert res.returncode != 0
    assert "--weight-type signed" in res.stdout + res.stderr


def test_signed_run_equals_the_affinity_run_on_magnitudes_and_says_so(tmp_path):
    signed = _write(tmp_path, "signed.txt",
                    [(u, v, a * (-1) ** i) for i, ((u, v), a) in enumerate(zip(EDGES, STRENGTH))])
    mags = _write(tmp_path, "mags.txt", [(u, v, a) for (u, v), a in zip(EDGES, STRENGTH)])
    t_s, res = _local(tmp_path, signed, "-wt", "signed")
    t_m, _ = _local(tmp_path, mags, "-wt", "affinity")
    pd.testing.assert_frame_equal(t_s.sort_index(), t_m.sort_index(), check_exact=False, rtol=1e-6)
    assert "|w|" in res.stdout


def test_report_header_states_the_weight_semantics(tmp_path):
    path = _write(tmp_path, "hdr.txt", [(u, v, a) for (u, v), a in zip(EDGES, STRENGTH)])
    _, res = _local(tmp_path, path, "-wt", "affinity", "-dt", "neglog")
    report = open(tmp_path / "out_wt_affinity_dt_neglog" / "report_hdr_local.tsv").read()
    assert "Edge weights\taffinity, distance = -ln(w)" in report


def test_convert_keeps_negative_weights(tmp_path):
    path = _write(tmp_path, "conv.txt", [("A", "B", 0.5), ("B", "C", -0.4)])
    out = tmp_path / "conv_out"
    out.mkdir()
    res = run_cli("convert", "-i", path, "-t", "edgelist", "-w", "-o", str(out), "-to", "edgelist", "-fo", "c")
    assert res.returncode == 0, res.stdout[-1500:] + res.stderr[-1500:]
    written = "".join(open(os.path.join(out, f)).read() for f in os.listdir(out))
    assert "-0.4" in written


@pytest.mark.parametrize("wtype", ["affinity", "signed"])
def test_python_and_cython_engines_agree(tmp_path, wtype):
    rows = [(u, v, a * (-1 if wtype == "signed" and i % 2 else 1))
            for i, ((u, v), a) in enumerate(zip(EDGES, STRENGTH))]
    path = _write(tmp_path, f"eng_{wtype}.txt", rows)
    tables = []
    for engine in ("cython", "python"):
        out = tmp_path / f"kp_{wtype}_{engine}"
        out.mkdir()
        res = run_cli("keyplayer", "kp-info", "-i", path, "-t", "edgelist", "-w", "-wt", wtype,
                      "-n", "C,F", "-m", "2", "--engine", engine, "-o", str(out), "--no-plot")
        assert res.returncode == 0, res.stdout[-1500:] + res.stderr[-1500:]
        report = [f for f in os.listdir(out) if f.endswith(".tsv")][0]
        tables.append(open(out / report).read().split("\n\n", 2)[-1])
    assert tables[0] == tables[1]


# ---------- percolation thresholds --------------------------------------------

def test_percolation_thresholds_follow_the_weight_type(tmp_path):
    from percolation import edge_thresholds_from_graph
    path = _write(tmp_path, "perc.txt", [("A", "B", -0.9), ("B", "C", 0.2)])
    g = _load(path, "signed")
    assert sorted(edge_thresholds_from_graph(g)) == pytest.approx([0.1, 0.8])
    gd = _write(tmp_path, "percd.txt", [("A", "B", 0.3), ("B", "C", 0.7)])
    assert sorted(edge_thresholds_from_graph(_load(gd, "distance"))) == pytest.approx([0.3, 0.7])


def test_kernels_refuse_a_negative_length():
    from _ext.wrapper import _edges
    g = ig.Graph([(0, 1), (1, 2)])
    g.es["weight"] = [1.0, -0.5]
    with pytest.raises(ValueError, match="signed"):
        _edges(g)
