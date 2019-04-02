__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t,mazza@css-mendel.it>
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
    using the canonical igraph notation for attributes (a :py:class:`dict` structure, in which the attribute name is the key``
    and any object associated to it is its ``value``.
    """

    @staticmethod
    def add_graph_attribute(graph: Graph, attr_name: str, attr: object):
        r"""
        Add an attribute to a :py:class:`~igraph.Graph` object at the graph level.

        .. warning:: if the graph attribute name (``attr_name``) is already initialized, it will be overwritten by this method.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str attr_name: The name of the attribute being added
        :param object attr: Any object being added as attribute
        :raise TypeError: if ``graph`` is not a :py:class:`~igraph.Graph` object or if ``attr_name`` is not a string
        """

        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"Graph argument is not a igraph.Graph")

        if not isinstance(attr_name, str):
            raise TypeError(u"Attribute name is not a string")

        if attr_name in graph.attributes():
            sys.stdout.write("Graph attribute {} already present, will overwrite\n".format(attr_name))

        sys.stdout.write("Graph attribute {} added\n".format(attr_name))
        graph[attr_name] = attr

    @staticmethod
    def add_node_attribute(graph: Graph, attr_name: str, attr_list: list, nodes: list):
        r"""
        Add attributes at the vertex level of a :py:class:`~igraph.Graph` object. These attributes must be stored in a
        :py:class:`list` whose elements must be sorted by ``nodes`` (a list of string storing the vertex ``name``
        attribute).

        .. warning:: if the vertex attribute name (``attr_name``) is already initialized, it will be overwritten by this method.

        :param igraph.Graph graph: a :class:`igraph.Graph` object.
        :param str attr_name: The name of the attribute that will be added to the :py:class:`~igraph.Graph`
        :param list attr_list: alist of object, sorted by the ``nodes`` parameter. Each object will be adced singularly to the corresponding node
        :param list nodes: the vertex ``name`` attribute corresponding to the vertices to which attributes will be added..
        :raise TypeError: if any of the arguments is not of the expected type
        :raise WrongArgumentError: If all the attributes pointed to non-existing nodes.
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(attr_name, str):
            raise TypeError(u"Attribute name is not a string")
        
        if isinstance(nodes, str):
            sys.stdout.write(u"Converting string nodes to list of nodes\n")
            nodes = [nodes]

        assert len(attr_list) == len(nodes), u"In add_node_attribute, length of attributes list cannot be " \
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
            sys.stdout.write(u"Node attribute {} added\n".format(attr_name))

    @staticmethod
    def add_edge_attribute(graph: Graph, attr_name: str, attr_list: list, edges: list):
        r"""
        Add edge attributes to the input :py:class:`igraph.Graph` object under the attribute name specified in ``attr_name``.
        The attributes must be stored in a list, passed to ``attr_list`` and sorted according to the target edge list,
        specified in ``edges``.

        .. warning:: if the vertex attribute name (``attr_name``) is already initialized, it will be overwritten by this method.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str attr_name: string. The name of the attribute being added to the edges of the Graph.
        :param list attr_list: a list, sorted by vertex index, storing the values that will be added to each target edge.
        :param list edges: edges to which attributes will be applied.
        :raise TypeError: if ``graph`` is not a :py:class:`~igraph.Graph`
        :raise ValueError: if one of the edges IDs points to more than one edge (edge names must be univocal)
        :raise WrongArgumentError: if all the ``edges`` does not point to existing ones
        """

        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(attr_name, str):
            raise TypeError("Attribute name is not a string")
        
        assert len(attr_list) == len(edges), u"in add_edge_attribute, length of attributes list cannot be " \
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
                raise ValueError(u"Edge %s has multiple name hits, edge `adjacent_nodes` must be univocal")

        if err_count == count:
            raise WrongArgumentError("All the attributes pointed to non-existing edges.")
        else:
            sys.stdout.write("Edge attribute {} added\n".format(attr_name))

    @staticmethod
    def add_edge_names(graph: Graph, readd: bool=False):
        r"""
        Initialize (or rewrite, according to the ``readd`` flag) the edge attribute ``adjacent_nodes`` that allows to
        identify an edge by the vertices it is linking.

        This attribute points for each edge to a tuple containing the two vertices (their graph ``name`` attributes),
        sorted alphanumerically.

        As Pyntacle does not allow multigraphs, this attribute is used to identify an edge when performing queries on edges.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param bool readd: a :py:class:`bool` that specifies whether the edge names should be re-added to the input graph or not
        :raise TypeError: if ``graph`` is not a :py:class:`~igraph.Graph`
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        if not isinstance(readd, bool):
            raise TypeError(u"`readd` must be a boolean {} found".format(type(readd).__name__))

        if readd is True or "adjacent_nodes" not in graph.es.attributes():
            # sys.stdout.write("Adding attribute 'adjacent_nodes' to each edge (will be stored as a tuple)\n")
            edge_names = []
            for e in graph.get_edgelist():
                # print("{0}, {1}".format(self.graph.vs[e[0]]["name"], self.graph.vs[e[1]]["name"]))
                edge_names.append(tuple(sorted(tuple((graph.vs[e[0]]["name"], graph.vs[e[1]]["name"])))))
            graph.es["adjacent_nodes"] = edge_names
        else:
            sys.stdout.write(u"attribute 'adjacent_nodes' already exists\n")

    @staticmethod
    def add_graph_name(graph: Graph, name: str):
        r"""
        Initialize or replace the graph ``name`` Pyntacloe reserved attribute with the value stored in the ``name``
        parameter. This attribute is a :py:class:`list` that stores the name (or names) of the graph.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str name: a string representing the name of the graph to be added.
        :raise TypeError: if ``graph`` is not a :py:class:`~igraph.Graph`
        """
        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a igraph.Graph")

        #sys.stdout.write(u"adding attribute 'name' to the graph")

        graph["name"] = [name]

    @staticmethod
    def add_parent_name(graph: Graph):
        r"""
        Add the graph ``name`` attribute to each vertex, under the ``parent`` reserved attribute. This attribute is a
        :py:class:`list` that is updated when performing set operations by means of the :class:`~pyntacle.graph_operations.set_operations.GraphSetOps`
        module, and it is used to keep track of the graph of origin of each vertex.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :raise TypeError: if ``graph`` is not a :py:class:`~igraph.Graph`
        """

        if not isinstance(graph, Graph) is not Graph:
            raise TypeError(u"graph argument is not a 'igraph.Graph'")



        #sys.stdout.write(u"adding reserved attribute '__parent' to the vertices")

        graph.vs["parent"] = graph["name"]
