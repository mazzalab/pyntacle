import pandas as pd
import igraph as ig
import csv
import pygraphviz as gdot

from utility import *



def check_input_values(size, nei):
    """
    Check if the input values are within the valid range for the Watts-Strogatz function.
    Parameters:
    size (int): number of vertices (must be greater than or equal to k)
    nei (int): degree of each vertex (must be even and less than n)
	"""
    if size < nei:
        #print("Error: size must be greater than or equal to nei.")
        return False
    if nei % 2 != 0:
        #print("Error: nei must be even.")
        return False
    if nei >= size:
        #print("Error: nei must be less than size.")
        return False
    return True

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
		print(df_edges)
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
	### round(3) of matrix

	adj_matrix = [[round(elem, 3) for elem in row] for row in adj_matrix]
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
		edges_df["W"] = edges_df["W"].round(3)
		edges_df.to_csv(out_name,sep="\t",index=False)

def grafo_to_dot(grafo,name):

	if grafo.outdir:
		out_name = f'{grafo.outdir}/{name}.dot'
	else:
		out_name = f'{name}.dot'

	# edges_listTouple=name_from_edge(grafo)
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

def output_decision(grafo,fileType,filename):
    
    if fileType=="matrix":
        grafo.outdir = ""
        print(f"########################\n {grafo.outdir},{filename}")

        grafo_to_matrix(grafo,filename)
    elif fileType=="sif":
        grafo_to_sif(grafo,filename)
    elif fileType=="edgelist":
        grafo_to_edgelist(grafo,filename)
    elif fileType=="dot":
        grafo_to_dot(grafo,filename)
    else:
        print("Error")


def define_labels(grafo):
	size=grafo.vcount()
	labels=[f'n{i}' for i in range(1, size+1)]
	grafo.vs["label"]=labels
	grafo.vs["name"]=labels

	return grafo




def erdos_renyi(number_nodes, number_edges, probability, directed=False, loops=False):
	if probability:
		grafo=ig.Graph.Erdos_Renyi(number_nodes, p=probability, directed=directed, loops=False)
		grafo=define_labels(grafo)
		return grafo
	else:
		grafo=ig.Graph.Erdos_Renyi(number_nodes, m=number_edges, directed=directed, loops=False)
		grafo=define_labels(grafo)
		return grafo

def tree_generate(number_nodes, children, directed):
	grafo=ig.Graph.Tree(number_nodes, children, type=directed)
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
		raise TypeError(u"\nInvalid input values.\nsize (int): number of vertices (must be greater than or equal to k)\nnei (int): degree of each vertex (must be even and less than n)\n")


def lattice(dimension, nei=1, directed=False, mutual=False, circular=False):
	grafo=ig.Graph.Lattice(dimension, nei=nei, directed=directed, mutual=mutual, circular=circular)
	grafo=define_labels(grafo)
	return grafo