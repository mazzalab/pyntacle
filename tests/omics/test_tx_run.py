import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from omics import transcriptomics
from omics.provenance import Provenance


def test_run_end_to_end_on_synthetic_counts():
    rng = np.random.default_rng(5)
    n_t, n_n, p = 120, 90, 120
    P = np.eye(p)
    for i in range(0, 40, 2):
        P[i, i + 1] = P[i + 1, i] = 0.4
    lat = rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=n_t + n_n)
    mu = np.r_[rng.uniform(6, 9, 80), np.full(40, 0.3)]
    sd = np.r_[np.full(40, 1.2), np.full(40, 0.2), np.full(40, 0.2)]
    counts = rng.poisson(np.exp2(mu + sd * lat)).T
    X = pd.DataFrame(counts, index=["g{}".format(i) for i in range(p)],
                     columns=["s{}".format(i) for i in range(n_t + n_n)]).astype(float)
    labels = pd.Series(["T"] * n_t + ["N"] * n_n, index=X.columns)
    prov = Provenance("transcriptomics")
    out = transcriptomics.run(X, labels, gate_min_genes=20, gate_top=10, fdr=0.01, prov=prov)
    assert set(out) == {"T", "N"}
    for g in out.values():
        assert len(g["edges"]) > 0
        assert set(g["edges"]["source"]) | set(g["edges"]["target"]) <= {"g{}".format(i) for i in range(40)}
    kinds = {(v["name"], v["kind"]) for v in prov.values}
    assert ("input_scale", "data-driven") in kinds and ("fdr", "default") in kinds


def test_xena_log_scale_gives_the_same_network_as_counts():
    rng = np.random.default_rng(6)
    counts = pd.DataFrame(rng.poisson(50, (60, 40)).astype(float),
                          index=["g{}".format(i) for i in range(60)],
                          columns=["s{}".format(i) for i in range(40)])
    labels = pd.Series(["A"] * 20 + ["B"] * 20, index=counts.columns)
    runs = []
    for X in (counts, np.log2(counts + 1)):
        prov = Provenance("transcriptomics")
        try:
            runs.append(transcriptomics.run(X, labels, gate_min_genes=5, prov=prov))
        except SystemExit as exc:          # pure noise: the gate may refuse, identically
            runs.append(str(exc))
    if isinstance(runs[0], str):
        assert runs[0] == runs[1]
    else:
        for g in ("A", "B"):
            assert runs[0][g]["edges"].equals(runs[1][g]["edges"])
