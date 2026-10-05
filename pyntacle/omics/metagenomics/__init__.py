"""Relative abundances -> one microbial association network per group.

Shared taxon panel (union prevalence), per-group closure, multiplicative
zero replacement and CLR, then StARS-selected graphical lasso -- the
SPIEC-EASI recipe, as in the CRC case study."""
import pandas as pd

from .. import covariates as cov
from . import coda, panel
from .infer import stars_glasso


def run(X, labels, *, prov, meta=None, prevalence="auto", covariates=None,
        stars_beta=0.10, n_sub=50, seed=0, user_set=frozenset()):
    params = {"stars_beta": stars_beta, "n_sub": n_sub, "seed": seed}
    for name, value in params.items():
        prov.record("parameters", name, value, "user" if name in user_set else "default")
    if covariates:
        prov.record("parameters", "covariates", ",".join(covariates), "user")
    A = X.T.astype(float)                       # samples x taxa
    if (A.values < 0).any():
        raise SystemExit("ERROR: negative values in the table: it looks log- or CLR-transformed. "
                         "Pass relative abundances or counts; the pipeline does the CLR itself.")
    # share of each sample's total, whatever the input unit (%, fraction, reads)
    rel = A.div(A.sum(axis=1).where(lambda t: t > 0), axis=0)
    groups = list(dict.fromkeys(labels))
    by_group = {g: A.loc[labels.index[labels == g]] for g in groups}

    if str(prevalence) == "auto":
        th, table = panel.auto_prevalence(by_group)
        prov.diagnostic("prevalence_grid", table)
        prov.record("panel", "prevalence", th, "data-driven",
                    "lowest threshold leaving fewer taxa than the smallest group's n")
    else:
        th = float(prevalence)
        prov.record("panel", "prevalence", th, "user")
    taxa = panel.union_panel(by_group, th)
    if len(taxa) < 2:
        raise SystemExit("ERROR: prevalence {} leaves {} taxa; a network needs at least 2".format(
            th, len(taxa)))
    prov.record("panel", "n_taxa", len(taxa), "data-driven")

    results = {}
    for g in groups:
        sub, dropped = coda.drop_allzero(by_group[g][taxa])
        prov.record("panel", "zeros_" + g, round(float((sub.values == 0).mean()), 3), "data-driven",
                    "fraction of zero values in the panel; edges of sparse panels mostly "
                    "record co-presence")
        if dropped:
            prov.warn("group {}: dropped all-zero sample(s) {}".format(g, dropped))
        Z = coda.coda_transform(sub)
        if covariates:
            Z = cov.residualise(Z, cov.design_matrix(meta.loc[Z.index], covariates))
        fit = stars_glasso(Z, n_subsample=n_sub, beta=stars_beta, random_state=seed)
        prov.record("network", "lambda_" + g, round(fit["lambda_hat"], 4), "data-driven",
                    "StARS, subsample size {}, {} failed fits".format(fit["b"], fit["n_failed_fits"]))
        prov.record("network", "edges_" + g, len(fit["edges"]), "data-driven",
                    "n={} p={}".format(Z.shape[0], Z.shape[1]))
        prov.diagnostic("stars_" + g, fit["instability"])
        nodes = pd.DataFrame({"mean_rel_abundance": rel.loc[by_group[g].index, taxa].mean(axis=0),
                              "prevalence": panel.prevalence(by_group[g][taxa])})
        # samples in which both taxa of an edge are present (before zero
        # replacement): an edge resting on few of them mostly records co-presence
        present = sub > 0
        edges = fit["edges"].copy()
        edges["n_copresent"] = [int((present[a] & present[b]).sum())
                                for a, b in zip(edges["source"], edges["target"])]
        results[g] = {"edges": edges, "nodes": nodes, "stages": {"clr": Z}}
    return results
