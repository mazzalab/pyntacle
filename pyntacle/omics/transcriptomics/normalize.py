"""DESeq2 median-of-ratios size factors (Anders & Huber 2010), then log2(x+1).

Size factors are estimated on all groups together, so every group sits on
the same scale. As in the case study, a gene with zeros enters the reference
with the geometric mean of its non-zero samples, and each sample's ratios
skip the genes it does not detect.
"""
import numpy as np


def median_of_ratios_size_factors(counts):
    log_counts = np.log(counts.where(counts > 0))
    log_geomean = log_counts.mean(axis=1)
    valid = log_geomean.notna() & np.isfinite(log_geomean)
    ratios = log_counts.loc[valid].sub(log_geomean[valid], axis=0)
    return np.exp(ratios.median(axis=0))


def log_normalise(counts):
    sf = median_of_ratios_size_factors(counts)
    return np.log2(counts.div(sf, axis=1) + 1.0), sf
