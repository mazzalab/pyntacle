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
Brute-force search for the best kp-set.
This algorithm makes all possible combinations of node sets of a specified size and applies the KP-algorithm on them.
It hence selects the KPP-set with the best score.
"""


#original untouched version at https://github.com/mazzalab/pyntacle/blob/0ab47c0ccbb7d98123faca2c8c1a219ffc5ee7a0/algorithms/bruteforce_search_NEW.py

from config import *
import itertools
from functools import partial
from algorithms.keyplayer import KeyPlayer
from exceptions.wrong_argument_error import WrongArgumentError
from tools.misc.enums import KPPOSchoices, KPNEGchoices, SP_implementations
from tools.misc.kpsearch_utils import bruteforce_search_initializer
from tools.misc.graph_routines import check_graph_consistency
from algorithms.local_topology import LocalTopology as Lt
from tools.graph_utils import GraphUtils as gu
from igraph import Graph
import multiprocessing as mp

class BruteforceSearch:
    """
    Brute-force search for the best kp-set using either parallel or single core implementation. Returns ALL the best KP Sets
    for a given reachability or fragmentation metrics
    """

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def fragmentation(graph, kpp_size, kpp_type, max_distances=None, implementation=SP_implementations.igraph, parallel=False, ncores=None) -> (list, float):
        """
        (a wrapper for the single core and parallel bruteforce fragmentation)
        It searches and finds the kpp-set of a predefined dimension that best disrupts the graph.
        It generates all the possible kpp-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the kpp-set.
        The best kpp-set will be the one that maximizes the fragmentation of the graph.
        :param Graph graph: an `igraph.Graph` object formatted according to the *Minimum Requirements* (see pyntacle's manual)
        :param int kpp_size: the size of the kpp-set to be found
        :param KPNEGchoices kpp_type: any of the *KPNEGchoices* enumerators available
        :param int max_distances:
        :param SP_implementations implementations: one of the possible shortest path implementations avaiable in the `tools/misc/enums/SP_implementations` Default is SP_implementations.igraph (uses Dijkstra's algorithm from igraph)
        :param bool parallel: whether to use the parallel computing to perform the bruteforce search. Default is `False`
        :param int ncores: Positive integer specifying the number of cores that will be used to perform parallel computing. If `None` (default) the number of cores will be the maximum n umber of cores -1
        :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
                 - best_fragmentation_score: The value obtained when the S set is removed from the graph. If there are
                 multiple sets available, the fragmentation score represents the value when **any** of the sets
                 are removed
        """
        if kpp_type == KPNEGchoices.F or kpp_type == KPNEGchoices.dF:

            #case 0 : a graph consisting only of isolates (will not run bruteforce search
            if graph.ecount() == 0:
                sys.stdout.write(
                    "Graph is consisted of isolates, so there's no optimal KP Set that can fragment the network. Returning an empty list and the maximum {} value (1.0).\n".format(kpp_type.name))
                return [], 1.0

        #define an initial fragmentation status of the graph
        if kpp_type == KPNEGchoices.F:
            init_fragmentation_score = KeyPlayer.F(graph=graph)# initial fragmentation value

        elif kpp_type == KPNEGchoices.dF:
            init_fragmentation_score = KeyPlayer.dF(graph=graph, implementation=implementation,max_distances=max_distances)  # initial fragmentation value
        else:
            init_fragmentation_score = None

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count()-1

            else:
                if not isinstance(ncores, int) or ncores < 0 :
                    raise TypeError("\"ncores\" must be an integer, {} found")

            sys.stdout.write("Parallel BruteForce implementation using {} cores".format(ncores))

        #todo this doesn't work, focusing on single core implementation instead
        if parallel:
            final_set = BruteforceSearch.__bruteforce_fragmentation_parallel(graph=graph, kpp_size=kpp_size, kpp_type=kpp_type, ncores=ncores, max_distances=max_distances, implementation=implementation) #this is equivalent to the kppset_score_pairs

        #return the score of each kpp pair when nodes are removed
        else:
            final_set = BruteforceSearch.__bruteforce_fragmentation_single(graph=graph, kpp_size=kpp_size, kpp_type=kpp_type, max_distances=max_distances, implementation=implementation) #this is equivalent to the kppset_score_pairs
            # print (final_set)
            # input()

        maxKpp = max(final_set.values())  # this takes only in the first hit, not all hits

        if init_fragmentation_score is not None:
            if maxKpp < init_fragmentation_score:
                sys.stdout.write(
                    "There is no set of size {} that maximize the initial fragmentation score, returning an empty list and the max fragmentation score\n".format(
                        kpp_size))
                return [], round(init_fragmentation_score, 5)

            else:
                S = [list(x) for x in final_set.keys() if final_set[x] == maxKpp]

        else:
            S = [list(x) for x in final_set.keys() if final_set[x] == maxKpp]

        final = [graph.vs(x)["name"] for x in S]

        maxKpp = round(maxKpp, 5)

        if len(final) > 1:
            sys.stdout.write("The best kpp-sets for metric {} of size {} are {} with score {}\n".format(kpp_type.name, kpp_size, final, maxKpp))
        else:
            sys.stdout.write("The best kpp-sets for metric {} of size {} is {} with score {}\n".format(kpp_type.name, kpp_size, final, maxKpp))

        return final, maxKpp

    @staticmethod
    def __bruteforce_fragmentation_single(graph:Graph, kpp_size:int, kpp_type: KPNEGchoices, implementation: SP_implementations, max_distances):
        """
        """

        if kpp_type == KPNEGchoices.F:
            type_func = partial(KeyPlayer.F, graph=graph)

        elif kpp_type == KPNEGchoices.dF:
            type_func = partial(KeyPlayer.dF, graph=graph, max_distances=max_distances, implementation=implementation)

        else:  # here all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)



        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices,
                                      kpp_size)  # generate all possible node combinations for the selected set

        kppset_score_pairs = {}

        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size

        for S in allS:
            temp_graph = graph.copy()
            temp_graph.delete_vertices(S)
            kppset_score_pairs[tuple(S)] = type_func(graph=temp_graph)

        return kppset_score_pairs

    #todo Tommaso this is the part of the code that causes the issue
    @staticmethod
    def __crunch_fragmentation_combinations__(allS, graph: Graph, kpp_type: KPNEGchoices, implementation:SP_implementations,max_distances) -> dict:
        """
        Internal wrapper to some operations from `__bruteforce_fragmentation_parallel`
        """
        kppset_score_pairs = {} #todo Tommaso this is actually created in bruteforce_fragmentation_parallel. Shouldn't be better to pass it from there? (I didn't touch this from your code)

        # print("{}: {}".format(os.getpid(), len(allS)))

        temp_graph = graph.copy()
        temp_graph.delete_vertices(allS)

        if kpp_type == KPNEGchoices.F:
            type_func = partial(KeyPlayer.F, graph=temp_graph)

        elif kpp_type == KPNEGchoices.dF:
            type_func = partial(KeyPlayer.dF, graph=temp_graph, max_distances=max_distances, implementation=implementation)

        else:  # here all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        kppset_score_pairs[allS] = type_func(temp_graph)
        return kppset_score_pairs

    @staticmethod
    def __bruteforce_fragmentation_parallel(graph:  Graph, kpp_size :int, kpp_type:KPNEGchoices, ncores:int, implementation:SP_implementations,max_distances=None) -> dict:
        """
        It searches and finds the kpp-set of a predefined dimension that best disrupts the graph.
        It generates all the possible kpp-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the kpp-set.
        The best kpp-set will be the one that maximizes the fragmentation of the graph.
        :param ncore: Number of CPU cores for parallel computing calculation of the maximum fragmentation score
        :param kpp_size: the size of the kpp-set
        :type kpp_size: int
        :param kpp_type: Either KeyplayerAttribute.DF or KeyplayerAttribute.F
        :type kpp_type: KeyplayerAttribute.name
        :return: - maxkpp_tuple_names: A list of group of nodes (names) of size **kpp_size** achieving the same maximum fragmentation score
                 - best_fragmentation_score: The achieved maximum fragmentation score
        :rtype: (list[list[str]], float)
        :raises TypeError: When the kpp-set size is not an integer number
        :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.F or KeyplayerAttribute.DF
        """
        sys.stdout.write("Brute-force search of the best kpp-set of size {}".format(kpp_size))

        kppset_score_pairs = {}
        """: type: dic{(), float}"""

        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)

        pool = mp.Pool(ncores)
        #todo Tommaso: it stops here. Main reason is that "__cruch_fragmentation_combinations__" calls one of the KP functions and regardless which ones you choose, the decorator gives an error.
        #todo Tommaso: the command you should uyse to reproduce the issue is bf = BruteforceSearch.fragmentation(graph=graph, kpp_size=2, kpp_type=KPNEGchoices.dF, parallel=True, ncores=2)
        for partial_result in pool.imap_unordered(partial(BruteforceSearch.__crunch_fragmentation_combinations__, graph=graph, kpp_type=kpp_type, implementation=implementation, max_distances=max_distances), allS):
            kppset_score_pairs = {**kppset_score_pairs, **partial_result}

        pool.close()
        pool.join()

        return kppset_score_pairs

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def reachability(graph, kpp_size, kpp_type, max_distances=None, m=None, implementation=SP_implementations.igraph, parallel=False, ncores=None) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best reaches all other nodes over the graph.
        It generates all the possible kpp-sets and calculates their reachability scores.
        The best kpp-set will be the one that best reaches all other nodes of the graph.

        **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
        **dR**: min = 0 (unreachable); max = 1 (total reachability)

        :param Graph graph: a valid `igraph.Graph` object, already prepared to be used for pyntacle see "Pyntacle Minimum Requirements" for more info on regard
        :param int kpp_size: size of the kpp-set
        :param int m: maximum path length between the kpp-set and the other nodes of the graph
        :param KPPOSchoices kpp_type: Either `KPPOSchoices.mreach` or `KPPOSchoices.dR`
        :param int max_distances:
        :param SP_implementations implementations: one of the possible shortest path implementations avaiable in the `tools/misc/enums/SP_implementations` Default is SP_implementations.igraph (uses Dijkstra's algorithm from igraph)
        :param bool parallel: whether to use the parallel computing to perform the bruteforce search. Default is `False`
        :param int ncores: Positive integer specifying the number of cores that will be used to perform parallel computing. If `None` (default) the number of cores will be the maximum n umber of cores -1
        :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
                 - best_reachability_score: The value for the S set that maximmixe the *KPNEG* metrics requested. If there are
                 multiple sets available, then there are multiple solutions to the reachability scores, meaning that different sets of nodes maximumze the reachability metric queried
        """

        if kpp_type == KPPOSchoices.mreach and m is None:
            raise WrongArgumentError("\"m\" must be specified for mreach")
        if kpp_type == KPPOSchoices.mreach and isinstance(m, int) and m <= 0:
            raise TypeError({"\"m\" must be a positive integer"})

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count()-1

            else:
                if not isinstance(ncores, int) or ncores < 0 :
                    raise TypeError("\"ncores\" must be an integer, {} found")

            sys.stdout.write("Parallel BruteForce implementation using {} cores".format(ncores))

        if parallel:
            final_set = BruteforceSearch.__bruteforce_reachability_parallel(graph=graph, kpp_size=kpp_size, kpp_type=kpp_type, m=m, max_distances=max_distances, implementation=implementation, ncores=ncores)
        else:
            final_set = BruteforceSearch.__bruteforce_reachability_single(graph=graph, kpp_size=kpp_size, kpp_type=kpp_type, m=m, max_distances=max_distances, implementation=implementation)
            print("ciao")
            input()
            print(final_set)
            input()

        # now the dictionary is filled with all the possible solutions. Time to find the maximal ones
        maxKpp = max(final_set.values())  # take the maximum value

        S = [list(x) for x in final_set.keys() if final_set[x] == maxKpp]

        final = [graph.vs(x)["name"] for x in S]

        maxKpp = round(maxKpp, 5)

        if len(final) > 1:
            sys.stdout.write(
                "The best kpp-sets for metric {} of size {} are {} with score {}\n".format(kpp_type.name, kpp_size,
                                                                                           final, maxKpp))
        else:
            sys.stdout.write(
                "The best kpp-sets for metric {} of size {} is {} with score {}\n".format(kpp_type.name, kpp_size,
                                                                                          final, maxKpp))

        return final, maxKpp

    @staticmethod
    def __bruteforce_reachability_single(graph: Graph, kpp_size: int, kpp_type: KPPOSchoices, m: int, max_distances: int, implementation=SP_implementations.igraph):
        """
        Internal function that Implements bruteforce search at a singe core level. Recommended when the graph is relatively small (under 500 nodes)
        """
        kppset_score_pairs = {}
        # Generation of all combinations of nodes (all kpp-sets) of size equal to the kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)
        # initialize graphUtils tool to retrieve  the node names from node indices
        utils = gu(graph=graph)

        for S in allS:
            nodes = utils.get_node_names(list(S))

            if kpp_type == KPPOSchoices.mreach:
                if implementation != SP_implementations.igraph:
                    sp_matrix = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
                    reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distances=max_distances,
                                                          implementation=implementation, sp_matrix=sp_matrix)
                else:
                    reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distances=max_distances,
                                                          implementation=implementation)

            elif kpp_type == KPPOSchoices.dR:
                if implementation != SP_implementations.igraph:
                    sp_matrix = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
                    reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distances=max_distances,
                                                      implementation=implementation, sp_matrix=sp_matrix)
                else:
                    reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distances=max_distances,
                                                      implementation=implementation)

            else:  # here all the other KPNEG functions we want to insert
                sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
                sys.exit(0)

            kppset_score_pairs[tuple(S)] = reachability_score

        return kppset_score_pairs

    @staticmethod
    def __bruteforce_reachability_parallel(graph:Graph, kpp_size: int, kpp_type: KPPOSchoices, m:int, max_distances:int, implementation:SP_implementations, ncores:int) -> (list, float):
        """
        Internal function that Implements bruteforce search on a set of cores (passed by the `ncores` parameter). Recommended when the graph is quite large (over 500 nodes)
        """
        kppset_score_pairs = {}
        """: type: dic{(), float}"""
        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        allS = itertools.combinations(graph.vs.indices, kpp_size)

        pool = mp.Pool(ncores)

        #todo maybe the sp_matrix to be passed to the __crunch_reachability_combinations function should be computed here and not afterwards, to avoid reundancy and speed up code?.
        #todo this doesn't work at all, must be reworked IMHO
        for partial_result in pool.imap_unordered(partial(BruteforceSearch.__crunch_reachability_combinations,graph=graph,kpp_type=kpp_type,m=m, max_distances=max_distances, implementation=implementation),allS):
            kppset_score_pairs = {**kppset_score_pairs, **partial_result}

        pool.close()
        pool.join()

        return kppset_score_pairs #returns the dictionary filled with the correct values for each node combination

    @staticmethod
    def __crunch_reachability_combinations(allS, graph: Graph, kpp_type: KPPOSchoices, m: int, implementation: SP_implementations, max_distances) -> dict:
        """
        Internal wrapper to some operations from `__bruteforce_reachability_parallel`
        """

        # print("{}: {}".format(os.getpid(), len(allS)))
        kppset_score_pairs = {} #todo Tommaso this is actually created in bruteforce_reachability_parallel. Shouldn't be better to pass it from there? (I didn't touch this from your code)

        if kpp_type == KPPOSchoices.mreach:
            if implementation != SP_implementations.igraph:
                sp_matrix = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
                reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distances=max_distances,
                                                      implementation=implementation, sp_matrix=sp_matrix)
            else:
                reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distances=max_distances,
                                                      implementation=implementation)

        #todo Tommaso this doesn't work because the "nodes" parameter in reachshilibty_score requires node names when calling KP functions
        elif kpp_type == KPPOSchoices.dR:
            if implementation != SP_implementations.igraph:
                sp_matrix = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
                reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distances=max_distances,
                                                  implementation=implementation, sp_matrix=sp_matrix)
            else:
                reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distances=max_distances,
                                                  implementation=implementation)

        else:  # here all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        kppset_score_pairs[allS] = reachability_score

        return kppset_score_pairs

