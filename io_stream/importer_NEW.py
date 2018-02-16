__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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
import numpy as np
import os
import sys
from config import *
from misc.binarycheck import *
from misc.import_utils import *
from utils.add_attributes import *
from utils.adjmatrix_utils import AdjmUtils
from utils.edgelist_utils import EglUtils
from exceptions.unproperlyformattedfile_error import UnproperlyFormattedFileError


"**Wraps up all the importersz for several type of network represenation files**"


class PyntacleImporter:
    @staticmethod
    #@filechecker

    #
    # @separator_sniffer
    def AdjacencyMatrix(file, sep=None, header=True) -> (Graph, list):
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
        eepresenting the separator. .
        :param bool header: Whether the header is present or not (default is `True`
        :return: an `igraph.Graph` object (the input graph)
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
                node_names = f.columns.values

            else:
                f = pd.read_csv(filepath_or_buffer=file, sep=sep, header=None)
                node_names = [str(x) for x in range(0, len(f.columns))]

            graph = Graph.Adjacency(f.values.tolist(), mode="UPPER")

            AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file))[0],
                                                         node_names=node_names)

            print(graph.summary())
            print(graph.attributes())

        return graph

    # @staticmethod
    # @filechecker
    # @separator_sniffer
    # def EdgeList(file, sep=None, header=True):
    #     """
    #
    #     :param file:
    #     :param sep:
    #     :param header:
    #     :return:
    #     """
    #
    #     eglutils = EglUtils(file=file, header=header, separator=sep)
    #     graph = Graph()
    #     """:type: Graph"""
    #     graph.vs["name"] = []
    #     if header:
    #
    #         adj = pd.read_csv(file, sep=sep, header=0)
    #
    #     else:
    #         adj = pd.read_csv(file, sep=sep, header=None)
    #
    #     adj.values.sort()
    #     adj = adj.drop_duplicates()
    #
    #     # add all vertices to graph
    #     graph.add_vertices(list(set(adj[0].tolist() + adj[1].tolist())))
    #     graph.add_edges([tuple(x) for x in adj.values])
    #
    #     return graph
    #
    # @staticmethod
    # @filechecker
    # @separator_sniffer
    # def Sif(file, sep=None, header=True):
    #     graph = Graph()
    #     """:type: Graph"""
    #     graph.vs["name"] = []
    #
    #     sif_list = [line.rstrip('\n').split(sep) for line in open(file_name, "r")]
    #
    #     """:type: list[str]"""
    #
    #     if header:
    #         self.logger.info(
    #             "storing second column of header as edge attribute \"__sif_interaction\". Interaction name can be found in the graph attribute \"__sif_interaction_name\"")
    #         graph["__sif_interaction_name"] = sif_list[0][1]
    #         graph.es()["__sif_interaction"] = None
    #         del sif_list[0]
    #
    #     else:
    #         graph["__sif_interaction_name"] = None
    #
    #     for i, elem in enumerate(sif_list):
    #
    #         if len(elem) == 0:
    #             pass  # this should be an empty line
    #
    #         elif len(elem) == 1:  # add the single node as isolate
    #             if elem[0] not in graph.vs()["name"]:
    #                 graph.add_vertex(name=elem[0])
    #
    #         elif len(elem) == 3:
    #
    #             # print(elem)
    #             first = elem[0]
    #             second = elem[2]
    #
    #             if first not in graph.vs()["name"]:
    #                 graph.add_vertex(name=first)
    #
    #             if second not in graph.vs()["name"]:
    #                 graph.add_vertex(name=second)
    #
    #             if not graph.are_connected(first, second):
    #                 graph.add_edge(source=first, target=second, __sif_interaction=elem[1])
    #
    #             else:
    #                 self.logger.warning(
    #                     "an edge already exist between node {0} and node {1}. This should not happen, as pyntacle only supports simple graphs.\n Attribute \"__sif_interaction\n Will skip line {2}".format(
    #                         first, second, i))
    #                 node_ids = GraphUtils(graph=graph).get_node_indices(node_names=[first, second])
    #                 graph.es(graph.get_eid(node_ids[0], node_ids[1]))["__sif_interaction"] = elem[1]
    #
    #
    #         elif len(elem) >= 4:
    #             first = elem[0]
    #             interaction = elem[1]
    #             other_nodes = elem[2:]
    #
    #             if first not in graph.vs()["name"]:
    #                 graph.add_vertex(name=first)
    #
    #             for n in other_nodes:
    #                 if n not in graph.vs()["name"]:
    #                     graph.add_vertex(name=n)
    #                 if not graph.are_connected(first, n):
    #                     graph.add_edge(source=first, target=n, __sif_interaction=interaction)
    #
    #                 else:
    #                     self.logger.warning(
    #                         "an edge already exist between node {0} and node {1}. This should not happen, as pyntacle only supports simple graphs.\n Attribute \"__sif_interaction\n will be override".format(
    #                             first, n))
    #                     node_ids = GraphUtils(graph=graph).get_node_indices(node_names=[first, n])
    #                     graph.es(graph.get_eid(node_ids[0], node_ids[1]))["__sif_interaction"] = interaction
    #
    #         else:
    #             self.logger.warning("line {} is malformed, hence it will be skipped".format(i))
    #
    #             # print(g.vs()["name"])
    #
    #     # add missing attribute to graph
    #     AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file_name))[0])
    #
    #     '''
    #     define graph as undirected
    #     '''
    #     graph = Graph.as_undirected(graph)
    #     self.logger.info("Sif File imported")
    #     return graph
    # #
    # @staticmethod
    # @filechecker
    # @separator_sniffer
    # def Dot():
    #     pass
    #
    # @staticmethod
    # @filechecker
    # def Binary():
    #     pass