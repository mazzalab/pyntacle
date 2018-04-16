__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software; you can use and redistribute it under
  the terms of the BY-NC-ND license as published by
  Creative Commons; either version 4 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  License for more details.

  You should have received a copy of the license along with this
  work. If not, see http://creativecommons.org/licenses/by-nc-nd/4.0/.
  """

"""
This Module covers the Greedy optimization algorithms for optimal kp-set calculation using Key-Players metrics developed by Borgatti
"""
from config import *
import random
from functools import partial
from algorithms.keyplayer import KeyPlayer as kp
from algorithms.local_topology import LocalTopology as Lt
from tools.misc.graph_routines import *
from exceptions.wrong_argument_error import WrongArgumentError
from tools.misc.enums import KPPOSchoices, KPNEGchoices, Cmode
from tools.misc.kpsearch_utils import greedy_search_initializer
from tools.graph_utils import GraphUtils as gu

class GreedyOptimization:
    """
    Greedy optimization algorithms for optimal kp-set calculation
    """
    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def fragmentation(graph, kpp_size, kpp_type, seed=None, max_distances=None, implementation=Cmode.igraph) -> (list, float):
        """
        It iteratively searches for a kpp-set of a predefined vertex set size, removes it and measures the residual
        fragmentation score of the KPNEG metric queried (choices are available in misc/enums).
        The best kpp-set will be that that maximizes the fragmentation when the nodes are removed from the graph.
        Available KP NEG choices:
        * KPNEGchoices.F: min = 0 (all nodes are isolates); max = 1 (network is a clique)
        * KPNEGchoices.dF: min = 0 (all nodes are isolates and therefore not connected; max = 1
        (The distance between each node pair is 1 hence the network is a clique)

        Args:
            graph (igraph.Graph): an igraph.Graph object. The graph should have specific properties.
                Please see the `Minimum requirements` specifications in pyntacle's manual

            kpp_size (int): the size of the optimal set found for the selected integer
            kpp_type (KPNEGchoices): a KPNEGchoices enumerators. right now, "F", and "dF" are available.
            seed (int): a seed that can be defined in order to replicate results. Default is None
            max_distances (int): an integer specifiying the maximum distance after that two nodes will be considered
            disconnected. Useful when trying to find short range interactions.

        Returns:
            KPSET(list), KPVALUE(float)
                * kpset (list): a list containing the node names of the optimal KPNEG set found
                * kpvalue (float): float representing the kp score for the graph when the set is removed
        """


        #todo reminder che l'implementazione è automatica
        if kpp_type == KPNEGchoices.F or kpp_type == KPNEGchoices.dF:
            if graph.ecount() == 0:
                sys.stdout.write("Graph is consisted of isolates, so there's no optimal KP Set that can fragment the network. Returning an empty list.\n")
                return [], 1.0


        # Definition of the starting S and notS sets
        node_indices = graph.vs.indices #retrieve the node indices of the whole graph

        random.shuffle(node_indices) #shuffle the node indices in order to subset each time a different starting set
        S = node_indices[0:kpp_size] #initial node set

        S.sort() #sort the starting set in order to retrieve its size afterwards

        notS = set(node_indices).difference(set(S)) #all the other indices in the graph that will be scanned

        # temporary copy of the graph from which the vertices that are selected as starting kpset will be removed
        temp_graph = graph.copy()
        temp_graph.delete_vertices(S)

        if kpp_type == KPNEGchoices.F:
            type_func = partial(kp.F, graph=graph)

        elif kpp_type == KPNEGchoices.dF:
            type_func = partial(kp.dF, graph=graph, max_distances=max_distances, implementation=implementation)
            # call the initial graph score here using automatic implementation for SPs

        else: #here all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        fragmentation_score = type_func(graph=graph)
        
        kppset_score_pairs_history = {} #a dictionary that stores score pairs
        kppset_score_pairs_history[tuple(S)] = fragmentation_score #keep track of the initial kp scores after the initial set is removed

        optimal_set_found = False #this becomes True when the maximum fragmentation is achieved

        while not optimal_set_found:
            kppset_score_pairs = {} #create a dictionary of solutions {tuple of solutions: score}

            for si in S:  #loop through all the node indices of the initial query
                temp_kpp_set = S.copy()  #copy the list of original indices
                temp_kpp_set.remove(si)  #remove the node of the current loop iteration

                for notsi in notS: #iterate all over the nodes not in the starting KPSET
                    temp_kpp_set.append(notsi) #create a new KPSET by replacing the input node (si) with all the pther nodes
                    temp_kpp_set.sort()  #necessary to avoid repetitions, we track the indices of the initial KP Set
                    temp_kpp_set_tuple = tuple(temp_kpp_set)  #convert the set to tuple

                    if temp_kpp_set_tuple in kppset_score_pairs_history:  #if we already passed through this kpset, then:
                        kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple] #append this pair to the history of this kpset (1st for loop)

                    else: #compute the KPNEG metrics for this new set
                        temp_graph = graph.copy() #create a new graph object and remove the modified kpp-set
                        temp_graph.delete_vertices(temp_kpp_set)

                        # if kpp_type == KPNEGchoices.F:
                        #     temp_kpp_func_value = kp.F(graph=temp_graph) #new modified scores
                        #
                        # elif kpp_type == KPNEGchoices.dF:
                        #     temp_kpp_func_value = kp.dF(graph=temp_graph, max_distances=max_sp)
                        temp_kpp_func_value = type_func(graph=temp_graph)
                        kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value #store the value in the dictionary
                        kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value

                    temp_kpp_set.remove(notsi) #remove the node

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            max_fragmentation = kppset_score_pairs[maxKpp]

            #todo Tommaso: how do we handle the case in which there is no optimal fragmentation score that maximize the initial fragmentation score?
            if max_fragmentation > fragmentation_score:
                S = list(maxKpp)
                notS = set(node_indices).difference(set(S))
                fragmentation_score = max_fragmentation
            else:
                optimal_set_found = True

        final = graph.vs(S)["name"]
        sys.stdout.write("A optimal kpp-set of size {} is {} with score {}\n".format(kpp_size, final,
                                                                         fragmentation_score))

        #this must be replaced when we find that greedy works
        return final, round(fragmentation_score, 5)

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer #todo solve the m problem in this decorator
    def reachability(graph, kpp_size, kpp_type, seed=None, max_distances=None, m=None, implementation=Cmode.igraph) -> (list, float):
        """
        It iteratively searches for a kpp-set of a predefined dimension, with maximal reachability according to the
        KPPOS metrics asked.
        Available choices:
        #. m-reach: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
        #. dR: min = 0 (unreachable); max = 1 (total reachability)

        :param int kpp_size: size of the kpp-set
        :param int m: maximum path length between the kpp-set and the other nodes of the graph
        :param KeyplayerAttribute.name kpp_type: Either KeyplayerAttribute.mreach or KeyplayerAttribute.dR
        :return: - S: **[EXPAND]**
                 - reachability_score: **[EXPAND]**
        :raises TypeError: When the kpp-set size is greater than the graph size
        :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.mreach or KeyplayerAttribute.dR
        """
        # sys.stdout.write("Greedily-optimized search of a kpp-set of size {0} for metric {1}\n".format(kpp_size, kpp_type.name))

        # Definition of the starting S and notS sets
        node_indices = graph.vs.indices
        random.shuffle(node_indices)
        S = node_indices[0:kpp_size]
        S_names = graph.vs(S)["name"] #take in input the node names
        S.sort()
        notS = set(node_indices).difference(set(S))

        utils = gu(graph=graph)

        if kpp_type == KPPOSchoices.mreach and m is None:
            raise WrongArgumentError("\"m\" must be specified for mreach")

        if kpp_type == KPPOSchoices.mreach:
            if not isinstance(m, int) or m <= 0:
                raise TypeError({"\"m\" must be a positive integer"})
            else:
                if implementation != Cmode.igraph:
                    sps = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)

                    type_func = partial(kp.mreach, graph=graph, nodes=S_names, m=m, max_distances=max_distances,
                                        implementation=implementation, sp_matrix=sps)
                else:
                    type_func = partial(kp.mreach, graph=graph, nodes=S_names, m=m, max_distances=max_distances,
                                        implementation=implementation)
        elif kpp_type == KPPOSchoices.dR:
            if implementation != Cmode.igraph:
                sps = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
                type_func = partial(kp.dR, graph=graph, nodes=S_names, max_distances=max_distances, implementation=implementation, sp_matrix=sps)
            else:
                type_func = partial(kp.dR, graph=graph, nodes=S_names, max_distances=max_distances,
                                    implementation=implementation)

        else: #all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        reachability_score = type_func()

        kppset_score_pairs_history = {}

        kppset_score_pairs_history[tuple(S)] = reachability_score

        optimal_set_found = False
        while not optimal_set_found:
            kppset_score_pairs = {}

            for si in S:
                temp_kpp_set = S.copy()
                temp_kpp_set.remove(si)

                for notsi in notS:
                    temp_kpp_set.append(notsi)
                    temp_kpp_set.sort()
                    temp_kpp_set_tuple = tuple(temp_kpp_set)

                    if temp_kpp_set_tuple in kppset_score_pairs_history:
                        kppset_score_pairs[temp_kpp_set_tuple] = kppset_score_pairs_history[temp_kpp_set_tuple]

                    else:
                        temp_kpp_set_names = utils.get_node_names(index_list=temp_kpp_set)
                        temp_kpp_func_value=type_func(graph=graph, nodes=temp_kpp_set_names, max_distances=max_distances, implementation=implementation)

                        kppset_score_pairs[temp_kpp_set_tuple] = temp_kpp_func_value
                        kppset_score_pairs_history[temp_kpp_set_tuple] = temp_kpp_func_value

                    temp_kpp_set.remove(notsi)

            maxKpp = max(kppset_score_pairs, key=kppset_score_pairs.get)
            max_reachability = kppset_score_pairs[maxKpp]

            if max_reachability > reachability_score:
                S = list(maxKpp)
                notS = set(node_indices).difference(set(S))
                reachability_score = max_reachability
            else:
                optimal_set_found = True
        final = graph.vs(S)["name"]
        sys.stdout.write("A optimal kpp-set of size {} is {} with score {}\n".format(kpp_size, final,
                                                                                   reachability_score))
        return final, round(reachability_score, 5)
