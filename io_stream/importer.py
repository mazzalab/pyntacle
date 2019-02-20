__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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

from igraph import Graph
import pandas as pd
import pickle
from internal.binarycheck import *
from internal.io_utils import input_file_checker, separator_sniffer
from tools.graph_utils import GraphUtils as gu
from tools.add_attributes import AddAttributes
from tools.adjmatrix_utils import AdjmUtils
from tools.edgelist_utils import EglUtils
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.improperly_formatted_file_error import ImproperlyFormattedFileError
from exceptions.wrong_argument_error import WrongArgumentError
from pyparsing import *
from itertools import product
from collections import OrderedDict
from ordered_set import OrderedSet

def dot_attrlist_to_dict(mylist):
    mydict = {}
    for i in range(0, len(mylist), 2):
        key = mylist[i]
        values = mylist[i + 1]

        if key not in mydict:
            mydict[key] = {}
        for v in values:
            mydict[key][v[0]] = v[1]

    return mydict

def dot_edgeattrlist_to_dict(mylist):
    mydict = {}
    for j in range(0, len(mylist)):
        edge = mylist[j]
        key = tuple(edge[0])

        if len(key) > 2:
            for n in range(0, len(key) - 1):
                if (key[n], key[n + 1]) not in mydict:
                    mydict[(key[n], key[n + 1])] = {}
                if len(edge) == 2:
                    values = edge[1]
                    for v in values:
                        mydict[(key[n], key[n + 1])][v[0]] = v[1]

            continue
        if any(isinstance(e, ParseResults) for e in key):
            # This reads and explicitates the notation a -- {b c d} for edges
            keys = product(key[0], key[1])
            for k in keys:
                if k not in mydict:
                    mydict[k] = {}

        else:
            if key not in mydict:
                mydict[key] = {}
            if len(edge) > 1:
                values = edge[1]
                for v in values:
                    mydict[key][v[0]] = v[1]
            else:
                continue
                # for v in values:
                #     mydict[key][v[0]] = v[1]

    return mydict


