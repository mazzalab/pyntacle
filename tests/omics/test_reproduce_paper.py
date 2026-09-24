"""Slow: rebuild the CRC case-study networks from the raw files.

Runs only with PYNTACLE_SLOW=1 and the article_pynta data present:

    PYNTACLE_SLOW=1 pytest tests/omics/test_reproduce_paper.py -v
"""
import os
import subprocess
import sys

import igraph as ig
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

ART = os.environ.get("PYNTACLE_ARTICLE_DIR", "/home/manu/work/article_pynta")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
MAIN = os.path.join(ROOT, "pyntacle", "main.py")
pytestmark = pytest.mark.skipif(not (os.environ.get("PYNTACLE_SLOW") and os.path.isdir(ART)),
                                reason="slow reproduction test: set PYNTACLE_SLOW=1")


# export_v2 was built with scikit-learn 1.8, whose graphical_lasso solver
# reproduces it to 5e-7; 1.7 converges to the same graph and lambda with
# partial correlations that differ in the 3rd-4th decimal.
_SK = tuple(int(x) for x in __import__("sklearn").__version__.split(".")[:2])
WEIGHT_TOL = 1e-6 if _SK >= (1, 8) else 5e-3


def _pairs(a, b):
    return {tuple(sorted(x)) for x in zip(map(str, a), map(str, b))}


def _jaccard(x, y):
    return len(x & y) / len(x | y)


# The paper chose the prevalence threshold on genus (auto rule -> 0.15) and
# applied the same value to family ("applied uniformly to both taxonomic
# ranks"); on family alone the auto rule would pick 0.10.
@pytest.mark.parametrize("level,extra", [("genus", []), ("family", ["--prevalence", "0.15"])])
def test_metagenomics_matches_export_v2_exactly(tmp_path, level, extra):
    d = os.path.join(ART, "metagen", "data")
    r = subprocess.run([sys.executable, MAIN, "omics", "metagenomics",
                        "-i", os.path.join(d, "bacteria.sample.relabund.{}.txt".format(level)),
                        "-m", os.path.join(d, "sample_metadata_{}.txt".format(level)),
                        "--group-col", "Definition",
                        "--groups", "Primary Solid Tumor,Solid Tissue Normal",
                        "-o", str(tmp_path), "--prefix", level] + extra, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    ref_dir = os.path.join(ART, "metagen", "metagenomics_output", "pyntacle_export_v2")
    for grp, ref in (("primary_solid_tumor", "tumor"), ("solid_tissue_normal", "normal")):
        g = ig.Graph.Read_GraphML(str(tmp_path / "{}_{}.graphml".format(level, grp)))
        mine = {tuple(sorted((g.vs[e.source]["name"], g.vs[e.target]["name"]))): e["assoc_weight"]
                for e in g.es}
        refdf = pd.read_csv(os.path.join(ref_dir, "{}_{}_glasso_dual.tsv".format(level, ref)), sep="\t")
        theirs = {tuple(sorted((a, b))): w
                  for a, b, w in zip(refdf["N1"], refdf["N2"], refdf["assoc_weight"])}
        assert set(mine) == set(theirs), (grp, len(mine), len(theirs))
        assert max(abs(mine[k] - theirs[k]) for k in mine) < WEIGHT_TOL
    report = pd.read_csv(tmp_path / "{}_report.tsv".format(level), sep="\t")
    assert float(report.loc[report["name"] == "prevalence", "value"].iloc[0]) == 0.15


def test_transcriptomics_is_equivalent_to_network_final_gen3(tmp_path):
    c = os.path.join(ART, "Colon")
    r = subprocess.run([sys.executable, MAIN, "omics", "transcriptomics",
                        "-i", os.path.join(c, "GeneExp_COAD-Xena_StarCount", "TCGA-COAD.star_counts.tsv"),
                        "--tcga", "--biotype",
                        os.path.join(c, "preprocessing_gen3", "mygene_biotype_cache_hvg.csv"),
                        "--drop-sex-genes", "-o", str(tmp_path), "--prefix", "coad"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    for grp, ref in (("tumor", "tumore"), ("normal", "normale")):
        mine = pd.read_csv(tmp_path / "coad_{}.tsv".format(grp), sep="\t")
        theirs = pd.read_csv(os.path.join(c, "network_final_gen3", "edges_{}_FDR0.001.csv.gz".format(ref)))
        me, th = _pairs(mine["N1"], mine["N2"]), _pairs(theirs["gene1"], theirs["gene2"])
        nodes_me = set(mine["N1"]) | set(mine["N2"])
        nodes_th = set(theirs["gene1"]) | set(theirs["gene2"])
        assert _jaccard(me, th) >= 0.95, (grp, len(me), len(th), _jaccard(me, th))
        assert _jaccard(nodes_me, nodes_th) >= 0.95, (grp, len(nodes_me), len(nodes_th))
