import matplotlib.pyplot as plt
import argparse
import os
import sys
import pandas as pd
import igraph as ig
import numpy as np
from statistics import mean
from colorama import Fore, Style, Back

from _ext.wrapper import (cython_wrapper_greedy, cython_wrapper_info,
                          cython_wrapper_bruteforce, CYTHON_UNSUPPORTED_DIRECTED,
                          DEFAULT_MAX_TIES)

### import of home-made subClass of igraph
from parser import create_parser
from GraphTacle import Graphtacle
from algorithms.group_centrality import *
from algorithms.key_player import *
from utility import *
from communities import *
from generate import *
from mesoscale import *
from algorithms.greedy import *
from algorithms.stochastic_gradient_descent import *
from create_html import *
from time import time

# main function
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
	operation the historical one-row-per-node shape is kept so the TSV still reads
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


def main(args):

	# omics builds networks, it does not read one: none of the graph flags below
	# exist on its parser. Imported here so the other commands never load its
	# optional dependencies.
	if args.command == "omics":
		from omics.cli import run_omics
		run_omics(args)
		return

	#### Check general flags
	if args.directed:
		directed = True
	else:
		directed = False

	if args.weight:
		weighted = True
	else:
		weighted = False

	# The Cython engine builds the network through igraph's undirected weighted
	# adjacency constructor, which rejects an asymmetric matrix from inside a nogil
	# block -- that used to abort the interpreter with no traceback. Say so up
	# front instead of letting the user wait for the file to load first.
	if directed and args.command in ("keyplayer", "groupcentrality"):
		sys.exit(Fore.RED + Style.BRIGHT +
			f"ERROR: --directed is not supported by '{args.command}'. "
			"Drop -d to analyse the network as undirected, or use the 'local', "
			"'global' or 'set' commands, which do handle directed graphs."
			+ Style.RESET_ALL)

	use_cython = getattr(args, "engine", "cython") != "python"
	seed = getattr(args, "seed", None)

	# Brute force fills this with oper -> (tied_sets, n_optimal, score). Several
	# node sets routinely reach the same optimum and reporting one of them throws
	# the rest of the answer away, so they travel together into the TSV and the
	# HTML. Greedy and gradient descent are heuristics: they visit one set and
	# leave the dict empty.
	tie_info = {}
	report_notes = []
	max_ties = int(getattr(args, "max_ties", DEFAULT_MAX_TIES))

	# Old Pyntacle's --no-plot skips figure/HTML generation and writes only the
	# TSV; benchmarking wall time against it is unfair unless the new tool can
	# do the same -- otherwise every cell measures "new also drew a plot" (the SVG,
	# and HTML old never had at all), not the metric computation itself.
	no_plot = getattr(args, "no_plot", False)

	# -np drives OpenMP inside the compiled kernels; the Python engine has no
	# parallel path at all, so asking for N cores there silently gets one. Say so
	# rather than let the run look like the tool does not scale.
	if not use_cython and int(getattr(args, "nprocs", 1)) > 1:
		print(Fore.YELLOW + Style.BRIGHT +
			f"WARNING: --engine python is single-threaded; -np {args.nprocs} will be ignored. "
			"Drop --engine python to use the compiled kernels, which do honour -np."
			+ Style.RESET_ALL)

	# brute_force only exists in the compiled engine (algorithms/brute_force.py
	# was removed), so --engine python cannot serve it. Falling back to Cython
	# would report a python-engine run that never happened. Only the finders
	# search: kp-info/gc-info carry -a with its brute_force default but never use it.
	if (not use_cython and getattr(args, "algorithm", None) == "brute_force"
			and getattr(args, "subcommand", None) in ("kp-finder", "gc-finder")):
		sys.exit(Fore.RED + Style.BRIGHT +
			"ERROR: --algorithm brute_force has no python implementation, so it cannot "
			"be run with --engine python. Use --algorithm greedy or gradient_descent "
			"for the python engine, or drop --engine python to brute-force with the "
			"compiled kernels." + Style.RESET_ALL)

	### Initialize the graph
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
		
		# handle the output path
		dirpath, filename = os.path.split(args.inputFile)
		filename = filename.strip().split(".")[0]

		if args.outdir == None:
			print("No Output directory specified")
			outdir = dirpath
		else:
			outdir = args.outdir

		print(f"\nWorking on: {args.inputFile}\n")
		g = Graphtacle.from_file(args.inputFile, args.command, args.fileType, sep, header, directed, weighted)
		g.path_function(outdir)

		## Checking if nodes have to be removed

		if args.remove:
			nodes_toRemove = (args.remove).split(',')
			nodes_list = [x.replace(" ", "") for x in nodes_toRemove]
			g.remove_node(nodes_list) ##assegno a var di classe
			index_toRemove = [i for i in range(len(g.vs["name"])) if g.vs["name"][i] in nodes_list]
			g.delete_vertices(index_toRemove) #remove target nodes
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, args.inputFile)
			# Graphtacle.re() builds a brand new instance via __init__, which resets
			# self.removed = None -- re-stamp it here or every report downstream
			# (HTML/TSV) prints "Removed nodes: None" even though -r was passed.
			g.remove_node(nodes_list)
			g.name=g.name+"_NoNodes"
			filename = g.name
			print(f"Nodes removed : {nodes_list}\n")
		else:
			print("No nodes removed\n")
			nodes_toRemove = None

		print(f"Number of nodes: {len(g.vs.indices)}")
		print(f"Number of edges: {len(g.es.indices)}")
		# print("Edges with weights:")
		# for edge in g.es:
		# 	source = g.vs[edge.source]["name"]
		# 	target = g.vs[edge.target]["name"]
		# 	weight = edge["weight"] if "weight" in edge.attributes() else None
		# 	print(f"{source} -- {target} : {weight}")

		# Detect if there are multiple components
		print(f"Number of components: {len(g.components())}")
		if len(g.components())>1:
			print("WARNING: The keyplayer colored in the figure could be only one of the possible sets\n" + Style.RESET_ALL)

			print(Fore.YELLOW + Style.BRIGHT + f"WARNING: The graph is fragmented in {len(g.components())} components"+ Style.RESET_ALL)
			# print(f"Number of nodes in the largest component: {len(g.components().giant().vs.indices)}")
			# print(f"Number of edges in the largest component: {len(g.components().giant().es.indices)}")


	else: # in case of 'generate'
		cwd = os.getcwd()

		if args.outdir == None:
			print("No Output directory specified, the output will be stored to the current working directory")
			outdir = cwd
		else:
			outdir = args.outdir

	print(f"Function : {args.command}\n")

	### Generating Local metrics
	if args.command == "local":
		
		if args.color:
			nodes_toColor = (args.color).split(',')
			nodes_list_color = [x.replace(" ", "") for x in nodes_toColor]
			print(f"Colored nodes : {nodes_list_color}\n")

		df =  pd.DataFrame({
					"Node Name" : g.vs["label"],
					"Degree": g.degree(), 
					"Betweenness": g.betweenness(weights=g.es["weight"]),
					"Closeness": g.closeness(weights=g.es["weight"]),
					"Radiality": g.radiality(),
					"Radiality reach": g.radiality_reach(),
					"Clustering Coefficient": g.transitivity_local_undirected(weights=g.es["weight"],mode="zero"),
					"Eccentricity": g.eccentricity(),
					"Eigenvector (Scaled)": g.eigenvector_centrality(weights=g.es["weight"],scale=True),
					"Pagerank": g.pagerank(weights=g.es["weight"])
					})

		if not no_plot:
			create_local_html(df,g,outdir)

	### Generating Global metrics
	elif args.command == "global":
		# Compute the weighted all-pairs shortest-path matrix and the unweighted
		# diameter once, then feed them to radiality/radiality_reach so each APSP
		# is not recomputed per-metric.
		sps_w = distance_matrix(g, weights=g.es["weight"])
		diam_u = g.diameter()
		# radiality subtracts a mean distance from the diameter, so both have to be
		# measured in the same unit: weighted sps go with the weighted diameter.
		diam_w = g.diameter(weights=g.es["weight"])
		radiality = g.radiality(sps=sps_w, diameter=diam_w)
		radiality_reach = g.radiality_reach(sps=sps_w, diameter=diam_w)
		df =  pd.DataFrame({
					"Average shortest path length" : g.average_path_length(directed=directed, unconn=False),
					"Median shortest path length": g.median_global_shortest_path_length(),
					"Diameter": g.diameter(weights=g.es["weight"]),
					"Components": len(g.components()),
					"Radius": float(g.radius()),
					"Density": g.density(),
					"pi": g.ecount()/diam_u,
					"Average clustering coefficient": g.transitivity_avglocal_undirected(),
					"Weighted clustering coefficient": g.transitivity_undirected(),
					"Average degree": mean(g.degree()),
					"Average Closeness":mean(g.closeness(weights=g.es["weight"])),
					"Average Eccentricity":mean(g.eccentricity()),
					"Average Radiality":(mean(radiality)),
					"Average Radiality Reach": mean(radiality_reach),
					"Completeness Naive": g.completeness_naive(directed=directed),
					"Completeness":g.completeness(directed=directed),
					"Compactness": g.compactness(directed=directed)
					},  index=[0]).melt()
		df.columns=["Measure","Score"]

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

				# old code
				# if args.operation=="all":
				# 	print("all\n")        
				# 	df = brute_force_groupcentrality(g, int(args.k_size), args.operation, distance_type=args.value, nprocs=int(args.nprocs))
				# 	g.nameSub_function("finder_"+args.operation)
				# else:
				# 	if args.value:
				# 		print(args.operation)
				# 		gc_set, score = brute_force_groupcentrality(g, int(args.k_size), args.operation, distance_type=args.value, nprocs=int(args.nprocs))
				# 		df = pd.DataFrame({"Nodes_set" : gc_set,args.operation : score}) 
				# 		g.nameSub_function("finder_"+args.operation)
				# 	else:
				# 		print(args.operation)
				# 		gc_set, score = brute_force_groupcentrality(g, int(args.k_size), args.operation, distance_type=None, nprocs=int(args.nprocs))
				# 		df = pd.DataFrame({"Nodes_set" : gc_set,args.operation : score}) 
				# 		g.nameSub_function("finder_"+args.operation)
			
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
				raise TypeError(u"Select the the correct algorithm [brute_force | greedy | gradient_descent]") 

			if not no_plot:
				# Normalize brute_force/greedy/gradient_descent x all/single into the
				# same canonical Operation/NodeSet/Score contract create_keyplayer_html
				# already uses. df's own column names/shapes are inconsistent across
				# the three algorithms ("Group Centrality" vs "Groupcentrality" vs, for
				# brute_force's single-operation branch, a copy-pasted "Key-player"), so
				# index positionally instead of by name. For "all" each row already
				# holds a full node-set list per cell; for a single operation the dict
				# construction above spreads the k found node names across k rows with
				# the score broadcast onto each -- collapse that back into one row.
				if tie_info:
					# Brute force already carries one entry per operation, with every
					# optimal set attached; positional indexing of df would now hit the
					# SetID column instead of the node sets.
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
			
			if args.nodes is None:
				print(Fore.YELLOW + Style.BRIGHT + "WARNING: No nodes specified. Specify the nodes using the -n flag" + Style.RESET_ALL)
				return
			
			nodes=args.nodes.split(",")


			if args.operation=="all":

				info_results = []
				for oper in ["degree", "betweenness", "closeness"]:
					info_results.append((nodes, cython_wrapper_info(g, nodes, oper, distance_type=args.value, mdist=-1, n_threads=int(args.nprocs))))

				df = pd.DataFrame(info_results, columns=["Node-set","Score"])
				df.insert(0, 'Operation', ["degree","betweenness","closeness"])
				g.nameSub_function("info_"+args.operation)

			else:

				score = cython_wrapper_info(g, nodes, args.operation, distance_type=args.value, mdist=-1, n_threads=int(args.nprocs))
				df = pd.DataFrame({"Node-set" : "[" + ",".join(nodes) + "]", args.operation : score}, index=[0]) 
				g.nameSub_function("info_"+args.operation)

		else:
			raise TypeError(u"Select the the correct subcommand [gc-finder | gc-info]") 

	### Keyplayer
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
				raise TypeError(u"Select the correct algorithm [brute_force | greedy | gradient_descent]")

		elif args.subcommand == "kp-info":

			if args.nodes is None:
				print(Fore.YELLOW + Style.BRIGHT + "WARNING: No nodes specified. Specify the nodes using the -n flag" + Style.RESET_ALL)
				return

			nodes=args.nodes.split(",")

			if args.operation=="all":

				info_results = []
				for oper in ['F', 'dF', 'dR', 'mreach']:
					info_results.append((nodes, cython_wrapper_info(g, nodes, oper, distance_type='min', mdist=int(args.mdist), n_threads=int(args.nprocs))))

				df = pd.DataFrame(info_results, columns=["Key-player","Score"])
				df.insert(0, 'Operation', ["F","dF","dR","mreach"])
				g.nameSub_function("info_"+args.operation+"_"+args.algorithm)

			else:

				score = cython_wrapper_info(g, nodes, args.operation, distance_type='min', mdist=int(args.mdist), n_threads=int(args.nprocs))
				df = pd.DataFrame({"Key-player" : "[" + ",".join(nodes) + "]", args.operation : score}, index=[0]) 
				g.nameSub_function("info_"+args.operation)
		
		else:
		
			raise TypeError(u"Select the right option") 

	### Set-Theory
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
			#gi=g1.intersection(g2) ## non rimuove gli isolati
			# Identifica i vertici comuni
			common_vertices = set(g1.vs["name"]).intersection(set(g2.vs["name"]))
			# Identifica gli archi comuni
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
			raise TypeError(u"Select the right option: union | intersection | difference")

	### Converter
	elif args.command == "convert":
		print("\nConvert")
		output_decision(g,args.typeOutput,args.outputName)

	### Communities
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

	### Extract
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

	### Generate
	elif args.command == "generate":
		print("\nGenerate")
		if args.subcommand=='erdos-renyi':
			if not all(x == False for x in [args.numberNodes, args.numberEdges, args.probability]):
				grafo=erdos_renyi(int(args.numberNodes), int(args.numberEdges), float(args.probability), directed=args.directed, loops=args.loops)
				filename = outdir+"/erdos_renyi"
				g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
				output_decision(g,args.fileType,filename)
			else:
				TypeError(u"One of the arguments is missing")

		elif args.subcommand=="tree":
			if not all(x == False for x in [int(args.numberNodes), int(args.children)]):
				grafo=tree_generate(int(args.numberNodes), int(args.children), args.directed)
				filename = outdir+"/tree"
				g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
				output_decision(g,args.fileType,filename)
			else:
				TypeError(u"One of the arguments is missing")

		elif args.subcommand=='barabasi':
			if not all(x == False for x in [int(args.numberNodes), int(args.averageEdge)]):
				grafo=barabasi(int(args.numberNodes), int(args.averageEdge), directed=args.directed, implementation=args.implementation)
				filename = outdir+"/barabasi"
				g=Graphtacle.re(grafo, args.subcommand, args.fileType, file=filename)
				output_decision(g,args.fileType,filename)
			else:
				TypeError(u"One of the arguments is missing")

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
			TypeError(u"Select the right option: erdos-renyi | tree | barabasi | watts-strogatz | lattice")

	#### mesoscale
	elif args.command == "mesoscale":
		print("Mesoscale\n")
		
		df_ti = ti( g, int(args.kSteps), weighted=False, weight_attr=None, threshold=args.threshold, verbose=args.verbose ) 
		
		if weighted:

			df_wi = ti( g, int(args.kSteps), weighted=True, weight_attr="weight", threshold=args.threshold, verbose=args.verbose) 

		df_gtom = gtom(g, int(args.kSteps), verbose=args.verbose)

	#### percolation
	elif args.command == "percolation":
		print("Percolation\n")
		# imported lazily: percolation.py pulls in plotly, keep it out of the other commands
		from percolation import (run_percolation, summarize_percolation_results,
								  save_percolation_html_v2)

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
			save_percolation_html_v2(g, results, filename=html_path, name=filename)
			print(f"\nInteractive HTML saved in: {html_path}")

		# per-node activation / recovery report
		node_labels = results["node_labels"]
		perc_df = pd.DataFrame({
			"Node": node_labels,
			"Activation_time": results["activation_time"],
			"Recovery_time": results["recovery_time"],
		})

		# optional snapshot of node states at a chosen time (captured inline
		# by run_percolation itself -- see snapshot_infected/snapshot_node)
		if results["snapshot_state"] is not None:
			snap_t = results["snapshot_time"]
			state_names = {0: "susceptible", 1: "infected", 2: "recovered"}
			perc_df[f"State_at_t{snap_t}"] = [state_names[int(x)] for x in results["snapshot_state"]]

		perc_df.to_csv(report_path, sep="\t", index=False)
		print(f"\nCreated report in: {report_path}.\n")

	else:
		raise TypeError(u"Select the right option:  local | global | groupcentrality | keyplayer | set | convert | communities | extract | generate | mesoscale | percolation")

	############################################################################################################################################
	####################################### OUTPUT img , tsv ######################################################################
	############################################################################################################################################

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

			# Normalize every kp-finder/kp-info x all/single-operation shape into the
			# same canonical Operation/KeySet/Score contract for the HTML report --
			# KeySet is always a plain list of node names, one row per operation.
			if args.subcommand == "kp-info":
				if args.operation == "all":
					df_html = pd.DataFrame({
						"Operation": df["Operation"],
						"KeySet": [list(nodes) for _ in range(len(df))],
						"Score": df["Score"],
					})
				else:
					df_html = pd.DataFrame({
						"Operation": [str(args.operation)],
						"KeySet": [list(nodes)],
						"Score": [df[str(args.operation)].iloc[0]],
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
		#elif :
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



if __name__ == '__main__':

	# build the parser
	parser = create_parser()
	
	# parse arguments
	args = parser.parse_args()

	# no subcommand given: print help instead of crashing on args.directed
	if args.command is None:
		parser.print_help()
		sys.exit(0)

	# call main function
	main(args)
