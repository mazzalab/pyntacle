import os
import pandas as pd
import igraph as ig
import csv
import pygraphviz as gdot

from pyntacle.utility import *



def check_input_values(size, nei):
    """Watts-Strogatz starts from a ring where each node reaches the nodes up to
    `nei` steps away, 2 * nei neighbours in all: they must be fewer than the nodes."""
    return nei >= 1 and 2 * nei < size

def igraph_to_graphviz(grafo,weighted=False,directed=False):
	if weighted:
		# Initialize a Graphviz graph
		graphViz = gdot.AGraph(strict=False, directed=directed)

		# Transfer nodes and edges to Graphviz graph
		for vertex in grafo.vs:
		    graphViz.add_node(vertex.index, name=vertex["name"])

		for edge in grafo.es:
		    source, target = edge.tuple
		    graphViz.add_edge(source, target, weight=edge['weight'])
	else:
		raise TypeError("Not yet implemented")

	return graphViz


def name_from_edge(grafo, weight=False):
	edges_listTouple = grafo.get_edgelist()
	edges=[]
	if weight:
		for edges_tuple in edges_listTouple:
			v_names = []
			for v in list(edges_tuple):
				v_names.append(grafo.vs[v]["name"])
			edges.append(v_names)
		weights=list(grafo.es["weight"])
		v1 = [x[0] for x in edges]
		v2 = [x[1] for x in edges]
		df_edges=pd.DataFrame({"V1":v1,"V2":v2,"W":weights})
		return df_edges
	else:

		for edges_tuple in edges_listTouple:
			v_names = []
			for v in list(edges_tuple):
				v_names.append(grafo.vs[v]["name"])
			edges.append(v_names)
		return edges

def grafo_to_matrix(grafo,name):

	if grafo.outdir:
		out_name = f'{grafo.outdir}/{name}.txt'
	else:
		out_name = f'{name}.txt'

	if grafo.directed==True:
		raise TypeError(u"Not yet implemented")
	
	adj_matrix = grafo.get_adjacency(attribute="weight")
	nodes=grafo.vs["name"]
	header = [""] + nodes

	with open(out_name, 'w', newline='') as file:
		file.write("\t".join(header))
		file.write("\n")
		for i in range(len(nodes)):
			row = [nodes[i]] + adj_matrix[i]
			file.write("\t".join([str(elem) for elem in row]))
			file.write("\n")
	

def grafo_to_edgelist(grafo,name):

	if grafo.outdir:
		out_name = f'{grafo.outdir}/{name}.tsv'
	else:
		out_name = f'{name}.tsv'

	if grafo.directed==True:
		raise TypeError(u"Not yet implemented")

	if set(grafo.es["weight"])=={1}:
		edges_listTouple=name_from_edge(grafo)
		with open(out_name, 'w', newline='') as file:
			file.write("V1\tV2\n")
			writer = csv.writer(file, delimiter="\t")
			writer.writerows(edges_listTouple)
	else:
		edges_df=name_from_edge(grafo,True)
		edges_df.to_csv(out_name,sep="\t",index=False)

def grafo_to_dot(grafo,name):

	if grafo.outdir:
		out_name = f'{grafo.outdir}/{name}.dot'
	else:
		out_name = f'{name}.dot'

	if grafo.directed==True:
		raise TypeError(u"Not yet implemented")
	if set(grafo.es["weight"])=={1}:
		grafo.write_dot(out_name)
	else:
		graphViz=igraph_to_graphviz(grafo,weighted=True,directed=False)
		graphViz.write(out_name)


