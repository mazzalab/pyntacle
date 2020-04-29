__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t.mazza@css-mendel.it>
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
from igraph import Graph
from collections import OrderedDict
import pandas as pd
import numpy as np
from exceptions.unsupported_graph_error import UnsupportedGraphError
from tools.add_attributes import AddAttributes
from internal.graph_routines import check_graph_consistency

def check_file(graph: Graph, file: str, sep: str):
    if not os.path.exists(file):
        raise FileNotFoundError(u"File does not exist")

    if sep is None:
        sys.stdout.write(u"using '\t' as default separator\n")
        sep = "\t"

    with open(file, "r") as attrfile:
        head = attrfile.readline()

        # if this is a node, the header is not specified
        first = head.split(sep)[0]

        if first in graph.vs("name"):
            sys.stdout.write("ERROR: header is not specified\n")
            raise ValueError("header is not specified")

        return (file, sep)

class ImportAttributes():
    r"""
    Imports attributes for nodes, edges or the whole graph from a text file and adds it to the ``igraph.Graph`` object of
    interest at the appropriate layer. We refer to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#aff>`_
    on Pyntacle website for more details on the allowed types of attribute files.

    :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

    :raise NotAGraphError: if the initialized object is not of :py:class:`igraph.Graph`
    """

    @staticmethod
    @check_graph_consistency
    def import_graph_attributes(graph: Graph, file: str, sep: str or None=None):
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

        .. note:: each value is imported as a :py:class:`str`, be sure to turn it into your type of interest if needed.

        ..warning: any of the `Pyntacle Reserved graph Attributes <http://pyntacle.css-mendel.it/requirements.html>`_ with the exception of ``name`` and ``sif_interaction_name`` will be dropped. If one of these two attributes is passed, the graph ``name`` will be updated by appending the value in the corresponding graph attribute file, while the ``sif_interaction_name`` will be overwritten.

        :param str file: the path to the attribute file
        :param str,None sep: field separator between columns. If :py:class:`None` it will be guessed
        """
        reserved_graph_attributes = ["isolates", "implementation"]
        check = check_file(graph=graph, file=file, sep=sep)
        infile = check[0]
        sep = check[1]

        with open(infile, "r") as attrfile:
            next(attrfile)
            for line in attrfile:
                attrs = line.strip().split(str(sep))

                if attrs[0] == "name":
                    sys.stdout.write("Appending the 'name' attribute with the current one.\n")
                    graph["name"].append(attrs[1])

                if attrs[0] == "sif_interaction_name":
                    sys.stdout.write("Replacing graph 'sif_interaction_name' attribute with the current one.\n")
                    AddAttributes.add_graph_attribute(graph, "sif_interaction_name", attrs[0])

                #exception for Pyntacle reserved Attributes
                elif attrs[0] in reserved_graph_attributes:
                    sys.stdout.write("WARNING: attempting to import Pyntacle reserved graph attribute '{}', will skip.\n".format(attrs[0]))

                else:
                    sys.stdout.write("Adding {} attribute to graph (as a string).\n".format(attrs[0]))
                    AddAttributes.add_graph_attribute(graph, attrs[0],
                                                      attrs[1])
        sys.stdout.write(u"Graph attributes from {} imported\n".format(os.path.basename(file)))

    @staticmethod
    @check_graph_consistency
    def import_node_attributes(graph: Graph, file: str, sep: str or None=None):
        r"""
        This method takes an attribute node file and add each attribute to the the :py:class:`igraph.Graph` object.
        A node attribute file is a table in which the first column matches the vertex``name`` attribute of the
        :py:class:`igraph.Graph` object and the rest of the column are attributes that are assigned to the target node,
        such as:

        +------------+-------------+-------------+
        | Node_Name  | Attribute_1 | Attribute_2 |
        +============+=============+=============+
        | node_A     | NA          |        NA   |
        +------------+-------------+-------------+
        | node_B     | 3.3         |      0.012  |
        +------------+-------------+-------------+
        | node_C     | -2.3        |      0.054  |
        +------------+-------------+-------------+

        .. note:: the attribute file **must** have an header, that is used to specify the attribute name. The first cell of the header is skipped

        .. note:: to represent an empty value for the selected nodes, one can use ``NA``, ``?``, ``NaN``, ``NONE``, ``none``, ``None``. This will return an attribute value of type :py:class:`None` for the attribute of the selected vertex

        .. warning:: attribute names that matches with `Pyntacle reserved attributes <http://pyntacle.css-mendel.it/requirements.html>`_ will be dropped

        .. warning: if the same node is declared in multiple lines, only the last occurrence of the node will be kept

        .. warning: if two (or more) columns have the same header, they will al be imported and the corresponding duplicated attributes will contain a ``.X`` attribute, where ``X`` is a number starting from 1

        We refer the user to the `graph attribute <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#na>`_
        file specification guide in the Pyntacle official page for further details on attribute files.

        :param str file: the path to the attribute file
        :param str,None sep: field separator between columns. If :py:class:`None` it will be guessed

        :raise KeyError: if any of the attribute names starts with ``__``
        """

        sys.stdout.write(u"Reading attributes from file %s and adding them to nodes\n" % file)
        sys.stdout.write(
            u"WARNING: Attributes will be added as strings, so remember to convert them to proper types\n")

        #check if file name is properly passed
        check = check_file(graph=graph, file=file, sep=sep)
        infile = check[0]
        if sep is None:
            sep = check[1]

        reserved_vertex_attrs = ["name", "parent", "module"] #list that will be used  will skip the importing of reserved attributes
        node_names = graph.vs["name"] #will be used to matche the  node names

        #import attribute file as pandas dataframe
        df = pd.read_csv(infile, index_col=0, sep=sep)

        not_in_graph = list(set(df.index) - set(node_names))
        not_in_graph.sort()

        if len(not_in_graph) > 0:
            sys.stdout.write(u"WARNING: Nodes {} are not present in graph. They will be dropped.\n".format(",".join(not_in_graph)))
            df.drop(not_in_graph, inplace=True)

            if df.empty:
                raise ValueError(u"No node is present in the graph. Is this file correct?")

        if len(df.index[df.index.duplicated()].unique()) > 0: #remove multiple nnodes and keep only the first occurrence
            sys.stdout.write(u"WARNING: Duplicated node names in the vertex column. Only the first occurrence of the node will be kept.\n")
            df = df[~df.index.duplicated(keep='last')] #remove all occurrences of multiple node hits

        if any(x in df.columns for x in reserved_vertex_attrs):
            sys.stdout.write(u"WARNING: some of the columns are labeled as Pyntacle reserved vertex attributes, these columns will be dropped.\n")

            for elem in reserved_vertex_attrs:
                cols = [c for c in df.columns if not c.startswith(elem)]
                df = df[cols]

        df = df.replace(to_replace=["?", "None", "NaN", "none", "NA", "NONE"], value=np.nan) #Set all NA values to NaN
        df.where((pd.notnull(df)), None) #replace all NaNs with None

        #add attributes to graph
        for elem in df.columns:
            AddAttributes.add_node_attribute(graph, elem, attr_list=df[elem].tolist(), nodes=df.index.tolist())

        sys.stdout.write(u"Node attributes from {} imported\n".format(os.path.basename(file)))

    @staticmethod
    @check_graph_consistency
    def import_edge_attributes(graph: Graph, file: str, sep: str or None=None, mode: str='standard'):
        r"""
        This method imports attributes at the edge level of a :py:class:`igraph.Graph` object.

        We offer two ways to import edge attributes, that can be specified in the ``mode`` parameter:

        * a ``standard`` mode, a table like format format in which the first two columns represent the ``source`` and the ``target`` vertices that uniquely identifies the edge The order of the spurce and target node is not important. The third columns onwards represents the attrobute that will be assigned to each edge in the :py:class:`igraph.Graph`, like in the following example:

        +--------+--------+------------+------------+
        | Source | Target | Attribute1 | Attribute2 |
        +========+========+============+============+
        | node_A | node_B |  12        |     18     |
        +--------+--------+------------+------------+
        | node_B | node_C | int_a      |     NA     |
        +--------+--------+------------+------------+

        .. note:: the attribute file **must** have an header, that is used to specify the edge attribute name. The first two cells of the header are skipped, as only the source and target are used to identify edges

        * a ``cytoscape`` mode, in which we port the `Cytoscape Legacy format <http://manual.cytoscape.org/en/stable/Node_and_Edge_Column_Data.html?highlight=legacy>`_ for edge attributes

        .. note:: to represent an empty value for the selected nodes, one can use ``NA``, ``?`` or ``NONE``. This will return an attribute value of type :py:class:`None` for the attribute of the selected edge

        .. warning: any edge attributes named as one of the `Pyntacle reserved edge attributes <http://pyntacle.css-mendel.it/requirements.html>`_, with the exception of ``weights`` and ``sif_interaction``, will be dropped. If  the ``sif_interaction`` attribute has been initialized, the string in the column will be appended

        We refer the user to the s`graph attribute <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#na>`_
        file specification guide in the Pyntacle official page for further details on attribute files.

        :param str file: the path to the attribute file
        :param str,None sep: field separator between columns. If :py:class:`None` it will be guessed
        :param str mode: either ``standard`` or ``cytoscape``

        :raise UnsupportedGraphError: if the :py:class:`igraph.Graph` has multiple edges (occurs when the graph does not respect the minimum requirements for Pyntacle)
        :raise ValueError: if the formatting of the edge attribute file does not meet the desired requirements
        """

        check = check_file(graph=graph, file=file, sep=sep)
        infile = check[0]
        if sep is None:
            sep = check[1]
        edges_list = set()
        attrs_dict = {}

        reserved_edge_attributes = ["adjacent_nodes", "module"]

        with open(infile, "r") as attrfile:
            if mode == "standard":
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[2:]]
            elif mode == "cytoscape":
                attrnames = [x for x in attrfile.readline().rstrip().split(sep)[1:]]
            err_count = 0
            line_count = 0

            for line in attrfile:

                if line in ['\n', '\r\n']:
                    sys.stdout.write(u"WARNING: Skipping empty line\n")
                
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
                        sys.stdout.write(
                            u"WARNING: Edge {0}-{1} has already been assigned an attribute, will be overwritten\n".format(
                                tmp[0],
                                tmp[1]))
                    
                    if mode == "standard":
                        attrs = tmp[2:]

                    elif mode == "cytoscape":
                        attrs = tmp[1:]
                    
                    select = []
                    match = graph.es.select(adjacent_nodes=perm_node_names[0])
                    if len(match) != 0:
                        select.append(match)
                    
                    match_inv = graph.es.select(adjacent_nodes=perm_node_names[1])
                    if len(match_inv) != 0:
                        select.append(match_inv)
                        
                    if len(select) == 1:

                        for i, obj in enumerate(attrs):

                            if attrnames[i] not in attrs_dict:
                                attrs_dict[attrnames[i]] = OrderedDict()

                            if obj.upper() in ["NONE", "NA", "?", "NAN"]:
                                attrs_dict[attrnames[i]][select[0]["adjacent_nodes"][0]] = None
                                # select[0][attrnames[i]] = None

                            else:
                                attrs_dict[attrnames[i]][select[0]["adjacent_nodes"][0]] = obj
                                # select[0][attrnames[i]] = obj
                    
                    elif len(select) > 1:
                        raise UnsupportedGraphError(
                            u"More than one edge with the same name is present in the graph. ")
                        # OVERWRITTEN AND REPLACED BY AN ERROR
                        # This happens if the graph has duplicate edges. Should not happen.
                        # self.logger.info(
                        #     "Multiple edge hits (probably a multigraph). Adding the attributes to each edge")
                        # for edge in select:
                        #     for i, obj in enumerate(attrs):
                        #         edge[attrnames[i]] = obj
                    
                    else:
                        err_count += 1
                        sys.stdout.write(u"WARNING: Edge (%s,%s) not found\n" % (tmp[0], tmp[1]))
                    line_count += 1
            
            if err_count == line_count:
                raise ValueError(u"Edge attributes not added; all lines in the attribute file were skipped.")

            else:
                for attr in attrs_dict:
                    if attr in reserved_edge_attributes:
                        sys.stdout.write("WARNING: attribute '{}' is a Pyntacle reserved edge attribute, will be dropped.\n".format(attr))

                    elif attr == "sif_interaction":
                        for e in attrs_dict[attr].keys():
                            print(e)
                            input()
                            select = graph.es.select(adjacent_nodes=e)
                            if select[0]["sif_interaction"] is None:
                                select[0]["sif_interaction"] = [attrs_dict[attr][e]]
                            else:
                                select[0]["sif_interaction"].append(attrs_dict[attr][e])
                                select[0]["sif_interaction"].sort() #resort sif_interaction alphanumerically
                    else:
                        AddAttributes.add_edge_attribute(graph, attr, list(attrs_dict[attr].values()),
                                                         list(attrs_dict[attr].keys()))
                        sys.stdout.write("Edge attribute {} added\n".format(attr))
                    
        sys.stdout.write(u"Edge attributes from {} imported\n".format(os.path.basename(file)))
