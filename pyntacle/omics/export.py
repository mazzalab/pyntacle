"""Write one group's network the way Pyntacle reads it.

The edge list's Weight is the signed partial correlation r itself, the
quantity the pipeline estimated. Pyntacle reads it with
`-w --weight-type signed`: |r| is the strength of the tie, 1/|r| the length
used by shortest-path metrics, and the sign is kept (see the "Edge weights"
page of the documentation).
"""
import os
import re

import igraph as ig
import numpy as np

# the command line that reads these networks with the intended semantics
PYNTACLE_FLAGS = "-w --weight-type signed"


def safe_name(label):
    return re.sub(r"[^a-z0-9]+", "_", str(label).lower()).strip("_") or "group"


def _attr(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    return str(v)


def write_network(edges, nodes, outdir, prefix, group):
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.join(outdir, "{}_{}".format(prefix, safe_name(group)))
    e = edges.copy()
    e["source"], e["target"] = e["source"].astype(str), e["target"].astype(str)
    e["abs_r"] = e["r"].astype(float).abs()
    e = e.sort_values(["source", "target"]).reset_index(drop=True)

    # significant digits, not decimals: a small r must never be written as 0,
    # which Pyntacle cannot tell from a missing edge
    e[["source", "target", "r"]].rename(
        columns={"source": "N1", "target": "N2", "r": "Weight"}).to_csv(
        stem + ".tsv", sep="\t", index=False, float_format="%.8g")

    names = sorted(set(e["source"]) | set(e["target"]))
    idx = {n: i for i, n in enumerate(names)}
    g = ig.Graph(n=len(names), edges=[(idx[a], idx[b]) for a, b in zip(e["source"], e["target"])])
    g.vs["name"] = names
    for col in nodes.columns:
        g.vs[col] = [_attr(v) for v in nodes[col].reindex(names)]
    g.es["assoc_weight"] = e["r"].astype(float).tolist()
    g.es["abs_r"] = e["abs_r"].tolist()
    if "q_value" in e.columns:
        g.es["q_value"] = e["q_value"].astype(float).tolist()
    g.write_graphml(stem + ".graphml")
    return {"edgelist": stem + ".tsv", "graphml": stem + ".graphml",
            "n_nodes": len(names), "n_edges": len(e)}
