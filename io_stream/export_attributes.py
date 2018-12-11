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
import os
from igraph import Graph
from exceptions.notagraph_error import NotAGraphError

class ExportAttributes():
    r"""
    Export Attributes stored into the ``igraph.Graph`` object as text files. These attributes can belong to the whole
    graph, nodes or edges that belong to the input network.

    :raise NotAGraphError: if the initialized object is not of :py:class:`igraph.Graph`
    """

    logger = None

    def __init__(self, graph: Graph):

        self.logger = log

        if type(graph) is not Graph:
            raise NotAGraphError(u"object is not a igraph.Graph object")

        else:
            self.__graph = graph

    def export_edge_attributes(self, file :str, mode :str='standard'):
        r"""
        Export attributes related to the  *edges* of a network stored into an :py:class:`igraph.Graph` object to a text
        file. Pyntacle can export edges in two formats:

        * a *standard* mode (a tab-separated file), that is structured as such:

        +----------+--------+-------------+-------------+
        |  Source  | Target | Attribute_1 | Attribute_2 |
        +==========+========+=============+=============+
        |     A    |   B    |     12.1    |    tie_1    |
        +----------+--------+-------------+-------------+
        |     A    |   C    |     2.56    |    tie_2    |
        +----------+--------+-------------+-------------+


        * the `cytoscape legacy format <http://manual.cytoscape.org/en/stable/Node_and_Edge_Column_Data.html#legacy-cytoscape-attributes-format>`_

        .. note:: we recommend visit the `Pyntacle File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#ea>`_ for more information on how edge attribute files are formatted

        .. note:: If an edge does not have an assigned value to the target attribute, the attribute value for that edge will be **NA**

        .. warning:: this method works well for one-dimensional values (:py:class:`str`, :py:class:`float`, :py:class:`int`). If the attribute value is not among these types, (e.g.: a :py:class:`list`), it will be written to file as string

        :param str file: the path to the output file. A directory tree will be created if the path does not point to an existent directory.
        :param str mode: either ``standard`` or ``cytoscape``

        :raise ValueError: if ``mode`` is not either ``standard`` or ``cytoscape``
        :raise TypeError: if ``mode`` is not a string
        """

        if not isinstance(mode, str):
            raise TypeError(u"'mode' must be a string, {}",format(type(mode).__name__))
        
        warnflag = 0
        dirname = os.path.dirname(file) or '.'
        if not os.path.exists(dirname):
            self.logger.warning(u"The directory tree for the output file does not exist, it will be created")
            os.makedirs(dirname, exist_ok=True)
        with open(file, 'w') as out:
            # Writing header
            attributes_tokeep = [x for x in self.__graph.es()[0].attributes() if
                                 x != 'adjacent_nodes' and not x.startswith('__')]
            if mode == 'standard':
                out.write('Node1' + '\t' + 'Node2' + '\t' + '\t'.join(attributes_tokeep) + '\n')
            elif mode == 'cytoscape':
                out.write('Edge(Cytoscape Format)' + '\t' + '\t'.join(attributes_tokeep) + '\n')
            else:
                raise ValueError(u"{0} is not valid, it must be either 'standard' or 'cytoscape, {0} found'".format(mode))


            for e in self.__graph.es():
                if mode == 'standard':
                    out.write(str(e.attributes()['adjacent_nodes'][0]) + '\t')
                    out.write(str(e.attributes()['adjacent_nodes'][1]))
                    for attr in attributes_tokeep:
                        # Checking the type of the attribute
                        if not isinstance(e.attributes()[attr], (str, float, int)) and \
                                        e.attributes()[attr] is not None and warnflag == 0:
                            self.logger.warning("The attribute {} looks like an iterable. "
                                                "It will be written as it is.".format(attr))
                            warnflag = 1
    
                        if e.attributes()[attr] is None:
                            out.write('\t' + 'NA')
                        else:
                            out.write('\t' + str(e.attributes()[attr]))
                    out.write('\n')
                else:
                    if e.attributes()['__sif_interaction'] is None:
                        out.write('(interacts with) ')
                    else:
                        for interaction in e.attributes()['__sif_interaction']:
                            out.write(str(e.attributes()['adjacent_nodes'][0]) + ' ')
                            out.write('(' + interaction + ') ')
                            out.write(str(e.attributes()['adjacent_nodes'][1]))

                            for attr in attributes_tokeep:
                                # Checking the type of the attribute
                                if not isinstance(e.attributes()[attr], (str, float, int)) and \
                                                e.attributes()[attr] is not None and warnflag == 0:
                                    self.logger.warning(u"The attribute {} looks like an iterable. "
                                                        "It will be written as it is.".format(attr))
                                    warnflag = 1
            
                                if e.attributes()[attr] is None:
                                    out.write('\t' + 'NA')
                                else:
                                    out.write('\t' + str(e.attributes()[attr]))
                            out.write('\n')
        sys.stdout.write(u"Edge attributes successfully exported at path {}.\n".format(os.path.abspath(file)))


    def export_node_attributes(self,  file :str):
        r"""
        Export attributes belonging to vertices of the :py:class:`igraph.Graph` object into a tab-delimited format that
        later reused in Pyntacle (by means of the :class:`~pyntacle.io_stream.import_attributes.ImportAttributes` or
        ported to other network analysis tools.

        .. note:: We recommend visit the `Pyntacle File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#na>`_ for more information on how node attribute files are formatted

        .. note:: If a vertex does not have an assigned value to for an attribute, the attribute value for that node will be **NA**

        .. warning:: This method works well for one-dimensional values (:py:class:`str`, :py:class:`float`, :py:class:`int`). If the attribute value is not among these types, (e.g.: a :py:class:`list`), it will be written to file as string

        :param str file: the path at which the node attribute file will be written to. A directory tree will be created if the path does not point to an existent directory.
        """
        warnflag = 0
        dirname = os.path.dirname(file) or '.'
        if not os.path.exists(dirname):
            self.logger.warning(u"The directory tree for the output file does not exist, it will be created")
            os.makedirs(dirname, exist_ok=True)
        with open(file, 'w') as out:
            # Writing header
            attributes_tokeep = [x for x in self.__graph.vs()[0].attributes() if
                                 x != 'name' and not x.startswith('__')]
            out.write('Node' + '\t' + '\t'.join(attributes_tokeep) + '\n')
            for v in self.__graph.vs():
                out.write(str(v.attributes()['name']))
                for attr in attributes_tokeep:

                    # Checking the type of the attribute
                    if not isinstance(v.attributes()[attr], (str, float, int)) and \
                                    v.attributes()[attr] is not None and warnflag == 0:
                        self.logger.warning("The attribute {} looks like an iterable. "
                                            "It will be written as it is.".format(attr))
                        warnflag = 1

                    if v.attributes()[attr] is None:
                        out.write('\t' + 'NA')
                    else:
                        out.write('\t' + str(v.attributes()[attr]))
                out.write('\n')
        
        sys.stdout.write(u"Node attributes successfully exported at path {}.\n".format(os.path.abspath(file)))


    def export_graph_attributes(self, file):
        """
        Exports graph attributes to a tab-separated file. These graph attributes are a property of the :py:class:`igraph.Graph` input object

        .. note:: We recommend visit the `Pyntacle File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#ga>`_ for more information on how graph attribute files are formatted

        .. if the graph attribute if :py:class:`None`

        .. warning:: This method works well for one-dimensional values (:py:class:`str`, :py:class:`float`, :py:class:`int`). If the attribute value is not among these types, (e.g.: a :py:class:`list`), it will be written to file as string
        
        :param str file: the path to the graph attribute file. A directory tree will be created if the path does not point to an existent directory.
        """
        warnflag = 0
        dirname = os.path.dirname(file) or '.'
        if not os.path.exists(dirname):
            self.logger.warning(
                u"The directory tree for the output file does not exist, it will be created")
            os.makedirs(dirname)
        with open(file, 'w') as out:
            # Writing header
            attributes_tokeep = [x for x in self.__graph.attributes() if
                                 not x.startswith('__')]
            out.write('Attribute' + '\t' + 'Value' + '\n')

            for attr in attributes_tokeep:

                if attr == 'name':
                    out.write(attr + '\t' + str(self.__graph[attr]) + '\n')
                    continue

                # Checking the type of the attribute
                if not isinstance(self.__graph[attr], (str, float, int)) and \
                                self.__graph[attr] is not None and warnflag == 0:
                    self.logger.warning(u"The attribute {} looks like an iterable. "
                                        "It will be written as it is.".format(attr))
                    warnflag = 1

                elif self.__graph[attr] is None:
                    out.write(attr + '\tNA' + '\n')
                else:
                    out.write(attr + '\t' + str(self.__graph[attr]) + '\n')
        
        sys.stdout.write(u"Graph attributes successfully exported at path {}.\n".format(os.path.abspath(file)))
