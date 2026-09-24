import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from omics.transcriptomics import select


def _planted(n_samples=60, seed=0):
    rng = np.random.default_rng(seed)
    silent = rng.normal(0.5, 0.2, (300, n_samples)).clip(0)
    # same spread of means for stable and variable genes, so the mean-variance
    # trend is estimated on both at every expression level
    expressed = rng.uniform(5, 11, (300, 1)) + rng.normal(0, 0.3, (300, n_samples))
    variable = rng.uniform(5, 11, (40, 1)) + rng.normal(0, 2.0, (40, n_samples))
    idx = ["s{}".format(i) for i in range(300)] + ["e{}".format(i) for i in range(300)] \
        + ["v{}".format(i) for i in range(40)]
    return pd.DataFrame(np.vstack([silent, expressed, variable]), index=idx)


def test_expressed_genes_separates_silent():
    kept, info = select.expressed_genes(_planted())
    assert not any(g.startswith("s") for g in kept.index)
    assert info["n_expressed"] == 340


def test_hvg_recovers_planted_variable_genes():
    hvg, info = select.highly_variable_genes(_planted())
    v = {g for g in hvg if g.startswith("v")}
    assert len(v) >= 36 and len(hvg - v) <= 10


def test_biotype_filter_rescues_lincs_and_matches_unversioned(tmp_path):
    ann = pd.DataFrame({"gene": ["ENSG1.3", "ENSG2.1", "ENSG3.1", "ENSG4.2"],
                        "symbol": ["TP53", "LINC00470", "FOO", "XIST"],
                        "type_of_gene": ["protein-coding", "unknown", "pseudo", "ncRNA"]})
    ann.to_csv(tmp_path / "a.csv", index=False)
    a = select.load_annotation(str(tmp_path / "a.csv"))
    kept, rescued = select.biotype_filter(["ENSG1.9", "ENSG2.1", "ENSG3.1", "ENSG4.2"], a)
    assert kept == ["ENSG1.9", "ENSG2.1", "ENSG4.2"] and rescued == 1
    assert select.sex_linked_mask(["ENSG1.9", "ENSG4.2"], a).tolist() == [False, True]
