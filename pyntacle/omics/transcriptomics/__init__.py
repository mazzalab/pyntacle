"""Bulk RNA-seq counts -> one gene association network per group.

Order follows the CRC case study: counts, joint median-of-ratios, per-group
GMM selection, union, optional biotype and sex-linked filters, per-group
expression gate, Ledoit-Wolf partial correlations with a permutation FDR.
"""
import numpy as np
import pandas as pd

from .. import covariates as cov
from . import gate as gate_mod
from . import infer, normalize, scale, select


def run(X, labels, *, prov, meta=None, input_scale="auto", annotation=None,
        drop_sex_genes=False, covariates=None, gate_alpha=0.05, gate_top=100,
        gate_min_genes=300, fdr=0.001, n_perm=3, seed=20260731, random_state=42,
        user_set=frozenset()):
    params = {"gate_alpha": gate_alpha, "gate_top": gate_top, "gate_min_genes": gate_min_genes,
              "fdr": fdr, "n_perm": n_perm, "seed": seed}
    for name, value in params.items():
        prov.record("parameters", name, value, "user" if name in user_set else "default")
    if covariates:
        prov.record("parameters", "covariates", ",".join(covariates), "user")

    detected = scale.detect_scale(X) if input_scale == "auto" else input_scale
    prov.record("scale", "input_scale", detected,
                "data-driven" if input_scale == "auto" else "user")
    counts = scale.to_counts(X, detected)

    log_norm, sf = normalize.log_normalise(counts)
    prov.diagnostic("size_factors", sf.describe().round(4).to_dict())

    groups = list(dict.fromkeys(labels))
    per_group = {g: log_norm[labels.index[labels == g]] for g in groups}

    union = set()
    for g in groups:
        hvg, info = select.highly_variable_genes(per_group[g], random_state)
        prov.record("selection", "hvg_" + g, len(hvg), "data-driven",
                    "GMM: {} expressed genes; rho(residual, mean) {}".format(
                        info["n_expressed"], info["rho_residual_mean"]))
        union |= hvg
    # matrix order, not sorted: the permutation null draws one shuffle per gene
    # in column order, so the order is part of what the seed reproduces
    genes = [g for g in log_norm.index if g in union]
    prov.record("selection", "hvg_union", len(genes), "data-driven")

    if annotation is not None:
        genes, rescued = select.biotype_filter(genes, annotation)
        prov.record("selection", "after_biotype", len(genes), "user",
                    "protein-coding + ncRNA; {} LINC genes rescued from unknown".format(rescued))
    if drop_sex_genes:
        if annotation is None:
            raise SystemExit("ERROR: --drop-sex-genes needs gene symbols: pass --biotype")
        mask = select.sex_linked_mask(genes, annotation)
        genes = [g for g, m in zip(genes, mask) if not m]
        prov.record("selection", "sex_linked_removed", int(mask.sum()), "user")

    results = {}
    for g in groups:
        D = per_group[g].loc[genes]
        design = cov.design_matrix(meta.loc[D.columns], covariates) if covariates else None
        q, diag = gate_mod.auto_expression_gate(D, design, gate_alpha, gate_top, gate_min_genes)
        prov.diagnostic("gate_" + g, diag)
        if q is None:
            raise SystemExit("ERROR: group {}: no expression quantile removes the "
                             "low-expression bias (report diagnostics: gate_{})".format(g, g))
        mean_expr = D.mean(axis=1)
        D = D.loc[mean_expr >= mean_expr.quantile(q)]
        prov.record("gate", "quantile_" + g, q, "data-driven", "{} genes kept".format(D.shape[0]))

        kept = infer.zscore_genes(D).index
        res = infer.permutation_fdr(infer.standardised_samples(D.loc[kept], design),
                                    n_perm=n_perm, seed=seed)
        edges = infer.edges_at_fdr(res, np.array(kept), fdr)
        prov.record("network", "lambda_LW_" + g, round(res["lam"], 4), "data-driven")
        prov.record("network", "null_separation_" + g,
                    round(float(res["sorted_abs"][0] / res["null_max"]), 2), "data-driven",
                    "max |pcor| observed / max under permutation")
        prov.record("network", "edges_" + g, len(edges), "data-driven",
                    "n={} p={}".format(D.shape[1], len(kept)))
        nodes = pd.DataFrame({"mean_log2_expr": D.mean(axis=1)})
        if annotation is not None:
            base = [select.base_id(i) for i in nodes.index]
            nodes["symbol"] = annotation["symbol"].reindex(base).values
            nodes["biotype"] = annotation["type_of_gene"].reindex(base).values
        results[g] = {"edges": edges, "nodes": nodes,
                      "stages": {"log_norm": per_group[g], "final": D}}
    return results
