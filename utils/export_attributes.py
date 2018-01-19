# external libraries
from config import *
import os
from collections import Iterable
from igraph import Graph
from exception.notagraph_error import NotAGraphError

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The pyntacle Project"
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

class ExportAttributes():
    """
    **[EXPAND]**
    """
    logger = None

    def __init__(self, graph: Graph):

        self.logger = log

        if type(graph) is not Graph:
            raise NotAGraphError("object is not a igraph.Graph")


        else:
            self.__graph = graph

    def export_edge_attributes(self, filename, mode='standard'):
        """
        **[EXPAND]**

        :param filename:
        :param mode:
        :return:
        """
        
        warnflag = 0
        if not os.path.exists(os.path.dirname(filename)):
            self.logger.warning("The directory tree for the output file does not exist, it will be created")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as out:
            # Writing header
            attributes_tokeep = [x for x in self.__graph.es()[0].attributes() if
                                 x != 'node_names' and not x.startswith('__')]

            if mode == 'standard':
                out.write('Node1' + '\t' + 'Node2' + '\t' + '\t'.join(attributes_tokeep) + '\n')
            else:
                out.write('Edge(Cytoscape Format)' + '\t' + '\t'.join(attributes_tokeep) + '\n')

            for e in self.__graph.es():
                if mode == 'standard':
                    out.write(str(e.attributes()['node_names'][0]) + '\t')
                    out.write(str(e.attributes()['node_names'][1]))
                else:
                    out.write(str(e.attributes()['node_names'][0]) + ' ')
                    if e.attributes()['__sif_interaction'] is None:
                        out.write('(interacts with) ')
                    else:
                        out.write('(' + e.attributes()['__sif_interaction'] + ') ')
                    out.write(str(e.attributes()['node_names'][1]))

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

    def export_node_attributes(self, filename):
        """
        **[EXPAND]**
        
        :param filename:
        :return:
        """
        warnflag = 0
        if not os.path.exists(os.path.dirname(filename)):
            self.logger.warning("The directory tree for the output file does not exist, it will be created")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as out:
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

    def export_graph_attributes(self, filename):
        """
        **[EXPAND]**
        
        :param filename:
        :return:
        """
        warnflag = 0
        if not os.path.exists(os.path.dirname(filename)):
            self.logger.warning(
                "The directory tree for the output file does not exist, it will be created")
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'w') as out:
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
                    self.logger.warning("The attribute {} looks like an iterable. "
                                        "It will be written as it is.".format(attr))
                    warnflag = 1

                elif self.__graph[attr] is None:
                    out.write(attr + '\tNA' + '\n')
                else:
                    out.write(attr + '\t' + str(self.__graph[attr]) + '\n')
