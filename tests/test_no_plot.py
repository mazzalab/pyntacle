"""--no-plot must suppress every figure and HTML report, on every command that
produces one, while still writing the TSV.

Old Pyntacle ships --no-plot; the benchmark comparing it against this tool
runs both arms with report generation off so wall-clock time measures metric
computation, not "new also drew a plot / built a D3 page old never had at
all". This pins that the flag actually reaches every plotting/HTML call site,
not just the ones exercised by the smoke test that first added it.
"""
import os
import subprocess
import sys

from conftest import PKG_DIR

PYTHON = sys.executable

EDGELIST = "A\tB\nB\tC\nC\tD\nD\tA\nA\tC\nD\tE\nE\tF\nF\tD\n"


def _run(tmp_path, name, *argv):
    edgelist = tmp_path / "toy.tsv"
    edgelist.write_text(EDGELIST)
    outdir = tmp_path / name
    outdir.mkdir()
    proc = subprocess.run(
        [PYTHON, os.path.join(PKG_DIR, "main.py"), *argv,
         "-t", "edgelist", "-i", str(edgelist), "-nh", "-o", str(outdir)],
        capture_output=True, text=True, cwd=PKG_DIR,
    )
    assert proc.returncode == 0, proc.stderr
    return outdir


def _kinds(outdir):
    return {p.suffix for p in outdir.iterdir()}


def _assert_plots_suppressed(tmp_path, *argv):
    """Run once plain, once with --no-plot; report suffix must survive, the rest must not."""
    with_plots = _run(tmp_path, "with", *argv)
    without_plots = _run(tmp_path, "without", *argv, "--no-plot")

    assert ".tsv" in _kinds(with_plots)
    assert ".tsv" in _kinds(without_plots), "the TSV is the benchmark's parity data, --no-plot must not touch it"

    dropped = _kinds(with_plots) - _kinds(without_plots)
    assert dropped, f"--no-plot suppressed nothing; baseline had {_kinds(with_plots)}"
    assert _kinds(without_plots) <= {".tsv"}, f"--no-plot left non-tsv output: {_kinds(without_plots)}"


def test_local_no_plot_skips_html_and_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "local")


def test_global_no_plot_skips_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "global")


def test_groupcentrality_gcfinder_no_plot_skips_html_and_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "groupcentrality", "gc-finder", "-k", "2",
                              "-oper", "degree", "-a", "greedy", "--seed", "1")


def test_groupcentrality_gcinfo_no_plot_skips_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "groupcentrality", "gc-info", "-n", "A,B",
                              "-oper", "degree")


def test_keyplayer_kpfinder_no_plot_skips_html_and_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "keyplayer", "kp-finder", "-k", "2",
                              "-oper", "F", "-a", "greedy", "--seed", "1")


def test_keyplayer_kpinfo_no_plot_skips_html(tmp_path):
    _assert_plots_suppressed(tmp_path, "keyplayer", "kp-info", "-n", "A,B", "-oper", "F")


def test_communities_no_plot_skips_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "communities", "fastgreedy")


def test_extract_no_plot_skips_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "extract", "-l")


def test_mesoscale_no_plot_skips_svg(tmp_path):
    _assert_plots_suppressed(tmp_path, "mesoscale", "-k", "2")


def test_percolation_no_plot_skips_html(tmp_path):
    _assert_plots_suppressed(tmp_path, "percolation", "-n", "A")


def test_set_union_no_plot_skips_svg(tmp_path):
    edgelist = tmp_path / "toy.tsv"
    edgelist.write_text(EDGELIST)
    edgelist2 = tmp_path / "toy2.tsv"
    edgelist2.write_text("A\tB\nB\tC\nC\tA\n")

    def run(name, *extra):
        outdir = tmp_path / name
        outdir.mkdir()
        proc = subprocess.run(
            [PYTHON, os.path.join(PKG_DIR, "main.py"), "set", "union",
             "-t", "edgelist", "-i", str(edgelist), "-nh",
             "-i2", str(edgelist2), "-o", str(outdir), *extra],
            capture_output=True, text=True, cwd=PKG_DIR,
        )
        assert proc.returncode == 0, proc.stderr
        return outdir

    with_plots = run("with")
    without_plots = run("without", "--no-plot")

    assert ".tsv" in _kinds(with_plots)
    assert ".tsv" in _kinds(without_plots)
    assert _kinds(with_plots) - _kinds(without_plots), "baseline had no extra artifact to suppress"
    assert _kinds(without_plots) <= {".tsv"}
