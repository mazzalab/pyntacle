import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
MAIN = os.path.join(ROOT, "pyntacle", "main.py")


def _abund(tmp_path):
    rng = np.random.default_rng(4)
    taxa = ["t{}".format(i) for i in range(10)]
    ids = ["s{}".format(i) for i in range(80)]
    pd.DataFrame(rng.dirichlet(np.ones(10), size=80).T, index=taxa, columns=ids).to_csv(
        tmp_path / "ab.tsv", sep="\t")
    pd.DataFrame({"grp": ["Tumor"] * 50 + ["Normal"] * 30, "age": rng.normal(60, 9, 80)},
                 index=ids).to_csv(tmp_path / "meta.tsv", sep="\t")


def _run(*args):
    return subprocess.run([sys.executable, MAIN, "omics"] + list(args), capture_output=True, text=True)


def test_cli_metagenomics_writes_networks_and_report(tmp_path):
    _abund(tmp_path)
    out = tmp_path / "out"
    r = _run("metagenomics", "-i", str(tmp_path / "ab.tsv"), "-m", str(tmp_path / "meta.tsv"),
             "--group-col", "grp", "-o", str(out), "--n-sub", "10", "--covariates", "age")
    assert r.returncode == 0, r.stderr
    for f in ("ab_tumor.tsv", "ab_normal.graphml", "ab_report.json", "ab_report.tsv"):
        assert (out / f).exists(), f
    report = pd.read_csv(out / "ab_report.tsv", sep="\t")
    kinds = dict(zip(report["name"], report["kind"]))
    assert kinds["n_sub"] == "user" and kinds["stars_beta"] == "default"
    assert kinds["prevalence"] == "data-driven" and kinds["covariates"] == "user"


def test_cli_requires_metadata_unless_tcga(tmp_path):
    _abund(tmp_path)
    r = _run("metagenomics", "-i", str(tmp_path / "ab.tsv"), "-o", str(tmp_path / "o"))
    assert r.returncode != 0 and "--metadata" in (r.stderr + r.stdout)


def test_cli_reports_unknown_group_column(tmp_path):
    _abund(tmp_path)
    r = _run("metagenomics", "-i", str(tmp_path / "ab.tsv"), "-m", str(tmp_path / "meta.tsv"),
             "--group-col", "Definition", "-o", str(tmp_path / "o"))
    assert r.returncode != 0 and "Definition" in (r.stderr + r.stdout) and "grp" in (r.stderr + r.stdout)


def test_existing_commands_do_not_import_omics():
    code = "import sys; sys.path.insert(0, 'pyntacle'); import main; print('omics' in sys.modules)"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    assert r.stdout.strip().endswith("False"), r.stderr
