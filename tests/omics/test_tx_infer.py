import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from omics.transcriptomics import gate, infer


def _ggm(n=300, p=40, seed=1):
    """Pairs (0,1), (2,3), ...: known sparse precision matrix."""
    rng = np.random.default_rng(seed)
    P = np.eye(p)
    for i in range(0, p - 1, 2):
        P[i, i + 1] = P[i + 1, i] = 0.45
    X = rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=n)
    genes = ["g{}".format(i) for i in range(p)]
    truth = {("g{}".format(i), "g{}".format(i + 1)) for i in range(0, p - 1, 2)}
    return pd.DataFrame(X.T + 8.0, index=genes), truth


def test_lw_pcor_with_frozen_lambda_is_deterministic():
    df, _ = _ggm()
    X = infer.standardised_samples(df)
    a, iu, lam = infer.lw_pcor(X)
    b, _, _ = infer.lw_pcor(X, lam=lam)
    assert 0 <= lam <= 1 and np.array_equal(a, b)


def test_permutation_fdr_recovers_planted_edges():
    df, truth = _ggm()
    res = infer.permutation_fdr(infer.standardised_samples(df), n_perm=3, seed=7)
    edges = infer.edges_at_fdr(res, np.array(df.index), 0.01)
    found = {tuple(sorted(e)) for e in zip(edges["source"], edges["target"])}
    assert len(found & truth) >= 0.9 * len(truth)
    assert len(found - truth) <= 2
    assert (edges["q_value"] <= 0.01).all()
    # positive precision entries give negative partial correlations
    assert (edges.set_index(["source", "target"])["r"] < 0).loc[
        [e for e in zip(edges["source"], edges["target"]) if tuple(sorted(e)) in truth]].all()


def test_gate_stops_when_low_expression_artefact_is_removed():
    rng = np.random.default_rng(3)
    df, _ = _ggm(p=400)
    low = pd.DataFrame(rng.poisson(0.3, (100, 300)).astype(float),
                       index=["z{}".format(i) for i in range(100)])
    # zero-inflated co-occurrence: each pair of low genes shares a private switch
    for i in range(0, 100, 2):
        on = (rng.normal(size=300) > 1.2).astype(float) * 3
        low.iloc[i] += on
        low.iloc[i + 1] += on
    q, diag = gate.auto_expression_gate(pd.concat([df, low]), min_genes=100)
    assert diag["bias"].iloc[0] == "yes"
    assert q is not None and q > 0 and diag["bias"].iloc[-1] == "no"


def test_covariate_removes_confounded_edge():
    rng = np.random.default_rng(9)
    n = 300
    age = rng.normal(size=n)
    base = rng.normal(size=(n, 30))
    base[:, 0] += 2 * age
    base[:, 1] += 2 * age          # g0-g1 only through age
    df = pd.DataFrame(base.T + 8.0, index=["g{}".format(i) for i in range(30)],
                      columns=["s{}".format(i) for i in range(n)])
    from omics.covariates import design_matrix
    design = design_matrix(pd.DataFrame({"age": age}, index=df.columns), ["age"])
    def top_pair(X):
        pc, iu, _ = infer.lw_pcor(X)
        i = int(np.argmax(np.abs(pc)))
        return {iu[0][i], iu[1][i]}, float(abs(pc[i]))
    pair, strength = top_pair(infer.standardised_samples(df))
    assert pair == {0, 1}
    pc, iu, _ = infer.lw_pcor(infer.standardised_samples(df, design))
    k = [i for i in range(len(pc)) if iu[0][i] == 0 and iu[1][i] == 1][0]
    assert abs(pc[k]) < strength / 3
