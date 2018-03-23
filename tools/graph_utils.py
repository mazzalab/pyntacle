# external libraries
from config import *
from igraph import Graph
import numpy as np

# pyntacle libraries
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.missing_attribute_error import MissingAttributeError
from exceptions.notagraph_error import NotAGraphError
from exceptions.unsupported_graph_error import UnsupportedGrapherror
from exceptions.wrong_argument_error import WrongArgumentError
from exceptions.multiple_solutions_error import MultipleSolutionsError

'''
a series of generic utilities for an iGraph graph object
'''

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 October 2016"
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
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc.,  51 Franklin Street, Fifth Floor, Boston, MA
  02110-1301 USA
  """


class GraphUtils():
    '''
    A series of methods that can be performed on graph and that can be accessed pretty quickly
    '''

    logger = None
    """:type: Logger"""

    def __init__(self, graph: Graph):
        self.logger = log

        if not isinstance(graph, Graph):  # check that the object is a graph
            raise NotAGraphError("input graph is not a graph")

        if graph.vcount() < 1:
            self.logger.fatal("This graph does not contain vertices")
            raise IllegalGraphSizeError("This graph does not contain vertices")

        elif graph.ecount() < 1:
            self.logger.fatal("This graph does not contain edges")
            raise IllegalGraphSizeError("This graph does not contain edges")

        else:
            self.__graph = graph

    def graph_checker(self):
        """
        **[EXPAND]**
        
        :return:
        """

        if Graph.is_directed(self.__graph):
            raise UnsupportedGrapherror("Input graph is direct, pyntacle supports only undirected graphs")

        if not Graph.is_simple(self.__graph):
            raise UnsupportedGrapherror("Input Graph contains self loops and multiple edges")

        if "name" not in self.__graph.vs().attributes():
            raise KeyError("nodes must have the attribute  \"name\"")
        if not all(isinstance(item, str) for item in self.__graph.vs()["name"]):
            raise TypeError("node \"name\" attribute must be a string")

        if len(set(self.__graph.vs()["name"])) != len(self.__graph.vs()["name"]):
            raise UnsupportedGrapherror("Node names must be unique, check the \"name\" attribute in graph")

    def check_index_list(self, index_list):
        """
        **[EXPAND]**
        
        :param index_list:
        :return:
        """
        self.graph_checker()

        if not isinstance(index_list, list):
            raise ValueError("index list is not a list")

        if len(index_list) < 0:
            raise WrongArgumentError("List is empty")

        for ind in index_list:
            if not isinstance(ind, int):
                raise ValueError("indices must be integers")

        if set(index_list) > set(self.__graph.vs.indices):
            self.logger.error("The input node index '{}' does not exist in the graph".format(index_list))
            raise WrongArgumentError("The input node index '{}' does not exist in the graph".format(index_list))

        return None

    def check_name_list(self, names_list: list):
        """
        **[EXPAND]**
        
        :param names_list:
        :return:
        """
        self.graph_checker()
        # print(names_list)
        # print (self.graph.vs()["name"])
        if not isinstance(names_list, list):
            raise ValueError("node names list is not a list")

        if len(names_list) < 0:
            raise WrongArgumentError("List is empty")

        for name in names_list:
            if not isinstance(name, str):
                raise ValueError("node names must be strings")

            if name not in self.__graph.vs()["name"]:
                raise MissingAttributeError("node {} is not in vertex \"name\" attribute".format(name))

        if len(list(set(names_list))) != len(names_list):
            self.logger.warning("The names list contains duplicated node names, "
                                "so there will be a double index in index list")

    def attribute_in_nodes(self, attribute):
        """
        **[EXPAND]**
        
        :param attribute:
        :return:
        """
        self.graph_checker()

        if attribute not in self.__graph.vs().attributes():
            raise MissingAttributeError("attribute specified is not present in graph nodes")

    def attribute_in_edges(self, attribute):
        """
        **[EXPAND]**
        
        :param attribute:
        :return:
        """
        self.graph_checker()

        if attribute not in self.__graph.es().attributes():
            raise MissingAttributeError("attribute specified is not present in graph edges")

    def attribute_in_graph(self, attribute):
        """
        **[EXPAND]**
        
        :param attribute:
        :return:
        """
        self.graph_checker()

        if attribute not in self.__graph.attributes():
            raise MissingAttributeError("attribute specified is not present in graph")

    def check_attribute_type(self, attribute, attribute_types):
        '''
        Check that attributes are coherent and present in the graph
        
        :param attribute: a the input attribute to be checked
        :param attribute_types: a type of enumerator that will be screened
        :raise ValueError: if the attribute type is not of the selected enumerator
        '''
        attribute_types = (attribute_types,)
        if not isinstance(attribute, attribute_types):
            raise MissingAttributeError("the value {} is not a  legal AttributeType".format(str(attribute)))

    def check_attributes_types(self, attributes_list: list, attribute_types):
        '''
        Check that attributes are coherent and present in the graph
        
        :param attributes_list: a list of attributes asked to be reported
        :param attribute_types: a type of enumerator or a list of enumerators that will be screened
        :raise ValueError: if the attribute type is not of the selected enumerator
        '''

        if isinstance(attribute_types, list):
            attribute_types = tuple(attribute_types)

        else:
            attribute_types = (attribute_types,)

        for elem in attributes_list:
            if not isinstance(elem, attribute_types):
                raise MissingAttributeError("the value {} is not a  legal AttributeType".format(str(elem)))

    def get_node_names(self, index_list: list) -> list:
        '''
        Convert a list of indices to a list of node names (the original ID)
        
        :param index_list: a list of integers containing the index list
        :return: a list of node names
        '''
        self.graph_checker()
        self.check_index_list(index_list)
        names_list = self.__graph.vs(index_list)["name"]
        return names_list

    def get_node_indices(self, node_names: list) -> list:
        '''
        Convert a list of names into a list of indices
        
        :param node_names: a list of strings containing all the node names
        :return: an index list containing the indices of the input node names
        '''

        self.graph_checker()
        self.check_name_list(node_names)
        index_list = []

        for name in node_names:
            select = self.__graph.vs.select(name=name)
            if len(select) > 1:
                raise IndexError("name is not unique, node names must be unique, plese check your graph")

            else:
                index = select[0].index
                index_list.append(index)

        return index_list

    def get_attribute_names(self, attribute_list: list, type="graph") -> list:
        """
        **[EXPAND]**
        
        :param attribute_list:
        :param type:
        :return:
        """
        self.graph_checker()

        attribute_names = []

        if type == "graph":  # search for graph attributes
            for attribute in attribute_list:
                try:
                    attr = self.__graph[attribute.name]
                    attribute_names.append(attribute.name)
                    if attr is None:
                        self.logger.warning("Attribute specified has None value")

                except KeyError:
                    self.logger.warning("Attribute {} is not in graph".format(attribute))

        elif type == "node":  # search for node attributes
            for attribute in attribute_list:

                if attribute.name not in self.__graph.vs().attributes():
                    self.logger.warning("Attribute {} not present in nodee attributes".format(attribute))

                else:
                    attribute_names.append(attribute.name)

        elif type == "edge":
            for attribute in attribute_list:

                if attribute.name not in self.__graph.es().attributes():
                    self.logger.warning("Attribute {} not present in edge attributes".format(attribute))

                else:
                    attribute_names.append(attribute.name)

        else:
            raise ValueError("attribute type not supported. Legal options are \"graph\", \"node\", \"edge\"")

        return attribute_names

    def get_largest_component(self):
        """
        Return the maximum component of a graph (a subrgraph of the original one)
        
        :return: a graph object with the only the largest component. If more than one component if present
        :raise MultipleSolutionserror: if there is more than one largest component
        """
        
        self.logger.info("Giving you only the largest component of the input graph")

        components = self.__graph.components()

        comp_len = [len(comp) for comp in components]
        self.logger.info("Graph has the following components: {}".format(",".join(map(str, comp_len))))

        max_ind = np.argmax(comp_len)

        max_list = [i for i, x in enumerate(comp_len) if x == max_ind]


        if len(max_list) > 1:
            raise MultipleSolutionsError("there are {} largest components, cannot choose one".format(len(max_list)))

        else:
            subgraph = self.__graph.induced_subgraph(components[max_ind])

            self.logger.info(
                "Largest component has {0} nodes and {1} edges (out of {2} nodes and {3} edges in total)".format(
                    subgraph.vcount(), subgraph.ecount(), self.__graph.vcount(), self.__graph.ecount()))

            return subgraph