from .cython_metrics import cython_greedy, cython_info, cython_bruteforce

import numpy as np
from time import time

import math
import igraph as ig
import pandas as pd

def select_operation(oper):
    if oper == "F":
        return 0
    elif oper == "dF":
        return 1
    elif oper == "dR":
        return 2
    elif oper == "mreach":
        return 3
    elif oper == "degree":
        return 4
    elif oper == "betweenness":
        return 5
    elif oper == "closeness":
        return 6
    else:
        raise KeyError(u"Choose the correct operation")

def select_distance_type(distance_type):
    if distance_type == "mean":
        return 0
    elif distance_type == "max":
        return 1
    elif distance_type == "min":
        return 2
    else:
        raise KeyError(u"Choose the correct distance type")

def cython_wrapper_greedy(graph, k_size, oper, distance_type='min', mdist=1, n_threads=1):

    node_names = graph.vs()["name"]
    node_indices =  graph.iNodes
    df_tmp = pd.DataFrame({"name":node_names, "indices":node_indices})

    shuffled_df = df_tmp.sample(frac=1.0) ### shuffle keeping the name association with indices

    selected=shuffled_df.iloc[:k_size]
    sorted_df=selected.sort_values(by="indices")

    K_indices = np.array(sorted_df["indices"]).astype(np.int32)

    notK_indices = set(node_indices).difference(set(sorted_df["indices"]))
    notK_indices = np.array(list(notK_indices)).astype(np.int32)

    adj = np.array(graph.get_adjacency( attribute="weight", default=0).data).astype(float)

    oper_idx = select_operation(oper)
    dist_idx = select_distance_type(distance_type)

    # print("Adjacency matrix:")
    # print(adj)

    found_k, found_score = cython_greedy(K_indices, notK_indices, adj, operation=oper_idx, mdist=mdist, dist_type=dist_idx, num_threads=n_threads)

    # convert indices back to names:
    found_k = np.asarray(found_k)
    found_k = [node_names[i] for i in found_k]

    return found_k, found_score

def cython_wrapper_info(graph, nodes, oper, distance_type, mdist, n_threads):

    node_names = graph.vs()["name"]
    node_indices =  graph.iNodes
    df_tmp = pd.DataFrame({"name":node_names, "indices":node_indices}).sort_values(by="indices")

    K_indices = df_tmp[df_tmp["name"].isin(nodes)]['indices'].to_numpy().astype(np.int32)

    notK_indices = df_tmp[~df_tmp["name"].isin(nodes)]['indices'].to_numpy().astype(np.int32)

    adj = np.array(graph.get_adjacency( attribute="weight", default=0).data).astype(float)

    oper_idx = select_operation(oper)
    dist_idx = select_distance_type(distance_type)

    found_score = cython_info(K_indices, notK_indices, adj, oper_idx, mdist, dist_idx, n_threads)

    return found_score

def cython_wrapper_bruteforce(graph, k_size, oper, distance_type='min', mdist=1, n_threads=1):

    node_names = graph.vs()["name"]

    K_indices = np.arange(k_size).astype(np.int32) # its just a placeholder, we will select the indices later

    adj = np.array(graph.get_adjacency( attribute="weight", default=0).data).astype(float)

    oper_idx = select_operation(oper)
    dist_idx = select_distance_type(distance_type)

    comb_num = math.comb(adj.shape[0], k_size)

    found_k, found_score = cython_bruteforce(adj, K_indices, operation=oper_idx, mdist=mdist, dist_type=dist_idx, comb_num=comb_num, num_threads=n_threads)

    # convert indices back to names:
    found_k = np.asarray(found_k)
    found_k = [node_names[i] for i in found_k]

    return found_k, found_score

