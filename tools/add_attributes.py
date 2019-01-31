__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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
from exceptions.wrong_argument_error import WrongArgumentError

class AddAttributes:
    r"""
    Add specific and generic properties to any of the py:class:`igraph.Graph` object layers (graph, vertices and edges)

    :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.

    """

    @staticmethod
    def add_graph_attributes(graph: Graph, attr_name: str, attr: object):
        r"""
        Add an attribute to a graph object. if ``attr`` is a :py:class:`dict`and the input :py:class:`~igraph.Graph`
        already points to an existing dictionary, this is updated

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object
        :param str attr_name: The name of the attribute being added
        :param object attr: Any object being added as attribute
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(attr_name, str):
            raise TypeError(u"Attribute name is not a string")

        if attr_name in graph.attributes():
            sys.stdout.write("graph attribute {} already present, will overwrite\n")

        graph[attr_name] = attr

    @staticmethod
    def add_node_attributes(graph: Graph, attr_name: str, attr_list: list, nodes: list):
        r"""
        This method takes an header file and, optionally, a separator, and add them to a graph imprted in __init

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object
        :param attr_list: the object being added as attribute
        :param attr_name: string. The name of the attribute being imported
        :param nodes: list. Nodes to which attributes will be applied.
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(attr_name, str):
            raise TypeError(u"Attribute name is not a string")
        
        if isinstance(nodes, str):
            sys.stdout.write(u"Converting string nodes to list of nodes\n")
            nodes = [nodes]

        
        assert len(attr_list) == len(nodes), u"in add_node_attributes, length of attributes list cannot be " \
                                             "different from length of list of nodes."
        
        count = 0
        err_count = 0
        for n, a in zip(nodes, attr_list):
            select = graph.vs.select(name=n)
            count += 1
            if len(select) == 0:
                sys.stdout.write(u"Node %s not found in graph" % n)
                err_count += 1

            elif len(select) == 1:
                select[0][attr_name] = a

            else:
                sys.stdout.write(u"Node %s has multiple name hits, please check your attribute file\n" % n)
                raise ValueError(u"Multiple node hits")
        
        if err_count == count:
            raise WrongArgumentError(u"All the attributes pointed to non-existing nodes.")
        else:
            sys.stdout.write(u"Node attribute {} successfully added!\n".format(attr_name))

    @staticmethod
    def add_edge_attributes(graph: Graph, attr_name: str, attr_list: list, edges: list):
        r"""
        Add edge attributes to the target a :py:class:`igraph.Graph` object under the attribute name specified in ``attr_name``

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object
        :param attr_name: string. The name of the attribute being imported
        :param attr_list: the object being added as attribute
        :param edges: list. edges to which attributes will be applied.
        """

        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(attr_name, str):
            raise TypeError("Attribute name is not a string")
        
        assert len(attr_list) == len(edges), u"in add_edge_attributes, length of attributes list cannot be " \
                                             "different from length of list of nodes."
        count = 0
        err_count = 0
        for e, a in zip(edges, attr_list):
            select = graph.es.select(adjacent_nodes=e)
            if len(select) == 0:
                select = graph.es.select(adjacent_nodes=(e[1], e[0]))
            count += 1
            if len(select) == 0:
                sys.stdout.write(u"Edge %s not found in graph\n" %str(e))
                err_count += 1
            
            elif len(select) == 1:
                select[0][attr_name] = a
                
            else:
                raise ValueError(u"Edge %s has multiple name hits, edge names must be univocal")

        if err_count == count:
            raise WrongArgumentError("All the attributes pointed to non-existing edges.")

    @staticmethod
    def add_edge_names(graph: Graph, readd: bool=False):
        r"""
        Add adjacent edge as attribute stored in a tuple to each edge

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object
        :param bool: a :py:class:`bool` that specifies whether the edge names should be re-added or not
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(readd, bool):
            raise TypeError(u"object is not a igraph.Graph")

        if readd is True or "adjacent_nodes" not in graph.es.attributes():
            # sys.stdout.write("Adding attribute 'adjacent_nodes' to each edge (will be stored as a tuple).\n")
            edge_names = []
            for e in graph.get_edgelist():
                # print("{0}, {1}".format(self.graph.vs[e[0]]["name"], self.graph.vs[e[1]]["name"]))
                edge_names.append((graph.vs[e[0]]["name"], graph.vs[e[1]]["name"]))
            graph.es["adjacent_nodes"] = edge_names
        else:
            sys.stdout.write(u"attribute 'adjacent_nodes' already exists\n")

    @staticmethod
    def add_graph_name(graph: Graph, name: str):
        r"""
        Initialize or replace the graph ``name`` attribute with the value stored in the ``namestring`` parameter.

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object
        :param str name: a string representing the name of the graph to be added.
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        #sys.stdout.write(u"adding attribute 'name' to the graph")

        graph["name"] = [name]

    @staticmethod
    def add_parent_name(graph: Graph):
        r"""
        Add the graph ``name`` attribute to each vertex, under the ``parent``  reserved attribute.

        :param igraph.Graph graph: a :py:class:`igraph.Graph` object
        """

        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")



        #sys.stdout.write(u"adding reserved attribute '__parent' to the vertices")

        graph.vs["parent"] = graph["name"]
