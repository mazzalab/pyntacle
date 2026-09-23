############### PERCOLATION

from igraph import Graph
import numpy as np
import pandas as pd
from colorama import Fore, Style
import math
import json
from plotly import graph_objs as go
import plotly.io as pio
from collections import deque

# Colors (same semantics as your notebook)
COL_S   = "#bdbdbd"   # susceptible
COL_I   = "#FFD700"   # infected
COL_R   = "#2ca02c"   # recovered
COL_USED= "#d62728"   # used edges
COL_BASE= "#bbbbbb"   # base edges

# Threshold for using KK layout vs a faster layout for large graphs
LAYOUT_KK_THRESHOLD = 1000  # use KK if N <= 1000, otherwise use a faster layout


# ---------- Parameter validation ----------

def _validate_percolation_params(
    graph,
    Pstar,
    tau,
    seed_node,
    pth_max,
    dist,
    tau_dist,
    max_steps,
    use_edge_weights_as_pth=False,
    tau_vector=None,
    snapshot_infected=None,
):
    """
    Basic validation for percolation parameters.
    Raises ValueError / TypeError on invalid inputs.
    """

    # graph check (very light)
    if not hasattr(graph, "get_adjacency"):
        raise TypeError(
            u"Invalid graph object: expected an igraph.Graph or Graphtacle-like "
            u"object with a 'get_adjacency()' method."
        )

    # we need n_nodes for several checks
    if hasattr(graph, "iNodes"):
        n_nodes = len(graph.iNodes)
    else:
        n_nodes = graph.vcount()

    # Pstar
    if not isinstance(Pstar, (int, float, np.number)):
        raise TypeError(u"P* must be a numeric value.")
    if Pstar < 0.0 or Pstar > 1.0:
        raise ValueError(u"P* must be in the range [0, 1].")

    # tau (still validated even if tau_vector is provided, for consistency)
    if not isinstance(tau, (int, float, np.number)):
        raise TypeError(u"Tau must be a numeric value.")
    if tau <= 0:
        raise ValueError(u"Tau (recovery time) must be > 0.")

    # pth_max (only relevant if we are NOT using edge weights as thresholds)
    if not isinstance(pth_max, (int, float, np.number)):
        raise TypeError(u"p_th,max must be a numeric value.")
    if pth_max < 0.0 or pth_max > 1.0:
        raise ValueError(u"p_th,max must be in the range [0, 1].")

    # distribution for edge thresholds
    valid_dist = {"uniform", "normal", "bimodal"}
    if dist not in valid_dist:
        raise TypeError(
            u"Unknown distribution '{dist}'. Select the right option: uniform | normal | bimodal"
            .format(dist=dist)
        )

    # distribution for tau (recovery time)
    valid_tau_dist = {"fixed", "uniform", "normal", "bimodal"}
    if tau_dist not in valid_tau_dist:
        raise TypeError(
            u"Unknown tau distribution '{tau_dist}'. "
            u"Select the right option: fixed | uniform | normal | bimodal"
            .format(tau_dist=tau_dist)
        )

    # max_steps
    if max_steps is not None:
        if not isinstance(max_steps, (int, np.integer)):
            raise TypeError(u"max_steps must be an integer or None.")
        if max_steps <= 0:
            raise ValueError(u"max_steps must be >= 1.")

    # snapshot_infected (trigger for the single-state snapshot report)
    if snapshot_infected is not None:
        if not isinstance(snapshot_infected, (int, np.integer)):
            raise TypeError(u"snapshotInfected must be an integer or None.")
        if snapshot_infected <= 0:
            raise ValueError(u"snapshotInfected must be >= 1.")

    # seed_node index (if int) – list/labels handled later in run_percolation
    if seed_node is not None and isinstance(seed_node, int):
        if seed_node < 0 or seed_node >= n_nodes:
            raise ValueError(
                u"Seed node index out of range. "
                u"Valid range is [0, {max_idx}] (0-based indices)."
                .format(max_idx=n_nodes - 1)
            )

    # per-node tau vector, if provided
    if tau_vector is not None:
        arr = np.asarray(tau_vector, dtype=float)
        if arr.ndim != 1:
            raise ValueError(
                u"tau_vector must be a 1D array-like of per-node recovery times."
            )
        if len(arr) != n_nodes:
            raise ValueError(
                u"Length of tau_vector ({lv}) does not match number of nodes ({n})."
                .format(lv=len(arr), n=n_nodes)
            )
        if np.any(arr <= 0):
            raise ValueError(
                u"All recovery times in tau_vector must be > 0."
            )

    # if we want to interpret edge weights as thresholds p_th,ij
    if use_edge_weights_as_pth:
        # the graph must actually have edge weights
        if "weight" not in graph.es.attribute_names():
            raise ValueError(
                u"use_edge_weights_as_pth=True but the graph has no 'weight' edge attribute."
            )

        weights = graph.es["weight"]
        if len(weights) != graph.ecount():
            raise ValueError(
                u"Length of graph.es['weight'] does not match number of edges."
            )

        # check that weights are numeric and in [0,1]
        bad_idx = []
        for idx, w in enumerate(weights):
            try:
                w_f = float(w)
            except (TypeError, ValueError):
                bad_idx.append(idx)
                continue
            if w_f < 0.0 or w_f > 1.0 or math.isnan(w_f):
                bad_idx.append(idx)

        if bad_idx:
            raise ValueError(
                u"Edge weights used as thresholds must be numeric in [0,1] and not NaN. "
                u"Found invalid values on edges indices: {bad}"
                .format(bad=",".join(str(i) for i in bad_idx))
            )

        # if we use edge weights as thresholds, pth_max / dist are conceptually disabled.
        # we enforce that they are at default values (pth_max=1, dist='uniform').
        if not (math.isclose(float(pth_max), 1.0) and dist == "uniform"):
            raise ValueError(
                u"When using a weighted graph as local thresholds p_th,ij, -pth and -dist "
                u"must NOT be used. Please do not override pth_max or pthDistribution."
            )


# ---------- Threshold sampling ----------

def _sample_single_threshold(pth_max, dist, rng):
    """
    Sample a single local threshold p_th,ij in [0, pth_max] according to the
    chosen distribution.
    """
    if pth_max <= 0:
        return 0.0

    if dist == "uniform":
        return float(rng.uniform(0.0, pth_max))

    elif dist == "normal":
        # Normal around pth_max/2, truncated to [0, pth_max]
        mean = pth_max / 2.0
        std = pth_max / 6.0 if pth_max > 0 else 1.0
        value = mean
        # simple rejection sampling
        for _ in range(10):
            candidate = rng.normal(mean, std)
            if 0.0 <= candidate <= pth_max:
                value = candidate
                break
        # clip just in case
        return float(min(max(value, 0.0), pth_max))

    elif dist == "bimodal":
        # Half "easy" (low threshold), half "hard" (high threshold)
        if rng.random() < 0.5:
            # easy group, thresholds near 0
            return float(rng.uniform(0.0, pth_max / 3.0))
        else:
            # hard group, thresholds near pth_max
            return float(rng.uniform(2.0 * pth_max / 3.0, pth_max))

    else:
        # Should never happen if _validate_percolation_params is used,
        # but we keep it defensive.
        raise TypeError(
            u"Unknown distribution '{dist}'. Select the right option: uniform | normal | bimodal"
            .format(dist=dist)
        )


def _sample_edge_thresholds_matrix(graph, pth_max=1.0, dist="uniform", rng=None):
    """
    Samples a local threshold p_th,ij for every edge, drawing from the
    chosen distribution.

    Returns a length-E array aligned to graph.get_edgelist(), not a dense
    (n, n) matrix: a dense matrix costs O(n^2) regardless of how sparse the
    graph is, which is the memory wall this module used to reintroduce.

    Parameters
    ----------
    graph : igraph.Graph (or Graphtacle)
    pth_max : float
        Maximum value of the local threshold; each p_th,ij is in [0, pth_max].
    dist : {"uniform", "normal", "bimodal"}
        Distribution used to sample the thresholds.
    rng : np.random.Generator or None
        Random generator; if None, a default generator is created.

    Returns
    -------
    edge_pth : np.ndarray, shape (E,)
        edge_pth[e] = p_th,ij for the e-th edge of graph.get_edgelist().
    """
    if rng is None:
        rng = np.random.default_rng()

    edges = graph.get_edgelist()
    return np.array(
        [_sample_single_threshold(pth_max, dist, rng) for _ in edges],
        dtype=float,
    )


def _edge_thresholds_from_weights(graph):
    """
    Build a length-E array of local thresholds p_th,ij using the edge
    attribute 'weight' as p_th,ij (assumed numeric in [0,1]), aligned to
    graph.get_edgelist() (igraph already stores es["weight"] in that order).
    """
    return np.array([float(w) for w in graph.es["weight"]], dtype=float)


