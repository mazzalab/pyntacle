"""Shared publication style for the benchmark figures (figures4papers house
style, scientific-figure-making skill): blue for Pyntacle 2, strong red for the
1.3.2 baseline, greys for guides; sans-serif 16 pt, no grid, open top/right
spines, frameless legends; every figure saved as PDF, SVG and 300 dpi PNG."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402

import matrix  # noqa: E402

PALETTE = {"blue_main": "#0F4D92", "blue_secondary": "#3775BA", "red_strong": "#B64342",
           "red_2": "#E9A6A1", "neutral": "#CFCECE", "grey": "#767676", "teal": "#42949E",
           "violet": "#9A4D8E"}
GUIDE = PALETTE["grey"]
COL = {"old": PALETTE["red_strong"], "new": PALETTE["blue_main"], "new-py": PALETTE["blue_secondary"]}
LAB = {"old": "Pyntacle 1.3.2", "new": "Pyntacle 2", "new-py": "Pyntacle 2, Python engine"}
MARK = {"old": "s", "new": "o", "new-py": "^"}
TOPO = {"er": "Erdős–Rényi", "ba": "Barabási–Albert", "ws": "Watts–Strogatz"}
CMD = {"local": "Local metrics", "global": "Global metrics", "kp-info": "Key-player scores",
       "gc-info": "Group-centrality scores", "kp-finder": "Key-player search",
       "gc-finder": "Group-centrality search"}

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16, "axes.linewidth": 2, "xtick.major.width": 2, "ytick.major.width": 2,
    "xtick.minor.width": 1.2, "ytick.minor.width": 1.2, "xtick.major.size": 6, "ytick.major.size": 6,
    "lines.linewidth": 2.5, "lines.markersize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "svg.fonttype": "none", "pdf.fonttype": 42, "ps.fonttype": 42,
})


def config_for(out):
    """The profile behind a results directory: results/<profile> was written
    by configs/<profile>.json."""
    name = os.path.basename(os.path.normpath(out))
    return matrix.load_config(os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs",
                                           name + ".json"))


def panel_label(ax, letter, x=-0.2):
    ax.text(x, 1.04, letter, transform=ax.transAxes, fontsize=22, fontweight="bold", va="bottom")


def nodes_formatter(v, _):
    return "{:g}k".format(v / 1000) if v >= 1000 else "{:g}".format(v)


def log_axes(ax, xticks, base=10):
    ax.set_xscale("log", base=base); ax.set_yscale("log")
    ax.set_xticks(xticks)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(nodes_formatter))
    ax.xaxis.set_minor_locator(mticker.NullLocator())


def save(fig, out, name):
    os.makedirs(os.path.join(out, "plots"), exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(os.path.join(out, "plots", name + "." + ext), dpi=300, bbox_inches="tight",
                    pad_inches=0.05)
    plt.close(fig)
    print("plots/" + name)
