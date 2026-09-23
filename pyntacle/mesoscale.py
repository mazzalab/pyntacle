############### GTOM
from igraph import Graph
import numpy as np
import pandas as pd
import itertools
from colorama import Fore, Style
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
    # check if undirected
    if graph.is_directed():
        print("\nThe Generalized Topological Overlap Measure, is computed on the undirected graph.\n")
    
    # check diameter to limit steps_m
    diameter = graph.diameter(directed=False, unconn=True) # check impact on performance 

    if steps_m > diameter:
        print(f"\n[Warning] KSTEPS > graph diameter! -> Argument KSTEPS wil be cliped to match graph diameter.\n")
        steps_m = diameter

    A = np.array(graph.get_adjacency().data)

    # Treat a directed graph as undirected, as the message above promises.
    # get_adjacency() returns the *asymmetric* directed adjacency; GTOM is
    # defined on the undirected graph, so symmetrise (binary OR of the two
    # directions) instead of only claiming to. Without this the numbers were
    # computed on the directed adjacency and did not match the undirected graph.
    if graph.is_directed():
        A = np.maximum(A, A.T)

    # A self-loop shows up as a non-zero diagonal entry; only then is there
    # anything to drop (and to warn about). The guard used to test `== 0`,
    # which is true for every node without a loop, so the warning fired on
    # essentially every graph.
    if np.any(A[np.diag_indices_from(A)] != 0.):
        A[np.diag_indices_from(A)] = 0.
        print(Fore.YELLOW + Style.BRIGHT + "\n[Warning] The graph contains self-loops, which are not considered in the Generalized Topological Overlap Measures.\n" + Style.RESET_ALL)

    num_nodes = len(graph.iNodes)
    
    # la funzione calcola il numeratore e denominatore in forma matriciale
    def compute_ti(matrix_step):

        # remove elements of the diagonal from the adj
        np.fill_diagonal(matrix_step, 0)

        # clip all the step values to 1
        row, col = np.nonzero(matrix_step)
        matrix_step[row, col] = 1

        # compute the numerator
        numerator = np.dot(matrix_step, matrix_step.T) + A 
        
        # find the minimum cardinality beteween the two sets of neighbours (use only the nodes that have links)
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
        
    # create the temp copies of the adj matrix
    temp = A.copy()
    cumulative = temp.copy().astype(float)

    # Only the final step's matrix is returned; intermediate steps are printed
    # when verbose. Keep just the last result instead of an (steps_m, n, n)
    # cube -- that cube was steps_m times the memory the algorithm actually
    # needs (3.2 GB per step already at n=20k).
    last = compute_ti(cumulative)

    if verbose:
        print(f"GTOM matrix for step: {1}\n\n")
        print(f"{pd.DataFrame(last, index=graph.vs['label'], columns=graph.vs['label']).round(3)}\n")
    # compute GTOM for every step from 0 to m
    for m in range(1, steps_m):

        temp = np.dot(temp, A)
        cumulative += temp
        last = compute_ti(cumulative)

        if verbose:
            print(f"GTOM matrix for step: {m+1}\n\n {pd.DataFrame(last, index=graph.vs['label'], columns=graph.vs['label']).round(3)}\n")

    # Creazione del DataFrame per visualizzare i risultati
    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())

    df = pd.DataFrame(last, index=node_labels, columns=node_labels)

    return df


###### TI Matrix

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
    :param verbose: Booleano, True stampa gli effetti tra i nodi per path di lunghezza k.
    :return: DataFrame con TI per ciascun nodo.
    """
    
    # Creazione di una matrice per memorizzare i path_effect tra i nodi
    n_nodes = len(graph.iNodes)
    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())
    degree = graph.degree(loops=False)

    # i path vengono calcolati con la matrice di adiacenza
    A = np.array(graph.get_adjacency().data)

    # Treat a directed graph as undirected, consistently with GTOM. TI used to
    # run silently on the asymmetric directed adjacency; symmetrise it and say
    # so, so the number matches the same edges built undirected.
    if graph.is_directed():
        A = np.maximum(A, A.T)
        print(Fore.YELLOW + Style.BRIGHT + "\nTopological Importance is computed on the undirected graph.\n" + Style.RESET_ALL)

    # A self-loop is a non-zero diagonal entry; only then is there anything to
    # drop (and to warn about). The guard used to test `== 0`, true for every
    # node without a loop, so the warning fired on nearly every graph -- and
    # the two branches had their messages swapped.
    if np.any(A[np.diag_indices_from(A)] != 0.):
        A[np.diag_indices_from(A)] = 0.
        if weighted:
            print(Fore.YELLOW + Style.BRIGHT + "\n[Warning] The graph contains self-loops, which are not considered in the Weighted Topological Importance calculation.\n" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + Style.BRIGHT + "\n[Warning] The graph contains self-loops, which are not considered in the Topological Importance calculation.\n" + Style.RESET_ALL)

    # funzione per calcolare l'effetto di tutti i nodi
    def Ksteps_effect(edge_effect, weighted):

        # The old code stored every step's n x n effect matrix in a
        # (k, n, n) cube only to collapse it into two sums. Accumulate those
        # sums on the fly instead: `acc` is the running sum of the step
        # matrices and `ti` their running row-sums; only the last step's
        # matrix (`last`) is kept, for the topological-overlap threshold.
        # Memory drops from k * n^2 to ~2 * n^2, bit-for-bit identical output.
        step_effect = np.asarray(edge_effect, dtype=float)
        acc = step_effect.copy()
        ti = step_effect.sum(axis=1)
        last = step_effect

        if verbose:
            print(f"Topological Importance effect for step {1}:\n\n")
            print(f"{pd.DataFrame(step_effect, index=node_labels, columns=node_labels).round(3)}\n")

        for step in range(2, k+1):

            # nodi raggiunti con step di lunghezza 'step': D^step = D^(step-1) . D,
            # one matmul per step instead of re-squaring from scratch each time
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
            # print(f"threshold_nodes:\n{threshold_nodes}\n")
            threshold_nodes = np.dot(threshold_nodes, threshold_nodes.T)
            # print(f"threshold_nodes:\n{threshold_nodes}\n")
            np.fill_diagonal(threshold_nodes, 0)
            threshold_nodes = np.sum(threshold_nodes, axis=1)
            # print(f"threshold_nodes:\n{threshold_nodes}\n")
            max_to = np.max(threshold_nodes)
            
            if max_to > 0:
                to = threshold_nodes / max_to
            else:
                to = threshold_nodes
            # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

            df['TO_' + str(k)] = to

        return df

    # compute weighted or unweighted graph
    if weighted:
        A_w = np.array(graph.get_adjacency(attribute=weight_attr).data)
        # same undirected treatment for the weighted adjacency; the stronger of
        # two reciprocal directions is kept
        if graph.is_directed():
            A_w = np.maximum(A_w, A_w.T)
        weighted_effect = A_w / graph.strength(graph.iNodes, weights=weight_attr)
        
        df = Ksteps_effect(weighted_effect, weighted=True)

    else:
        degree_arr = np.array(degree, dtype=float)
        result = np.divide(1.0, degree_arr, out=np.zeros_like(degree_arr), where=degree_arr != 0)
        direct_effect = A * result
        df = Ksteps_effect(direct_effect, weighted=False)    

    return df

