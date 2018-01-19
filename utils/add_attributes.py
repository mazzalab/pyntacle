# external libraries
import logging
import os

from igraph import Graph
from config import *

from exception.illegal_argument_number_error import IllegalArgumentNumberError
from exception.unsupported_graph_error import UnsupportedGrapherror
# Dedalus Libraries
from exception.wrong_argument_error import WrongArgumentError

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The Dedalus Project"
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


class AddAttributes():
    logger = None

    def __init__(self, graph: Graph):

        self.logger = log

        if type(graph) is not Graph:
            raise WrongArgumentError("object is not a igraph.Graph")
        else:
            self.__graph = graph

    def __check_file(self, file_name: str, sep: str):

        if not os.path.exists(file_name):
            raise FileNotFoundError("File does not exist")

        if sep is None:
            self.logger.info("using \"\t\" as default separator")
            sep = "\t"

        with open(file_name, "r") as attrfile:
            head = attrfile.readline()
            '''
            if this is a node, the header is not specified
            '''
            first = head.split(sep)[0]

            if first in self.__graph.vs("name"):
                self.logger.error("header is not specified")
                raise ValueError("header is not specified")

            return (file_name, sep)

    def add_graph_attributes(self, attr, sep=None):

        '''
        Add an attribute to a graph object
        
        :param attr:
        :return: an igraph.Graph object
        :param sep: field separator fi input is a file
        '''

        if isinstance(attr, dict):
            for k in attr.keys():
                if not isinstance(k, str):
                    raise TypeError("attribute is not a string")
                else:
                    self.__graph[k] = attr[k]
        else:
            check = self.__check_file(file_name=attr, sep=sep)
            infile = check[0]
            sep = check[1]
            with open(infile, "r") as attrfile:
                next(attrfile)
                for line in attrfile:
                    self.__graph[line.strip().split(str(sep))[0]] = line.strip().split(str(sep))[1]

    def add_node_attributes(self, file_name: str, sep=None):
        '''
        This function takes an header file and, optionally, a separator, and add them to a graph imprted in __init
        
        :param file_name: the name of an existing file name
        :return: an igraph object with the attribute added (a string attribute)
        '''
        self.logger.info("Reading attributes from file %s and adding them to nodes" % file_name)
        self.logger.warning("Attributes will be added as strings, so remember to convert them to proper types")

        '''
        check if file name is properly passed
        '''

        check = self.__check_file(file_name=file_name, sep=sep)
        infile = check[0]
        sep = check[1]
        with open(infile, "r") as attrfile:
            last_pos = attrfile.tell()
            # Checking if one or more attributes' names start with '__'. Avoids malicious injection.
            if any(i.startswith('__') for i in attrfile.readline().rstrip().split(sep)):
                raise KeyError(
                    "One of the attributes in your attributes/weights file starts with __ (double underscore)."
                    "This notation is reserved to private variables, please avoid using it.")
            attrfile.seek(last_pos)
            
            # read the first line as header and store the attribute names
            attrnames = [x for x in attrfile.readline().rstrip().split(sep)[1:]]

            names_list = set()
            for line in attrfile:

                if line in ['\n', '\r\n']:
                    self.logger.warning("Skipping empty line")

                else:
                    tmp = line.rstrip().split(sep)
                    name = tmp[0]
                    attrs = tmp[1:]
                    # select node with attribute name matching the node attribute "name"
                    select = self.__graph.vs.select(name=name)

                    if name not in names_list:
                        names_list.add(name)
                    else:
                        self.logger.warning(
                            "WARNING: Node {} has already been assigned an attribute, will be overwritten".format(name))

                    if len(select) == 0:
                        self.logger.warning("node %s not found in graph" % name)

                    elif len(select) == 1:
                        for i, obj in enumerate(attrs):
                            select[0][attrnames[i]] = obj
                    else:
                        self.logger.error("Node %s has multiple name hits, please check your attribute file" % name)
                        raise ValueError("multiple node hits")

                    self.logger.info("Node attributes successfully added!")

    def add_edge_attributes(self, file_name: str, sep=None, mode='standard'):
        """
        Add edge attributes specified in a file like (nodeA/nodeB/listofvalues)
        **[EXPAND DESCRIPTIONS OF PARAMS]**
        
        :param file_name:
        :param sep:
        :param mode:
        :return:
        """
        check = self.__check_file(file_name=file_name, sep=sep)
        infile = check[0]
        sep = check[1]
        edges_list = set()
        print("IN ADD EDGE ATTRS. mode:", mode)
        with open(infile, "r") as attrfile:
            last_pos = attrfile.tell()
            # Checking if one or more attributes' names start with '__'. Avoids malicious injection.
            if any(i.startswith('__') for i in attrfile.readline().rstrip().split(sep)):
                raise KeyError(
                    "One of the attributes in your attributes/weights file starts with __ (double underscore)."
                    "This notation is reserved to private variables, please avoid using it.")
            attrfile.seek(last_pos)
            if mode == 'standard':
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[2:]]
            elif mode == 'cytoscape':
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[1:]]
            print(attrnames)

            for line in attrfile:
                if line in ['\n', '\r\n']:
                    self.logger.warning("Skipping empty line")

                else:
                    tmp = line.rstrip().split(sep)
                    if mode == 'standard':
                        perm_node_names = [(tmp[0], tmp[1]), (tmp[1], tmp[0])]
                    elif mode == 'cytoscape':
                        perm_node_names = [(tmp[0].split(' ')[0], tmp[0].split(' ')[2]),
                                           (tmp[0].split(' ')[2], tmp[0].split(' ')[0])]

                    if perm_node_names[0] not in edges_list and perm_node_names[1] not in edges_list:
                        edges_list.add(perm_node_names[0])
                        edges_list.add(perm_node_names[1])
                    else:
                        # This happens when the attribute list has a duplicate edge.
                        self.logger.warning(
                            "Edge {0}-{1} has already been assigned an attribute, will be overwritten".format(tmp[0],
                                                                                                              tmp[1]))

                    if mode == 'standard':
                        attrs = tmp[2:]
                    elif mode == 'cytoscape':
                        attrs = tmp[1:]
                    select = []
                    match = self.__graph.es.select(node_names=perm_node_names[0])

                    if len(match) != 0:
                        select.append(match)

                    match_inv = self.__graph.es.select(node_names=perm_node_names[1])
                    if len(match_inv) != 0:
                        select.append(match_inv)

                    if len(select) == 1:
                        for i, obj in enumerate(attrs):
                            if obj.upper() in ['NONE', 'NA', '?']:
                                select[0][attrnames[i]] = None
                            else:
                                select[0][attrnames[i]] = obj

                    elif len(select) > 1:
                        raise UnsupportedGrapherror(
                            "More than one edge with the same name is present in the graph. Probably a Multigraph")
                        # OVERWRITTEN AND REPLACED BY AN ERROR
                        # This happens if the graph has duplicate edges. Should not happen.
                        # self.logger.info(
                        #     "Multiple edge hits (probably a multigraph). Adding the attributes to each edge")
                        # for edge in select:
                        #     for i, obj in enumerate(attrs):
                        #         edge[attrnames[i]] = obj

                    else:
                        self.logger.warning("Edge (%s,%s) not found" % (tmp[0], tmp[1]))

            self.logger.info("Edge attributes added")
            return attrnames  # return the names of the attributes

    def add_edge_names(self, readd=False):
        '''
        Add adjacent edge as attribute stored in a tuple to each edge
        
        :return: an igraph.Graph object with the node attribute ""
        '''

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
        '''
        Assign a name to a graph (or replace it)
        '''

        self.logger.info("adding attribute \'name\' to the graph")

        self.__graph["name"] = [namestring]

    def add_parent_name(self):
        '''
        Add the graph's name to each vertex, as the "__parent" attribute
        '''

        self.logger.info("adding reserved attribute \'__parent\' to the vertices")

        self.__graph.vs["__parent"] = self.__graph["name"]

    def graph_initializer(self, graph_name: str, node_names=None):
        '''
        Generic method that wraps up th generic operations used when importing or creating a graph using igraph generator
        
        :param file_name:
        :param node_names:
        :return:
        '''

        '''
            add graph name (from filename)
        '''
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
