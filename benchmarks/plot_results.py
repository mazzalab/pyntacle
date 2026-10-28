"""summary.tsv -> publication figures (PDF, SVG, PNG) in <out>/plots.

    python plot_results.py results/paper
"""
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

from figstyle import PALETTE, COL, LAB, MARK, TOPO, CMD, GUIDE, panel_label, log_axes, save, config_for

LETTERS = "abcdefghijklmnopqrstuvwxyz"
JITTER = {"old": 0.93, "new": 1.07}
KEY = ["cmd", "topology", "n", "d", "weighted", "k", "algorithm", "threads"]


def load(out):
    s = pd.read_csv(os.path.join(out, "summary.tsv"), sep="\t")
    s = s[s.cmd != "startup"].copy()
    s["weighted"] = s.weighted.astype(str) == "True"
    # graphs keep their largest component, so n can fall a little short of
    # the requested size: plot against the requested one
    grid = sorted({n for g in CONFIG["groups"] for n in g["n"]})
    s["N"] = s.n.map(lambda v: min(grid, key=lambda g: abs(g - v)))
    st = s.status_summary.fillna("")
    s["censored"] = st.str.contains("timeout|oom")
    return s


def pairs(s, timeout):
    """Unweighted cells run by both versions, one row each. Where 1.3.2 stopped
    at the time limit (or was not run because a smaller network already had)
    and Pyntacle 2 finished, the limit stands in for the 1.3.2 time and the
    speedup is a lower bound."""
    k = [c for c in KEY if c != "n"] + ["N"]
    new = s[(s.tool == "new") & ~s.weighted].copy()
    old = s[(s.tool == "old") & ~s.weighted].copy()
    old["stopped"] = old.status_summary.fillna("").str.contains("timeout|oom|skipped")
    for d in (new, old):
        d[k] = d[k].astype(str)
    p = new.merge(old[k + ["wall_median", "rss_median", "stopped"]], on=k, suffixes=("", "_old"))
    p = p[p.wall_median.notna() & (p.wall_median_old.notna() | p.stopped)].copy()
    p["bound"] = p.wall_median_old.isna()
    p["old_wall"] = p.wall_median_old.fillna(timeout)
    p["speedup"] = p.old_wall / p.wall_median
    p["N"] = p.N.astype(float)
    p["algorithm"] = p.algorithm.replace("nan", np.nan)
    p["k"] = pd.to_numeric(p.k, errors="coerce")
    p["d"] = p.d.astype(float)
    return p


def line(ax, d, tool, weighted=False, y="wall_median", timeout=None):
    d = d[(d.tool == tool) & (d.weighted == weighted)].sort_values("N")
    ok = d[d[y].notna()]
    ax.plot(ok.N, ok[y], "--" if weighted else "-", marker=MARK[tool], color=COL[tool],
            mfc="white" if weighted else COL[tool])
    cens = d[d.censored]
    if timeout and len(cens):
        # the two versions' markers sit side by side when both hit the limit
        ax.plot(cens.N * JITTER[tool], [timeout] * len(cens), "x", color=COL[tool], ms=12, mew=2.5)


def fold(ax, d, y, word):
    """Mark 1.3.2 over Pyntacle 2 at the largest network both measured: an arrow
    joins the two points and the ratio sits to its right, clear of the lines."""
    o = d[(d.tool == "old") & ~d.weighted & d[y].notna()].set_index("N")[y]
    n = d[(d.tool == "new") & ~d.weighted & d[y].notna()].set_index("N")[y]
    both = o.index.intersection(n.index)
    if not len(both):
        return
    x = both.max()
    ax.annotate("", (x, n[x]), (x, o[x]), arrowprops=dict(arrowstyle="<->", color=COL["new"], lw=1.8,
                                                          shrinkA=8, shrinkB=8))
    text = "{:.1f}×\n{}".format(o[x] / n[x], word)
    style = dict(textcoords="offset points", ha="left", fontsize=14, color=COL["new"], fontweight="bold")
    if n.index.max() == x:
        # nothing to the right of the last size: widen the axis and write there
        lo, hi = ax.get_xlim()
        ax.set_xlim(lo, x * 2.6)
        ax.annotate(text, (x, (o[x] * n[x]) ** .5), xytext=(12, 0), va="center", **style)
    else:
        # Pyntacle 2 rises to the right: write below its point
        ax.annotate(text, (x, n[x]), xytext=(10, -12), va="top", **style)


def bar_legend(fig, y):
    h = [plt.Rectangle((0, 0), 1, 1, facecolor=COL[t], edgecolor="black", linewidth=1.2, label=LAB[t])
         for t in ("old", "new")]
    fig.legend(handles=h, loc="upper center", ncol=2, bbox_to_anchor=(.5, y))


def timeout_line(ax, timeout):
    ax.axhline(timeout, color=GUIDE, lw=1.5, ls="--")


