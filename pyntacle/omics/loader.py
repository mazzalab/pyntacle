"""Read the matrix and the metadata, put samples in columns, keep the groups."""
import os

import pandas as pd


def read_table(path, sep=None):
    if not os.path.exists(path):
        raise SystemExit("ERROR: file not found: " + path)
    if sep is None:
        name = path.lower()
        for ext in (".gz", ".bz2", ".zip", ".xz"):
            if name.endswith(ext):
                name = name[: -len(ext)]
        sep = "," if name.endswith(".csv") else "\t"
    return pd.read_csv(path, sep=sep, index_col=0)


def orient(matrix, sample_ids):
    """Features x samples, whichever way the file was written."""
    ids = set(map(str, sample_ids))
    in_cols = len(ids & set(map(str, matrix.columns)))
    in_rows = len(ids & set(map(str, matrix.index)))
    if in_cols == 0 and in_rows == 0:
        raise SystemExit("ERROR: no sample id is shared by the matrix and the metadata "
                         "(matrix columns look like {!r}, metadata ids like {!r})".format(
                             list(matrix.columns[:2]), list(sample_ids)[:2]))
    return matrix if in_cols >= in_rows else matrix.T


def check_groups(labels, min_n=5):
    counts = labels.value_counts()
    if len(counts) < 1:
        raise SystemExit("ERROR: no sample left in any group")
    small = counts[counts < min_n]
    if len(small):
        raise SystemExit("ERROR: groups need at least {} samples: {}".format(
            min_n, ", ".join("{} n={}".format(g, n) for g, n in small.items())))


def load_inputs(matrix_path, metadata_path, group_col, groups=None, sep=None, prov=None):
    meta = read_table(metadata_path, sep)
    meta.index = meta.index.astype(str)
    if group_col not in meta.columns:
        raise SystemExit("ERROR: --group-col {!r} not in metadata columns: {}".format(
            group_col, ", ".join(map(str, meta.columns[:20]))))
    X = orient(read_table(matrix_path, sep), meta.index)
    X.columns = X.columns.astype(str)
    labels = meta[group_col]
    n_nan = int(labels.isna().sum())
    labels = labels.dropna().astype(str)
    if groups:
        unknown = set(groups) - set(labels)
        if unknown:
            raise SystemExit("ERROR: --groups not found in column {!r}: {}".format(
                group_col, ", ".join(sorted(unknown))))
        labels = labels[labels.isin(groups)]
    shared = [s for s in X.columns if s in labels.index]
    if prov is not None:
        prov.record("input", "samples_in_matrix", X.shape[1], "data-driven")
        prov.record("input", "samples_used", len(shared), "data-driven",
                    "{} without group label, {} not in metadata".format(
                        n_nan, X.shape[1] - len(set(X.columns) & set(meta.index))))
    return X[shared].astype(float), labels.loc[shared]
