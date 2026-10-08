import pandas as pd
import igraph as ig
import numpy as np
from itertools import repeat
from colorama import Fore, Style
import csv
import matplotlib.pyplot as plt
import warnings
import math

from pyntacle.generate import *

# ---- adjacency matrix ----

def import_adjMatrix(file, sep=None, header=True, directed=False, weight=False):
    
    if header:
        adjMatrix = pd.read_csv(file, sep = sep, index_col=0, engine='python')
        node_names = adjMatrix.index.tolist()
    else:
        adjMatrix = pd.read_csv(file, sep=sep, header=None, engine='python')
        adjMatrix.index="n"+adjMatrix.index.astype(str)
        node_names = adjMatrix.index.tolist()
    
    values = adjMatrix.apply(pd.to_numeric, errors="coerce")
    if adjMatrix.shape[0] != adjMatrix.shape[1] or values.isna().any().any():
        raise ValueError(f"-t matrix needs a square table of numbers (node names on the first row "
                         f"and column with the header, numbers only with -nh); this file has "
                         f"{adjMatrix.shape[0]} rows and {adjMatrix.shape[1]} columns of values"
                         + ("" if not values.isna().any().any() else ", some of them not numbers"))
    adjMatrix = values
    # numeric names (1, 2, ...) are kept as text, as -n, -r and -nl give them
    node_names = [str(x) for x in node_names]

    if directed:
        mode="directed"
    else:
        mode="undirected"
        if not np.allclose(adjMatrix.values, adjMatrix.values.T, equal_nan=True):
            raise ValueError("the matrix is not symmetric, so it cannot be read as an undirected "
                             "network; add -d to read it as directed")

    if weight:
        grafo = ig.Graph.Weighted_Adjacency(adjMatrix.values.tolist(), mode=mode, attr="weight") 
        grafo.es["width"] = grafo.es["weight"]
    else:
        cells = adjMatrix.values
        if not np.isin(cells, (0, 1)).all():
            print("NOTE: the matrix holds values other than 0 and 1; without -w every non-zero "
                  "cell is one edge")
        grafo = ig.Graph.Adjacency((cells != 0).astype(int).tolist(), mode=mode)
    grafo.vs["name"] = node_names
    grafo.vs["label"] = node_names
    drop_loops_and_duplicates(grafo)

    return grafo


# ---- edge list ----

def drop_loops_and_duplicates(grafo):
    """Remove self-loops and merge parallel edges, keeping the largest weight.

    Both would corrupt the adjacency view of the compiled kernels (a loop on
    the diagonal, a duplicate read as weight 2); directed graphs included.
    """
    loops = sum(1 for e in grafo.es if e.source == e.target)
    pairs = [e.tuple if grafo.is_directed() else (min(e.tuple), max(e.tuple))
             for e in grafo.es if e.source != e.target]
    duplicates = len(pairs) - len(set(pairs))
    if loops:
        warn(f"removed {loops} self-loop(s) from the input network")
    if duplicates:
        warn(f"merged {duplicates} parallel edge(s), keeping the largest weight")
    if loops or duplicates:
        combine = {a: max for a in grafo.es.attributes()} if grafo.es.attributes() else None
        grafo.simplify(multiple=True, loops=True, combine_edges=combine)


def edgeGraph(df_edge, weight, directed=False):

    # numeric names (1, 2, ...) are kept as text, as -n, -r and -nl give them
    df_edge = df_edge.copy()
    for column in df_edge.columns[:2]:
        df_edge[column] = df_edge[column].astype(str)
    grafo = ig.Graph.TupleList(df_edge.values.tolist(), directed=directed, weights=weight)
    drop_loops_and_duplicates(grafo)
    grafo.vs["label"] = list(grafo.vs["name"])

    return grafo


def _weight_column(df_edge, weight, column):
    """Pick the weight column of an edge table, or weight 1 for every edge.

    Without -w a numeric weight column is ignored, and the user is told so;
    with -w a missing column gives weight 1 to every edge, and a column with
    gaps is refused rather than silently replaced."""
    has_column = len(df_edge.columns) > column
    if not weight:
        if has_column and pd.to_numeric(df_edge.iloc[:, column], errors="coerce").notna().all():
            print("NOTE: the file has a numeric weight column; it is ignored without -w")
        return [1] * len(df_edge)
    if not has_column or df_edge.iloc[:, column].isna().all():
        warn("-w given but the file has no weight column: every edge gets weight 1")
        return [1] * len(df_edge)
    values = pd.to_numeric(df_edge.iloc[:, column], errors="coerce")
    bad = df_edge.iloc[:, column][values.isna()]
    if len(bad):
        first = "empty" if pd.isna(bad.iloc[0]) else repr(bad.iloc[0])
        raise ValueError(f"{len(bad)} edge(s) have a missing or non-numeric weight "
                         f"(first: {first}, line {bad.index[0] + 2})")
    return values.astype(float).tolist()


