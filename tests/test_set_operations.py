"""The three `set` subcommands must all produce their output file.

`intersection` and `difference` build a Graphtacle and hand it straight to
`ig.plot`. igraph resolves its drawers by exact class, not by isinstance, so a
subclass raises `ValueError: unknown drawer for Graphtacle and backend cairo` --
and because the plot call comes *before* `output_decision`, the command dies
with a traceback and writes nothing at all. `union` escapes because it plots
through `Graphtacle.plot_set` instead.
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO_ROOT, "pyntacle", "main.py")


@pytest.fixture
def two_networks(tmp_path):
    first = os.path.join(str(tmp_path), "net1.txt")
    second = os.path.join(str(tmp_path), "net2.txt")
    with open(first, "w") as fh:
        fh.write("V1\tV2\nA\tB\nA\tC\nB\tC\nC\tD\n")
    with open(second, "w") as fh:
        fh.write("V1\tV2\nA\tB\nB\tC\nC\tX\nX\tY\n")
    return first, second


@pytest.mark.parametrize("subcommand", ["union", "intersection", "difference"])
def test_set_subcommand_completes_and_writes_its_report(two_networks, tmp_path, subcommand):
    first, second = two_networks
    outdir = os.path.join(str(tmp_path), f"out_{subcommand}")
    os.makedirs(outdir, exist_ok=True)

    result = subprocess.run(
        [sys.executable, MAIN, "set", subcommand, "-i", first, "-t", "edgelist",
         "-i2", second, "-o", outdir],
        capture_output=True, text=True, timeout=300)

    assert result.returncode == 0, (
        f"set {subcommand} exited {result.returncode}:\n{result.stderr[-1200:]}")

    reports = [f for f in os.listdir(outdir) if f.endswith(".tsv")]
    assert reports, f"set {subcommand} wrote no report into {outdir}"
