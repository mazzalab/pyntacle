import pandas as pd
import igraph as ig
import numpy as np
from itertools import repeat
# from numba import prange
import csv
import matplotlib.pyplot as plt
import warnings
import math

from generate import *

###### Read Adjacency Matrix ######

def import_adjMatrix(file, sep=None, header=True, directed=False, weight=False):
    
    if header:
        adjMatrix = pd.read_csv(file, sep = sep, index_col=0, engine='python')
        node_names = adjMatrix.index.tolist()
    else:
        adjMatrix = pd.read_csv(file, sep=sep, header=None, engine='python')
        adjMatrix.index="n"+adjMatrix.index.astype(str)
        node_names = adjMatrix.index.tolist()
    
    if directed:
        mode="directed"
        #raise TypeError("ERROR: Your graph is directed !")
    else:
        mode="undirected"
        
    if weight:
        grafo = ig.Graph.Weighted_Adjacency(adjMatrix.values.tolist(), mode=mode, attr="weight") 
        grafo.vs["label"] = node_names
        grafo.es["width"] = grafo.es["weight"]
        grafo.vs["name"] = node_names
    else:
        grafo = ig.Graph.Adjacency(adjMatrix.values.tolist(), mode=mode)
        grafo.vs["label"] = node_names
        grafo.vs["name"] = node_names
        
    return grafo


###### Read Edge List ######

def edgeGraph(df_edge, weight, directed=False):

    grafo = ig.Graph.TupleList(df_edge.values.tolist(), directed=directed, weights=weight)

    # Self-loops and parallel edges both corrupt the adjacency-matrix view the
    # Cython engine works on (a loop lands on the diagonal, a duplicate makes the
    # cell read as a weight of 2). Collapse them for directed graphs too, which
    # the previous `if not directed` guard skipped entirely.
    loops = sum(1 for e in grafo.es if e.source == e.target)
    duplicates = grafo.ecount() - len(set(
        (min(e.tuple), max(e.tuple)) for e in grafo.es if e.source != e.target))
    if loops:
        print(f"[Warning] Removed {loops} self-loop(s) from the input network")
    if duplicates:
        print(f"[Warning] Merged {duplicates} parallel edge(s), keeping the maximum weight")
    grafo.simplify(multiple=True, loops=True, combine_edges=max)

    grafo.vs["label"] = list(grafo.vs["name"])

    return grafo


def import_edgeList(file, sep= None, header=True, directed=False, weight=False):
    
    if header:
        df_edge = pd.read_csv(file, sep=sep, engine='python')
    else:
        df_edge = pd.read_csv(file, sep = sep, names=["V1","V2","weight"],  engine='python')

    if weight:
        if len(df_edge.columns) == 2 or df_edge.iloc[:, 2].isna().any():
            df_edge['weight'] = 1
        else:
            df_edge['weight'] = df_edge.iloc[:, 2].astype(float)
            df_edge = df_edge.loc[:, [df_edge.columns[0], df_edge.columns[1], 'weight']]
    else:
        df_edge['weight'] = 1

    grafo = edgeGraph(df_edge, weight, directed)

    return grafo


###### Read SIF File ######

def import_sif(file, sep= None, header=True, directed=False, weight=False):

    if header:
        df_edge = pd.read_csv(file, sep=sep, engine='python')
    else:
        df_edge = pd.read_csv(file, sep = sep, names=["V1","Interaction","V2","weight"],  engine='python')

    df_edge = df_edge.drop(df_edge.columns[1], axis=1)

    if weight:
        if len(df_edge.columns) == 2 or df_edge.iloc[:, 2].isna().any():
            print("\nWarning: weight column not found, adding default weight of 1\n")
            df_edge['weight'] = 1
        else:
            df_edge['weight'] = df_edge.iloc[:, 2]
            df_edge = df_edge.loc[:, [df_edge.columns[0], df_edge.columns[1], 'weight']]

    grafo = edgeGraph(df_edge, weight, directed)

    return grafo


###### Read DOT File ######