def import_edgeList(file, sep= None, header=True, directed=False, weight=False):
    
    if header:
        df_edge = pd.read_csv(file, sep=sep, engine='python')
    else:
        df_edge = pd.read_csv(file, sep = sep, names=["V1","V2","weight"],  engine='python')

    weights = _weight_column(df_edge, weight, 2)
    df_edge = df_edge.iloc[:, :2].copy()
    df_edge["weight"] = weights

    grafo = edgeGraph(df_edge, weight, directed)

    return grafo


# ---- SIF ----

def import_sif(file, sep= None, header=True, directed=False, weight=False):

    if header:
        df_edge = pd.read_csv(file, sep=sep, engine='python')
    else:
        df_edge = pd.read_csv(file, sep = sep, names=["V1","Interaction","V2","weight"],  engine='python')

    # a SIF names few interaction types; an edge list read as SIF puts the
    # second node there, and its weights where the second node should be
    kinds = df_edge.iloc[:, 1].nunique()
    if kinds > max(5, len(df_edge) / 2):
        warn(f"the interaction column (2nd) holds {kinds} different values in {len(df_edge)} rows: "
             "if the file is an edge list, read it with -t edgelist")

    weights = _weight_column(df_edge, weight, 3)
    df_edge = df_edge.iloc[:, [0, 2]].copy()
    df_edge["weight"] = weights

    grafo = edgeGraph(df_edge, weight, directed)

    return grafo


# ---- DOT ----

def import_dot(file, directed=False, weight=False):
    import pygraphviz as gdot
    import warnings
    
    grafo = ig.Graph(directed=directed)
    try:
        gviz = gdot.AGraph(file)
    except Exception as err:
        raise ValueError(f"could not read {file} as DOT ({err}). Check -t.")

    grafo.add_vertices(gviz.nodes())
    grafo.add_edges(gviz.edges())
    
    if gviz.is_directed() and not directed:
        warn("the DOT file declares a directed graph; it is read as undirected (add -d to keep the directions)")
    elif directed and not gviz.is_directed():
        warn("-d given but the DOT file declares an undirected graph; every edge is read as one-way")

    if weight:
        raw = [edge.attr['weight'] for edge in gviz.edges()]
        if all(w in (None, "") for w in raw):
            warn("-w given but the DOT edges have no weight attribute: every edge gets weight 1")
            weights = [1.0] * len(raw)
        else:
            try:
                weights = [float(w) for w in raw]
            except (TypeError, ValueError):
                bad = next(w for w in raw if not _is_number(w))
                raise ValueError(f"every DOT edge needs a numeric weight attribute with -w (found {bad!r})")
        grafo.es["weight"] = weights
        grafo.es["width"] = grafo.es["weight"]

    names=[]
    for node in gviz.nodes():
        names.append(node.attr['name'])
    
    # every vertex needs a name: fall back to the DOT node ids
    if None in names:
        names = [str(node) for node in gviz.nodes()]
    grafo.vs["label"] = names
    grafo.vs["name"] = names
    drop_loops_and_duplicates(grafo)

    return grafo


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False




# ---- helpers ----

def plain_copy(grafo, directed=None, with_weights=True):
    """Plain igraph copy of ``grafo``, vertex count included.

    The Graphtacle subclass cannot be copied with ``induced_subgraph`` or
    ``copy`` (its ``__init__`` takes a fixed positional signature and chokes on
    igraph's internal ``__ptr`` keyword), so the codebase rebuilds a plain
    ``ig.Graph`` from the edge list instead. Doing that without an explicit ``n``
    is a trap: igraph sizes the new graph from the highest endpoint it sees, so
    every *trailing* isolated vertex disappears and the vertex-attribute lists
    are truncated to match. An all-zero last row in an adjacency matrix is
    exactly that case.

    The compiled kernels never went through this path -- they read the dense
    adjacency the Graphtacle builds with the right ``n`` -- which is why the
    symptom was the Python and Cython engines disagreeing on a network that
    loaded and printed perfectly.

    Args:
        grafo: Source graph (Graphtacle or plain igraph Graph).
        directed (bool | None): Orientation of the copy. None keeps the source's.
        with_weights (bool): Carry the ``weight`` edge attribute, and the
            ``raw_weight``/``affinity``/``sign`` views, when present.

    Returns:
        igraph.Graph: A copy with the same vertex count, names, labels and edges.
    """
    attrs = {}
    if with_weights:
        # the weight views travel with the distance (see weight_views)
        for key in ("weight", "raw_weight", "affinity", "sign"):
            if key in grafo.es.attributes():
                attrs[key] = grafo.es[key]

    vertex_attrs = {}
    for key in ("name", "label"):
        if key in grafo.vs.attributes():
            vertex_attrs[key] = grafo.vs[key]

    return ig.Graph(n=grafo.vcount(),
                    directed=grafo.is_directed() if directed is None else directed,
                    vertex_attrs=vertex_attrs,
                    edges=grafo.get_edgelist(),
                    edge_attrs=attrs)


