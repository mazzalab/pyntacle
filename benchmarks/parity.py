"""Do old and new compute the same thing? One row per comparable cell.

Compares the warm-up output of each new/new-py cell with the old cell on the
same graph and parameters. Known, documented differences are normalised
away first (spec section 14):
  * new rounds its reports to 3 decimals, old to 5 -> tolerance
    |a - b| <= 1e-3 * max(1, |a|) + 5e-4;
  * eigenvector centrality is scaled to max 1 in new -> both rescaled;
  * metric names differ in spelling only (m-reach/mreach, group degree/degree);
  * global compactness: new reports the reciprocal of old's Randic-deAlba
    value (Mazza's correction, GraphTacle.compactness) -> old is inverted.

Brute-force finders must agree on the score *and* on the whole family of
optimal sets. Greedy is a heuristic: only its score is reported, and a
difference there is not a parity failure.
"""

import ast
import csv
import glob
import os

import collect

ABS_TOL, REL_TOL = 5e-4, 1e-3


def _close(a, b):
    return abs(a - b) <= REL_TOL * max(1.0, abs(a)) + ABS_TOL


def _norm(name):
    name = name.strip().lower().replace("group ", "").replace("-", "").replace("_", " ")
    return {"eigenvector (scaled)": "eigenvector"}.get(name, name)


def _lines(outdir):
    files = [f for f in glob.glob(os.path.join(outdir, "**", "*.tsv"), recursive=True)
             if os.path.basename(f).lower().startswith("report")]
    if not files:
        return None
    with open(files[0]) as fh:
        return [l.rstrip("\n").rstrip("\t").split("\t") for l in fh]


def _table(lines, first_cells):
    """Rows after the header line whose first cell is one of `first_cells`."""
    for i, l in enumerate(lines):
        if l and l[0].strip().lower() in first_cells:
            return l, [r for r in lines[i + 1:] if any(c.strip() for c in r)]
    return None, []


def _nodes(text):
    text = text.strip()
    if text.startswith("["):
        return frozenset(str(x) for x in ast.literal_eval(text))
    return frozenset(x.strip() for x in text.split(",") if x.strip())


def parse(cmd, tool, outdir):
    lines = _lines(outdir)
    if lines is None:
        return None
    if cmd == "local":
        head, rows = _table(lines, {"node name"})
        cols = [_norm(h) for h in head[1:]]
        table = {r[0]: {c: float(v) for c, v in zip(cols, r[1:]) if v.strip()} for r in rows if len(r) > 1}
        top = max((abs(v.get("eigenvector", 0)) for v in table.values()), default=0) or 1
        for v in table.values():
            if "eigenvector" in v:
                v["eigenvector"] /= top
        return table
    if cmd == "global":
        head, rows = _table(lines, {"metric", "measure"})
        return {_norm(r[0]): float(r[1]) for r in rows if len(r) > 1 and r[1].strip()}
    if cmd in ("kp-info", "gc-info"):
        head, rows = _table(lines, {"index", "operation"})
        return {_norm(r[0]): float(r[-1]) for r in rows if len(r) > 2}
    if cmd in ("kp-finder", "gc-finder"):
        head, rows = _table(lines, {"index", "operation"})
        res, current = {}, None
        for r in rows:
            if len(r) < 3:
                continue
            if r[0].strip():
                current = _norm(r[0])
            entry = res.setdefault(current, {"score": float(r[-1]), "sets": set()})
            entry["sets"].add(_nodes(r[-2]))
        return res
    return None


def compare(cmd, algorithm, old, new):
    """(same_result, max_abs_delta, max_rel_delta, notes)"""
    deltas, notes = [], []

    def track(a, b, label):
        deltas.append((abs(a - b), abs(a - b) / max(abs(a), 1e-12)))
        if not _close(a, b):
            notes.append("{}: {} vs {}".format(label, a, b))

    if cmd == "local":
        if set(old) != set(new):
            notes.append("node sets differ ({} vs {})".format(len(old), len(new)))
        for node in set(old) & set(new):
            for col in set(old[node]) & set(new[node]):
                track(old[node][col], new[node][col], node + "." + col)
    elif cmd in ("global", "kp-info", "gc-info"):
        for key in set(old) & set(new):
            if cmd == "global" and key == "compactness" and old[key]:
                track(1.0 / old[key], new[key], key + " (old inverted)")
            else:
                track(old[key], new[key], key)
        missing = set(old) ^ set(new)
        if missing:
            notes.append("only in one tool: " + ",".join(sorted(missing)))
    else:
        for metric in set(old) & set(new):
            track(old[metric]["score"], new[metric]["score"], metric)
            if algorithm == "brute_force" and old[metric]["sets"] != new[metric]["sets"]:
                notes.append("{}: optimal sets differ ({} old vs {} new)".format(
                    metric, len(old[metric]["sets"]), len(new[metric]["sets"])))
    if not deltas:
        return "na", "", "", "; ".join(notes) or "nothing comparable"
    max_abs = max(d[0] for d in deltas)
    max_rel = max(d[1] for d in deltas)
    hard = [n for n in notes if not n.startswith("only in one tool")]
    if algorithm == "greedy":
        return "na", round(max_abs, 6), round(max_rel, 6), "greedy heuristic; " + ("; ".join(notes[:5]) or "same score")
    return ("no" if hard else "yes"), round(max_abs, 6), round(max_rel, 6), "; ".join(notes[:5])


def main(out):
    rows = collect.load_raw(out)
    warm = {}
    for r in rows:
        if r["warmup"] == "1" and r["exit_status"] == "ok" and r["outdir"] and r["cmd"] != "startup":
            warm[tuple(r[k] for k in collect.KEY)] = r
    t = collect.KEY.index("tool")
    result = []
    for key, r in sorted(warm.items()):
        if key[t] == "old":
            continue
        ref = warm.get(key[:t] + ("old",) + key[t + 1:])
        if not ref:
            continue
        try:
            o, n = parse(r["cmd"], "old", ref["outdir"]), parse(r["cmd"], r["tool"], r["outdir"])
            same, ma, mr, notes = ("na", "", "", "report not found") if o is None or n is None \
                else compare(r["cmd"], r["algorithm"], o, n)
        except Exception as exc:  # a parse failure is a finding, not a crash of the harness
            same, ma, mr, notes = "na", "", "", "parse error: {}".format(exc)
        row = dict(zip(collect.KEY, key))
        row.update({"same_result": same, "max_abs_delta": ma, "max_rel_delta": mr, "notes": notes})
        result.append(row)
    path = os.path.join(out, "parity.tsv")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(collect.KEY) + ["same_result", "max_abs_delta",
                                                                "max_rel_delta", "notes"], delimiter="\t")
        w.writeheader()
        w.writerows(result)
    counts = {}
    for r in result:
        counts[r["same_result"]] = counts.get(r["same_result"], 0) + 1
    print("parity.tsv: {} comparisons {}".format(len(result), counts))
