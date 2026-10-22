"""Graphical lasso with the penalty chosen by StARS (Liu et al. 2010), the
estimator behind SPIEC-EASI (Kurtz et al. 2015). Deterministic for a seed."""
import warnings

import numpy as np
import pandas as pd


def _standardize(X):
    return (X - X.mean(axis=0)) / X.std(axis=0, ddof=1)


def _fit_precision(corr, alpha, max_iter=200):
    """Precision matrix at one penalty, by coordinate descent, or by LARS when
    coordinate descent raises or returns non-finite values. Returns
    (precision, info), info = {solver, n_iter, converged}; (None, None) when
    both solvers fail. A fit that reaches max_iter is kept as the last
    estimate and flagged converged=False."""
    from sklearn.covariance import graphical_lasso
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        for mode in ("cd", "lars"):
            try:
                _, prec, n_iter = graphical_lasso(corr, alpha=alpha, mode=mode, max_iter=max_iter,
                                                  return_n_iter=True)
            except Exception:
                continue
            if np.all(np.isfinite(prec)):
                return prec, {"solver": mode, "n_iter": int(n_iter), "converged": n_iter < max_iter}
    return None, None


def stars_glasso(X_df, n_subsample=50, beta=0.10, nlambda=30, lambda_min_ratio=0.05,
                 random_state=0, max_iter=200):
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
    failed = np.zeros(nlambda, dtype=int)          # both solvers raised or diverged
    at_limit = np.zeros(nlambda, dtype=int)        # kept, but stopped at max_iter
    for rep in range(n_subsample):
        idx = rng.choice(n, size=b, replace=False)
        corr_sub = np.corrcoef(_standardize(X[idx]), rowvar=False)
        for li, lam in enumerate(lambda_path):
            prec, info = _fit_precision(corr_sub, lam, max_iter)
            if prec is None:
                failed[li] += 1
                continue
            at_limit[li] += not info["converged"]
            adj = np.abs(prec) > 1e-10
            np.fill_diagonal(adj, False)
            presence[li, rep] = adj[iu]
    fitted = (n_subsample - failed) > 0
    theta = np.nanmean(presence[fitted], axis=1)
    raw = np.full(nlambda, np.inf)                 # a penalty with no fit counts as unstable
    raw[fitted] = np.mean(2 * theta * (1 - theta), axis=1)
    instability = np.maximum.accumulate(raw)
    valid = np.where(instability <= beta)[0]
    k_stars = valid.max() if len(valid) else 0
    # the final fit on all samples can fail where the subsample fits did not:
    # step back along the path to the closest larger penalty that fits
    for k in range(k_stars, -1, -1):
        prec, info = _fit_precision(corr_full, lambda_path[k], max_iter)
        if prec is not None:
            break
    else:
        raise SystemExit("ERROR: graphical lasso failed at every penalty of the path, "
                         "the largest included")
    d = np.sqrt(np.diag(prec))
    pcorr = -prec / np.outer(d, d)
    sel = [(i, j) for i, j in zip(*iu) if abs(prec[i, j]) > 1e-10]
    edges = pd.DataFrame({"source": [taxa[i] for i, _ in sel], "target": [taxa[j] for _, j in sel],
                          "r": [float(pcorr[i, j]) for i, j in sel]})
    # StARS reads the path from the largest penalty down and stops at k_stars:
    # fits at smaller penalties cannot move the choice to a denser network
    return {"edges": edges, "lambda_hat": float(lambda_path[k]), "lambda_stars": float(lambda_path[k_stars]),
            "b": b, "n_fits": n_subsample * nlambda, "n_failed_fits": int(failed.sum()),
            "n_fits_at_limit": int(at_limit.sum()), "final": info,
            "n_fits_to_stars": n_subsample * (k_stars + 1),
            "n_bad_fits_to_stars": int(failed[:k_stars + 1].sum() + at_limit[:k_stars + 1].sum()),
            "instability": pd.DataFrame({"lambda": lambda_path,
                                         "instability": [v if np.isfinite(v) else None for v in instability],
                                         "failed_fits": failed, "fits_at_limit": at_limit})}
