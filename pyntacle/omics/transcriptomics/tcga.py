"""TCGA barcodes: sample type and one aliquot per patient (--tcga)."""
import re

import pandas as pd

# GDC sample type codes -> group name; --tcga-types overrides
TYPE_NAMES = {"01": "tumor", "11": "normal"}
BARCODE = re.compile(r"^TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}-\d{2}", re.IGNORECASE)


def parse_types(spec):
    """'01:tumor,11:normal' -> {'01': 'tumor', '11': 'normal'}."""
    codes = {}
    for item in spec.split(","):
        code, _, name = item.strip().partition(":")
        if not re.fullmatch(r"\d{2}", code) or not name.strip():
            raise SystemExit("ERROR: --tcga-types expects CODE:NAME pairs such as "
                             "01:tumor,11:normal; got {!r}".format(item))
        codes[code] = name.strip()
    if len(set(codes.values())) != len(codes):
        raise SystemExit("ERROR: --tcga-types gives the same group name to two codes")
    return codes


def is_barcode(name):
    return bool(BARCODE.match(str(name)))


def orient_barcodes(X):
    """Samples in columns, whichever way the file was written."""
    in_cols = sum(map(is_barcode, X.columns))
    in_rows = sum(map(is_barcode, X.index))
    if in_cols == 0 and in_rows == 0:
        raise SystemExit("ERROR: --tcga needs TCGA barcodes (TCGA-XX-XXXX-01A) as sample names; "
                         "got names like {!r}".format(list(X.columns[:2])))
    return X if in_cols >= in_rows else X.T


def sample_type(barcode):
    parts = barcode.split("-")
    return parts[3][:2] if len(parts) >= 4 else None


def patient_id(barcode):
    return barcode[:12]


def _vial(barcode):
    parts = barcode.split("-")
    return parts[3][2:3] if len(parts) >= 4 else ""


def dedup_by_patient(cols, prefer_vial="A"):
    """Keep one barcode per patient, preferring the primary vial."""
    df = pd.DataFrame({"barcode": list(cols), "patient": [patient_id(c) for c in cols]})
    keep, dropped = [], []
    for _, grp in df.groupby("patient", sort=True):
        if len(grp) == 1:
            keep.append(grp["barcode"].iloc[0])
            continue
        pref = grp[[_vial(b) == prefer_vial for b in grp["barcode"]]]
        chosen = pref["barcode"].iloc[0] if len(pref) else grp["barcode"].iloc[0]
        keep.append(chosen)
        dropped.extend(b for b in grp["barcode"] if b != chosen)
    return keep, dropped


def tcga_groups(columns, codes=TYPE_NAMES):
    types = {c: sample_type(c) if is_barcode(c) else None for c in columns}
    other = [c for c in columns if types[c] not in codes]
    # samples ordered by group, then by patient id (dedup order), as in the case
    # study: the permutation null shuffles sample rows, so this order is part
    # of what the seed reproduces
    labels, dup = {}, []
    for code, name in codes.items():
        keep, dropped = dedup_by_patient([c for c in columns if types[c] == code])
        labels.update({c: name for c in keep})
        dup.extend(dropped)
    return pd.Series(labels, dtype=object), {"other_type": other, "duplicate": dup}
