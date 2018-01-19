'''
This method implement a simple dot file with graph name, node names and attributes. Links (undirected only)
can be represented in the following ways:
EITHER
a -- b;
a -- c;

OR
a -- b -- c;

OR
a -- {a--b--c}
'''

# external libraries
import os
import re

from igraph import Graph

from exception.unproperlyformattedfile_error import UnproperlyFormattedFileError
from io_stream.igraph_importer import IGraphImporter
from utils import add_attributes
from utils.add_attributes import AddAttributes
from config import *

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The Dedalus Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "03 / 11 / 2016"
__creator__ = "Tommaso Mazza"
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
  License for more details.

  You should have received a copy of the license along with this
  work. If not, see http://creativecommons.org/licenses/by-nc-nd/4.0/.
  """


class DotToGraph(IGraphImporter):
    logger = None

    def __init__(self):
        # super(DotToGraph, self).__init__()
        self.logger = log

    def import_graph(self, file_name: str, **kwargs):
        """
        **[EXPAND]**
        
        :param file_name:
        :param kwargs:
        :return:
        """
        if not os.path.exists(file_name):
            raise FileNotFoundError("path to file is not valid")

        graph = Graph()
        graph.vs()["name"] = None
        ''' initialize empty graph'''

        with open(file_name, "r") as dot_file:
            self.logger.info("Importing dot file {}".format(os.path.basename(file_name)))
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
                    add_attributes.AddAttributes(graph=graph).add_graph_attribute({"name": first_line[1]})

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
                        self.logger.info("no square brackets for edge attributes found on pair %s" % pair)

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
                                    self.logger.warning("An edge already exists between edge %s and edge %s,"
                                                        "skipping this edge (we recommend to check again your file" % (
                                                            l[0], elem))
                                else:
                                    graph.add_edge(source=l[0], target=elem)

                        elif (l[1][0] == "{" and l[1][-1] != "}") or (l[1][0] != "{" and l[1][-1] == "}"):
                            raise UnproperlyFormattedFileError("Missing one of the braces in edge list")

                        else:

                            if l[1] not in graph.vs()["name"]:
                                graph.add_vertex(name=l[1])

                            if graph.are_connected(l[0], l[1]):
                                self.logger.warning("An edge already exists between edge %s and edge %s,"
                                                    "skipping this edge (we recommend to check again your file" % (
                                                        l[0], l[1]))

                            else:
                                graph.add_edge(source=l[0], target=l[1])

                    elif len(l) > 2:

                        for i, n in enumerate(l):

                            if n not in graph.vs()["name"]:
                                graph.add_vertex(name=n)

                            if i > 0:
                                if graph.are_connected(l[i - 1], n):
                                    self.logger.warning("An edge already exists between edge %s and edge %s,"
                                                        "skipping this edge (we recommend to check again your file" % (
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

        AddAttributes(graph=graph).graph_initializer(graph_name=os.path.splitext(os.path.basename(file_name))[0])

        self.logger.info("Graph successfully imported")
        return graph