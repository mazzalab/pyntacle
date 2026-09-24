"""Counts in, whatever the file holds.

UCSC Xena distributes STAR counts as log2(count + 1); normalising those as if
they were counts is the silent error this module exists to prevent.
"""
import numpy as np

LOG_MAX = 50.0   # log2(count+1) of any real library stays far below this


def detect_scale(X):
    v = X.values
    if np.nanmin(v) < 0:
        raise SystemExit("ERROR: negative values in the matrix: not counts nor log2(count+1). "
                         "Pass raw counts.")
    if np.allclose(v, np.round(v)):
        return "counts"
    if np.nanmax(v) <= LOG_MAX:
        return "log2p1"
    raise SystemExit("ERROR: non-integer values above {}: the matrix looks normalised. "
                     "Pass raw counts, or --input-scale counts if they are.".format(LOG_MAX))


def to_counts(X, scale):
    if scale == "counts":
        C = X.round()
    elif scale == "log2p1":
        C = (np.power(2.0, X) - 1.0).round()
    else:
        raise ValueError(scale)
    return C.clip(lower=0.0)
