__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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

""" insert your method description here """




def crunch_reachability_combinations(allS, graph: Graph, kpp_type: _KeyplayerAttribute, m=None) -> dict:
    kppset_score_pairs = {}
    """: type: dic{(), float}"""

    # print("{}: {}".format(os.getpid(), len(allS)))

    if kpp_type == _KeyplayerAttribute.MREACH:
        reachability_score = KeyPlayer.mreach(m, index_list=allS, recalculate=True)
    else:
        reachability_score = KeyPlayer.DR(node_names_list=allS, recalculate=True)

    kppset_score_pairs[allS] = reachability_score

    return kppset_score_pairs

class BruteforceSearch:
    """
    **Brute-force search for the best kp-set**
    This class performs the search of the best kp set for each kp metric using a brute force algorithm
    specifically, it differs from the greedy_optimization class by finding ALL the best solutions for the
    kp-mmetrics questioned. It is divided in two methods: :func:`bruteforce_fragmentation`'s for finding best kp-neg
    set (and its relative values) and :func:'bruteforce_reachability's for finding the best kp-pos set (and its relative value)
    """

    __graph = None
    """:type: Graph"""

    def __init__(self, graph: Graph):
        """
        Initializes a graph for brute-force search of the best KP-set
        :param Graph graph: Graph provided in input
        :raises IllegalGraphSizeError: if the graph does not contain vertices or edges
        """
        self.logger = log


        if graph.vcount() < 1:
            self.logger.fatal("This graph does not contain vertices")
            raise IllegalGraphSizeError("This graph does not contain vertices")
        elif graph.ecount() < 1:
            self.logger.fatal("This graph does not contain edges")
            raise IllegalGraphSizeError("This graph does not contain edges")
        else:
            self.__graph = graph
            GraphUtils.graph_checker(graph=self.__graph)

    def bruteforce_fragmentation_parallel(self, kpp_size, kpp_type: _KeyplayerAttribute, ncore=mp.cpu_count()) -> (
    list, float):
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

            self.logger.info("Brute-force search of the best kpp-set of size {}".format(kpp_size))

            if ncore == 1:
                # let's call and return results from the serial implementation
                return self.bruteforce_fragmentation(kpp_size, kpp_type)

            else:
                kppset_score_pairs = {}
                """: type: dic{(), float}"""

                # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
                node_indices = self.__graph.vs.indices
                allS = itertools.combinations(node_indices, kpp_size)

                pool = mp.Pool(ncore)
                for partial_result in pool.imap_unordered(partial(crunch_fragmentation_combinations,graph=self.__graph,kpp_type=kpp_type),allS):
                    kppset_score_pairs = {**kppset_score_pairs, **partial_result}

                pool.close()
                pool.join()

                best_fragmentation_score = max(kppset_score_pairs.values())
                maxkpp_node_names = [self.__graph.vs(k)["name"] for k, v in kppset_score_pairs.items() if
                                     v == best_fragmentation_score]
                self.logger.info("The best kpp-set of size {} {} {} with score {}".format(kpp_size,
                                                                                          'are' if len(
                                                                                              maxkpp_node_names) > 1 else 'is',
                                                                                          ', '.join([''.join(m) for m in
                                                                                                     maxkpp_node_names]),
                                                                                          best_fragmentation_score))
                return maxkpp_node_names, best_fragmentation_score



    def bruteforce_reachability_parallel(self, kpp_size, kpp_type, m=None, ncore=mp.cpu_count()) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best reaches all other nodes over the graph.
        It generates all the possible kpp-sets and calculates their reachability scores.
        The best kpp-set will be the one that best reaches all other nodes of the graph.

        .. note:: **m-reach**: min = 0 (unreachable); max = size(graph) - kpp_size (total reachability)

                       **DR**: min = 0 (unreachable); max = 1 (total reachability)

        :param int kpp_size: size of the kpp-set
        :param int m: maximum path length between the kpp-set and the other nodes of the graph
        :param KeyplayerAttribute.name kpp_type: Either KeyplayerAttribute.mreach or KeyplayerAttribute.DR
        :param ncore: Number of CPU cores for parallel computing calculation of the maximum fragmentation score
        :raises TypeError: When the kpp-set size is greater than the graph size
        :raises WrongArgumentError: When the kpp-type argument is not of type KeyplayerAttribute.mreach or KeyplayerAttribute.DR
        """

        if not isinstance(kpp_size, int):
            self.logger.error("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
            raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))
        elif kpp_size >= self.__graph.vcount():
            self.logger.error("The kpp_size must be strictly less than the graph size")
            raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")
        elif kpp_type != _KeyplayerAttribute.DR and kpp_type != _KeyplayerAttribute.MREACH:
            self.logger.error(
                "The kpp_type argument ('{}') must be of type KeyplayerAttribute.DR or KeyplayerAttribute.MREACH".format(
                    kpp_type))
            raise TypeError(
                "The kpp_type argument ('{}') must be of type KeyplayerAttribute.DR or KeyplayerAttribute.MREACH".format(
                    kpp_type))
        else:
            self.logger.info("Brute-force search of the best kpp-set of size {}".format(kpp_size))

            kppset_score_pairs = {}
            """: type: dic{(), float}"""

            # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
            allS = itertools.combinations(self.__graph.vs.indices, kpp_size)

            pool = mp.Pool(ncore)
            for partial_result in pool.imap_unordered(partial(crunch_reachability_combinations,
                                                              graph=self.__graph,
                                                              kpp_type=kpp_type,
                                                              m=m),
                                                      allS):
                kppset_score_pairs = {**kppset_score_pairs, **partial_result}
            pool.close()
            pool.join()

            best_reachability_score = max(kppset_score_pairs.values())
            maxkpp_node_names = [self.__graph.vs(k)["name"] for k, v in kppset_score_pairs.items() if
                                 v == best_reachability_score]
            self.logger.info("The best kpp-set of size {} {} {} with score {}".format(kpp_size,
                                                                                      'are' if len(
                                                                                          maxkpp_node_names) > 1 else 'is',
                                                                                      ', '.join([''.join(m) for m in
                                                                                                 maxkpp_node_names]),
                                                                                      best_reachability_score))
            return maxkpp_node_names, best_reachability_score