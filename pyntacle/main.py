import matplotlib.pyplot as plt
import argparse
import os
import sys
import pandas as pd
import igraph as ig
import numpy as np
from statistics import mean
from colorama import Fore, Style, Back

if __package__ in (None, ""):
	# run as a script (python pyntacle/main.py): make the package importable
	sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyntacle._ext.wrapper import (cython_wrapper_greedy, cython_wrapper_info,
                                   cython_wrapper_bruteforce, CYTHON_UNSUPPORTED_DIRECTED,
                                   DEFAULT_MAX_TIES)

from pyntacle.parser import create_parser
from pyntacle.GraphTacle import Graphtacle
from pyntacle.algorithms.group_centrality import *
from pyntacle.algorithms.key_player import *
from pyntacle.utility import *
from pyntacle.communities import *
from pyntacle.generate import *
from pyntacle.mesoscale import *
from pyntacle.algorithms.greedy import *
from pyntacle.algorithms.stochastic_gradient_descent import *
from pyntacle.create_html import *
from time import time

def tie_notes(tie_info):
	"""Header lines stating how many sets reach the optimum and how many are listed."""
	notes = []
	single = len(tie_info) == 1
	for oper, (tied_sets, n_optimal, _score) in tie_info.items():
		label = "Optimal sets" if single else f"Optimal sets ({oper})"
		notes.append(f"{label}\t{n_optimal} (showing {len(tied_sets)})")
	return notes


def tied_sets_frame(tie_info, set_column, explode=False, score_column="score"):
	"""Turn the brute-force tie dictionary into the report table.

	With several operations each row holds a whole node set in one cell, which is
	the shape the SVG plot and the HTML normaliser already expect. For a single
	operation the one-row-per-node shape is kept so the TSV still reads
	as a node list. Either way SetID says which optimal set a row belongs to.
	"""
	rows = []
	for oper, (tied_sets, _n_optimal, score) in tie_info.items():
		for set_id, nodes in enumerate(tied_sets, start=1):
			if explode:
				for node in nodes:
					rows.append({"SetID": set_id, set_column: node, score_column: score})
			else:
				rows.append({"operation": oper, "SetID": set_id,
				             set_column: list(nodes), "score": score})
	return pd.DataFrame(rows)


def with_tie_columns(df_html, set_column, tie_info=None):
	"""Attach the Ties/NOptimal columns every HTML report reads.

	Heuristic searches have no ties to report, so their single set becomes a
	one-element Ties list: the report's JS then needs no special case.
	"""
	ties, counts = [], []
	for operation, nodes in zip(df_html["Operation"], df_html[set_column]):
		info = (tie_info or {}).get(operation)
		if info is None:
			ties.append([list(nodes)])
			counts.append(1)
		else:
			ties.append([list(s) for s in info[0]])
			counts.append(int(info[1]))
	df_html["Ties"] = ties
	df_html["NOptimal"] = counts
	return df_html


def first_set_only(df):
	"""The SVG plot draws one set: keep set 1 and restore the pre-tie column shape."""
	if "SetID" not in df.columns:
		return df
	return df[df["SetID"] == 1].drop(columns=["SetID"]).reset_index(drop=True)


def info_node_set(g, nodes_arg, subcommand):
	"""The node set given with -n to kp-info / gc-info, checked against the graph."""
	if not nodes_arg:
		sys.exit(Fore.RED + Style.BRIGHT + f"ERROR: {subcommand} needs a node set: give it with -n "
		         "(comma-separated node names)" + Style.RESET_ALL)
	nodes = [n.strip() for n in nodes_arg.split(",") if n.strip()]
	unknown = sorted(set(nodes) - set(g.vs["name"]))
	if unknown:
		sys.exit(Fore.RED + Style.BRIGHT + "ERROR: nodes not in the network: " + ", ".join(unknown)
		         + Style.RESET_ALL)
	return nodes


