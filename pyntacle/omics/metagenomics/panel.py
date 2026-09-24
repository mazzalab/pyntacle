"""Taxon panel shared by all groups (prevalence in any group, union).

Auto threshold: the lowest prevalence on the grid that leaves fewer taxa than
samples in the smallest group -- the limiting case for any covariance-based
estimator."""
import numpy as np
import pandas as pd

GRID = np.round(np.arange(0.05, 0.51, 0.05), 2)


def prevalence(df):
    return (df > 0).mean(axis=0)


def union_panel(groups_dfs, threshold):
    keep = set()
    for df in groups_dfs.values():
        pr = prevalence(df)
        keep |= set(pr.index[pr >= threshold])
    return sorted(keep)


def auto_prevalence(groups_dfs, grid=GRID):
    n_min = min(df.shape[0] for df in groups_dfs.values())
    rows, chosen = [], None
    for th in grid:
        n_taxa = len(union_panel(groups_dfs, th))
        rows.append({"threshold": float(th), "n_taxa": n_taxa, "n_min": n_min})
        if chosen is None and 2 <= n_taxa < n_min:
            chosen = float(th)
    if chosen is None:
        raise SystemExit("ERROR: no prevalence threshold on the grid leaves between 2 and {} "
                         "taxa; pass --prevalence explicitly".format(n_min - 1))
    return chosen, pd.DataFrame(rows)
