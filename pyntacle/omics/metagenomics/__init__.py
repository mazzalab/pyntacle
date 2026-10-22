"""Relative abundances -> one microbial association network per group.

Shared taxon panel (union prevalence), per-group closure, multiplicative
zero replacement and CLR, then StARS-selected graphical lasso -- the
SPIEC-EASI recipe, as in the CRC case study."""
import pandas as pd

from .. import covariates as cov
from . import coda, panel
from .infer import stars_glasso


def run(X, labels, *, prov, meta=None, prevalence="auto", covariates=None,
        stars_beta=0.10, n_sub=50, max_iter=200, seed=0, user_set=frozenset()):
    params = {"stars_beta": stars_beta, "n_sub": n_sub, "max_iter": max_iter, "seed": seed}
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
    n_min = min(df.shape[0] for df in by_group.values())
    if str(prevalence) != "auto" and len(taxa) >= n_min:
        prov.warn("prevalence {} leaves {} taxa for {} samples in the smallest group: the graphical "
                  "lasso may fail or stop at --max-iter at small penalties (see the StARS fit counts); "
                  "--prevalence auto keeps fewer taxa than samples".format(th, len(taxa), n_min))

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
        fit = stars_glasso(Z, n_subsample=n_sub, beta=stars_beta, random_state=seed, max_iter=max_iter)
        final = fit["final"]
        note = "StARS, subsample size {}".format(fit["b"])
        if fit["lambda_hat"] != fit["lambda_stars"]:
            note += "; StARS selected {:.4g}, where the fit on all samples failed".format(fit["lambda_stars"])
            prov.warn("group {}: the graphical lasso failed on all samples at the StARS penalty {:.4g}; "
                      "the closest larger penalty that fits, {:.4g}, was used".format(
                          g, fit["lambda_stars"], fit["lambda_hat"]))
        prov.record("network", "lambda_" + g, round(fit["lambda_hat"], 4), "data-driven", note)
        prov.record("network", "stars_failed_fits_" + g, fit["n_failed_fits"], "data-driven",
                    "of {} subsample fits: both solvers raised or diverged; left out of the edge "
                    "frequencies".format(fit["n_fits"]))
        prov.record("network", "stars_fits_at_max_iter_" + g, fit["n_fits_at_limit"], "data-driven",
                    "of {} subsample fits: stopped at --max-iter without converging; kept in the edge "
                    "frequencies".format(fit["n_fits"]))
        prov.record("network", "final_fit_" + g, "converged" if final["converged"] else "not converged",
                    "data-driven", "{}, {} iteration(s)".format(
                        "coordinate descent" if final["solver"] == "cd" else "LARS", final["n_iter"]))
        bad = fit["n_failed_fits"] + fit["n_fits_at_limit"]
        if bad > 0.1 * fit["n_fits"]:
            prov.warn("group {}: {} of {} StARS subsample fits failed or stopped at --max-iter; the "
                      "penalty rests on the others (fewer taxa, or a larger --max-iter, may help)".format(
                          g, bad, fit["n_fits"]))
        if not final["converged"]:
            prov.warn("group {}: the network fit stopped at --max-iter ({}) without converging; the "
                      "weights are the last estimate".format(g, max_iter))
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
