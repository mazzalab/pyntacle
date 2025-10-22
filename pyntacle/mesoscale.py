############### GTOM
from igraph import Graph
import numpy as np
import pandas as pd
import itertools
from colorama import Fore, Style
from collections import defaultdict as df
    
def gtom(graph, steps_m, verbose=False):
    """
    Calcola la Generalized Topological Overlap Measure per ciascun nodo in un grafo fino a un massimo di `m` passi,
    in linea con il metodo descritto nell'articolo 'Gene network interconnectedness and the generalized topological overlap measure'.
    
    :param graph: Oggetto di tipo Graphtacle (sottoclasse di igraph.Graph).
    :param m: Numero massimo di passi per il calcolo della GTOM.
    :return: DataFrame con GTOM per ciascun nodo.
    """
    # check if undirected
    if graph.directed:
        print("\nThe Generalized Topological Overlap Measure, is computed on the undirected graph.\n")
    
    # check diameter to limit steps_m
    diameter = graph.diameter(directed=False, unconn=True) # check impact on performance 

    if steps_m > diameter:
        print(f"\n[Warning] KSTEPS > graph diameter! -> Argument KSTEPS wil be cliped to match graph diameter.\n")
        steps_m = diameter

    A = np.array(graph.get_adjacency().data)
    
    if np.any(A[np.diag_indices_from(A)] == 0.):
        A[np.diag_indices_from(A)] = 0.
        print(Fore.YELLOW + Style.BRIGHT + "\n[Warning] The graph contains self-loops, which are not considered in the Generalized Topological Overlap Measures.\n" + Style.RESET_ALL)
    
    num_nodes = len(graph.iNodes)
    matrix_m = np.zeros((steps_m, num_nodes, num_nodes))
    
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
    
    # store the initial result for one step GTOM
    matrix_m[0, :, :] = compute_ti(cumulative)

    if verbose:
        print(f"GTOM matrix for step: {1}\n\n")
        print(f"{pd.DataFrame(matrix_m[0, :, :], index=graph.vs['label'], columns=graph.vs['label']).round(3)}\n")
    # compute GTOM for every step from 0 to m
    for m in range(1, steps_m): 
        
        temp = np.dot(temp, A)
        cumulative += temp
        matrix_m[m, :, :] = compute_ti(cumulative)

        if verbose:
            print(f"GTOM matrix for step: {m+1}\n\n {pd.DataFrame(matrix_m[m, :, :], index=graph.vs['label'], columns=graph.vs['label']).round(3)}\n")

    # Creazione del DataFrame per visualizzare i risultati
    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())

    df = pd.DataFrame(matrix_m[-1, :, :], index=node_labels, columns=node_labels)

    return df


###### TI Matrix

