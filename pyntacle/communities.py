import os
from tkinter.ttk import Style
import numpy as np
import igraph as ig
from itertools import combinations
from collections import defaultdict
from typing import List, Dict, Tuple

### import of home-made subClass of igraph
from utility import *


def fastgreedy(grafo, n=None):
	print("\nFastgreedy")
	modules = grafo.community_fastgreedy(weights=grafo.es["weight"])
	modules = modules.as_clustering(n=n)
	return modules.subgraphs()

def infomap(grafo):
	print("\nInfomap")
	modules=grafo.community_infomap(edge_weights=grafo.es["weight"], vertex_weights=None, trials=10)
	return modules.subgraphs()

def leading_eigenvector(grafo,n):
	print("\nleading-eigenvector")
	modules=grafo.community_leading_eigenvector(clusters=n, weights=grafo.es["weight"])
	return modules.subgraphs()

def random_walk(grafo, n, steps=4):
	modules=grafo.community_walktrap(weights=grafo.es["weight"],steps=steps)
	modules=modules.as_clustering(n)
	return modules.subgraphs()

def percolation(g: ig.Graph, k: int = 3) -> List[ig.Graph]:

	print(f"\nPercolation method (k={k})")
 
	if k < 2:
		raise ValueError("k must be >= 2")

	# --- Preconditioning: undirected + simple graph on a working copy
	work = g.copy()
	if work.is_directed():
		try:
			work = work.as_undirected(mode="collapse")
		except TypeError:
			work = work.as_undirected()
	try:
		work.simplify(multiple=True, loops=True)
	except TypeError:
		work.simplify()

	# find all cliques of size k 
	k_cliques_sets = [frozenset(c) for c in work.cliques(min=k, max=k)]

	# clique-graph via (k-1)-subset bucketing (connect cliques sharing k-1 vertices)
	buckets = defaultdict(list)  # key: (k-1)-tuple -> list of clique indices containing it
	for idx, c in enumerate(k_cliques_sets):
		for sig in combinations(sorted(c), k - 1):
			buckets[sig].append(idx)

	edge_set = set()

	for idxs in buckets.values():
		if len(idxs) < 2:
			continue
		for i in range(len(idxs)):
			for j in range(i + 1, len(idxs)):
				a, b = idxs[i], idxs[j]
				if a > b:
					a, b = b, a
				edge_set.add((a, b))
				
	clique_graph = ig.Graph(n=len(k_cliques_sets), edges=list(edge_set), directed=False)
	
	# add the actual nodes that compose each clique
	clique_graph.vs["label"] = [sorted(list(clique_set)) for clique_set in k_cliques_sets]

	# retrieve the connected components of the clique-graph => CPM communities
	modules = clique_graph.components().subgraphs()

	return modules


def communities(grafo,algorithm,n,giant,steps=4, communitySize=3):

	subgraph = get_connected_subgraph(ig.Graph(directed=False,vertex_attrs={"name":grafo.vs["name"],
																		   "label": grafo.vs["label"]},
																		   edges=grafo.get_edgelist(),
																		   edge_attrs={"weight": grafo.es["weight"]
																		   }), giant)

	if (type(n)==str) & (algorithm!="infomap"): 
		n=int(n)
	else:
		if type(n)==str or (algorithm=="percolation"):
			print("Number of communities is ignored")
		elif (algorithm=="infomap"):
			pass#a
		else:
			print("WARNING: number of clusters not provided, the algorithm tries to do as many splits as possible.")
	
	if algorithm == "fastgreedy":
		modules = fastgreedy(subgraph,n)
	elif algorithm == "infomap":
		modules = infomap(subgraph)
	elif algorithm == "leading-eigenvector":
		modules = leading_eigenvector(subgraph,n)
	elif algorithm == "random-walk":
		modules = random_walk(subgraph, n, int(steps))
	elif algorithm == "percolation":
		modules = percolation(subgraph, communitySize)
	else:
		raise TypeError(u"'fastgreedy | infomap | leading-eigenvector | random-walk | percolation' are the available options") 

	return modules
		


def communities_filtering(modules, min_nodes=None,max_nodes=None,min_components=None,max_components=None):
	
	if not all(x == None for x in [min_nodes, max_nodes, min_components, max_components]):

		modules = list(filter(lambda x: x.vcount() >= int(min_nodes) if min_nodes is not None else x, modules))
		modules = list(filter(lambda x: x.vcount() <= int(max_nodes) if max_nodes is not None else x, modules))
		modules = list(filter(lambda x: len(x.components()) >= int(min_components) if min_components is not None else x, modules))
		modules = list(filter(lambda x: len(x.components()) <= int(max_components) if max_components is not None else x, modules))


	return modules

def communities_to_df(modules, subcommand) -> pd.DataFrame:

	df = pd.DataFrame({})

	if subcommand == "percolation":
		df = {'Node':{}, 'Community':[], 'Clique':[]} 
		for idx, comp in enumerate(modules):
			for v in comp.vs:
				for node in v["label"]:
					if node not in df['Node']:
						df['Node'][node] = len(df['Node']) # assign to use later to extend community and clique lists
						df['Community'].append([idx])
						df['Clique'].append([list(v["label"])])
					else:
						df['Community'][df['Node'][node]].extend([idx])
						df['Clique'][df['Node'][node]].extend([list(v["label"])])

		df['Community'] = [list(set(x)) for x in df['Community']]
		df['Node'] = list(df['Node'].keys())

	else:

		df = {'Node':[], 'Community':[]} 
		for idx, comp in enumerate(modules):
			for v in comp.vs:
				df['Node'].append(v["name"])
				df['Community'].append(idx)


	return pd.DataFrame(df).sort_values(by="Node").reset_index(drop=True)