def import_dot(file, directed=False, weight=False):
    import pygraphviz as gdot
    import warnings
    
    grafo = ig.Graph(directed=directed)
    gviz = gdot.AGraph(file)

    grafo.add_vertices(gviz.nodes())
    grafo.add_edges(gviz.edges())
    
    if directed:
        warnings.warn("Your input file is currently considered to be directed graph!")
    else:
        mode="undirected"
        print("[Warning] Your input file is currently considered to be undirected graph!")

    if weight:
        weights=[]
        for edge in gviz.edges():
            weights.append(edge.attr['weight'])
        grafo.es["weight"] = weights
        grafo.es["width"] = grafo.es["weight"]

    #new
    names=[]
    for node in gviz.nodes():
        names.append(node.attr['name'])
    
    # `name` is mandatory downstream (vs.find(name=...) is used everywhere), so
    # fall back to the DOT node ids rather than leaving the attribute unset.
    if None in names:
        names = [str(node) for node in gviz.nodes()]
    grafo.vs["label"] = names
    grafo.vs["name"] = names

    # print("QUI")
    return grafo




###### dummy functions

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

    The Cython engine hands the network to igraph as a weighted adjacency matrix
    built with ``get_adjacency(attribute="weight", default=0)``. In that
    representation 0 means "no edge", so a genuine 0-weight edge silently
    disappears: a path 0-1-2-3 whose middle weight is 0 is seen as two components
    by the engine and as one by igraph. There is no way to tell the two apart
    downstream, so refuse the input here rather than return a wrong number.

    Sub-unit weights are legal but make the distance-based scores (dR, group
    closeness, radiality) leave the [0, 1] range, so they earn a warning.
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
            "The network contains edge weights below 1. Weights are used directly as "
            "distances, so dR, group closeness and radiality are not bounded in [0, 1] "
            "for this input.",
            RuntimeWarning, stacklevel=2)


def subtract_count_dist_matrix(count_all, count_nogroup):
    if count_all.shape[0] == count_all.shape[1] == count_nogroup.shape[0] == count_nogroup.shape[1]:
        v = count_all.shape[0]
        res = np.copy(count_all)
        for i in range(v):
            for j in range(i, v):
                if count_all[j, i] == count_nogroup[j, i]:
                    res[i, j] = count_all[i, j] - count_nogroup[i, j]
        return res
    else:
        raise WrongArgumentError(u"Parameter error", "The function parameters do not have the same shape")



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



def summary_to_df(grafo, dir, g1, g2):
        
    edges_listTouple=grafo.get_edgelist()
    components=grafo.clusters(mode='weak')
    #vertex=components.giant().vs["name"]
    vertex=grafo.vs["name"]
    
    # Get the indices of the nodes in the largest connected component
    largest_component_indices = components.giant().vs["name"]
    # Create a subgraph that includes only the nodes in the largest connected component
    subgraph = grafo.subgraph(largest_component_indices)
    
    edges=[]
    for edges_tuple in edges_listTouple:
        v_names = []
        for v in list(edges_tuple):
            v_names.append(grafo.vs[v]["name"])
        edges.append(v_names)
    if len(edges)>0:
        if (len(vertex)-len(edges))>0:
            df =  pd.DataFrame({"Merged from" : [g1, g2] + [""] +["Vertex"] + vertex, 
                                "": list(repeat("", 3)) + ["Edges"] + edges + list(repeat("", len(vertex)-len(edges)))
                                })
        else:
            df =  pd.DataFrame({"Merged from" : [g1, g2] + [""] +["Vertex"] + vertex + list(repeat("", len(edges)-len(vertex))), 
                                "": list(repeat("", 3)) + ["Edges"] + edges 
                                })

        return df
    else:
        raise ValueError("The resulting graph doesn't contain any edges")