# ---------- Tau sampling (per-node recovery times) ----------

def _sample_single_tau(tau_max, tau_dist, rng):
    """
    Sample a single recovery time τ in (0, tau_max], according to tau_dist.
    """
    if tau_max <= 0:
        # should not happen after validation, but keep it safe
        return 1.0

    if tau_dist == "fixed":
        return float(tau_max)

    # reuse the threshold sampler: it works on [0, max] generically
    t = _sample_single_threshold(tau_max, tau_dist, rng)
    if t <= 0:
        t = 1.0
    return float(t)


def _sample_tau_vector(n_nodes, tau, tau_dist, rng):
    """
    If tau_dist != 'fixed', samples a per-node recovery time τ_i.
    If tau_dist == 'fixed', returns None (use scalar tau everywhere).
    """
    if tau_dist == "fixed":
        return None

    tau_max = float(tau)
    if tau_max <= 0:
        tau_max = 1.0

    tau_vec = np.zeros(n_nodes, dtype=float)
    for i in range(n_nodes):
        tau_vec[i] = _sample_single_tau(tau_max, tau_dist, rng)
    return tau_vec


# ---------- Open-edge adjacency ----------

def _build_open_neighbors(n_nodes, edges, open_mask, directed):
    """
    Adjacency list restricted to OPEN edges: neighbors[u] holds every node
    reachable from u through an edge e with open_mask[e] == True.

    Built in O(V + E) from the edge list. Replaces the old
    open_neighbors = [np.where(open_edges[u, :])[0] for u in range(n)],
    an O(n^2) scan over a dense (n, n) matrix regardless of how sparse the
    graph actually is.
    """
    neighbors = [[] for _ in range(n_nodes)]
    for (i, j), is_open in zip(edges, open_mask):
        if not is_open:
            continue
        neighbors[i].append(j)
        if not directed and i != j:
            neighbors[j].append(i)
    return [np.asarray(lst, dtype=int) for lst in neighbors]


# ---------- Core percolation dynamics ----------

