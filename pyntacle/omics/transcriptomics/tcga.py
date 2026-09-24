"""TCGA barcodes: sample type and one aliquot per patient (--tcga)."""
import pandas as pd

TYPE_NAMES = {"01": "tumor", "11": "normal"}


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
    types = {c: sample_type(c) for c in columns}
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
