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

# external libraries
from config import *
import logging
import os
from igraph import Graph
from exceptions.illegal_argument_number_error import IllegalArgumentNumberError
from tools.misc.enums import SP_implementations
from exceptions.unsupported_graph_error import UnsupportedGrapherror
# pyntacle Libraries
from exceptions.wrong_argument_error import WrongArgumentError

class AddAttributes():
    logger = None

    def __init__(self, graph: Graph):

        self.logger = log

        if type(graph) is not Graph:
            raise WrongArgumentError("object is not a igraph.Graph")
        else:
            self.__graph = graph


    def add_graph_attributes(self, attr_name, attr):
        """
        Add an attribute to a graph object

        :param attr: any object being added as attribute
        :param attr_name: string. The name of the attribute being imported
        :return: an igraph.Graph object
        """

        if not isinstance(attr_name, str):
            raise TypeError("Attribute name is not a string")
        else:
            if isinstance(attr, dict):
                if attr_name in self.__graph.attributes():
                    self.__graph[attr_name].update(attr)
                else:
                    self.__graph[attr_name] = attr

            else:
                self.__graph[attr_name] = attr

    def add_node_attributes(self, attr_name, attr_list, nodes):
        """
        This function takes an header file and, optionally, a separator, and add them to a graph imprted in __init

        :param attr_list: the object being added as attribute
        :param attr_name: string. The name of the attribute being imported
        :param nodes: list. Nodes to which attributes will be applied.
        :return: an igraph object with the attribute added
        """

        if not isinstance(attr_name, str):
            raise TypeError("Attribute name is not a string")
        
        if isinstance(nodes, str):
            self.logger.warning("WARNING: converting string nodes to list of nodes")
            nodes = [nodes]
        if attr_name.startswith('__'):
            raise KeyError(
                "One of the attributes being added starts with __ (double underscore)."
                "This notation is reserved to private variables, please avoid using it.")
        
        assert len(attr_list) == len(nodes), "in add_node_attributes, length of attributes list cannot be " \
                                             "different from length of list of nodes."
        
        count = 0
        err_count = 0
        for n, a in zip(nodes, attr_list):
            select = self.__graph.vs.select(name=n)
            count += 1
            if len(select) == 0:
                self.logger.warning("Node %s not found in graph" % n)
                err_count += 1
            elif len(select) == 1:
                select[0][attr_name] = a
            else:
                self.logger.error("Node %s has multiple name hits, please check your attribute file" % n)
                raise ValueError("Multiple node hits")
        
        if err_count == count:
            raise WrongArgumentError("All the attributes pointed to non-existing nodes.")
        else:
            self.logger.info("Node attribute {} successfully added!".format(attr_name))

    def add_edge_attributes(self, attr_name, attr_list, edges):
        """
        Add edge attributes specified in a file like (nodeA/nodeB/listofvalues)
        **[EXPAND DESCRIPTIONS OF PARAMS]**

        :param attr_name: string. The name of the attribute being imported
        :param attr_list: the object being added as attribute
        :param edges: list. edges to which attributes will be applied.
        :return:
        """

        if not isinstance(attr_name, str):
            raise TypeError("Attribute name is not a string")
        
        # Checking if one or more attributes' names start with '__'. Avoids malicious injection.
        if attr_name.startswith('__'):
            raise KeyError(
                "One of the attributes in your attributes/weights file starts with __ (double underscore)."
                "This notation is reserved to private variables, please avoid using it.")
        
        assert len(attr_list) == len(edges), "in add_edge_attributes, length of attributes list cannot be " \
                                             "different from length of list of nodes."
        count = 0
        err_count = 0
        for e, a in zip(edges, attr_list):
            select = self.__graph.es.select(node_names=e)
            if len(select) == 0:
                select = self.__graph.es.select(node_names=(e[1], e[0]))
            count += 1
            if len(select) == 0:
                self.logger.warning("Edge %s not found in graph" %str(e))
                err_count += 1
            
            elif len(select) == 1:
                select[0][attr_name] = a
                
            else:
                self.logger.error("Edge %s has multiple name hits, please check your attribute file" % str(e))
                raise ValueError("Multiple edge hits")
        
        if err_count == count:
            raise WrongArgumentError("All the attributes pointed to non-existing edges.")
        else:
            return attr_name  # return the names of the attributes

    def add_edge_names(self, readd=False):
        """
        Add adjacent edge as attribute stored in a tuple to each edge

        :return: an igraph.Graph object with the node attribute ""
        """

        if readd is True or "node_names" not in self.__graph.es.attributes():
            self.logger.info("adding attribute \'node_names\' to each edge (will be stored as a tuple)")
            edge_names = []
            for e in self.__graph.get_edgelist():
                # print("{0}, {1}".format(self.__graph.vs[e[0]]["name"], self.__graph.vs[e[1]]["name"]))
                edge_names.append((self.__graph.vs[e[0]]["name"], self.__graph.vs[e[1]]["name"]))
            self.__graph.es["node_names"] = edge_names
            # for edge in self.__graph.es():
            #     source = edge.source
            #     target = edge.target
            #     source_name = self.__graph.vs(source)["name"][0]
            #     target_name = self.__graph.vs(target)["name"][0]
            #     edge["node_names"] = (source_name, target_name)
        else:
            self.logger.info("attribute \'node_names\' already exist")

    def add_graph_name(self, namestring):
        """
        Assign a name to a graph (or replace it)
        """

        self.logger.info("adding attribute \'name\' to the graph")

        self.__graph["name"] = [namestring]

    def add_parent_name(self):
        """
        Add the graph's name to each vertex, as the "__parent" attribute
        """

        self.logger.info("adding reserved attribute \'__parent\' to the vertices")

        self.__graph.vs["__parent"] = self.__graph["name"]

    def graph_initializer(self, graph_name: object, node_names: object = None):
        """
        **EXPAND**
        :param graph_name:
        :param node_names:
        :return:
        """
        self.__graph.to_undirected() #reconvert graph to directed
        if "name" not in self.__graph.attributes():
            self.logger.info("adding file name to graph name")
            self.add_graph_name(graph_name)

        '''
        add vertices names
        '''
        if "name" not in self.__graph.vs.attributes():
            if node_names is None:
                self.logger.info("adding node names to graph corresponding to their indices")
                self.__graph.vs()["name"] = [str(x.index) for x in self.__graph.vs()]

            else:
                if not isinstance(node_names, list) or not all(isinstance(item, str) for item in node_names):
                    raise WrongArgumentError("node names must be a list of strings")

                if len(node_names) != self.__graph.vcount():
                    raise IllegalArgumentNumberError("node names must be of the same length of vertices")

                self.logger.info("Adding node names to graph using the provided node names")
                self.__graph.vs["name"] = node_names

        '''
        add parent's name to vertices
        '''
        if "__parent" not in self.__graph.vs().attributes():
            '''
            add parent's name to vertices
            '''
            self.logger.info("adding reserved attribute \'__parent\' to the vertices")
            self.add_parent_name()

        '''
        add edge vertices names as an attribute 'node_names'
        '''
        if "node_names" not in self.__graph.es().attributes():
            '''
            add edge vertices names as an attribute 'adjacent_vertices'
            '''
            self.logger.info("adding source and target names as \"node name\" attribute to edges")
            self.add_edge_names()
        # for sif file conversion purposes
        if not "__sif_interaction_name" in self.__graph.attributes():
            self.__graph["__sif_interaction_name"] = None

        if not "__sif_interaction" in self.__graph.es().attributes():
            self.__graph.es()["__sif_interaction"] = None
            
        '''
        Adding implementation info for functions that require it
        '''
        sp_implementation = SP_implementations.igraph
        if self.__graph.vcount() > 3500:  # random number
            # Todo: add GPU ram control on number of nodes, similar to the one we do on the cpu & ram
            # if cuda_avail:
            #     sp_implementation = SP_implementations.gpu
            # else:
                sp_implementation = SP_implementations.cpu
        
        self.__graph["__implementation"] = sp_implementation