def run_percolation(
    graph,
    Pstar,
    tau=4,
    tau_dist="fixed",
    seed_node=None,
    pth_max=1.0,
    dist="uniform",
    max_steps=None,
    verbose=False,
    use_edge_weights_as_pth=False,
    tau_vector=None,
    snapshot_infected=None,
    snapshot_node=None,
):
    """
    Simulates a percolation / epidemic-like dynamics on a graph.

    Node states:
        0 = susceptible
        1 = active / infected
        2 = recovered

    Rule of transmission for each edge (i,j):
        the edge is "open" if  P* >= p_th,ij
        that is A*_ij = 1 if P* >= p_th,ij, otherwise A*_ij = 0.

    Dynamics:
        - Start from one or more seeds s at t = 0 (state 1).
        - At each step, active nodes try to infect neighbors through
          "open" edges.
        - A node remains active for τ steps (possibly τ_i if distributed
          or read from file), then becomes recovered.

    Parameters
    ----------
    graph : igraph.Graph (or subclass Graphtacle)
        Input graph.
    Pstar : float
        Global percolation probability P* in [0, 1].
    tau : float
        Recovery time parameter.
        If tau_dist == "fixed" and tau_vector is None:
            single global recovery time (steps).
        If tau_dist != "fixed" and tau_vector is None:
            interpreted as τ_max, the upper bound of a distribution used to
            draw per-node τ_i in (0, τ_max].
        If tau_vector is not None:
            per-node recovery time τ_i is taken from this vector and
            tau_dist is ignored in the actual dynamics.
    tau_dist : {"fixed", "uniform", "normal", "bimodal"}
        How to handle τ when tau_vector is None:
          - "fixed"   → use the same τ for all nodes.
          - otherwise → draw a per-node τ_i from the chosen distribution
                        in (0, tau] for each node.
    seed_node :
        - None → one random seed
        - int  → single node index
        - str  → single node label
        - comma-separated str → multiple labels, e.g. "EE,BR"
        - list/tuple/set/ndarray of ints and/or labels
    pth_max : float
        Maximum value of local threshold p_th in [0, 1] (only used when
        use_edge_weights_as_pth=False).
    dist : {"uniform", "normal", "bimodal"}
        Distribution for local thresholds p_th,ij (only used when
        use_edge_weights_as_pth=False).
    max_steps : int or None
        Maximum number of simulation steps.
        If None, max(1, num_nodes) is used.
    verbose : bool
        If True, prints some optional info (no warnings here).
    use_edge_weights_as_pth : bool
        If True, interpret the edge attribute 'weight' as fixed local
        thresholds p_th,ij in [0,1]. In this case, pth_max and dist must
        be left at their default values (1.0, 'uniform').
    tau_vector : array-like or None
        If provided, defines per-node recovery times τ_i directly.
        Length must equal number of nodes and all values must be > 0.
    snapshot_infected : int or None
        If provided, capture the full per-node state vector the first time
        the number of currently-infected nodes reaches this value.
    snapshot_node : str or None
        If provided (a node label, or a 0-based index given as a string),
        capture the full per-node state vector at the exact step this node
        becomes infected. If both snapshot_infected and snapshot_node are
        given, whichever condition is met first wins (only one snapshot is
        ever kept).

    Returns
    -------
    results : dict
        {
          "Pstar": float,
          "tau": float,
          "tau_distribution": str,
          "tau_vector": np.ndarray or None,
          "pth_max": float,
          "distribution": str,
          "edge_threshold_source": str,  # "sampled" or "edge_weights"
          "seed_index": int,        # first seed (for backward compat)
          "seed_indices": list[int],
          "seed_label": hashable,   # label of first seed
          "seed_labels": list,
          "node_labels": list,
          "edges": list[tuple[int, int]],  # graph.get_edgelist(), aligned to the two arrays below
          "edge_thresholds": np.ndarray, shape (E,),
          "open_edges": np.ndarray, shape (E,), bool,
          "n_steps": int,                       # simulated steps, excluding t=0
          "snapshot_state": np.ndarray or None,  # per-node state at snapshot_time
          "snapshot_time": int or None,
          "active_counts": list[int],
          "susceptible_counts": list[int],
          "recovered_counts": list[int],
          "activation_time": np.ndarray, shape (n,),
          "recovery_time": np.ndarray, shape (n,),
          "infection_edges": dict[frozenset, float]  # u-v edges with infection time
        }
    """
    rng = np.random.default_rng()

    # validate parameters (raises early if something is wrong)
    _validate_percolation_params(
        graph=graph,
        Pstar=Pstar,
        tau=tau,
        seed_node=seed_node,
        pth_max=pth_max,
        dist=dist,
        tau_dist=tau_dist,
        max_steps=max_steps,
        use_edge_weights_as_pth=use_edge_weights_as_pth,
        tau_vector=tau_vector,
        snapshot_infected=snapshot_infected,
    )

    # number of nodes (compatible with Graphtacle)
    if hasattr(graph, "iNodes"):
        n_nodes = len(graph.iNodes)
    else:
        n_nodes = graph.vcount()

    if n_nodes == 0:
        raise ValueError(u"Input graph has no nodes (vcount == 0).")

    # node labels
    if "label" in graph.vs.attribute_names():
        node_labels = list(graph.vs["label"])
    else:
        node_labels = list(range(graph.vcount()))

    # edge list (fixed order; edge_thresholds/open_edges/open_neighbors below
    # are all aligned to it -- no dense (n, n) adjacency is ever built here).
    edges = graph.get_edgelist()

    # local thresholds for each edge -- length-E array, see
    # _sample_edge_thresholds_matrix / _edge_thresholds_from_weights.
    if use_edge_weights_as_pth:
        edge_pth = _edge_thresholds_from_weights(graph)
        edge_threshold_source = "edge_weights"
    else:
        edge_pth = _sample_edge_thresholds_matrix(graph, pth_max=pth_max, dist=dist, rng=rng)
        edge_threshold_source = "sampled"

    # open edges: True if P* >= p_th,ij, one flag per edge (NaN -> False)
    open_edges = (Pstar >= edge_pth)

    # adjacency list restricted to open edges, built in O(V+E).
    open_neighbors = _build_open_neighbors(n_nodes, edges, open_edges, graph.is_directed())

    # per-node tau
    if tau_vector is not None:
        tau_vec_used = np.asarray(tau_vector, dtype=float)
        tau_dist_effective = "per-node-fixed"
    else:
        tau_vec_used = _sample_tau_vector(n_nodes, tau, tau_dist, rng)
        tau_dist_effective = tau_dist

    # ---------- seed handling (supports multiple seeds) ----------
    def _index_from_label(label):
        try:
            return node_labels.index(label)
        except ValueError:
            raise ValueError(
                u"Seed node '{seed}' not found among node labels."
                .format(seed=label)
            )

    if seed_node is None:
        # single random seed
        seeds_idx = [int(rng.integers(0, n_nodes))]
    else:
        seeds_idx = []

        # single int index
        if isinstance(seed_node, int):
            if seed_node < 0 or seed_node >= n_nodes:
                raise ValueError(
                    u"Seed node index out of range. "
                    u"Valid range is [0, {max_idx}] (0-based indices)."
                    .format(max_idx=n_nodes - 1)
                )
            seeds_idx = [seed_node]

        # string: either single label or "A,B,C"
        elif isinstance(seed_node, str):
            if "," in seed_node:
                parts = [s.strip() for s in seed_node.split(",") if s.strip()]
                if not parts:
                    raise ValueError(
                        u"Seed node string is empty after splitting on comma."
                    )
                for lab in parts:
                    seeds_idx.append(_index_from_label(lab))
            else:
                seeds_idx = [_index_from_label(seed_node)]

        # iterable of ints/labels
        elif isinstance(seed_node, (list, tuple, set, np.ndarray)):
            not_found = []
            out_of_range = []
            for s in seed_node:
                if isinstance(s, int):
                    if 0 <= s < n_nodes:
                        seeds_idx.append(int(s))
                    else:
                        out_of_range.append(s)
                else:
                    try:
                        idx = node_labels.index(s)
                        seeds_idx.append(idx)
                    except ValueError:
                        not_found.append(s)
            if out_of_range:
                raise ValueError(
                    u"One or more seed node indices out of range: {bad}. "
                    u"Valid range is [0, {max_idx}] (0-based indices)."
                    .format(
                        bad=",".join(str(x) for x in out_of_range),
                        max_idx=n_nodes - 1,
                    )
                )
            if not_found:
                raise ValueError(
                    u"Seed node(s) {bad} not found among node labels."
                    .format(bad=",".join(str(x) for x in not_found))
                )

        else:
            raise TypeError(
                u"seed_node must be None, int, str, or an iterable of ints/labels; "
                u"got type {t}".format(t=type(seed_node))
            )

    # deduplicate & sort seeds
    seeds_idx = sorted(set(seeds_idx))
    if len(seeds_idx) == 0:
        raise ValueError(u"No valid seed nodes were provided.")

    # node states: 0 = S, 1 = I, 2 = R
    state = np.zeros(n_nodes, dtype=int)
    active_time = np.zeros(n_nodes, dtype=int)

    # activation / recovery times (NaN if never activated / never recovered)
    activation_time = np.full(n_nodes, np.nan)
    recovery_time = np.full(n_nodes, np.nan)

    # set all seeds as infected at t=0
    state[seeds_idx] = 1
    active_time[seeds_idx] = 0
    activation_time[seeds_idx] = 0

    # maximum number of steps
    if max_steps is None:
        max_steps = max(1, n_nodes)

    # resolve the (at most one) node whose activation should trigger
    # snapshot_node, once, before the loop.
    snap_node_idx = None
    if snapshot_node is not None:
        try:
            snap_node_idx = node_labels.index(snapshot_node)
        except ValueError:
            snap_node_idx = int(snapshot_node)

    # time series -- counts only, O(1) work per step.
    active_counts = []
    susceptible_counts = []
    recovered_counts = []

    # At most ONE full per-node state vector is ever kept: the single
    # snapshot the caller asked for (if any), captured the moment its
    # trigger fires. The old code appended state.copy() (O(n)) every step
    # into a growing states_over_time list -- O(n) * O(max_steps), i.e. the
    # same O(n^2)-at-scale wall this module reintroduced on the adjacency
    # side, just from a different array. Nothing downstream actually needed
    # the full history: only the step count (n_steps) and, optionally, the
    # state at one specific step (the snapshot report in main.py).
    snapshot_state = None
    snapshot_time = None

    def record_counts():
        """Track per-step S/I/R counts (three sums, never a full copy)."""
        susceptible_counts.append(int(np.sum(state == 0)))
        active_counts.append(int(np.sum(state == 1)))
        recovered_counts.append(int(np.sum(state == 2)))

    def maybe_capture_snapshot(step):
        """Capture state.copy() once, the first time a requested trigger fires."""
        nonlocal snapshot_state, snapshot_time
        if snapshot_state is not None:
            return
        infected_trigger = (
            snapshot_infected is not None
            and active_counts[-1] >= int(snapshot_infected)
        )
        node_trigger = (
            snap_node_idx is not None
            and not np.isnan(activation_time[snap_node_idx])
        )
        if infected_trigger or node_trigger:
            snapshot_state, snapshot_time = state.copy(), step

    # initial record (t = 0) -- also the only chance to catch a seed node
    # matching snapshot_node, since seeds activate before the loop starts.
    record_counts()
    maybe_capture_snapshot(0)

    # *** SPEED-UP: record infection edges on the fly (instead of recomputing later) ***
    infection_edges = {}

    # temporal evolution
    for step in range(1, max_steps + 1):
        active_nodes = np.where(state == 1)[0]
        if len(active_nodes) == 0:
            break  # no active nodes, process extinct

        new_active = np.zeros(n_nodes, dtype=bool)

        # transmission along open edges
        for u in active_nodes:
            neighbors = open_neighbors[u]
            if neighbors.size == 0:
                continue
            for v in neighbors:
                if state[v] == 0 and not new_active[v]:  # only susceptibles, first infector
                    new_active[v] = True
                    # store infection edge and time
                    infection_edges[frozenset({int(u), int(v)})] = float(step)

        # update active time and recovery
        for u in active_nodes:
            active_time[u] += 1
            if tau_vec_used is None:
                this_tau = tau
            else:
                this_tau = tau_vec_used[u]
            if active_time[u] >= this_tau:
                state[u] = 2  # recovered
                if np.isnan(recovery_time[u]):
                    recovery_time[u] = step

        # activate new infected
        for v in np.where(new_active)[0]:
            if state[v] == 0:
                state[v] = 1
                active_time[v] = 0
                if np.isnan(activation_time[v]):
                    activation_time[v] = step

        # record counts + possibly capture the snapshot at end of step
        record_counts()
        maybe_capture_snapshot(step)

    # prepare seeds info for results
    seed_index = seeds_idx[0]  # first seed (for old code)
    seed_labels = [node_labels[i] for i in seeds_idx]
    seed_label_first = seed_labels[0]

    results = {
        "Pstar": Pstar,
        "tau": float(tau),
        "tau_distribution": tau_dist_effective,
        "tau_vector": tau_vec_used,
        "pth_max": pth_max,
        "distribution": dist,
        "edge_threshold_source": edge_threshold_source,
        "seed_index": seed_index,
        "seed_indices": seeds_idx,
        "seed_label": seed_label_first,
        "seed_labels": seed_labels,
        "node_labels": node_labels,
        "edges": edges,
        "edge_thresholds": edge_pth,
        "open_edges": open_edges,
        "n_steps": len(active_counts) - 1,
        "snapshot_state": snapshot_state,
        "snapshot_time": snapshot_time,
        "active_counts": active_counts,
        "susceptible_counts": susceptible_counts,
        "recovered_counts": recovered_counts,
        "activation_time": activation_time,
        "recovery_time": recovery_time,
        "infection_edges": infection_edges,
    }

    return results

