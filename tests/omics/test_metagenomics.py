import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from omics import metagenomics
from omics.metagenomics import coda, panel
from omics.metagenomics import infer as minfer
from omics.provenance import Provenance


def test_coda_matches_definitions_and_is_scale_invariant():
    a = np.array([[0.5, 0.0, 0.25, 0.25], [0.1, 0.2, 0.3, 0.4]])
    r = coda.multiplicative_replacement(a)
    assert np.allclose(r.sum(axis=1), 1) and (r > 0).all()
    assert np.isclose(r[0, 1], (1 / 4) ** 2)
    assert np.allclose(coda.clr(r).sum(axis=1), 0)
    pct = pd.DataFrame(a * 100)
    assert np.allclose(coda.coda_transform(pct).values, coda.coda_transform(pd.DataFrame(a)).values)


def test_auto_prevalence_is_lowest_threshold_below_min_n():
    rng = np.random.default_rng(0)
    frac = np.linspace(0.02, 0.6, 30)
    big = pd.DataFrame(rng.random((50, 30)) * (rng.random((50, 30)) < frac))
    small = pd.DataFrame(rng.random((12, 30)) * (rng.random((12, 30)) < frac))
    groups = {"A": big, "B": small}
    th, table = panel.auto_prevalence(groups)
    assert len(panel.union_panel(groups, th)) < 12
    assert (table.loc[table["threshold"] < th, "n_taxa"] >= 12).all()


def test_auto_prevalence_refuses_when_impossible():
    tiny = pd.DataFrame(np.ones((5, 30)))
    with pytest.raises(SystemExit, match="--prevalence"):
        panel.auto_prevalence({"A": tiny})


def test_stars_recovers_planted_graph_and_is_deterministic():
    rng = np.random.default_rng(2)
    p = 12
    P = np.eye(p)
    for i in range(0, p - 1, 2):
        P[i, i + 1] = P[i + 1, i] = 0.45
    X = pd.DataFrame(rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=300),
                     columns=["t{}".format(i) for i in range(p)])
    a = minfer.stars_glasso(X, n_subsample=20)
    b = minfer.stars_glasso(X, n_subsample=20)
    pairs = {tuple(sorted(e)) for e in zip(a["edges"]["source"], a["edges"]["target"])}
    truth = {("t{}".format(i), "t{}".format(i + 1)) for i in range(0, p - 1, 2)}
    assert truth <= pairs and a["lambda_hat"] == b["lambda_hat"]


def test_run_builds_one_network_per_group_on_shared_panel():
    rng = np.random.default_rng(4)
    taxa = ["t{}".format(i) for i in range(10)]
    X = pd.DataFrame(rng.dirichlet(np.ones(10), size=80).T, index=taxa,
                     columns=["s{}".format(i) for i in range(80)])
    X.iloc[:, 0] = 0.0                                   # one all-zero sample
    labels = pd.Series(["T"] * 50 + ["N"] * 30, index=X.columns)
    prov = Provenance("metagenomics")
    out = metagenomics.run(X, labels, prov=prov, n_sub=10)
    assert set(out) == {"T", "N"}
    assert ("prevalence", "data-driven") in {(v["name"], v["kind"]) for v in prov.values}
    assert any("s0" in w for w in prov.warnings)
