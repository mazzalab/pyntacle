import igraph as ig
import matplotlib.pyplot as plt
from statistics import mean
import pandas as pd
import numpy as np
import os
import math
import itertools
import pickle as pk
import collections
import warnings
### home-made functions import
from utility import *


#######################################################################################################
# Creating a Subclass of iGraph in order to add new functions (imports, stats, ...) to a Graph object #
#######################################################################################################

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

    def __init__(self, nodes,edges,names,labels,weights,directed,fileType,sep,header,graph_name,function,
                 weight_views=None, weight_info=None, raw_weights=False):

        # Vertex count must be passed explicitly: otherwise igraph infers it
        # from the maximum edge index, silently dropping any isolated vertex
        # whose index is higher than every edge endpoint. `nodes` is an int
        # when reconstructed via __reduce__ (pickle) and a list of indices
        # when built by re()/from_file().
        n = nodes if isinstance(nodes, int) else len(nodes)
        # the sub-unit warning is about distances; raw weights kept only to be
        # written back out (raw_weights) are not read as anything
        validate_weights(weights, warn_sub_unit=not raw_weights)
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
        self.name = os.path.split(os.path.splitext(graph_name)[0])[1]  # name file without path
        self.function = function  # function , for example local, global, keyplayer
        self.sep = sep
        self.header=header
        self.directed=directed
        # Per-instance analysis state. These used to be class attributes assigned
        # through `Graphtacle.x = ...`, so every live graph shared one value --
        # which the `set` command, holding two graphs at once, silently corrupted.
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

    
    ### metodo costruttore 
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
        #print("\nSelect the type of input: matrix, edgelist, sif or dot\n")
        fileType = str(fileType)
        #print("\n")
        
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

#### Implement special methods: To make your subclass picklable, you need to implement the following special methods:
#### __reduce__: This method should return a tuple of callable objects (functions or classes) and their arguments that 
#### can be used to recreate the object when unpickling. The first element of the tuple is a callable that will create 
#### an instance of your class, and the second element is a tuple of arguments for that callable
    def __reduce__(self):
        # Extract necessary data for reconstruction (for load picklable objects)
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

        # Return a tuple with the class constructor and its arguments
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
        # Deliberately not stored back on self.name: doing so made a second call
        # build report_<previous report path>_... on top of the first one.
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
            

    def plot_keyplayer(self,df,filename,exp_format,operation,outdir=False):

        layout=self.layout('kk')
        coord = np.array(layout)
        ed = np.array(self.get_edgelist())
        lines = coord[ed[:,:]]
        lines = np.moveaxis(lines, 0,-1)

        names = list(self.vs["name"])
        cord_df = pd.DataFrame({"Node": names, "X": coord[:, 0], "Y": coord[:, 1]}).set_index("Node")
        #colors = ["#c73333","#71b82d","#e0c292","#186cab","#db9c2d","#f2f0ce"]
        colors = ["#BDC3C7","#F4D03F","#2ECC71","#3498DB","#EC7063"]
        texts=["not-Keyplayers","F","dF","dR","mreach"]