class PyntacleImporter:
    """A series of methods to import several Pyntacle supported network file formats and turn them into
    appropriate :py:class:`igraph.Graph` objects that are ready to be processed by Pyntacle """

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def AdjacencyMatrix(file: str, sep: str or None=None, header: bool=True) -> Graph:
        r"""
        Imports an adjacency matrix file to a :py:class:`igraph.Graph` object ready to be used by Pyntacle.

        For more information on adjacency matrices we refer the user to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#adjm>`_
        on Pyntacle website.

        .. note:: We support unweighted undirected Adjacency Matrices, so only zeroes and ones are allowed in the input file.

        .. note:: If an header is present, it **must** contain unique names (two nodes can't have the same ID). if not, an  error wil be raised. The names of the node will be assigned to the vertex ``name`` attribute. If the header is not present, the node "name" attribute will be the corresponding sequential index assigned by igraph.

        :param str file: the path to the file storing the adjacency matrix
        :param None,int sep: The field separator inside the network file. if :py:class:`None` (default) it will be guessed. Otherwise, you can place the string representing the column separator.
        :param bool header: Whether the header is present or not (default is ``True``)

        :return igraph.Graph: an iGraph.Graph object compliant with Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_

        :raise WrongArgumentError: if ``sep`` is not found in the adjacency matrix
        :raise ValueError: if the matrix is not squared
        """

        if not AdjmUtils(file=file, header=header, sep=sep).is_squared():
            raise ValueError(u"Matrix is not squared")

        with open(file, "r") as adjmatrix:
            iterator = iter(adjmatrix.readline, '')

            first_line = next(iterator, None).rstrip()
            if sep not in first_line:
                raise WrongArgumentError(u'The specified separator "{}" is not present in the adjacency matrix file'.format(sep))

            if header:
                #use pandas to parse this into
                f = pd.read_csv(filepath_or_buffer=file, sep=sep, index_col=0)
                node_names = f.columns.values.tolist()

            else:
                f = pd.read_csv(filepath_or_buffer=file, sep=sep, header=None)
                node_names = [str(x) for x in range(0, len(f.columns))]

            graph = Graph.Adjacency(f.values.tolist(), mode="UPPER")
            util = gu(graph=graph)
            util.graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0],  node_names=node_names)
            graph = util.get_graph()

            sys.stdout.write(u"Adjacency matrix from {} imported\n".format(os.path.basename(file)))
            return graph

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def EdgeList(file: str, sep: str or None=None, header: bool=False):
        r"""
        Takes an edge list and turns it into a :py:class:`igraph.Graph` object that stores the input edge list.

        An edge list is a text file that represents all the edges in a graph with a scheme, such as:

        +-------+-------+
        | nodeA | nodeB |
        | nodeB | nodeA |
        +-------+-------+

        We accept undirected edge list, so the node pairs must be repeated twice, so the reciprocal of any edge must be
        present in the edge list file.

        For more specifications on the nature of edge lists we refer the user to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#egl>`_
        on Pyntacle website.

        .. note:: only the first two columns of the edge list are read, any additional column will be skipped. The first two columns will be assumed to represent and edge by default.

        :param str file: a valid path to the edge list File
        :param None,int sep: The field separator inside the network file. if :py:class:`None` (default) it will be guessed. Otherwise, you can place the string representing the column separator.
        :param bool header: Whether a first line with column name (header) is present or not (default is ``False``)

        :return igraph.Graph: an iGraph.Graph object compliant with Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_
        """
        eglutils = EglUtils(file=file, header=header, sep=sep)

        if eglutils.is_direct():
            raise ValueError(u"Edgelist is not ready to be parsed by Pyntacle, it's direct. Use the `edgelist_utils` module in `tools` to make it undirect")

        elif eglutils.is_multigraph():
            raise ValueError(u"Edgelist contains multiple edges. It is not ready to be parsed by Pyntacle, Use the `edgelist_utils` module in `tools` to turn it into a simple graph.")

        graph = Graph() #initialize an empty graph that will be filled
        
        if header:
            adj = pd.read_csv(file, sep=sep, header=0, dtype=str)
            adj.columns = [0, 1]
            
            
        else:
            adj = pd.read_csv(file, sep=sep, header=None, dtype=str)
        
        adj.values.sort()
        adj = adj.drop_duplicates()
        adj.dropna(how="all", inplace=True) #remove all empty lines

        graph.add_vertices(list(str(x) for x in OrderedSet(adj[0].tolist() + adj[1].tolist())))
        edgs = adj.values.tolist()

        graph.add_edges(edgs)
        #initialize the graph by calling the graph_initializer() method
        util = gu(graph=graph)
        util.graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0])
        graph = util.get_graph()

        sys.stdout.write(u"Edge list from {} imported\n".format(os.path.basename(file)))
        return graph

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def Sif(file: str, sep: str or None=None, header: bool=True) -> Graph:
        r"""
        Imports a Simple Interaction File (SIF), a relaxed network file formats used by several visualization and analysis tools such as `Cytoscape <https://cytoscape.org/>`_

        For more specifications on the nature of the SIF we refer the user to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#sif>`_
        on Pyntacle website and to the `Cytoscape documentation <http://wiki.cytoscape.org/Cytoscape_User_Manual/Network_Formats>`_

        .. note:: SIF is a flexible file format, in which the column order is generally not important. Pyntacle limits this flexibility by always reporting the source node in the 1st column, the interaction type in the 2nd column and the target node in the 3rd column.

        .. note:: We assume that the SIF does not contain any vertex attribute. To import vertex attributes, please use the :class:`~pyntacle.io_stream.import_attributes.ImportAttributes`

        .. note:: The interaction type and (if present) the header associated to the interaction will be stored in the edge attribute ``sif_interaction`` and ``sif_interaction_name``, respectively.

        :param str file: the path to the target SIF
        :param None,int sep: The field separator inside the network file. if :py:class:`None` (default) it will be guessed. Otherwise, you can place the string representing the column separator.
        :param bool header: Whether the header is present or not (default is ``True``) If present, the name of the interaction (2nd column) will be stored in the graph private attrovute ``sif_interaction__name``

        :return igraph.Graph: an iGraph.Graph object compliant with Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_
        """

        graph = Graph()
        graph.vs["name"] = []

        with open(file, "r") as f:
        
            """:type: list[str]"""
            if header:
                graph["sif_interaction_name"] = f.readline().rstrip('\n').split(sep)[1]
            else:
                graph["sif_interaction_name"] = None
                
            nodeslist = []
            edgeslist = OrderedDict()
            for i, elem in enumerate(f):
                elem = elem.rstrip('\n').split(sep)
                if len(elem) == 0:
                    pass  # this should be an empty line
    
                elif len(elem) == 1:  # add the single node as isolate
                    nodeslist.append(elem[0])

                elif len(elem) == 3:
                    nodeslist.extend([elem[0], elem[2]])
                    if ((elem[0], elem[2]) not in edgeslist) and ((elem[2], elem[0]) not in edgeslist):
                        edgeslist[(elem[0], elem[2])] = [elem[1]]
                    else:
                        if (elem[0], elem[2]) in edgeslist:
                            if elem[1] not in edgeslist[(elem[0], elem[2])]:
                                edgeslist[(elem[0], elem[2])].append(elem[1])
                        elif (elem[2], elem[0]) in edgeslist:
                            if elem[1] not in edgeslist[(elem[2], elem[0])]:
                                edgeslist[(elem[2], elem[0])].append(elem[1])
                        else:
                            raise KeyError(u"This should not happen - SIF formatting looks weird. "
                                           "Please contact the developers.")

                elif len(elem) >= 4:
                    first = elem[0]
                    interaction = elem[1]
                    other_nodes = elem[2:]
                        
                    nodeslist.append(first)
                    for n in other_nodes:
                        nodeslist.append(n)
                        if ((first, n) not in edgeslist) and ((n, first) not in edgeslist):
                            edgeslist[(first, n)] = [interaction]
                        else:
                            if (first, n) in edgeslist:
                                if interaction not in edgeslist[(first, n)]:
                                    edgeslist[(first, n)].append(interaction)
                            elif (n, first) in edgeslist:
                                if interaction not in edgeslist[(n, first)]:
                                    edgeslist[(n, first)].append(interaction)
                            else:
                                raise KeyError(u"This should not happen - SIF formatting looks weird. "
                                                 "Please contact the developers.")
                            
    
                else:
                    raise ImproperlyFormattedFileError("line {} is malformed".format(i))
    
            nodeslist = list(set(nodeslist))
            graph.add_vertices(nodeslist)
            graph.add_edges(edgeslist.keys())
            graph.es()["sif_interaction"] = list(edgeslist.values())

            # initialize graph
            util = gu(graph=graph)
            util.graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0])
            graph = util.get_graph()
    
            sys.stdout.write(u"SIF from {} imported\n".format(file))

        return graph

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def Dot(file: str, **kwargs):
        r"""
        Import a DOT file into a :py:class:`igraph.Graph` object.

        Dot is a network file format designed for network visualization
        by `GraphViz <https://www.graphviz.org/>`_ and other tools to trustfully reproduce network properties graphically .

        The main documentation on Dot can be found `here <https://www.graphviz.org/doc/info/lang.html>`_

        We refer the user to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#dot>`_
        within the Pyntacle official page for more details regarding  the specifics of Dot Files.

        .. warning:: the attributes of the DOT file object may not be imported correctly. for this reason, we recommend to import these attributes by means of the :class:`~pyntacle.io_stream.import_attributes.ImportAttributes` module

        :param str file: the path to the target DOT file
        :param kwargs: optional arguments to specify additional keywords that are present in the imported DOT format

        :return igraph.Graph: an iGraph.Graph object compliant with Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_
        """
        graph = Graph()
        graph.vs()["name"] = None
        graph.es()["sif_interaction"] = None

        # initialize empty graph

        dotdata = open(file)
        last_pos = dotdata.tell()

        header_comment = False
        if dotdata.readline().startswith('/*'):
            header_comment = True
        dotdata.seek(last_pos)
        if header_comment:
            dotdata = dotdata.read().split("\n", 1)[1]
        else:
            dotdata = dotdata.read()

        # Parsing dot file
        graph_beginning = 'graph' + Optional(Word(alphanums))('initial_name') + Word('{')

        graph_element = 'graph'
        graph_ATTR = Word(alphanums + '_"-') + Suppress('=') + Word(alphanums + '"_?-')
        graph_indented_block = nestedExpr('[', '];', content=Group(graph_ATTR))
        graph_elementBlock = graph_element + Optional(graph_indented_block)

        node_element = Word(alphanums)
        node_ATTR = Word(alphanums + '_"-') + Suppress('=') + Word(alphanums + '"_?-')
        node_elementBlock = node_element + nestedExpr('[', '];', content=Group(node_ATTR))

        edgeformat = Word(alphanums) | Suppress('{') + Group(
            delimitedList(Word(alphanums), delim=White())) + Suppress('}')
        edge_element = Group(
            Word(alphanums) + OneOrMore(Optional(Suppress('->')) + Optional(Suppress('--')) + edgeformat))
        edge_ATTR = Word(alphanums + '-_"') + Suppress('=') + Word(alphanums + '"-_?')
        edge_indented_block = nestedExpr('[', ']', content=Group(edge_ATTR))
        edge_elementBlock = Group(edge_element + Optional(edge_indented_block) + Suppress(';'))

        graph_end = '}'

        header_parser = graph_beginning + ZeroOrMore(
            graph_elementBlock.setResultsName("graph_attrs_block", listAllMatches=False)) + \
                        ZeroOrMore(node_elementBlock)("node_attrs_block") + \
                        ZeroOrMore(edge_elementBlock)("edge_attrs_block") + graph_end

        tokens = header_parser.parseString(dotdata)
        # Converting lists to dictionaries
        graph_attrs_dict = dot_attrlist_to_dict(tokens.graph_attrs_block)
        node_attrs_dict = dot_attrlist_to_dict(tokens.node_attrs_block)
        edge_attrs_dict = dot_edgeattrlist_to_dict(tokens.edge_attrs_block)

        if tokens.initial_name:
            graphname = tokens.initial_name
        else:
            graphname = os.path.splitext(os.path.basename(file))[0]

        for a in graph_attrs_dict:
            for k in graph_attrs_dict[a]:
                AddAttributes.add_graph_attributes(graph, k, graph_attrs_dict[a][k])
                if k == 'name':
                    graphname = k

        for a in node_attrs_dict:
            for k in node_attrs_dict[a]:
                if a not in graph.vs()["name"]:
                    graph.add_vertex(name=a)
                if k != 'name':
                    AddAttributes.add_node_attributes(graph, k, [node_attrs_dict[a][k]], [a])

        for a in edge_attrs_dict:
            for n in a:
                if n not in graph.vs()["name"]:
                        graph.add_vertex(name=n)

            if graph.are_connected(a[0], a[1]):
                sys.stdout.write(u"An edge already exists between node %s and node %s,"
                                 "skipping this edge (we recommend to check again your file\n" % (
                                     a[0], a[1]))
            else:
                graph.add_edge(source=a[0], target=a[1])

        if Graph.is_directed(graph):
            sys.stdout.write(u"Converting graph to undirect\n")
            graph.to_undirected()

        util = gu(graph=graph)
        util.graph_initializer(graph_name=graphname)
        graph = util.get_graph()

        for a in edge_attrs_dict:
            for k in edge_attrs_dict[a]:
                AddAttributes.add_edge_attributes(graph, k, [edge_attrs_dict[a][k]], [a])

        sys.stdout.write(u"DOT from {} imported\n".format(os.path.basename(file)))
        return graph

    @staticmethod
    @input_file_checker
    def Binary(file: str) -> Graph:
        r"""
        Loads a binary file  (a :py:class:`pickle` object) that stores a :py:class:`igraph.Graph` object and makes it
        ready to be used for Pyntacle.

        We refer the user to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#bin>`_
        within the Pyntacloe official page for more details regarding  the specifics of :py:class:`igraph.Graph`
        binary objects that can be serialized by Pyntacle.

        :param str file: the location of the binary file

        :return igraph.Graph: an iGraph.Graph object compliant with Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_

        :raise IOError: if the binary does not contain a :py:class:`igraph.Graph` object
        """

        if not is_binary_file(file):
            raise WrongArgumentError(u"file is not a binary")

        graph = pickle.load(open(file, "rb"))
        if not isinstance(graph, Graph):
            raise IOError(u"binary is not a graph object")

        else:
            if graph.ecount() < 1 and graph.vcount() < 2:
                raise IllegalGraphSizeError(u"Graph must contain at least 2 nodes linked by one edge")

            else:
                utils = gu(graph=graph)
                utils.graph_initializer(
                    graph_name=os.path.splitext(os.path.basename(file))[0])

                if Graph.is_directed(graph):

                    sys.stdout.write(u"Converting graph to undirect\n")
                    graph.to_undirected()

                utils.check_graph()
                graph = utils.get_graph()
                sys.stdout.write(u"Binary from {} imported\n".format(os.path.basename(file)))
                return graph
