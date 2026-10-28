"""paper-threads summary -> publication figures (PDF, SVG, PNG) in <out>/plots.

    python plot_threads.py results/paper-threads
"""
import os
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from figstyle import COL, LAB, MARK, TOPO, GUIDE, panel_label, log_axes, save, config_for

NEW = COL["new"]
CMD = {"kp-finder": "key-player search", "gc-finder": "group-centrality search"}
# stopped runs of different series at the same size are drawn side by side
JITTER = {"old": 0.93, "new": 1.07}


def load(out):
    s = pd.read_csv(os.path.join(out, "summary.tsv"), sep="\t")
    s = s[s.cmd != "startup"].copy()
    s["weighted"] = s.weighted.astype(str) == "True"
    grid = sorted({n for g in CONFIG["groups"] for n in g["n"]})
    # graphs keep their largest component: plot against the requested size
    s["N"] = s.n.map(lambda v: min(grid, key=lambda g: abs(g - v)))
    st = s.status_summary.fillna("")
    s["censored"] = st.str.contains("timeout|oom")
    return s


def fig_scaling(s, out, timeout):
    """Strong scaling: one fixed problem, 1 to 16 threads."""
    cases = [("kp-finder", 500), ("gc-finder", 200)]
    threads = [1, 2, 4, 8, 16]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for j, (cmd, n) in enumerate(cases):
        d = s[(s.cmd == cmd) & (s.algorithm == "brute_force") & (s.topology == "er")
              & (s.N == n) & (s.k == 2) & ~s.weighted & (s.threads.isin(threads))]
        top, bot = axes[0, j], axes[1, j]
        for tool in ("old", "new"):
            x = d[d.tool == tool].sort_values("threads")
            ok = x[x.wall_median.notna()]
            top.plot(ok.threads, ok.wall_median, marker=MARK[tool], color=COL[tool], label=LAB[tool])
            cens = x[x.censored]
            top.plot(cens.threads, [timeout] * len(cens), "x", color=COL[tool], ms=12, mew=2.5)
            if len(ok):
                # ideal scaling drawn from the smallest thread count measured
                t0, w0 = ok.threads.iloc[0], ok.wall_median.iloc[0]
                top.plot(threads, [w0 * t0 / t for t in threads], ":", color=COL[tool], lw=1.8)
                eff = w0 * t0 / (ok.wall_median * ok.threads)
                bot.plot(ok.threads, eff, marker=MARK[tool], color=COL[tool])
        top.axhline(timeout, color=GUIDE, lw=1.5, ls="--")
        log_axes(top, threads, base=2)
        top.set_title("{}\nErdős–Rényi, n = {}, k = 2".format(CMD[cmd].capitalize(), n))
        top.set_ylabel("wall time (s)")
        bot.set_xscale("log", base=2); bot.set_xticks(threads)
        bot.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: "{:g}".format(v)))
        bot.xaxis.set_minor_locator(mticker.NullLocator())
        bot.set_ylim(0, 1.08); bot.axhline(1, color=GUIDE, lw=1.5, ls=":")
        bot.set_xlabel("threads"); bot.set_ylabel("parallel efficiency")
        panel_label(top, "ab"[j]); panel_label(bot, "cd"[j])
    h = [plt.Line2D([], [], color=COL[t], marker=MARK[t], label=LAB[t]) for t in ("old", "new")]
    h += [plt.Line2D([], [], color=GUIDE, ls=":", lw=1.8, label="ideal scaling"),
          plt.Line2D([], [], color=GUIDE, ls="none", marker="x", ms=12, mew=2.5, label="timeout (1 h)")]
    fig.legend(handles=h, loc="upper center", ncol=4, bbox_to_anchor=(.5, 1.05))
    fig.tight_layout(pad=2)
    save(fig, out, "T1_strong_scaling")


def fig_size(s, out, timeout):
    """Brute force on 16 threads: how large a network each version handles."""
    panels = [("kp-finder", "er", 2), ("kp-finder", "ba", 2), ("kp-finder", "ws", 2), ("kp-finder", "er", 3),
              ("gc-finder", "er", 2), ("gc-finder", "ba", 2), ("gc-finder", "ws", 2), ("gc-finder", "er", 3)]
    fig, axes = plt.subplots(2, 4, figsize=(22, 10.5), sharey=True)
    for ax, (cmd, topo, k), letter in zip(axes.flat, panels, "abcdefgh"):
        d = s[(s.cmd == cmd) & (s.algorithm == "brute_force") & (s.threads == 16)
              & (s.topology == topo) & (s.k == k)]
        # the strong-scaling problem (n = 200, k = 2) is not part of the size series
        d = d[~((d.k == 2) & (d.N == 200))]
        for tool in ("old", "new"):
            for weighted, ls in ((False, "-"), (True, "--")):
                x = d[(d.tool == tool) & (d.weighted == weighted)].sort_values("N")
                if x.empty:
                    continue
                ok = x[x.wall_median.notna()]
                ax.plot(ok.N, ok.wall_median, ls, marker=MARK[tool], color=COL[tool],
                        mfc="white" if weighted else COL[tool])
                cens = x[x.censored]
                ax.plot(cens.N * JITTER[tool], [timeout] * len(cens), "x", color=COL[tool], ms=12, mew=2.5)
        ax.axhline(timeout, color=GUIDE, lw=1.5, ls="--")
        log_axes(ax, sorted(d.N.unique()))
        ax.set_title("{}\n{}, k = {}".format(CMD[cmd].capitalize(), TOPO[topo], k))
        if letter in "ae":
            ax.set_ylabel("wall time (s), 16 threads")
        if letter in "efgh":
            ax.set_xlabel("nodes")
        panel_label(ax, letter)
    h = [plt.Line2D([], [], color=COL[t], marker=MARK[t], label=LAB[t]) for t in ("old", "new")]
    h += [plt.Line2D([], [], color=NEW, marker="o", mfc="white", ls="--", label="Pyntacle 2, weighted"),
          plt.Line2D([], [], color=GUIDE, ls="none", marker="x", ms=12, mew=2.5, label="stopped: 1 h or 8 GB limit")]
    fig.legend(handles=h, loc="upper center", ncol=4, bbox_to_anchor=(.5, 1.04))
    fig.tight_layout(pad=2)
    save(fig, out, "T2_bruteforce_16_threads")


if __name__ == "__main__":
    out = sys.argv[1]
    CONFIG = config_for(out)
    timeout = CONFIG["timeout_s"]
    s = load(out)
    fig_scaling(s, out, timeout)
    fig_size(s, out, timeout)
