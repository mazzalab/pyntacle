"""Self-terminating expression gate.

Weakly expressed genes, with their frequent zero counts, produce spurious
strong partial correlations. Raise a mean-expression quantile until the
strongest edges are no longer concentrated among the least expressed genes
(one-sided Mann-Whitney). The stopping point is chosen by the data.
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from .infer import lw_pcor, standardised_samples, zscore_genes

GRID = np.arange(0.0, 0.91, 0.05)


def expression_bias_pvalue(df, design=None, top=100):
    genes = zscore_genes(df).index
    X = standardised_samples(df.loc[genes], design)
    mean_expr = df.loc[genes].mean(axis=1).values
    pcor, iu, _ = lw_pcor(X)
    best = np.argsort(-np.abs(pcor))[:top]
    mask = np.zeros(X.shape[1], dtype=bool)
    mask[np.unique(np.concatenate([iu[0][best], iu[1][best]]))] = True
    pval = mannwhitneyu(mean_expr[mask], mean_expr[~mask], alternative="less").pvalue
    return float(pval), X.shape[1], float(mean_expr[mask].mean()), float(mean_expr[~mask].mean())


def auto_expression_gate(df, design=None, alpha=0.05, top=100, min_genes=300, grid=None):
    mean_expr = df.mean(axis=1)
    rows, chosen = [], None
    for q in (GRID if grid is None else grid):
        sub = df.loc[mean_expr >= mean_expr.quantile(q)]
        if sub.shape[0] < min_genes:
            break
        pval, p_eff, m_top, m_bg = expression_bias_pvalue(sub, design, top)
        rows.append({"quantile": round(float(q), 2), "genes": p_eff, "mean_top": round(m_top, 2),
                     "mean_background": round(m_bg, 2), "p_value": pval,
                     "bias": "yes" if pval < alpha else "no"})
        if pval >= alpha:
            chosen = round(float(q), 2)
            break
    return chosen, pd.DataFrame(rows)