def summarize_percolation_results(graph, results):
    """
    Build a human-readable multi-line summary of a percolation run,
    similar to the Jupyter notebook output.

    Parameters
    ----------
    graph : igraph.Graph
    results : dict
        Output of run_percolation(...).

    Returns
    -------
    summary : str
        Multi-line string ready to be printed.
    """
    Pstar           = float(results["Pstar"])
    tau             = float(results["tau"])
    seed_index      = int(results["seed_index"])
    seed_labels     = results.get("seed_labels", None)
    open_edges      = results["open_edges"]
    edge_pth        = results["edge_thresholds"]
    activation_time = np.asarray(results["activation_time"], dtype=float)
    active_counts   = np.asarray(results["active_counts"], dtype=int)
    infection_edges = results.get("infection_edges", {})

    N = graph.vcount()
    E = graph.ecount()
    mean_k = 2.0 * E / max(1, N)

    # --- Edge categories: blocked / eligible-but-slow / usable ---
    # Blocked      → p_th >= P*  (closed)
    # Usable       → open AND actually used in infection_edges
    # Eligible-slow→ open but never used (conceptually "too slow"/unused)
    # edge_thresholds/open_edges are length-E, aligned to results["edges"].
    edgelist = results["edges"]

    # Set of used undirected edges
    used_pairs = set()
    for e_set in infection_edges.keys():
        u, v = sorted(list(e_set))
        used_pairs.add((u, v))

    blocked = 0
    usable  = 0
    open_total = 0

    for e_idx, (u, v) in enumerate(edgelist):
        if not open_edges[e_idx]:
            blocked += 1
        else:
            open_total += 1
            if (min(u, v), max(u, v)) in used_pairs:
                usable += 1

    eligible_slow = open_total - usable

    # --- Final reached ---
    reached_mask = ~np.isnan(activation_time)
    reached = int(np.sum(reached_mask))
    frac_reached = 100.0 * reached / max(1, N)

    # --- Peak infectious + end time ---
    if active_counts.size > 0:
        I_max = int(active_counts.max())
        t_peak_idx = int(np.argmax(active_counts))
        t_peak = float(t_peak_idx)

        non_zero_idx = np.where(active_counts > 0)[0]
        if non_zero_idx.size > 0:
            t_end = float(non_zero_idx[-1])
        else:
            t_end = 0.0
    else:
        I_max = 0
        t_peak = 0.0
        t_end = 0.0

    # --- Infection tree depth (in hops) ---
    seeds = results.get("seed_indices", [seed_index])

    # Directed edges from earlier-infected to later-infected
    neighbors_dir = {i: [] for i in range(N)}
    for e_set, t in infection_edges.items():
        u, v = list(e_set)
        tu, tv = activation_time[u], activation_time[v]
        if math.isnan(tu) or math.isnan(tv):
            continue
        if tu < tv:
            src, dst = u, v
        elif tv < tu:
            src, dst = v, u
        else:
            # Same activation time: prefer seeds as parents if possible
            if u in seeds and v not in seeds:
                src, dst = u, v
            elif v in seeds and u not in seeds:
                src, dst = v, u
            else:
                src, dst = u, v
        neighbors_dir[src].append(dst)

    # BFS / longest distance from seeds
    dist = [-1] * N
    dq = deque()
    for s in seeds:
        if 0 <= s < N:
            dist[s] = 0
            dq.append(s)

    while dq:
        u = dq.popleft()
        for w in neighbors_dir.get(u, []):
            if dist[w] < dist[u] + 1:
                dist[w] = dist[u] + 1
                dq.append(w)

    depth = max((d for d in dist if d >= 0), default=0)

    # Seed label (if present)
    if seed_labels is not None and len(seed_labels) > 0:
        seed_label_str = f"{seed_index} ({seed_labels[0]})"
    else:
        seed_label_str = str(seed_index)

    summary = (
        "------------------------------------------------------------------------\n"
        "INFECTION PERCOLATION — SUMMARY\n"
        "------------------------------------------------------------------------\n"
        f"Seed node: {seed_label_str}\n"
        f"Params:  P* = {Pstar:.3f}   τ_r = {tau:.3f}   (edge usable if Δt<τ_r)\n"
        f"Graph:   N = {N}   E = {E}   avg_degree ≈ {mean_k:.2f}\n"
        f"Edges:   blocked p_th≥P* = {blocked} | "
        f"eligible-but-slow Δt≥τ_r = {eligible_slow} | "
        f"usable Δt<τ_r = {usable}\n"
        "------------------------------------------------------------------------\n"
        f"Final reached (ever infected): {reached} / {N}  ({frac_reached:.2f}%)\n"
        f"Peak infectious I_max: {I_max} at t ≈ {t_peak:.3f}\n"
        f"End time (no infectious left): t_end ≈ {t_end:.3f}\n"
        f"Infection tree depth (hops): {depth}\n"
        "------------------------------------------------------------------------"
    )
    return summary
# ---------- Layout & helpers (igraph-based) ----------

def kk_layout_igraph(graph):
    """
    Kamada-Kawai layout for igraph.Graph.
    Returns dict: node_index -> (x, y)
    """
    layout = graph.layout_kamada_kawai()
    return {i: (layout[i][0], layout[i][1]) for i in range(graph.vcount())}

def auto_layout_igraph(graph, kk_threshold=LAYOUT_KK_THRESHOLD):
    """
    Choose a layout depending on graph size.

    - If N <= kk_threshold → Kamada-Kawai (nice but heavier).
    - Otherwise           → igraph's DRL layout (fast force-directed).

    Returns
    -------
    pos : dict
        Mapping node_index -> (x, y).
    """
    N = graph.vcount()
    if N <= kk_threshold:
        layout = graph.layout_kamada_kawai()
    else:
        # DRL is designed for large graphs; fall back to FR if needed
        try:
            layout = graph.layout_drl()
        except Exception:
            layout = graph.layout_fruchterman_reingold()
    return {i: (layout[i][0], layout[i][1]) for i in range(N)}


def edges_xy(edgelist, pos):
    """
    Build x,y arrays for Plotly line segments from a list of edges
    and a pos dict {node: (x,y)}.
    """
    xs, ys = [], []
    for u, v in edgelist:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return xs, ys


# ---------- HTML builder (igraph + results dict) ----------

