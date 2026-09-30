"""The command line as users reach it: `python -m pyntacle`, the script path,
the version flag, the output directory, and the kp-info / gc-info reports."""
import os
import subprocess
import sys

from conftest import PKG_DIR, REPO_ROOT

PYTHON = sys.executable
EDGELIST = "A\tB\nB\tC\nC\tD\nD\tA\nA\tC\n"


def _run(*argv, cwd=REPO_ROOT):
    return subprocess.run([PYTHON, *argv], capture_output=True, text=True, cwd=cwd)


def test_module_entry_point_prints_help():
    proc = _run("-m", "pyntacle")
    assert proc.returncode == 0, proc.stderr
    assert "keyplayer" in proc.stdout


def test_script_entry_point_runs_from_any_directory(tmp_path):
    proc = _run(os.path.join(PKG_DIR, "main.py"), cwd=str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert "keyplayer" in proc.stdout


def test_version_flag_prints_the_version():
    proc = _run("-m", "pyntacle", "--version")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.startswith("Pyntacle ")


def test_missing_output_directory_is_created(tmp_path):
    edgelist = tmp_path / "toy.tsv"
    edgelist.write_text(EDGELIST)
    outdir = tmp_path / "new" / "nested"
    proc = _run("-m", "pyntacle", "local", "-t", "edgelist", "-i", str(edgelist), "-nh",
                "-o", str(outdir), "--no-plot")
    assert proc.returncode == 0, proc.stderr
    assert (outdir / "report_toy_local.tsv").exists()


FIGURE_8 = os.path.join(REPO_ROOT, "examples", "figure_8.egl")


def _info(tmp_path, *argv):
    proc = _run("-m", "pyntacle", *argv, "-t", "edgelist", "-i", FIGURE_8, "-o", str(tmp_path))
    return proc, sorted(p.name for p in tmp_path.iterdir()) if tmp_path.exists() else []


def _table(report):
    lines = report.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Operation\t"))
    return [l.split("\t") for l in lines[start:] if l]


def test_gc_info_has_one_row_per_operation_and_an_html_report(tmp_path):
    proc, files = _info(tmp_path, "groupcentrality", "gc-info", "-n", "HS,BR")
    assert proc.returncode == 0, proc.stderr
    assert "figure_8_groupcentrality.html" in files
    table = _table(tmp_path / "report_figure_8_groupcentrality_info_all.tsv")
    assert table[0] == ["Operation", "Node-set", "Score"]
    assert [r[0] for r in table[1:]] == ["degree", "closeness", "betweenness"]


def test_single_operation_info_keeps_the_same_columns(tmp_path):
    proc, _ = _info(tmp_path, "keyplayer", "kp-info", "-n", "HS,BR", "-oper", "dF")
    assert proc.returncode == 0, proc.stderr
    table = _table(tmp_path / "report_figure_8_keyplayer_info_dF.tsv")
    assert table[0] == ["Operation", "Key-player", "Score"]
    assert [r[0] for r in table[1:]] == ["dF"]


def test_info_without_node_set_fails(tmp_path):
    proc, _ = _info(tmp_path, "groupcentrality", "gc-info")
    assert proc.returncode != 0
    assert "-n" in proc.stderr


def test_info_with_unknown_node_fails_and_names_it(tmp_path):
    proc, _ = _info(tmp_path, "keyplayer", "kp-info", "-n", "HS,NOPE")
    assert proc.returncode != 0
    assert "NOPE" in proc.stderr
