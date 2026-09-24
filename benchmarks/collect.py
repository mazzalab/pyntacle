"""runs_raw_*.tsv -> summary.tsv, scaling.tsv, capability.tsv (spec section 9).

Only measured runs (warm-up excluded, exit_status ok) enter the statistics;
every status, including censored and skipped ones, is still counted in
status_summary so a failed cell never silently disappears.
"""

import csv
import glob
import os
import statistics

KEY = ("cmd", "tool", "topology", "n", "d", "weighted", "k", "algorithm", "threads")


def _median(xs):
    return statistics.median(xs) if xs else None


def _mad(xs):
    if not xs:
        return None
    med = statistics.median(xs)
    return statistics.median([abs(x - med) for x in xs])


def _r(x, nd=4):
    return "" if x is None else round(x, nd)


def load_raw(out):
    rows = []
    for path in sorted(glob.glob(os.path.join(out, "runs_raw_*.tsv"))):
        with open(path) as fh:
            rows.extend(csv.DictReader(fh, delimiter="\t"))
    return rows


def summarise(rows):
    cells = {}
    for r in rows:
        cells.setdefault(tuple(r[k] for k in KEY), []).append(r)

    startup = {}
    for key, rs in cells.items():
        if key[0] == "startup":
            startup[key[1]] = _median([float(r["wall_s"]) for r in rs
                                       if r["warmup"] == "0" and r["exit_status"] == "ok"])

    out = {}
    for key, rs in cells.items():
        ok = [r for r in rs if r["warmup"] == "0" and r["exit_status"] == "ok"]
        # a cell too slow for repeats keeps its warm-up as the only number
        if not ok:
            ok = [r for r in rs if r["exit_status"] == "ok"]
        walls = [float(r["wall_s"]) for r in ok]
        rss = [float(r["max_rss_mb"]) for r in ok]
        threads = int(key[KEY.index("threads")] or 1)
        eff = [(float(r["cpu_user_s"]) + float(r["cpu_sys_s"])) / (float(r["wall_s"]) * threads)
               for r in ok if float(r["wall_s"]) > 0]
        statuses = {}
        for r in rs:
            statuses[r["exit_status"]] = statuses.get(r["exit_status"], 0) + 1
        wall_med = _median(walls)
        base = startup.get(key[1])
        row = dict(zip(KEY, key))
        row.update({
            "m": rs[0]["m"], "density": rs[0]["density"], "n_rep": len(walls),
            "wall_median": _r(wall_med), "wall_mad": _r(_mad(walls)),
            "wall_min": _r(min(walls) if walls else None), "wall_max": _r(max(walls) if walls else None),
            "compute_median": _r(max(0.0, wall_med - base) if wall_med is not None and base is not None
                                 and key[0] != "startup" else None),
            "rss_median": _r(_median(rss), 1), "cpu_eff": _r(_median(eff), 3),
            "status_summary": ";".join("{}={}".format(k, v) for k, v in sorted(statuses.items())),
        })
        out[key] = row

    # ratios against old on the identical cell
    t = KEY.index("tool")
    for key, row in out.items():
        if key[t] == "old":
            row["speedup_vs_old"] = row["compute_speedup_vs_old"] = row["rss_ratio_vs_old"] = ""
            continue
        ref = out.get(key[:t] + ("old",) + key[t + 1:])
        def ratio(a, b):
            return round(a / b, 3) if a not in ("", None) and b not in ("", None, 0) and b > 0 else ""
        row["speedup_vs_old"] = ratio(ref["wall_median"], row["wall_median"]) if ref else ""
        row["compute_speedup_vs_old"] = ratio(ref["compute_median"], row["compute_median"]) if ref else ""
        row["rss_ratio_vs_old"] = ratio(ref["rss_median"], row["rss_median"]) if ref else ""
    return out


def scaling(summary):
    th = KEY.index("threads")
    fams = {}
    for key, row in summary.items():
        if row["cmd"] in ("kp-finder", "gc-finder") and row["wall_median"] != "":
            fams.setdefault(key[:th], {})[int(row["threads"])] = row
    out = []
    for fam, by_p in fams.items():
        if len(by_p) < 2 or 1 not in by_p:
            continue
        t1 = by_p[1]["wall_median"]
        for p in sorted(by_p):
            r = by_p[p]
            out.append({"cmd": r["cmd"], "tool": r["tool"], "topology": r["topology"], "n": r["n"],
                        "k": r["k"], "algorithm": r["algorithm"], "weighted": r["weighted"],
                        "threads": p, "wall_median": r["wall_median"],
                        "speedup_p": round(t1 / r["wall_median"], 3),
                        "efficiency_p": round(t1 / r["wall_median"] / p, 3)})
    return out


def capability(summary):
    def status_of(tool, cmd):
        st = [r["status_summary"] for k, r in summary.items() if r["tool"] == tool and r["cmd"] == cmd]
        if not st:
            return "no"
        return "yes" if any("ok=" in s for s in st) else "fails ({})".format(st[0])
    rows = [
        {"feature": "weighted shortest paths (local/global/kp/gc)", "old": "no", "new": "yes",
         "notes": "1.3.2 --weights only reaches PageRank"},
        {"feature": "single-direction edge list", "old": "no", "new": "yes",
         "notes": "old rejects it as directed; needs every edge listed twice"},
        {"feature": "brute force with the python engine", "old": "n/a", "new": "no",
         "notes": "compiled kernels only"},
    ]
    for cmd in ("local", "global", "kp-info", "kp-finder", "gc-info", "gc-finder"):
        rows.append({"feature": cmd + " runs", "old": status_of("old", cmd),
                     "new": status_of("new", cmd), "notes": ""})
    return rows


def _write(path, rows, fields):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main(out):
    rows = load_raw(out)
    if not rows:
        raise SystemExit("no runs_raw_*.tsv under " + out)
    summ = summarise(rows)
    fields = list(KEY) + ["m", "density", "n_rep", "wall_median", "wall_mad", "wall_min", "wall_max",
                          "compute_median", "rss_median", "cpu_eff", "speedup_vs_old",
                          "compute_speedup_vs_old", "rss_ratio_vs_old", "status_summary"]
    ordered = sorted(summ.values(), key=lambda r: (r["cmd"], r["topology"], r["d"], r["weighted"],
                                                   r["k"], r["algorithm"], int(r["threads"] or 1),
                                                   int(r["n"] or 0), r["tool"]))
    _write(os.path.join(out, "summary.tsv"), ordered, fields)
    sc = scaling(summ)
    _write(os.path.join(out, "scaling.tsv"), sc,
           ["cmd", "tool", "topology", "n", "k", "algorithm", "weighted", "threads",
            "wall_median", "speedup_p", "efficiency_p"])
    _write(os.path.join(out, "capability.tsv"), capability(summ), ["feature", "old", "new", "notes"])
    print("summary.tsv: {} cells, scaling.tsv: {} rows".format(len(ordered), len(sc)))
