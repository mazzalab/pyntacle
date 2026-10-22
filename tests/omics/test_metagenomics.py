import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from pyntacle.omics import metagenomics
from pyntacle.omics.metagenomics import coda, panel
from pyntacle.omics.metagenomics import infer as minfer
from pyntacle.omics.provenance import Provenance


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


def test_run_refuses_log_transformed_input():
    rng = np.random.default_rng(3)
    ab = pd.DataFrame(rng.dirichlet(np.ones(8), 40).T, index=["t{}".format(i) for i in range(8)],
                      columns=["s{}".format(i) for i in range(40)])
    clr = np.log(ab) - np.log(ab).mean()
    labels = pd.Series(["A"] * 20 + ["B"] * 20, index=ab.columns)
    with pytest.raises(SystemExit, match="CLR-transformed"):
        metagenomics.run(clr, labels, prov=Provenance("metagenomics"), n_sub=5)


def test_node_abundance_is_a_share_of_the_sample_whatever_the_unit():
    rng = np.random.default_rng(3)
    ab = pd.DataFrame(rng.dirichlet(np.ones(8), 40).T, index=["t{}".format(i) for i in range(8)],
                      columns=["s{}".format(i) for i in range(40)])
    labels = pd.Series(["A"] * 20 + ["B"] * 20, index=ab.columns)
    frac = metagenomics.run(ab, labels, prov=Provenance("metagenomics"), n_sub=5)
    reads = metagenomics.run((ab * 12345).round(), labels, prov=Provenance("metagenomics"), n_sub=5)
    for g in ("A", "B"):
        a, b = frac[g]["nodes"]["mean_rel_abundance"], reads[g]["nodes"]["mean_rel_abundance"]
        assert np.allclose(a, ab.T.loc[labels.index[labels == g], a.index].mean())
        assert np.allclose(a, b, atol=1e-4)


def test_each_edge_counts_the_samples_where_both_taxa_are_present():
    # zeros are placed by hand, so the co-presence of every pair is known
    rng = np.random.default_rng(7)
    taxa = ["t{}".format(i) for i in range(6)]
    X = pd.DataFrame(rng.dirichlet(np.ones(6), size=60).T, index=taxa,
                     columns=["s{}".format(i) for i in range(60)])
    X.loc["t0", X.columns[:20]] = 0.0
    X.loc["t1", X.columns[10:30]] = 0.0
    labels = pd.Series(["A"] * 60, index=X.columns)
    out = metagenomics.run(X, labels, prov=Provenance("metagenomics"), n_sub=5, prevalence=0.1)
    present = X.T > 0
    edges = out["A"]["edges"]
    assert len(edges)
    for a, b, n in zip(edges.source, edges.target, edges.n_copresent):
        assert n == int((present[a] & present[b]).sum())


def _planted(n=300, p=12, seed=2):
    rng = np.random.default_rng(seed)
    P = np.eye(p)
    for i in range(0, p - 1, 2):
        P[i, i + 1] = P[i + 1, i] = 0.45
    return pd.DataFrame(rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=n),
                        columns=["t{}".format(i) for i in range(p)])


def test_fit_reports_solver_iterations_and_convergence():
    corr = np.corrcoef(_planted().values, rowvar=False)
    prec, info = minfer._fit_precision(corr, 0.05)
    assert info == {"solver": "cd", "n_iter": info["n_iter"], "converged": True} and info["n_iter"] < 200
    prec, info = minfer._fit_precision(corr, 0.001, max_iter=1)
    assert prec is not None and info["n_iter"] == 1 and not info["converged"]


def test_stars_counts_fits_stopped_at_max_iter_apart_from_failed_ones():
    X = _planted()
    full = minfer.stars_glasso(X, n_subsample=5)
    capped = minfer.stars_glasso(X, n_subsample=5, max_iter=1)
    assert full["n_fits"] == capped["n_fits"] == 5 * 30
    assert full["final"]["converged"] and not capped["final"]["converged"]
    assert capped["n_fits_at_limit"] > full["n_fits_at_limit"] and capped["n_failed_fits"] == 0
    table = capped["instability"]
    assert table["fits_at_limit"].sum() == capped["n_fits_at_limit"]


