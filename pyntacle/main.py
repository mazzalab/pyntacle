import matplotlib.pyplot as plt
import argparse
import os
import sys
import pandas as pd
import igraph as ig
import numpy as np
from statistics import mean
from colorama import Fore, Style, Back

use_cython = True
from _ext.wrapper import cython_wrapper_greedy, cython_wrapper_info, cython_wrapper_bruteforce

### import of home-made subClass of igraph
from parser import create_parser
from GraphTacle import Graphtacle
from algorithms.group_centrality import *
from algorithms.key_player import *
from algorithms.brute_force import *
from utility import *
from communities import *
from generate import *
from mesoscale import *
from algorithms.greedy import *
from algorithms.stochastic_gradient_descent import *
from create_html import *
from time import time

# main function
def main(args):

	#### Check general flags
	if args.directed:
		directed = True
	else:
		directed = False

	if args.weight:
		weighted = True
	else:
		weighted = False

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

		#create_local_html(df,g,outdir)

	### Generating Global metrics
	elif args.command == "global":
		df =  pd.DataFrame({
					"Average shortest path length" : g.average_path_length(directed=directed, unconn=False),
					"Median shortest path length": g.median_global_shortest_path_length(),
					"Diameter": g.diameter(weights=g.es["weight"]),
					"Components": len(g.components()),
					"Radius": float(g.radius()),
					"Density": g.density(),
					"pi": g.ecount()/g.diameter(),
					"Average clustering coefficient": g.transitivity_avglocal_undirected(),
					"Weighted clustering coefficient": g.transitivity_undirected(),
					"Average degree": mean(g.degree()),
					"Average Closeness":mean(g.closeness(weights=g.es["weight"])),
					"Average Eccentricity":mean(g.eccentricity()),
					"Average Radiality":(mean(g.radiality())),
					"Average Radiality Reach": mean(g.radiality_reach()),
					"Completeness Naive": g.completeness_naive(directed=directed),
					"Completeness":g.completeness(directed=directed),
					"Compactness": g.compactness(directed=directed)
					},  index=[0]).melt()
		df.columns=["Measure","Score"]

	elif args.command == "groupcentrality":
		print(args.subcommand)

		if args.subcommand == "gc-finder":
			if args.algorithm=="brute_force":

				if args.operation=="all":
					
					bruteforce_results = []
					for oper in ['degree', 'betweenness', 'closeness']:
						bruteforce_results.append(cython_wrapper_bruteforce(g, int(args.k_size), oper, n_threads=int(args.nprocs)))

					df = pd.DataFrame(bruteforce_results, columns=["Group Centrality","score"])
					df.insert(0, 'operation', ["F","dF","dR","mreach"])
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					        
				else:
					
					print("Using operation: ", args.operation)
					k_set, score = cython_wrapper_bruteforce(g, int(args.k_size), args.operation, n_threads=int(args.nprocs))
					df = pd.DataFrame({"Key-player": k_set, args.operation: score})	
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
							greedy_results.append(cython_wrapper_greedy(g, int(args.k_size), oper, distance_type=args.value, n_threads=int(args.nprocs)))

						df = pd.DataFrame(greedy_results, columns=["Groupcentrality","score"])
						df.insert(0, 'operation', ["degree", "betweenness", "closeness"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					else:
						print("Using operation: ", args.operation)
						k_set, score = cython_wrapper_greedy(g, int(args.k_size), args.operation, distance_type=args.value, n_threads=int(args.nprocs))
						df = pd.DataFrame({"Groupcentrality": k_set, args.operation: score})	
						g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)

					end = time()
					print(f"Passed Time Cython: {end - start}")
				else:
					print("Using greedy algorithm")
					time_start = time()
					if args.operation=="all":
						tmp=call_all_greedy(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,function=args.command)
						df=pd.DataFrame(tmp,columns=["nodes","score"])
						df.insert(0, 'operation', ["degree","closeness","betweenness"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					else:
						gc=call_greedy(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None)
						df=pd.DataFrame({"Nodes_set":[','.join(gc[0])], args.operation:gc[1]})
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					end = time()
					print(f"Time taken: {end - time_start} seconds")
			elif args.algorithm=="gradient_descent":
				print("Using gradient_descent")
				if args.operation=="all":
					tmp=call_all_sgd(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,probability=args.probability,tolerance=args.tolerance,maxsec=args.maxsec,function=args.command)
					df=pd.DataFrame(tmp,columns=["nodes","score"])
					df.insert(0, 'operation', ["degree","closeness","betweenness"])
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
				else:
					gc=call_stochastic_gradient_descent(g,int(args.k_size),args.operation,distance_type=args.value,mdist=None,probability=float(args.probability),tolerance=float(args.tolerance),maxsec=int(args.maxsec))
					df=pd.DataFrame({"Nodes_set":gc[0], args.operation:gc[1]})
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

			else:
				raise TypeError(u"Select the the correct algorithm [brute_force | greedy | gradient_descent]") 

			if args.operation=="all":
				create_groupcentrality_html(df,g,outdir,filename)
			else:
				# df_single_metric=pd.DataFrame({"Nodes Set": ['B','I']})
				# print(df_single_metric)
				# tmp_s=[]
				# for i in df["Nodes_set"]:
				# 	tmp_s.append(tuple(i))

				# df_single_metric["Nodes Set"].iloc[0]=tmp_s
				# df_single_metric["Operation"]=str(args.operation).capitalize()
				# df_single_metric["Score"]=df[str(args.operation)].unique()[0]
				create_groupcentrality_html(df,g,outdir,filename)

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
					
					bruteforce_results = []
					for oper in ['F', 'dF', 'dR', 'mreach']:
						bruteforce_results.append(cython_wrapper_bruteforce(g, int(args.k_size), oper, mdist=int(args.mdist), n_threads=int(args.nprocs)))

					df = pd.DataFrame(bruteforce_results, columns=["Key-player","score"])
					df.insert(0, 'operation', ["F","dF","dR","mreach"])
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					        
				else:
					
					print("Using operation: ", args.operation)
					k_set, score = cython_wrapper_bruteforce(g, int(args.k_size), args.operation, mdist=int(args.mdist), n_threads=int(args.nprocs))
					df = pd.DataFrame({"Key-player": k_set, args.operation: score})	
					g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)
			
			elif args.algorithm == "greedy":
				print("Using greedy algorithm")

				if use_cython:
					start = time()

					if args.operation == "all":
						greedy_results = []
						for oper in ['F', 'dF', 'dR', 'mreach']:
							greedy_results.append(cython_wrapper_greedy(g, int(args.k_size), oper, mdist=int(args.mdist), n_threads=int(args.nprocs)))

						df = pd.DataFrame(greedy_results, columns=["Key-player","score"])
						df.insert(0, 'operation', ["F","dF","dR","mreach"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)

					else:
						print("Using operation: ", args.operation)
						k_set, score = cython_wrapper_greedy(g, int(args.k_size), args.operation, mdist=int(args.mdist), n_threads=int(args.nprocs))
						df = pd.DataFrame({"Key-player": k_set, args.operation: score})	
						g.nameSub_function("finder_" + args.operation + "_" + args.algorithm)
				
					end = time()
					print(f"Passed Time Cython: {end - start}")
				else:
					start = time()

					if args.operation=="all": 

						tmp=call_all_greedy(g, int(args.k_size), args.operation, distance_type=None, mdist=int(args.mdist), function=args.command)
						df=pd.DataFrame(tmp,columns=["Key-player","score"])
						df.insert(0, 'operation', ["F","dF","dR","mreach"])
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					
					else:
					
						kset=call_greedy(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist))
						df=pd.DataFrame({"Key-player":kset[0], args.operation:kset[1]})	
						g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
					
					end = time()
					print(f"Passed Time pure Python: {end - start}")

			elif args.algorithm == "gradient_descent":
				print("Using gradient_descent")
				if args.operation == "all":
					tmp=call_all_sgd(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist),probability=args.probability,tolerance=args.tolerance,maxsec=args.maxsec,function=args.command)
					df=pd.DataFrame(tmp,columns=["nodes","score"])
					df.insert(0, 'operation', ["F","dF","dR","mreach"])
					g.nameSub_function("finder_"+args.operation+"_"+args.algorithm)
				else:
					kset=call_stochastic_gradient_descent(g,int(args.k_size),args.operation,distance_type=None,mdist=int(args.mdist),probability=float(args.probability),tolerance=float(args.tolerance),maxsec=int(args.maxsec))
					df=pd.DataFrame({"Nodes_set":kset[0], args.operation:kset[1]})
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
			g1 = ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
			g2 = ig.Graph(directed=False,vertex_attrs={"name":g2.vs["name"],"label": g2.vs["label"]},edges=g2.get_edgelist(), edge_attrs={"weight": g2.es["weight"]})
			gu=g1.union(g2)
			df = summary_to_df(gu, args.outdir, filename, filename2)
			gu=get_connected_subgraph(gu)
			g = Graphtacle.re(gu, args.command, args.fileType, sep, header, directed, weighted, outdir+"/union.tsv")
			g.nameSub_function(args.subcommand)

			g.plot_set(filename,filename2,g1.vs["name"],g2.vs["name"],args.format,args.subcommand,outdir=outdir)
			g.name = f"{filename}_&_{filename2}"
			filename_set = f"{filename}_{filename2}"

			output_decision(g,"matrix",g.name+str("_union"))


		elif args.subcommand == 'intersection':
			print("Intersection\n")
			g1 = ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
			g2 = ig.Graph(directed=False,vertex_attrs={"name":g2.vs["name"],"label": g2.vs["label"]},edges=g2.get_edgelist(), edge_attrs={"weight": g2.es["weight"]})
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

			if outdir:
				ig.plot(g, opacity=0.7, target = f"{outdir}/{filename_set}_{g.function}_{g.sub_func}.{args.format}",vertex_label=g.vs["name"], bbox = (1000, 1000),edge_width=0.8,vertex_size=15)
			else:
				ig.plot(g, opacity=0.7, target = f"{filename_set}_{g.function}_{g.sub_func}.{args.format}", vertex_label=g.vs["name"],bbox = (1000, 1000),edge_width=0.8,vertex_size=15)

			output_decision(g,"matrix",g.name+str("_intersection"))


		elif args.subcommand == 'difference':
			print("Difference\n")
			g1 = ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
			g2 = ig.Graph(directed=False,vertex_attrs={"name":g2.vs["name"],"label": g2.vs["label"]},edges=g2.get_edgelist(), edge_attrs={"weight": g2.es["weight"]})

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

			if outdir:
				ig.plot(g, opacity=0.7, target = f"{outdir}/{filename_set}_{g.function}_{g.sub_func}.{args.format}",vertex_label=g.vs["name"], bbox = (1000, 1000),edge_width=0.8,vertex_size=15)
			else:
				ig.plot(g, opacity=0.7, target = f"{filename_set}_{g.function}_{g.sub_func}.{args.format}", vertex_label=g.vs["name"],bbox = (1000, 1000),edge_width=0.8,vertex_size=15)

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
			g=ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
			g,df=selecting_component(g,int(args.selectComponent))
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="selected_subgraph"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif (args.largest) & (args.ncomponents!=False):
			print("Selecting n components...")
			g=ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
			g,df=extract_and_df(g,args.ncomponents)
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="largest_subgraphs"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif args.largest:
			print("Selecting largest component...")
			g=ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
			g,df=extract_and_df(g)
			g = Graphtacle.re(g, args.command, args.fileType, sep, header, directed, weighted, outdir+f"/{filename}.tsv")
			g.function=args.command
			g.sub_func="largest_component"
			output_decision(g,args.fileType,f"{filename}_{g.function}_{g.sub_func}")

		elif args.ncomponents!=False:
			print("Removing the last n components...")
			g=ig.Graph(directed=False,vertex_attrs={"name":g.vs["name"],"label": g.vs["label"]},edges=g.get_edgelist(), edge_attrs={"weight": g.es["weight"]})
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

	else:
		raise TypeError(u"Select the right option:  local | global | groupcentrality | keyplayer | set | convert")

	############################################################################################################################################
	####################################### OUTPUT img , tsv ######################################################################
	############################################################################################################################################

	if args.command == "convert" or args.command == "generate":
		pass
	elif args.command == "set":
		df=df.round(3)
		print("")
		print(df)
		g.export_file(df, outdir)
		print(f"\nCreated report in: {g.name}.\n")

	elif args.command == "communities":
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
		g.export_file(df, outdir)
		print(f"\nCreated report in: {g.name}.\n")
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

		if outdir:
			ig.plot(g, opacity=0.7, target = f"{outdir}/{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_label_size=2.5)
		else:
			ig.plot(g, opacity=0.7, target = f"{filename}_{g.function}.{args.format}", bbox = (1000, 1000),edge_width=0.8,vertex_size=15,vertex_label_size=2.5)


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
			f.write(f"Analysisi type\t{g.function}\n")
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
		g.export_file(df, outdir)
		print(f"\nCreated report in: {g.name}.\n")

		if args.subcommand=="kp-info":
			pass
		else:
			g.plot_keyplayer(df,filename,args.format,args.operation,outdir=outdir)
			print(Fore.YELLOW + Style.BRIGHT + "WARNING: The keyplayer colored in the figure could be only one of the possible sets\n" + Style.RESET_ALL)

		if args.operation=="all":
			create_keyplayer_html(df,g,outdir,filename)
		else:
			df_single_metric=pd.DataFrame({"K-set":["tmp_string"]})
			tmp_s=[]
			for i in df["Key-player"]:
				tmp_s.append(tuple(i))

			df_single_metric["K-set"].iloc[0]=tmp_s
			df_single_metric["Operation"]=str(args.operation)
			df_single_metric["Score"]=df[str(args.operation)].unique()[0]
			create_keyplayer_html(df_single_metric,g,outdir,filename)

	else:
		df=df.round(3) 
		print("")
		print(df)
		g.export_file(df, outdir)

		graph = ig.Graph(
			edges=g.get_edgelist(),
			directed=g.is_directed(),
			vertex_attrs={"name": g.vs["name"], "label": g.vs["label"]},
			edge_attrs={"weight": g.es["weight"] if "weight" in g.es.attributes() else None},
		)

		print(f"\nCreated report in: {g.name}.\n")
		if hasattr(args,"color"):
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

	# call main function
	main(args)
