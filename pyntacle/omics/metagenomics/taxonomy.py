"""Taxonomic lineages as feature ids (--rank).

MetaPhlAn tables list every rank at once ("k__Bacteria|p__Firmicutes|...");
QIIME 2 collapsed tables use one rank per table ("d__Bacteria;p__...;g__X").
Nested ranks sum into each other, so a network must be built on one of them.
"""
import re

import pandas as pd

RANKS = {"kingdom": "k", "phylum": "p", "class": "c", "order": "o", "family": "f",
         "genus": "g", "species": "s", "strain": "t"}
_LETTER = {"d": "k", "k": "k", "p": "p", "c": "c", "o": "o", "f": "f", "g": "g", "s": "s", "t": "t"}
_SILVA = dict(zip("0123456", "kpcofgs"))       # SILVA 132 "D_5__" prefixes
_NAME = {v: k for k, v in RANKS.items()}
_PART = re.compile(r"^(?:([a-z])|D_(\d))__(.*)$")


def _parts(feature):
    return [p.strip() for p in re.split(r"[|;]", str(feature)) if p.strip()]


def _rank_of(part):
    m = _PART.match(part)
    if not m:
        return None
    return _LETTER.get(m.group(1)) if m.group(1) else _SILVA.get(m.group(2))


_ORDER = "kpcofgst"


def feature_rank(feature):
    """Rank letter of a lineage (its last component), None if not a lineage.
    Unnamed trailing levels ("__", as `qiime taxa collapse` pads them) count
    from the last named one."""
    parts = _parts(feature)
    for back, part in enumerate(reversed(parts)):
        letter = _rank_of(part)
        if letter is not None:
            pos = _ORDER.index(letter) + back
            return _ORDER[pos] if pos < len(_ORDER) else None
        if part.strip("_"):
            return None
    return None


def _short(feature):
    """Last named component, prefix kept ("g__Blautia"; "f__Lachnospiraceae"
    when the genus is unassigned)."""
    for part in reversed(_parts(feature)):
        m = _PART.match(part)
        if part.strip("_") and (m is None or m.group(3)):
            return part
    return str(feature)


def select_rank(X, rank=None, prov=None):
    """Rows of one rank, renamed to their short name. Tables whose ids are not
    lineages are returned unchanged (and refuse --rank)."""
    ranks = pd.Series([feature_rank(f) for f in X.index], index=X.index)
    if ranks.isna().all():
        if rank:
            raise SystemExit("ERROR: --rank needs taxonomic lineages as feature ids "
                             "(e.g. k__Bacteria|p__Firmicutes); got ids like {!r}".format(X.index[0]))
        return X
    found = ranks.dropna().value_counts()
    if rank is None:
        if len(found) > 1:
            raise SystemExit("ERROR: the table mixes taxonomic ranks ({}): choose one with --rank".format(
                ", ".join("{} {}".format(_NAME[r], n) for r, n in found.items())))
        letter = found.index[0]
    else:
        letter = RANKS[rank]
        if letter not in found.index:
            raise SystemExit("ERROR: no feature at rank {} (ranks present: {})".format(
                rank, ", ".join(_NAME[r] for r in found.index)))
    keep = ranks == letter
    out = X.loc[keep]
    short = pd.Index([_short(f) for f in out.index])
    if not short.duplicated().any():
        out.index = short
    if prov is not None:
        prov.record("input", "rank", _NAME[letter], "user" if rank else "data-driven",
                    "{} of {} features kept".format(int(keep.sum()), len(X)))
    return out
