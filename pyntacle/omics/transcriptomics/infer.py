"""Gene association network: Ledoit-Wolf shrinkage partial correlations,
edges called by a permutation FDR (Schafer & Strimmer 2005; Tusher 2001).

Shrinkage is frozen at the observed value when the null is computed:
re-estimating it on permuted data inflates it and makes the null too narrow.
"""
import gc

import numpy as np
import pandas as pd

from ..covariates import residualise

N_RANKS = 800   # FDR evaluated on this many log-spaced edge ranks


def zscore_genes(df):
    """z-score per gene (rows genes, columns samples); zero-variance genes dropped."""
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0).dropna()


def standardised_samples(df, design=None):
    """Samples x genes array for lw_pcor, optionally with covariates regressed out."""
    X = zscore_genes(df).T
    if design is not None:
        X = residualise(X, design.loc[X.index])
        X = ((X - X.mean()) / X.std()).dropna(axis=1)
    return X.values.astype(np.float64)


def lw_pcor(X, lam=None):
    """Ledoit-Wolf shrinkage, inverse, partial correlations (upper triangle)."""
    n, p = X.shape
    Xc = X - X.mean(axis=0, keepdims=True)
    S = (Xc.T @ Xc) / n
    mu = np.trace(S) / p
    S2 = np.sum(S * S)
    d2 = (S2 - p * mu * mu) / p
    norms2 = np.einsum("ij,ij->i", Xc, Xc)
    b2 = (np.sum(norms2 ** 2) - n * S2) / (n * n * p)
    lam_hat = min(b2, d2) / d2
    lam_use = lam_hat if lam is None else lam
    Sh = (1.0 - lam_use) * S
    Sh.flat[:: p + 1] += lam_use * mu
    del S
    Theta = np.linalg.inv(Sh)
    del Sh
    d = np.sqrt(np.diag(Theta))
    Theta /= d[:, None]
    Theta /= d[None, :]
    iu = np.triu_indices(p, k=1)
    pcor = -Theta[iu].astype(np.float32)
    del Theta
    gc.collect()
    return pcor, iu, lam_hat


def permutation_fdr(X, n_perm=3, seed=20260731):
    """Null from shuffling each gene independently across samples."""
    n, p = X.shape
    pcor, iu, lam_obs = lw_pcor(X)
    absv = np.abs(pcor)
    rng = np.random.default_rng(seed)
    null_chunks = []
    for _ in range(n_perm):
        Xp = np.empty_like(X)
        for j in range(p):
            Xp[:, j] = X[rng.permutation(n), j]
        pcor_p, _, _ = lw_pcor(Xp, lam=lam_obs)
        null_chunks.append(np.abs(pcor_p))
        del Xp, pcor_p
    null = np.sort(np.concatenate(null_chunks))
    del null_chunks
    order = np.argsort(-absv)
    sorted_abs = absv[order]
    # the case study's grid starts at rank 20; ranks 1-19 are added so that a
    # network with fewer than 20 real edges can still be called
    grid = np.round(np.geomspace(20, absv.size, N_RANKS)).astype(np.int64)
    ranks = np.unique(np.r_[np.arange(1, min(20, absv.size + 1)), grid])
    exceed = (null.size - np.searchsorted(null, sorted_abs[ranks - 1], side="left")) / n_perm
    fdr = np.minimum(exceed / ranks, 1.0)
    fdr = np.minimum.accumulate(fdr[::-1])[::-1]   # monotone in rank
    null_max = float(null[-1])
    del null
    gc.collect()
    return {"pcor": pcor, "iu": iu, "order": order, "sorted_abs": sorted_abs, "ranks": ranks,
            "fdr": fdr, "lam": float(lam_obs), "null_max": null_max}


def edges_at_fdr(res, genes, level):
    ok = np.where(res["fdr"] <= level)[0]
    if not ok.size:
        return pd.DataFrame({"source": [], "target": [], "r": [], "q_value": []})
    k = int(res["ranks"][ok[-1]])
    sel = res["order"][:k]
    # q of the edge at rank i: the FDR at the first evaluated rank >= i
    pos = np.searchsorted(res["ranks"], np.arange(1, k + 1), side="left")
    return pd.DataFrame({"source": genes[res["iu"][0][sel]], "target": genes[res["iu"][1][sel]],
                         "r": res["pcor"][sel].astype(float), "q_value": res["fdr"][pos]})
