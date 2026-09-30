"""Counts in, whatever the file holds.

UCSC Xena distributes STAR counts as log2(count + 1); normalising those as if
they were counts is the silent error this module exists to prevent.
"""
import numpy as np

LOG_MAX = 50.0   # log2(count+1) of any real library stays far below this


def _back_transforms_to_integers(v):
    """log2(count + 1) comes back to integers (Xena's rounding aside);
    log2(TPM + 1) or log2(FPKM + 1) does not."""
    c = np.power(2.0, v[np.isfinite(v)]) - 1.0
    small = c[(c > 0.5) & (c < 100)]
    return small.size == 0 or np.mean(np.abs(small - np.round(small)) < 0.05) > 0.5


def detect_scale(X):
    v = X.values
    if np.nanmin(v) < 0:
        raise SystemExit("ERROR: negative values in the matrix: not counts nor log2(count+1). "
                         "Pass raw counts.")
    if np.allclose(v, np.round(v)):
        return "counts"
    if np.nanmax(v) <= LOG_MAX:
        if not _back_transforms_to_integers(v):
            raise SystemExit("ERROR: the values look like log2(x + 1) of normalised data (TPM, FPKM): "
                             "2^x - 1 is not a count. Pass raw counts; for log2(expected_count + 1) "
                             "from RSEM, pass --input-scale log2p1.")
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