WEIGHT_TYPES = ("distance", "affinity", "signed")
DISTANCE_TRANSFORMS = ("inverse", "one-minus", "neglog")
TRANSFORM_FORMULA = {"inverse": "1/w", "one-minus": "1 - w", "neglog": "-ln(w)"}
MIN_DISTANCE = 1e-6


def weight_views(raw, weight_type="distance", transform="inverse"):
    """Distance, affinity and sign of every edge from the weights as read.

    Shortest-path metrics need a length, strength-based metrics (clustering,
    eigenvector, PageRank, communities, mesoscale TI) need a tie strength, and
    the two are inverse notions. The user states which one the file holds:

    - ``distance``: w > 0 is a length; affinity = 1/w.
    - ``affinity``: w > 0 is a strength; distance = transform(w).
    - ``signed``: w != 0 is a signed strength (e.g. a correlation); the
      magnitude ``|w|`` is the strength, the sign is kept apart and never folded
      silently.

    Transforms from strength a to length d: ``inverse`` d = 1/a, the usual
    convention for weighted shortest paths (Newman 2001; Brandes 2001; Opsahl
    et al. 2010); ``one-minus`` d = 1 - a and ``neglog`` d = -ln a, both for
    0 < a <= 1 and floored at MIN_DISTANCE so no pair collapses to distance 0.

    Returns a dict of lists: ``distance``, ``affinity``, ``sign``.
    """
    if weight_type not in WEIGHT_TYPES:
        raise ValueError(f"ERROR: unknown weight type {weight_type!r}; use one of {', '.join(WEIGHT_TYPES)}")
    if transform not in DISTANCE_TRANSFORMS:
        raise ValueError(f"ERROR: unknown distance transform {transform!r}; use one of {', '.join(DISTANCE_TRANSFORMS)}")
    w = [float(x) for x in raw]
    if any(math.isnan(x) for x in w):
        raise ValueError("ERROR: the network contains NaN edge weights.")

    if weight_type != "signed":
        negative = [i for i, x in enumerate(w) if x < 0]
        if negative:
            raise ValueError(
                f"ERROR: {len(negative)} edge weight(s) are negative (first: {w[negative[0]]}), "
                f"which a {weight_type} cannot be. If the weights are signed associations "
                "(e.g. correlations), use --weight-type signed: the magnitude is used as "
                "the strength of the tie and the sign is kept.")
    if any(x == 0.0 for x in w):
        # validate_weights explains why a zero weight cannot be an edge
        validate_weights(w)

    sign = [-1 if x < 0 else 1 for x in w]
    if weight_type == "distance":
        return {"distance": w, "affinity": [1.0 / x for x in w], "sign": sign}

    affinity = [abs(x) for x in w]
    if transform == "inverse":
        distance = [1.0 / a for a in affinity]
    else:
        above = [a for a in affinity if a > 1.0]
        if above:
            raise ValueError(
                f"ERROR: the {transform} transform needs strengths in (0, 1], but "
                f"{len(above)} edge(s) exceed 1 (largest: {max(above)}). Use the inverse "
                "transform (--distance-transform inverse), which accepts any positive strength.")
        if transform == "one-minus":
            distance = [max(1.0 - a, MIN_DISTANCE) for a in affinity]
        else:
            distance = [max(-math.log(a), MIN_DISTANCE) for a in affinity]
    return {"distance": distance, "affinity": affinity, "sign": sign}


def describe_weights(info):
    """One line stating how weights were read, for reports and the console."""
    if not info:
        return "unweighted"
    if info["type"] == "distance":
        return "distance"
    return f"{info['type']}, distance = {TRANSFORM_FORMULA[info['transform']].replace('w', '|w|' if info['type'] == 'signed' else 'w')}"