def test_final_fit_steps_to_a_larger_penalty_when_it_fails_on_all_samples(monkeypatch):
    X = _planted()
    full_corr = np.corrcoef(minfer._standardize(X.values), rowvar=False)
    ref = minfer.stars_glasso(X, n_subsample=5)
    real = minfer._fit_precision

    def failing_on_all_samples(corr, alpha, max_iter=200):
        # fails on the full data at the StARS penalty and below, as FengQ_2015 did
        if np.allclose(corr, full_corr) and alpha <= ref["lambda_hat"] * 1.0001:
            return None, None
        return real(corr, alpha, max_iter)

    monkeypatch.setattr(minfer, "_fit_precision", failing_on_all_samples)
    out = minfer.stars_glasso(X, n_subsample=5)
    assert out["lambda_stars"] == ref["lambda_hat"] and out["lambda_hat"] > ref["lambda_hat"]
    path = out["instability"]["lambda"].tolist()
    assert path.index(out["lambda_hat"]) == path.index(out["lambda_stars"]) - 1


def test_stars_treats_a_penalty_without_any_fit_as_unstable(monkeypatch):
    X = _planted()
    real = minfer._fit_precision
    monkeypatch.setattr(minfer, "_fit_precision",
                        lambda corr, alpha, max_iter=200: (None, None) if alpha < 0.2 else real(corr, alpha, max_iter))
    out = minfer.stars_glasso(X, n_subsample=5)
    table = out["instability"]
    assert out["lambda_hat"] >= 0.2 and table.loc[table["lambda"] < 0.2, "instability"].isna().all()
    assert out["n_failed_fits"] == 5 * int((table["lambda"] < 0.2).sum())


def test_run_reports_convergence_and_warns_when_the_network_fit_stops_at_max_iter():
    rng = np.random.default_rng(4)
    taxa = ["t{}".format(i) for i in range(10)]
    X = pd.DataFrame(rng.dirichlet(np.ones(10), size=80).T, index=taxa,
                     columns=["s{}".format(i) for i in range(80)])
    labels = pd.Series(["T"] * 50 + ["N"] * 30, index=X.columns)
    prov = Provenance("metagenomics")
    metagenomics.run(X, labels, prov=prov, n_sub=5)
    values = {v["name"]: v for v in prov.values}
    for g in ("T", "N"):
        assert values["final_fit_" + g]["value"] == "converged"
        assert values["stars_failed_fits_" + g]["value"] == 0
        assert "stars_fits_at_max_iter_" + g in values
    assert values["max_iter"]["value"] == 200 and values["max_iter"]["kind"] == "default"
    assert not any("max-iter" in w for w in prov.warnings)
    prov = Provenance("metagenomics")
    metagenomics.run(X, labels, prov=prov, n_sub=5, max_iter=1, user_set=frozenset({"max_iter"}))
    values = {v["name"]: v for v in prov.values}
    assert values["final_fit_T"]["value"] == "not converged" and values["max_iter"]["kind"] == "user"
    assert any("network fit stopped at --max-iter" in w for w in prov.warnings)


def test_user_prevalence_leaving_more_taxa_than_samples_is_warned():
    rng = np.random.default_rng(5)
    taxa = ["t{}".format(i) for i in range(30)]
    X = pd.DataFrame(rng.dirichlet(np.ones(30), size=45).T, index=taxa,
                     columns=["s{}".format(i) for i in range(45)])
    labels = pd.Series(["A"] * 25 + ["B"] * 20, index=X.columns)
    prov = Provenance("metagenomics")
    metagenomics.run(X, labels, prov=prov, n_sub=3, prevalence=0.1)
    assert any("30 taxa for 20 samples" in w for w in prov.warnings)


def test_auto_prevalence_scans_up_to_095():
    # 40 taxa present everywhere but 10 samples per taxon missing: only a
    # threshold above 0.5 leaves fewer taxa than the 30 samples
    rng = np.random.default_rng(6)
    n, p = 30, 40
    present = np.ones((n, p), dtype=bool)
    for j in range(p):
        present[rng.choice(n, size=(j % 20) // 2, replace=False), j] = False
    df = pd.DataFrame(rng.random((n, p)) * present)
    th, table = panel.auto_prevalence({"A": df})
    assert th > 0.5 and len(panel.union_panel({"A": df}, th)) < n
    assert table["threshold"].max() == 0.95
