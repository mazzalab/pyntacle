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

from igraph import Graph
import pandas as pd
import re
import pickle
import numpy as np
from config import *
from misc.binarycheck import *
from utils.graph_utils import GraphUtils
from misc.import_utils import *
from utils.add_attributes import *
from utils.adjmatrix_utils import AdjmUtils
from utils.edgelist_utils import EglUtils
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.unproperlyformattedfile_error import UnproperlyFormattedFileError


"Wraps up all the importers for several type of network representation files"


class PyntacleImporter:
    @staticmethod
    @filechecker
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
    @filechecker
    @separator_sniffer
    def EdgeList(file, sep=None, header=False):
        """
        Take an edge list and turns it into an `igraph.Graph` object that stores the input edge list. An Edge List is a
        text file that represnt all the edges in a graph with a scheme, *nodeA* **separator** *nodeB*. We accept
        undirected edge list, so the node pairs must be repeated twice, with the node names inverted (so a line with
        *nodeB* **separator** *nodeB* must be present or it will raise an error.
        :param str file: a valid path to the Edge List File
        :param sep: if None(default) we will try to guess the separator. Otherwise, you can place the string
        representing the rows and columns separator.
        :param bool header: Whether the header is present or not (default is *False*)
        :return: an `igraph.Graph` object.
        """

        EglUtils(file=file, header=header, separator=sep).is_pyntacle_ready()

        graph = Graph() #initialize an empty graph that will be filled

        graph.vs["name"] = []
        if header:

            adj = pd.read_csv(file, sep=sep, header=0)

        else:
            adj = pd.read_csv(file, sep=sep, header=None)

        adj.values.sort()
        adj = adj.drop_duplicates()

        # add all vertices to graph
        graph.add_vertices(list(set(adj[0].tolist() + adj[1].tolist())))
        graph.add_edges([tuple(x) for x in adj.values])
        #initialize the graph by calling the graph_initializer() method
        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0])
        sys.stdout.write("Edge List from file {} imported\n".format(file))
        return graph

    @staticmethod
    @filechecker
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
                        graph.es(graph.get_eid(node_ids[0], node_ids[1]))["__sif_interaction"] = interaction

            else:
                sys.stdout.write("line {} is malformed, hence it will be skipped\n".format(i))

                # print(g.vs()["name"])

        # add missing attribute to graph
        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0])

        sys.stdout.write("Sif File  from file {} imported\n".format(file))

        return graph

    @staticmethod
    @filechecker
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
        ''' initialize empty graph'''

        with open(file, "r") as dot_file:
            sys.stdout.write("Importing dot file {}".format(os.path.basename(file)))
            # check whether graph exists in the first line, as well as a '{'
            first_line = dot_file.readline().rstrip().split(" ")
            # print(first_line)

            if len(first_line) <= 3:

                if first_line[0].lower() != "graph":
                    raise UnproperlyFormattedFileError("First line must have a graph statement "
                                                       "at the beginning of the line")
                if first_line[-1] != "{":
                    raise UnproperlyFormattedFileError("first line must enhd with \"{\"")

                if len(first_line) == 3:
                    AddAttributes(graph=graph).add_graph_attributes({"name": first_line[1]})

            else:
                raise UnproperlyFormattedFileError("graph must contain at max one unique name "
                                                   "(use \"_\" for complex names")

            '''
            split the file by semicolon and remove any trailing characters before or after an edge
            '''
            rest = dot_file.read().split(";")
            rest = [x.rstrip() for x in rest]
            rest = [x.lstrip(" ") for x in rest]
            rest = [x.lstrip() for x in rest]
            rest = [x.lstrip("\t") for x in rest]

            if len(rest) < 1:
                raise IOError("Dot file does not contains edges")

            if rest[-1] != "}":
                raise UnproperlyFormattedFileError("dot file must contain an\"}\" at the end ")

            else:
                '''
                remove last element parenthesis)
                '''
                del rest[-1]

                '''
                read node list
                '''

                for pair in rest:
                    # print(pair)
                    # print(rest)
                    l = pair.split("--")
                    l = [x.rstrip(" ") for x in l]
                    l = [x.lstrip(" ") for x in l]
                    # print(l)

                    # parse edge labels
                    attribute_flag = False
                    print(l[-1])

                    try:
                        m = re.search(r"\[(.+?)\]", l[-1]).group(1)

                        try:
                            edge_attributes = re.findall(r"([A-Za-z0-9_]+)[\=]+([A-Za-z0-9_]+)", m)
                            attribute_flag = True

                        except AttributeError:
                            raise UnproperlyFormattedFileError(
                                "edge attributes are not formatted according to the dot standards")

                    except AttributeError:
                        sys.stdout.write("no square brackets for edge attributes found on pair %s\n" % pair)

                    if l[0] not in graph.vs()["name"]:
                        graph.add_vertex(name=l[0])

                    if len(l) == 2:

                        '''
                        case 1:
                        a -- b;
                        a -- {a b c};
                        '''

                        if l[1][0] == "{" and l[1][-1] == "}":
                            # print("culo")
                            '''remove first and last parenthesis'''
                            l[1] = l[1][1:-1]
                            # print(l)
                            l[1] = l[1].lstrip(" ")  # remove all blank characters (left and right)
                            l[1] = l[1].rstrip(" ")
                            if l[1] == "":
                                raise UnproperlyFormattedFileError("dot file contains empty parenthesis")

                            ls = l[1].split(" ")
                            print(ls)

                            for elem in ls:
                                if elem not in graph.vs()["name"]:
                                    graph.add_vertex(name=elem)

                                if graph.are_connected(l[0], elem):
                                    sys.stdout.write("An edge already exists between edge %s and edge %s,"
                                                        "skipping this edge (we recommend to check again your file\n" % (
                                                            l[0], elem))
                                else:
                                    graph.add_edge(source=l[0], target=elem)

                        elif (l[1][0] == "{" and l[1][-1] != "}") or (l[1][0] != "{" and l[1][-1] == "}"):
                            raise UnproperlyFormattedFileError("Missing one of the braces in edge list")

                        else:

                            if l[1] not in graph.vs()["name"]:
                                graph.add_vertex(name=l[1])

                            if graph.are_connected(l[0], l[1]):
                                sys.stdout.write("An edge already exists between edge %s and edge %s,"
                                                    "skipping this edge (we recommend to check again your file\n" % (
                                                        l[0], l[1]))

                            else:
                                graph.add_edge(source=l[0], target=l[1])

                    elif len(l) > 2:

                        for i, n in enumerate(l):

                            if n not in graph.vs()["name"]:
                                graph.add_vertex(name=n)

                            if i > 0:
                                if graph.are_connected(l[i - 1], n):
                                    sys.stdout.write("An edge already exists between edge %s and edge %s,"
                                                        "skipping this edge (we recommend to check again your file\n" % (
                                                            l[i - 1], n))
                                else:
                                    graph.add_edge(l[i - 1], n)
                                    if attribute_flag:  # find out the edge just added
                                        # to the network and add the attributes in edge attributes to it
                                        source_index = graph.vs.select(name=l[i - 1])[0].index
                                        target_index = graph.vs.select(name=n)[0].index
                                        edge = graph.es.select(_source=source_index, _target=target_index)
                                        for ed in edge:
                                            for at in edge_attributes:
                                                ed[at[0]] = at[1]

                    else:
                        raise UnproperlyFormattedFileError("edges do not match dot grammar")

        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0])

        sys.stdout.write("Dot File {} imported to a Graph Object\n".format(file))
        return graph

    @staticmethod
    @filechecker
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