def ti(graph, k, weighted=False, weight_attr="weight", threshold=0.0, verbose=False):
    """
    Calcola la Topological Importance (TI) per ciascun nodo in un grafo fino a un massimo di `n` passi,
    in linea con il metodo descritto nel manuale CoSBiLab Graph.
    
    :param graph: Oggetto di tipo Graphtacle (sottoclasse di igraph.Graph).
    :param k: Numero massimo di passi per il calcolo della TI.
    :param nodes: Nodi per cui calcolare la TI (opzionale). Se None, calcola per tutti i nodi.
    :param weighted: Booleano, True se considerare un grafo pesato.
    :param weight_attr: Nome dell'attributo del peso (richiesto se weighted=True).
    :param verbose: Booleano, True stampa gli effetti tra i nodi per path di lunghezza k.
    :return: DataFrame con TI per ciascun nodo.
    """
    
    # Creazione di una matrice per memorizzare i path_effect tra i nodi
    n_nodes = len(graph.iNodes)
    matrix_effect = np.zeros((k, n_nodes, n_nodes)) 
    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())
    degree = graph.degree(loops=False)

    # i path vengono calcolati con la matrice di adiacenza 
    A = np.array(graph.get_adjacency().data)
    
    if np.any(A[np.diag_indices_from(A)] == 0.):
        A[np.diag_indices_from(A)] = 0.
        if weighted:
            print(Fore.YELLOW + Style.BRIGHT + "\n[Warning] The graph contains self-loops, which are not considered in the Topological Importance calculation.\n" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + Style.BRIGHT + "\n[Warning] The graph contains self-loops, which are not considered in the Weighted Topological Importance calculation.\n" + Style.RESET_ALL)

    # funzione per calcolare l'effetto di tutti i nodi 
    def Ksteps_effect(edge_effect, weighted):
        
        matrix_effect[0, :, :] = edge_effect

        if verbose:
            print(f"Topological Importance effect for step {1}:\n\n")
            print(f"{pd.DataFrame(edge_effect, index=node_labels, columns=node_labels).round(3)}\n")

        for step in range(2, k+1):

            # nodi raggiunti con step di lunghezza 'step'
            matrix_effect[step - 1, :, :] = np.linalg.matrix_power(edge_effect, step)
            
            if verbose:
                print(f"Topological Importance effect for step {step}:\n\n")
                print(f"{pd.DataFrame(matrix_effect[step - 1, :, :], index=node_labels, columns=node_labels).round(3)}\n")

        # somma gli effetti di un nodo sul network 
        sigma_matrix = np.sum(matrix_effect, axis=2)

        # the cell[i][j] will contain the average effect of node i on node j over all the paths
        data = np.sum(matrix_effect, 0)/ k
        ti = np.sum(sigma_matrix, axis=0) / k
            
        # else:
            
        #     # the cell[i][j] will contain the effect of node i on node j for a path of len k
        #     data = matrix_effect[-1]
        #     ti = sigma_matrix[-1]


        df = pd.DataFrame(data, index=node_labels, columns=node_labels)


        if weighted:
            df['WI_' + str(k)] = ti
        else:
            df['TI_' + str(k)] = ti

        # compute topological overlap
        if threshold > 0.:
      
            # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            # print(f"matrix_effect:\n{matrix_effect[-1, :, :]}\n")
            threshold_nodes = (matrix_effect[-1, :, :] > threshold).astype(int)
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
        weighted_effect = A_w / graph.strength(graph.iNodes, weights=weight_attr)
        
        df = Ksteps_effect(weighted_effect, weighted=True)

    else:
        degree_arr = np.array(degree, dtype=float)
        result = np.divide(1.0, degree_arr, out=np.zeros_like(degree_arr), where=degree_arr != 0)
        direct_effect = A * result
        df = Ksteps_effect(direct_effect, weighted=False)    

    return df

###### TI RECURSIVE

