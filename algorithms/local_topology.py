"""
Calculator of local properties of graphs
"""

# external libraries
from enum import Enum
from igraph import Graph
from algorithms import global_topology
from exceptions.wrong_argument_error import WrongArgumentError
from utils.graph_utils import GraphUtils
from config import *

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "14 November 2016"
__license__ = u"""
  Copyright (C) 20016-2017  Tommaso Mazza <t,mazza@css-mendel.it>
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


class _LocalAttribute(Enum):
    degree = 0
    betweenness = 1
    clustering_coefficient = 2
    closeness = 3
    eccentricity = 4
    shortest_path = 5
    radiality = 6
    radiality_reach = 7
    eigenvector_centrality = 8
    pagerank = 9


class LocalTopology:
    """
    Calculator of local properties of graphs **[EXPAND?]**
    """

    __graph = None
    """:type: Graph"""
    logger = None
    """:type: Logger"""

    def __init__(self, graph):
        """
        Initializes a graph for local properties calculation
        
        :param Graph graph: Graph provided in input
        :raises IllegalGraphSizeError: if graph does not contain vertices or edges
        """
        self.logger = log

        self.__graph_utils = GraphUtils(graph=graph)
        self.__graph_utils.graph_checker()

        self.__graph = graph

    def get_graph(self) -> Graph:
        """
        Returns the graph
        :return: - A Graph data structure
        """
        return self.__graph

    def set_graph(self, graph, deepcopy=False):
        """
        Replaces the internal graph object with a new one
        
        :param igraph.Graph graph: igraph.Graph object provided in input
        :param bool deepcopy: Flag determining shallow or deep copy of attributes of the graph
        """
        if not deepcopy:
            for elem in graph.attributes():
                del graph[elem]
        self.__graph = graph

    def degree(self, index_list=None, recalculate=False) -> list:
        """
        Computes the degree of every node in the graph, or of a specified list of nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the degree is recalculated regardless if it had been already computed
        :return: - A list containing the degree values of the specified node indices. If an index is not specified, it returns a list of degree values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        """
        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the degree of nodes {}".format(index_list))

            for i in index_list:
                if recalculate or _LocalAttribute.degree.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.degree.name] is None:
                    self.__graph.vs[i][_LocalAttribute.degree.name] = self.__graph.degree(vertices=i)
            return self.__graph.vs.select(index_list)[_LocalAttribute.degree.name]

        else:

            if recalculate or _LocalAttribute.degree.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.degree.name]:
                self.logger.info("Calculating the degree of all nodes")
                self.__graph.vs[_LocalAttribute.degree.name] = self.__graph.degree(self.__graph.vs.indices)

            return self.__graph.vs[_LocalAttribute.degree.name]

    def betweenness(self, index_list=None, recalculate=False):
        """
        Computes the betweenness of every node in the graph, or of a specified list of nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the betweenness is recalculated regardless if it had been already computed
        :return: - A list containing the betweenness values of the specified node indices. If an index is not specified, it returns a list of betweenness values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        """

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the betweenness of nodes {}".format(index_list))
            for i in index_list:
                if recalculate or _LocalAttribute.betweenness.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.betweenness.name] is None:
                    self.__graph.vs[i][_LocalAttribute.betweenness.name] = self.__graph.betweenness(vertices=i,
                                                                                                    directed=False)
                pass

            return self.__graph.vs.select(index_list)[_LocalAttribute.betweenness.name]

        else:

            if recalculate or _LocalAttribute.betweenness.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.betweenness.name] is None:
                self.logger.info("Calculating the betweenness of all nodes")
                self.__graph.vs[_LocalAttribute.betweenness.name] = self.__graph.betweenness(directed=False)

            return self.__graph.vs[_LocalAttribute.betweenness.name]

    def clustering_coefficient(self, index_list=None, recalculate=False):
        """
        Computes the clustering coefficient of every node in the graph, or of a specified list of nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the clustering coefficient is recalculated regardless if it had been already computed
        :return: - A list containing the clustering coefficient values of the specified node indices. If an index is not specified, it returns a list of clustering coefficient values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        """
        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the clustering coefficient of nodes {}".format(index_list))
            for i in index_list:
                if recalculate or _LocalAttribute.clustering_coefficient.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.clustering_coefficient.name] is None:
                    self.__graph.vs[i][
                        _LocalAttribute.clustering_coefficient.name] = self.__graph.transitivity_local_undirected(
                        mode="zero", vertices=i)
            return self.__graph.vs.select(index_list)[_LocalAttribute.clustering_coefficient.name]

        else:

            if recalculate or _LocalAttribute.clustering_coefficient.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.clustering_coefficient.name] is None:
                self.logger.info("Calculating the clustering coefficient of all nodes")
                self.__graph.vs[
                    _LocalAttribute.clustering_coefficient.name] = self.__graph.transitivity_local_undirected(
                    mode="zero")

            return self.__graph.vs[_LocalAttribute.clustering_coefficient.name]

    def closeness(self, index_list=None, recalculate=False):
        """
        Computes the closeness of every node in the graph, or of a specified list of nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the closeness is recalculated regardless if it had been already computed
        :return: - A list containing the closeness values of the specified node indices. If an index is not specified, it returns a list of closeness values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        """

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the closeness of nodes {}".format(index_list))
            for i in index_list:
                if recalculate or _LocalAttribute.closeness.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.closeness.name] is None:
                    self.__graph.vs[i][_LocalAttribute.closeness.name] = self.__graph.closeness(vertices=i)
            return self.__graph.vs.select(index_list)[_LocalAttribute.closeness.name]

        else:

            if recalculate or _LocalAttribute.closeness.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.closeness.name] is None:
                self.logger.info("Calculating the closeness of all nodes")
                self.__graph.vs[_LocalAttribute.closeness.name] = self.__graph.closeness()

            return self.__graph.vs[_LocalAttribute.closeness.name]

    def eccentricity(self, index_list=None, recalculate=False):
        """
        Computes the eccentricity of every node in the graph, or of a specified list of nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the eccentricity is recalculated regardless if it had been already computed
        :return: - A list containing the eccentricity values of the specified node indices. If an index is not specified, it returns a list of eccentricity values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        """

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the eccentricity of nodes {}".format(index_list))
            for i in index_list:
                if recalculate or _LocalAttribute.eccentricity.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.eccentricity.name] is None:
                    self.__graph.vs[i][_LocalAttribute.eccentricity.name] = self.__graph.eccentricity(vertices=i)
            return self.__graph.vs.select(index_list)[_LocalAttribute.eccentricity.name]

        else:

            if recalculate or _LocalAttribute.eccentricity.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.eccentricity.name] is None:
                self.logger.info("Calculating the eccentricity of all nodes")
                self.__graph.vs[_LocalAttribute.eccentricity.name] = self.__graph.eccentricity()

            return self.__graph.vs[_LocalAttribute.eccentricity.name]

    def shortest_path_igraph(self, index_list=None, recalculate=False):
        """
        Calculates the shortest path lengths between all (or a specified list of) nodes in the graph and every other nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the eccentricity is recalculated regardless if it had been already computed
        :return: - A list containing the shortest paths of the specified node indices. If an index is not specified, it returns a list of shortest paths from all nodes of the graph
        :raises WrongArgumentError: When the input node index does not exist
        """

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the shortest paths from nodes {}".format(index_list))
            for i in index_list:
                if recalculate or _LocalAttribute.shortest_path.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.shortest_path.name] is None:
                    self.__graph.vs[i][_LocalAttribute.shortest_path.name] = self.__graph.shortest_paths(source=i)[0]

            return self.__graph.vs.select(index_list)[_LocalAttribute.shortest_path.name]

        else:
            if recalculate or _LocalAttribute.shortest_path.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.shortest_path.name] is None:
                self.logger.info("Calculating the shortest paths from all nodes")
                self.__graph.vs[_LocalAttribute.shortest_path.name] = self.__graph.shortest_paths()

            return self.__graph.vs[_LocalAttribute.shortest_path.name]

    def radiality(self, index_list=None, recalculate=False):
        """
        Computes the radiality of every node in the graph, or of a specified list of nodes. The radiality of a node v
        is calculated by computing the shortest path between the node v and all other nodes in the graph. The value
        of each path is then subtracted by the value of the diameter + 1 and the resulting values are summated.
        Finally, the obtained value is divided for the number of nodes -1 (n-1).
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the eccentricity is recalculated regardless if it had been already computed
        :return: - A list containing the radiality values of the specified node indices. If an index is not specified, it returns a list of radiality values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        """

        gt = global_topology.GlobalTopology(graph=self.__graph)
        diameter = gt.diameter()
        num_nodes = self.__graph.vcount()

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)

            self.logger.info("Calculating the radiality of nodes {}".format(index_list))
            shortest_path_lengths = self.shortest_path_igraph(recalculate=True)

            for i in index_list:
                if recalculate or _LocalAttribute.radiality.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.radiality.name] is None:

                    partial_sum = 0

                    for sp_length in shortest_path_lengths[i]:
                        if sp_length != 0:  # skip itself
                            partial_sum += diameter + 1 - sp_length
                    self.__graph.vs[i][_LocalAttribute.radiality.name] = float(partial_sum) / (num_nodes - 1)

            return self.__graph.vs.select(index_list)[_LocalAttribute.radiality.name]

        else:
            shortest_path_lengths = self.shortest_path_igraph(recalculate=True)
            self.logger.info("Calculating the radiality of all nodes")

            for i in self.__graph.vs.indices:
                if recalculate or _LocalAttribute.radiality.name not in self.__graph.vs().attributes() \
                        or None in self.__graph.vs()[_LocalAttribute.radiality.name]:

                    partial_sum = 0

                    for sp_length in shortest_path_lengths[i]:
                        if sp_length != 0:  # skip itself
                            partial_sum += diameter + 1 - sp_length
                    self.__graph.vs[i][_LocalAttribute.radiality.name] = float(partial_sum) / (num_nodes - 1)

            return self.__graph.vs[_LocalAttribute.radiality.name]

    def radiality_reach(self, index_list=None, recalculate=False):
        """
        Computes a modified version of the radiality in which the radiality is computer for each component and then
        weighted over the proportion of nodes present in that component with respect
        to the total number of nodes in the graph. This ensures that the radiality **[EXPAND]**
        
        :param index_list:
        :param recalculate:
        :return:
        """

        comps = self.__graph.components()
        total_nodes = self.__graph.vcount()

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)

            self.logger.info("Calculating the radiality reach of nodes {}".format(index_list))

            for i in index_list:
                # print(i)

                if recalculate or _LocalAttribute.radiality_reach.name not in self.__graph.vs[i].attributes() \
                        or self.__graph.vs[i][_LocalAttribute.radiality_reach.name] is None:

                    for ind, c in enumerate(comps): #find the corresponding index of the component
                        if i in c:
                            subg_ind = c.index(i)
                            comp_ind = ind
                            break

                    subg = self.__graph.induced_subgraph(vertices=comps[comp_ind])

                    if subg.ecount() > 0:  # control that the component is not made of node isolates

                        gt = global_topology.GlobalTopology(graph=subg)
                        num_nodes = subg.vcount()
                        diameter = gt.diameter()

                        shortest_path_lengths = subg.shortest_paths(source=subg_ind)[0]
                        #print(shortest_path_lengths)

                        partial_sum = 0

                        for sp_length in shortest_path_lengths:
                            if sp_length != 0:  # skip itself
                                partial_sum += diameter + 1 - sp_length


                        # print(float(partial_sum) / (num_nodes - 1))
                        # print((num_nodes/total_nodes))
                        radiality_reach = (float(partial_sum) / (num_nodes - 1)) * (num_nodes/total_nodes)
                        # print(radiality_reach)

                        self.__graph.vs[i][_LocalAttribute.radiality_reach.name] = radiality_reach
                    else:
                        self.__graph.vs[i][_LocalAttribute.radiality_reach.name] = 0 #when the node is an isolate, the radiality reach of that node is 0
                        #todo discuss this with tommaso  (especially for average radiality reach)

            return self.__graph.vs.select(index_list)[_LocalAttribute.radiality_reach.name]

        else:
            self.logger.info("Calculating the radiality_reach of all nodes")
            #print(None in self.__graph.vs()[LocalAttribute.radiality_reach.name])

            if recalculate or _LocalAttribute.radiality_reach.name not in self.__graph.vs().attributes() \
                    or None in self.__graph.vs()[_LocalAttribute.radiality_reach.name]:

                for ind, elem in enumerate(comps):

                    subg = self.__graph.induced_subgraph(vertices=elem)

                    if subg.ecount() > 0: #control that the component is not made of node isolate#

                        gt = global_topology.GlobalTopology(graph=subg)

                        num_nodes = subg.vcount()

                        diameter = gt.diameter()

                        shortest_path_lengths = subg.shortest_paths()
                        #print (shortest_path_lengths[:3])

                        for i in subg.vs.indices:

                                partial_sum = 0

                                for sp_length in shortest_path_lengths[i]:
                                    if sp_length != 0:  # skip itself
                                        partial_sum += diameter + 1 - sp_length

                                correct_ind = self.__graph.vs(comps[ind][i])[0].index
                                # print(float(partial_sum) / (num_nodes - 1))
                                # print(num_nodes / total_nodes)
                                radiality_reach = (float(partial_sum) / (num_nodes - 1)) * (num_nodes / total_nodes)

                                self.__graph.vs[correct_ind][_LocalAttribute.radiality_reach.name] = radiality_reach

                    else:
                        self.__graph.vs[elem[0]][_LocalAttribute.radiality_reach.name] = 0

            return self.__graph.vs[_LocalAttribute.radiality_reach.name]

    def eigenvector_centrality(self, scaled=False, recalculate=False, index_list=None):
        """
        Calculates the eigenvector centrality between all  nodes in the graph using igraph builtin operators (Igraph.evc)
        
        :param bool scaled: whether to normalize the eigenvector centrality (1/eigenvector value)
        :param bool recalculate: If True, the eccentricity is recalculated regardless if it had been already computed
        :return: A list containing the radiality values of the specified node indices. If an index is not specified, it returns a list of radiality values for all nodes contained in the graph
        :raises WrongArgumentError: if the input is not an igraph Graph object
        """

        if not isinstance(scaled, bool):
            raise ValueError("\"scaled\" parameter is not a boolean")

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)
            self.logger.info("Calculating the radiality of nodes {}".format(index_list))
            ec = Graph.evcent(self.__graph, directed=False, scale=scaled)
            for i in index_list:
                if recalculate or _LocalAttribute.eigenvector_centrality.name not in self.__graph.vs[i].attributes() or \
                                self.__graph.vs[i][_LocalAttribute.eigenvector_centrality.name] is None:
                    self.__graph.vs(i)[_LocalAttribute.eigenvector_centrality.name] = ec[i]

            return self.__graph.vs.select(index_list)[_LocalAttribute.eigenvector_centrality.name]

        else:
            if recalculate or _LocalAttribute.eigenvector_centrality.name not in self.__graph.vs.attributes() or None in \
                    self.__graph.vs()[_LocalAttribute.eigenvector_centrality.name]:
                self.logger.info("Calculating the eigenvector centrality of all nodes")
                ec = Graph.evcent(self.__graph, directed=False, scale=scaled)
                for i, elem in enumerate(ec):
                    self.__graph.vs()[_LocalAttribute.eigenvector_centrality.name] = elem

            return self.__graph.vs[_LocalAttribute.eigenvector_centrality.name]

    def pagerank(self, index_list=None, weights=None, damping=0.85, recalculate=False):
        """
        Computes the pagerank index of every node in the graph, or of a specified list of nodes
        
        :param list[int] index_list: List of node indices
        :param bool recalculate: If True, the pagerank is recalculated regardless if it had been already computed
        :param int damping: a proposed damping factor
        :param list[int,float] weights: a list of edge weights to apply to the pagerank algorithm
        :return: A list containing the pagerank values of the specified node indices. If an index is not specified, it returns a list of pagerank values for all nodes contained in the graph
        :raises WrongArgumentError: When the input node index does not exist
        :raises IllegalSizeArgument: if the weights length does not match the total size of the nodes
        """

        if weights:
            if not isinstance(weights, list):
                raise WrongArgumentError("weights must be a list")

            if len(weights) != self.__graph.ecount():
                raise AttributeError("weights must have the same length of number of edges")

            for w in weights:
                try:
                    w = float(w)

                except TypeError:
                    self.logger.info("weight is {0}, keeping it a {1}".format(w, type(w).__name__))

                except ValueError:
                    self.logger.error("weight is {}, cannot convert to float.")
                    raise WrongArgumentError("one of the weights cannot be converted to float")

        if not isinstance(damping, (int, float)):
            if not damping > 0 or not damping <= 1:
                raise ValueError("Damping must be between 0.1 and 1")

        if index_list is not None:
            self.__graph_utils.check_index_list(index_list=index_list)

            self.logger.info("Calculating the pagerank of nodes {}".format(index_list))

            if recalculate or _LocalAttribute.pagerank.name not in self.__graph.vs(index_list).attributes() or None in \
                    self.__graph.vs(index_list)[_LocalAttribute.pagerank.name]:

                if weights:

                    if damping != 0.85:
                        self.logger.info("using the specified damping factor (default is 0.85)")
                        self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph,
                                                                                        vertices=index_list,
                                                                                        directed=False,
                                                                                        damping=damping,
                                                                                        weights=weights)

                    else:

                        self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph, directed=False,
                                                                                        vertices=index_list,
                                                                                        weights=weights)

                else:
                    if damping != 0.85:
                        self.logger.info("using the specified damping factor (default is 0.85)")
                        self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph,
                                                                                        vertices=index_list,
                                                                                        directed=False,
                                                                                        damping=damping)
                    else:
                        self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph,
                                                                                        vertices=index_list,
                                                                                        directed=False)

            return self.__graph.vs.select(index_list)[_LocalAttribute.pagerank.name]

        else:
            if recalculate or _LocalAttribute.pagerank.name not in self.__graph.vs.attributes() or None in \
                    self.__graph.vs()[_LocalAttribute.pagerank.name]:

                self.logger.info("Calculating the pagerank for all nodes")

                if weights:

                    if len(weights) != self.__graph.ecount():
                        raise ValueError("Weights list does not matches the total number of nodes")

                    else:
                        if damping != 0.85:
                            self.logger.info("using the specified damping factor (default is 0.85)")
                            self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph, directed=False,
                                                                                            damping=damping,
                                                                                            weights=weights)
                        else:
                            self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph, directed=False,
                                                                                            weights=weights)

                else:
                    if damping != 0.85:
                        self.logger.info("using the specified damping factor (default is 0.85)")
                        self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph, directed=False,
                                                                                        damping=damping)
                    else:
                        self.__graph.vs[_LocalAttribute.pagerank.name] = Graph.pagerank(self.__graph, directed=False)

            return self.__graph.vs[_LocalAttribute.pagerank.name]