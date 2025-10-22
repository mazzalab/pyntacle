import random
import pandas as pd
from .key_player import *

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
        
        temp_grafo = ig.Graph(directed=False, vertex_attrs={"name":grafo.vs["name"],"label": grafo.vs["label"]}, edges=grafo.get_edgelist(), edge_attrs={"weight": grafo.es["weight"]})
        
        # print("Node names:", node_names)
        # print("Edges before pruning")
        # for edge in temp_grafo.es:
        #     print("edge:", edge)
        #     print(f"Edge ({edge.source}, {edge.target}): Weight = {edge['weight']}")

        temp_grafo.delete_vertices(node_names)
        # print("\n\nEdges after pruning")
        # for edge in temp_grafo.es:
        #     print(f"Edge ({edge.source}, {edge.target}): Weight = {edge['weight']}")

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


def call_greedy(grafo,k_size,operation,distance_type="min",mdist=None):

    node_names = grafo.vs()["name"]
    node_indices =  grafo.iNodes
    df_tmp=pd.DataFrame({"name":node_names,"indices":node_indices})

    shuffled_df = df_tmp.sample(frac=1.0) ### shuffle keeping the name association with indices

    selected=shuffled_df.iloc[:k_size]
    sorted_df=selected.sort_values(by="indices")

    S_names = list(sorted_df["name"])
    S_indices = list(sorted_df["indices"])

    notS = set(node_names).difference(set(S_names))

    optimization_score=operation_selector(grafo,operation,S_names,distance_type,mdist)
    nodeSet_score_history = {tuple(S_names): optimization_score}
    
    optimal_set_found = False

    while not optimal_set_found:
        nodeSet_score = {}

        for si in S_names:
            temp_node_set = S_names.copy()
            temp_node_set.remove(si)

            for notsi in notS:
                temp_node_set.append(notsi)
                temp_node_set.sort()
                temp_node_set_tuple = tuple(temp_node_set)

                if temp_node_set_tuple in nodeSet_score_history:
                    nodeSet_score[temp_node_set_tuple] = nodeSet_score_history[temp_node_set_tuple]
                else:
                    temp_node_func_value = operation_selector(grafo,operation,temp_node_set,distance_type,mdist)
                    nodeSet_score[temp_node_set_tuple] = temp_node_func_value
                    nodeSet_score_history[temp_node_set_tuple] = temp_node_func_value

                temp_node_set.remove(notsi)

        maxNode = max(nodeSet_score, key=nodeSet_score.get)
        max_nodeScore = nodeSet_score[maxNode]

        if max_nodeScore > optimization_score:
            S_names = list(maxNode)
            notS = set(node_names).difference(set(S_names))
            optimization_score = max_nodeScore
        else:
            optimal_set_found = True

    return S_names, round(optimization_score,3)




def call_all_greedy(grafo,k_size,operation,distance_type="min",mdist=None,function=None):
    
    results=[]
    if function=="groupcentrality":
        for oper in ["degree","closeness","betweenness"]:#
            results.append(call_greedy(grafo,k_size,oper,distance_type,mdist))
    elif function=="keyplayer":
        for oper in ["F","dF","dR","mreach"]:
            results.append(call_greedy(grafo,k_size,oper,distance_type,mdist))
    else:
        raise KeyError(u"choose the correct function keyplayer | groupcentrality")

    return results




# def cython_greedy(grafo,k_size,operation,distance_type="min",mdist=None):

#     node_names = grafo.vs()["name"]
#     node_indices =  grafo.iNodes
#     df_tmp = pd.DataFrame({"name":node_names,"indices":node_indices})
#     df_tmp = selected.sort_values(by="indices")
#     shuffled_df = df_tmp.sample(frac=1.0) ### shuffle keeping the name association with indices
#     
#     set_k = shuffled_df.iloc[:k_size]
#     set_notK = shuffled_df.iloc[k_size:]

#     set_k = set_k.sort_values(by="indices")
#     set_notK = set_notK.sort_values(by="indices")

#     k_names = np.array(set_k["name"])
#     k_indices = np.array(set_k["indices"])
#     all_indices = np.array(df_tmp["indices"])

#     notk = set(node_names).difference(set(S_names))
#     adj = np.array(grafo.get_adjacency(attribute="weight").data, dtype=np.float)


#     print(f"K_indices: {k_indices}")
#     print(f"all_indices: {len(all_indices)}")
#     print(f"adj size: {len(adj)};\nadj: {adj[0][:20]}")


#     S_names, score = cython_kp(k_indices, all_indices, adj, operation, distance_type, mdist)

#     print(f"In greedy.py: {S_names}, {score}")

#     return S_names, score

#     pass