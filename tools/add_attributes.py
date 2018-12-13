__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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

from config import *
from igraph import Graph
from tools.enums import CmodeEnum
from exceptions.wrong_argument_error import WrongArgumentError
from exceptions.illegal_argument_number_error import IllegalArgumentNumberError


class AddAttributes:
    r"""
    Add specific and generic properties to any of the py:class:`igraph.Graph` object elements

    :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

    """

    logger = None

    def __init__(self, graph: Graph):
        self.logger = log
        if type(graph) is not Graph:
            raise WrongArgumentError(u"object is not a igraph.Graph")
        else:
            self.__graph = graph

    def add_graph_attributes(self, attr_name: str, attr: object):
        r"""
        Add an attribute to a graph object

        :param str attr_name: The name of the attribute being imported
        :param object attr: Any object being added as attribute
        """

        if not isinstance(attr_name, str):
            raise TypeError(u"Attribute name is not a string")
        else:
            if isinstance(attr, dict):
                if attr_name in self.__graph.attributes():
                    self.__graph[attr_name].update(attr)
                else:
                    self.__graph[attr_name] = attr

            else:
                self.__graph[attr_name] = attr

    def add_node_attributes(self, attr_name: str, attr_list: list, nodes: list):
        r"""
        This method takes an header file and, optionally, a separator, and add them to a graph imprted in __init

        :param attr_list: the object being added as attribute
        :param attr_name: string. The name of the attribute being imported
        :param nodes: list. Nodes to which attributes will be applied.
        """

        if not isinstance(attr_name, str):
            raise TypeError(u"Attribute name is not a string")
        
        if isinstance(nodes, str):
            self.logger.warning(u"converting string nodes to list of nodes")
            nodes = [nodes]
        if attr_name.startswith('__'):
            raise KeyError(
                u"One of the attributes being added starts with __ (double underscore)."
                "This notation is reserved to internal variables, please avoid using it.")
        
        assert len(attr_list) == len(nodes), u"in add_node_attributes, length of attributes list cannot be " \
                                             "different from length of list of nodes."
        
        count = 0
        err_count = 0
        for n, a in zip(nodes, attr_list):
            select = self.__graph.vs.select(name=n)
            count += 1
            if len(select) == 0:
                self.logger.warning(u"Node %s not found in graph" % n)
                err_count += 1
            elif len(select) == 1:
                select[0][attr_name] = a
            else:
                self.logger.error(u"Node %s has multiple name hits, please check your attribute file" % n)
                raise ValueError(u"Multiple node hits")
        
        if err_count == count:
            raise WrongArgumentError(u"All the attributes pointed to non-existing nodes.")
        else:
            self.logger.info(u"Node attribute {} successfully added!".format(attr_name))

    def add_edge_attributes(self, attr_name: str, attr_list: list, edges: list):
        r"""
        Add edge attributes specified in a file like (nodeA/nodeB/listofvalues)


        :param attr_name: string. The name of the attribute being imported
        :param attr_list: the object being added as attribute
        :param edges: list. edges to which attributes will be applied.

        :return str:
        """

        if not isinstance(attr_name, str):
            raise TypeError("Attribute name is not a string")
        
        # Checking if one or more attributes' names start with '__'. Avoids malicious injection.
        if attr_name.startswith('__'):
            raise KeyError(
                u"One of the attributes in your attributes/weights file starts with `__`."
                "This notation is reserved to internal variables, please avoid using it.")
        
        assert len(attr_list) == len(edges), u"in add_edge_attributes, length of attributes list cannot be " \
                                             "different from length of list of nodes."
        count = 0
        err_count = 0
        for e, a in zip(edges, attr_list):
            select = self.__graph.es.select(adjacent_nodes=e)
            if len(select) == 0:
                select = self.__graph.es.select(adjacent_nodes=(e[1], e[0]))
            count += 1
            if len(select) == 0:
                self.logger.warning(u"Edge %s not found in graph" %str(e))
                err_count += 1
            
            elif len(select) == 1:
                select[0][attr_name] = a
                
            else:
                self.logger.error(u"Edge %s has multiple name hits, please check your attribute file" % str(e))
                raise ValueError(u"Multiple edge hits")
        
        if err_count == count:
            raise WrongArgumentError("All the attributes pointed to non-existing edges.")

    def add_edge_names(self, readd: bool=False):
        r"""
        Add adjacent edge as attribute stored in a tuple to each edge

        :param bool: a :py:class:`bool` that specifies whether the edge names should be re-added or not
        """

        if readd is True or "adjacent_nodes" not in self.__graph.es.attributes():
            self.logger.info("adding attribute 'adjacent_nodes' to each edge (will be stored as a tuple)")
            edge_names = []
            for e in self.__graph.get_edgelist():
                # print("{0}, {1}".format(self.__graph.vs[e[0]]["name"], self.__graph.vs[e[1]]["name"]))
                edge_names.append((self.__graph.vs[e[0]]["name"], self.__graph.vs[e[1]]["name"]))
            self.__graph.es["adjacent_nodes"] = edge_names
        else:
            self.logger.info(u"attribute 'adjacent_nodes' already exist")

    def add_graph_name(self, namestring: str):
        r"""
        Initialize or replace the graph ``name`` attribute with the value stored in the ``namestring`` parameter.

        :param str namestring: a string representing the name of the graph to be added.
        """

        self.logger.info(u"adding attribute 'name' to the graph")

        self.__graph["name"] = [namestring]

    def add_parent_name(self):
        r"""
        Add the graph ``name`` attribute to each vertex, under the ``__parent``  reserved attribute.
        """

        self.logger.info(u"adding reserved attribute '__parent' to the vertices")

        self.__graph.vs["__parent"] = self.__graph["name"]

    def graph_initializer(self, graph_name: str, node_names: list or None= None):
        r"""
        Turns the input :py:class:`igraph.Graph` object into a Ptyntacle-ready network by making it compliant to the
        Pyntacle `Minimum requirements <http://pyntacle.css-mendel.it/requirements.html>`_

        :param str graph_name: The network name (will be stored in the graph ``name`` attribute
        :param str, None node_names: optional, a list of strings matching the total number of vertices of the graph. Each item in the list becomes the vertex ``name`` attribute sequentially (index-by-index correspondance). Defaults to py:class:`None` (node ``name`` attribute is filled by node indices).
        """
        self.__graph.to_undirected() #reconvert graph to directed
        if "name" not in self.__graph.attributes():
            self.logger.info(u"adding file name to graph name")
            self.add_graph_name(graph_name)


        #add vertex names
        if "name" not in self.__graph.vs.attributes():
            if node_names is None:
                self.logger.info(u"adding node names to graph corresponding to their indices")
                self.__graph.vs()["name"] = [str(x.index) for x in self.__graph.vs()]

            else:
                if not isinstance(node_names, list) or not all(isinstance(item, str) for item in node_names):
                    raise WrongArgumentError(u"node names must be a list of strings")

                if len(node_names) != self.__graph.vcount():
                    raise IllegalArgumentNumberError(u"node names must be of the same length of vertices")

                self.logger.info(u"Adding node names to graph using the provided node names")
                self.__graph.vs["name"] = node_names


        #add parent name to vertices
        if "__parent" not in self.__graph.vs().attributes():
            self.logger.info(u"adding reserved attribute '__parent' to the vertices")
            self.add_parent_name()

        if "adjacent_nodes" not in self.__graph.es().attributes():

            # add edge vertices names as an attribute 'adjacent_vertices'
            self.logger.info(u"adding source and target names as \"adjacent_nodes\" attribute to edges")
            self.add_edge_names()
        # for sif file conversion purposes
        if not "__sif_interaction_name" in self.__graph.attributes():
            self.__graph["__sif_interaction_name"] = None

        if not "__sif_interaction" in self.__graph.es().attributes():
            self.__graph.es()["__sif_interaction"] = None
            

        #Adding implementation info for functions that require it
        sp_implementation = CmodeEnum.igraph

        n_nodes = self.__graph.vcount()

        if n_nodes > 100:
            density = (2*(self.__graph.ecount()))/(n_nodes*(n_nodes-1))
            if density < 0.5 and n_nodes <=500:
                sp_implementation = CmodeEnum.igraph
            else:
                if cuda_avail:
                    sp_implementation = CmodeEnum.gpu
                else:
                    if n_cpus >= 2:
                        sp_implementation = CmodeEnum.cpu
                    else:
                        sp_implementation = CmodeEnum.igraph
        
        self.__graph["__implementation"] = sp_implementation
