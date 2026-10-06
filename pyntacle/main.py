import matplotlib
# figures are written to files: no window, no display needed (cluster nodes have none)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import argparse
import os
import sys
import warnings
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


def fail(err):
	"""Stop with a one-line error instead of a traceback."""
	message = str(err) if str(err).startswith("ERROR") else "ERROR: " + str(err)
	sys.exit(Fore.RED + Style.BRIGHT + message + Style.RESET_ALL)


def read_network(path, args, sep, header, directed, weighted, **kwargs):
	"""Load an input network, stopping with a one-line error when it cannot be read."""
	if not os.path.isfile(path):
		fail(f"input file not found: {path}")
	if os.path.getsize(path) == 0:
		fail(f"input file is empty: {path}")
	try:
		return Graphtacle.from_file(path, args.command, args.fileType, sep, header, directed, weighted, **kwargs)
	except ValueError as err:
		fail(err)
	except Exception as err:
		fail(f"could not read {path} as '{args.fileType}' ({type(err).__name__}: {err}). "
		     "Check -t, -s and -nh.")


def show_table(df, max_rows=20):
	"""Print a result table whole in width, cut to `max_rows` rows: the report has all of it."""
	with pd.option_context("display.max_columns", None, "display.width", None,
	                       "display.max_colwidth", 60):
		print(df.head(max_rows).to_string(index=False))
	if len(df) > max_rows:
		print(f"... {len(df) - max_rows} more rows in the report")


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

	# generate has neither: it writes undirected, unweighted networks
	directed = bool(getattr(args, "directed", False))
	weighted = bool(getattr(args, "weight", False))

	# The compiled kernels work on undirected graphs only: refuse -d before the
	# file is loaded.
	if directed and args.command in ("keyplayer", "groupcentrality"):
		sys.exit(Fore.RED + Style.BRIGHT +
			f"ERROR: --directed is not supported by '{args.command}'. "
			"Drop -d to analyse the network as undirected, or use the 'local' or "
			"'global' commands, which do handle directed graphs."
			+ Style.RESET_ALL)

	if directed and args.command in ("set", "extract", "convert"):
		sys.exit(Fore.RED + Style.BRIGHT +
			f"ERROR: '{args.command}' writes undirected networks only. Drop -d."
			+ Style.RESET_ALL)

	use_cython = getattr(args, "engine", "cython") != "python"
	seed = getattr(args, "seed", None)

	# Brute force fills this with oper -> (tied_sets, n_optimal, score): several
	# node sets can reach the same optimum and all of them are reported. Greedy
	# and gradient descent return a single set and leave it empty.
	tie_info = {}
	report_notes = []
	# (label, path) of every figure and HTML page, printed after the report
	written = []
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
		header = not args.NoHeader
		sep = str(args.sep) if args.sep else None

		# outputs go to -o, or next to the input file
		dirpath, filename = os.path.split(args.inputFile)
		filename = filename.strip().split(".")[0]
		outdir = args.outdir or dirpath or "."

		print(Style.BRIGHT + f"pyntacle {args.command}" + (f" {args.subcommand}" if getattr(args, "subcommand", None) else "")
		      + Style.RESET_ALL)
		print(f"Input: {args.inputFile}")
		print(f"Output directory: {os.path.abspath(outdir)}")
		# analysis commands read the weights as declared by -wt/-dt; commands that
		# only write the network back out keep them exactly as read
		weight_type = getattr(args, "weightType", None) if weighted else None
		g = read_network(args.inputFile, args, sep, header, directed, weighted, weight_type=weight_type,
		                 distance_transform=getattr(args, "distanceTransform", "inverse"))
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
			nodes_list = [x.strip() for x in args.remove.split(",") if x.strip()]
			unknown = sorted(set(nodes_list) - set(g.vs["name"]))
			if unknown:
				sys.exit(Fore.RED + Style.BRIGHT + "ERROR: -r names nodes not in the network: "
				         + ", ".join(unknown) + Style.RESET_ALL)
			g.remove_node(nodes_list)
			index_toRemove = [i for i in range(len(g.vs["name"])) if g.vs["name"][i] in nodes_list]
			g.delete_vertices(index_toRemove) #remove target nodes
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, args.inputFile)
			# re() builds a new instance, which resets the removed-node list
			g.remove_node(nodes_list)
			g.name=g.name+"_NoNodes"
			filename = g.name
			print(f"Removed nodes: {', '.join(nodes_list)}")
			nodes_toRemove = nodes_list
		else:
			nodes_toRemove = None

		n_components = len(g.components())
		print(f"Network: {g.vcount()} nodes, {g.ecount()} edges, {n_components} component(s)")
		if n_components > 1 and args.command in Graphtacle.DISTANCE_COMMANDS:
			warn(f"the network is split into {n_components} components; metrics based on "
			     "shortest paths only see the pairs that can reach each other")
		print("")

		if getattr(args, "subcommand", None) in ("kp-finder", "gc-finder"):
			if args.k_size >= g.vcount():
				fail(f"-k must be smaller than the number of nodes ({g.vcount()})")
			engine = "" if use_cython else ", python engine"
			threads = f", {args.nprocs} threads" if use_cython and args.nprocs > 1 else ""
			print(f"Search: {args.algorithm}, k = {args.k_size}, operation {args.operation}{engine}{threads}\n")
			search_start = time()

	else: # in case of 'generate'
		outdir = args.outdir or os.getcwd()
		print(Style.BRIGHT + f"pyntacle generate {args.subcommand}" + Style.RESET_ALL)
		print(f"Output directory: {os.path.abspath(outdir)}")


	# ---- local ----
	if args.command == "local":
		
		if args.color:
			nodes_list_color = [x.strip() for x in args.color.split(",") if x.strip()]
			unknown = sorted(set(nodes_list_color) - set(g.vs["name"]))
			if unknown:
				fail("-c names nodes not in the network: " + ", ".join(unknown))
			print(f"Highlighted nodes: {', '.join(nodes_list_color)}\n")

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
			written.append(("HTML report", create_local_html(df, g, outdir)))

	# ---- global ----
	elif args.command == "global":
		# all-pairs distances computed once and shared by radiality and radiality reach
		lengths = path_lengths(g)
		sps_w = distance_matrix(g, weights=lengths)
		# radiality needs the diameter in the same unit as the distances
		diam_w = finite_max(sps_w)
		radiality = g.radiality(sps=sps_w, diameter=diam_w)
		radiality_reach = g.radiality_reach(sps=sps_w, diameter=diam_w)
		# hop distances: the weighted matrix itself when every weight is 1;
		# otherwise the weighted one is freed before the hop one is built
		sps_u = sps_w if lengths is None else None
		del sps_w
		if sps_u is None:
			sps_u = distance_matrix(g, dtype=np.float32)
		diam_u = finite_max(sps_u)
		median_hops = g.median_global_shortest_path_length(sps=sps_u)
		del sps_u
		df =  pd.DataFrame({
					# over the pairs that reach each other, as the median
					"Average shortest path length" : g.average_path_length(directed=directed, unconn=True),
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
					
					k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(g, int(args.k_size), args.operation, n_threads=int(args.nprocs), max_ties=max_ties)
					tie_info[args.operation] = (tied_sets, n_optimal, score)
					df = tied_sets_frame(tie_info, "Group Centrality", explode=True, score_column=args.operation)
					report_notes.extend(tie_notes(tie_info))
					g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)


			elif args.algorithm=="greedy":
				if use_cython:

					if args.operation == "all":
						greedy_results = []
						for oper in ["degree", "betweenness", "closeness"]:
							greedy_results.append(cython_wrapper_greedy(g, int(args.k_size), oper, distance_type=args.value, n_threads=int(args.nprocs), seed=seed))

						df = pd.DataFrame(greedy_results, columns=["Groupcentrality","score"])
						df.insert(0, 'operation', ["degree", "betweenness", "closeness"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					else:
						k_set, score = cython_wrapper_greedy(g, int(args.k_size), args.operation, distance_type=args.value, n_threads=int(args.nprocs), seed=seed)
						df = pd.DataFrame({"Groupcentrality": k_set, args.operation: score})	
						g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)

				else:
					if args.operation=="all":
						tmp=call_all_greedy(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,function=args.command,seed=seed)
						df=pd.DataFrame(tmp,columns=["Groupcentrality","score"])
						df.insert(0, 'operation', ["degree","closeness","betweenness"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					else:
						gc=call_greedy(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,seed=seed)
						df=pd.DataFrame({"Groupcentrality":gc[0], args.operation:gc[1]})
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

			elif args.algorithm=="gradient_descent":
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
			print(f"Search time: {time() - search_start:.2f} s\n")

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
				written.append(("HTML report", create_groupcentrality_html(with_tie_columns(df_html, "NodeSet", tie_info), g, outdir, filename)))

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
				written.append(("HTML report", create_groupcentrality_html(with_tie_columns(df_html, "NodeSet"), g, outdir, filename)))

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
					
					k_set, score, tied_sets, n_optimal = cython_wrapper_bruteforce(g, int(args.k_size), args.operation, mdist=int(args.mdist), n_threads=int(args.nprocs), max_ties=max_ties)
					tie_info[args.operation] = (tied_sets, n_optimal, score)
					df = tied_sets_frame(tie_info, "Key-player", explode=True, score_column=args.operation)
					report_notes.extend(tie_notes(tie_info))
					g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)
			
			elif args.algorithm == "greedy":

				if use_cython:

					if args.operation == "all":
						greedy_results = []
						for oper in ['F', 'dF', 'dR', 'mreach']:
							greedy_results.append(cython_wrapper_greedy(g, int(args.k_size), oper, mdist=int(args.mdist), n_threads=int(args.nprocs), seed=seed))

						df = pd.DataFrame(greedy_results, columns=["Key-player","score"])
						df.insert(0, 'operation', ["F","dF","dR","mreach"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					else:
						k_set, score = cython_wrapper_greedy(g, int(args.k_size), args.operation, mdist=int(args.mdist), n_threads=int(args.nprocs), seed=seed)
						df = pd.DataFrame({"Key-player": k_set, args.operation: score})	
						g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)
				
				else:

					if args.operation=="all": 

						tmp=call_all_greedy(g, int(args.k_size), args.operation, distance_type=None, mdist=int(args.mdist), function=args.command, seed=seed)
						df=pd.DataFrame(tmp,columns=["Key-player","score"])
						df.insert(0, 'operation', ["F","dF","dR","mreach"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					
					else:
					
						kset=call_greedy(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist),seed=seed)
						df=pd.DataFrame({"Key-player":kset[0], args.operation:kset[1]})	
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					

			elif args.algorithm == "gradient_descent":
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
			print(f"Search time: {time() - search_start:.2f} s\n")

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
		# the second network is read with the same -t, -s, -nh and -w as the first
		filename2 = os.path.split(args.inputFile2)[1].strip().split(".")[0]
		print(f"Second input: {args.inputFile2}")
		g2 = read_network(args.inputFile2, args, sep, header, directed, weighted)
		try:
			result = set_operation(plain_copy(g, directed=False), plain_copy(g2, directed=False), args.subcommand)
		except ValueError as err:
			fail(err)
		g1_names, g2_names = list(g.vs["name"]), list(g2.vs["name"])
		name = f"{filename}_{args.subcommand}_{filename2}"
		g = Graphtacle.re(result, args.command, args.fileType, sep, header, directed, weighted, name)
		g.name = name
		df = component_table(result)
		network_path = output_decision(g, args.fileType, name, outdir)
		print(f"{args.subcommand.capitalize()} of {filename} and {filename2}: "
		      f"{result.vcount()} nodes, {result.ecount()} edges, "
		      f"{len(result.connected_components())} component(s)")
		print(f"Network file: {network_path}")
		if not no_plot:
			path = os.path.join(outdir, f"{name}.{args.format}")
			if args.subcommand == "union":
				g.plot_set(filename, filename2, g1_names, g2_names, path)
			else:
				ig.plot(plain_copy(g), opacity=0.7, target=path,
				        vertex_label=g.vs["name"], bbox=(1000, 1000), edge_width=0.8, vertex_size=15)
			written.append(("Figure", path))
		# the generic figure at the end would draw the same network again
		no_plot = True

	# ---- convert ----
	elif args.command == "convert":
		network_path = output_decision(g, args.typeOutput, args.outputName, outdir)
		print(f"Network file: {network_path}")

	# ---- communities ----
	elif args.command == "communities":
		try:
			modules = communities(g, args.subcommand, args.numberCommunities, args.giant, args.steps, args.communitySize)
		except ValueError as err:
			fail(err)
		# clique percolation returns graphs of cliques: a community is the union of their nodes
		if args.subcommand == "percolation":
			members = [sorted({n for v in m.vs for n in v["label"]}) for m in modules]
		else:
			members = [m.vs["name"] for m in modules]
		base = plain_copy(g, directed=False)
		node_graphs = [base.induced_subgraph(names) for names in members]
		filtered_mod = communities_filtering(node_graphs, args.minNodes, args.maxNodes, args.minComponents, args.maxComponents)
		kept = [i for i, m in enumerate(node_graphs) if any(m is f for f in filtered_mod)]
		if not kept:
			fail(f"no community passes the size filters; the {len(modules)} found have "
			     + ", ".join(str(len(m)) for m in members) + " nodes")
		print(f"Communities: {len(modules)} found" +
		      (f", {len(kept)} kept by the filters" if len(kept) < len(modules) else ""))
		df = communities_to_df([modules[i] for i in kept], args.subcommand, ids=[i + 1 for i in kept])
		community_graphs = {i + 1: node_graphs[i] for i in kept}

	# ---- extract ----
	elif args.command == "extract":
		if args.nodeList:
			nodes_list_extr = [x.strip() for x in args.nodeList.split(",") if x.strip()]
		try:
			if args.selectComponent:
				sub_func, (sub, df) = "selected_subgraph", selecting_component(plain_copy(g, directed=False), int(args.selectComponent))
			elif args.largest and args.ncomponents:
				sub_func, (sub, df) = "largest_subgraphs", extract_and_df(plain_copy(g, directed=False), int(args.ncomponents))
			elif args.largest:
				sub_func, (sub, df) = "largest_component", extract_and_df(plain_copy(g, directed=False))
			elif args.ncomponents:
				sub_func, (sub, df) = "removed_subgraphs", extract_and_df(plain_copy(g, directed=False), -int(args.ncomponents))
			elif args.nodeList:
				sub_func, (sub, df) = "selected_by_nodes", components_by_nodes(g, nodes_list_extr)
			else:
				sys.exit(Fore.RED + Style.BRIGHT + "ERROR: extract needs one of -l, -l -n N, -n N, -sc N or -nl NODES"
				         + Style.RESET_ALL)
		except ValueError as err:
			fail(err)
		g = Graphtacle.re(sub, args.command, args.fileType, sep, header, directed, weighted, filename)
		g.function = args.command
		g.sub_func = sub_func
		network_path = output_decision(g, args.fileType, f"{filename}_{g.function}_{g.sub_func}", outdir)
		print(f"Extracted: {sub.vcount()} nodes, {sub.ecount()} edges, "
		      f"{len(sub.connected_components())} component(s)")
		print(f"Network file: {network_path}")
		print("")

	# ---- generate ----
	elif args.command == "generate":
		sub = args.subcommand
		def need(*flags):
			missing = [flag for flag, value in flags if value is None]
			if missing:
				sys.exit(Fore.RED + Style.BRIGHT + f"ERROR: generate {sub} needs " + ", ".join(missing) + Style.RESET_ALL)
		try:
			if sub == "erdos-renyi":
				need(("-n", args.numberNodes))
				if (args.probability is None) == (args.numberEdges is None):
					fail("generate erdos-renyi needs either -e (number of edges) or -p (wiring probability), not both")
				n = args.numberNodes
				most = n * (n - 1) // 2 + (n if args.loops else 0)
				if args.numberEdges is not None and args.numberEdges > most:
					fail(f"-e is at most {most} for {n} nodes" + ("" if args.loops else " without self-loops (-l)"))
				grafo = erdos_renyi(int(args.numberNodes), int(args.numberEdges or 0), float(args.probability or 0),
				                    loops=args.loops)
			elif sub == "tree":
				need(("-n", args.numberNodes), ("-c", args.children))
				grafo = tree_generate(int(args.numberNodes), int(args.children), False)
			elif sub == "barabasi":
				need(("-n", args.numberNodes), ("-a", args.averageEdge))
				grafo = barabasi(int(args.numberNodes), int(args.averageEdge), implementation=args.implementation)
			elif sub == "watts-strogatz":
				need(("-s", args.size), ("-nei", args.nei), ("-p", args.probability))
				if args.dimension and len(args.dimension) > 1:
					fail("watts-strogatz takes one number with -dim: how many dimensions the starting lattice has")
				grafo = watts_strogatz(dim=args.dimension[0] if args.dimension else 1, size=int(args.size), nei=int(args.nei),
				                       probability=float(args.probability), loops=args.loops, multiple=args.multiple)
			else:
				need(("-dim", args.dimension))
				grafo = lattice(dimension=args.dimension, nei=int(args.nei or 1),
				                circular=args.circular)
		except (ValueError, ig.InternalError) as err:
			fail(err)
		name = f"{sub.replace('-', '_')}_n{grafo.vcount()}_e{grafo.ecount()}"
		g = Graphtacle.re(grafo, sub, args.fileType, file=name)
		network_path = output_decision(g, args.fileType, name, outdir)
		print(f"Generated {sub}: {grafo.vcount()} nodes, {grafo.ecount()} edges")
		print(f"Network file: {network_path}")

	# ---- mesoscale ----
	elif args.command == "mesoscale":
		
		df_ti = ti( g, int(args.kSteps), weighted=False, weight_attr=None, threshold=args.threshold, verbose=args.verbose ) 
		
		if weighted:

			# TI spreads effects in proportion to tie strength
			df_wi = ti( g, int(args.kSteps), weighted=True, weight_attr="affinity", threshold=args.threshold, verbose=args.verbose) 

		df_gtom = gtom(g, int(args.kSteps), verbose=args.verbose)

	# ---- percolation ----
	elif args.command == "percolation":
		# imported here so the other commands do not load plotly
		from pyntacle.percolation import (run_percolation, summarize_percolation_results,
								  save_percolation_html)

		# optional per-node recovery times from a TSV file (columns: Nodes, Recovery_time)
		tau_vector = None
		if args.tauFile:
			if not os.path.isfile(args.tauFile):
				fail(f"-tauFile not found: {args.tauFile}")
			tau_df = pd.read_csv(args.tauFile, sep=None, engine="python")
			if not {"Nodes", "Recovery_time"} <= set(tau_df.columns):
				fail(f"-tauFile needs the columns Nodes and Recovery_time; {args.tauFile} has "
				     + ", ".join(map(str, tau_df.columns)))
			try:
				tau_map = dict(zip(tau_df["Nodes"].astype(str), tau_df["Recovery_time"].astype(float)))
			except ValueError:
				fail(f"-tauFile: Recovery_time must be numeric in {args.tauFile}")
			missing = [str(name) for name in g.vs["name"] if str(name) not in tau_map]
			if missing:
				fail("-tauFile has no recovery time for: " + ", ".join(missing[:10])
				     + (f" and {len(missing) - 10} more" if len(missing) > 10 else ""))
			tau_vector = [tau_map[str(name)] for name in g.vs["name"]]

		# a run without --seed draws one and prints it, so any run can be repeated
		perc_seed = args.seed if args.seed is not None else int(np.random.default_rng().integers(2**31))
		print(f"Random seed: {perc_seed}")

		try:
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
				seed=perc_seed,
			)
		except ValueError as err:
			fail(err)

		print(summarize_percolation_results(g, results))

		html_path = os.path.join(outdir, f"{filename}_percolation.html")
		report_path = os.path.join(outdir, f"report_{filename}_percolation.tsv")

		if not no_plot:
			# interactive HTML animation of the spreading process
			save_percolation_html(g, results, filename=html_path, name=filename)
			written.append(("HTML report", html_path))

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
		print(f"\nReport: {report_path}")

	else:
		raise TypeError("Select the right option:  local | global | groupcentrality | keyplayer | set | convert | communities | extract | generate | mesoscale | percolation")

	# ---- reports and figures ----

	if args.command == "convert" or args.command == "generate" or args.command == "percolation":
		pass
	elif args.command == "set":
		print("")
		show_table(df)
		report_path = g.export_file(df, outdir)
		print(f"\nReport: {report_path}")

	elif args.command == "communities":
		if not no_plot:
			large = [i for i, c in community_graphs.items() if c.vcount() > 20]
			if large:
				warn("communities with more than 20 nodes are not drawn: " + ", ".join(map(str, large)))
			for i, c in community_graphs.items():
				if c.vcount() <= 20:
					path = os.path.join(outdir, f"{filename}_community_{i}.{args.format}")
					ig.plot(c, target=path, bbox=(600, 600), vertex_label=c.vs["name"], vertex_color="#BDC3C7")
					written.append(("Figure", path))
		print("")
		show_table(df)
		report_path = g.export_file(df, outdir)
		print(f"\nReport: {report_path}")
	elif args.command == "mesoscale":
		
		df_ti = df_ti.round(3) 
		df_gtom = df_gtom.round(3)
	
		k = int(args.kSteps)
		summary = pd.DataFrame({"Node": df_ti.index, f"TI_{k}": df_ti.iloc[:, -1].values})
		if weighted:
			df_wi = df_wi.round(3)
			summary[f"WI_{k}"] = df_wi.iloc[:, -1].values
		show_table(summary.sort_values(f"TI_{k}", ascending=False, kind="stable"))
		print("The full topological importance and overlap matrices are in the report.")

		if not no_plot:
			path = os.path.join(outdir, f"{filename}_{g.function}.{args.format}")
			ig.plot(plain_copy(g), opacity=0.7, target=path, bbox=(1000, 1000), edge_width=0.8,
			        vertex_size=15, vertex_label_size=2.5)
			written.append(("Figure", path))

		stem = f"report_{g.name}_{g.function}" + (f"_{g.sub_func}" if g.sub_func else "")
		filename = os.path.join(outdir, stem + ".tsv")
		g.name = filename

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
		print(f"\nReport: {filename}")


	elif args.command == "keyplayer":

		df=df.round(3) 
		show_table(df)
		report_path = g.export_file(df, outdir, notes=report_notes)
		print(f"\nReport: {report_path}")

		if not no_plot:
			if args.subcommand=="kp-info":
				pass
			else:
				path = os.path.join(outdir, f"{filename}_{g.function}_{g.sub_func}.{args.format}")
				written.append(("Figure", g.plot_keyplayer(first_set_only(df), args.operation, path)))
				tied = [o for o, (_sets, n_optimal, _score) in tie_info.items() if n_optimal > 1]
				if tied:
					print(f"The figure shows the first optimal set of {', '.join(tied)}; "
					      "the report and the HTML page list all of them.")

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
			written.append(("HTML report", create_keyplayer_html(with_tie_columns(df_html, "KeySet", tie_info), g, outdir, filename)))

	else:
		df=df.round(3) 
		show_table(df)
		report_path = g.export_file(df, outdir, notes=report_notes)

		print(f"\nReport: {report_path}")
		if not no_plot:
			# -c (local) and -nl (extract) nodes are drawn green, the others red
			marked = (nodes_list_color if getattr(args, "color", None)
			          else nodes_list_extr if getattr(args, "nodeList", None) else None)
			style = {"vertex_color": [("green" if n in marked else "red") for n in g.vs["name"]] if marked else "red"}
			if args.command in ("local", "global"):
				stem = f"{filename}_{g.function}"
			else:
				stem = f"{filename}_{g.function}_{g.sub_func}" if g.sub_func else f"{filename}_{g.function}"
				style["vertex_label_size"] = 2.5
			path = os.path.join(outdir, f"{stem}.{args.format}")
			ig.plot(plain_copy(g), opacity=0.7, target=path, bbox=(1000, 1000), edge_width=0.8, vertex_size=15, **style)
			written.append(("Figure", path))

	for label, path in written:
		print(f"{label}: {path}")
	print(Fore.GREEN + Style.BRIGHT + "Done!\n" + Style.RESET_ALL)



def _show_warning(message, category, filename, lineno, file=None, line=None):
	warn(str(message))


def cli(argv=None):
	"""Entry point of the ``pyntacle`` command."""
	warnings.showwarning = _show_warning
	parser = create_parser()
	args = parser.parse_args(argv)

	# no subcommand given: print help instead of crashing on args.directed
	if args.command is None:
		parser.print_help()
		sys.exit(0)

	main(args)


if __name__ == '__main__':
	cli()
