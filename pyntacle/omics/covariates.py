"""Regress sample covariates (age, purity, batch, ...) out of every feature.

Run per group, right before association is estimated: partial correlations
of the residuals are conditional on the covariates as well.
"""
import numpy as np
import pandas as pd


def design_matrix(meta, columns):
    missing = [c for c in columns if c not in meta.columns]
    if missing:
        raise SystemExit("ERROR: --covariates not in metadata: " + ", ".join(missing))
    sub = meta[columns]
    bad = [c for c in columns if sub[c].isna().any()]
    if bad:
        raise SystemExit("ERROR: covariates with missing values in this group: " + ", ".join(bad))
    parts = [pd.Series(1.0, index=meta.index, name="intercept")]
    for c in columns:
        if pd.api.types.is_numeric_dtype(sub[c]):
            parts.append(sub[c].astype(float))
        else:
            parts.append(pd.get_dummies(sub[c].astype(str), prefix=c, drop_first=True).astype(float))
    return pd.concat(parts, axis=1)


def residualise(Y, design):
    B, *_ = np.linalg.lstsq(design.values, Y.values, rcond=None)
    return pd.DataFrame(Y.values - design.values @ B, index=Y.index, columns=Y.columns)
