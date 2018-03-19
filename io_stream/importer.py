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

"Wraps up all the importers for several type of network representation files (all the file formats supported by Pyntacle"

import pandas as pd
import re
import pickle
import numpy as np
from config import *
from misc.binarycheck import *
from tools.graph_utils import GraphUtils
from misc.io_utils import *
from tools.add_attributes import *
from tools.adjmatrix_utils import AdjmUtils
from tools.edgelist_utils import EglUtils
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.unproperlyformattedfile_error import UnproperlyFormattedFileError
from pyparsing import *
from itertools import product

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
    @staticmethod
    @input_file_checker
    @separator_sniffer
    def AdjacencyMatrix(file, sep=None, header=True) -> Graph:
        """
        Import an Adjacency matrix file to an `igraph.Graph` object ready to be used by Pyntacle's methods.
        for more specifications on Adjacency Matrix please visit [Ref]_
        *IMPORTANT* We support unweighted undirected Adjacency Matrices, so only zeroes and ones are allowed in the
        input file. The string separing the values inside the adjacency mateix can be specified. If not, Pyntacle will
        try to guess it. By default, Pyntacle assumes that an header if present. The header must contain unique names
        (so two nodes can't have the same name). if not, an  error wil be raised. The header names will be assigned to
        the "name" node attribute in the `igraph.Graph` object. If the header is not present, the node "name" attribute
        will be the relative index assigned by igraph (represented as a string)
        [Ref] http://mathworld.wolfram.com/AdjacencyMatrix.html
        :param str file: the path to the Adjacency Matrix File
        :param sep: if None(default) we will try to guess the separator. Otherwise, you can place the string
        representing the rows and columns separator.
        :param bool header: Whether the header is present or not (default is `True`
        :return: an `igraph.Graph` object.
        """

        if not AdjmUtils(file=file, header=header, separator=sep).is_squared():
            raise ValueError("Matrix is not squared")

        with open(file, "r") as adjmatrix:
            #todo Mauro controlli che questa parte sul separatore fatto bene funziona?
            iterator = iter(adjmatrix.readline, '')

            first_line = next(iterator, None).rstrip()
            if sep not in first_line:
                raise WrongArgumentError('The specified separator "{}" is not present in the adjacency matrix file'.format(sep))
            # else:
            #     n_cols = len(first_line.split(sep))

            if header:
                #use pandas to parse this into
                f = pd.read_csv(filepath_or_buffer=file, sep=sep, index_col=0)
                node_names = f.columns.values.tolist()

            else:
                f = pd.read_csv(filepath_or_buffer=file, sep=sep, header=None)
                node_names = [str(x) for x in range(0, len(f.columns))]

            graph = Graph.Adjacency(f.values.tolist(), mode="UPPER")
            AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0],
                                                         node_names=node_names)

            sys.stdout.write("Adjacency Matrix from file {} imported\n".format(file))
            return graph

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def EdgeList(input_file, sep=None, header=False):
        """
        Take an edge list and turns it into an `igraph.Graph` object that stores the input edge list. An Edge List is a
        text file that represnt all the edges in a graph with a scheme, *nodeA* **separator** *nodeB*. We accept
        undirected edge list, so the node pairs must be repeated twice, with the node names inverted (so a line with
        *nodeB* **separator** *nodeB* must be present or it will raise an error.
        :param str input_file: a valid path to the Edge List File
        :param sep: if None(default) we will try to guess the separator. Otherwise, you can place the string
        representing the rows and columns separator.
        :param bool header: Whether the header is present or not (default is *False*)
        :return: an `igraph.Graph` object.
        """

        if not EglUtils(file=input_file, header=header, separator=sep).is_pyntacle_ready():
            raise UnproperlyFormattedFileError("Edgelist is not ready to be parsed by Pyntacle, fix it and then come back!")

        graph = Graph() #initialize an empty graph that will be filled
        
        if header:

            adj = pd.read_csv(input_file, sep=sep, skiprows=1, header=None)

        else:
            adj = pd.read_csv(input_file, sep=sep, header=None)
            
        adj.values.sort()
        adj = adj.drop_duplicates()
        # add all vertices to graph
        graph.add_vertices(list(str(x) for x in set(adj[0].tolist() + adj[1].tolist())))
        graph.add_edges([tuple(x) for x in adj.values])
        #initialize the graph by calling the graph_initializer() method
        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(input_file))[0])
        sys.stdout.write("Edge List from file {} imported\n".format(input_file))
        return graph

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def Sif(file, sep=None, header=True) -> Graph:
        """
        Import a Simple Interaction File (**SIF**) usually used by tools like Cytoscape to visualize and analyze networks
        inside the Cytoscape Framework, as well as by other Cytscape-like applications. For information regarding the SIF
        file specification, visit: `The Official Cytoscape Page`_. Here, we accept Cytoscape file **with the interaction
        type in between the two node columns** (e.g. NodeA *separator* **INTERACTION** NodeB). The interaction type and
        (if present) the header associated to the interaction will be stored in the edge attribute `__sif_interaction`
        and `__sif_interaction_name` respectively.
        _The Official Cytoscape Page: http://wiki.cytoscape.org/Cytoscape_User_Manual/Network_Formats.
        The SIF file may contain an header(*header=True*).
        :param str file: a valid path to the Edge List File
        :param sep: if None(default) we will try to guess the separator. Otherwise, you can place the string
        representing the rows and columns separator.
        :param bool header: Whether the header is present or not (default is *False*)
        :return: an `igraph.Graph` object.
        """

        graph = Graph()
        graph.vs["name"] = []

        sif_list = [line.rstrip('\n').split(sep) for line in open(file, "r")]

        """:type: list[str]"""

        if header:
            graph["__sif_interaction_name"] = sif_list[0][1]
            graph.es()["__sif_interaction"] = None
            del sif_list[0]

        else:
            graph["__sif_interaction_name"] = None

        for i, elem in enumerate(sif_list):

            if len(elem) == 0:
                pass  # this should be an empty line

            elif len(elem) == 1:  # add the single node as isolate
                if elem[0] not in graph.vs()["name"]:
                    graph.add_vertex(name=elem[0])

            elif len(elem) == 3:

                # print(elem)
                first = elem[0]
                second = elem[2]

                if first not in graph.vs()["name"]:
                    graph.add_vertex(name=first)

                if second not in graph.vs()["name"]:
                    graph.add_vertex(name=second)

                if not graph.are_connected(first, second):
                    graph.add_edge(source=first, target=second, __sif_interaction=elem[1])

                else:
                    node_ids = GraphUtils(graph=graph).get_node_indices(node_names=[first, second])
                    graph.es(graph.get_eid(node_ids[0], node_ids[1]))["__sif_interaction"] = elem[1]

            elif len(elem) >= 4:
                first = elem[0]
                interaction = elem[1]
                other_nodes = elem[2:]

                if first not in graph.vs()["name"]:
                    graph.add_vertex(name=first)

                for n in other_nodes:
                    if n not in graph.vs()["name"]:
                        graph.add_vertex(name=n)
                    if not graph.are_connected(first, n):
                        graph.add_edge(source=first, target=n, __sif_interaction=interaction)

                    else:
                        sys.stdout.write(
                            "an edge already exist between node {0} and node {1}. This should not happen, as pyntacle only supports simple graphs.\n Attribute \"__sif_interaction\n will be overriden\n".format(
                                first, n))
                        node_ids = GraphUtils(graph=graph).get_node_indices(node_names=[first, n])
                        graph.es(graph.get_eid(node_ids[0], node_ids[1], directed=False))["__sif_interaction"] = interaction

            else:
                sys.stdout.write("line {} is malformed, hence it will be skipped\n".format(i))

                # print(g.vs()["name"])

        # add missing attribute to graph
        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0])

        sys.stdout.write("Sif File  from file {} imported\n".format(file))

        return graph

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def Dot(file, sep=None, **kwargs):
        """

        :param file:
        :param sep:
        :param kwargs:
        :return:
        """

        graph = Graph()
        graph.vs()["name"] = None
        graph.es()["__sif_interaction"] = None

        ''' initialize empty graph'''

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
                AddAttributes(graph).add_graph_attributes(k, graph_attrs_dict[a][k])
                if k == 'name':
                    graphname = k

        for a in node_attrs_dict:
            for k in node_attrs_dict[a]:
                if a not in graph.vs()["name"]:
                    graph.add_vertex(name=a)
                if k != 'name':
                    AddAttributes(graph).add_node_attributes(k, [node_attrs_dict[a][k]], [a])

        for a in edge_attrs_dict:
            for n in a:
                if n not in graph.vs()["name"]:
                        graph.add_vertex(name=n)

            if graph.are_connected(a[0], a[1]):
                sys.stdout.write("An edge already exists between node %s and node %s,"
                                 "skipping this edge (we recommend to check again your file\n" % (
                                     a[0], a[1]))
            else:
                graph.add_edge(source=a[0], target=a[1])

        if Graph.is_directed(graph):
            sys.stdout.write("Converting graph to undirect\n")
            graph.to_undirected()

        AddAttributes(graph=graph).graph_initializer(graph_name=graphname,
                                                     node_names=graph.vs["name"])

        for a in edge_attrs_dict:
            for k in edge_attrs_dict[a]:
                AddAttributes(graph).add_edge_attributes(k, [edge_attrs_dict[a][k]], [a])

        sys.stdout.write("Dot File {} imported to a Graph Object\n".format(file))
        return graph

    @staticmethod
    @input_file_checker
    def Binary(file) -> Graph:
        """
        Reload a binary file that stores an `igraph.Graph` object and makes it ready to be used for pyntacle (if it's
        not already).
        :param file_name: Path to the binary file
        :return: an iGraph.Graph object
        """

        if not is_binary_file(file):
            raise WrongArgumentError("file is not a binary")

        graph = pickle.load(open(file, "rb"))
        sys.stdout.write("loading file %s from binary\n" % file)
        if not isinstance(graph, Graph):
            raise IOError("binary is not a graph object")

        else:
            if graph.ecount() < 1 and graph.vcount() < 2:
                raise IllegalGraphSizeError("Graph must contain at least 2 nodes linked by one edge")

            else:
                AddAttributes(graph=graph).graph_initializer(
                    graph_name=os.path.splitext(os.path.basename(file))[0])

                if Graph.is_directed(graph):

                    sys.stdout.write("Converting graph to undirect\n")
                    graph.to_undirected()

                GraphUtils(graph=graph).graph_checker()
                sys.stdout.write("Binary from file {} imported\n".format(file))
                return graph