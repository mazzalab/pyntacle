__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.2"
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
Import attributes for an `igraph.Graph` object stored in a file and adds it to the Graph that has to be studied
"""
from config import *
from igraph import Graph
from collections import OrderedDict

from exceptions.illegal_argument_number_error import IllegalArgumentNumberError
from exceptions.unsupported_graph_error import UnsupportedGraphError
# pyntacle Libraries
from exceptions.wrong_argument_error import WrongArgumentError
from tools.add_attributes import AddAttributes

class ImportAttributes():
    logger = None
    
    def __init__(self, graph: Graph):
        
        self.logger = log
        
        if type(graph) is not Graph:
            raise WrongArgumentError("object is not a igraph.Graph")
        else:
            self.__graph = graph
    
    def __check_file(self, file: str, sep: str):
        
        if not os.path.exists(file):
            raise FileNotFoundError("File does not exist")
        
        if sep is None:
            self.logger.info("using \"\t\" as default separator")
            sep = "\t"
        
        with open(file, "r") as attrfile:
            head = attrfile.readline()
            '''
            if this is a node, the header is not specified
            '''
            first = head.split(sep)[0]
            
            if first in self.__graph.vs("name"):
                self.logger.error("header is not specified")
                raise ValueError("header is not specified")
            
            return (file, sep)
    
    def import_graph_attributes(self, file, sep=None):
        
        '''
        Add an attribute to a graph object. The first line is always skipped, aa it is assumed to be a header.

        :param attr: file
        :return: an igraph.Graph object
        :param sep: field separator if input is a file
        '''
        
        check = self.__check_file(file=file, sep=sep)
        infile = check[0]
        sep = check[1]
        with open(infile, "r") as attrfile:
            next(attrfile)
            for line in attrfile:
                attrs = line.strip().split(str(sep))

                AddAttributes(self.__graph).add_graph_attributes(attrs[0],
                                                                 attrs[1])
        sys.stdout.write("Graph attributes from {} imported.\n".format(file))


    def import_node_attributes(self, file: str, sep=None):
        '''
        This function takes an header file and, optionally, a separator, and add them to a graph imprted in __init

        :param file: the name of an existing file name
        :return: an igraph object with the attribute added (a string attribute)
        '''
        self.logger.info("Reading attributes from file %s and adding them to nodes" % file)
        self.logger.warning(
            "Attributes will be added as strings, so remember to convert them to proper types")
    
        '''
        check if file name is properly passed
        '''
        reserved_attrs = ["name", "__parent"]
        check = self.__check_file(file=file, sep=sep)
        infile = check[0]
        sep = check[1]
        attrs_dict = {}
        with open(infile, "r") as attrfile:
            last_pos = attrfile.tell()
            # Checking if one or more attributes' names start with '__'. Avoids malicious injection.
            if any(i in reserved_attrs for i in attrfile.readline().rstrip().split(sep)):
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
                    if any(x.upper() in ["NA", "NONE", "?"] for x in attrs):
                        self.logger.warning("NAs found for node {}, replacing it with None")
                        attrs = [None if x in ["NA", "NONE", "?"] else x for x in attrs]
                    # select node with attribute name matching the node attribute "name"
                    select = self.__graph.vs.select(name=name)
                
                    if name not in names_list:
                        names_list.add(name)
                    else:
                        self.logger.warning(
                            "WARNING: Node {} has already been assigned an attribute, will be overwritten".format(
                                name))
                
                    if len(select) == 0:
                        self.logger.warning("node %s not found in graph" % name)
                
                    elif len(select) == 1:
                        for i, obj in enumerate(attrs):
                            if attrnames[i] not in attrs_dict:
                                attrs_dict[attrnames[i]] = OrderedDict()
                            attrs_dict[attrnames[i]][select[0]["name"]] = obj
                    else:
                        self.logger.error(
                            "Node %s has multiple name hits, please check your attribute file" % name)
                        raise ValueError("multiple node hits")
                    
        for attr in attrs_dict:
            AddAttributes(self.__graph).add_node_attributes(attr, list(attrs_dict[attr].values()), list(attrs_dict[attr].keys()))
                
        sys.stdout.write("Node attributes from {} imported.\n".format(file))

    def import_edge_attributes(self, file: str, sep=None, mode='standard'):
        """
        Add edge attributes specified in a file like (nodeA/nodeB/listofvalues) to the `igraph.Graph` object declared
        when the class was initialized.
        :param file: a valid $PATH to a file storing an edge attributes. This file can be either a standard edge attribute file
        or a Cytoscape Legacy format. See our [file format](http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html)
        page for details regarding this file format
        :param sep: a string specified the separator character of your edge attrib ute file. if `None` (default) it will
        be guessed.
        :param mode: a strng specified the file format of the edge attributes file. choices are `standard` or `cytoscape`
        """
        check = self.__check_file(file=file, sep=sep)
        infile = check[0]
        sep = check[1]
        edges_list = set()
        attrs_dict = {}
        with open(infile, "r") as attrfile:
            if mode == 'standard':
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[2:]]
            elif mode == 'cytoscape':
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[1:]]
            err_count = 0
            line_count = 0
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
                            "Edge {0}-{1} has already been assigned an attribute, will be overwritten".format(
                                tmp[0],
                                tmp[1]))
                    
                    if mode == 'standard':
                        attrs = tmp[2:]
                    elif mode == 'cytoscape':
                        attrs = tmp[1:]
                    
                    select = []
                    match = self.__graph.es.select(adjacent_nodes=perm_node_names[0])
                    if len(match) != 0:
                        select.append(match)
                    
                    match_inv = self.__graph.es.select(adjacent_nodes=perm_node_names[1])
                    if len(match_inv) != 0:
                        select.append(match_inv)
                        
                    if len(select) == 1:
                        for i, obj in enumerate(attrs):
                            if attrnames[i] not in attrs_dict:
                                attrs_dict[attrnames[i]] = OrderedDict()
                            if obj.upper() in ['NONE', 'NA', '?']:
                                attrs_dict[attrnames[i]][select[0]["adjacent_nodes"][0]] = None
                                # select[0][attrnames[i]] = None
                            else:
                                attrs_dict[attrnames[i]][select[0]["adjacent_nodes"][0]] = obj
                                # select[0][attrnames[i]] = obj
                    
                    elif len(select) > 1:
                        raise UnsupportedGraphError(
                            "More than one edge with the same name is present in the graph. Probably a Multigraph")
                        # OVERWRITTEN AND REPLACED BY AN ERROR
                        # This happens if the graph has duplicate edges. Should not happen.
                        # self.logger.info(
                        #     "Multiple edge hits (probably a multigraph). Adding the attributes to each edge")
                        # for edge in select:
                        #     for i, obj in enumerate(attrs):
                        #         edge[attrnames[i]] = obj
                    
                    else:
                        err_count += 1
                        self.logger.warning("Edge (%s,%s) not found" % (tmp[0], tmp[1]))
                    line_count += 1
            
            if err_count == line_count:
                raise IllegalArgumentNumberError("Error: edge attributes not added; all lines in the attribute file were skipped.")
            else:
                self.logger.info("Edge attributes added")
                for attr in attrs_dict:
                    AddAttributes(self.__graph).add_edge_attributes(attr, list(attrs_dict[attr].values()),
                                                                    list(attrs_dict[attr].keys()))
                    
        sys.stdout.write("Edge attributes from {} imported.\n".format(file))
