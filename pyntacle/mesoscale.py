from igraph import Graph
import numpy as np
import pandas as pd
import itertools
from colorama import Fore, Style
from pyntacle.utility import warn
from collections import defaultdict as df
    
def gtom(graph, steps_m, verbose=False):
    """Compute the Generalized Topological Overlap Measure (GTOM) matrix.

    GTOM extends classical Topological Overlap Measure (TOM) to m-step
    neighborhoods, yielding a pairwise node-similarity matrix in [0, 1].
    Yip & Horvath (2007) formulation.

    Args:
        graph: An igraph Graph (directed graphs are treated as undirected).
        steps_m (int): Maximum number of neighborhood steps. Clipped to
            graph diameter if larger.
        verbose (bool): If True, print partial results at each step.

    Returns:
        pandas.DataFrame: n x n matrix of GTOM scores. Entry [i, j] is the
            topological overlap between nodes i and j at step steps_m.
    """
    if graph.is_directed():
        warn("the generalized topological overlap is computed on the undirected graph")
    
    # steps beyond the diameter add nothing
    diameter = graph.diameter(directed=False, unconn=True)

    if steps_m > diameter:
        warn(f"-k {steps_m} exceeds the network diameter: {diameter} steps are used")
        steps_m = diameter

    A = np.array(graph.get_adjacency().data)

    # GTOM is defined on the undirected graph: symmetrise a directed adjacency
    if graph.is_directed():
        A = np.maximum(A, A.T)

    # self-loops are non-zero diagonal entries
    if np.any(A[np.diag_indices_from(A)] != 0.):
        A[np.diag_indices_from(A)] = 0.
        warn("self-loops are left out of the generalized topological overlap")

    num_nodes = len(graph.iNodes)
    
    # numerator and denominator in matrix form
    def compute_ti(matrix_step):

        # remove elements of the diagonal from the adj
        np.fill_diagonal(matrix_step, 0)

        # clip all the step values to 1
        row, col = np.nonzero(matrix_step)
        matrix_step[row, col] = 1

        # compute the numerator
        numerator = np.dot(matrix_step, matrix_step.T) + A 
        
        # find the minimum cardinality between the two sets of neighbours (use only the nodes that have links)
        row, col = np.nonzero(numerator)
        neigh_card = np.sum(matrix_step, axis=1)
        neigh_card = np.repeat(neigh_card.reshape(-1,1), num_nodes, axis=1)

        # compute the denominator
        denominator = np.minimum(neigh_card, neigh_card.T)
        denominator += np.ones((len(graph.iNodes), len(graph.iNodes))) - A

        gtom = numerator/denominator

        # the metric is equal to 1 for i == j
        np.fill_diagonal(gtom, 1)

        return gtom
        
    temp = A.copy()
    cumulative = temp.copy().astype(float)

    # only the last step's matrix is kept; intermediate ones are printed when verbose
    last = compute_ti(cumulative)

    if verbose:
        print(f"GTOM matrix for step: {1}\n\n")
        print(f"{pd.DataFrame(last, index=graph.vs['label'], columns=graph.vs['label']).round(3)}\n")
    # GTOM for steps 2..m
    for m in range(1, steps_m):

        temp = np.dot(temp, A)
        cumulative += temp
        last = compute_ti(cumulative)

        if verbose:
            print(f"GTOM matrix for step: {m+1}\n\n {pd.DataFrame(last, index=graph.vs['label'], columns=graph.vs['label']).round(3)}\n")

    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())

    df = pd.DataFrame(last, index=node_labels, columns=node_labels)

    return df


# ---- topological importance ----