def extract_and_df(grafo,ncomponents=False):

    components=grafo.clusters(mode='weak') #

    if len(components)<=abs(int(ncomponents)): 
        print(f"Your graph has {len(components)} components")
        raise ValueError("The number of requested components is higher than the components in the graph")

    if ncomponents:
        # Get the cluster sizes along with their ids
        cluster_sizes = [(i, len(c)) for i, c in enumerate(components)]

        # Sort the clusters by size in descending order
        sorted_clusters = sorted(cluster_sizes, key=lambda x: x[1], reverse=True)

        # Now you can retrieve the first N largest clusters
        largest_clusters = sorted_clusters[:int(ncomponents)]

        # If you want to get the actual vertex idsname for these clusters
        #largest_clusters_ids = [components[i[0]] for i in largest_clusters]
        largest_subgraphs = [components.subgraph(i[0]) for i in largest_clusters]
        # Now 'largest_clusters_ids' contains the vertex ids of the first N largest clusters

        # Compute separate layouts for each subgraph
        layouts = [subgraph.layout('fr') for subgraph in largest_subgraphs]

        # Determine the bounding box for each layout
        bounding_boxes = []
        for layout in layouts:
            x_coords, y_coords = zip(*layout.coords)
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            bounding_boxes.append((min_x, max_x, min_y, max_y))

        # Adjust the layouts so the subgraphs do not overlap
        max_x_so_far = 0
        for i, layout in enumerate(layouts):
            min_x, max_x, min_y, max_y = bounding_boxes[i]
            x_offset = max_x_so_far - min_x + 1  # We add a space of 1 to avoid overlap
            for pos in layout:
                pos[0] += x_offset
            max_x_so_far += (max_x - min_x) + 1

        # Combine all the layouts into one
        combined_layout = [pos for layout in layouts for pos in layout.coords]

        # Combine all the subgraphs into one graph for plotting
        output_graph = ig.Graph()
        for subgraph in largest_subgraphs:
            output_graph = output_graph.disjoint_union(subgraph)

        # Plot the combined graph using the combined layout
        vertex=list(output_graph.vs["name"])


    else:
        vertex=components.giant().vs["name"]
        largest_component_name = components.giant().vs["name"]
        output_graph = grafo.subgraph(largest_component_name)

    print(output_graph.summary())
    edges_listTouple=output_graph.get_edgelist()
    edges=[]
    for edges_tuple in edges_listTouple:
        v_names = []
        for v in list(edges_tuple):
            v_names.append(output_graph.vs[v]["name"])

        edges.append(v_names)

    if len(edges)>0:
        if (len(vertex)-len(edges))>0:
            df =  pd.DataFrame({"Vertex": vertex,"Edges":edges + list(repeat("", len(vertex)-len(edges)))})
        else:
            df =  pd.DataFrame({"Vertex": vertex + list(repeat("", len(edges)-len(vertex))),"Edges":edges})
    else:
        raise ValueError("The resulting graph doesn't contain any edges")
    
    return output_graph,df



def selecting_component(grafo,selectedComponent):
    components=grafo.clusters(mode='weak') # 

    if len(components)<=abs(int(selectedComponent)): 
        print(f"Your graph has {len(components)} components")
        raise ValueError("The number of requested components is higher than the components in the graph")

    # Get the cluster sizes along with their ids
    cluster_sizes = [(i, len(c)) for i, c in enumerate(components)]

    # Sort the clusters by size in descending order
    sorted_clusters = sorted(cluster_sizes, key=lambda x: x[1], reverse=True)

    # Now you can retrieve the first N largest clusters
    selected_component = sorted_clusters[int(selectedComponent)-1]
    
    output_graph = ig.Graph()
    output_graph = components.subgraph(selected_component[0])

    # Plot the combined graph using the combined layout
    vertex=list(output_graph.vs["name"])

    edges_listTouple=output_graph.get_edgelist()
    edges=[]
    for edges_tuple in edges_listTouple:
        v_names = []
        for v in list(edges_tuple):
            v_names.append(output_graph.vs[v]["name"])
        edges.append(v_names)

    if len(edges)>0:
        if (len(vertex)-len(edges))>0:
            df =  pd.DataFrame({"Vertex": vertex,"Edges":edges + list(repeat("", len(vertex)-len(edges)))})
        else:
            df =  pd.DataFrame({"Vertex": vertex + list(repeat("", len(edges)-len(vertex))),"Edges":edges})
    else:
        raise ValueError("The resulting graph doesn't contain any edges")
    
    return output_graph,df


# Function to apply the modified logic
def process_row_modified(row):
    found_non_zero = False
    non_zero_count = 0

    for col in ['size_F', 'size_df', 'size_dR', 'size_mreach']:
        if not found_non_zero and row[col] != 0:
            found_non_zero = True
        elif found_non_zero and row[col] != 0:
            non_zero_count += 1
            row[col] = max(0, row[col] - non_zero_count)

    # Modify 3 to 4 and 4 to 8
    for col in ['size_F', 'size_df', 'size_dR', 'size_mreach']:
        if row[col] == 3:
            row[col] = 4
        elif row[col] == 4:
            row[col] = 8

    return row



