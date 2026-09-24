"""Which genes enter the network.

Two 2-component Gaussian mixtures, no hand-set threshold: one on mean
expression (expressed vs silent), one on the residual of a LOESS fit of log
variance on mean (more variable than expected at that expression level).
Biotype and sex-linked filters need gene annotation and are optional.
"""
import re

import numpy as np
import pandas as pd

KEEP_TYPES = {"protein-coding", "ncRNA"}
# applied with re.match, as in the case study: LINC genes are rescued from
# "unknown"; the -ASn branch, anchored at the start, never fires
LNCRNA_SYMBOL = re.compile(r"^LINC\d+$|-AS\d+$")
SEX_LINKED = frozenset({
    "TBL1Y", "RPS4Y1", "RPS4Y2", "DDX3Y", "USP9Y", "UTY", "KDM5D", "EIF1AY",
    "NLGN4Y", "ZFY", "TXLNGY", "TMSB4Y", "PRKY", "XIST", "TSIX", "PRKX",
})


def base_id(gene):
    return str(gene).split(".")[0]


def _gmm_high(values, random_state):
    from sklearn.mixture import GaussianMixture
    x = np.asarray(values).reshape(-1, 1)
    gm = GaussianMixture(n_components=2, random_state=random_state, n_init=5).fit(x)
    high = int(np.argmax(gm.means_.ravel()))
    return gm.predict_proba(x)[:, high] > 0.5, gm


def expressed_genes(df, random_state=42):
    mean_expr = df.mean(axis=1)
    keep, gm = _gmm_high(mean_expr.values, random_state)
    return mean_expr[keep], {"n_expressed": int(keep.sum()),
                             "gmm_means": np.round(gm.means_.ravel(), 3).tolist()}


def highly_variable_genes(df, random_state=42):
    from scipy.stats import spearmanr
    from statsmodels.nonparametric.smoothers_lowess import lowess
    mean_expressed, info = expressed_genes(df, random_state)
    var_expr = df.loc[mean_expressed.index].var(axis=1)
    valid = var_expr > 0
    x = mean_expressed[valid].values
    y = np.log(var_expr[valid].values)
    order = np.argsort(x)
    span = x[order].max() - x[order].min()
    trend_sorted = lowess(y[order], x[order], frac=0.3, delta=0.01 * span, return_sorted=False)
    trend = np.empty_like(trend_sorted)
    trend[order] = trend_sorted
    residual = pd.Series(y - trend, index=mean_expressed[valid].index)
    keep, gm = _gmm_high(residual.values, random_state)
    rho, _ = spearmanr(residual.values, mean_expressed.loc[residual.index].values)
    hvg = set(residual.index[keep])
    info.update({"n_hvg": len(hvg), "gmm_residual_means": np.round(gm.means_.ravel(), 3).tolist(),
                 "rho_residual_mean": round(float(rho), 4)})
    return hvg, info


def load_annotation(path):
    from ..loader import read_table
    ann = read_table(path).reset_index()
    missing = {"symbol", "type_of_gene"} - set(ann.columns)
    if missing:
        raise SystemExit("ERROR: annotation file needs columns symbol and type_of_gene "
                         "(missing: {})".format(", ".join(sorted(missing))))
    idcol = "gene" if "gene" in ann.columns else ann.columns[0]
    ann["base"] = ann[idcol].map(base_id)
    return ann.drop_duplicates("base").set_index("base")[["symbol", "type_of_gene"]]


def query_mygene(gene_ids):
    try:
        import mygene
    except ImportError:
        raise SystemExit("ERROR: --biotype mygene needs the mygene package: pip install mygene")
    ids = sorted({base_id(g) for g in gene_ids})
    res = mygene.MyGeneInfo().querymany(ids, scopes="ensembl.gene", fields="symbol,type_of_gene",
                                        species="human", as_dataframe=True, verbose=False)
    res = res[~res.index.duplicated()]
    for col in ("symbol", "type_of_gene"):
        if col not in res.columns:
            res[col] = np.nan
    return res.reindex(ids)[["symbol", "type_of_gene"]].fillna({"type_of_gene": "unknown"})


def biotype_filter(genes, annotation):
    base = [base_id(g) for g in genes]
    types = annotation["type_of_gene"].reindex(base).fillna("unknown").astype(str).values
    symbols = annotation["symbol"].reindex(base).fillna("").astype(str).values
    rescue = (types == "unknown") & np.array([bool(LNCRNA_SYMBOL.match(s)) for s in symbols], dtype=bool)
    types = np.where(rescue, "ncRNA", types)
    kept = [g for g, t in zip(genes, types) if t in KEEP_TYPES]
    return kept, int(rescue.sum())


def sex_linked_mask(genes, annotation):
    symbols = annotation["symbol"].reindex([base_id(g) for g in genes])
    return symbols.isin(SEX_LINKED).values