def main(args):

	if getattr(args, "outdir", None):
		os.makedirs(args.outdir, exist_ok=True)

	# omics builds networks rather than reading one; imported here so the other
	# commands never load its optional dependencies.
	if args.command == "omics":
		from pyntacle.omics.cli import run_omics
		run_omics(args)
		return

	if args.directed:
		directed = True
	else:
		directed = False

	if args.weight:
		weighted = True
	else:
		weighted = False

	# The compiled kernels work on undirected graphs only: refuse -d before the
	# file is loaded.
	if directed and args.command in ("keyplayer", "groupcentrality"):
		sys.exit(Fore.RED + Style.BRIGHT +
			f"ERROR: --directed is not supported by '{args.command}'. "
			"Drop -d to analyse the network as undirected, or use the 'local', "
			"'global' or 'set' commands, which do handle directed graphs."
			+ Style.RESET_ALL)

	use_cython = getattr(args, "engine", "cython") != "python"
	seed = getattr(args, "seed", None)

	# Brute force fills this with oper -> (tied_sets, n_optimal, score): several
	# node sets can reach the same optimum and all of them are reported. Greedy
	# and gradient descent return a single set and leave it empty.
	tie_info = {}
	report_notes = []
	max_ties = int(getattr(args, "max_ties", DEFAULT_MAX_TIES))

	# --no-plot writes only the TSV report, without figures or HTML.
	no_plot = getattr(args, "no_plot", False)

	# -np sets the OpenMP threads of the compiled kernels; the Python engine is
	# single-threaded.
	if not use_cython and int(getattr(args, "nprocs", 1)) > 1:
		print(Fore.YELLOW + Style.BRIGHT +
			f"WARNING: --engine python is single-threaded; -np {args.nprocs} will be ignored. "
			"Drop --engine python to use the compiled kernels, which do honour -np."
			+ Style.RESET_ALL)

	# brute_force exists only in the compiled engine. kp-info/gc-info accept -a
	# but never search, so only the finders are checked.
	if (not use_cython and getattr(args, "algorithm", None) == "brute_force"
			and getattr(args, "subcommand", None) in ("kp-finder", "gc-finder")):
		sys.exit(Fore.RED + Style.BRIGHT +
			"ERROR: --algorithm brute_force has no python implementation, so it cannot "
			"be run with --engine python. Use --algorithm greedy or gradient_descent "
			"for the python engine, or drop --engine python to brute-force with the "
			"compiled kernels." + Style.RESET_ALL)

	# load the network
	if args.command!="generate":
		if args.NoHeader:
			header = False
		else:
			header = True

		if args.sep:
			sep=str(args.sep)
			print(f"Separator used: {sep}")
		else:
			sep=None
		
		# output path
		dirpath, filename = os.path.split(args.inputFile)
		filename = filename.strip().split(".")[0]

		if args.outdir == None:
			print("No Output directory specified")
			outdir = dirpath
		else:
			outdir = args.outdir

		print(f"\nWorking on: {args.inputFile}\n")
		# analysis commands read the weights as declared by -wt/-dt; commands that
		# only write the network back out keep them exactly as read
		weight_type = getattr(args, "weightType", None) if weighted else None
		try:
			g = Graphtacle.from_file(args.inputFile, args.command, args.fileType, sep, header, directed, weighted,
									 weight_type=weight_type,
									 distance_transform=getattr(args, "distanceTransform", "inverse"))
		except ValueError as err:
			sys.exit(Fore.RED + Style.BRIGHT + str(err) + Style.RESET_ALL)
		g.path_function(outdir)
		if weight_type is not None:
			print(f"Edge weights: {describe_weights(g.weight_info)}")
			if weight_type == "signed":
				n_neg = sum(1 for x in g.es["sign"] if x < 0)
				print(Fore.YELLOW + Style.BRIGHT +
					f"NOTE: {n_neg} of {g.ecount()} edges are negative. Every metric of "
					f"'{args.command}' is computed on the magnitude |w|; the sign is kept "
					"(edge attribute 'sign') but not used." + Style.RESET_ALL)

		# node removal (-r)
		if args.remove:
			nodes_toRemove = (args.remove).split(',')
			nodes_list = [x.replace(" ", "") for x in nodes_toRemove]
			g.remove_node(nodes_list)
			index_toRemove = [i for i in range(len(g.vs["name"])) if g.vs["name"][i] in nodes_list]
			g.delete_vertices(index_toRemove) #remove target nodes
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, args.inputFile)
			# re() builds a new instance, which resets the removed-node list
			g.remove_node(nodes_list)
			g.name=g.name+"_NoNodes"
			filename = g.name
			print(f"Nodes removed : {nodes_list}\n")
		else:
			print("No nodes removed\n")
			nodes_toRemove = None

		print(f"Number of nodes: {len(g.vs.indices)}")
		print(f"Number of edges: {len(g.es.indices)}")

		print(f"Number of components: {len(g.components())}")
		if len(g.components())>1:
			print("WARNING: The keyplayer colored in the figure could be only one of the possible sets\n" + Style.RESET_ALL)

			print(Fore.YELLOW + Style.BRIGHT + f"WARNING: The graph is fragmented in {len(g.components())} components"+ Style.RESET_ALL)


	else: # in case of 'generate'
		cwd = os.getcwd()

		if args.outdir == None:
			print("No Output directory specified, the output will be stored to the current working directory")
			outdir = cwd
		else:
			outdir = args.outdir

	print(f"Function : {args.command}\n")

	# ---- local ----
	if args.command == "local":
		
		if args.color:
			nodes_toColor = (args.color).split(',')
			nodes_list_color = [x.replace(" ", "") for x in nodes_toColor]
			print(f"Colored nodes : {nodes_list_color}\n")

		lengths = path_lengths(g)
		# all-pairs distances computed once and shared by radiality and radiality reach
		sps_w = distance_matrix(g, weights=lengths)
		diam_w = finite_max(sps_w)
		df =  pd.DataFrame({
					"Node Name" : g.vs["label"],
					"Degree": g.degree(), 
					"Betweenness": g.betweenness(weights=lengths),
					"Closeness": g.closeness(weights=lengths),
					"Radiality": g.radiality(sps=sps_w, diameter=diam_w),
					"Radiality reach": g.radiality_reach(sps=sps_w, diameter=diam_w),
					# strength-based metrics: a heavier weight is a stronger tie
					"Clustering Coefficient": g.transitivity_local_undirected(weights=g.affinities(),mode="zero"),
					"Eccentricity": g.eccentricity(),
					"Eigenvector (Scaled)": g.eigenvector_centrality(weights=g.affinities(),scale=True),
					"Pagerank": g.pagerank(weights=g.affinities())
					})

		if not no_plot:
			create_local_html(df,g,outdir)

	# ---- global ----
	elif args.command == "global":
		# all-pairs distances computed once and shared by radiality and radiality reach
		lengths = path_lengths(g)
		sps_w = distance_matrix(g, weights=lengths)
		# radiality needs the diameter in the same unit as the distances
		diam_w = finite_max(sps_w)
		radiality = g.radiality(sps=sps_w, diameter=diam_w)
		radiality_reach = g.radiality_reach(sps=sps_w, diameter=diam_w)
		# hop distances: the weighted matrix itself when every weight is 1
		sps_u = sps_w if lengths is None else distance_matrix(g, dtype=np.float32)
		diam_u = finite_max(sps_u)
		median_hops = g.median_global_shortest_path_length(sps=sps_u)
		del sps_u
		df =  pd.DataFrame({
					"Average shortest path length" : g.average_path_length(directed=directed, unconn=False),
					"Median shortest path length": median_hops,
					"Diameter": diam_w,
					"Components": len(g.components()),
					"Radius": float(g.radius()),
					"Density": g.density(),
					"pi": g.ecount()/diam_u,
					"Average clustering coefficient": g.transitivity_avglocal_undirected(),
					"Weighted clustering coefficient": g.transitivity_undirected(),
					"Average degree": mean(g.degree()),
					"Average Closeness":mean(g.closeness(weights=lengths)),
					"Average Eccentricity":mean(g.eccentricity()),
					"Average Radiality":(mean(radiality)),
					"Average Radiality Reach": mean(radiality_reach),
					"Completeness Naive": g.completeness_naive(directed=directed),
					"Completeness":g.completeness(directed=directed),
					"Compactness": g.compactness(directed=directed)
					},  index=[0]).melt()
		df.columns=["Measure","Score"]

	# ---- groupcentrality ----
	elif args.command == "groupcentrality":

		if args.subcommand == "gc-finder":
			if args.algorithm=="brute_force":

				if args.operation=="all":
					
					for oper in ['degree', 'betweenness', 'closeness']:
						k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(g, int(args.k_size), oper, n_threads=int(args.nprocs), max_ties=max_ties)
						tie_info[oper] = (tied_sets, n_optimal, score)

					df = tied_sets_frame(tie_info, "Group Centrality")
					report_notes.extend(tie_notes(tie_info))
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					        
				else:
					
					print("Using operation: ", args.operation)
					k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(g, int(args.k_size), args.operation, n_threads=int(args.nprocs), max_ties=max_ties)
					tie_info[args.operation] = (tied_sets, n_optimal, score)
					df = tied_sets_frame(tie_info, "Group Centrality", explode=True, score_column=args.operation)
					report_notes.extend(tie_notes(tie_info))
					g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)


			elif args.algorithm=="greedy":
				if use_cython:
					start = time()

					if args.operation == "all":
						greedy_results = []
						for oper in ["degree", "betweenness", "closeness"]:
							greedy_results.append(cython_wrapper_greedy(g, int(args.k_size), oper, distance_type=args.value, n_threads=int(args.nprocs), seed=seed))

						df = pd.DataFrame(greedy_results, columns=["Groupcentrality","score"])
						df.insert(0, 'operation', ["degree", "betweenness", "closeness"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					else:
						print("Using operation: ", args.operation)
						k_set, score = cython_wrapper_greedy(g, int(args.k_size), args.operation, distance_type=args.value, n_threads=int(args.nprocs), seed=seed)
						df = pd.DataFrame({"Groupcentrality": k_set, args.operation: score})	
						g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)

					end = time()
					print(f"Passed Time Cython: {end - start}")
				else:
					print("Using greedy algorithm")
					time_start = time()
					if args.operation=="all":
						tmp=call_all_greedy(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,function=args.command,seed=seed)
						df=pd.DataFrame(tmp,columns=["Groupcentrality","score"])
						df.insert(0, 'operation', ["degree","closeness","betweenness"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					else:
						gc=call_greedy(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,seed=seed)
						df=pd.DataFrame({"Groupcentrality":gc[0], args.operation:gc[1]})
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					end = time()
					print(f"Time taken: {end - time_start} seconds")
			elif args.algorithm=="gradient_descent":
				print("Using gradient_descent")
				if args.operation=="all":
					tmp=call_all_sgd(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,probability=args.probability,tolerance=args.tolerance,maxsec=args.maxsec,function=args.command,seed=seed)
					df=pd.DataFrame(tmp,columns=["Groupcentrality","score"])
					df.insert(0, 'operation', ["degree","closeness","betweenness"])
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
				else:
					gc=call_stochastic_gradient_descent(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,probability=float(args.probability),tolerance=float(args.tolerance),maxsec=int(args.maxsec),seed=seed)
					df=pd.DataFrame({"Groupcentrality":gc[0], args.operation:gc[1]})
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

			else:
				raise TypeError("Select the correct algorithm [brute_force | greedy | gradient_descent]") 

			if not no_plot:
				# The HTML report reads one row per operation: Operation, NodeSet, Score.
				# Column names differ between algorithms, so df is read by position; a
				# single-operation df holds one node per row and is collapsed to one set.
				if tie_info:
					operations = list(tie_info)
					df_html = pd.DataFrame({
						"Operation": operations,
						"NodeSet": [list(tie_info[o][0][0]) for o in operations],
						"Score": [tie_info[o][2] for o in operations],
					})
				elif args.operation == "all":
					df_html = pd.DataFrame({
						"Operation": df.iloc[:, 0],
						"NodeSet": [list(s) for s in df.iloc[:, 1]],
						"Score": df.iloc[:, 2],
					})
				else:
					df_html = pd.DataFrame({
						"Operation": [str(args.operation)],
						"NodeSet": [list(df.iloc[:, 0])],
						"Score": [df.iloc[:, 1].iloc[0]],
					})
				create_groupcentrality_html(with_tie_columns(df_html, "NodeSet", tie_info), g, outdir, filename)

		elif args.subcommand == "gc-info":

			nodes = info_node_set(g, args.nodes, args.subcommand)
			operations = ["degree", "closeness", "betweenness"] if args.operation == "all" else [args.operation]
			scores = [cython_wrapper_info(g, nodes, oper, distance_type=args.value, mdist=-1,
			                              n_threads=int(args.nprocs)) for oper in operations]
			df = pd.DataFrame({"Operation": operations, "Node-set": [nodes] * len(operations), "Score": scores})
			g.nameSub_function("info_" + args.operation)

			if not no_plot:
				df_html = pd.DataFrame({"Operation": operations,
				                        "NodeSet": [list(nodes) for _ in operations],
				                        "Score": scores})
				create_groupcentrality_html(with_tie_columns(df_html, "NodeSet"), g, outdir, filename)

		else:
			raise TypeError("Select the correct subcommand [gc-finder | gc-info]") 

	# ---- keyplayer ----
	elif args.command == "keyplayer":  
			
		if args.subcommand == "kp-finder":
			if args.algorithm == "brute_force":

				if args.operation=="all":
					
					for oper in ['F', 'dF', 'dR', 'mreach']:
						k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(g, int(args.k_size), oper, mdist=int(args.mdist), n_threads=int(args.nprocs), max_ties=max_ties)
						tie_info[oper] = (tied_sets, n_optimal, score)

					df = tied_sets_frame(tie_info, "Key-player")
					report_notes.extend(tie_notes(tie_info))
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					        
				else:
					
					print("Using operation: ", args.operation)
					k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(g, int(args.k_size), args.operation, mdist=int(args.mdist), n_threads=int(args.nprocs), max_ties=max_ties)
					tie_info[args.operation] = (tied_sets, n_optimal, score)
					df = tied_sets_frame(tie_info, "Key-player", explode=True, score_column=args.operation)
					report_notes.extend(tie_notes(tie_info))
					g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)
			
			elif args.algorithm == "greedy":
				print("Using greedy algorithm")

				if use_cython:
					start = time()

					if args.operation == "all":
						greedy_results = []
						for oper in ['F', 'dF', 'dR', 'mreach']:
							greedy_results.append(cython_wrapper_greedy(g, int(args.k_size), oper, mdist=int(args.mdist), n_threads=int(args.nprocs), seed=seed))

						df = pd.DataFrame(greedy_results, columns=["Key-player","score"])
						df.insert(0, 'operation', ["F","dF","dR","mreach"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					else:
						print("Using operation: ", args.operation)
						k_set, score = cython_wrapper_greedy(g, int(args.k_size), args.operation, mdist=int(args.mdist), n_threads=int(args.nprocs), seed=seed)
						df = pd.DataFrame({"Key-player": k_set, args.operation: score})	
						g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)
				
					end = time()
					print(f"Passed Time Cython: {end - start}")
				else:
					start = time()

					if args.operation=="all": 

						tmp=call_all_greedy(g, int(args.k_size), args.operation, distance_type=None, mdist=int(args.mdist), function=args.command, seed=seed)
						df=pd.DataFrame(tmp,columns=["Key-player","score"])
						df.insert(0, 'operation', ["F","dF","dR","mreach"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					
					else:
					
						kset=call_greedy(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist),seed=seed)
						df=pd.DataFrame({"Key-player":kset[0], args.operation:kset[1]})	
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					
					end = time()
					print(f"Passed Time pure Python: {end - start}")

			elif args.algorithm == "gradient_descent":
				print("Using gradient_descent")
				if args.operation == "all":
					tmp=call_all_sgd(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist),probability=args.probability,tolerance=args.tolerance,maxsec=args.maxsec,function=args.command,seed=seed)
					df=pd.DataFrame(tmp,columns=["Key-player","score"])
					df.insert(0, 'operation', ["F","dF","dR","mreach"])
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
				else:
					kset=call_stochastic_gradient_descent(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist),probability=float(args.probability),tolerance=float(args.tolerance),maxsec=int(args.maxsec),seed=seed)
					df=pd.DataFrame({"Key-player":kset[0], args.operation:kset[1]})
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
			else:
				raise TypeError("Select the correct algorithm [brute_force | greedy | gradient_descent]")

		elif args.subcommand == "kp-info":

			nodes = info_node_set(g, args.nodes, args.subcommand)
			operations = ["F", "dF", "dR", "mreach"] if args.operation == "all" else [args.operation]
			scores = [cython_wrapper_info(g, nodes, oper, distance_type='min', mdist=int(args.mdist),
			                              n_threads=int(args.nprocs)) for oper in operations]
			df = pd.DataFrame({"Operation": operations, "Key-player": [nodes] * len(operations), "Score": scores})
			g.nameSub_function("info_" + args.operation)
		
		else:
		
			raise TypeError("Select the right option") 

	# ---- set ----
	elif args.command == "set":
		print("The second input file must be of the same format as the first, including separator and header\n")
		dirpath2, filename2 = os.path.split(args.inputFile2)
		filename2 = filename2.strip().split(".")[0]
		g2 = Graphtacle.from_file(args.inputFile2, args.command, args.fileType, sep, header, directed, weighted)

		if args.subcommand == "union":
			print("Union\n")
			g1 = plain_copy(g, directed=False)
			g2 = plain_copy(g2, directed=False)
			gu=g1.union(g2)
			df = summary_to_df(gu, args.outdir, filename, filename2)
			gu=get_connected_subgraph(gu)
			g = Graphtacle.re(gu, args.command, args.fileType, sep, header, directed, weighted, outdir+"/union.tsv")
			g.nameSub_function(args.subcommand)

			if not no_plot:
				g.plot_set(filename,filename2,g1.vs["name"],g2.vs["name"],args.format,args.subcommand,outdir=outdir)
			g.name = f"{filename}_&_{filename2}"
			filename_set = f"{filename}_{filename2}"

			output_decision(g,"matrix",g.name+str("_union"))


		elif args.subcommand == 'intersection':
			print("Intersection\n")
			g1 = plain_copy(g, directed=False)
			g2 = plain_copy(g2, directed=False)
			# igraph's intersection() keeps isolated vertices: build it from the shared edges
			common_vertices = set(g1.vs["name"]).intersection(set(g2.vs["name"]))
			common_edges = set()
			for edge in g1.es:
				source, target = g1.vs[edge.source]["name"], g1.vs[edge.target]["name"]
				if source in common_vertices and target in common_vertices and g2.are_connected(source, target):
					common_edges.add((source, target))
			gi = ig.Graph()
			gi.add_vertices(list(common_vertices))
			gi.add_edges(list(common_edges))
			gi.vs["label"] = gi.vs["name"]

			df = summary_to_df(gi, args.outdir, filename, filename2)
			g = Graphtacle.re(gi, args.command, args.fileType, sep, header, directed, weighted, outdir+"/intersection.tsv")
			g.nameSub_function(args.subcommand)
			g.name = f"{filename}_&_{filename2}"
			filename_set = f"{filename}_{filename2}"

			if not no_plot:
				if outdir:
					ig.plot(plain_copy(g), opacity=0.7, target = f"{outdir}/{filename_set}_{g.function}_{g.sub_func}.{args.format}",vertex_label=g.vs["name"], bbox = (1000, 1000),edge_width=0.8,vertex_size=15)
				else:
					ig.plot(plain_copy(g), opacity=0.7, target = f"{filename_set}_{g.function}_{g.sub_func}.{args.format}", vertex_label=g.vs["name"],bbox = (1000, 1000),edge_width=0.8,vertex_size=15)

			output_decision(g,"matrix",g.name+str("_intersection"))


		elif args.subcommand == 'difference':
			print("Difference\n")
			g1 = plain_copy(g, directed=False)
			g2 = plain_copy(g2, directed=False)

			gd = g1.copy()
			g2_vertices = set(g2.vs["name"])

			for edge in g1.es:
				start_vertex_name = g1.vs[edge.source]['name']
				end_vertex_name = g1.vs[edge.target]['name']
				if start_vertex_name in g2_vertices and end_vertex_name in g2_vertices:
					if g2.are_connected(start_vertex_name, end_vertex_name):
						gd.delete_edges([(start_vertex_name, end_vertex_name)])

			# Remove isolated vertices (vertices with no edges) from gd
			isolated_vertices = [v.index for v in gd.vs if gd.degree(v) == 0]
			gd.delete_vertices(isolated_vertices)

			df = summary_to_df(gd, args.outdir, filename, filename2)
			gd=get_connected_subgraph(gd)
			g = Graphtacle.re(gd, args.command, args.fileType, sep, header, directed, weighted, outdir+"/difference.tsv")
			g.nameSub_function(args.subcommand)
		
			g.name = f"{filename}_&_{filename2}"
			filename_set = f"{filename}_{filename2}"

			if not no_plot:
				if outdir:
					ig.plot(plain_copy(g), opacity=0.7, target = f"{outdir}/{filename_set}_{g.function}_{g.sub_func}.{args.format}",vertex_label=g.vs["name"], bbox = (1000, 1000),edge_width=0.8,vertex_size=15)
				else:
					ig.plot(plain_copy(g), opacity=0.7, target = f"{filename_set}_{g.function}_{g.sub_func}.{args.format}", vertex_label=g.vs["name"],bbox = (1000, 1000),edge_width=0.8,vertex_size=15)

			output_decision(g,"matrix",g.name+str("_difference"))

		else:
			raise TypeError("Select the right option: union | intersection | difference")

	# ---- convert ----
	elif args.command == "convert":
		print("\nConvert")
		output_decision(g,args.typeOutput,args.outputName)

	# ---- communities ----
	elif args.command == "communities":
		if args.giant:
			giant=True
		else:
			giant=False

		print("\nCommunities")

		modules = communities(g, args.subcommand, args.numberCommunities, giant, args.steps, args.communitySize)
		filtered_mod = communities_filtering(modules, args.minNodes, args.maxNodes, args.minComponents, args.maxComponents)
		df = communities_to_df(modules, args.subcommand)

		if len(filtered_mod) == 0:
			print(Fore.RED + Style.BRIGHT +"\nNo components respected the constraints; try and change the parameters\n" + Style.RESET_ALL)
			print(Fore.RED + Style.BRIGHT +"These were the results:\n")
			print(df.to_string(index=False))
			print(""+ Style.RESET_ALL)
			df=pd.DataFrame({})

	# ---- extract ----
	elif args.command == "extract":

		if args.nodeList:
			nodes_toList = (args.nodeList).split(',')
			nodes_list_extr = [x.replace(" ", "") for x in nodes_toList]
			print(f"Selected nodes : {nodes_list_extr}\n")

		if args.selectComponent:
			print("Selecting the n-th component...")
			g=plain_copy(g, directed=False)
			g,df=selecting_component(g,int(args.selectComponent))
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="selected_subgraph"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif (args.largest) & (args.ncomponents!=False):
			print("Selecting n components...")
			g=plain_copy(g, directed=False)
			g,df=extract_and_df(g,args.ncomponents)
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="largest_subgraphs"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif args.largest:
			print("Selecting largest component...")
			g=plain_copy(g, directed=False)
			g,df=extract_and_df(g)
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="largest_component"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif args.ncomponents!=False:
			print("Removing the last n components...")
			g=plain_copy(g, directed=False)
			g,df=extract_and_df(g,-int(args.ncomponents))
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="removed_subgraphs"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif args.nodeList:
			g,df=components_by_nodes(g,nodes_list_extr)
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="selected_by_nodes"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		else:
			raise TypeError("Specify one of the following combination of flags -l | -l -n | -n | -sc ")

	# ---- generate ----
	elif args.command == "generate":
		print("\nGenerate")
		if args.subcommand=='erdos-renyi':
			if not all(x == False for x in [args.numberNodes, args.numberEdges, args.probability]):
				grafo=erdos_renyi(int(args.numberNodes), int(args.numberEdges), float(args.probability), directed=args.directed, loops=args.loops)
				filename = outdir+"/erdos_renyi"
				g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
				output_decision(g,args.fileType,filename)
			else:
				raise TypeError("One of the arguments is missing")

		elif args.subcommand=="tree":
			if not all(x == False for x in [int(args.numberNodes), int(args.children)]):
				grafo=tree_generate(int(args.numberNodes), int(args.children), args.directed)
				filename = outdir+"/tree"
				g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
				output_decision(g,args.fileType,filename)
			else:
				raise TypeError("One of the arguments is missing")

		elif args.subcommand=='barabasi':
			if not all(x == False for x in [int(args.numberNodes), int(args.averageEdge)]):
				grafo=barabasi(int(args.numberNodes), int(args.averageEdge), directed=args.directed, implementation=args.implementation)
				filename = outdir+"/barabasi"
				g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
				output_decision(g,args.fileType,filename)
			else:
				raise TypeError("One of the arguments is missing")

		elif args.subcommand=='watts-strogatz':
			grafo=watts_strogatz(dim=int(args.dimension), size=int(args.size), nei=int(args.nei), probability=int(args.probability),loops=args.loops, multiple=args.multiple)
			filename = outdir+"/tree"
			g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
			output_decision(g,args.fileType,filename)

		elif args.subcommand=='lattice':
			lista_dim=[int(num) for num in args.dimension.split(",") ]
			grafo=lattice(dimension=lista_dim, nei=int(args.nei), directed=args.directed, mutual=args.mutual, circular=args.circular)
			filename = outdir+"/lattice"
			g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
			output_decision(g,args.fileType,filename)
		else:
			raise TypeError("Select the right option: erdos-renyi | tree | barabasi | watts-strogatz | lattice")

	# ---- mesoscale ----
	elif args.command == "mesoscale":
		print("Mesoscale\n")
		
		df_ti = ti( g, int(args.kSteps), weighted=False, weight_attr=None, threshold=args.threshold, verbose=args.verbose ) 
		
		if weighted:

			# TI spreads effects in proportion to tie strength
			df_wi = ti( g, int(args.kSteps), weighted=True, weight_attr="affinity", threshold=args.threshold, verbose=args.verbose) 

		df_gtom = gtom(g, int(args.kSteps), verbose=args.verbose)

	# ---- percolation ----
	elif args.command == "percolation":
		print("Percolation\n")
		# imported here so the other commands do not load plotly
		from pyntacle.percolation import (run_percolation, summarize_percolation_results,
								  save_percolation_html)

		# optional per-node recovery times from a TSV file (columns: Nodes, Recovery_time)
		tau_vector = None
		if args.tauFile:
			tau_df = pd.read_csv(args.tauFile, sep=None, engine="python")
			tau_map = dict(zip(tau_df["Nodes"].astype(str), tau_df["Recovery_time"].astype(float)))
			tau_vector = [tau_map[str(name)] for name in g.vs["name"]]

		results = run_percolation(
			g,
			Pstar=float(args.PrInf),
			tau=float(args.tau),
			tau_dist=args.tauDistribution,
			seed_node=args.nodes,
			pth_max=float(args.pthMax),
			dist=args.pthDistribution,
			max_steps=args.maxSteps,
			verbose=args.verbose,
			tau_vector=tau_vector,
			use_edge_weights_as_pth=weighted,
			snapshot_infected=args.snapshotInfected,
			snapshot_node=args.snapshotNode,
		)

		print(summarize_percolation_results(g, results))

		if outdir:
			html_path = f"{outdir}/{filename}_percolation.html"
			report_path = f"{outdir}/report_{filename}_percolation.tsv"
		else:
			html_path = f"{filename}_percolation.html"
			report_path = f"report_{filename}_percolation.tsv"

		if not no_plot:
			# interactive HTML animation of the spreading process
			save_percolation_html(g, results, filename=html_path, name=filename)
			print(f"\nInteractive HTML saved in: {html_path}")

		# per-node activation / recovery report
		node_labels = results["node_labels"]
		perc_df = pd.DataFrame({
			"Node": node_labels,
			"Activation_time": results["activation_time"],
			"Recovery_time": results["recovery_time"],
		})

		# optional snapshot of node states (--snapshot-infected / --snapshot-node)
		if results["snapshot_state"] is not None:
			snap_t = results["snapshot_time"]
			state_names = {0: "susceptible", 1: "infected", 2: "recovered"}
			perc_df[f"State_at_t{snap_t}"] = [state_names[int(x)] for x in results["snapshot_state"]]

		perc_df.to_csv(report_path, sep="\t", index=False)
		print(f"\nCreated report in: {report_path}.\n")

	else:
		raise TypeError("Select the right option:  local | global | groupcentrality | keyplayer | set | convert | communities | extract | generate | mesoscale | percolation")

	# ---- reports and figures ----

	if args.command == "convert" or args.command == "generate" or args.command == "percolation":
		pass
	elif args.command == "set":
		df=df.round(3)
		print("")
		print(df)
		report_path = g.export_file(df, outdir)
		print(f"\nCreated report in: {report_path}.\n")

	elif args.command == "communities":
		if not no_plot:
			for i,c in enumerate(filtered_mod):
				if c.vcount()>20:
					print(Fore.YELLOW + Style.BRIGHT + f"WARNING: The community {abs(i)} has more than 20 nodes, the image will not be generated\n" + Style.RESET_ALL)
					break
				if outdir:
					ig.plot(c, target = f"{outdir}/{filename}_community_{abs(i)}.{args.format}", bbox = (600, 600))
				else:
					ig.plot(c, target = f"{filename}_community_{abs(i)}.{args.format}", bbox = (600, 600))
		print("\nIn the file:")
		print(df)
		report_path = g.export_file(df, outdir)
		print(f"\nCreated report in: {report_path}.\n")
	elif args.command == "mesoscale":
		
		df_ti = df_ti.round(3) 
		df_gtom = df_gtom.round(3)
	
		if len(g.vs.indices) <= 100:

			print(f"Topological Importance ({int(args.kSteps)}):\n{df_ti}\n")
			print("\n-----------------------------------------\n")
			
			if weighted:
				df_wi = df_wi.round(3) 
				print(f"Weighted Topological Importance ({int(args.kSteps)}):\n{df_wi}\n")
				print("\n-----------------------------------------\n")

			print(f"Generalized Topological Overlap Measure ({int(args.kSteps)}):\n{df_gtom}\n")
		else:
			print(f"\nGraph is too large to display detailed metrics. See the report file for details.\n")
		
		if not no_plot:
			try:
				if outdir:
					ig.plot(plain_copy(g), opacity=0.7, target = f"{outdir}/{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_label_size=2.5)
				else:
					ig.plot(plain_copy(g), opacity=0.7, target = f"{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_label_size=2.5)
			except Exception as e:
				print(Fore.YELLOW + Style.BRIGHT + f"\nWARNING: Plotting skipped due to backend error: {e}" + Style.RESET_ALL)

		if g.sub_func:
			if outdir:
				filename=f"{outdir}/report_{g.name}_{g.function}_{g.sub_func}.tsv"
			else:
				filename=f"report_{g.name}_{g.function}_{g.sub_func}.tsv"
		else:
			if outdir:
				filename=f"{outdir}/report_{g.name}_{g.function}.tsv"
			else:
				filename=f"report_{g.name}_{g.function}.tsv"

		g.name=filename

		with open(filename, "w") as f:
			f.write(f"Pyntacle report\t{g.name.strip().split('/')[-1]}\n")
			f.write(f"Analysis type\t{g.function}\n")
			f.write("\nNetwork Overview\n")
			f.write(f"Removed nodes\t{g.removed}\n")
			f.write(f"Number of components\t{len(g.components())}\n")
			f.write(f"Number of Nodes\t{len(g.vs['label'])}\n")
			f.write(f"Number of Edges\t{len(g.get_edgelist())}\n\n")
			f.write("\nTopological Importance\n")
			f.write(df_ti.to_csv(sep="\t", index=True))
			if weighted:
				f.write("\nWeighted Topological Importance\n")
				f.write(df_wi.to_csv(sep="\t", index=True))
			f.write("\nTopological Overlap Measure\n")
			f.write(df_gtom.to_csv(sep="\t", index=True))


	elif args.command == "keyplayer":

		df=df.round(3) 
		print(df)
		report_path = g.export_file(df, outdir, notes=report_notes)
		print(f"\nCreated report in: {report_path}.\n")

		if not no_plot:
			if args.subcommand=="kp-info":
				pass
			else:
				g.plot_keyplayer(first_set_only(df),filename,args.format,args.operation,outdir=outdir)
				print(Fore.YELLOW + Style.BRIGHT + "WARNING: The keyplayer colored in the figure could be only one of the possible sets\n" + Style.RESET_ALL)

			# The HTML report reads one row per operation: Operation, KeySet, Score.
			if args.subcommand == "kp-info":
				df_html = pd.DataFrame({
					"Operation": df["Operation"],
					"KeySet": [list(nodes) for _ in range(len(df))],
					"Score": df["Score"],
				})
			elif tie_info:
				operations = list(tie_info)
				df_html = pd.DataFrame({
					"Operation": operations,
					"KeySet": [list(tie_info[o][0][0]) for o in operations],
					"Score": [tie_info[o][2] for o in operations],
				})
			else:
				if args.operation == "all":
					df_html = pd.DataFrame({
						"Operation": df["operation"],
						"KeySet": [list(ks) for ks in df["Key-player"]],
						"Score": df["score"],
					})
				else:
					df_html = pd.DataFrame({
						"Operation": [str(args.operation)],
						"KeySet": [list(df["Key-player"])],
						"Score": [df[str(args.operation)].iloc[0]],
					})
			create_keyplayer_html(with_tie_columns(df_html, "KeySet", tie_info), g, outdir, filename)

	else:
		df=df.round(3) 
		print("")
		print(df)
		report_path = g.export_file(df, outdir, notes=report_notes)

		graph = plain_copy(g)

		print(f"\nCreated report in: {report_path}.\n")
		if no_plot:
			pass
		elif hasattr(args,"color"):
			if args.color:
				vertex_color=[]
				for node in g.vs:
					if node["name"] in nodes_list_color:
						vertex_color.append("green")
					else:
						vertex_color.append("red")
			else:
				vertex_color='red'
			if outdir:
				ig.plot(graph, opacity=0.7, target = f"{outdir}/{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_color=vertex_color)
			else:
				ig.plot(graph, opacity=0.7, target = f"{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_color=vertex_color)
		elif hasattr(args,"nodeList"):
			vertex_color=[]
			for node in g.vs:
				if args.nodeList:
					if (node["name"] in nodes_list_extr):
						vertex_color.append("green")
				else:
					vertex_color.append("red")

			if outdir:
				ig.plot(graph, opacity=0.7, target = f"{outdir}/{filename}_{g.function}_{g.sub_func}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_color=vertex_color)
			else:
				ig.plot(graph, opacity=0.7, target = f"{filename}_{g.function}_{g.sub_func}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_color=vertex_color)

		else:
			if g.sub_func:
				if outdir:
					ig.plot(graph, opacity=0.7, target = f"{outdir}/{filename}_{g.function}_{g.sub_func}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_label_size=2.5)
				else:
					ig.plot(graph, opacity=0.7, target = f"{filename}_{g.function}_{g.sub_func}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_label_size=2.5)
			else:
				if outdir:
					ig.plot(graph, opacity=0.7, target = f"{outdir}/{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15)
				else:
					ig.plot(graph, opacity=0.7, target = f"{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15)

	print(Fore.GREEN + Style.BRIGHT + "Done!\n" + Style.RESET_ALL)



def cli(argv=None):
	"""Entry point of the ``pyntacle`` command."""
	parser = create_parser()
	args = parser.parse_args(argv)

	# no subcommand given: print help instead of crashing on args.directed
	if args.command is None:
		parser.print_help()
		sys.exit(0)

	main(args)


if __name__ == '__main__':
	cli()