def legend(fig, tools, weighted=True, timeout=True, y=1.04, ncol=None):
    h = [plt.Line2D([], [], color=COL[t], marker=MARK[t], label=LAB[t]) for t in tools]
    if weighted:
        h.append(plt.Line2D([], [], color=COL["new"], marker="o", mfc="white", ls="--",
                            label="Pyntacle 2, weighted"))
    if timeout:
        h.append(plt.Line2D([], [], color=GUIDE, ls="none", marker="x", ms=12, mew=2.5,
                            label="stopped at the 1 h limit"))
    fig.legend(handles=h, loc="upper center", ncol=ncol or len(h), bbox_to_anchor=(.5, y))


def fig_metrics(s, out, timeout):
    """Whole-network commands: wall time against size, per topology."""
    cmds = ["local", "global", "kp-info", "gc-info"]
    fig, axes = plt.subplots(len(cmds), 3, figsize=(17, 19), sharex=True)
    base = s[(s.d == 3) & s.cmd.isin(cmds) & s.algorithm.isna()]
    for i, cmd in enumerate(cmds):
        for j, topo in enumerate(TOPO):
            ax = axes[i, j]
            d = base[(base.cmd == cmd) & (base.topology == topo)]
            for tool in ("old", "new"):
                line(ax, d, tool, timeout=timeout)
            line(ax, d, "new", weighted=True, timeout=timeout)
            timeout_line(ax, timeout)
            log_axes(ax, sorted(d.N.unique()))
            if i == 0:
                ax.set_title(TOPO[topo], pad=14)
            if j == 0:
                ax.set_ylabel("{}\nwall time (s)".format(CMD[cmd]))
            if i == len(cmds) - 1:
                # d is the number of edges added per node: the mean degree is 2d
                ax.set_xlabel("nodes (mean degree 6)")
            panel_label(ax, LETTERS[3 * i + j], x=-0.24 if j == 0 else -0.16)
    axes[3, 0].text(.38, .72, "1.3.2 gr-info fails\non every input", transform=axes[3, 0].transAxes,
                    ha="center", va="center", fontsize=14, color=COL["old"])
    legend(fig, ("old", "new"), y=1.02)
    fig.tight_layout(pad=2)
    save(fig, out, "1_metrics_scaling")


def fig_memory(s, out):
    cmds = ["local", "global", "kp-info"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), sharey=True)
    base = s[(s.d == 3) & s.algorithm.isna() & ~s.weighted & (s.topology == "ba")]
    for ax, cmd, letter in zip(axes, cmds, "abc"):
        d = base[base.cmd == cmd]
        for tool in ("old", "new"):
            line(ax, d, tool, y="rss_median")
        log_axes(ax, sorted(d.N.unique()))
        fold(ax, d, "rss_median", "less")
        ax.set_title(CMD[cmd]); ax.set_xlabel("nodes (Barabási–Albert)")
        panel_label(ax, letter)
    axes[0].set_ylabel("peak memory (MB)")
    legend(fig, ("old", "new"), weighted=False, timeout=False, y=1.1)
    fig.tight_layout(pad=2)
    save(fig, out, "2_memory")


def fig_bruteforce(s, out, timeout):
    """Exhaustive search on one thread: how large a network each version handles."""
    panels = [("er", 2), ("ba", 2), ("ws", 2), ("er", 3)]
    fig, axes = plt.subplots(2, 4, figsize=(22, 10.5), sharey=True)
    for i, cmd in enumerate(("kp-finder", "gc-finder")):
        bf = s[(s.cmd == cmd) & (s.algorithm == "brute_force")]
        for j, (topo, k) in enumerate(panels):
            ax = axes[i, j]
            d = bf[(bf.topology == topo) & (bf.k == k)]
            for tool in ("old", "new"):
                line(ax, d, tool, timeout=timeout)
            line(ax, d, "new", weighted=True, timeout=timeout)
            timeout_line(ax, timeout)
            log_axes(ax, sorted(d.N.unique()))
            ax.set_title("{}\n{}, k = {}".format(CMD[cmd], TOPO[topo], k))
            if i == 1:
                ax.set_xlabel("nodes")
            panel_label(ax, LETTERS[4 * i + j])
        axes[i, 0].set_ylabel("wall time (s), 1 thread")
    legend(fig, ("old", "new"), y=1.04)
    fig.tight_layout(pad=2)
    save(fig, out, "3_bruteforce")


def fig_greedy(s, out, timeout):
    fig, axes = plt.subplots(2, 3, figsize=(17, 10.5), sharex=True, sharey=True)
    for i, cmd in enumerate(("kp-finder", "gc-finder")):
        g = s[(s.cmd == cmd) & (s.algorithm == "greedy") & (s.topology == "ba")]
        for j, k in enumerate((2, 3, 4)):
            ax = axes[i, j]
            d = g[g.k == k]
            for tool in ("old", "new"):
                line(ax, d, tool, timeout=timeout)
            timeout_line(ax, timeout)
            log_axes(ax, sorted(g.N.unique()))
            ax.set_title("{}\ngreedy, k = {}".format(CMD[cmd], k))
            if i == 1:
                ax.set_xlabel("nodes (Barabási–Albert)")
            panel_label(ax, LETTERS[3 * i + j])
        axes[i, 0].set_ylabel("wall time (s)")
    legend(fig, ("old", "new"), weighted=False, y=1.04)
    fig.tight_layout(pad=2)
    save(fig, out, "4_greedy")