def save_percolation_html_from_results_igraph(
    graph,
    results,
    filename="percolation.html",
    max_frames=180,
    default_vh=90,
):
    """
    Build an interactive HTML (KK/FR layout, instant/cumulative edges, focus on node)
    from an igraph.Graph + the results dict returned by run_percolation().

    Parameters
    ----------
    graph : igraph.Graph
        The same graph passed to run_percolation.
    results : dict
        Output of run_percolation(graph, ...).
    filename : str
        Path of the HTML file to create.
    max_frames : int
        Maximum number of time frames in the slider (subsample if longer).
    default_vh : int
        Height of the graph area in viewport height units (vh).

    Returns
    -------
    filename : str
        The path of the saved HTML file.
    """

    # basic sanity checks on results
    required_keys = [
        "Pstar", "tau", "pth_max", "distribution",
        "seed_index", "node_labels", "edges",
        "edge_thresholds", "open_edges",
        "n_steps", "activation_time", "recovery_time",
    ]
    for k in required_keys:
        if k not in results:
            raise KeyError(u"results dict is missing key '{k}'".format(k=k))

    Pstar            = results["Pstar"]
    tau              = results["tau"]
    tau_distribution = results.get("tau_distribution", "fixed")
    tau_vector       = results.get("tau_vector", None)
    pth_max          = results["pth_max"]
    distribution     = results["distribution"]
    seed_index       = results["seed_index"]
    node_labels      = results["node_labels"]
    edge_pth         = results["edge_thresholds"]
    open_edges       = results["open_edges"]
    n_steps          = results["n_steps"]
    activation_time  = results["activation_time"]
    recovery_time    = results["recovery_time"]

    N = graph.vcount()
    E = graph.ecount()

    if len(node_labels) != N:
        raise ValueError(
            u"Length of node_labels ({ln}) does not match graph.vcount() ({N})"
            .format(ln=len(node_labels), N=N)
        )
    if len(edge_pth) != E:
        raise ValueError(
            u"edge_thresholds length ({le}) does not match number of edges ({E})"
            .format(le=len(edge_pth), E=E)
        )
    if len(open_edges) != E:
        raise ValueError(
            u"open_edges length ({le}) does not match number of edges ({E})"
            .format(le=len(open_edges), E=E)
        )
    if len(activation_time) != N or len(recovery_time) != N:
        raise ValueError(
            u"activation_time and/or recovery_time lengths do not match number of nodes."
        )

    mean_k = 2.0 * E / max(1, N)

    # effective tau for q_eff and title
    if tau_distribution == "fixed" or tau_vector is None:
        tau_eff = float(tau)
    else:
        try:
            tau_eff = float(np.nanmean(tau_vector))
        except Exception:
            tau_eff = float(tau)

    # --- time axis: discrete steps 0..T ---
    T = n_steps
    times = list(range(T + 1))

    # optional subsampling if too many frames
    if len(times) > max_frames:
        idx = np.linspace(0, len(times) - 1, max_frames).astype(int)
        times = [times[i] for i in idx]

    # --- per-node info for coloring ---
    node_ti = [
        float(activation_time[i]) if not math.isnan(activation_time[i]) else float("inf")
        for i in range(N)
    ]
    node_tr = [
        float(recovery_time[i]) if not math.isnan(recovery_time[i]) else float("inf")
        for i in range(N)
    ]

    # --- layout: KK for small graphs, FR for larger ones (threshold = 1000) ---
    if N <= 1000:
        layout = graph.layout_kamada_kawai()
    else:
        layout = graph.layout_fruchterman_reingold()
    pos = {i: (layout[i][0], layout[i][1]) for i in range(N)}

    nodes = list(range(N))
    node_x = [pos[u][0] for u in nodes]
    node_y = [pos[u][1] for u in nodes]

    # --- base edges (static faint gray) ---
    edgelist = graph.get_edgelist()
    base_x, base_y = edges_xy(edgelist, pos)

    # --- infection edges and times ---
    # run_percolation records infection_edges on the fly, so it's always
    # present (possibly empty, e.g. an isolated seed that never spread).
    raw_tedge = results["infection_edges"]
    tedge = {
        frozenset({int(min(e)), int(max(e))}): float(t)
        for e, t in raw_tedge.items()
    }

    used_sorted = sorted(
        ((min(e), max(e), float(t)) for e, t in tedge.items()),
        key=lambda r: r[2],
    )
    used_u = [u for u, _, _ in used_sorted]
    used_v = [v for _, v, _ in used_sorted]
    used_t = [t for _, _, t in used_sorted]

    # --- title (similar style as your notebook) ---
    q_eff = max(0.0, min(1.0, Pstar * (1.0 - 1.0 / max(1.0, tau_eff))))

    if tau_distribution in ("fixed", None):
        tau_title = f"τ={tau_eff:.2f}"
    else:
        tau_title = f"τ̄≈{tau_eff:.2f}"

    title = (
        f"Percolation (KK/FR) | P*={Pstar:.2f}, {tau_title} | "
        f"N={N}, E={E}, ⟨k⟩≈{mean_k:.2f}, q_eff≈{q_eff:.2f} | t=0.00"
    )

    base_size = 6 if N > 1500 else 8

    # --- initial Plotly figure (base edges + empty used edges + nodes) ---
    fig = go.Figure([
        go.Scattergl(
            x=base_x, y=base_y, mode="lines",
            line=dict(width=1.0, color=COL_BASE),
            opacity=0.28,
            hoverinfo="skip", name="Base edges"
        ),
        go.Scattergl(
            x=[], y=[], mode="lines",
            line=dict(width=2.2, color=COL_USED),
            hoverinfo="skip", name="Used edges"
        ),
        go.Scatter(
            x=node_x, y=node_y, mode="markers",
            marker=dict(
                size=base_size,
                color=[COL_S] * N,
                line=dict(width=0.5, color="#222")
            ),
            text=[str(lbl) for lbl in node_labels],  # hover label
            hoverinfo="text",
            name="Nodes", showlegend=False
        ),
        # Legend-only markers
        go.Scatter(
            x=[0], y=[0], mode="markers", name="Susceptible",
            marker=dict(size=10, color=COL_S, line=dict(width=0.5, color="#222")),
            hoverinfo="skip", visible="legendonly"
        ),
        go.Scatter(
            x=[0], y=[0], mode="markers", name="Infected",
            marker=dict(size=10, color=COL_I, line=dict(width=0.5, color="#222")),
            hoverinfo="skip", visible="legendonly"
        ),
        go.Scatter(
            x=[0], y=[0], mode="markers", name="Recovered",
            marker=dict(size=10, color=COL_R, line=dict(width=0.5, color="#222")),
            hoverinfo="skip", visible="legendonly"
        ),
    ])

    fig.update_layout(
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=64, b=10),
        showlegend=True,
        legend=dict(itemsizing="constant"),
        uirevision=True,
    )

    figure_div = pio.to_html(
        fig, include_plotlyjs="inline", full_html=False, div_id="percoFig"
    )

    # --- tiny "bootstrap-like" CSS (no external deps) ---
    bootstrap_min = r"""
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,sans-serif}
.container-fluid{width:100%;padding-left:1rem;padding-right:1rem;margin-left:auto;margin-right:auto}
.row{display:flex;flex-wrap:wrap;margin-left:-.5rem;margin-right:-.5rem;gap:.5rem}
.col{flex:1 0 0%;padding-left:.5rem;padding-right:.5rem}
.col-auto{flex:0 0 auto;padding-left:.5rem;padding-right:.5rem}
.g-2{gap:.5rem}.btn{display:inline-block;font-weight:500;line-height:1.2;text-align:center;border:1px solid #ced4da;padding:.375rem .75rem;border-radius:.375rem;background:#f8f9fa;cursor:pointer}
.btn:active{transform:translateY(1px)}.btn-primary{background:#0d6efd;color:#fff;border-color:#0d6efd}
.btn-outline-secondary{background:#fff;color:#6c757d;border-color:#6c757d}
.form-select,.form-range{display:block;width:100%}.form-select{padding:.375rem 2rem .375rem .75rem;border:1px solid #ced4da;border-radius:.375rem;background:#fff}
.form-range{height:1.25rem;padding:0}.badge{display:inline-block;padding:.35em .65em;font-size:.75em;border-radius:10rem;background:#f1f3f5}
.sticky-top{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #e9ecef}
"""

    payload = {
        "times": times,
        "node_x": node_x,
        "node_y": node_y,
        "node_ti": node_ti,
        "node_tr": node_tr,
        "used_u": used_u,
        "used_v": used_v,
        "used_t": used_t,
        "default_vh": int(default_vh),
        "node_labels": [str(lbl) for lbl in node_labels],
        "base_size": float(base_size),
    }
    js_payload = json.dumps(payload)

    html = f"""<!doctype html>
<html><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Percolation (KK/FR, instant/cumulative)</title>
<style>
{bootstrap_min}
#graphWrap {{ height: {int(default_vh)}vh; width: 100%; }}
#percoFig  {{ height: 100%;  width: 100%; }}
.controls .form-range {{ width: 100%; }}
</style>
</head>
<body>
<div class="sticky-top">
  <div class="container-fluid">
    <div class="row g-2 controls">
      <div class="col-auto"><button id="play" class="btn btn-primary" title="Play/Pause">▶</button></div>
      <div class="col"><input id="slider" type="range" class="form-range" min="0" value="0" step="1" /></div>
      <div class="col-auto"><span class="badge">t=<span id="tval">0</span></span></div>
      <div class="col-auto">
        <select id="speed" class="form-select" title="Speed (ms/frame)">
          <option value="30">very fast</option>
          <option value="60">fast</option>
          <option value="120" selected>normal</option>
          <option value="240">slow</option>
          <option value="480">very slow</option>
        </select>
      </div>
      <div class="col-auto">
        <select id="mode" class="form-select" title="Edges mode">
          <option value="instant" selected>Instant</option>
          <option value="cumulative">Cumulative</option>
        </select>
      </div>
      <div class="col-auto">
        <label style="display:flex;align-items:center;gap:.4rem">
          <input id="showBase" type="checkbox" checked/> Base edges
        </label>
      </div>
      <div class="col-auto"><button id="step" class="btn btn-outline-secondary" title="Step one frame">Step</button></div>
      <div class="col-auto"><button id="reset" class="btn btn-outline-secondary" title="Reset zoom">Reset zoom</button></div>
      <div class="col-auto">
        <input id="focusLabel" placeholder="Node label" 
               style="max-width:8rem;padding:.25rem .4rem;border:1px solid #ced4da;border-radius:.375rem;font-size:.85rem" />
      </div>
      <div class="col-auto">
        <button id="focusBtn" class="btn btn-outline-secondary" title="Zoom & highlight node">Focus</button>
      </div>
      <div class="col-auto">
        <button id="clearFocus" class="btn btn-outline-secondary" title="Clear focus">Clear</button>
      </div>
    </div>
  </div>
</div>

<div class="container-fluid" style="margin-top:.5rem">
  <div id="graphWrap">{figure_div}</div>
</div>

<script>
(function() {{
  const DATA = {js_payload};
  const times = DATA.times;
  const N = DATA.node_x.length;

  const plotDiv    = document.getElementById('percoFig');
  const slider     = document.getElementById('slider');
  const tval       = document.getElementById('tval');
  const playBtn    = document.getElementById('play');
  const stepBtn    = document.getElementById('step');
  const resetBtn   = document.getElementById('reset');
  const speedSel   = document.getElementById('speed');
  const modeSel    = document.getElementById('mode');
  const showBase   = document.getElementById('showBase');
  const wrap       = document.getElementById('graphWrap');
  const focusInput = document.getElementById('focusLabel');
  const focusBtn   = document.getElementById('focusBtn');
  const clearFocus = document.getElementById('clearFocus');

  slider.max = Math.max(0, times.length-1);

  const COL_S   = "{COL_S}";
  const COL_I   = "{COL_I}";
  const COL_R   = "{COL_R}";
  const BASE_SZ = DATA.base_size || {float(base_size)};
  const FOC_COL = "#ff0000";

  // Precompute global extents to define a nice zoom window around a node
  const minX = Math.min.apply(null, DATA.node_x);
  const maxX = Math.max.apply(null, DATA.node_x);
  const minY = Math.min.apply(null, DATA.node_y);
  const maxY = Math.max.apply(null, DATA.node_y);
  const spanX = maxX - minX || 1.0;
  const spanY = maxY - minY || 1.0;
  const SPAN  = Math.max(spanX, spanY) * 0.01;  // ~30% of graph extent

  let focusedIndex = null;  // node index currently highlighted (if any)

  function nodeColorsAndSizesAt(t) {{
    const colors = new Array(N);
    const sizes  = new Array(N);
    for (let i=0;i<N;i++) {{
      const ti = DATA.node_ti[i], tr = DATA.node_tr[i];
      if (!isFinite(ti) || t < ti) colors[i] = COL_S;
      else if (t < tr)             colors[i] = COL_I;
      else                         colors[i] = COL_R;
      sizes[i] = BASE_SZ;
    }}
    if (focusedIndex !== null && focusedIndex >= 0 && focusedIndex < N) {{
      colors[focusedIndex] = FOC_COL;
      sizes[focusedIndex]  = BASE_SZ * 1.7;
    }}
    return {{colors, sizes}};
  }}

  function usedEdgesXY(idx) {{
    const mode = modeSel.value;
    const t0 = times[idx];
    const t1 = (idx < times.length-1) ? times[idx+1] : Infinity;
    const ux=[], uy=[];
    const U=DATA.used_u, V=DATA.used_v, T=DATA.used_t;
    if (mode === 'cumulative') {{
      for (let i=0;i<T.length;i++) {{
        if (T[i] <= t0) {{
          const u=U[i], v=V[i];
          ux.push(DATA.node_x[u], DATA.node_x[v], null);
          uy.push(DATA.node_y[u], DATA.node_y[v], null);
        }} else break;
      }}
    }} else {{
      for (let i=0;i<T.length;i++) {{
        const te=T[i];
        if (te < t0) continue;
        if (te >= t1) break;
        const u=U[i], v=V[i];
        ux.push(DATA.node_x[u], DATA.node_x[v], null);
        uy.push(DATA.node_y[u], DATA.node_y[v], null);
      }}
    }}
    return [ux, uy];
  }}

  function repaint(idx) {{
    idx = Math.max(0, Math.min(times.length-1, idx|0));
    const t = times[idx];
    const cs = nodeColorsAndSizesAt(t);
    const colors = cs.colors;
    const sizes  = cs.sizes;
    const [ux, uy] = usedEdgesXY(idx);

    // traces: 0=base, 1=used, 2=nodes, 3-5 legend-only
    Plotly.restyle(plotDiv, {{x:[ux], y:[uy]}}, [1]);
    Plotly.restyle(plotDiv, {{
      'marker.color': [colors],
      'marker.size' : [sizes]
    }}, [2]);
    Plotly.restyle(plotDiv, {{'visible':[showBase.checked]}}, [0]);

    tval.textContent = t.toFixed(0);
    const title = plotDiv.layout.title.text;
    const cut = title.lastIndexOf("| t=");
    const newTitle = (cut>0 ? title.slice(0, cut) : title) + " | t=" + t.toFixed(0);
    Plotly.relayout(plotDiv, {{'title.text': newTitle}});
  }}

  function resizeToWrap() {{
    const rect = wrap.getBoundingClientRect();
    Plotly.relayout(plotDiv, {{width: rect.width, height: rect.height}});
  }}
  window.addEventListener('resize', resizeToWrap);
  setTimeout(resizeToWrap, 0);

  function onSlide() {{ repaint(parseInt(slider.value,10)); }}
  slider.addEventListener('input', onSlide);
  slider.addEventListener('change', onSlide);

  let timer=null, playing=false;
  function step() {{
    let i = parseInt(slider.value,10);
    if (i >= times.length-1) i = -1; // loop
    slider.value = i+1; repaint(i+1);
  }}
  function play() {{
    if (playing) return;
    playing = true; playBtn.textContent = "⏸";
    timer = setInterval(step, parseInt(speedSel.value,10));
  }}
  function pause() {{
    playing = false; playBtn.textContent = "▶";
    if (timer) {{ clearInterval(timer); timer=null; }}
  }}
  playBtn.addEventListener('click', ()=> playing ? pause() : play());
  speedSel.addEventListener('change', ()=> {{ if (playing) {{ pause(); play(); }} }});
  stepBtn.addEventListener('click', ()=> {{ pause(); step(); }});
  resetBtn.addEventListener('click', ()=> {{
    focusedIndex = null;
    Plotly.relayout(plotDiv, {{
      'xaxis.autorange':true,
      'yaxis.autorange':true
    }});
    repaint(parseInt(slider.value,10));
  }});
  showBase.addEventListener('change', ()=> repaint(parseInt(slider.value,10)));

  // ---- focus / highlight a node by label ----
  function focusNodeByLabel(label) {{
    if (!label) return;
    const labels = DATA.node_labels || [];
    const idx = labels.indexOf(label);
    if (idx === -1) {{
      alert("Node label '" + label + "' not found.");
      return;
    }}
    focusedIndex = idx;

    const x = DATA.node_x[idx];
    const y = DATA.node_y[idx];

    const xMin = x - SPAN;
    const xMax = x + SPAN;
    const yMin = y - SPAN;
    const yMax = y + SPAN;

    Plotly.relayout(plotDiv, {{
      'xaxis.range': [xMin, xMax],
      'yaxis.range': [yMin, yMax]
    }});
    repaint(parseInt(slider.value,10));
  }}

  focusBtn.addEventListener('click', ()=> {{
    const label = (focusInput.value || "").trim();
    focusNodeByLabel(label);
  }});

  focusInput.addEventListener('keyup', (e)=> {{
    if (e.key === 'Enter') {{
      const label = (focusInput.value || "").trim();
      focusNodeByLabel(label);
    }}
  }});

  clearFocus.addEventListener('click', ()=> {{
    focusedIndex = null;
    repaint(parseInt(slider.value,10));
  }});

  repaint(0);
}})();
</script>
</body></html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    return filename


####################################################################################################
####################################################################################################


def save_percolation_html_v2(
    graph,
    results,
    filename="percolation.html",
    max_frames=180,
    default_vh=90,
):
    """
    Copy of save_percolation_html_from_results_igraph() kept as a separate
    function so the original is never modified while this one is iterated on.

    First addition over the original: an epidemic curve (S/I/R counts vs t)
    plotted below the network animation, using active_counts/susceptible_counts/
    recovered_counts -- run_percolation already computes these every step but the
    original HTML never plotted them (only summarize_percolation_results read
    them, for the printed text summary). A dotted vertical marker on the curve
    tracks the network animation's current t, moved in lockstep by repaint().

    Build an interactive HTML (KK/FR layout, instant/cumulative edges, focus on node)
    from an igraph.Graph + the results dict returned by run_percolation().

    Parameters
    ----------
    graph : igraph.Graph
        The same graph passed to run_percolation.
    results : dict
        Output of run_percolation(graph, ...).
    filename : str
        Path of the HTML file to create.
    max_frames : int
        Maximum number of time frames in the slider (subsample if longer).
    default_vh : int
        Height of the graph area in viewport height units (vh).

    Returns
    -------
    filename : str
        The path of the saved HTML file.
    """

    # basic sanity checks on results
    required_keys = [
        "Pstar", "tau", "pth_max", "distribution",
        "seed_index", "node_labels", "edges",
        "edge_thresholds", "open_edges",
        "n_steps", "activation_time", "recovery_time",
    ]
    for k in required_keys:
        if k not in results:
            raise KeyError(u"results dict is missing key '{k}'".format(k=k))

    Pstar            = results["Pstar"]
    tau              = results["tau"]
    tau_distribution = results.get("tau_distribution", "fixed")
    tau_vector       = results.get("tau_vector", None)
    pth_max          = results["pth_max"]
    distribution     = results["distribution"]
    seed_index       = results["seed_index"]
    node_labels      = results["node_labels"]
    edge_pth         = results["edge_thresholds"]
    open_edges       = results["open_edges"]
    n_steps          = results["n_steps"]
    activation_time  = results["activation_time"]
    recovery_time    = results["recovery_time"]

    N = graph.vcount()
    E = graph.ecount()

    if len(node_labels) != N:
        raise ValueError(
            u"Length of node_labels ({ln}) does not match graph.vcount() ({N})"
            .format(ln=len(node_labels), N=N)
        )
    if len(edge_pth) != E:
        raise ValueError(
            u"edge_thresholds length ({le}) does not match number of edges ({E})"
            .format(le=len(edge_pth), E=E)
        )
    if len(open_edges) != E:
        raise ValueError(
            u"open_edges length ({le}) does not match number of edges ({E})"
            .format(le=len(open_edges), E=E)
        )
    if len(activation_time) != N or len(recovery_time) != N:
        raise ValueError(
            u"activation_time and/or recovery_time lengths do not match number of nodes."
        )

    mean_k = 2.0 * E / max(1, N)

    # effective tau for q_eff and title
    if tau_distribution == "fixed" or tau_vector is None:
        tau_eff = float(tau)
    else:
        try:
            tau_eff = float(np.nanmean(tau_vector))
        except Exception:
            tau_eff = float(tau)

    # --- time axis: discrete steps 0..T ---
    T = n_steps
    times = list(range(T + 1))

    # optional subsampling if too many frames
    if len(times) > max_frames:
        idx = np.linspace(0, len(times) - 1, max_frames).astype(int)
        times = [times[i] for i in idx]

    # --- per-node info for coloring ---
    node_ti = [
        float(activation_time[i]) if not math.isnan(activation_time[i]) else float("inf")
        for i in range(N)
    ]
    node_tr = [
        float(recovery_time[i]) if not math.isnan(recovery_time[i]) else float("inf")
        for i in range(N)
    ]

    # --- layout: KK for small graphs, FR for larger ones (threshold = 1000) ---
    if N <= 1000:
        layout = graph.layout_kamada_kawai()
    else:
        layout = graph.layout_fruchterman_reingold()
    pos = {i: (layout[i][0], layout[i][1]) for i in range(N)}

    nodes = list(range(N))
    node_x = [pos[u][0] for u in nodes]
    node_y = [pos[u][1] for u in nodes]

    # --- base edges (static faint gray) ---
    edgelist = graph.get_edgelist()
    base_x, base_y = edges_xy(edgelist, pos)

    # --- infection edges and times ---
    # run_percolation records infection_edges on the fly, so it's always
    # present (possibly empty, e.g. an isolated seed that never spread).
    raw_tedge = results["infection_edges"]
    tedge = {
        frozenset({int(min(e)), int(max(e))}): float(t)
        for e, t in raw_tedge.items()
    }

    used_sorted = sorted(
        ((min(e), max(e), float(t)) for e, t in tedge.items()),
        key=lambda r: r[2],
    )
    used_u = [u for u, _, _ in used_sorted]
    used_v = [v for _, v, _ in used_sorted]
    used_t = [t for _, _, t in used_sorted]

    # --- title (similar style as your notebook) ---
    q_eff = max(0.0, min(1.0, Pstar * (1.0 - 1.0 / max(1.0, tau_eff))))

    if tau_distribution in ("fixed", None):
        tau_title = f"τ={tau_eff:.2f}"
    else:
        tau_title = f"τ̄≈{tau_eff:.2f}"

    title = (
        f"Percolation v2 (KK/FR) | P*={Pstar:.2f}, {tau_title} | "
        f"N={N}, E={E}, ⟨k⟩≈{mean_k:.2f}, q_eff≈{q_eff:.2f} | t=0.00"
    )

    base_size = 6 if N > 1500 else 8

    # --- initial Plotly figure (base edges + empty used edges + nodes) ---
    fig = go.Figure([
        go.Scattergl(
            x=base_x, y=base_y, mode="lines",
            line=dict(width=1.0, color=COL_BASE),
            opacity=0.28,
            hoverinfo="skip", name="Base edges"
        ),
        go.Scattergl(
            x=[], y=[], mode="lines",
            line=dict(width=2.2, color=COL_USED),
            hoverinfo="skip", name="Used edges"
        ),
        go.Scatter(
            x=node_x, y=node_y, mode="markers",
            marker=dict(
                size=base_size,
                color=[COL_S] * N,
                line=dict(width=0.5, color="#222")
            ),
            text=[str(lbl) for lbl in node_labels],  # hover label
            hoverinfo="text",
            name="Nodes", showlegend=False
        ),
        # Legend-only markers
        go.Scatter(
            x=[0], y=[0], mode="markers", name="Susceptible",
            marker=dict(size=10, color=COL_S, line=dict(width=0.5, color="#222")),
            hoverinfo="skip", visible="legendonly"
        ),
        go.Scatter(
            x=[0], y=[0], mode="markers", name="Infected",
            marker=dict(size=10, color=COL_I, line=dict(width=0.5, color="#222")),
            hoverinfo="skip", visible="legendonly"
        ),
        go.Scatter(
            x=[0], y=[0], mode="markers", name="Recovered",
            marker=dict(size=10, color=COL_R, line=dict(width=0.5, color="#222")),
            hoverinfo="skip", visible="legendonly"
        ),
    ])

    fig.update_layout(
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=10, r=10, t=64, b=10),
        showlegend=True,
        legend=dict(itemsizing="constant"),
        uirevision=True,
    )

    figure_div = pio.to_html(
        fig, include_plotlyjs="inline", full_html=False, div_id="percoFig"
    )

    # --- epidemic curve (S/I/R counts over the full, unsampled time axis) ---
    # active_counts/susceptible_counts/recovered_counts are already computed by
    # run_percolation for every step but the original HTML never plotted them
    # (summarize_percolation_results only reads them for the text summary).
    full_times = list(range(T + 1))
    sus_counts = results["susceptible_counts"]
    inf_counts = results["active_counts"]
    rec_counts = results["recovered_counts"]

    fig2 = go.Figure([
        go.Scatter(x=full_times, y=sus_counts, mode="lines", name="Susceptible",
                   line=dict(color=COL_S, width=2)),
        go.Scatter(x=full_times, y=inf_counts, mode="lines", name="Infected",
                   line=dict(color=COL_I, width=2)),
        go.Scatter(x=full_times, y=rec_counts, mode="lines", name="Recovered",
                   line=dict(color=COL_R, width=2)),
    ])
    fig2.update_layout(
        title="Epidemic curve (S/I/R over time)",
        xaxis=dict(title="t"),
        yaxis=dict(title="Number of nodes"),
        margin=dict(l=50, r=10, t=40, b=35),
        legend=dict(orientation="h", y=1.15),
        # vertical marker tracking the network animation's current t, moved by
        # repaint() in lockstep with the slider -- x0/x1 updated via Plotly.relayout.
        shapes=[dict(type="line", xref="x", yref="paper", x0=0, x1=0, y0=0, y1=1,
                     line=dict(color="#333", width=1, dash="dot"))],
    )
    curve_div = pio.to_html(fig2, include_plotlyjs=False, full_html=False, div_id="percoCurve")

    # --- tiny "bootstrap-like" CSS (no external deps) ---
    bootstrap_min = r"""
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,sans-serif}
.container-fluid{width:100%;padding-left:1rem;padding-right:1rem;margin-left:auto;margin-right:auto}
.row{display:flex;flex-wrap:wrap;margin-left:-.5rem;margin-right:-.5rem;gap:.5rem}
.col{flex:1 0 0%;padding-left:.5rem;padding-right:.5rem}
.col-auto{flex:0 0 auto;padding-left:.5rem;padding-right:.5rem}
.g-2{gap:.5rem}.btn{display:inline-block;font-weight:500;line-height:1.2;text-align:center;border:1px solid #ced4da;padding:.375rem .75rem;border-radius:.375rem;background:#f8f9fa;cursor:pointer}
.btn:active{transform:translateY(1px)}.btn-primary{background:#0d6efd;color:#fff;border-color:#0d6efd}
.btn-outline-secondary{background:#fff;color:#6c757d;border-color:#6c757d}
.form-select,.form-range{display:block;width:100%}.form-select{padding:.375rem 2rem .375rem .75rem;border:1px solid #ced4da;border-radius:.375rem;background:#fff}
.form-range{height:1.25rem;padding:0}.badge{display:inline-block;padding:.35em .65em;font-size:.75em;border-radius:10rem;background:#f1f3f5}
.sticky-top{position:sticky;top:0;z-index:10;background:#fff;border-bottom:1px solid #e9ecef}
"""

    payload = {
        "times": times,
        "node_x": node_x,
        "node_y": node_y,
        "node_ti": node_ti,
        "node_tr": node_tr,
        "used_u": used_u,
        "used_v": used_v,
        "used_t": used_t,
        "default_vh": int(default_vh),
        "node_labels": [str(lbl) for lbl in node_labels],
        "base_size": float(base_size),
    }
    js_payload = json.dumps(payload)

    html = f"""<!doctype html>
<html><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Percolation v2 (KK/FR, instant/cumulative + epidemic curve)</title>
<style>
{bootstrap_min}
#graphWrap {{ height: {int(default_vh)}vh; width: 100%; }}
#percoFig  {{ height: 100%;  width: 100%; }}
.controls .form-range {{ width: 100%; }}
#curveWrap {{ height: 28vh; width: 100%; margin-top: .75rem; }}
#percoCurve {{ height: 100%; width: 100%; }}
</style>
</head>
<body>
<div class="sticky-top">
  <div class="container-fluid">
    <div class="row g-2 controls">
      <div class="col-auto"><button id="play" class="btn btn-primary" title="Play/Pause">▶</button></div>
      <div class="col"><input id="slider" type="range" class="form-range" min="0" value="0" step="1" /></div>
      <div class="col-auto"><span class="badge">t=<span id="tval">0</span></span></div>
      <div class="col-auto">
        <select id="speed" class="form-select" title="Speed (ms/frame)">
          <option value="30">very fast</option>
          <option value="60">fast</option>
          <option value="120" selected>normal</option>
          <option value="240">slow</option>
          <option value="480">very slow</option>
        </select>
      </div>
      <div class="col-auto">
        <select id="mode" class="form-select" title="Edges mode">
          <option value="instant" selected>Instant</option>
          <option value="cumulative">Cumulative</option>
        </select>
      </div>
      <div class="col-auto">
        <label style="display:flex;align-items:center;gap:.4rem">
          <input id="showBase" type="checkbox" checked/> Base edges
        </label>
      </div>
      <div class="col-auto"><button id="step" class="btn btn-outline-secondary" title="Step one frame">Step</button></div>
      <div class="col-auto"><button id="reset" class="btn btn-outline-secondary" title="Reset zoom">Reset zoom</button></div>
      <div class="col-auto">
        <input id="focusLabel" placeholder="Node label" 
               style="max-width:8rem;padding:.25rem .4rem;border:1px solid #ced4da;border-radius:.375rem;font-size:.85rem" />
      </div>
      <div class="col-auto">
        <button id="focusBtn" class="btn btn-outline-secondary" title="Zoom & highlight node">Focus</button>
      </div>
      <div class="col-auto">
        <button id="clearFocus" class="btn btn-outline-secondary" title="Clear focus">Clear</button>
      </div>
    </div>
  </div>
</div>

<div class="container-fluid" style="margin-top:.5rem">
  <div id="graphWrap">{figure_div}</div>
</div>

<div class="container-fluid">
  <div id="curveWrap">{curve_div}</div>
</div>

<script>
(function() {{
  const DATA = {js_payload};
  const times = DATA.times;
  const N = DATA.node_x.length;

  const plotDiv    = document.getElementById('percoFig');
  const curveDiv   = document.getElementById('percoCurve');
  const slider     = document.getElementById('slider');
  const tval       = document.getElementById('tval');
  const playBtn    = document.getElementById('play');
  const stepBtn    = document.getElementById('step');
  const resetBtn   = document.getElementById('reset');
  const speedSel   = document.getElementById('speed');
  const modeSel    = document.getElementById('mode');
  const showBase   = document.getElementById('showBase');
  const wrap       = document.getElementById('graphWrap');
  const focusInput = document.getElementById('focusLabel');
  const focusBtn   = document.getElementById('focusBtn');
  const clearFocus = document.getElementById('clearFocus');

  slider.max = Math.max(0, times.length-1);

  const COL_S   = "{COL_S}";
  const COL_I   = "{COL_I}";
  const COL_R   = "{COL_R}";
  const BASE_SZ = DATA.base_size || {float(base_size)};
  const FOC_COL = "#ff0000";

  // Precompute global extents to define a nice zoom window around a node
  const minX = Math.min.apply(null, DATA.node_x);
  const maxX = Math.max.apply(null, DATA.node_x);
  const minY = Math.min.apply(null, DATA.node_y);
  const maxY = Math.max.apply(null, DATA.node_y);
  const spanX = maxX - minX || 1.0;
  const spanY = maxY - minY || 1.0;
  const SPAN  = Math.max(spanX, spanY) * 0.01;  // ~30% of graph extent

  let focusedIndex = null;  // node index currently highlighted (if any)

  function nodeColorsAndSizesAt(t) {{
    const colors = new Array(N);
    const sizes  = new Array(N);
    for (let i=0;i<N;i++) {{
      const ti = DATA.node_ti[i], tr = DATA.node_tr[i];
      if (!isFinite(ti) || t < ti) colors[i] = COL_S;
      else if (t < tr)             colors[i] = COL_I;
      else                         colors[i] = COL_R;
      sizes[i] = BASE_SZ;
    }}
    if (focusedIndex !== null && focusedIndex >= 0 && focusedIndex < N) {{
      colors[focusedIndex] = FOC_COL;
      sizes[focusedIndex]  = BASE_SZ * 1.7;
    }}
    return {{colors, sizes}};
  }}

  function usedEdgesXY(idx) {{
    const mode = modeSel.value;
    const t0 = times[idx];
    const t1 = (idx < times.length-1) ? times[idx+1] : Infinity;
    const ux=[], uy=[];
    const U=DATA.used_u, V=DATA.used_v, T=DATA.used_t;
    if (mode === 'cumulative') {{
      for (let i=0;i<T.length;i++) {{
        if (T[i] <= t0) {{
          const u=U[i], v=V[i];
          ux.push(DATA.node_x[u], DATA.node_x[v], null);
          uy.push(DATA.node_y[u], DATA.node_y[v], null);
        }} else break;
      }}
    }} else {{
      for (let i=0;i<T.length;i++) {{
        const te=T[i];
        if (te < t0) continue;
        if (te >= t1) break;
        const u=U[i], v=V[i];
        ux.push(DATA.node_x[u], DATA.node_x[v], null);
        uy.push(DATA.node_y[u], DATA.node_y[v], null);
      }}
    }}
    return [ux, uy];
  }}

  function repaint(idx) {{
    idx = Math.max(0, Math.min(times.length-1, idx|0));
    const t = times[idx];
    const cs = nodeColorsAndSizesAt(t);
    const colors = cs.colors;
    const sizes  = cs.sizes;
    const [ux, uy] = usedEdgesXY(idx);

    // traces: 0=base, 1=used, 2=nodes, 3-5 legend-only
    Plotly.restyle(plotDiv, {{x:[ux], y:[uy]}}, [1]);
    Plotly.restyle(plotDiv, {{
      'marker.color': [colors],
      'marker.size' : [sizes]
    }}, [2]);
    Plotly.restyle(plotDiv, {{'visible':[showBase.checked]}}, [0]);
    Plotly.relayout(curveDiv, {{'shapes[0].x0': t, 'shapes[0].x1': t}});

    tval.textContent = t.toFixed(0);
    const title = plotDiv.layout.title.text;
    const cut = title.lastIndexOf("| t=");
    const newTitle = (cut>0 ? title.slice(0, cut) : title) + " | t=" + t.toFixed(0);
    Plotly.relayout(plotDiv, {{'title.text': newTitle}});
  }}

  function resizeToWrap() {{
    const rect = wrap.getBoundingClientRect();
    Plotly.relayout(plotDiv, {{width: rect.width, height: rect.height}});
  }}
  window.addEventListener('resize', resizeToWrap);
  setTimeout(resizeToWrap, 0);

  function resizeCurveToWrap() {{
    const rect = document.getElementById('curveWrap').getBoundingClientRect();
    Plotly.relayout(curveDiv, {{width: rect.width, height: rect.height}});
  }}
  window.addEventListener('resize', resizeCurveToWrap);
  setTimeout(resizeCurveToWrap, 0);

  function onSlide() {{ repaint(parseInt(slider.value,10)); }}
  slider.addEventListener('input', onSlide);
  slider.addEventListener('change', onSlide);

  let timer=null, playing=false;
  function step() {{
    let i = parseInt(slider.value,10);
    if (i >= times.length-1) i = -1; // loop
    slider.value = i+1; repaint(i+1);
  }}
  function play() {{
    if (playing) return;
    playing = true; playBtn.textContent = "⏸";
    timer = setInterval(step, parseInt(speedSel.value,10));
  }}
  function pause() {{
    playing = false; playBtn.textContent = "▶";
    if (timer) {{ clearInterval(timer); timer=null; }}
  }}
  playBtn.addEventListener('click', ()=> playing ? pause() : play());
  speedSel.addEventListener('change', ()=> {{ if (playing) {{ pause(); play(); }} }});
  stepBtn.addEventListener('click', ()=> {{ pause(); step(); }});
  resetBtn.addEventListener('click', ()=> {{
    focusedIndex = null;
    Plotly.relayout(plotDiv, {{
      'xaxis.autorange':true,
      'yaxis.autorange':true
    }});
    repaint(parseInt(slider.value,10));
  }});
  showBase.addEventListener('change', ()=> repaint(parseInt(slider.value,10)));

  // ---- focus / highlight a node by label ----
  function focusNodeByLabel(label) {{
    if (!label) return;
    const labels = DATA.node_labels || [];
    const idx = labels.indexOf(label);
    if (idx === -1) {{
      alert("Node label '" + label + "' not found.");
      return;
    }}
    focusedIndex = idx;

    const x = DATA.node_x[idx];
    const y = DATA.node_y[idx];

    const xMin = x - SPAN;
    const xMax = x + SPAN;
    const yMin = y - SPAN;
    const yMax = y + SPAN;

    Plotly.relayout(plotDiv, {{
      'xaxis.range': [xMin, xMax],
      'yaxis.range': [yMin, yMax]
    }});
    repaint(parseInt(slider.value,10));
  }}

  focusBtn.addEventListener('click', ()=> {{
    const label = (focusInput.value || "").trim();
    focusNodeByLabel(label);
  }});

  focusInput.addEventListener('keyup', (e)=> {{
    if (e.key === 'Enter') {{
      const label = (focusInput.value || "").trim();
      focusNodeByLabel(label);
    }}
  }});

  clearFocus.addEventListener('click', ()=> {{
    focusedIndex = null;
    repaint(parseInt(slider.value,10));
  }});

  repaint(0);
}})();
</script>
</body></html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    return filename
