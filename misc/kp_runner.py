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

""" **a series of decorators to improve the usability of some pyntacle's function, like 
checking if the `igraph.Graph` object is compatible with pyntacle's specifications, verify the presence of nodes 
in the input graph, give elapsed time of execution and so on"""

# pyntacle libraries
from algorithms.greedy_optimization import *
from algorithms.bruteforce_search import *
from utils.graph_utils import *
from config import *
import time
from algorithms.key_player import _KeyplayerAttribute

class KeyPlayerWrapper():
    '''
    Wrapper for the KeyPlayer class, in order to pass proper data structures to the reporter class
    '''

    logger = None
    """:type: logger"""

    def __init__(self, graph: Graph):

        self.__kp = KeyPlayer
        self.logger = log
        '''
        check if graph has node names and they are unique
        '''
        if "name" not in graph.vs().attributes():
            raise AttributeError("\"name\" is not a node attribute, cannot compute name")

        elif len(list(set(graph.vs()["name"]))) != len(graph.vs()["name"]):
            raise AttributeError("node names are not unique")

        else:
            if "name" not in graph.attributes():
                raise MissingAttributeError("graph name is not defined")

            if graph.ecount() < 1 and graph.vcount() <= 2:
                raise IllegalGraphSizeError("Graph must contain at least one two node and 1 edge")

            else:
                self.__graph = graph

        # initialize graph utility class
        self.__utils = GraphUtils(graph=self.__graph)
        self.__utils.graph_checker()  # check graph properties

        self.results = {}  # dictionary that will store results

    def run_single_metrics(self, key_player: _KeyplayerAttribute, names_list=None, recalculate=False, m=None):

        # initialize kp function

        '''
        Given a single metric, compute it and store it into a dictionary of results
        
        :param key_player: a KeyplayerAttribute object
        :param names_list: a list of node names
        :param recalculate: boolean, whether to pass the "recalculate" flag to the KeyPlayer Method
        :param m: if MREACH is specified, this must be specified as well
        '''

        self.__utils.check_attribute_type(key_player, _KeyplayerAttribute)

        starting_value = None
        kp_value = None
        kp_nodes = None

        if names_list is None:

            if key_player == _KeyplayerAttribute.DF:
                kp_value = self.__kp(graph=self.__graph).DF(recalculate)

            elif key_player == _KeyplayerAttribute.F:
                kp_value = self.__kp(graph=self.__graph).F(recalculate)

            else:
                # print(KeyplayerAttribute)
                raise ValueError("Cannot compute Key Player Value for selected attribute")

        else:

            if len(names_list) >= self.__graph.vcount():
                raise IllegalKppsetSizeError("KP Set must be smaller than total graph size")
            # check if indices are in graph
            self.__utils.check_name_list(names_list=names_list)

            if not names_list:
                raise KeyError("node list must contain at least one node name")

            # retrieve index list
            index_list = self.__utils.get_node_indices(names_list)
            kp_nodes = self.__utils.get_node_names(index_list)

            if key_player == _KeyplayerAttribute.DF:
                starting_value = self.__kp(graph=self.__graph).DF(recalculate=recalculate)
                graph_copy = self.__graph.copy()
                graph_copy.delete_vertices(index_list)

                # start = time.perf_counter()
                kp_value = self.__kp(graph=graph_copy).DF(recalculate=recalculate)
                # end = time.perf_counter()
                # print("--- DF - Elapsed time: {:.2f} seconds ---".format(end - start))

            elif key_player == _KeyplayerAttribute.F:
                starting_value = self.__kp(graph=self.__graph).F(recalculate=recalculate)

                graph_copy = self.__graph.copy()
                graph_copy.delete_vertices(index_list)

                # start = time.perf_counter()
                kp_value = self.__kp(graph=graph_copy).F(recalculate=recalculate)
                # end = time.perf_counter()
                # print("--- F - Elapsed time: {:.2f} seconds ---".format(end - start))

            elif key_player == _KeyplayerAttribute.DR or key_player == _KeyplayerAttribute.MREACH:

                if key_player == _KeyplayerAttribute.MREACH:
                    if not isinstance(m, int) or m <= 0:
                        raise ValueError("m must be specified for MREACH and be a positive integer")

                    else:
                        # start = time.perf_counter()
                        kp_value = self.__kp(graph=self.__graph).mreach(m=m, index_list=index_list,recalculate=recalculate)
                        # end = time.perf_counter()
                        # print("--- MREACH - Elapsed time: {:.2f} seconds ---".format(end - start))
                        # print(kp_value)

                else:
                    # start = time.perf_counter()
                    kp_value = self.__kp(graph=self.__graph).DR(index_list=index_list, recalculate=recalculate)
                    # end = time.perf_counter()
                    # print("--- dR - Elapsed time: {:.2f} seconds ---".format(end - start))

        self.results[key_player] = (starting_value, kp_nodes, kp_value)
        #print(self.results)

    def run_pos_or_neg(self, choice: str, names_list=None, recalculate=False, m=None):
        '''
        Computes kpp-neg (DF, F) and kpp-pos(dR, MREACH) metrics,store everything into a dictionary
        
        :param choice: either "kpp pos" or "kpp neg"
        :param names_list: a list of node names
        :param recalculate: a boolean that will be passed to the KeyPlayerClass
        :param m: if kpp-pos is specified, must be specified
        '''
        choice = choice.lower()
        if choice == "kpp-pos":
            # compute both dR and MREACH
            self.run_single_metrics(key_player=_KeyplayerAttribute.DR, names_list=names_list, recalculate=recalculate)
            self.run_single_metrics(key_player=_KeyplayerAttribute.MREACH, names_list=names_list,
                                    recalculate=recalculate, m=m)

        elif choice == "kpp-neg":
            # compute both DF and F
            self.run_single_metrics(key_player=_KeyplayerAttribute.F, names_list=names_list, recalculate=recalculate)
            self.run_single_metrics(key_player=_KeyplayerAttribute.DF, names_list=names_list,
                                    recalculate=recalculate, m=m)
        else:
            raise WrongArgumentError("only viable choices for \"choice\" are \"kpp-pos\" or \"kpp-neg\"")

    def run_greedy(self, key_player, kpsize: int, m=None):
        '''
        Run Greedy optimization and wraps everything into a dictionary that will be passed to pyntacle commands
        
        :param key_player: a single KeyplayerAttribute or a list of KeyPlayerAttributes
        :param kpsize: an integer of kpsizes
        :param m: the m-reach distance(required if KeyPlayerattribute.MREACH is present
        :return: a dictionary of results like {keyplayer: ([kpset], [kpvalue])} (this is to remain coherent to the BruteForce optimization
        '''

        if not (isinstance(kpsize, int)) or kpsize <= 0:
            raise ValueError("kp must contain at least one element")

        if not isinstance(key_player, (list, _KeyplayerAttribute)):
            raise WrongArgumentError("kp must be a KeyplayerAttribute or a list of KeyplayerAttribute(s)")

        else:
            self.results["algorithm"] = "Greedy"  # todo handle this
            # greedy optimization for the KeyPlayerAttribuite
            if isinstance(key_player, _KeyplayerAttribute):
                starting_value = None

                if key_player == _KeyplayerAttribute.F:
                    starting_value = KeyPlayer(graph=self.__graph).F()
                    start = time.perf_counter()
                    go = GreedyOptimization(graph=self.__graph).optimize_kpp_neg(kpp_size=kpsize,
                                                                                 kpp_type=key_player)  # return a tuple(kp nodes, kpvalue)
                    end = time.perf_counter()
                    print("--- Elapsed time (F - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))


                elif key_player == _KeyplayerAttribute.DF:
                    start = time.perf_counter()
                    starting_value = KeyPlayer(graph=self.__graph).DF()
                    go = GreedyOptimization(graph=self.__graph).optimize_kpp_neg(kpp_size=kpsize,
                                                                                 kpp_type=key_player)  # return a tuple(kp nodes, kpvalue)
                    end = time.perf_counter()
                    print("--- Elapsed time (DF - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                elif key_player == _KeyplayerAttribute.DR:
                    start = time.perf_counter()
                    go = GreedyOptimization(graph=self.__graph).optimize_kpp_pos(kpp_size=kpsize,
                                                                                 kpp_type=key_player)  # return a tuple(kp nodes, kpvalue)
                    end = time.perf_counter()
                    print("--- Elapsed time (dR - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                elif key_player == _KeyplayerAttribute.MREACH:
                    if not isinstance(m, int) or m <= 0:
                        raise ValueError("m must be specified for MREACH and be a positive integer")
                    else:
                        start = time.perf_counter()
                        go = GreedyOptimization(graph=self.__graph).optimize_kpp_pos(kpp_size=kpsize,
                                                                                     kpp_type=key_player,
                                                                                     m=m)  # return a tuple(kp nodes, kpvalue)
                        end = time.perf_counter()
                        print("--- Elapsed time (MREACH - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                else:
                    raise ValueError("{} is not a legal KeyplayerAttribute".format(key_player))

                kp_nodes = self.__utils.get_node_names(go[0])
                kp_value = go[1]
                self.results[key_player] = (starting_value, kp_nodes, kp_value)
                # print(self.results)

            else:
                if not key_player:
                    raise ValueError("list must contain at least one KeyplayerAttribute")

                for k in key_player:
                    if not isinstance(k, _KeyplayerAttribute):
                        raise ValueError("{} is not a KeyplayerAttribute".format(k))

                    starting_value = None

                    if k == _KeyplayerAttribute.F:
                        starting_value = KeyPlayer(graph=self.__graph).F()
                        go = GreedyOptimization(graph=self.__graph).optimize_kpp_neg(kpp_size=kpsize,
                                                                                     kpp_type=k)  # return a tuple(kp nodes, kpvalue

                    elif k == _KeyplayerAttribute.DF:
                        starting_value = KeyPlayer(graph=self.__graph).DF()
                        go = GreedyOptimization(graph=self.__graph).optimize_kpp_neg(kpp_size=kpsize,
                                                                                     kpp_type=k)  # return a tuple(kp nodes, kpvalue)

                    elif k == _KeyplayerAttribute.DR:
                        go = GreedyOptimization(graph=self.__graph).optimize_kpp_pos(kpp_size=kpsize,
                                                                                     kpp_type=k)  # return a tuple(kp nodes, kpvalue)

                    elif k == _KeyplayerAttribute.MREACH:
                        if not isinstance(m, int) or m <= 0:
                            raise ValueError("m must be specified for MREACH and be a positive integer")
                        else:
                            go = GreedyOptimization(graph=self.__graph).optimize_kpp_pos(kpp_size=kpsize,
                                                                                         kpp_type=k,
                                                                                         m=m)  # return a tuple(kp nodes, kpvalue)
                    else:
                        raise ValueError("{} is not a legal KeyplayerAttribute".format(k))

                    kp_nodes = self.__utils.get_node_names(go[0])
                    kp_value = go[1]
                    self.results[k] = (starting_value, kp_nodes, kp_value)

    def run_bruteforce(self, key_player, kpsize: int, m=None):
        """
        **[EXPAND]**
        
        :param key_player:
        :param kpsize:
        :param m:
        :return:
        """
        if not (isinstance(kpsize, int)) or kpsize <= 0:
            raise ValueError("kp must contain at least one element")

        if not isinstance(key_player, (list, _KeyplayerAttribute)):
            raise WrongArgumentError("kp must be a KeyplayerAttribute or a list of KeyplayerAttribute(s)")

        else:

            self.results["algorithm"] = "Brute-Force"
            # greedy optimization for the KeyPlayerAttribuite
            if isinstance(key_player, _KeyplayerAttribute):
                starting_value = None

                if key_player == _KeyplayerAttribute.F:
                    starting_value = KeyPlayer(graph=self.__graph).F()
                    start = time.perf_counter()
                    go = BruteforceSearch(graph=self.__graph).bruteforce_fragmentation(kpp_size=kpsize,kpp_type=key_player)  # return a tuple(kp nodes, kpvalue)
                    end = time.perf_counter()
                    print("--- Elapsed time (F - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                elif key_player == _KeyplayerAttribute.DF:
                    start = time.perf_counter()
                    starting_value = KeyPlayer(graph=self.__graph).DF()
                    go = BruteforceSearch(graph=self.__graph).bruteforce_fragmentation(kpp_size=kpsize,
                                                                                 kpp_type=key_player)  # return a tuple(kp nodes, kpvalue)
                    end = time.perf_counter()
                    print("--- Elapsed time (DF - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                elif key_player == _KeyplayerAttribute.DR:
                    start = time.perf_counter()
                    go = BruteforceSearch(graph=self.__graph).bruteforce_reachability(kpp_size=kpsize,
                                                                                 kpp_type=key_player)  # return a tuple(kp nodes, kpvalue)
                    end = time.perf_counter()
                    print("--- Elapsed time (dR - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                elif key_player == _KeyplayerAttribute.MREACH:
                    if not isinstance(m, int) or m <= 0:
                        raise ValueError("m must be specified for MREACH and be a positive integer")
                    else:
                        start = time.perf_counter()
                        go = BruteforceSearch(graph=self.__graph).bruteforce_reachability(kpp_size=kpsize,
                                                                                     kpp_type=key_player,
                                                                                     m=m)  # return a tuple(kp nodes, kpvalue)
                        end = time.perf_counter()
                        print("--- Elapsed time (MREACH - GREEDY OPTIMIZATION): {:.2f} seconds ---".format(end - start))

                else:
                    raise ValueError("{} is not a legal KeyplayerAttribute".format(key_player))

                kp_nodes = self.__utils.get_node_names(go[0])
                kp_value = go[1]
                self.results[key_player] = (starting_value, kp_nodes, kp_value)
                # print(self.results)

            else:
                if not key_player:
                    raise ValueError("list must contain at least one KeyplayerAttribute")

                for k in key_player:
                    if not isinstance(k, _KeyplayerAttribute):
                        raise ValueError("{} is not a KeyplayerAttribute".format(k))

                    starting_value = None

                    if k == _KeyplayerAttribute.F:
                        starting_value = KeyPlayer(graph=self.__graph).F()
                        go = BruteforceSearch(graph=self.__graph).bruteforce_fragmentation(kpp_size=kpsize,
                                                                                     kpp_type=k)  # return a tuple(kp nodes, kpvalue

                    elif k == _KeyplayerAttribute.DF:
                        starting_value = KeyPlayer(graph=self.__graph).DF()
                        go = BruteforceSearch(graph=self.__graph).bruteforce_fragmentation(kpp_size=kpsize,
                                                                                     kpp_type=k)  # return a tuple(kp nodes, kpvalue)

                    elif k == _KeyplayerAttribute.DR:
                        go = BruteforceSearch(graph=self.__graph).bruteforce_reachability(kpp_size=kpsize,
                                                                                     kpp_type=k)  # return a tuple(kp nodes, kpvalue)

                    elif k == _KeyplayerAttribute.MREACH:
                        if not isinstance(m, int) or m <= 0:
                            raise ValueError("m must be specified for MREACH and be a positive integer")
                        else:
                            go = BruteforceSearch(graph=self.__graph).bruteforce_reachability(kpp_size=kpsize,
                                                                                         kpp_type=k,
                                                                                         m=m)  # return a tuple(kp nodes, kpvalue)
                    else:
                        raise ValueError("{} is not a legal KeyplayerAttribute".format(k))

                    kp_nodes = self.__utils.get_node_names(go[0])
                    kp_value = go[1]
                    self.results[k] = (starting_value, kp_nodes, kp_value)

    def get_results(self):
        '''

        :return: self.results, a dictionary of key player results
        '''
        if self.results:
            return self.results
        else:
            raise ValueError("one or more Key Player metrics must be computed")