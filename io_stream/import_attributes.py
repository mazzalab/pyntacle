__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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
from igraph import Graph
from collections import OrderedDict

from exceptions.illegal_argument_number_error import IllegalArgumentNumberError
from exceptions.unsupported_graph_error import UnsupportedGraphError
# pyntacle Libraries
from exceptions.wrong_argument_error import WrongArgumentError
from tools.add_attributes import AddAttributes

class ImportAttributes():
    r"""
    Imports attributes for nodes, edges or the whole graph from a text file and adds it to the ``igraph.Graph`` object of
    interest at the appropriate layer. We refer to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#aff>`_
    on Pyntacle website for more details on the allowed types of attribute files.

    :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

    :raise NotAGraphError: if the initialized object is not of :py:class:`igraph.Graph`
    """
    #todo Mauro: make the methods static

    logger = None
    
    def __init__(self, graph: Graph):
        
        self.logger = log
        
        if type(graph) is not Graph:
            raise WrongArgumentError(u"object is not a igraph.Graph")
        else:
            self.__graph = graph
    
    def __check_file(self, file: str, sep: str):
        
        if not os.path.exists(file):
            raise FileNotFoundError(u"File does not exist")
        
        if sep is None:
            self.logger.info(u"using '\t' as default separator")
            sep = "\t"
        
        with open(file, "r") as attrfile:
            head = attrfile.readline()

            # if this is a node, the header is not specified
            first = head.split(sep)[0]
            
            if first in self.__graph.vs("name"):
                self.logger.error("header is not specified")
                raise ValueError("header is not specified")
            
            return (file, sep)
    
    def import_graph_attributes(self, file: str, sep: str or None=None):
        r"""
        Adds attributes at the ``graph`` level of a :py:class:`igraph.Graph` object. this file is usually a tabular
        file with each line storing in the first column the attribute name and in the second the attribute value, i.e.:

        +------------+-------+
        |  Attribute | Value |
        +============+=======+
        |   diameter |  2    |
        +------------+-------+

        We refer the user to the `graph attribute <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#ga>`_
        file specification guide in the Pyntacle official page for further details on attribute files.

        .. note:: The first line is always skipped, as it is assumed to be a header.

        .. note:: each value is orted as a :py:class:`str`, be sure to turn it into your type of interest if needed.


        :param str file: the path to the attribute file
        :param str,None sep: field separator between columns. If :py:class:`None` it will be guessed
        """
        
        check = self.__check_file(file=file, sep=sep)
        infile = check[0]
        sep = check[1]

        # todo mauro: add ctrls (e.g. input file exists, input file is a string, sep is a string
        # todo mauro add controls on whether an edge attribute starts with `__` (reserved for private attributes)

        with open(infile, "r") as attrfile:
            next(attrfile)
            for line in attrfile:
                attrs = line.strip().split(str(sep))

                AddAttributes(self.__graph).add_graph_attributes(attrs[0],
                                                                 attrs[1])
        sys.stdout.write(u"Graph attributes from {} imported.\n".format(file))


    def import_node_attributes(self, file: str, sep: str or None=None):
        r"""
        This method takes an attribute node file and add each attribute to the the :py:class:`igraph.Graph` object.
        A node attribute file is a table in which the first column matches the vertex``name`` attribute of the
        :py:class:`igraph.Graph` object and the rest of the column are attributes that are assigned to the target node,
        such as:

        +------------+-------------+-------------+
        | Node_Name  | Attribute_1 | Attribute_2 |
        +============+=============+=============+
        | node_A     | NA          |        NA   |
        | node_B     | 3.3         |      0.012  |
        | node_C     | -2.3        |      0.054  |
        +------------+-------------+-------------+

        .. note:: the attribute file **must** have an header, that is used to specify the attribute name. The first cell of the header is skipped

        .. note:: to represent an empty value for the selected nodes, one can use ``NA``, ``?`` or ``NONE``. This will return an attribute value of type :py:class:`None` for the attribute of the selected vertex

        .. warning:: the attribute name cannot start with `__`, as this is usually reserved for private attributes


        We refer the user to the `graph attribute <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#na>`_
        file specification guide in the Pyntacle official page for further details on attribute files.

        :param str file: the path to the attribute file
        :param str,None sep: field separator between columns. If :py:class:`None` it will be guessed

        :raise KeyError: if any of the attribute names starts with ``__``
        """

        self.logger.info(u"Reading attributes from file %s and adding them to nodes" % file)
        self.logger.warning(
            u"Attributes will be added as strings, so remember to convert them to proper types")

        #check if file name is properly passed

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
                    u"One of the attributes in your attributes/weights file starts with `__`."
                    "This notation is reserved to internal variables, please avoid using it.")
            attrfile.seek(last_pos)
        
            # read the first line as header and store the attribute names
            attrnames = [x for x in attrfile.readline().rstrip().split(sep)[1:]]
        
            names_list = set()
            for line in attrfile:
            
                if line in ['\n', '\r\n']:
                    self.logger.warning(u"Skipping empty line")
            
                else:
                    tmp = line.rstrip().split(sep)
                    name = tmp[0]
                    attrs = tmp[1:]
                    if any(x.upper() in ["NA", "NONE", "?"] for x in attrs):
                        self.logger.warning(u"NAs found for node {}, replacing it with None")
                        attrs = [None if x in ["NA", "NONE", "?"] else x for x in attrs]
                    # select node with attribute name matching the node attribute "name"
                    select = self.__graph.vs.select(name=name)
                
                    if name not in names_list:
                        names_list.add(name)
                    else:
                        self.logger.warning(
                            u"Node {} has already been assigned an attribute, will be overwritten".format(
                                name))
                
                    if len(select) == 0:
                        self.logger.warning(u"node %s not found in graph" % name)
                
                    elif len(select) == 1:
                        for i, obj in enumerate(attrs):
                            if attrnames[i] not in attrs_dict:
                                attrs_dict[attrnames[i]] = OrderedDict()
                            attrs_dict[attrnames[i]][select[0]["name"]] = obj
                    else:
                        raise ValueError(u"multiple node hits")
                    
        for attr in attrs_dict:
            AddAttributes(self.__graph).add_node_attributes(attr, list(attrs_dict[attr].values()), list(attrs_dict[attr].keys()))
                
        sys.stdout.write(u"Node attributes from {} imported.\n".format(file))

    def import_edge_attributes(self, file: str, sep: str or None=None, mode: str='standard'):
        r"""
        This method imports attributes at the edge level of a :py:class:`igraph.Graph` object.

        We offer two ways to import edge attributes, that can be specified in the ``mode`` parameter:

        * a ``standard`` mode, a table like format format in which the first two columns represent the ``source`` and the ``target`` vertices that uniquely identifies the edge The order of the spurce and target node is not important. The third columns onwards represents the attrobute that will be assigned to each edge in the :py:class:`igraph.Graph`, like in the following example:

        +--------+--------+------------+------------+
        | Source | Target | Attribute1 | Attribute2 |
        +========+========+============+============+
        | node_A | node_B |  12        |     18     |
        | node_B | node_C | int_a      |     NA     |
        +--------+--------+------------+------------+

        .. note:: the attribute file **must** have an header, that is used to specify the edge attribute name. The first two cells of the header are skipped, as only the source and target are used to identify edges

        * a ``cytoscape`` mode, in which we port the `Cytoscape Legacy format <http://manual.cytoscape.org/en/stable/Node_and_Edge_Column_Data.html?highlight=legacy>`_ for edge attributes

        .. note:: to represent an empty value for the selected nodes, one can use ``NA``, ``?`` or ``NONE``. This will return an attribute value of type :py:class:`None` for the attribute of the selected edge

        We refer the user to the `graph attribute <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#na>`_
        file specification guide in the Pyntacle official page for further details on attribute files.

        :param str file: the path to the attribute file
        :param str,None sep: field separator between columns. If :py:class:`None` it will be guessed
        :param str mode: either ``standard`` or ``cytoscape``

        :raise UnsupportedGraphError: if the :py:class:`igraph.Graph` has multiple edges (occurs when the graph does not respect the minimum requirements for Pyntacle)
        :raise IllegalArgumentNumberError: if the formatting of the edge attribute file does not meet the desired requirements
        """
        # todo mauro add controls on whether an edge attribute starts with `__` (reserved for private attributes)

        check = self.__check_file(file=file, sep=sep)
        infile = check[0]
        sep = check[1]
        edges_list = set()
        attrs_dict = {}
        with open(infile, "r") as attrfile:
            if mode == "standard":
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[2:]]

            elif mode == "cytoscape":
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[1:]]
            err_count = 0
            line_count = 0

            for line in attrfile:

                if line in ['\n', '\r\n']:
                    self.logger.warning(u"Skipping empty line")
                
                else:
                    tmp = line.rstrip().split(sep)

                    if mode == "standard":
                        perm_node_names = [(tmp[0], tmp[1]), (tmp[1], tmp[0])]

                    elif mode == "cytoscape":
                        perm_node_names = [(tmp[0].split(' ')[0], tmp[0].split(' ')[2]),
                                           (tmp[0].split(' ')[2], tmp[0].split(' ')[0])]
                    
                    if perm_node_names[0] not in edges_list and perm_node_names[1] not in edges_list:
                        edges_list.add(perm_node_names[0])
                        edges_list.add(perm_node_names[1])

                    else:
                        # This happens when the attribute list has a duplicate edge.
                        self.logger.warning(
                            u"Edge {0}-{1} has already been assigned an attribute, will be overwritten".format(
                                tmp[0],
                                tmp[1]))
                    
                    if mode == "standard":
                        attrs = tmp[2:]

                    elif mode == "cytoscape":
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

                            if obj.upper() in ["NONE", "NA", "?"]:
                                attrs_dict[attrnames[i]][select[0]["adjacent_nodes"][0]] = None
                                # select[0][attrnames[i]] = None

                            else:
                                attrs_dict[attrnames[i]][select[0]["adjacent_nodes"][0]] = obj
                                # select[0][attrnames[i]] = obj
                    
                    elif len(select) > 1:
                        raise UnsupportedGraphError(
                            u"More than one edge with the same name is present in the graph. Probably a Multigraph")
                        # OVERWRITTEN AND REPLACED BY AN ERROR
                        # This happens if the graph has duplicate edges. Should not happen.
                        # self.logger.info(
                        #     "Multiple edge hits (probably a multigraph). Adding the attributes to each edge")
                        # for edge in select:
                        #     for i, obj in enumerate(attrs):
                        #         edge[attrnames[i]] = obj
                    
                    else:
                        err_count += 1
                        self.logger.warning(u"Edge (%s,%s) not found" % (tmp[0], tmp[1]))
                    line_count += 1
            
            if err_count == line_count:
                raise IllegalArgumentNumberError(u"Edge attributes not added; all lines in the attribute file were skipped.")

            else:
                self.logger.info("Edge attributes added")

                for attr in attrs_dict:
                    AddAttributes(self.__graph).add_edge_attributes(attr, list(attrs_dict[attr].values()),
                                                                    list(attrs_dict[attr].keys()))
                    
        sys.stdout.write(u"Edge attributes from {} imported.\n".format(file))
