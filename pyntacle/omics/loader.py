"""Read the matrix and the metadata, put samples in columns, keep the groups."""
import bz2
import gzip
import lzma
import os

import pandas as pd

COMPRESSED = (".gz", ".bz2", ".xz", ".zip")
_OPENERS = {".gz": gzip.open, ".bz2": bz2.open, ".xz": lzma.open}
_EXPORT_HINT = {
    ".qza": "export it first: qiime tools export --input-path {0} --output-path exported/ "
            "&& biom convert -i exported/feature-table.biom -o table.tsv --to-tsv",
    ".biom": "convert it first: biom convert -i {0} -o table.tsv --to-tsv",
}


def default_sep(path):
    name = path.lower()
    for ext in COMPRESSED:
        if name.endswith(ext):
            name = name[: -len(ext)]
    return "," if name.endswith(".csv") else "\t"


def _comment_rows(path, sep):
    """Line numbers of '#' lines to skip. Tool banners go (MetaPhlAn's database
    and command line, `biom convert`'s "# Constructed from biom file"), and so
    does QIIME 2's "#q2:types" row; a leading '#' line with as many fields as
    the data, such as "#OTU ID" or "#clade_name", is the header and stays."""
    opener = _OPENERS.get(os.path.splitext(path.lower())[1], open)
    head = []
    with opener(path, "rt") as fh:
        for line in fh:
            head.append(line.rstrip("\r\n"))
            if len(head) > 1 and not head[-1].startswith("#") and not head[-2].startswith("#"):
                break
    lead = 0
    while lead < len(head) and head[lead].startswith("#"):
        lead += 1
    skip = set(range(lead))
    if lead < len(head):
        width = len(head[lead].split(sep))
        for i in range(lead - 1, -1, -1):
            if not head[i].startswith("#q2:") and len(head[i].split(sep)) == width > 1:
                skip.discard(i)
                break
    skip |= {i for i, line in enumerate(head) if line.startswith("#q2:")}
    return sorted(skip)


def read_table(path, sep=None):
    if not os.path.exists(path):
        raise SystemExit("ERROR: file not found: " + path)
    ext = os.path.splitext(path.lower())[1]
    if ext in _EXPORT_HINT:
        raise SystemExit("ERROR: {} is not a text table; {}".format(path, _EXPORT_HINT[ext].format(path)))
    sep = default_sep(path) if sep is None else sep
    skip = _comment_rows(path, sep) if ext != ".zip" else []
    return pd.read_csv(path, sep=sep, index_col=0, skiprows=skip)


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


def _duplicates(index):
    return sorted(set(map(str, index[index.duplicated()])))


def check_matrix(X):
    """Values the pipelines cannot use, refused before any computation."""
    dup = _duplicates(X.index)
    if dup:
        raise SystemExit("ERROR: {} feature id(s) appear more than once in the matrix: {}".format(
            len(dup), ", ".join(dup[:5])))
    n_nan = int(X.isna().sum().sum())
    if n_nan:
        raise SystemExit("ERROR: the matrix has {} missing value(s) (first in sample {})".format(
            n_nan, X.columns[X.isna().any()][0]))
    return X


def check_groups(labels, min_n=5):
    counts = labels.value_counts()
    if len(counts) < 1:
        raise SystemExit("ERROR: no sample left in any group")
    small = counts[counts < min_n]
    if len(small):
        raise SystemExit("ERROR: groups need at least {} samples: {}".format(
            min_n, ", ".join("{} n={}".format(g, n) for g, n in small.items())))


def read_metadata(path, sep=None):
    meta = read_table(path, sep)
    meta.index = meta.index.astype(str)
    dup = _duplicates(meta.index)
    if dup:
        raise SystemExit("ERROR: {} sample id(s) appear more than once in the metadata: {}".format(
            len(dup), ", ".join(dup[:5])))
    return meta


def load_inputs(matrix_path, metadata_path, group_col, groups=None, sep=None, prov=None,
                features=None):
    """Matrix restricted to the labelled samples, and their labels.
    `features`, if given, maps the oriented matrix to the rows to analyse."""
    meta = read_metadata(metadata_path, sep)
    if group_col not in meta.columns:
        raise SystemExit("ERROR: --group-col {!r} not in metadata columns: {}".format(
            group_col, ", ".join(map(str, meta.columns[:20]))))
    X = orient(read_table(matrix_path, sep), meta.index)
    X.columns = X.columns.astype(str)
    # annotation columns next to the samples (MetaPhlAn's NCBI_tax_id, a
    # BIOM table's taxonomy) are not samples
    X = X[[c for c in X.columns
           if c in meta.index or pd.api.types.is_numeric_dtype(X[c])]]
    if features is not None:
        X = features(X)
    labels = meta[group_col]
    n_nan = int(labels.isna().sum())
    labels = labels.dropna().astype(str)
    if groups:
        unknown = set(groups) - set(labels)
        if unknown:
            raise SystemExit("ERROR: --groups not found in column {!r}: {} (values: {})".format(
                group_col, ", ".join(sorted(unknown)), ", ".join(sorted(set(labels))[:10])))
        labels = labels[labels.isin(groups)]
    shared = [s for s in X.columns if s in labels.index]
    if prov is not None:
        prov.record("input", "samples_in_matrix", X.shape[1], "data-driven")
        prov.record("input", "samples_used", len(shared), "data-driven",
                    "{} without group label, {} not in metadata".format(
                        n_nan, X.shape[1] - len(set(X.columns) & set(meta.index))))
    X = X[shared]
    try:
        X = X.astype(float)
    except ValueError:
        raise SystemExit("ERROR: non-numeric values in the matrix columns of the samples")
    return check_matrix(X), labels.loc[shared]
