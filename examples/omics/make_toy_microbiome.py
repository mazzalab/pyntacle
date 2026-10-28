"""Writes the toy microbiome of this directory: relabund.tsv and samples.tsv.

30 taxa (taxon_01 ... taxon_30) in 90 control and 90 tumor samples, as
relative abundances in percent, one taxon per row and one sample per column,
as in a MetaPhlAn table collapsed to one rank. The data are simulated: log
abundances are drawn from a multivariate normal, closed to 100% per sample,
and abundances under a detection limit are set to zero. In both groups
taxon_01 ... taxon_06 rise and fall together and taxon_07 ... taxon_10
oppose them; taxon_25 ... taxon_28 are rare in control samples and form a
module of their own in tumor samples.

    python make_toy_microbiome.py
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
N_TAXA, N_PER_GROUP, SEED = 30, 90, 42


def group(rng, tumor):
    mean = np.linspace(3.0, -1.0, N_TAXA)
    cov = np.eye(N_TAXA)
    a, b = range(0, 6), range(6, 10)
    for i in a:
        for j in a:
            if i != j:
                cov[i, j] = 0.6
        for j in b:
            cov[i, j] = cov[j, i] = -0.35
    m = range(24, 28)
    if tumor:
        mean[list(m)] += 2.5
        for i in m:
            for j in m:
                if i != j:
                    cov[i, j] = 0.7
    else:
        mean[list(m)] -= 2.0
    logab = rng.multivariate_normal(mean, cov, size=N_PER_GROUP, method="eigh")
    ab = np.exp(logab)
    ab /= ab.sum(axis=1, keepdims=True)
    ab[ab < 0.002] = 0.0
    return 100 * ab / ab.sum(axis=1, keepdims=True)


def main():
    rng = np.random.default_rng(SEED)
    control, tumor = group(rng, False), group(rng, True)
    taxa = ["taxon_{:02d}".format(i + 1) for i in range(N_TAXA)]
    ids = ["S{:03d}".format(i + 1) for i in range(2 * N_PER_GROUP)]
    pd.DataFrame(np.vstack([control, tumor]).T, index=taxa, columns=ids).round(5).to_csv(
        os.path.join(HERE, "relabund.tsv"), sep="\t", index_label="taxon")
    pd.DataFrame({"condition": ["control"] * N_PER_GROUP + ["tumor"] * N_PER_GROUP},
                 index=pd.Index(ids, name="sample")).to_csv(os.path.join(HERE, "samples.tsv"), sep="\t")


if __name__ == "__main__":
    main()
