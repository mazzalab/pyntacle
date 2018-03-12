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

import itertools
from functools import partial
from algorithms.keyplayer_NEW import KeyPlayer
from exceptions.wrong_argument_error import WrongArgumentError
from misc.enums import KPPOSchoices, KPNEGchoices
from misc.kpsearch_utils import greedy_search_initializer
from misc.graph_routines import check_graph_consistency
from misc.implementation_seeker import implementation_seeker
from tools.graph_utils import GraphUtils as gu
from config import *

class BruteforceSearch:
    """
    Brute-force search for the best kp-set **[EXPAND]**
    """
    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def fragmentation(graph, kpp_size, kpp_type, max_distances=None) -> (list, float):
        """
        It searches and finds the kpp-set of a predefined dimension that best disrupts the graph.
        It generates all the possible kpp-sets and calculates the fragmentation score of the residual graph, after
        having extracted the nodes belonging to the kpp-set.
        The best kpp-set will be the one that maximizes the fragmentation of the graph.

        :param int kpp_size: the size of the kpp-set
        :param KPNEGchoices kpp_type: any of the *KPNEGchoices* enumerators available
        :return: - S: a list of lists containing all the possible sets of nodes that optimize the kp-sets
                 - best_fragmentation_score: The value obtained when the S set is removed from the graph. If there are
                 multiple sets available, the fragmentation score represents the value when **any** of the sets
                 are removed
        """

        if kpp_type == KPNEGchoices.F or kpp_type == KPNEGchoices.dF:
            if graph.ecount() == 0:
                sys.stdout.write("Graph is consisted of isolates, so there's no optimal KP Set that can fragment the network. Returning an empty list.\n")
                return [], 1.0

        # todo: enable multiple solutions
        kppset_score_pairs = {}

        # Generation of all combinations of nodes (all kpp-sets) of size kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size) #generate all possible node combinations for the selected set

        if kpp_type == KPNEGchoices.F:
            type_func = partial(KeyPlayer.F, graph=graph)

        elif kpp_type == KPNEGchoices.dF:
            implementation = implementation_seeker(graph) #call the correct implementation and pass it
            type_func = partial(KeyPlayer.dF, graph=graph, max_distances=max_distances, implementation=implementation)

        else:  # here all the other KPNEG functions we want to insert
            sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
            sys.exit(0)

        init_fragmentation_score = type_func(graph=graph) #initial fragmentation value

        for S in allS:
            temp_graph = graph.copy()
            temp_graph.delete_vertices(S)
            kppset_score_pairs[tuple(S)] = type_func(graph=temp_graph)

        maxKpp = max(kppset_score_pairs.values()) #this takes only in the first hit, not all hits

        if maxKpp < init_fragmentation_score:
            sys.stdout.write("There is no set of size {} that maximize the initial fragmentation score, returning an empty list and the max fragmentation score\n".format(kpp_size))
            return [], round(init_fragmentation_score, 5)

        else:
            S = [list(x) for x in kppset_score_pairs.keys() if kppset_score_pairs[x] == maxKpp]

        final = [graph.vs(x)["name"] for x in S]

        if len(final) > 1:
            sys.stdout.write("The best kpp-set(s) of size {} are {} with score {}".format(kpp_size, final,
                                                                                      maxKpp))

        else:
            sys.stdout.write("The best kpp-set(s) of size {} is {} with score {}".format(kpp_size, final,
                                                                                          maxKpp))

        return final, round(maxKpp, 5)

    @staticmethod
    @check_graph_consistency
    @greedy_search_initializer
    def reachability(graph, kpp_size, kpp_type, m=None, max_distances=None) -> (list, float):
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

        #find the correct implementation that will be passed to either one of the two KP metrics (in order to avoid the implementation seeker to find it at every iteration
        implementation = implementation_seeker(graph)

        kppset_score_pairs = {} #dictionary that will store results

        # Generation of all combinations of nodes (all kpp-sets) of size equal to the kpp_size
        node_indices = graph.vs.indices
        allS = itertools.combinations(node_indices, kpp_size)
        #initialize graphUtils tool to retrieve  the node names from node indices
        utils = gu(graph=graph)

        for S in allS:
            nodes = utils.get_node_names(S)

            if kpp_type == KPPOSchoices.mreach:
                reachability_score = KeyPlayer.mreach(graph=graph, nodes=nodes, m=m, max_distances=max_distances, implementation=implementation)

            elif kpp_type == KPPOSchoices.dR:
                reachability_score = KeyPlayer.dR(graph=graph, nodes=nodes, max_distances=max_distances, implementation=implementation)

            else:  # here all the other KPNEG functions we want to insert
                sys.stdout.write("{} Not yet implemented, please come back later!".format(kpp_type.name))
                sys.exit(0)

            kppset_score_pairs[tuple(S)] = reachability_score

        #now the dictionary is filled with all the possible solutions. Time to find the maximal ones
        maxKpp = max(kppset_score_pairs.values()) #take the maximum value

        result = [list(x) for x in kppset_score_pairs.keys() if x == maxKpp]

        if len(result) > 1:
            sys.stdout.write("The best kpp-sets of size {} are {} with score {}\n".format(kpp_size, result, maxKpp))
        else:
            sys.stdout.write("The best kpp-sets of size {} is {} with score {}\n".format(kpp_size, result, maxKpp))

        return result, round(maxKpp, 5)