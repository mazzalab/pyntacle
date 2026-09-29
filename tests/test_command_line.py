"""The command line as users reach it: `python -m pyntacle`, the script path,
the version flag and the output directory."""
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
