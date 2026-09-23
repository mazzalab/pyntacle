"""--engine python and -np are mutually exclusive in effect; say so.

The Python engine has neither OpenMP nor multiprocessing, so `-np 8 --engine
python` silently runs on one core. Asking for eight and getting one without a
word is the kind of thing that gets written up as "pyntacle does not scale".

Also pins down what --engine can and cannot switch: there is no Python
brute-force implementation any more (algorithms/brute_force.py was removed), so
that combination has to be refused rather than quietly fall back to Cython.
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO_ROOT, "pyntacle", "main.py")

# Matched verbatim rather than by keyword: the reports print "df_single_metric",
# so a loose search for "single" passes without any warning being emitted.
NP_WARNING = "--engine python is single-threaded"


@pytest.fixture
def network(tmp_path):
    path = os.path.join(str(tmp_path), "net.txt")
    with open(path, "w") as fh:
        fh.write("V1\tV2\n")
        for u, v in [("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "E"),
                     ("D", "E"), ("D", "F"), ("E", "G"), ("F", "G"), ("G", "H")]:
            fh.write(f"{u}\t{v}\n")
    return path


def run_cli(*args, cwd=None):
    return subprocess.run([sys.executable, MAIN, *args],
                          capture_output=True, text=True, timeout=300, cwd=cwd)


def test_python_engine_with_multiple_threads_warns(network, tmp_path):
    """-np > 1 together with --engine python must tell the user it will not scale."""
    outdir = os.path.join(str(tmp_path), "out")
    os.makedirs(outdir, exist_ok=True)

    result = run_cli("keyplayer", "kp-finder", "-i", network, "-t", "edgelist",
                     "--algorithm", "greedy", "-oper", "F", "-k", "2",
                     "--engine", "python", "-np", "4", "-o", outdir)

    assert result.returncode == 0, result.stderr[-800:]
    assert NP_WARNING in (result.stdout + result.stderr), (
        "no warning about -np being ineffective with --engine python:\n" + result.stdout[-800:])


def test_python_engine_with_one_thread_stays_quiet(network, tmp_path):
    """The warning must be about the mismatch, not fire on every python-engine run."""
    outdir = os.path.join(str(tmp_path), "out1")
    os.makedirs(outdir, exist_ok=True)

    result = run_cli("keyplayer", "kp-finder", "-i", network, "-t", "edgelist",
                     "--algorithm", "greedy", "-oper", "F", "-k", "2",
                     "--engine", "python", "-np", "1", "-o", outdir)

    assert result.returncode == 0, result.stderr[-800:]
    assert NP_WARNING not in (result.stdout + result.stderr)


def test_python_engine_refuses_brute_force(network, tmp_path):
    """There is no Python brute force; falling back to Cython would be a lie."""
    outdir = os.path.join(str(tmp_path), "out2")
    os.makedirs(outdir, exist_ok=True)

    result = run_cli("keyplayer", "kp-finder", "-i", network, "-t", "edgelist",
                     "--algorithm", "brute_force", "-oper", "F", "-k", "2",
                     "--engine", "python", "-o", outdir)

    assert result.returncode != 0, "brute_force + --engine python should not succeed"
    combined = result.stdout + result.stderr
    assert "brute" in combined.lower() and "python" in combined.lower()


def test_cython_engine_brute_force_still_works(network, tmp_path):
    """The refusal above must not catch the default engine."""
    outdir = os.path.join(str(tmp_path), "out3")
    os.makedirs(outdir, exist_ok=True)

    result = run_cli("keyplayer", "kp-finder", "-i", network, "-t", "edgelist",
                     "--algorithm", "brute_force", "-oper", "F", "-k", "2",
                     "-np", "2", "-o", outdir)

    assert result.returncode == 0, result.stderr[-800:]


def test_engine_flag_is_documented_as_single_threaded(network):
    """The help text has to carry the caveat too, not only the runtime warning."""
    result = run_cli("keyplayer", "--help")
    assert "--engine" in result.stdout
    engine_help = result.stdout[result.stdout.index("--engine"):]
    engine_help = engine_help[:400].lower()
    assert "single" in engine_help or "-np" in engine_help
