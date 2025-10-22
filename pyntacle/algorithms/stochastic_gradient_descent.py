import random
import pandas as pd
from .key_player import *
import time
import datetime


def count_time(t):
	if t=="start":
		start_time = time.time()
		# Get the current date and time
		current_datetime = datetime.datetime.now()
		# Format the datetime object as HH:MM:SS
		formatted_time = current_datetime.strftime("%H:%M:%S")
		# Print the formatted time
		print("\nStarting time (HH:MM:SS):", formatted_time)
		return start_time
	elif t=="end":
		# Get the current date and time
		current_datetime = datetime.datetime.now()
		# Format the datetime object as HH:MM:SS
		formatted_time = current_datetime.strftime("%H:%M:%S")
		# Print the formatted time
		print("End time (HH:MM:SS):", formatted_time)
		return formatted_time
	else: print("Internal Error")

def operation_selector(grafo,operation,node_names,distance_type="min",mdist=None):
	if operation=="degree":		
		result=grafo.group_degree(node_names)
	elif operation=="closeness":
		result=grafo.group_closeness(np_paths=None,nodes=node_names, distance_type=distance_type)
	elif operation=="betweenness":
		result=grafo.group_betweenness(np_counts=None,nodes=node_names)
	elif operation=="F":
		temp_grafo = ig.Graph(directed=False,vertex_attrs={"name":grafo.vs["name"],"label": grafo.vs["label"]},edges=grafo.get_edgelist())
		temp_grafo.delete_vertices(node_names)

		if temp_grafo.ecount == 0:
			result=1
		else:
			result=fragmentation(temp_grafo)
	elif operation=="dF":
		temp_grafo = ig.Graph(directed=False,vertex_attrs={"name":grafo.vs["name"],"label": grafo.vs["label"]},edges=grafo.get_edgelist())
		temp_grafo.delete_vertices(node_names)

		if temp_grafo.ecount == 0:
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



def call_stochastic_gradient_descent(grafo,k_size,operation,distance_type="min",mdist=None,probability=0,tolerance=0.01,maxsec=120):

	start_time=count_time("start")

	node_names = grafo.vs()["name"]
	node_indices =  grafo.iNodes
	df_tmp=pd.DataFrame({"name":node_names,"indices":node_indices})

	shuffled_df = df_tmp.sample(frac=1.0) ### shuffle keeping the name association with indices

	selected=shuffled_df.iloc[:k_size]
	sorted_df=selected.sort_values(by="indices")

	S_names = list(sorted_df["name"])
	S_indices = list(sorted_df["indices"])

	notS = list(set(node_names).difference(set(S_names)))

    # Initialize the optimization loop

	optimization_score=operation_selector(grafo,operation,S_names,distance_type,mdist)
	nodeSet_score_history = {tuple(S_names): optimization_score}
	nodeSet_score = {tuple(S_names): optimization_score}
	optimal_set_found = False
	
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
			curr_score = operation_selector(grafo,operation,temp_node_set,distance_type,mdist)
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
			notS = list(set(node_names).difference(set(S_names)))
			nodeSet_score.clear()
			nodeSet_score[temp_node_set_tuple] = curr_score
			optimization_score = curr_score
		elif curr_score == optimization_score:
			nodeSet_score[temp_node_set_tuple] = curr_score
		else:
			continue

	S_names=list(nodeSet_score.keys())
	count_time("end")

	return S_names, round(optimization_score,3)



def call_all_sgd(grafo,k_size,operation,distance_type="min",mdist=None,probability=0,tolerance=0.01,maxsec=120,function=None):
    
    results=[]
    if function=="groupcentrality":
        for oper in ["degree","closeness","betweenness"]:#
            results.append(call_stochastic_gradient_descent(grafo,k_size,oper,distance_type,mdist,probability,tolerance,maxsec))
    elif function=="keyplayer":
        for oper in ["F","dF","dR","mreach"]:
            results.append(call_stochastic_gradient_descent(grafo,k_size,oper,distance_type,mdist,probability,tolerance,maxsec))
    else:
        raise KeyError(u"choose the correct function keyplayer | groupcentrality")

    return results