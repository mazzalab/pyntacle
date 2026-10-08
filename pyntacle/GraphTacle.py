import igraph as ig
import matplotlib.pyplot as plt
from statistics import mean
import pandas as pd
import numpy as np
import os
import math
import itertools
import pickle as pk
import warnings
from pyntacle.utility import *


def _component_block(sps, members):
    """Rows and columns of one component in an all-pairs distance matrix (None
    when there is no matrix). Components are disconnected from each other, so
    the block is exactly the component's own distance matrix."""
    if sps is None:
        return None
    return np.asarray(sps)[np.ix_(members, members)]


class Graphtacle(ig.Graph, ig.GraphBase):
    """Extended igraph.Graph subclass for Pyntacle network analysis.

    Adds file I/O, local/global topology metrics (radiality, completeness,
    compactness), group centrality measures (degree, betweenness, closeness),
    and visualization helpers on top of the standard igraph API.

    Attributes:
        fileType (str): Input file format (matrix, edgelist, sif, dot).
        name (str): Graph name derived from the input file basename.
        function (str): Active Pyntacle command (local, global, keyplayer, …).
    """

    # edge attributes that carry the weight semantics besides es["weight"]
    WEIGHT_VIEWS = ("raw_weight", "affinity", "sign")
    # commands whose metrics read es["weight"] as a path length
    DISTANCE_COMMANDS = ("local", "global", "keyplayer", "groupcentrality")

    def __init__(self, nodes,edges,names,labels,weights,directed,fileType,sep,header,graph_name,function,
                 weight_views=None, weight_info=None, raw_weights=False):

        # The vertex count is passed explicitly so that isolated vertices are
        # kept. `nodes` is an int when unpickled (__reduce__) and a list of
        # indices when built by re()/from_file().
        n = nodes if isinstance(nodes, int) else len(nodes)
        # the sub-unit warning concerns distances: only the commands that use
        # weights as path lengths check for it
        validate_weights(weights, warn_sub_unit=not raw_weights and function in self.DISTANCE_COMMANDS)
        edge_attrs = {"weight": weights}
        edge_attrs.update(weight_views or {})
        super().__init__(n=n,
                         directed=directed,
                         vertex_attrs={"name":names,"label": labels},
                         edges=edges,
                         edge_attrs=edge_attrs)
        # how es["weight"] was obtained: {"type": ..., "transform": ...}, or None
        # when the weights are the raw values (file conversions) or absent
        self.weight_info = weight_info
        
        self.iNodes=[v.index for v in self.vs]
        self.fileType = fileType
        self.name = os.path.split(os.path.splitext(graph_name)[0])[1]  # file name without path or extension
        self.function = function  # command, e.g. local, global, keyplayer
        self.sep = sep
        self.header=header
        self.directed=directed
        # per-instance analysis state (the set command holds two graphs at once)
        self.removed = None
        self.sub_func = ""
        self.outdir = ""
        self.memory=[fileType,sep,header,graph_name,function]
        self.memories=[nodes,edges,names,labels,weights,directed,fileType,sep,header,graph_name,function]
        

    @classmethod
    def re(cls, grafo, func, fileType,sep=None, header=True, directed=False, weight=False, file="file_name"):
        """Rebuild a Graphtacle from an igraph graph (e.g. after removing
        nodes), keeping the weight views and their provenance."""

        nodes = [v.index for v in grafo.vs]
        edges = grafo.get_edgelist()
        names = grafo.vs["name"]
        labels = grafo.vs["label"]
        graph_name = file
        function = func
        fileType = fileType
        
        views, info = None, None
        if weight:
            weights = grafo.es["weight"]
            views = {a: grafo.es[a] for a in cls.WEIGHT_VIEWS if a in grafo.es.attributes()}
            info = getattr(grafo, "weight_info", None)
        else:
            weights=1
        return cls(nodes,edges,names,labels,weights,directed,fileType,sep,header,graph_name, function,
                   weight_views=views, weight_info=info, raw_weights=bool(weight) and info is None)


    @classmethod
    def from_file(cls, file, func, fileType, sep: str or None = None, header: bool = True, directed: bool = False, weight: bool = False,
                  weight_type=None, distance_transform="inverse"):
        """Construct a Graphtacle by loading a network file.

        Args:
            file (str): Path to the input network file.
            func (str): Pyntacle command being executed (e.g. ``local``).
            fileType (str): One of ``matrix``, ``edgelist``, ``sif``, ``dot``.
            sep (str | None): Column separator. None uses whitespace/tab auto-detect.
            header (bool): True if the file has a header row.
            directed (bool): True to load as a directed graph.
            weight (bool): True to parse edge weights.
            weight_type (str | None): What the weights are: ``distance``,
                ``affinity`` or ``signed`` (see utility.weight_views). With
                None the weights are kept exactly as read, for commands that
                only write the network back out.
            distance_transform (str): Strength-to-length transform for
                ``affinity`` and ``signed``: inverse, one-minus or neglog.

        Returns:
            Graphtacle: Loaded graph object.

        Raises:
            TypeError: If fileType is not recognized.
        """
        function = func
        graph_name = file
        fileType = str(fileType)
        
        if fileType=="matrix":
            grafo=import_adjMatrix(file,sep,header,directed,weight)
        elif fileType=="edgelist":
            grafo=import_edgeList(file,sep,header,directed,weight)
        elif fileType=="sif":
            grafo=import_sif(file,sep,header,directed,weight)
        elif fileType=="dot":
            grafo=import_dot(file,directed,weight)
        else:
            raise TypeError("ERROR: Check the format of your file")

        nodes = [v.index for v in grafo.vs]
        edges = grafo.get_edgelist()
        names = grafo.vs["name"]
        labels = grafo.vs["label"]
        
        views, info = None, None
        if weight:
            raw = [float(number) for number in grafo.es["weight"]]
            if weight_type is None:
                weights = raw
            else:
                v = weight_views(raw, weight_type, distance_transform)
                # es["weight"] is always a length, so every shortest-path
                # consumer (igraph and the compiled kernels) reads it unchanged
                weights = v["distance"]
                views = {"raw_weight": raw, "affinity": v["affinity"], "sign": v["sign"]}
                info = {"type": weight_type, "transform": distance_transform}
        else:
            weights=1

        return cls(nodes,edges,names,labels,weights,directed,fileType,sep,header,graph_name, function,
                   weight_views=views, weight_info=info, raw_weights=bool(weight) and weight_type is None)

    def __reduce__(self):
        # pickling support: rebuild the instance through __init__
        nodes = len(self.vs)
        edges = self.get_edgelist()
        names = self.vs["name"]
        labels = self.vs["label"]
        weights = self.es["weight"]
        views = {a: self.es[a] for a in self.WEIGHT_VIEWS if a in self.es.attributes()} or None
        directed = self.is_directed()
        fileType = self.fileType
        sep = self.sep
        header = self.header
        graph_name = os.path.splitext(self.name)[0]
        function = self.function

        return (self.__class__, (nodes, edges, names, labels, weights, directed, fileType, sep, header, graph_name, function,
                                 views, self.weight_info))

    
    def remove_node(self,node):
        self.removed=node

    def nameSub_function(self,funct):
        self.sub_func=funct

    def path_function(self,outdir):
        self.outdir=outdir

    def affinities(self):
        """Tie strengths for strength-based metrics (clustering, eigenvector,
        PageRank, communities, TI): es["affinity"] when the weights were
        declared, otherwise es["weight"] (all 1 on an unweighted graph)."""
        if "affinity" in self.es.attributes():
            return self.es["affinity"]
        return self.es["weight"]

    def get_edge_weight(self, start, end):
        return self.es[self.get_eid(start, end)]['weight']

    def export_file(self, df, outdir, notes=None):
        """Write a TSV report file with a standard Pyntacle header.

        The report contains: project header, analysis type, network overview
        (nodes, edges, components, removed nodes), and the data DataFrame.

        Args:
            df (pandas.DataFrame): Results table to append after the header.
            outdir (str | None): Output directory. If None, writes to the
                current working directory.
            notes (list[str] | None): Extra header lines, written between the
                network overview and the table. Brute-force runs use them to
                state how many node sets reach the optimum.

        Returns:
            str: Path of the report that was written.
        """
        stem = f"report_{self.name}_{self.function}"
        if self.sub_func:
            stem = f"{stem}_{self.sub_func}"
        # not stored on self.name, so that repeated calls do not nest the prefix
        filename = f"{outdir}/{stem}.tsv" if outdir else f"{stem}.tsv"

        with open(filename, "w") as f:
            f.write(f"Pyntacle report\t{filename.strip().split('/')[-1]}\n")
            f.write(f"Analysis type\t{self.function}\n")
            f.write("\nNetwork Overview\n")
            f.write(f"Removed nodes\t{self.removed}\n")
            f.write(f"Number of components\t{len(self.components())}\n")
            f.write(f"Number of Nodes\t{len(self.vs['label'])}\n")
            f.write(f"Number of Edges\t{len(self.get_edgelist())}\n")
            f.write(f"Edge weights\t{describe_weights(getattr(self, 'weight_info', None))}\n\n")
            for line in notes or []:
                f.write(f"{line}\n")
            if notes:
                f.write("\n")
            f.write(df.to_csv(sep="\t", index=False))

        return filename
            

    def plot_node_sets(self, sets, path, others="other nodes"):
        """Draw the network with the node sets highlighted and save it to `path`.

        `sets` is a list of (label, nodes). One set is drawn in yellow with no
        legend. Several sets each get a colour and a legend entry; a node in m
        sets is drawn as m concentric discs, the first set's the largest.
        """
        layout = self.layout('kk')
        coord = np.array(layout)
        ed = np.array(self.get_edgelist())
        lines = np.moveaxis(coord[ed[:, :]], 0, -1)
        cord_df = pd.DataFrame({"X": coord[:, 0], "Y": coord[:, 1]}, index=list(self.vs["name"]))

        plt.figure(figsize=(20, 20))
        for label, (x, y) in zip(list(self.vs["name"]), coord):
            plt.text(x, y, label, ha='center', va='center', ma='center', zorder=20, fontsize=5)
        plt.plot(lines[:, 0, :], lines[:, 1, :], c='black', alpha=0.2, linewidth=1.5, zorder=1)
        plt.scatter(cord_df["X"], cord_df["Y"], c="#BDC3C7", alpha=1, zorder=10, s=100)

        if len(sets) == 1:
            nodes = list(dict.fromkeys(sets[0][1]))
            plt.scatter(cord_df.loc[nodes, "X"], cord_df.loc[nodes, "Y"], c="#F4D03F", alpha=1, zorder=11, s=200)
        else:
            colors = ["#F4D03F", "#2ECC71", "#3498DB", "#EC7063"]
            members = [set(nodes) for _label, nodes in sets]
            for i, nodes in enumerate(members):
                rows = []
                for node in nodes:
                    holders = [j for j, m in enumerate(members) if node in m]
                    # the first set holding the node gets the widest disc, later ones nest inside
                    size = len(holders) - holders.index(i)
                    rows.append((node, {3: 4, 4: 8}.get(size, size)))
                rows = [(node, size) for node, size in rows if size > 0]
                plt.scatter(cord_df.loc[[n for n, _ in rows], "X"], cord_df.loc[[n for n, _ in rows], "Y"],
                            c=colors[i % len(colors)], alpha=1, zorder=11 + i,
                            s=np.array([size for _, size in rows]) * 300)
            labels = [others] + [label for label, _nodes in sets]
            fills = ["#BDC3C7"] + [colors[i % len(colors)] for i in range(len(sets))]
            patches = [plt.plot([], [], marker="o", ms=10, ls="", mec=None, color=c, label=l)[0]
                       for c, l in zip(fills, labels)]
            plt.legend(title="Nodes color", frameon=True, handles=patches, loc="best")

        plt.axis('off')
        plt.savefig(path)
        plt.close()
        return path

    def plot_set(self, filename1, filename2, g1_names, g2_names, path):
        """Draw a union with the nodes of each input network coloured and save it to `path`."""

        coord = np.array(self.layout('kk'))
        lines = np.moveaxis(coord[np.array(self.get_edgelist())], 0, -1)
        names = list(self.vs["name"])
        in1, in2 = set(g1_names), set(g2_names)
        groups = [[i for i, n in enumerate(names) if n in in1 and n not in in2],
                  [i for i, n in enumerate(names) if n in in2 and n not in in1],
                  [i for i, n in enumerate(names) if n in in1 and n in in2]]
        colors = ["#2ECC71", "#3498DB", "#EC7063"]
        # two inputs with the same file name are told apart by their order
        texts = ([filename1, filename2] if filename1 != filename2
                 else [f"{filename1} (first)", f"{filename2} (second)"]) + ["Common"]

        plt.figure(figsize=(20,20))
        for label, (x, y) in zip(names, coord):
            plt.text(x, y, label, ha='center', va='center', ma='center', zorder=20,fontsize=5)
        plt.plot(lines[:,0, :], lines[:, 1, :], c='black', alpha=0.2, linewidth=1.5, zorder=1)
        for z, (idx, c) in enumerate(zip(groups, colors)):
            plt.scatter(coord[idx, 0], coord[idx, 1], c=c, alpha=1, zorder=11 + z, s=100)

        patches = [plt.plot([], [], marker="o", ms=10, ls="", mec=None, color=c, label=t)[0]
                   for c, t in zip(colors, texts)]
        plt.legend(title="Nodes color",frameon=True,handles=patches,loc="best")
        plt.axis('off')
        plt.savefig(path)
        plt.close()
        return path


    def radiality(self, sps=None, diameter=None):
        """Compute radiality centrality for all nodes.

        Radiality of node i = sum over the nodes j it reaches of
        (diameter + 1 - d(i, j)), divided by N - 1. On a connected network this
        is (diameter + 1) - the mean distance from i; a node that reaches nothing
        scores 0.

        Args:
            sps: optional precomputed weighted all-pairs shortest-path matrix
                (list of rows). If None it is computed once here.
            diameter: optional precomputed diameter, in the unit of ``sps``.
                If None it is the largest finite entry of ``sps``.

        Returns:
            list[float]: Radiality score for each node in vertex order.
        """
        radiality=[]
        weights = self.es["weight"] if "weight" in self.es.attributes() else None
        if sps is None:
            sps = distance_matrix(self, weights=weights)

        sps = np.asarray(sps, dtype=float)
        if diameter is None:
            diameter = finite_max(sps)
        norm = self.vcount() - 1

        for node in self.iNodes:
            row = sps[node]
            reachable = row[np.isfinite(row)]
            # each other node it reaches adds diameter + 1 - distance; a node it
            # cannot reach adds nothing (the node itself is the one 0 in the row)
            radiality.append(((reachable.size - 1) * (diameter + 1) - reachable.sum()) / norm)

        return radiality
    
    
    
    
    def radiality_reach(self, nodes=None, sps=None, diameter=None):
        comps = self.components()
        if len(comps) == 1:
            return self.radiality(sps=sps, diameter=diameter)
        else:
            tot_nodes = self.vcount()
            # one plain igraph copy, sliced per component: induced_subgraph cannot
            # build a Graphtacle (its __init__ has a different signature)
            base = plain_copy(self, directed=False)
            if nodes is None:
                result = [None] * tot_nodes

                for c in comps:
                    subg = base.induced_subgraph(c)
                    subg = Graphtacle.re(subg, self.function, self.fileType, self.sep, self.header, self.directed, self.es["weight"], self.name)
                    if subg.ecount() == 0:  # isolates do not have a radiality-reach value by definition
                        rad = [0]
                    else:
                        part_nodes = subg.vcount()
                        rad = subg.radiality(sps=_component_block(sps, c))
                        # scaling the radiality by weighting it over the total number of nodes
                        proportion_nodes = part_nodes / tot_nodes
                        rad = [r * proportion_nodes for r in rad]
                    for i, ind in enumerate(c):
                        result[ind] = rad[i]
                return result
            else:
                result = [None] * len(nodes)
                for c in comps:
                    comp_names = set(self.vs(c)["name"])
                    wanted = [nm for nm in nodes if nm in comp_names]
                    if not wanted:
                        continue
                    subg = base.induced_subgraph(c)
                    subg = Graphtacle.re(subg, self.function, self.fileType, self.sep, self.header, self.directed, self.es["weight"], self.name)
                    part_nodes = subg.vcount()
                    if subg.ecount() == 0:  # isolates do not have a radiality-reach value by definition
                        rad = [0] * part_nodes
                    else:
                        proportion_nodes = part_nodes / tot_nodes
                        rad = [r * proportion_nodes for r in subg.radiality(sps=_component_block(sps, c))]
                    sub_names = subg.vs["name"]
                    for nm in wanted:
                        result[nodes.index(nm)] = rad[sub_names.index(nm)]
                return result

    def median_global_shortest_path_length(self, sps=None, chunk=512):
        """Median hop count over connected pairs; `sps`, if given, is the hop
        distance matrix already computed.

        Hop counts are integers, so the median is read off their histogram,
        filled a block of rows at a time: no copy of the matrix is made."""
        if sps is None:
            # hop counts are exact in float32: half the memory of the default
            sps = distance_matrix(self, dtype=np.float32)
        counts = np.zeros(1, dtype=np.int64)
        for start in range(0, sps.shape[0], chunk):
            block = sps[start:start + chunk]
            c = np.bincount(block[np.isfinite(block) & (block != 0)].astype(np.int64))
            if c.size > counts.size:
                c[:counts.size] += counts
                counts = c
            else:
                counts[:c.size] += c
        total = int(counts.sum())
        if total == 0:
            return float("nan")
        # the value at sorted position i is the first whose cumulative count exceeds i
        cum = np.cumsum(counts)
        low = int(np.searchsorted(cum, (total - 1) // 2 + 1))
        high = int(np.searchsorted(cum, total // 2 + 1))
        return (low + high) / 2

    


    def get_shortestpaths(self):
        """Weighted all-pairs distances, unreachable pairs left as ``np.inf``."""
        weights = self.es["weight"] if "weight" in self.es.attributes() else None
        return distance_matrix(self, weights=weights)



    def completeness_naive(self, directed=False):

        # total number of non-zero elements (E)
        if directed:
            num = self.ecount()
        else:
            num = self.ecount()*2

        # possible adjacency-matrix non-zeros, self-loops excluded
        node_tot = self.vcount()
        maxe = node_tot * (node_tot - 1)

        # total number of non-edges (V)
        denom = maxe - num
        if denom == 0:
            return 1
        else:
            completeness = num / denom
            return completeness


    def completeness(self, directed=False):
        
        node_tot = self.vcount()
        k = math.pow(node_tot, 2)
        # (SQRT(k) -1)
        addend_left = node_tot - 1
        # number of zeros in the matrix
        if directed:
            z = k - self.ecount()
        else:
            z = k - (self.ecount() * 2)

        #  If the graph is complete
        if z == 0:
            return 1
        else:
            addend_right = (k / z) - 1
            completeness = addend_left * addend_right
            return completeness



    def compactness(graph, directed=False):
        """Compactness: the reciprocal of the Randić and DeAlba product
        ((n²/e) − 1)(1 − 1/n), with e the adjacency-matrix non-zeros."""
        # an undirected edge occupies two cells, as in completeness()
        if directed:
            e = graph.ecount()
        else:
            e = graph.ecount() * 2

        node_tot = graph.vcount()
        addend_left = (math.pow(node_tot, 2) / e) - 1
        addend_right = 1 - (1 / node_tot)
        
        compactness = math.pow(addend_left, -1) * math.pow(addend_right, -1)

        return compactness


    def group_degree(self, nodes=None):
        """Compute group degree centrality for a set of nodes.

        Group degree = (number of non-group nodes adjacent to at least one
        group member) / (total nodes - group size).

        Args:
            nodes: Iterable of node names (labels) forming the group.

        Returns:
            float: Normalized group degree in [0, 1].
        """

        # node names to indices
        nodes_ind=[]
        for i in list(nodes):
            nodes_ind.append(self.vs.find(name=i).index)

        selected_neig = self.neighborhood(nodes, order=1, mode="all")
        flat_list = [item for sublist in selected_neig for item in sublist if item not in nodes_ind]
        normalized_score = len(set(flat_list)) / (len(self.vs) - len(nodes))

        return normalized_score


    def group_betweenness(self, nodes):
        """Compute group betweenness centrality for a set of nodes.

        For every pair of non-group nodes joined by a path, the share of its
        shortest paths with an inner node in the group; the sum is divided by
        the (N - k)(N - k - 1) / 2 pairs, k being the group size, so a group on
        every shortest path scores 1. From each source the
        vertices are settled in distance order, and the number of shortest
        paths (sigma) and of those avoiding the group are summed over each
        vertex's shortest-path predecessors, weights included.

        Args:
            nodes: Iterable of node names forming the group.

        Returns:
            float: Group betweenness score.
        """
        n = self.vcount()
        group = {self.vs.find(name=i).index for i in nodes}
        m = n - len(group)
        if m < 2:
            return 0.0

        weights = self.es["weight"] if "weight" in self.es.attributes() else [1.0] * self.ecount()
        # a zero weight is not an edge, as in the compiled kernels
        neighbours = [[] for _ in range(n)]
        for (u, v), w in zip(self.get_edgelist(), weights):
            if w != 0:
                neighbours[u].append((v, float(w)))
                neighbours[v].append((u, float(w)))

        total = 0.0
        for src in range(n):
            if src in group:
                continue
            dist = self.distances(source=src, weights=weights)[0]
            order = sorted((v for v in range(n) if math.isfinite(dist[v])), key=lambda v: dist[v])
            sigma = [0.0] * n
            avoid = [0.0] * n
            sigma[src] = avoid[src] = 1.0
            for v in order:
                if v == src:
                    continue
                # equal path lengths agree to rounding, not to the bit
                tol = 1e-10 * max(1.0, dist[v])
                for u, w in neighbours[v]:
                    if abs(dist[u] + w - dist[v]) <= tol:
                        sigma[v] += sigma[u]
                        avoid[v] += avoid[u]
                if v in group:
                    avoid[v] = 0.0
            for v in order:
                if v > src and v not in group and sigma[v] > 0:
                    total += 1.0 - avoid[v] / sigma[v]

        return 2 * total / (m * (m - 1))


    def group_closeness(self, np_paths, nodes=None, distance_type="min"):
        """Compute group closeness centrality for a set of nodes.

        Wasserman-Faust group closeness: (r / (N - k)) * (r / sum over the r
        non-group nodes j the group reaches of d(K, j)), where d(K, j) is the
        distance from group K to node j aggregated with distance_type. On a
        connected network this is (N - k) / sum d(K, j).

        Args:
            np_paths (numpy.ndarray | None): Pre-computed shortest-path matrix.
                Pass None to compute on the fly.
            nodes: Iterable of node names forming the group.
            distance_type (str): How to aggregate distances from K to j.
                One of ``min``, ``max``, ``mean``. Default ``min``.

        Returns:
            float: Group closeness score. Higher = closer to the rest of the graph.
        """
       
        if not isinstance(np_paths, (type(None), np.ndarray)):
            raise TypeError("'np_paths' is not one NoneType or a numpy array")

        if np_paths is None:
            np_paths = self.get_shortestpaths()

        # node names to indices
        group_indices=[]
        for i in list(nodes):
            group_indices.append(self.vs.find(name=i).index)

        nongroup_nodes = list(set(self.vs["name"]) - set(nodes))
        nongroup_nodes_indices = [] 
        for i in list(nongroup_nodes):
            nongroup_nodes_indices.append(self.vs.find(name=i).index)

        nongroup_np_paths = np_paths.take(nongroup_nodes_indices, axis=0)

        group_closeness = 0
        reached = 0
        for np_path in nongroup_np_paths:
            # unreachable group members are dropped, not charged a sentinel distance
            temp_list = [elem for elem in np_path[group_indices] if np.isfinite(elem)]
            if temp_list:
                group_closeness += capo_dist(temp_list,distance_type)
                reached += 1
        if group_closeness != 0:
            # Wasserman-Faust: closeness over the reached nodes, scaled by the share
            # reached; equals (N-k)/sum on a connected network
            return (reached / len(nongroup_nodes)) * (reached / group_closeness)
        # a set that reaches no other node scores 0
        return 0.0