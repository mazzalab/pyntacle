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
    code = "import sys; sys.path.insert(0, '.'); import pyntacle.main; print('pyntacle.omics' in sys.modules)"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    assert r.stdout.strip().endswith("False"), r.stderr


@pytest.mark.parametrize("extra,message", [
    (["--fdr", "0.01"], "--fdr only applies to transcriptomics"),
    (["--tcga"], "--tcga only applies to transcriptomics"),
    (["--stars-b", "0.2"], "unrecognized arguments"),
    (["--n-sub", "0"], "not a positive integer"),
    (["--prevalence", "abc"], "'auto' or a number"),
    (["--covariates", "bmi"], "--covariates not in metadata: bmi"),
])
def test_cli_metagenomics_refuses_wrong_options(tmp_path, extra, message):
    _abund(tmp_path)
    r = _run("metagenomics", "-i", str(tmp_path / "ab.tsv"), "-m", str(tmp_path / "meta.tsv"),
             "--group-col", "grp", "-o", str(tmp_path / "o"), *extra)
    assert r.returncode != 0 and message in (r.stderr + r.stdout), r.stderr + r.stdout


@pytest.mark.parametrize("extra,message", [
    (["--tcga", "--group-col", "grp"], "--group-col does not apply with --tcga"),
    (["--tcga", "-m", "META"], "-m is read only for --covariates"),
    (["--tcga", "--groups", "Tumor"], "not among the --tcga groups (tumor, normal)"),
    (["--tcga-types", "06:met", "-m", "META", "--group-col", "grp"], "--tcga-types needs --tcga"),
    (["--drop-sex-genes", "-m", "META", "--group-col", "grp"], "pass --biotype"),
    (["--prevalence", "0.2", "-m", "META", "--group-col", "grp"], "only applies to metagenomics"),
])
def test_cli_transcriptomics_refuses_conflicts(tmp_path, extra, message):
    _abund(tmp_path)
    extra = [str(tmp_path / "meta.tsv") if a == "META" else a for a in extra]
    r = _run("transcriptomics", "-i", str(tmp_path / "ab.tsv"), "-o", str(tmp_path / "o"), *extra)
    assert r.returncode != 0 and message in (r.stderr + r.stdout), r.stderr + r.stdout


def test_cli_reads_a_metaphlan_table_at_one_rank(tmp_path):
    rng = np.random.default_rng(2)
    ids = ["s{}".format(i) for i in range(40)]
    genera = ["g{}".format(i) for i in range(6)]
    ab = rng.dirichlet(np.ones(6), size=40).T * 100
    rows = {"k__Bacteria": ab.sum(axis=0), "k__Bacteria|p__Firmicutes": ab.sum(axis=0)}
    for g, v in zip(genera, ab):
        rows["k__Bacteria|p__Firmicutes|c__C|o__O|f__F|g__" + g] = v
    table = pd.DataFrame(rows, index=ids).T
    table.index.name = "clade_name"
    with open(tmp_path / "merged.txt", "w") as fh:
        fh.write("#mpa_vJan21_CHOCOPhlAnSGB_202103\n")
        table.to_csv(fh, sep="\t")
    pd.DataFrame({"grp": ["A"] * 20 + ["B"] * 20}, index=ids).to_csv(tmp_path / "meta.tsv", sep="\t")
    base = ["metagenomics", "-i", str(tmp_path / "merged.txt"), "-m", str(tmp_path / "meta.tsv"),
            "--group-col", "grp", "-o", str(tmp_path / "o"), "--n-sub", "5"]
    r = _run(*base)
    assert r.returncode != 0 and "--rank" in r.stderr + r.stdout
    r = _run(*base, "--rank", "genus")
    assert r.returncode == 0, r.stderr + r.stdout
    g = pd.read_csv(tmp_path / "o" / "merged_report.tsv", sep="\t")
    assert "6 of 8 features kept" in g.loc[g["name"] == "rank", "note"].item()
