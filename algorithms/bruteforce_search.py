"""
Brute-force search optimization algorithms for the best kp-set.
This algorithm makes all possible combinations of node sets of a specified size and applies the KP-algorithm on them.
It hence selects the KPP-set with the best score.
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.2"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27(04/2018"
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


from config import *
import itertools
from functools import partial
from algorithms.keyplayer import KeyPlayer
from algorithms.shortest_path import ShortestPath as sp
from exceptions.wrong_argument_error import WrongArgumentError
from tools.enums import KpposEnum, KpnegEnum, CmodeEnum
from tools.misc.kpsearch_utils import bruteforce_search_initializer
from tools.misc.graph_routines import check_graph_consistency
from tools.graph_utils import GraphUtils as gu
from igraph import Graph
import multiprocessing as mp


def crunch_reachability_combinations(allS, graph: Graph, kpp_type: KpposEnum, m: int,
                                     max_distance: int, implementation: CmodeEnum) -> dict:
    # print("{}: {}".format(os.getpid(), len(allS)))
    kppset_score_pairs = {}
    if kpp_type == KpposEnum.mreach:
        if implementation != CmodeEnum.igraph:
            sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
            reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distance=max_distance,
                                                  implementation=implementation, sp_matrix=sp_matrix)
        else:
            reachability_score = KeyPlayer.mreach(graph=graph, nodes=allS, m=m, max_distance=max_distance,
                                                  implementation=implementation)
    elif kpp_type == KpposEnum.dR:
        if implementation != CmodeEnum.igraph:
            sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
            reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distance=max_distance,
                                              implementation=implementation, sp_matrix=sp_matrix)
        else:
            reachability_score = KeyPlayer.dR(graph=graph, nodes=allS, max_distance=max_distance,
                                              implementation=implementation)

    else:  # TODO: change to raise and exception
        sys.stdout.write("{} not yet implemented".format(kpp_type.name))
        sys.exit(0)

    kppset_score_pairs[allS] = reachability_score
    return kppset_score_pairs


def crunch_fragmentation_combinations(allS, graph: Graph, kpp_type: KpnegEnum,
                                      implementation: CmodeEnum, max_distance) -> dict:
    kppset_score_pairs_partial = {}

    # print("{}: {}".format(os.getpid(), len(allS)))

    temp_graph = graph.copy()
    temp_graph.delete_vertices(allS)

    if kpp_type == KpnegEnum.F:
        kppset_score_pairs_partial[allS] = KeyPlayer.F(temp_graph)

    elif kpp_type == KpnegEnum.dF:
        kppset_score_pairs_partial[allS] = KeyPlayer.dF(graph=temp_graph, max_distance=max_distance,
                                                        implementation=implementation)

    else:  # here all the other KPNEG functions we want to insert
        sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
        sys.exit(0)

    # kppset_score_pairs[allS] = type_func(temp_graph) #, graph=temp_graph, max_distance=max_distance, implementation=implementation)
    return kppset_score_pairs_partial


class BruteforceSearch:
    """
    Brute-force search for the best kp-set using either parallel or single core implementation. Return all the best
    KP-sets for a given reachability or fragmentation metrics
    """

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def fragmentation(graph, kpp_size, kpp_type: KpnegEnum, max_distance=None, implementation=CmodeEnum.igraph,
                      parallel=False, ncores=None) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best disrupts the graph.
        It generates all the possible KP-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the KP-set.
        The best KP-set will be the one that maximizes the fragmentation of the graph.
        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param int kpp_size: the size of the KP-set to be found
        :param KpnegEnum kpp_type: any option of the *KpnegEnum* enumerator
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :param CmodeEnum.igraph implementation: Computation of the shortest paths is deferred
        to the following implementations:
        *`imps.auto`: the most performing implementation is automatically chosen according to the geometry of graph
        *`imps.igraqh`: (default) use the default shortest path implementation in igraph (run on a single computing core)
        *`imps.pyntacle`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors or NVIDIA-enabled GPU graphic cards. This method returns a matrix (`:type np.ndarray:`) of shortest
        paths. Infinite distances actually equal the total number of vertices plus one.
        :param bool parallel: whether to use multicore processing
        :param int ncores: Positive integer specifying the number of cores that will be used to perform parallel
        computing. If `None` (default) the number of cores will be set to the maximum number of cores -1
        :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
                 - best_fragmentation_score: The value obtained when the S set is removed from the graph. If there are
                 multiple sets available, the fragmentation score represents the value when **any** of the sets
                 are removed
        """
        if kpp_type == KpnegEnum.F or kpp_type == KpnegEnum.dF:
            if graph.ecount() == 0:
                sys.stdout.write(
                    "Graph is consisted of isolates, so there is no optimal KP-set that can fragment the network. "
                    "Returning an empty list and the maximum {} value (1.0).\n".format(kpp_type.name))
                return [], 1.0

        # define an initial fragmentation status of the graph
        if kpp_type == KpnegEnum.F:
            init_fragmentation_score = KeyPlayer.F(graph=graph)
        elif kpp_type == KpnegEnum.dF:
            init_fragmentation_score = KeyPlayer.dF(graph=graph,implementation=implementation,max_distance=max_distance)
        else:
            init_fragmentation_score = None

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            else:
                if not isinstance(ncores, int) or ncores < 0:
                    raise TypeError("'ncores' must be an integer value, {} found")
            sys.stdout.write("Brute-Force Fragmentation will be performed in parallel using {} cores\n".format(ncores))
        if parallel:
            final_set = BruteforceSearch.__bruteforce_fragmentation_parallel(graph=graph, kpp_size=kpp_size,
                                                                             kpp_type=kpp_type, ncores=ncores,
                                                                             max_distance=max_distance,
                                                                             implementation=implementation)
        else:
            final_set = BruteforceSearch.__bruteforce_fragmentation_single(graph=graph, kpp_size=kpp_size,
                                                                           kpp_type=kpp_type,
                                                                           max_distance=max_distance,
                                                                           implementation=implementation)

        maxKpp = max(final_set.values())
        if init_fragmentation_score is not None:
            if maxKpp < init_fragmentation_score:
                sys.stdout.write(
                    "There is no set of size {} that maximize the initial fragmentation score, "
                    "returning an empty list and the max fragmentation score\n".format(kpp_size))
                return [], round(init_fragmentation_score, 5)
            else:
                S = [list(x) for x in final_set.keys() if final_set[x] == maxKpp]
        else:
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
    def __bruteforce_fragmentation_single(graph: Graph, kpp_size: int, kpp_type: KpnegEnum,
                                          implementation: CmodeEnum, max_distance):
        sys.stdout.write("Brute-force search of the best kpp-set of size {}".format(kpp_size))

        if kpp_type == KpnegEnum.F:
            type_func = partial(KeyPlayer.F, graph=graph)
        elif kpp_type == KpnegEnum.dF:
            type_func = partial(KeyPlayer.dF, graph=graph, max_distance=max_distance, implementation=implementation)
        else:  # TODO: change to raise exceptions
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)
        kppset_score_pairs = {}

        for S in allS:
            temp_graph = graph.copy()
            temp_graph.delete_vertices(S)
            kppset_score_pairs[tuple(S)] = type_func(graph=temp_graph)

        return kppset_score_pairs

    @staticmethod
    def __bruteforce_fragmentation_parallel(graph: Graph, kpp_size: int, kpp_type: KpnegEnum, ncores: int,
                                            implementation: CmodeEnum, max_distance=None) -> dict:
        sys.stdout.write("Brute-force search of the best kpp-set of size {}".format(kpp_size))

        kppset_score_pairs = {}
        """: type: dic{(), float}"""

        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)

        pool = mp.Pool(ncores)
        for partial_result in pool.imap_unordered(
                partial(crunch_fragmentation_combinations, graph=graph, kpp_type=kpp_type,
                        implementation=implementation, max_distance=max_distance), allS):
            kppset_score_pairs = {**kppset_score_pairs, **partial_result}

        pool.close()
        pool.join()

        return kppset_score_pairs

    @staticmethod
    @check_graph_consistency
    @bruteforce_search_initializer
    def reachability(graph, kpp_size, kpp_type: KpposEnum, max_distance=None, m=None, implementation=CmodeEnum.igraph,
                     parallel=False, ncores=None) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best reaches all other nodes in the graph.
        It generates all the possible kpp-sets and calculates their reachability scores.
        The best kpp-set will be the one that best reaches all other nodes of the graph.

        **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)
        **dR**: min = 0 (unreachable); max = 1 (total reachability)

        :param igraph.Graph graph: an igraph.Graph object, The graph must have specific properties. Please see the
        "Minimum requirements" specifications in the pyntacle's manual.
        :param int kpp_size: the size of the KP-set to be found
        :param KpnegEnum kpp_type: any option of the *KpposEnum* enumerators
        :param int max_distance: The maximum shortest path length over which two nodes are considered unreachable
        :param CmodeEnum.igraph implementation: Computation of the shortest paths is deferred
        to the following implementations:
        *`imps.auto`: the most performing implementation is automatically chosen according to the geometry of graph
        *`imps.igraqh`: (default) use the default shortest path implementation in igraph (run on a single computing core)
        *`imps.pyntacle`: compute shortest paths using the Floyd-Warshall algorithm designed for HPC hardware (multicore
        processors or NVIDIA-enabled GPU graphic cards. This method returns a matrix (`:type np.ndarray:`) of shortest
        paths. Infinite distances actually equal the total number of vertices plus one.
        :param bool parallel: whether to use multicore processing
        :param int ncores: Positive integer specifying the number of cores that will be used to perform parallel
        computing. If `None` (default) the number of cores will be set to the maximum number of cores -1

        :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
         - best_reachability_score: The value for the S set that maximmixes the *KP-pos* metrics requested. If there are
         multiple sets available, then there are multiple solutions to the reachability scores, meaning that
         different sets of nodes maximumze the reachability metric queried
        """

        if kpp_type == KpposEnum.mreach and m is None:
            raise WrongArgumentError("\"m\" must be specified for mreach")
        if kpp_type == KpposEnum.mreach and isinstance(m, int) and m <= 0:
            raise TypeError({"'m' must be a positive integer"})

        if parallel:
            if ncores is None:
                ncores = mp.cpu_count() - 1
            else:
                if not isinstance(ncores, int) or ncores < 0:
                    raise TypeError("'ncores' must be an integer, {} found")

            sys.stdout.write("Brute-Force Reachability will be performed in parallel using {} cores\n".format(ncores))

        if parallel:
            final_set = BruteforceSearch.__bruteforce_reachability_parallel(graph=graph, kpp_size=kpp_size,
                                                                            kpp_type=kpp_type, m=m,
                                                                            max_distance=max_distance,
                                                                            implementation=implementation,
                                                                            ncores=ncores)
        else:
            final_set = BruteforceSearch.__bruteforce_reachability_single(graph=graph, kpp_size=kpp_size,
                                                                          kpp_type=kpp_type, m=m,
                                                                          max_distance=max_distance,
                                                                          implementation=implementation)

        maxKpp = max(final_set.values())  # take the maximum value
        final = [list(graph.vs(x)["name"]) for x in final_set.keys() if final_set[x] == maxKpp]
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
    def __bruteforce_reachability_single(graph: Graph, kpp_size: int, kpp_type: KpposEnum, m: int,
                                         max_distance: int, implementation=CmodeEnum.igraph):
        sys.stdout.write("Brute-force search of the best kpp-set of size {}".format(kpp_size))

        kppset_score_pairs = {}
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)

        utils = gu(graph=graph)
        for S in allS:
            nodes = utils.get_node_names(list(S))

            if kpp_type == KpposEnum.mreach:
                if implementation != CmodeEnum.igraph:
                    sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
                    reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distance=max_distance,
                                                          implementation=implementation, sp_matrix=sp_matrix)
                else:
                    reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distance=max_distance,
                                                          implementation=implementation)

            elif kpp_type == KpposEnum.dR:
                if implementation != CmodeEnum.igraph:
                    sp_matrix = sp.get_shortestpaths(graph=graph, cmode=implementation, nodes=None)
                    reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distance=max_distance,
                                                      implementation=implementation, sp_matrix=sp_matrix)
                else:
                    reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distance=max_distance,
                                                      implementation=implementation)

            else:  # TODO: change to raise exceptions
                sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
                sys.exit(0)

            kppset_score_pairs[tuple(S)] = reachability_score

        return kppset_score_pairs

    @staticmethod
    def __bruteforce_reachability_parallel(graph: Graph, kpp_size: int, kpp_type: KpposEnum, m: int,
                                           max_distance: int, implementation: CmodeEnum, ncores: int) -> (list, float):
        sys.stdout.write("Brute-force search of the best kpp-set of size {}".format(kpp_size))

        kppset_score_pairs = {}
        """: type: dic{(), float}"""

        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        utils = gu(graph=graph)
        all_node_names = utils.get_node_names(graph.vs.indices)
        allS = itertools.combinations(all_node_names, kpp_size)

        pool = mp.Pool(ncores)

        for partial_result in pool.imap_unordered(
                partial(crunch_reachability_combinations, graph=graph, kpp_type=kpp_type, m=m,
                        max_distance=max_distance, implementation=implementation), allS):
            kppset_score_pairs = {**kppset_score_pairs, **partial_result}

        pool.close()
        pool.join()

        return kppset_score_pairs
