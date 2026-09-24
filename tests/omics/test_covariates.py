import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from omics import covariates


def test_residualise_removes_planted_confounder():
    rng = np.random.default_rng(0)
    n = 200
    age = rng.normal(60, 10, n)
    base = rng.normal(size=(n, 2))
    Y = pd.DataFrame(base + np.outer(age, [0.5, -0.3]), columns=["a", "b"])
    meta = pd.DataFrame({"age": age, "sex": rng.choice(["F", "M"], n)})
    D = covariates.design_matrix(meta, ["age", "sex"])
    assert list(D.columns) == ["intercept", "age", "sex_M"]
    R = covariates.residualise(Y, D)
    assert abs(np.corrcoef(R["a"], age)[0, 1]) < 1e-8
    assert np.corrcoef(R["a"], base[:, 0])[0, 1] > 0.99


def test_design_matrix_refuses_missing_values():
    meta = pd.DataFrame({"age": [1.0, np.nan, 3.0]})
    with pytest.raises(SystemExit, match="missing values"):
        covariates.design_matrix(meta, ["age"])