### processing colors
        if operation=="all":
            ###########   F       dF    dR    mreach   moreThan1
            f_x,df_x,dr_x,m_x,f_y,df_y,dr_y,m_y=[],[],[],[],[],[],[],[]
            f_names,df_names,dr_names,m_names=[],[],[],[]
            oper_names = [f_names, df_names, dr_names, m_names]
            duplicated_coord=[]
            c=0
            for c, list_nameNode in enumerate(df["Key-player"]):
                for node in list_nameNode:
                    if node not in oper_names[c]:
                        f_x.append(cord_df.loc[node, 'X'])
                        f_y.append(cord_df.loc[node, 'Y'])
                        #f_nodes = np.append(f_nodes, coord[self.vs.find(str(node)).index]) ### prendiamo l'indice del nodo e con "coord" le sue coordinate
                        oper_names[c].append(node)
    
            f_names = list(set(f_names))
            df_names = list(set(df_names))
            dr_names = list(set(dr_names))
            m_names = list(set(m_names))
            KPs_all = (f_names) + (df_names) + (dr_names) + (m_names)    
            duplicated_nodes=[k for k, v in collections.Counter(KPs_all).items() if v > 1]
            dup_x = cord_df.loc[duplicated_nodes, 'X'].values
            dup_y = cord_df.loc[duplicated_nodes, 'Y'].values

            df_metrics = pd.DataFrame({"names":sorted(list(set(KPs_all)))})
            # Merge with suffixes
            df_metrics = df_metrics.merge(pd.DataFrame({"F":f_names}), left_on='names', right_on='F',\
                                          how='outer') \
            .merge(pd.DataFrame({"dF":df_names}), left_on='names', right_on='dF', how='outer') \
            .merge(pd.DataFrame({"dR":dr_names}), left_on='names', right_on='dR', how='outer') \
            .merge(pd.DataFrame({"mreach":m_names}), left_on='names', right_on='mreach', how='outer') \
            .set_index("names")
            df_metrics["counts"]=(~df_metrics.isna()).sum(axis=1)
            df_metrics=pd.merge(cord_df,df_metrics,left_index=True,right_index=True)

            df_metrics['size_F'] = df_metrics.apply(lambda row: 0 if row['F'] is np.nan \
                                                    else row['counts'], axis=1)
            df_metrics['size_df'] = df_metrics.apply(lambda row: 0 if row['dF'] is np.nan \
                                                     else row['counts'], axis=1)
            df_metrics['size_dR'] = df_metrics.apply(lambda row: 0 if row['dR'] is np.nan \
                                                     else row['counts'], axis=1)
            df_metrics['size_mreach'] = df_metrics.apply(lambda row: 0 if row['mreach'] is np.nan \
                                                         else row['counts'], axis=1)


            # Apply the modified logic to each row
            df_metrics = df_metrics.apply(process_row_modified, axis=1)

            selected_rows_f = df_metrics.loc[f_names]
            selected_rows_df = df_metrics.loc[df_names]
            selected_rows_dr = df_metrics.loc[dr_names]
            selected_rows_m = df_metrics.loc[m_names]


            selected_rows_f=selected_rows_f[selected_rows_f.size_F!=0]
            selected_rows_df=selected_rows_df[selected_rows_df.size_df!=0]
            selected_rows_dr=selected_rows_dr[selected_rows_dr.size_dR!=0]
            selected_rows_m=selected_rows_m[selected_rows_m.size_mreach!=0]
        
            plt.figure(figsize=(20,20))
             
            # Add labels for each point
            for label, (x, y) in zip(list(self.vs["name"]), coord):
                plt.text(x, y, label, ha='center', va='center', ma='center', zorder=20,fontsize=5)

            #for segment in lines:
            plt.plot(lines[:,0, :], lines[:, 1, :], c='black', alpha=0.2, linewidth=1.5, zorder=1)

            plt.scatter(cord_df["X"], cord_df["Y"], c="#BDC3C7", alpha=1, zorder=10,s=100)
            plt.scatter(selected_rows_f.X, selected_rows_f.Y, c="#F4D03F", alpha=1, zorder=11,s=np.array(selected_rows_f.size_F)*300)
            plt.scatter(selected_rows_df.X, selected_rows_df.Y, c="#2ECC71", alpha=1, zorder=12,s=np.array(selected_rows_df.size_df)*300)
            plt.scatter(selected_rows_dr.X, selected_rows_dr.Y, c="#3498DB", alpha=1, zorder=13,s=np.array(selected_rows_dr.size_dR)*300)
            plt.scatter(selected_rows_m.X, selected_rows_m.Y, c="#EC7063", alpha=1, zorder=14,s=np.array(selected_rows_m.size_mreach)*300)
            patches = [ plt.plot([],[], marker="o", ms=10, ls="", mec=None, color=colors[i], \
                        label="{:s}".format(texts[i]) )[0]  for i in range(len(texts)) ]
            plt.legend(title="Nodes color",frameon=True,handles=patches,loc="best")
            # Remove axes
            plt.axis('off')

            if outdir:
                plt.savefig(f"{outdir}/{filename}_{self.function}_{self.sub_func}.{exp_format}")
            else:
                plt.savefig(f"{filename}_{self.function}_{self.sub_func}.{exp_format}")

        else:
            metrics_names,metrics_x,metrics_y=[],[],[]
            for node in df["Key-player"]:
                # for node in list_nameNode:
                    if node not in metrics_names:
                        metrics_x.append(cord_df.loc[node, 'X'])
                        metrics_y.append(cord_df.loc[node, 'Y'])
                        metrics_names.append(node)

            # metrics_names = list(set(metrics_names))


            plt.figure(figsize=(20,20))
             
            # Add labels for each point
            for label, (x, y) in zip(list(self.vs["name"]), coord):
                plt.text(x, y, label, ha='center', va='center', ma='center', zorder=20,fontsize=5)

            #for segment in lines:
            plt.plot(lines[:,0, :], lines[:, 1, :], c='black', alpha=0.2, linewidth=1.5, zorder=1)

            plt.scatter(cord_df["X"], cord_df["Y"], c="#BDC3C7", alpha=1, zorder=10,s=100)
            plt.scatter(metrics_x, metrics_y, c="#F4D03F", alpha=1, zorder=11,s=200)
            plt.axis('off')

            if outdir:
                plt.savefig(f"{outdir}/{filename}_{self.function}_{self.sub_func}.{exp_format}")
            else:
                plt.savefig(f"{filename}_{self.function}_{self.sub_func}.{exp_format}")




    def plot_set(self,filename1,filename2,g1_names,g2_names,exp_format,operation,outdir=False):

        layout=self.layout('kk')
        coord = np.array(layout)
        ed = np.array(self.get_edgelist())
        lines = coord[ed[:,:]]
        lines = np.moveaxis(lines, 0,-1)

        names = list(self.vs["name"])
        cord_df = pd.DataFrame({"Node": names, "X": coord[:, 0], "Y": coord[:, 1]})
        #colors = ["#c73333","#71b82d","#e0c292","#186cab","#db9c2d","#f2f0ce"]
        colors = ["#2ECC71","#3498DB","#EC7063"]
        texts=[filename1,filename2,"Common"]
        common_names=list(set(g1_names)&set(g2_names))
        df_set=cord_df.merge(pd.DataFrame({filename1+"_names":g1_names}), left_on='Node', right_on=filename1+"_names",\
                                          how='outer') \
            .merge(pd.DataFrame({filename2+"_names":g2_names}), left_on='Node', right_on=filename2+"_names", how='outer') \
            .merge(pd.DataFrame({"Common":common_names}), left_on='Node', right_on="Common", how='outer') \
            .set_index("Node")
        
        df_set_g1 = df_set.loc[g1_names]
        df_set_g2 = df_set.loc[g2_names]
        df_set_common = df_set.loc[common_names]

        df_set_g1=df_set_g1[df_set_g1[filename1+"_names"]!=0]
        df_set_g2=df_set_g2[df_set_g2[filename2+"_names"]!=0]
        df_set_common=df_set_common[df_set_common["Common"]!=0]



        plt.figure(figsize=(20,20))
             
        # Add labels for each point
        for label, (x, y) in zip(list(self.vs["name"]), coord):
            plt.text(x, y, label, ha='center', va='center', ma='center', zorder=20,fontsize=5)

        #for segment in lines:
        plt.plot(lines[:,0, :], lines[:, 1, :], c='black', alpha=0.2, linewidth=1.5, zorder=1)

        plt.scatter(cord_df["X"], cord_df["Y"], c="#BDC3C7", alpha=1, zorder=10,s=100)
        plt.scatter(df_set_g1.X, df_set_g1.Y, c="#2ECC71", alpha=1, zorder=11,s=100)
        plt.scatter(df_set_g2.X, df_set_g2.Y, c="#3498DB", alpha=1, zorder=12,s=100)
        plt.scatter(df_set_common.X, df_set_common.Y, c="#EC7063", alpha=1, zorder=13,s=100)
        
        patches = [ plt.plot([],[], marker="o", ms=10, ls="", mec=None, color=colors[i], \
                    label="{:s}".format(texts[i]) )[0]  for i in range(len(texts)) ]
        plt.legend(title="Nodes color",frameon=True,handles=patches,loc="best")
        # Remove axes
        plt.axis('off')
        
        filename_set = f"{filename1}_{filename2}"

        if outdir:
            plt.savefig(f"{outdir}/{filename_set}_{self.function}_{self.sub_func}.{exp_format}")
        else:
            plt.savefig(f"{filename_set}_{self.function}_{self.sub_func}.{exp_format}")




    def radiality(self, sps=None, diameter=None):
        """Compute radiality centrality for all nodes.

        Radiality of node i = (diameter + 1) - mean shortest-path distance from i
        to all other nodes. Higher values indicate nodes more centrally positioned.

        Args:
            sps: optional precomputed weighted all-pairs shortest-path matrix
                (list of rows). If None it is computed once here.
            diameter: optional precomputed (unweighted) diameter. If None it is
                computed once here.

        Returns:
            list[float]: Radiality score for each node in vertex order.
        """
        radiality=[]
        weights = self.es["weight"] if "weight" in self.es.attributes() else None
        if sps is None:
            sps = distance_matrix(self, weights=weights)

        if diameter is None:
            # The diameter must be measured in the same unit as sps, otherwise
            # (diameter + 1) - mean_distance mixes hops with weighted lengths and
            # goes negative as soon as the weights exceed 1.
            diameter = self.diameter(weights=weights)
        norm = self.vcount() - 1

        sps = np.asarray(sps, dtype=float)
        for node in self.iNodes:
            row = sps[node]
            reachable = row[np.isfinite(row)]
            radiality.append( (diameter + 1) - reachable.sum() / norm )

        return radiality
    
    
    
    
    def radiality_reach(self, nodes=None, sps=None, diameter=None):
        comps = self.components()
        if len(comps) == 1:
            return self.radiality(sps=sps, diameter=diameter)
        else:
            tot_nodes = self.vcount()
            # Build one plain igraph view of the whole graph, then slice each
            # component out of it. Constructed once (O(E)) instead of rebuilt
            # per component (O(comps*E)). A plain ig.Graph is used because
            # induced_subgraph on the Graphtacle subclass hits its custom
            # __init__ signature (TypeError: unexpected keyword '__ptr').
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
                        rad = subg.radiality()
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
                        rad = [r * proportion_nodes for r in subg.radiality()]
                    sub_names = subg.vs["name"]
                    for nm in wanted:
                        result[nodes.index(nm)] = rad[sub_names.index(nm)]
                return result

    def median_global_shortest_path_length(self):

        # hop counts are exact in float32: half the memory of the default
        sps = distance_matrix(self, dtype=np.float32)
        finite = sps[np.isfinite(sps) & (sps != 0)]
        if finite.size == 0:
            return float("nan")
        return float(np.median(finite))

    