def ti(graph, k, weighted=False, weight_attr="weight", threshold=0.0, verbose=False):
    """Compute Topological Importance (TI) for all nodes up to k propagation steps.

    TI measures a node's influence through k-step structural propagation.
    It is computed as the row sum of the averaged k-step effect matrix E^(k).

    Args:
        graph: An igraph Graph object.
        k (int): Maximum propagation steps. Higher k captures longer-range effects.
        weighted (bool): If True, use edge weights for the effect matrix.
        weight_attr (str): Name of the edge weight attribute (used when weighted=True).
        threshold (float): If > 0, also compute Topological Overlap (TO) by
            thresholding the k-step effect matrix at this value.
        verbose (bool): If True, print intermediate matrices at each step.

    Returns:
        pandas.DataFrame: the averaged k-step effect matrix with a TI_k (or
            WI_k) column and, with a threshold, a TO_k column.
    """
    
    n_nodes = len(graph.iNodes)
    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())
    degree = graph.degree(loops=False)

    A = np.array(graph.get_adjacency().data)

    # as in GTOM, a directed graph is analysed as undirected
    if graph.is_directed():
        A = np.maximum(A, A.T)
        warn("topological importance is computed on the undirected graph")

    # self-loops are non-zero diagonal entries
    if np.any(A[np.diag_indices_from(A)] != 0.):
        A[np.diag_indices_from(A)] = 0.
        if weighted:
            warn("self-loops are left out of the weighted topological importance")
        else:
            warn("self-loops are left out of the topological importance")

    # effect of every node on every other, averaged over steps 1..k
    def Ksteps_effect(edge_effect, weighted):

        # `acc` is the running sum of the step matrices and `ti` their running
        # row sums; only the last step's matrix is kept, for the TO threshold
        step_effect = np.asarray(edge_effect, dtype=float)
        acc = step_effect.copy()
        ti = step_effect.sum(axis=1)
        last = step_effect

        if verbose:
            print(f"Topological Importance effect for step {1}:\n\n")
            print(f"{pd.DataFrame(step_effect, index=node_labels, columns=node_labels).round(3)}\n")

        for step in range(2, k+1):

            # D^step = D^(step-1) . D
            last = last @ edge_effect
            acc += last
            ti = ti + last.sum(axis=1)

            if verbose:
                print(f"Topological Importance effect for step {step}:\n\n")
                print(f"{pd.DataFrame(last, index=node_labels, columns=node_labels).round(3)}\n")

        # the cell[i][j] will contain the average effect of node i on node j over all the paths
        data = acc / k
        ti = ti / k

        df = pd.DataFrame(data, index=node_labels, columns=node_labels)


        if weighted:
            df['WI_' + str(k)] = ti
        else:
            df['TI_' + str(k)] = ti

        # compute topological overlap
        if threshold > 0.:

            threshold_nodes = (last > threshold).astype(int)
            threshold_nodes = np.dot(threshold_nodes, threshold_nodes.T)
            np.fill_diagonal(threshold_nodes, 0)
            threshold_nodes = np.sum(threshold_nodes, axis=1)
            max_to = np.max(threshold_nodes)
            
            if max_to > 0:
                to = threshold_nodes / max_to
            else:
                to = threshold_nodes

            df['TO_' + str(k)] = to

        return df

    # compute weighted or unweighted graph
    if weighted:
        A_w = np.array(graph.get_adjacency(attribute=weight_attr).data)
        # same undirected treatment for the weighted adjacency; the stronger of
        # two reciprocal directions is kept
        if graph.is_directed():
            A_w = np.maximum(A_w, A_w.T)
        strength = np.array(graph.strength(graph.iNodes, weights=weight_attr), dtype=float)
        # an isolated node spreads nothing; 0/0 would make every product NaN
        weighted_effect = np.divide(A_w, strength, out=np.zeros_like(A_w, dtype=float), where=strength != 0)
        
        df = Ksteps_effect(weighted_effect, weighted=True)

    else:
        degree_arr = np.array(degree, dtype=float)
        result = np.divide(1.0, degree_arr, out=np.zeros_like(degree_arr), where=degree_arr != 0)
        direct_effect = A * result
        df = Ksteps_effect(direct_effect, weighted=False)    

    return df