def ti_recursive(graph, k, nodes=None, weighted=False, weight_attr="weight", threshold=None, verbose=False):
    """
    Calcola la Topological Importance (TI) per ciascun nodo in un grafo fino a un massimo di `n` passi,
    in linea con il metodo descritto nel manuale CoSBiLab Graph.
    
    :param graph: Oggetto di tipo Graphtacle (sottoclasse di igraph.Graph).
    :param k: Numero massimo di passi per il calcolo della TI.
    :param nodes: Nodi per cui calcolare la TI (opzionale). Se None, calcola per tutti i nodi.
    :param weighted: Booleano, True se considerare un grafo pesato.
    :param weight_attr: Nome dell'attributo del peso (richiesto se weighted=True).
    :param upto_k: Booleano, True considera la media degli effetti generati dal nodo i su path da 1 a n steps, False considera solo path di lunghezza n.
    :param verbose: Booleano, True stampa gli effetti tra i nodi per path di lunghezza k.
    :return: DataFrame con TI per ciascun nodo.
    """
    
    if nodes is None:
        nodes = [node.index for node in graph.vs]
    elif isinstance(nodes, int):
        nodes = [nodes]
    
    # Creazione di una matrice per memorizzare i path_effect tra i nodi
    n_nodes = len(nodes)
    matrix_effect = np.zeros((k+1, n_nodes, n_nodes)) # la prima dim serve per identificare la LEN massima del path (e serve come supporto nella ricorsione)
    degree = graph.degree()

    def compute_paths_and_effect(graph, start_node, k):
        """
        Trova tutti i percorsi di lunghezza esattamente `n` passi a partire da `start_node`.

        :param graph: Graph su cui calcolare il percorso.
        :param start_node: Nodo iniziale.
        :param k: Numero di passi desiderati.
        :return: Lista di percorsi (liste di nodi).
        """
        all_paths = []

        # Funzione ricorsiva DFS per esplorare il grafo
        def dfs(current_path, path_effect = 1 , path_effect_list = [1]):

            step = len(current_path)

            matrix_effect[step - 1, current_path[0], current_path[-1]] += path_effect  # store the partial result 

            # Se il cammino ha raggiunto esattamente n passi, aggiungilo alla lista
            if len(current_path) - 1 == k:  # n passi significa n+1 nodi
                all_paths.append(current_path)          #OBSOLETI

                return

            # Ottieni i vicini dell'ultimo nodo
            neighbors = graph.neighbors(current_path[-1])  # Usa il metodo `neighbors` del grafo
            
            # Esplora i vicini, permettendo ritorni indietro
            for neighbor in neighbors:
                
                # Aggiungi il vicino al cammino e continua 
                if weighted:

                    direct_effect = graph.es[graph.get_eid(current_path[-1], neighbor)][weight_attr] / graph.strength(neighbor, weights=weight_attr)
                    
                    dfs(current_path + [neighbor],              # update path
                        path_effect * direct_effect,            # update path effect
                        path_effect_list + [direct_effect])     # update direct effect list
                else:

                    direct_effect = 1/degree[neighbor]

                    dfs(current_path + [neighbor],              # update path
                        path_effect * direct_effect,            # update path effect
                        path_effect_list + [direct_effect])     # update direct effect list

        # Avvia la DFS partendo dal nodo di partenza
        dfs([start_node])
        return all_paths

    # Itera su ciascun nodo specificato
    for node in nodes:

        all_paths = compute_paths_and_effect(graph,node, k) 
        
    matrix_effect[0,:,:] = 0
    
    if verbose:
        for step in range(1,k+1):
            print(f"Topological Importance effect for step {step}:\n\n{matrix_effect[step]}\n")

    # Creazione del DataFrame per visualizzare i risultati
    node_labels = graph.vs["label"] if "label" in graph.vs.attribute_names() else range(graph.vcount())

    if upto_k:
        # Compute Ti_n, cioè la somma dei sigma_l,i (la somma degli effetti di un nodo i su gli altri per un path di lunghezza l).
        # Il df finale sarà  sigma_l,i e Ti_n
        print("Sum value (sigma_n,i) for the paths up to n for each node:\n")

        sigma_matrix = np.sum(matrix_effect, axis=2)

        df = pd.DataFrame(sigma_matrix.T, index=[node_labels[node] for node in nodes], columns=[steps for steps in range(k+1)])
        
        Ti_n = np.sum(sigma_matrix, axis=0) / k
        if weighted:
            df['WI_' + str(k)] = Ti_n
        else:
            df['TI_' + str(k)] = Ti_n
    
    else:

        df = pd.DataFrame(matrix_effect[-1,:,:], index=[node_labels[node] for node in nodes], columns=[node_labels[node] for node in nodes])
        # Aggiunta della colonna "SUM" che calcola la somma di ciascuna riga
        df['TI_' + str(k)] = df.sum(axis=1) / k
        # Aggiungi una nuova colonna in posizione 0
        # df.insert(0, 'Nodes', df.index)

    return df


def filter_lists(input_lists, k):
    # Filter based on length > k
    
    filtered_by_length = [lst for lst in input_lists if len(lst) <= k+1 and len(lst) != 1]

    # Filter out lists that are contained in another list
    final_filtered = filtered_by_length.copy()
    for i, lst_i in enumerate(filtered_by_length):
        for j, lst_j in enumerate(filtered_by_length):
            if i != j and is_subsequence(lst_i, lst_j):
                if lst_i in final_filtered:
                    final_filtered.remove(lst_i)
                break

    return filtered_by_length

def is_subsequence(sub, main):
    """Check if 'sub' is a subsequence of 'main'."""
    iter_main = iter(main)
    return all(any(elem == main_elem for main_elem in iter_main) for elem in sub)