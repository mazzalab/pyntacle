__author__ = u"Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.3"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"20/07/2020"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t,mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """

from config import *
from tools.enums import CmodeEnum
from algorithms.greedy_optimization import GreedyOptimization
from algorithms.bruteforce_search import BruteforceSearch
from algorithms.stochastic_gradient_descent import StochasticGradientDescent
from internal.timeit import timeit
from tools.enums import KpposEnum, KpnegEnum, GroupCentralityEnum, GroupDistanceEnum
from algorithms.keyplayer import KeyPlayer
from algorithms.local_topology import LocalTopology
from igraph import Graph


class InfoWrapper:
    r"""
    Wrapper for the Group centrality methods that compute indices for a given set of nodes,
    to pass proper data structures to the Pyntacle command line.
    """

    logger = None

    def __init__(self, graph: Graph, nodes: str or list):
        r"""
        Initialize the graph object.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param nodes: either a single node or a lis of nodes (the vertex ``name`` attribute(s)) belonging to the graph
        """

        self.logger = log
        self.logger.info(u"Initializing group search info wrapper")
        self.method = None  # this will store the class that will be used to compute group centrality
        self.graph = graph

        if isinstance(nodes, str):
            nodes = [nodes]

        else:
            if not isinstance(nodes, list) and not all(isinstance(x, str) for x in nodes):
                raise ValueError(u"'nodes' are not a string or a list of strings")

        if not all(x in self.graph.vs()["name"] for x in nodes):
            raise KeyError(u"One of the nodes not in the vertex ['name'] attribute. "
                           "Are the node names are correct?")
        self.nodes = nodes

        # initialize graph utility class
        self.results = {}  # dictionary that will store results

    def set_graph(self, graph: Graph):
        """
        replace the original graph with another one
        """

        if not isinstance(graph, Graph):
            raise TypeError("'graph is not an igraph.Graph object'")

        self.graph = graph

    def set_nodes(self, nodes: str or list):
        if isinstance(nodes, str):
            nodes = [nodes]

        else:
            if not isinstance(nodes, list) and not all(isinstance(x, str) for x in nodes):
                raise ValueError(u"'nodes' are not a string or a list of strings")

        if not all(x in self.graph.vs()["name"] for x in nodes):
            raise KeyError(u"One of the nodes not in the vertex ['name'] attribute. "
                           "Are the node names are correct?")
        self.nodes = nodes

    def reset_results(self):
        """reset the results dictionary"""

        self.results = {}

    def get_results(self) -> dict:
        r"""
        Returns a dictionary with the queried KP metrics for the given set of nodes.

        :return dict: results: a dictionary, each ``key`` being the name of the group index queried and ``value`` being a list. The first element of a list is the queried set of nodes, the second element is the corresponding KP value.
        """
        return self.results

    @timeit
    def run_reachability(self, kp_type: KpposEnum, m=None, cmode=CmodeEnum.igraph):
        r"""
        Run a single positive key player metric on a single node or a set of nodes, adds everything to an ordered dictionary.

        :param KpposEnum kp_type: one of the positive key player indices of interest defined in :class:`tools.enums.KpposEnum`
        :param int m: if ``kp_type`` is the m-reach, specifies the maximum distance that will be used to compute mreach. Must be a positive integer.
        """
        self.method = KeyPlayer

        if not isinstance(kp_type, KpposEnum):
            raise TypeError(
                u"Metric must be ones of the Kppos enums in `tools.enums`, {} found".format(type(kp_type).__name__))

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError(u"'m' must be specified for m-reach")
            elif not isinstance(m, int) or m <= 0:
                raise ValueError(u"'m' must be a positive integer")

        sys.stdout.write(u"Computing {0} for nodes ({1})\n".format(kp_type.name, ", ".join(self.nodes)))

        if kp_type == KpposEnum.dR:
            single_result = self.method.dR(graph=self.graph, nodes=self.nodes, cmode=cmode)

        else:
            single_result = self.method.mreach(graph=self.graph, nodes=self.nodes, m=m, cmode=cmode)

        self.results[kp_type.name] = [self.nodes, single_result]
        self.logger.info(
            u"Positive key player computation for {} completed, results are in the 'results' dictionary".format(
                kp_type.name))

    @timeit
    def run_fragmentation(self, kp_type: KpnegEnum, cmode=CmodeEnum.igraph):
        r"""
        Run a single negative key player metrics for a given  node or a set of nodes and store them into a dictionary
        that is then passed to the Pyntacle command line utilities

        :param KpnegEnum kp_type: one of the KPPNEGchoices defined in :class:`tools.enums.KpnegEnum`
        """
        self.method = KeyPlayer

        if not isinstance(kp_type, KpnegEnum):
            raise TypeError(
                "'kp_type' must be ones of the 'KPNEGchoices' metrics, {} found".format(type(kp_type).__name__))

        copy = self.graph.copy()
        copy.delete_vertices(self.nodes)

        sys.stdout.write(
            u"Computing {0} for nodes ({1})\n".format(kp_type.name, ", ".join(self.nodes)))

        if kp_type == KpnegEnum.dF:
            single_result = self.method.dF(graph=copy, cmode=cmode)

        else:
            single_result = self.method.F(graph=copy)

        self.results[kp_type.name] = [self.nodes, single_result]
        self.logger.info(u"Kp pos search completed, results are in the 'results' dictionary")

    @timeit
    def run_groupcentrality(self, gr_type: GroupCentralityEnum, cmode: CmodeEnum = CmodeEnum.igraph,
                            gr_distance: GroupDistanceEnum = GroupDistanceEnum.minimum):
        r"""
        Wraps the group centrality methods in :class:`algorithms.local_topology.LocalTopology`, runs them and store the
        result for a subset of nodes into a dictionary, to be reused by the groupcentrality command line for Pyntacle
        and by Octopus.

        :param GroupCentralityEnum gr_type: one of the group centralityy metrics defined in :class:`tools.enums.GroupCentralityEnum`
        :param cmode: one of the possible implementations defined in :class:`tools.enums.GroupCentralityEnum`
        :param gr_distance:
        """
        self.method = LocalTopology
        if not isinstance(gr_type, GroupCentralityEnum):
            raise TypeError(u"'gr_type' must be ones of the GroupCentrality enums in `tools.enums`, {} found".format(
                type(gr_type).__name__))

        if gr_type == GroupCentralityEnum.group_closeness and not isinstance(gr_distance, GroupDistanceEnum):
            raise TypeError(
                "`gr_distance` must be one of the GroupDistanceEnum, {} found".format(type(gr_distance).__name__))

        sys.stdout.write(
            u"Computing {0} for nodes ({1})\n".format(gr_type.name.replace("_", " "), ", ".join(self.nodes)))

        if gr_type == GroupCentralityEnum.group_closeness:
            single_result = self.method.group_closeness(graph=self.graph, nodes=self.nodes,
                                                        cmode=cmode, distance=gr_distance)

        elif gr_type == GroupCentralityEnum.group_degree:
            single_result = self.method.group_degree(graph=self.graph, nodes=self.nodes)

        else:
            single_result = self.method.group_betweenness(graph=self.graph, nodes=self.nodes)

        if gr_type == GroupCentralityEnum.group_closeness:
            self.results["_".join([gr_type.name, gr_distance.name])] = [self.nodes, single_result]
        else:
            self.results[gr_type.name] = [self.nodes, single_result]
        self.logger.info(
            u"Group centrality computation for {} completed, results are in the 'results' dictionary".format(
                gr_type.name))


class BFWrapper:
    r"""
    Convenient wrapper around the brute-force search methods in algorithms.bruteforce to pass properly formatted results
    to the Pyntacle command line
    """

    def __init__(self, graph: Graph):
        r"""
        Initialize the graph object
        :param graph:
        """
        self.logger = log
        self.bf = BruteforceSearch
        self.graph = graph
        self.results = {}  # dictionary that will store results

    def set_graph(self, graph: Graph):
        """
        replace the original graph with another one
        """

        if not isinstance(graph, Graph):
            raise TypeError("'graph is not an igraph.Graph object'")

        self.graph = graph

    def reset_results(self):
        """reset the results dictionary"""

        self.results = {}

    def get_results(self) -> dict:
        r"""
        Returns a dictionary with the queried KP metrics for the given set of nodes.

        :return dict: results: a dictionary, each ``key`` being the name of the group index queried and ``value`` being a list. The first element of a list is the queried set of nodes, the second element is the corresponding KP value.
        """
        return self.results

    @timeit
    def run_fragmentation(self, k: int, kp_type: KpnegEnum, cmode=CmodeEnum.igraph, nprocs=1):
        r"""
        Wrapper around the brute-force search that stores the results for the KP-Neg metrics in
        the "results" dictionary

        :param cmode:
        :param nprocs: number of processors to be spawn
        :param int k: size of the kpp-set to be found
        :param KpnegEnum kp_type: on of the KPNEGchoices enumerators stored in internal.enums
        """
        if not nprocs:
            nprocs = 1
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'k' must be a positive integer of size 1")

        if not isinstance(kp_type, KpnegEnum):
            raise TypeError(u"'kp_type' must be one of the KPPNEGchoices options available")

        bf_results = self.bf.fragmentation(graph=self.graph, k=k, metric=kp_type, cmode=cmode, nprocs=nprocs)
        self.results[kp_type.name] = [bf_results[0], bf_results[1]]

    @timeit
    def run_reachability(self, k: int, kp_type: KpposEnum, m=None, cmode=CmodeEnum.igraph, nprocs=1):
        r"""
        Wrapper around the brute-force search module that stores the results for KPPOS metrics

        :param int k: size of the kpp-set to be found
        :param KpposEnum kp_type: on of the KPPOSchoices enumerators stored in internal.enums
        :param int m: for the "mreach" metrics, a positive integer greater than one representing the maximum distance for mreach
        """
        if not nprocs:
            nprocs = 1
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'kpp_size' must be a positive integer of size 1")

        if not isinstance(kp_type, KpposEnum):
            raise TypeError(u"'kp_type' must be one of the KPPNEGchoices options available")

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError(u"'m' must be a specified for m-reach ")
            elif not isinstance(m, int) or m <= 0:
                raise ValueError(u"'m' must be a positive integer equal or greater than one ")

        bf_results = self.bf.reachability(graph=self.graph, k=k, metric=kp_type, m=m, cmode=cmode, nprocs=nprocs)
        self.results[kp_type.name] = [bf_results[0], bf_results[1]]

    @timeit
    def run_groupcentrality(self, k: int, gr_type: GroupCentralityEnum, cmode: CmodeEnum = CmodeEnum.igraph,
                            nprocs: int = 1, distance: GroupDistanceEnum = GroupDistanceEnum.minimum):
        r"""
        Wrapper around the brute-force search module that stores the results for GroupCentrality metrics

        :param k:
        :param gr_type:
        :param cmode:
        :param nprocs:
        :param distance:
        """
        if not nprocs:
            nprocs = 1
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'k' must be a positive integer equal or greater than 1")

        if not isinstance(gr_type, GroupCentralityEnum):
            raise TypeError(u"'gr_type' must be one of the KPPNEGchoices options available")

        if gr_type == GroupCentralityEnum.group_closeness:
            if not isinstance(distance, GroupDistanceEnum):
                raise TypeError(
                    u"'distance' is not one of the GroupDistanceEnums,{} found".format(type(distance).__name__))

        bf_results = self.bf.group_centrality(graph=self.graph, k=k, metric=gr_type, cmode=cmode, nprocs=nprocs)

        if gr_type == GroupCentralityEnum.group_closeness:
            self.results["_".join([gr_type.name, distance.name])] = [bf_results[0], bf_results[1]]
        else:
            self.results[gr_type.name] = [bf_results[0], bf_results[1]]


class GOWrapper:
    r"""
    Wrapper for the greedy optimization, to pass properly formatted data structures to the Pyntacle Command Line
    after a greedy optimization run
    """

    logger = None

    def __init__(self, graph: Graph):
        """
        """
        self.go = GreedyOptimization  # initialize an empty GreedyOptimization class
        # initialize graph utility class
        self.graph = graph
        self.logger = log
        self.results = {}  # dictionary that will store results

    def set_graph(self, graph: Graph):
        """
        replace the original graph with another one
        """

        if not isinstance(graph, Graph):
            raise TypeError("'graph is not an igraph.Graph object'")

        self.graph = graph

    def reset_results(self):
        """reset the rfesults dictionary"""

        self.results = {}

    def get_results(self) -> dict:
        r"""
        returns the dictionary with the queried KP metrics and the set of nodes found by greedy optimization, along with
        the corresponding value.

        :return dict: results: a dictionary with the name of the KP metrics queried as keys and a list for each kp metrics, The first element of a list ifs the queried set of nodes, the second element is the corresponding KP value
        """
        return self.results

    @timeit
    def run_fragmentation(self, k: int, kp_type: KpnegEnum, cmode=CmodeEnum.igraph):
        r"""
        Wrapper around the Greedy Optimization Module that stores the greedy optimization results for KPPOS metrics in
        the "results" dictionary.

        :param int k: size of the kpp-set to be found
        :param KpnegEnum kp_type: on of the KPNEGchoices enumerators stored in internal.enums
        """

        if not isinstance(k, int) or k < 1:
            raise ValueError(u"\k' must be a positive integer of size 1")

        if not isinstance(kp_type, KpnegEnum):
            raise TypeError(u"'kp_type' must be one of the KPPNEGchoices options available")

        go_results = self.go.fragmentation(graph=self.graph, k=k, metric=kp_type, cmode=cmode)
        self.results[kp_type.name] = [go_results[0][0], go_results[1]]

    @timeit
    def run_reachability(self, k: int, kp_type: KpposEnum, m=None, cmode=CmodeEnum.igraph):
        r"""
        Wrapper around the Greedy Optimization Module that stores the greedy optimization results for KPPOS metrics

        :param int k: size of the kpp-set to be found
        :param KpposEnum kp_type: on of the KPPOSchoices enumerators stored in internal.enums
        :param int m: for the "mreach" metrics, a positive integer greatrer than one representing the maximum distance for mreach
        """
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'k' must be a positive integer of size 1")

        if not isinstance(kp_type, KpposEnum):
            raise TypeError(u"'kp_type' must be one of the KpposEnums available in `tools.enums`")

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError(u"'m' must be a specified for computing m-reach")
            elif not isinstance(m, int) or m <= 0:
                raise ValueError(u"'m' must be a positive integer")

        go_results = self.go.reachability(graph=self.graph, k=k, metric=kp_type, m=m, cmode=cmode)

        self.results[kp_type.name] = [go_results[0][0], go_results[1]]

    @timeit
    def run_groupcentrality(self, k: int, gr_type: GroupCentralityEnum, cmode=CmodeEnum.igraph,
                            distance=GroupDistanceEnum.minimum):
        r"""
        
        :param k: 
        :param gr_type:
        :param cmode:
        :param distance:
        """
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'k' must be a positive integer of size 1")

        if not isinstance(gr_type, GroupCentralityEnum):
            raise TypeError(u"'gr_type' must be one of the enumerators available in tools.enums")

        if gr_type == GroupCentralityEnum.group_closeness:
            if not isinstance(distance, GroupDistanceEnum):
                raise TypeError(
                    u"'distance' is not one of the GroupDistanceEnums,{} found".format(type(distance).__name__))

        go_results = self.go.group_centrality(graph=self.graph, k=k, metric=gr_type, cmode=cmode)

        if gr_type == GroupCentralityEnum.group_closeness:
            self.results["_".join([gr_type.name, distance.name])] = [go_results[0][0], go_results[1]]
        else:
            self.results[gr_type.name] = [go_results[0][0], go_results[1]]


class SGDWrapper:
    r"""
    Wrapper for the stochastic gradient descent algorithm, to pass properly formatted data structures to
    the Pyntacle command-line after a run
    """

    logger = None

    def __init__(self, graph: Graph):
        """
        """
        self.sgd = StochasticGradientDescent
        self.graph = graph
        self.logger = log
        self.results = {}

    def set_graph(self, graph: Graph):
        """
        replace the original graph with another one
        """

        if not isinstance(graph, Graph):
            raise TypeError("'graph is not an igraph.Graph object'")

        self.graph = graph

    def reset_results(self):
        """reset the results dictionary"""

        self.results = {}

    def get_results(self) -> dict:
        r"""
        returns the dictionary with the queried KP metrics and the set of nodes found by the
        stochastic gradient descent algorithm, along with the corresponding value.
        :return dict: results: a dictionary with the name of the KP metrics queried as keys and a list for each
        kp metrics. The first element of a list is the queried set of nodes, the second element is the
        corresponding KP value
        """
        return self.results

    @timeit
    def run_fragmentation(self, k: int, kp_type: KpnegEnum, cmode: CmodeEnum, **kwargs):
        r"""
        Wrapper around the stochastic gradient descent module that stores the results for the KP-Pos metrics in
        the sgd_results dictionary.

        :param cmode:
        :param int k: size of the kpp-set to be found
        :param KpnegEnum kp_type: on of the KPNEGchoices enumerators stored in internal.enums
        """

        if not isinstance(k, int) or k < 1:
            raise ValueError(u"\k' must be a positive integer of size greater or equal than 1")

        if not isinstance(kp_type, KpnegEnum):
            raise TypeError(u"'kp_type' must be one of the available KpnegEnum options")

        sgd_results = self.sgd.fragmentation(graph=self.graph, k=k, metric=kp_type, cmode=cmode, **kwargs)
        self.results[kp_type.name] = [sgd_results[0], sgd_results[1]]

    @timeit
    def run_reachability(self, k: int, kp_type: KpposEnum, m: int, cmode: CmodeEnum, **kwargs):
        r"""
        Wrapper around the stochastic gradient descent module that stores the results for KP-POS metrics

        :param cmode:
        :param int k: size of the kpp-set to be found
        :param KpposEnum kp_type: on of the KPPOSchoices enumerators stored in internal.enums
        :param int m: for the "m-reach" metrics, a positive integer greater than one representing the maximum distance
        """
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'k' must be a positive integer of size greater or equal than 1")

        if not isinstance(kp_type, KpposEnum):
            raise TypeError(u"'kp_type' must be one of the KpnegEnum available in `tools.enums`")

        if kp_type == KpposEnum.mreach:
            if not m:
                raise ValueError(u"'m' must be a specified for computing m-reach")
            elif not isinstance(m, int) or m <= 0:
                raise ValueError(u"'m' must be a positive integer")

        sgd_results = self.sgd.reachability(graph=self.graph, k=k, metric=kp_type, m=m, cmode=cmode, **kwargs)

        self.results[kp_type.name] = [sgd_results[0], sgd_results[1]]

    @timeit
    def run_groupcentrality(self, k: int, gr_type: GroupCentralityEnum,
                            distance: GroupDistanceEnum, cmode: CmodeEnum, **kwargs):
        r"""

        :type cmode: object
        :param k:
        :param gr_type:
        :param cmode:
        :param distance:
        """
        if not isinstance(k, int) or k < 1:
            raise ValueError(u"'k' must be a positive integer of size greater or equal than 1")

        if not isinstance(gr_type, GroupCentralityEnum):
            raise TypeError(u"'gr_type' must be one of the enumerators available in tools.enums")

        if gr_type == GroupCentralityEnum.group_closeness:
            if not isinstance(distance, GroupDistanceEnum):
                raise TypeError(
                    u"'distance' is not one of the GroupDistanceEnums,{} found".format(type(distance).__name__))

        sgd_results = self.sgd.group_centrality(graph=self.graph, k=k, metric=gr_type, cmode=cmode, **kwargs)

        if gr_type == GroupCentralityEnum.group_closeness:
            self.results["_".join([gr_type.name, distance.name])] = [sgd_results[0], sgd_results[1]]
        else:
            self.results[gr_type.name] = [sgd_results[0], sgd_results[1]]
