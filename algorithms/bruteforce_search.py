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
from tools.misc.implementation_seeker import implementation_seeker
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
    def __crunch_fragmentation_combinations__(allS, graph: Graph, kpp_type: KPNEGchoices, max_distances) -> dict:
        kppset_score_pairs = {}

        # print("{}: {}".format(os.getpid(), len(allS)))

        temp_graph = graph.copy()
        temp_graph.delete_vertices(allS)
        if kpp_type == KPNEGchoices.F:
            type_func = partial(KeyPlayer.F, graph=graph)

        elif kpp_type == KPNEGchoices.dF:
            if '__implementation' in graph.attributes():
                implementation = graph['__implementation']
            else:
                implementation = SP_implementations.igraph
            type_func = partial(KeyPlayer.dF, graph=graph, max_distances=max_distances, implementation=implementation)

        else:  # here all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        init_fragmentation_score = type_func(graph=graph)  # initial fragmentation value

        kppset_score_pairs[allS] = type_func(temp_graph)
        return kppset_score_pairs

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def fragmentation(graph, kpp_size, kpp_type, max_distances=None, parallel = True, ncores = None) -> (list, float):
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
        :param bool parallel: whether to use parallelization or not. Default is True
        :param int ncores: the total number of cores to be used in parallel search. Defaul is the maximum number of cores -1
        :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
                 - best_fragmentation_score: The value obtained when the S set is removed from the graph. If there are
                 multiple sets available, the fragmentation score represents the value when **any** of the sets
                 are removed
        """
        if kpp_type == KPNEGchoices.F or kpp_type == KPNEGchoices.dF:
            if graph.ecount() == 0:
                sys.stdout.write(
                    "Graph is consisted of isolates, so there's no optimal KP Set that can fragment the network. Returning an empty list.\n")
                return [], 1.0


        if kpp_type == KPNEGchoices.F:
            type_func =  partial(KeyPlayer.F, graph=graph)
            init_fragmentation_score = type_func


        elif kpp_type == KPNEGchoices.dF:
            type_func = partial(KeyPlayer.dF, graph=graph, max_distances=max_distances)
            init_fragmentation_score = type_func

        else:
            init_fragmentation_score = None
        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices,
                                      kpp_size)  # generate all possible node combinations for the selected set

        if parallel:

            if ncores is None:
                ncores = mp.cpu_count()-1

            else:
                if not isinstance(ncores, int) or ncores < 0 :
                    raise TypeError("\"ncores\" must be an integer, {} found")

            sys.stdout.write("Parallel BruteForce implementation using {} cores".format(ncores))

        if parallel:
            final_set = BruteforceSearch.__bruteforce_fragmentation_parallel__(graph=graph, kpp_size=kpp_size, kpp_type=kpp_type, ncores=ncores, max_distances=max_distances) #this is equivalent to the kppset_score_pairs

        else:
            final_set = BruteforceSearch.__bruteforce_fragmentation_single__(graph=graph, kpp_size=kpp_size, kpp_type=kpp_type, max_distances=max_distances) #this is equivalent to the kppset_score_pairs

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

        if len(final) > 1:
            sys.stdout.write("The best kpp-set(s) of size {} are {} with score {}".format(kpp_size, final,maxKpp))

        else:
            sys.stdout.write("The best kpp-set(s) of size {} is {} with score {}".format(kpp_size, final,maxKpp))

        return final, round(maxKpp, 5)

    # @staticmethod
    # def __bruteforce_fragmentation_single:
    #
    #     def fragmentation(graph, kpp_size, kpp_type, max_distances=None) -> (list, float):
    #         """
    #         It searches and finds the kpp-set of a predefined dimension that best disrupts the graph.
    #         It generates all the possible kpp-sets and calculates the fragmentation score of the residual graph, after
    #         having extracted the nodes belonging to the kpp-set.
    #         The best kpp-set will be the one that maximizes the fragmentation of the graph.
    #         :param int kpp_size: the size of the kpp-set
    #         :param KPNEGchoices kpp_type: any of the *KPNEGchoices* enumerators available
    #         :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
    #                  - best_fragmentation_score: The value obtained when the S set is removed from the graph. If there are
    #                  multiple sets available, the fragmentation score represents the value when **any** of the sets
    #                  are removed
    #         """
    #
    #         if kpp_type == KPNEGchoices.F or kpp_type == KPNEGchoices.dF:
    #             if graph.ecount() == 0:
    #                 sys.stdout.write(
    #                     "Graph is consisted of isolates, so there's no optimal KP Set that can fragment the network. Returning an empty list.\n")
    #                 return [], 1.0
    #
    #         # todo: enable multiple solutions
    #         kppset_score_pairs = {}
    #
    #         # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
    #         node_indices = graph.vs.indices
    #         allS = itertools.combinations(node_indices,
    #                                       kpp_size)  # generate all possible node combinations for the selected set
    #
    #         if kpp_type == KPNEGchoices.F:
    #             type_func = partial(KeyPlayer.F, graph=graph)
    #
    #         elif kpp_type == KPNEGchoices.dF:
    #             type_func = partial(KeyPlayer.dF, graph=graph, max_distances=max_distances)
    #
    #         else:  # here all the other KPNEG functions we want to insert
    #             sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
    #             sys.exit(0)
    #
    #         init_fragmentation_score = type_func(graph=graph)  # initial fragmentation value
    #
    #         for S in allS:
    #             temp_graph = graph.copy()
    #             temp_graph.delete_vertices(S)
    #             kppset_score_pairs[tuple(S)] = type_func(graph=temp_graph)
    #
    #         maxKpp = max(kppset_score_pairs.values())  # this takes only in the first hit, not all hits
    #
    #         if maxKpp < init_fragmentation_score:
    #             sys.stdout.write(
    #                 "There is no set of size {} that maximize the initial fragmentation score, returning an empty list and the max fragmentation score\n".format(
    #                     kpp_size))
    #             return [], round(init_fragmentation_score, 5)
    #
    #         else:
    #             S = [list(x) for x in kppset_score_pairs.keys() if kppset_score_pairs[x] == maxKpp]
    #
    #         final = [graph.vs(x)["name"] for x in S]
    #
    #         if len(final) > 1:
    #             sys.stdout.write("The best kpp-set(s) of size {} are {} with score {}".format(kpp_size, final,
    #                                                                                           maxKpp))
    #
    #         else:
    #             sys.stdout.write("The best kpp-set(s) of size {} is {} with score {}".format(kpp_size, final,
    #                                                                                          maxKpp))
    #
    #         return final, round(maxKpp, 5)


    @staticmethod
    def __bruteforce_fragmentation_parallel__(graph:  Graph, kpp_size :int, kpp_type:KPNEGchoices, ncores:int, max_distances=None) -> (list, float):
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
        for partial_result in pool.imap_unordered(partial(BruteforceSearch.__crunch_fragmentation_combinations__,graph=graph,kpp_type=kpp_type), allS):
            kppset_score_pairs = {**kppset_score_pairs, **partial_result}

        pool.close()
        pool.join()

        return kppset_score_pairs

    #

    # #todo implement this
    # @staticmethod
    # def crunch_reachability_combinations(allS, graph: Graph, kpp_type: _KeyplayerAttribute, m=None) -> dict:
    #     kppset_score_pairs = {}
    #     """: type: dic{(), float}"""
    #
    #     # print("{}: {}".format(os.getpid(), len(allS)))
    #
    #     if kpp_type == KPPOSchoices.mreach:
    #         if implementation != SP_implementations.igraph:
    #             sp_matrix = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
    #             reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distances=max_distances,
    #                                                   implementation=implementation, sp_matrix=sp_matrix)
    #         else:
    #             reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distances=max_distances,
    #                                                   implementation=implementation)
    #
    #     elif kpp_type == KPPOSchoices.dR:
    #         if implementation != SP_implementations.igraph:
    #             sp_matrix = Lt.shortest_path_pyntacle(graph=graph, implementation=implementation)
    #             reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distances=max_distances,
    #                                               implementation=implementation, sp_matrix=sp_matrix)
    #         else:
    #             reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distances=max_distances,
    #                                               implementation=implementation)
    #
    #     else:  # here all the other KPNEG functions we want to insert
    #         sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
    #         sys.exit(0)
    #
    #     kppset_score_pairs[allS] = reachability_score
    #
    #     return kppset_score_pairs



    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def reachability(graph, kpp_size, kpp_type, max_distances=None, m=None) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best reaches all other nodes over the graph.
        It generates all the possible kpp-sets and calculates their reachability scores.
        The best kpp-set will be the one that best reaches all other nodes of the graph.

        **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
        **dR**: min = 0 (unreachable); max = 1 (total reachability)

        :param int kpp_size: size of the kpp-set
        :param int m: maximum path length between the kpp-set and the other nodes of the graph
        :param KPPOSchoices kpp_type: Either `KPPOSchoices.mreach` or `KPPOSchoices.dR`
        """

        if kpp_type == KPPOSchoices.mreach and m is None:
            raise WrongArgumentError("\"m\" must be specified for mreach")
        if kpp_type == KPPOSchoices.mreach and isinstance(m, int) and m <= 0:
            raise TypeError({"\"m\" must be a positive integer"})

        if '__implementation' in graph.attributes():
            implementation = graph['__implementation']
        else:
            implementation = SP_implementations.igraph

        kppset_score_pairs = {} #dictionary that will store results

        # Generation of all combinations of nodes (all kpp-sets) of size equal to the kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)
        #initialize graphUtils tool to retrieve  the node names from node indices
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

        #now the dictionary is filled with all the possible solutions. Time to find the maximal ones
        maxKpp = max(kppset_score_pairs.values()) #take the maximum value
        
        result = [utils.get_node_names(list(x)) for x in kppset_score_pairs.keys() if kppset_score_pairs[x] == maxKpp]

        if len(result) > 1:
            sys.stdout.write("The best kpp-sets of size {} are {} with score {}\n".format(kpp_size, result, maxKpp))
        else:
            sys.stdout.write("The best kpp-sets of size {} is {} with score {}\n".format(kpp_size, result, maxKpp))

        return result, round(maxKpp, 5)

# class BruteforceSearch:
#     """
#     **Brute-force search for the best kp-set**
#     This class performs the search of the best kp set for each kp metric using a brute force algorithm
#     specifically, it differs from the greedy_optimization class by finding ALL the best solutions for the
#     kp-mmetrics questioned. It is divided in two methods: :func:`bruteforce_fragmentation`'s for finding best kp-neg
#     set (and its relative values) and :func:'bruteforce_reachability's for finding the best kp-pos set (and its relative value)
#     """
#
#     def bruteforce_reachability_parallel(self, kpp_size, kpp_type, m=None, ncore=mp.cpu_count()) -> (list, float):
#         """
#         It searches and finds the kpp-set of a predefined dimension that best reaches all other nodes over the graph.
#         It generates all the possible kpp-sets and calculates their reachability scores.
#         The best kpp-set will be the one that best reaches all other nodes of the graph.
#
#         .. note:: **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
#
#                        **DR**: min = 0 (unreachable); max = 1 (total reachability)
#
#         :param int kpp_size: size of the kpp-set
#         :param int m: maximum path length between the kpp-set and the other nodes of the graph
#         :param KeyplayerAttribute.name kpp_type: Either KeyplayerAttribute.mreach or KeyplayerAttribute.DR
#         :param ncore: Number of CPU cores for parallel computing calculation of the maximum fragmentation score
#         :raises TypeError: When the kpp-set size is greater than the graph size
#         :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.mreach or KeyplayerAttribute.DR
#         """
#
#         if not isinstance(kpp_size, int):
#             self.logger.error("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
#             raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
#         elif kpp_size >= self.__graph.vcount():
#             self.logger.error("The kpp_size must be strictly less than the graph size")
#             raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")
#         elif kpp_type != _KeyplayerAttribute.DR and kpp_type != _KeyplayerAttribute.MREACH:
#             self.logger.error(
#                 "The kpp_type argument ('{}') must be of type KeyplayerAttribute.DR or KeyplayerAttribute.MREACH".format(
#                     kpp_type))
#             raise TypeError(
#                 "The kpp_type argument ('{}') must be of type KeyplayerAttribute.DR or KeyplayerAttribute.MREACH".format(
#                     kpp_type))
#         else:
#             self.logger.info("Brute-force search of the best kpp-set of size {}".format(kpp_size))
#
#             kppset_score_pairs = {}
#             """: type: dic{(), float}"""
#
#             # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
#             allS = itertools.combinations(self.__graph.vs.indices, kpp_size)
#
#             pool = mp.Pool(ncore)
#             for partial_result in pool.imap_unordered(partial(crunch_reachability_combinations,
#                                                               graph=self.__graph,
#                                                               kpp_type=kpp_type,
#                                                               m=m),
#                                                       allS):
#                 kppset_score_pairs = {**kppset_score_pairs, **partial_result}
#             pool.close()
#             pool.join()
#
#             best_reachability_score = max(kppset_score_pairs.values())
#             maxkpp_node_names = [self.__graph.vs(k)["name"] for k, v in kppset_score_pairs.items() if
#                                  v == best_reachability_score]
#             self.logger.info("The best kpp-set of size {} {} {} with score {}".format(kpp_size,
#                                                                                       'are' if len(
#                                                                                           maxkpp_node_names) > 1 else 'is',
#                                                                                       ', '.join([''.join(m) for m in
#                                                                                                  maxkpp_node_names]),
#                                                                                       best_reachability_score))
#             return maxkpp_node_names, best_reachability_score