def fig_speedup(s, out, timeout):
    """Median speedup of Pyntacle 2 over 1.3.2 per command and size, unweighted;
    cells where 1.3.2 hit the time limit on some topology show a lower bound."""
    v = pairs(s, timeout)
    v = v[v.d == 3]
    v["row"] = np.where(v.algorithm.isna(), v.cmd.map(CMD),
                        v.cmd.map(CMD) + ", " + v.algorithm.str.replace("_", " ").fillna("")
                        + ", k = " + v.k.fillna(0).astype(int).astype(str))
    t = v.pivot_table(index="row", columns="N", values="speedup", aggfunc="median")
    bound = v.pivot_table(index="row", columns="N", values="bound", aggfunc="any")
    order = [CMD["local"], CMD["global"], CMD["kp-info"]]
    order += ["{}, {}, k = {}".format(CMD[c], a, k) for c in ("kp-finder", "gc-finder")
              for a, ks in (("brute force", (2, 3)), ("greedy", (2, 3, 4))) for k in ks]
    t = t.loc[[r for r in order if r in t.index]]
    t = t.loc[:, t.notna().any()]
    bound = bound.reindex(index=t.index, columns=t.columns).fillna(False).astype(bool)
    # every cell is a gain: white at 1x, blue as it grows
    cmap = LinearSegmentedColormap.from_list("speedup", ["#FFFFFF", PALETTE["blue_main"]])
    fig, ax = plt.subplots(figsize=(15, 9))
    data = np.log2(t.values.astype(float))
    lim = np.nanmax(data)
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=lim, aspect="auto")
    for (r, c), val in np.ndenumerate(t.values):
        if not np.isnan(val):
            text = "{:.1f}×".format(val) if val < 10 else "{:.0f}×".format(val)
            if bound.iat[r, c]:
                # a bound under 2x says little more than that 1.3.2 did not finish
                text = "≥" + text if val >= 2 else "1.3.2\n>1 h"
                ax.add_patch(plt.Rectangle((c - .5, r - .5), 1, 1, fill=False, hatch="//",
                                           edgecolor=GUIDE, linewidth=0, alpha=.45))
            ax.text(c, r, text, ha="center", va="center", fontsize=13,
                    color="white" if np.log2(val) > lim * .55 else "black")
    ax.set_xticks(range(len(t.columns)))
    ax.set_xticklabels(["{:g}k".format(c / 1000) if c >= 1000 else "{:g}".format(c) for c in t.columns])
    ax.set_yticks(range(len(t.index))); ax.set_yticklabels(t.index)
    ax.set_xlabel("nodes")
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, shrink=.8, pad=.02)
    ticks = [x for x in (0, 1, 2, 4, 6, 8, 10) if x <= lim]
    cb.set_ticks(ticks); cb.set_ticklabels(["{:g}×".format(2 ** x) for x in ticks])
    cb.set_label("speedup over 1.3.2 (median of three topologies)")
    cb.outline.set_visible(False)
    fig.tight_layout(pad=2)
    save(fig, out, "5_speedup_heatmap")


def fig_density(s, out):
    cmds = ("local", "global", "kp-info")
    d = s[(s.topology == "er") & (s.N == 2000) & s.algorithm.isna() & ~s.weighted
          & s.cmd.isin(cmds) & s.tool.isin(["old", "new"])]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8))
    for ax, cmd, letter in zip(axes, cmds, "abc"):
        x = d[d.cmd == cmd]
        degs = sorted(x.d.unique())
        ys = {}
        for o, tool in enumerate(("old", "new")):
            ys[tool] = [x[(x.d == g) & (x.tool == tool)].wall_median.median() for g in degs]
            ax.bar(np.arange(len(degs)) + (o - .5) * .38, ys[tool], .38, color=COL[tool],
                   edgecolor="black", linewidth=1.2, label=LAB[tool])
        for i, (a, b) in enumerate(zip(ys["old"], ys["new"])):
            ax.text(i, a * 1.03, ("{:.1f}×" if a / b < 10 else "{:.0f}×").format(a / b), ha="center", va="bottom", fontsize=14,
                    color=COL["new"], fontweight="bold")
        ax.set_ylim(0, max(ys["old"]) * 1.15)
        ax.set_xticks(range(len(degs))); ax.set_xticklabels(["{:g}".format(2 * g) for g in degs])
        ax.set_xlabel("mean degree")
        ax.set_title("{}\nErdős–Rényi, 2000 nodes".format(CMD[cmd]))
        panel_label(ax, letter)
    axes[0].set_ylabel("wall time (s)")
    bar_legend(fig, y=1.12)
    fig.tight_layout(pad=2)
    save(fig, out, "6_density")


if __name__ == "__main__":
    out = sys.argv[1]
    CONFIG = config_for(out)
    timeout = CONFIG["timeout_s"]
    s = load(out)
    fig_metrics(s, out, timeout)
    fig_memory(s, out)
    fig_bruteforce(s, out, timeout)
    fig_greedy(s, out, timeout)
    fig_speedup(s, out, timeout)
    fig_density(s, out)