def validate_weights(weights, warn_sub_unit=True):
    """Reject edge weights that cannot survive the round-trip through igraph.

    The compiled kernels read a zero weight as "no edge" and drop it, while
    igraph keeps the edge: a path 0-1-2-3 whose middle weight is 0 is two
    components for the kernels and one for igraph. There is no way to tell the
    two apart downstream, so refuse the input here rather than return a wrong
    number.

    Sub-unit weights are legal but let dR and group closeness exceed 1, so
    they earn a warning.
    """
    if isinstance(weights, (int, float)):
        weights = [weights]

    numeric = []
    for w in weights:
        try:
            numeric.append(float(w))
        except (TypeError, ValueError):
            raise ValueError(f"ERROR: non-numeric edge weight {w!r}")

    if any(w == 0.0 for w in numeric):
        raise ValueError(
            "ERROR: the network contains edges with weight zero. A zero weight is "
            "indistinguishable from an absent edge once the graph is converted to a "
            "weighted adjacency matrix, so the result would be silently wrong. "
            "Remove those edges, or give them a small positive weight."
        )

    if warn_sub_unit and any(0.0 < w < 1.0 for w in numeric):
        warnings.warn(
            "some edge lengths (the weights read as distances) are below 1, so dR and "
            "group closeness can exceed 1 for this input.",
            RuntimeWarning, stacklevel=2)


def capo_dist(path_list,distance_type):
    if distance_type == "max":
        return max(path_list)
    elif distance_type == "min":
        return min(path_list)
    elif distance_type == "mean":
        return sum(path_list)/len(path_list)
    else:
        raise ValueError(u"'distance' is wrong")

def get_connected_subgraph(grafo, giant=True):

    components=grafo.clusters(mode='weak')
    if giant:
        # Get the indices of the nodes in the largest connected component
        largest_component_name = components.giant().vs["name"]
        # Create a subgraph that includes only the nodes in the largest connected component
        subgraph = grafo.subgraph(largest_component_name)
    else:
        subgraph = grafo

    return subgraph



def warn(message):
    """Print a warning in the one style every command uses."""
    print(Fore.YELLOW + Style.BRIGHT + "WARNING: " + message + Style.RESET_ALL)


def round_report(df):
    """Round the float columns of a report to 3 decimals, or 3 significant digits below 0.1.

    A plain 3-decimal rounding would print the density of a large sparse
    network (e.g. 0.00024) as 0.0. Values below 1e-10 are written as 0.
    """
    df = df.copy()
    for col in df.columns[[np.issubdtype(t, np.floating) for t in df.dtypes]]:
        x = df[col].to_numpy(dtype=float)
        # below 1e-10 a value is floating-point noise (e.g. 7.99e-18 for a zero
        # eigenvector score), not a measure
        x = np.where(np.abs(x) < 1e-10, 0.0, x)
        with np.errstate(divide="ignore", invalid="ignore"):
            exponent = np.floor(np.log10(np.abs(x)))
        digits = np.where(np.isfinite(exponent), np.maximum(3, 2 - exponent), 3).astype(int)
        scale = 10.0 ** digits
        # + 0.0 turns -0.0 into 0.0
        df[col] = np.where(np.isfinite(x), np.round(x * scale) / scale, x) + 0.0
    return df


def component_table(grafo):
    """One row per node: its connected component (1 = the largest) and degree.

    The report of `extract` and `set`; the network itself is written next to it.
    Components of equal size are numbered in the order of their first node.
    """
    comps = sorted(grafo.connected_components(mode="weak"), key=lambda c: (-len(c), min(c)))
    rank = {v: i for i, comp in enumerate(comps, start=1) for v in comp}
    degree = grafo.degree()
    names = grafo.vs["name"]
    order = sorted(range(grafo.vcount()), key=lambda v: (rank[v], v))
    return pd.DataFrame({"Node": [names[v] for v in order],
                         "Component": [rank[v] for v in order],
                         "Degree": [degree[v] for v in order]})


def _components_by_size(grafo):
    comps = grafo.connected_components(mode="weak")
    return comps, sorted(range(len(comps)), key=lambda i: (-len(comps[i]), min(comps[i])))


def _keep_components(grafo, comps, chosen):
    keep = sorted(v for i in chosen for v in comps[i])
    out = grafo.induced_subgraph(keep)
    if out.ecount() == 0:
        raise ValueError("the selected components have no edges, so there is no network to write")
    return out, component_table(out)