def grafo_to_sif(grafo,name):

	if grafo.outdir:
		out_name = f'{grafo.outdir}/{name}.sif'
	else:
		out_name = f'{name}.sif'

	edges_listTouple=name_from_edge(grafo)
	if grafo.directed==True:
		raise TypeError(u"Not yet implemented")
	else :
		pass
	if set(grafo.es["weight"])=={1}:
		with open(out_name, 'w', newline='') as file:
				file.write("Node1\tInteraction\tNode2\n")
				for pair in edges_listTouple:
					file.write(f"{pair[0]}\tinteracts_with\t{pair[1]}\n")
	else:
		with open(out_name, 'w', newline='') as file:
			file.write("Node1\tInteraction\tNode2\tWeight\n")
			for pair in edges_listTouple:
				file.write(f"{pair[0]}\tinteracts_with\t{pair[1]}\t{grafo.get_edge_weight(pair[0], pair[1])}\n")

def output_decision(grafo, fileType, filename, outdir=None):
	"""Write the network as `fileType` to <outdir>/<filename>.<ext> and return the path.

	Without `outdir` the network's own output directory is used (the current
	directory when it has none)."""
	writers = {"matrix": (grafo_to_matrix, "txt"), "sif": (grafo_to_sif, "sif"),
	           "edgelist": (grafo_to_edgelist, "tsv"), "dot": (grafo_to_dot, "dot")}
	if fileType not in writers:
		raise ValueError(f"cannot write a network as '{fileType}'")
	if outdir is not None:
		grafo.outdir = outdir
	writer, ext = writers[fileType]
	# utility imports this module, so its names are not all bound at import time
	from pyntacle.utility import warn
	isolated = [name for name, d in zip(grafo.vs["name"], grafo.degree()) if d == 0]
	if isolated and fileType in ("edgelist", "sif"):
		warn(f"{len(isolated)} node(s) without edges cannot be written as {fileType} and are left out "
		     f"({', '.join(map(str, isolated[:5]))}{', ...' if len(isolated) > 5 else ''}); "
		     "matrix and dot keep them")
	# a name with folders in it (-fo sub/name) writes into them
	os.makedirs(os.path.dirname(os.path.join(grafo.outdir or ".", filename)) or ".", exist_ok=True)
	writer(grafo, filename)
	return f"{grafo.outdir}/{filename}.{ext}" if grafo.outdir else f"{filename}.{ext}"


def define_labels(grafo):
	size=grafo.vcount()
	labels=[f'n{i}' for i in range(1, size+1)]
	grafo.vs["label"]=labels
	grafo.vs["name"]=labels

	return grafo




def erdos_renyi(number_nodes, number_edges, probability, directed=False, loops=False):
	if probability:
		grafo=ig.Graph.Erdos_Renyi(number_nodes, p=probability, directed=directed, loops=loops)
		grafo=define_labels(grafo)
		return grafo
	else:
		grafo=ig.Graph.Erdos_Renyi(number_nodes, m=number_edges, directed=directed, loops=loops)
		grafo=define_labels(grafo)
		return grafo

def tree_generate(number_nodes, children, directed):
	grafo=ig.Graph.Tree(number_nodes, children, mode="out" if directed else "undirected")
	grafo=define_labels(grafo)
	return grafo 

def barabasi(number_nodes, average_edge, directed=False, implementation="psumtree"):
	grafo=ig.Graph.Barabasi(number_nodes, average_edge, directed=directed, implementation=implementation)
	grafo=define_labels(grafo)
	return grafo

def watts_strogatz(size, nei, probability,loops=False, multiple=False, dim=1):
	if check_input_values(size, nei):
		grafo=ig.Graph.Watts_Strogatz(dim, size, nei, probability,loops=loops, multiple=multiple)
		grafo=define_labels(grafo)
		return grafo
	else:
		raise ValueError(f"watts-strogatz needs -nei of at least 1 and 2 * nei below the lattice size (got -s {size}, -nei {nei})")


def lattice(dimension, nei=1, directed=False, mutual=False, circular=False):
	grafo=ig.Graph.Lattice(dimension, nei=nei, directed=directed, mutual=mutual, circular=circular)
	grafo=define_labels(grafo)
	return grafo