def components_by_nodes(grafo,node_list): # node_list=name

    g=plain_copy(grafo, directed=False)

    components=g.connected_components(mode='weak')

    # Get the cluster sizes along with their ids
    cluster_sizes = [(i, len(c)) for i, c in enumerate(components)]

    # Sort the clusters by size in descending order
    sorted_clusters = sorted(cluster_sizes, key=lambda x: x[1], reverse=True)
    keep_component=[]
    
    for component in sorted_clusters:
        componenti=components.subgraph(component[0]).vs["name"]
        common_elements = [element for element in componenti if element in node_list]
        if common_elements!=[]:
            keep_component.append(components.subgraph(component[0]))

    output_graph = ig.Graph()
    for subgraph in keep_component:
        output_graph = output_graph.disjoint_union(subgraph)


### creating dataframe
# Plot the combined graph using the combined layout
    vertex=list(output_graph.vs["name"])

    edges_listTouple=output_graph.get_edgelist()
    edges=[]
    for edges_tuple in edges_listTouple:
        v_names = []
        for v in list(edges_tuple):
            v_names.append(output_graph.vs[v]["name"])
        edges.append(v_names)

    if len(edges)>0:
        if (len(vertex)-len(edges))>0:
            df =  pd.DataFrame({"Vertex": vertex,"Edges":edges + list(repeat("", len(vertex)-len(edges)))})
        else:
            df =  pd.DataFrame({"Vertex": vertex + list(repeat("", len(edges)-len(vertex))),"Edges":edges})
    else:
        raise ValueError("The resulting graph doesn't contain any edges")
    
    return output_graph,df




def create_subplots(df, columns,topN):
    # Calculate the number of rows needed for the subplots based on the number of columns to plot
    if topN > len(df):
        topN= int(len(df) * 0.1)
        print(f"The number of nodes in your graph is less than the given \'-n\', so only the top {topN} will be displayed")

    nvar = len(columns)
    ncol=2
    nrows=nvar//ncol+bool(nvar%ncol)

    fig, axes = plt.subplots(nrows=nrows, ncols=ncol, figsize=(10, 6 * nrows), constrained_layout=True)

    for i in range(nvar):
        plt.subplot(nrows,ncol,i+1)
        # Sort the dataframe by the current column in descending order and take the top 10
        df_top10_sorted = df.sort_values(by=columns[i], ascending=False).head(topN)
        
        # Create a bar plot on the current axes
        plt.bar(df_top10_sorted['Node Name'], df_top10_sorted[columns[i]])
        
        size_factor = max(8 / len(df_top10_sorted['Node Name']), 6)

        # Plot with dynamically adjusted font size
        plt.xticks(df_top10_sorted['Node Name'], rotation=90, fontsize=size_factor)
        # Rotate x-axis labels
        plt.xticks(df_top10_sorted['Node Name'], rotation=90)
        
        # Set the title and labels for the subplot
        plt.title(f'Top {topN} Nodes for {columns[i]}')
        plt.xlabel('Node Name')
        plt.ylabel(f'{columns[i]}')
        plt.grid(axis='y', alpha=0.75)

    return fig


###### FUNCTION FOR DEBUGING #####################################################################################
def print_adjacency_matrix_with_vertices(graph):
    # Custom sorting function: numbers first (sorted numerically), then alphabetic
    def sort_key(name):
        return (not name.isdigit(), int(name) if name.isdigit() else name)

    vertices = sorted(graph.vs["name"], key=sort_key)

    # Reorder the graph according to the sorted vertex names
    vertex_mapping = {old_index: vertices.index(name) for old_index, name in enumerate(graph.vs["name"])}
    reordered_graph = graph.permute_vertices([vertex_mapping[i] for i in range(len(graph.vs))])

    # Convert the adjacency matrix of the reordered graph to a numpy array
    adj_matrix = np.array(reordered_graph.get_adjacency().data)

    # Prepare the string for printing the matrix
    matrix_str = "   " + "  ".join(vertices) + "\n"
    for i, row in enumerate(adj_matrix):
        matrix_str += vertices[i] + "  " + "  ".join(map(str, row)) + "\n"

    # Print the formatted adjacency matrix
    print(matrix_str)



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