######################### ex shortest_path.py
    def get_shortestpaths(self):
        """Weighted all-pairs distances, unreachable pairs left as ``np.inf``.

        The previous sentinel was ``vcount() + 1``, which is not an upper bound on
        a weighted graph -- a finite distance can exceed n+1 and would then have
        been mistaken for "unreachable".
        """
        weights = self.es["weight"] if "weight" in self.es.attributes() else None
        return distance_matrix(self, weights=weights)



    def get_shortestpath_count(self, nodes=None):
        """Packed geodesic matrix: counts above the diagonal, path lengths below.

        ``spaths[i, j]`` for ``j > i`` is the number of shortest i-j paths and
        ``spaths[j, i]`` their length; ``group_betweenness`` needs both, and
        ``subtract_count_dist_matrix`` only subtracts counts whose length matched.

        Uses int64: geodesic counts pass 32767 on any layered graph, and the old
        int16 wrapped around to negative values without a word.
        """
        if nodes:
            loop_nodes = nodes
        else:
            loop_nodes = self.vs()
        loop_nodes_size = len(loop_nodes)

        weights = self.es["weight"] if "weight" in self.es.attributes() else None
        spaths = np.zeros(shape=(loop_nodes_size, loop_nodes_size), dtype=np.int64)

        for node in loop_nodes:
            temp_row = np.zeros(shape=loop_nodes_size, dtype=np.int64)
            temp_col = np.zeros(shape=loop_nodes_size, dtype=np.int64)

            # index of the source in this matrix; the source is the only vertex
            # whose shortest path to itself has length 1, but relying on that
            # left row_col_index undefined whenever no such path came back
            row_col_index = node.index if hasattr(node, "index") else int(node)

            # A disconnected graph is a normal input here -- group_betweenness
            # calls this on a copy with every edge of the group deleted, which
            # isolates those vertices on purpose. igraph warns about the
            # unreachable targets anyway; the zeros it leaves behind are exactly
            # what the caller wants, so keep the warning out of the user's face.
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*[Cc]ouldn't reach.*")
                sp = self.get_all_shortest_paths(v=node, weights=weights)
            for s in sp:
                if len(s) > 1:
                    last = s[-1]
                    temp_row[last] += 1
                    temp_col[last] = len(s) - 1

            spaths[row_col_index, row_col_index:loop_nodes_size] = temp_row[row_col_index:loop_nodes_size]
            spaths[row_col_index:loop_nodes_size, row_col_index] = temp_col[row_col_index:loop_nodes_size]

        count_all = np.array(spaths)
        return count_all
        



    def completeness_naive(self, directed=False):

        # total number of non-zero elements (E)
        if directed:
            num = self.ecount()
        else:
            num = self.ecount()*2

        # Total number of possible edges (graph-loops excluded). `num` above counts
        # adjacency-matrix non-zeros, so the ceiling is n(n-1) in both orientations;
        # the two branches used to be swapped relative to completeness() below.
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
        ### aggiungiamo correzione T.Mazza che prende il reciproco del prodotto
        '''
        Capocefalo
        '''
        # Number of adjacency-matrix non-zeros, same convention as completeness():
        # an undirected edge occupies two cells. The branches used to be swapped.
        if directed:
            e = graph.ecount()
        else:
            e = graph.ecount() * 2

        node_tot = graph.vcount()
        addend_left = (math.pow(node_tot, 2) / e) - 1
        addend_right = 1 - (1 / node_tot)
        
        # implementation by Randić and deAlba : compactness = addend_left * addend_right
        compactness = math.pow(addend_left, -1) * math.pow(addend_right, -1) # compactness by Mazza

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

        # Get the corresponding node indices
        nodes_ind=[]
        for i in list(nodes): #### from name to index  ### indici loop ciclo
            nodes_ind.append(self.vs.find(name=i).index)

        selected_neig = self.neighborhood(nodes, order=1, mode="all")
        flat_list = [item for sublist in selected_neig for item in sublist if item not in nodes_ind]
        normalized_score = len(set(flat_list)) / (len(self.vs) - len(nodes))

        return normalized_score


    def group_betweenness(self, np_counts, nodes=None):
        """Compute group betweenness centrality for a set of nodes.

        Group betweenness = fraction of shortest paths between non-group nodes
        that pass through at least one group member, normalized by
        (N - k)(N - k - 1) / 2 where k = group size.

        Args:
            np_counts (numpy.ndarray | None): Pre-computed shortest-path count
                matrix (N×N). Pass None to compute on the fly.
            nodes: Iterable of node names forming the group.

        Returns:
            float: Normalized group betweenness in [0, 1].
        """

        # Count geodesics of the original graph
        if np_counts is not None:
            if not isinstance(np_counts, np.ndarray):
                raise TypeError("np_counts must be None or a nump.nparray, {} found".format(type(np_counts).__name__))

            if not all(x == self.vcount() for x in np_counts.shape):
                raise ValueError("np_counts must be squared and of the same size of the graph ({})".format(self.vcount()))

            count_all = np_counts
        else:
            count_all = self.get_shortestpath_count()

        # Get the corresponding node indices
        nodes_index=[]
        for i in list(nodes): #### from name to index  ### indici loop ciclo
            nodes_index.append(self.vs.find(name=i).index)


        # Count geodesics that do not pass through the group
        del_edg = [self.incident(vertex=nidx) for nidx in nodes_index]
        del1 = set(list(itertools.chain(*del_edg)))

        ### il nostro copy()
        grafo_notgroup = Graphtacle.re(self, self.function, self.fileType, self.sep, self.header, self.directed, self.es["weight"], self.name)

        grafo_notgroup.delete_edges(del1)
        count_notgroup = grafo_notgroup.get_shortestpath_count()
        # Count geodesics that do pass through the group
        count_group = subtract_count_dist_matrix(count_all, count_notgroup)

        # Divide the number of geodesics (g(C) / g)
        group_btw_temp = np.divide(count_group, count_all,out=np.zeros_like(count_group, dtype=np.float64),where=count_all != 0)

        # discard group-nodes (set group nodes' rows and columns to zero)
        group_btw_temp[nodes_index] = 0
        group_btw_temp[:, nodes_index] = 0

        # sum not-nan counts upper triangular matrix (SUM u<v)
        group_btw = np.sum(np.triu(group_btw_temp, 0), dtype=np.float64) / 2

        # normalization
        grafo_size = len(self.vs)
        group_size = len(nodes_index)
        group_btw = (2 * group_btw) / ((grafo_size - group_size) * (grafo_size - group_size - 1))

        return group_btw


    def group_closeness(self, np_paths, nodes=None, distance_type="min"):
        """Compute group closeness centrality for a set of nodes.

        Group closeness = (number of non-group nodes) / sum over non-group nodes j
        of d(K, j), where d(K, j) is the distance from group K to node j
        (aggregated using distance_type).

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

        # Get the corresponding node indices
        group_indices=[]
        for i in list(nodes): #### from name to index  ### indici loop ciclo
            group_indices.append(self.vs.find(name=i).index)

        nongroup_nodes = list(set(self.vs["name"]) - set(nodes))
        nongroup_nodes_indices = [] 
        for i in list(nongroup_nodes): #### from name to index  ### indici loop ciclo
            nongroup_nodes_indices.append(self.vs.find(name=i).index)

        nongroup_np_paths = np_paths.take(nongroup_nodes_indices, axis=0)

        group_closeness = 0
        for np_path in nongroup_np_paths:
            # unreachable group members are dropped, not charged a sentinel distance
            temp_list = [elem for elem in np_path[group_indices] if np.isfinite(elem)]
            if temp_list:
                group_closeness += capo_dist(temp_list,distance_type)
        if group_closeness != 0:
            normalized_score = len(nongroup_nodes) / group_closeness
            return normalized_score
        else: 
            print("Node set {} is disconnected from the rest of the grafo using the {} distance. Returning 0.\n".format(nodes, distance_type))
            return 0.0