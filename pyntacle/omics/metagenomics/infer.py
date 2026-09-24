"""Graphical lasso with the penalty chosen by StARS (Liu et al. 2010), the
estimator behind SPIEC-EASI (Kurtz et al. 2015). Deterministic for a seed."""
import warnings

import numpy as np
import pandas as pd


def _standardize(X):
    return (X - X.mean(axis=0)) / X.std(axis=0, ddof=1)


def _fit_precision(corr, alpha):
    from sklearn.covariance import graphical_lasso
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        for mode in ("cd", "lars"):
            try:
                _, prec = graphical_lasso(corr, alpha=alpha, mode=mode, max_iter=200)
            except Exception:
                continue
            if np.all(np.isfinite(prec)):
                return prec
    return None


def stars_glasso(X_df, n_subsample=50, beta=0.10, nlambda=30, lambda_min_ratio=0.05,
                 random_state=0):
    X = X_df.values
    n, p = X.shape
    taxa = np.array(X_df.columns, dtype=str)
    rng = np.random.default_rng(random_state)
    corr_full = np.corrcoef(_standardize(X), rowvar=False)
    lambda_max = np.abs(corr_full - np.diag(np.diag(corr_full))).max()
    lambda_path = np.logspace(np.log10(lambda_max), np.log10(lambda_max * lambda_min_ratio), nlambda)
    b = int(np.floor(((10 * np.sqrt(n) / n) if n > 144 else 0.8) * n))
    iu = np.triu_indices(p, k=1)
    presence = np.full((nlambda, n_subsample, len(iu[0])), np.nan)
    n_failed = 0
    for rep in range(n_subsample):
        idx = rng.choice(n, size=b, replace=False)
        corr_sub = np.corrcoef(_standardize(X[idx]), rowvar=False)
        for li, lam in enumerate(lambda_path):
            prec = _fit_precision(corr_sub, lam)
            if prec is None:
                n_failed += 1
                continue
            adj = np.abs(prec) > 1e-10
            np.fill_diagonal(adj, False)
            presence[li, rep] = adj[iu]
    theta = np.nanmean(presence, axis=1)
    instability = np.maximum.accumulate(np.nanmean(2 * theta * (1 - theta), axis=1))
    valid = np.where(instability <= beta)[0]
    k_sel = valid.max() if len(valid) else 0
    lambda_hat = lambda_path[k_sel]
    prec = _fit_precision(corr_full, lambda_hat)
    if prec is None:
        raise SystemExit("ERROR: graphical lasso did not converge at the selected lambda")
    d = np.sqrt(np.diag(prec))
    pcorr = -prec / np.outer(d, d)
    sel = [(i, j) for i, j in zip(*iu) if abs(prec[i, j]) > 1e-10]
    edges = pd.DataFrame({"source": [taxa[i] for i, _ in sel], "target": [taxa[j] for _, j in sel],
                          "r": [float(pcorr[i, j]) for i, j in sel]})
    return {"edges": edges, "lambda_hat": float(lambda_hat), "b": b, "n_failed_fits": n_failed,
            "instability": pd.DataFrame({"lambda": lambda_path, "instability": instability})}
