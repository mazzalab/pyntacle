import random
import pandas as pd
from .key_player import *
import time

def operation_selector(grafo,operation,node_names,distance_type="min",mdist=None):
	if operation=="degree":		
		result=grafo.group_degree(node_names)
	elif operation=="closeness":
		result=grafo.group_closeness(np_paths=None,nodes=node_names, distance_type=distance_type)
	elif operation=="betweenness":
		result=grafo.group_betweenness(node_names)
	elif operation=="F":
		temp_grafo = prune_graph(grafo, node_names)

		if temp_grafo.ecount() == 0:
			result=1
		else:
			result=fragmentation(temp_grafo)
	elif operation=="dF":
		temp_grafo = prune_graph(grafo, node_names)

		if temp_grafo.ecount() == 0:
			result=1
		else:
			result=distance_fragmentation(temp_grafo)
	elif operation=="dR":
		node_indices = [grafo.vs.find(name=name).index for name in node_names]            
		result=distance_weighted_reach(grafo, nodes=node_indices)
	elif operation=="mreach":
		node_indices = [grafo.vs.find(name=name).index for name in node_names] 
		result=reachability(grafo, mdist, nodes=node_indices)
	else:
		raise KeyError(u"choose the correct function")

	return result



def call_stochastic_gradient_descent(grafo,k_size,operation,distance_type="min",mdist=None,probability=0,tolerance=0.01,maxsec=120,seed=None,scorer=None):
	"""Gradient descent over node sets of size k_size.

	`scorer(node_names, operation)` scores a set; without it the pure-Python
	metrics are used.
	"""
	if scorer is None:
		scorer = lambda names, oper: operation_selector(grafo, oper, names, distance_type, mdist)

	start_time = time.time()

	if seed is not None:
		random.seed(seed)

	node_names = grafo.vs()["name"]
	node_indices =  grafo.iNodes
	df_tmp=pd.DataFrame({"name":node_names,"indices":node_indices})

	# shuffle keeping names aligned with indices
	shuffled_df = df_tmp.sample(frac=1.0, random_state=seed)

	selected=shuffled_df.iloc[:k_size]
	sorted_df=selected.sort_values(by="indices")

	S_names = list(sorted_df["name"])
	S_indices = list(sorted_df["indices"])

	# in node order, not set order: the walk then depends on the seed alone
	notS = [x for x in node_names if x not in S_names]

	# optimization loop

	optimization_score=scorer(S_names,operation)
	nodeSet_score_history = {tuple(S_names): optimization_score}
	nodeSet_score = {tuple(S_names): optimization_score}
	optimal_set_found = False
	# swaps of the current set tried without a move; all of them tried means a local optimum
	tried = set()
	n_swaps = len(S_names) * len(notS)

	while not optimal_set_found:
		si=random.choice(S_names)
		notsi=random.choice(notS)
		
		temp_node_set = S_names.copy()
		temp_node_set.remove(si)
		temp_node_set.append(notsi)
		temp_node_set.sort()
		temp_node_set_tuple = tuple(temp_node_set)


		# Evaluate the score of the current set S, if not already computed
		if temp_node_set_tuple in nodeSet_score_history:
			curr_score = nodeSet_score_history[temp_node_set_tuple]
		else:
			curr_score = scorer(temp_node_set,operation)
			nodeSet_score_history[temp_node_set_tuple] = curr_score

		if time.time() - start_time >= maxsec:
			optimal_set_found = True
		elif curr_score > optimization_score and (curr_score - optimization_score) <= tolerance:
			optimal_set_found = True
			nodeSet_score.clear()
			nodeSet_score[temp_node_set_tuple] = curr_score
			optimization_score = curr_score
		elif curr_score > optimization_score or ((curr_score < optimization_score and random.uniform(0, 1) < probability)):
			S_names = temp_node_set
			notS = [x for x in node_names if x not in S_names]
			nodeSet_score.clear()
			nodeSet_score[temp_node_set_tuple] = curr_score
			optimization_score = curr_score
			tried.clear()
		else:
			if curr_score == optimization_score:
				nodeSet_score[temp_node_set_tuple] = curr_score
			tried.add(temp_node_set_tuple)
			if len(tried) >= n_swaps:
				optimal_set_found = True

	# a flat list of node names, as call_greedy returns
	best = max(nodeSet_score, key=nodeSet_score.get)
	S_names = list(best)

	return S_names, optimization_score



def call_all_sgd(grafo,k_size,operation,distance_type="min",mdist=None,probability=0,tolerance=0.01,maxsec=120,function=None,seed=None,scorer=None):

    results=[]
    if function=="groupcentrality":
        for oper in ["degree","closeness","betweenness"]:
            results.append(call_stochastic_gradient_descent(grafo,k_size,oper,distance_type,mdist,probability,tolerance,maxsec,seed,scorer))
    elif function=="keyplayer":
        for oper in ["F","dF","dR","mreach"]:
            results.append(call_stochastic_gradient_descent(grafo,k_size,oper,distance_type,mdist,probability,tolerance,maxsec,seed,scorer))
    else:
        raise KeyError(u"choose the correct function keyplayer | groupcentrality")

    return results