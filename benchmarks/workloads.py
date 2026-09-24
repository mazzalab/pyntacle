"""Synthetic graph corpus for the old-vs-new benchmark.

Every graph is generated once from a fixed seed, reduced to its giant
component (the two tools treat isolates and small components differently,
which would make parity meaningless) and written as SIF with a header line,
the one format both tools read with the same defaults.

For each topology two files share the exact same edge set:

    <graph_id>.sif     node1 <tab> interacts <tab> node2
    <graph_id>_w.sif   same edges + a weight column, Uniform(0.1, 1.0)

The weighted file is only fed to the new tool: Pyntacle 1.3.2 has no
weighted shortest paths (its --weights flag only reaches PageRank).

A JSON sidecar (<graph_id>.json) records the real n and m after the
giant-component cut, so cells never have to re-read the graph to know them.
"""

import argparse
import json
import os
import random

import igraph as ig

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

TOPOLOGIES = ("er", "ba", "ws")


def graph_id(topology, n, m_per_node, seed):
    return "{}_n{}_d{}_s{}".format(topology, n, m_per_node, seed)


def _build(topology, n, m_per_node, seed):
    random.seed(seed)
    if topology == "er":
        g = ig.Graph.Erdos_Renyi(n=n, m=n * m_per_node)
    elif topology == "ba":
        g = ig.Graph.Barabasi(n=n, m=m_per_node)
    elif topology == "ws":
        g = ig.Graph.Watts_Strogatz(dim=1, size=n, nei=m_per_node, p=0.1)
    else:
        raise ValueError("unknown topology: " + topology)
    g.simplify()
    return g.connected_components().giant()


def ensure_graph(topology, n, m_per_node, seed=42, data_dir=DATA_DIR):
    """Return the metadata dict of a graph, generating its files if missing."""
    gid = graph_id(topology, n, m_per_node, seed)
    meta_path = os.path.join(data_dir, gid + ".json")
    if os.path.exists(meta_path):
        with open(meta_path) as fh:
            return json.load(fh)

    os.makedirs(data_dir, exist_ok=True)
    g = _build(topology, n, m_per_node, seed)
    width = len(str(g.vcount()))
    names = ["n" + str(i).zfill(width) for i in range(g.vcount())]
    rng = random.Random(seed + 1)
    edges = g.get_edgelist()

    sif = os.path.join(data_dir, gid + ".sif")
    sif_w = os.path.join(data_dir, gid + "_w.sif")
    # write under a private name and rename: shards on different nodes may
    # build the same graph at once on the shared filesystem
    tmp = ".{}.{}".format(os.getpid(), os.uname().nodename)
    with open(sif + tmp, "w") as plain, open(sif_w + tmp, "w") as weighted:
        plain.write("Node1\tInteraction\tNode2\n")
        weighted.write("Node1\tInteraction\tNode2\tweight\n")
        for s, t in edges:
            plain.write("{}\tinteracts\t{}\n".format(names[s], names[t]))
            weighted.write("{}\tinteracts\t{}\t{:.4f}\n".format(
                names[s], names[t], rng.uniform(0.1, 1.0)))

    # two nodes of the giant component, used by kp-info / gc-info cells
    probe = [names[0], names[g.vcount() // 2]]
    meta = {
        "graph_id": gid, "topology": topology, "n_requested": n,
        "m_per_node": m_per_node, "seed": seed,
        "n": g.vcount(), "m": g.ecount(),
        "density": round(2.0 * g.ecount() / (g.vcount() * (g.vcount() - 1)), 6),
        "sif": sif, "sif_weighted": sif_w, "probe_nodes": probe,
    }
    os.replace(sif + tmp, sif)
    os.replace(sif_w + tmp, sif_w)
    # the sidecar goes last: its presence is what marks the graph as complete
    with open(meta_path + tmp, "w") as fh:
        json.dump(meta, fh, indent=1)
    os.replace(meta_path + tmp, meta_path)
    return meta


def main():
    ap = argparse.ArgumentParser(description="Generate the benchmark graph corpus for a config.")
    ap.add_argument("config", help="benchmark config JSON")
    args = ap.parse_args()
    from matrix import load_config, graphs_of
    cfg = load_config(args.config)
    for topo, n, d in graphs_of(cfg):
        meta = ensure_graph(topo, n, d, cfg.get("seed", 42))
        print("{graph_id}\tn={n}\tm={m}".format(**meta))


if __name__ == "__main__":
    main()