def set_operation(g1, g2, operation):
    """Union, intersection or difference of two networks, matched by node name.

    union keeps every node and edge of both; intersection the edges found in
    both; difference the edges of the first that the second lacks. The last
    two keep only the nodes those edges touch. An edge keeps the weight it has
    in the first network, or in the second for an edge only the second has.
    """
    def edges(g):
        names = g.vs["name"]
        w = g.es["weight"] if "weight" in g.es.attributes() else [1.0] * g.ecount()
        return {tuple(sorted((names[e.source], names[e.target]))): x for e, x in zip(g.es, w)}

    e1, e2 = edges(g1), edges(g2)
    if operation == "union":
        kept = dict(e2)
        kept.update(e1)
        nodes = list(g1.vs["name"]) + [v for v in g2.vs["name"] if v not in set(g1.vs["name"])]
    elif operation == "intersection":
        kept = {k: w for k, w in e1.items() if k in e2}
    elif operation == "difference":
        kept = {k: w for k, w in e1.items() if k not in e2}
    else:
        raise ValueError("unknown set operation: " + str(operation))
    if operation != "union":
        touched = {v for k in kept for v in k}
        nodes = [v for v in g1.vs["name"] if v in touched]
    if not kept:
        raise ValueError(f"the {operation} of the two networks has no edges, so there is no network to write")
    index = {v: i for i, v in enumerate(nodes)}
    out = ig.Graph(n=len(nodes), edges=[(index[a], index[b]) for a, b in kept])
    out.vs["name"] = nodes
    out.vs["label"] = nodes
    out.es["weight"] = list(kept.values())
    return out


def extract_and_df(grafo, ncomponents=False):
    """The largest component, the n largest (n > 0), or all but the n smallest (n < 0)."""
    comps, by_size = _components_by_size(grafo)
    n = int(ncomponents) if ncomponents else 1
    if abs(n) > len(comps) or (n < 0 and abs(n) == len(comps)):
        raise ValueError(f"the network has {len(comps)} component(s): cannot "
                         + (f"keep the {n} largest" if n > 0 else f"drop the {-n} smallest"))
    return _keep_components(grafo, comps, by_size[:n])


def selecting_component(grafo, selectedComponent):
    """The n-th largest component (1 = the largest)."""
    comps, by_size = _components_by_size(grafo)
    n = int(selectedComponent)
    if not 1 <= n <= len(comps):
        raise ValueError(f"the network has {len(comps)} component(s): -sc must be between 1 and {len(comps)}")
    return _keep_components(grafo, comps, [by_size[n - 1]])


def components_by_nodes(grafo, node_list):
    """Every component that contains at least one of the given nodes."""
    g = plain_copy(grafo, directed=False)
    unknown = sorted(set(node_list) - set(g.vs["name"]))
    if unknown:
        raise ValueError("nodes not in the network: " + ", ".join(unknown))
    comps, by_size = _components_by_size(g)
    wanted = {g.vs.find(name=v).index for v in node_list}
    return _keep_components(g, comps, [i for i in by_size if wanted & set(comps[i])])


def distance_matrix(graph, weights=None, dtype=np.float64, chunk=512):
    """All-pairs shortest-path lengths as an (n, n) numpy array, ``inf`` if unreachable.

    ``graph.distances()`` returns n lists of n Python floats -- about 32 bytes
    per cell against 8 in an array -- and the caller then copies them into numpy
    anyway: at n = 10k that is a 3.2 GB list next to a 0.8 GB array. Filling
    the array a block of source rows at a time keeps only one block of Python
    objects alive.
    """
    n = graph.vcount()
    out = np.empty((n, n), dtype=dtype)
    for start in range(0, n, chunk):
        stop = min(n, start + chunk)
        out[start:stop] = graph.distances(source=range(start, stop), weights=weights, mode=ig.ALL)
    return out


def path_lengths(graph):
    """Edge lengths to hand to igraph's path searches: None when every length
    is 1, so igraph runs a BFS instead of a Dijkstra that gives the same answer."""
    w = graph.es["weight"] if "weight" in graph.es.attributes() else None
    if w is None or all(x == 1 for x in w):
        return None
    return w


def finite_max(sps, chunk=512):
    """Largest finite entry of a distance matrix: the diameter of the graph it
    was computed on (igraph's, with unconnected pairs ignored), without another
    all-pairs search. Read a block of rows at a time so the finiteness mask
    never spans the whole matrix."""
    best = 0.
    for start in range(0, sps.shape[0], chunk):
        block = sps[start:start + chunk]
        block = block[np.isfinite(block)]
        if block.size:
            best = max(best, float(block.max()))
    return best
