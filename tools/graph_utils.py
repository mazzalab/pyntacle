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
import numpy as np
from exceptions.unsupported_graph_error import UnsupportedGraphError
from exceptions.wrong_argument_error import WrongArgumentError
from exceptions.multiple_solutions_error import MultipleSolutionsError
from tools.enums import CmodeEnum
from tools.add_attributes import AddAttributes
from internal.name_checker import attribute_name_checker

class GraphUtils:

    logger = None

    def __init__(self, graph: Graph):
        r"""
        A set of generic utilities for determining the structural integrity of the graph and retrieve some of its parts.
        Additionally, it contains methods to initialize the :py:class:`~igraph.Graph` object for Pyntacle usage.

        :param igraph.Graph graph: a :py:class:`~igraph.Graph` object.
        :raise NotAGraphError: if ``graph`` is not an ``igraph.Graph`` object
        """
        self.logger = log

        if not isinstance(graph, Graph):
            raise TypeError(u"'graph' if not an igraph.Graph object ")

        else:
            self.graph = graph

    def set_graph(self, graph: Graph):
        r"""
        Replaces the :py:class:`igraph.Graph` object with another one.

        :param graph: a :py:class:`igraph.Graph` object
        """
        self.graph = graph
        self.check_graph()

    def check_graph(self):
        r"""
        Check that the input graph is compliant to the `Pyntacle minimum  graph requirements <http://pyntacle.css-mendel.it/requirements.html>`_.
        Raise an appropriate error if it is not so, otherwise return :py:class:`None`.

        :raise UnsupportedGraphError: if the :py:class:`igraph.Graph` is not compliant to `Pyntacle minimum requirements <http://pyntacle.css-mendel.it/>`_.
        :raise KeyError: If the graph vertices does not hold a vertex ``name`` attribute
        :raise TypeError: if any of the :py:class:`~igraph.Graph` attributes types differs from the one listed in `Pyntacle minimum requirements <http://pyntacle.css-mendel.it/>`_.
        """

        if Graph.is_directed(self.graph):
            raise UnsupportedGraphError(u"Graph is direct")
        if not Graph.is_simple(self.graph):
            raise UnsupportedGraphError(u"Graph contains self-loops and multiple edges")
        if self.graph.vcount() < 2:
            raise UnsupportedGraphError(u"Graph must contain at least two nodes")

        if self.graph.ecount() < 1:
            raise UnsupportedGraphError(u"Graph must contain at least one edge")

        if "name" not in self.graph.vs.attributes() and all(x == str for x in self.graph.vs()["name"]):
            raise KeyError(u"Nodes must have the attribute 'name' and it must be filled with strings")

        if len(set(self.graph.vs["name"])) != len(self.graph.vs["name"]):
            raise UnsupportedGraphError(u"Node 'name' attribute  must be unique, check the \"name\" attribute in graph")

        if "name" not in self.graph.attributes():
            raise UnsupportedGraphError(u"Graph must have a 'name' attribute")

        else:
            if not isinstance(self.graph["name"], list):
                raise TypeError(u"Graph 'name' attribute must be a list.")
            else:
                if not any([isinstance(x, str) for x in self.graph["name"]]):
                    raise TypeError(u"One of the graph 'names' is not a string")

                for name in self.graph["name"]:
                    try:
                        attribute_name_checker(name)
                    except ValueError:
                        raise UnsupportedGraphError(u"Any of the Graph 'name' attribute values contains illegal characters.")

        if any(x not in self.graph.attributes() for x in ["implementation"]):
            #print(self.graph.attributes())

            raise UnsupportedGraphError(u"One of the Pyntacle reserved graph attribute is missing, see goo.gl/MCsnd1 for more informations and initialize the `graph_initializer` method in `tools.graph_utils` To initialize your graph.")

        else:

            if not isinstance(self.graph["implementation"], CmodeEnum):
                raise TypeError("implementation must be filled with one of the CmodeEnums")

        if any(x not in self.graph.vs.attributes() for x in ["parent"]):
            raise UnsupportedGraphError(u"Pyntacle reserved vertex attribute missing, see goo.gl/MCsnd1 for more informations and initialize the `graph_initializer` method in `tools.graph_utils` To initialize your graph.")
        else:
            if not isinstance(self.graph.vs["parent"], (list, type(None))):
                raise TypeError("`parent` node attribute must be either a list or None")

            else:
                if not any([isinstance(x, (str, list)) for x in self.graph.vs["parent"]]):
                    raise TypeError(u"One of the graph 'parent' attribute values is not a string")

        if any(x not in self.graph.es.attributes() for x in ["adjacent_nodes"]):
            raise UnsupportedGraphError(u"Pyntacle reserved edge attribute missing, see goo.gl/MCsnd1 for more informations")

        else:
            if not any(isinstance(x, tuple) for x in self.graph.es["adjacent_nodes"]):
                raise TypeError("adjacent_nodes must be a tuple of strings")

    def check_index_list(self, indices: list):
        r"""
        Check that an index list (a list of integers representing the numeric indices of the graph vertices)
        is present into the input :py:class:`~igraph.Graph` objects. These indices should be positive integers ranging
        from :math:`0` to :math:`N-1`, where :math:`N` is the size of the graph.

        :param list indices: a list of  positive integers
        :raise ValueError: if ``indices`` is not a list of integers
        :raise WrongArgumentError: if any of the elements in ``indices`` does not exists in the graph.
        """

        if not isinstance(indices, list):
            raise ValueError(u"index list is not a list")

        if len(indices) == 0:
            raise WrongArgumentError(u"List is empty")

        for ind in indices:
            if not isinstance(ind, int) or ind < 0:
                raise ValueError("indices must be positive integers")

        if set(indices) > set(self.graph.vs.indices):
            raise WrongArgumentError(u"The input node index '{}' does not exist in the graph".format(indices))

        return None

    def nodes_in_graph(self, names: list or str) -> bool:
        r"""
        Scans a list of strings and checks whether they are present in the input :py:class:`~igraph.Graph` vertex names
        (by looking at the vertex ``name`` attribute).

        :param list names: a list of strings, corresponding to the vertex ``name`` attribute
        :return bool: ``True`` if all the element in ``names`` are present in the input :py:class:`~igraph.Graph`, ``False`` otherwise
        :raise ValueError: if ``names`` is not a list, an empty list or if any of the elements in ``names`` is not a :py:class:`str`
        """

        if isinstance(names, str):
            names = [names]

        elif not isinstance(names, list):
            raise ValueError(u"`names` must be a list")

        if len(names) < 0:
            raise ValueError(u"`names` is empty")

        for name in names:
            if not isinstance(name, str):
                raise ValueError(u"Node names must be strings")

            if name not in self.graph.vs()["name"]:
                sys.stdout.write("node {} is not in vertex `name` attribute".format(name))
                return False

        return True

    def attribute_in_nodes(self, attribute: str) -> bool:
        r"""
        Checks that a given attribute name is present in the input :py:class:`igraph.Graph` object as vetex (node) attribute.

        :param str attribute: the name of a vertex  attribute of interest.
        :return bool: ``True`` if the attribute is present in the vertex attributes, ``False`` otherwise.
        """

        if attribute not in self.graph.vs().attributes():
            return False
        return True

    def attribute_in_edges(self, attribute: str) -> bool:
        r"""
        Checks that a given attribute name is present in the input :py:class:`igraph.Graph` object as edge attribute.

        :param str attribute: the name of an edge attribute of interest.
        :return bool: ``True`` if the attribute is present in the edge attributes, ``False`` otherwise.
        """

        if attribute not in self.graph.es().attributes():
            return False

        return True

    def attribute_in_graph(self, attribute: str) -> bool:
        r"""
        Checks that a given attribute name is present in the input :py:class:`igraph.Graph` object as graph attribute.

        :param str attribute: the name of a graph attribute of interest.
        :return bool: ``True`` if the attribute is present in  the graph attributes, ``False`` otherwise.
        """

        if attribute not in self.graph.attributes():
            return False

        return True

    def get_node_names(self, indices: list) -> list:
        r"""
        Takes a list of integers that matches the node indices of the input :py:class:`~igraph.Graph` object and returns
        the corresponding vertex ``name`` attribute of each node matching each index.

        :param list indices: A list of integers containing indices present in graph. Inherits the :func:`~pyntacle.tools.graph_utils.GraphUtils.check_index_list` for checking the integrity of the ``indices`` argument.
        :return: A list of strings, storing the corresponding vertex ``name`` attribute
        """

        self.check_index_list(indices)
        names_list = self.graph.vs(indices)["name"]
        return names_list

    def get_node_indices(self, nodes: str or list) -> list:
        r"""
        Return a list of integers representing the corresponding vertex index of each of the elements in the ``nodes``
        argument (a :py:class:`str` or a py:class:`list` storing the vertex ``name`` attribute)

        :param str, list nodes: A string or a list of strings storing the vertex ``name`` attribute
        :return list: a list of indices of the corresponding node names given in input. The order of the input list is preserved
        :raise IndexError: if the node ``name`` of the input graph are not unique
        :raise ValueError: if any of the elements in ``nodes`` is not present in the input graph.
        """

        if not isinstance(nodes, list):
            names = [nodes]
        else:
            names = nodes

        if self.nodes_in_graph(nodes):
            index_list = []

            for name in names:
                select = self.graph.vs.select(name=name)
                if len(select) > 1:
                    raise IndexError(u"name is not unique, node names must be unique, please check your graph")

                else:
                    index = select[0].index
                    index_list.append(index)

            return index_list

        else:
            raise ValueError(u"One of the `nodes` is not present in the input Graph")

    def get_largest_component(self) -> Graph:
        r"""
        Returns the largest component component of a :py:class:`~igraph.Graph`, while retaining all the attributes
        of the original graph at all levels.

        .. warning: If the graph has two largest components of the same size, the method will raise an error.

        :return igraph.Graph: a :py:class:`~igraph.Graph` object storing the largest component. all other components will be pruned.
        :raise MultipleSolutionsError: if there is more than one largest component in the input :py:class:`~igraph.Graph`
        """

        self.logger.info(u"Getting the largest component of the input graph")

        components = self.graph.components()

        comp_len = [len(comp) for comp in components]
        self.logger.info(u"Graph has the following components: {}".format(",".join(map(str, comp_len))))

        max_comp = max(comp_len)
        max_ind = np.argmax(comp_len)

        max_list = [i for i, x in enumerate(comp_len) if x == max_comp]

        if len(max_list) > 1:
            raise MultipleSolutionsError(u"There are {} largest components, cannot choose one".format(len(max_list)))

        else:
            subgraph = self.graph.induced_subgraph(components[max_ind])

            self.logger.info(
                u"Largest component has {0} nodes and {1} edges (out of {2} nodes and {3} edges in total)".format(
                    subgraph.vcount(), subgraph.ecount(), self.graph.vcount(), self.graph.ecount()))

            return subgraph

    def prune_isolates(self):
        r"""
        Remove any disconnected vertex (node isolate) from the :py:class:`~igraph.Graph` object, pruning  it of all the
        isolates that contribute to the initial graph size but have no connection to any graph component of size at
        least two. Adds a graph attribute named ``isolates``, storing the vertex``name`` attribute of each of the node
        isolates that are removed by this method.

        .. note:: This method is used by the :func:`~pyntacle.tools.graph_utils.GraphUtils.graph_initializer` when initializing the graph to remove the isolates
        """

        init_size = self.graph.vcount()
        copy_graph = self.graph.copy() #the graph that will replace the self.graph object
        degr_nodes = self.graph.degree()
        isolates_ind = [i for i, x in enumerate(degr_nodes) if x == 0] #list of node indices to be removed.


        if len(isolates_ind) >= 1:
            removed_nodes = self.get_node_names(isolates_ind) #a list storing the vertex name attribute
            rem_size = init_size - len(removed_nodes)
            sys.stdout.write(u"WARNING: the following isolates will be removed from the input graph:\n{}\n"
                             u"Leaving {} nodes out of {}\nThe node names will be stored in the 'isolates' graph "
                             u"attribute\n".format(",".join(removed_nodes), rem_size, init_size))
            copy_graph.delete_vertices(isolates_ind)
            copy_graph["isolates"] = removed_nodes
            self.graph = copy_graph #replace the self.graph object

        else:
            self.logger.info(u"No isolate nodes")
            self.graph["isolates"] = None

    def graph_initializer(self, graph_name: str, node_names: list or None = None):
        r"""
        Transform the input :py:class:`igraph.Graph` object into a network that is compliant to the
        Pyntacle `Minimum requirements <http://pyntacle.css-mendel.it/requirements.html>`_.

        .. warning:: This method will prune the graph of any node isolates, as they are not accepted by Pyntacle.

        :param str graph_name: The network name (will be stored in the graph ``name`` attribute). This string must not contain illegal characters (see the Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_ for more info on the illegal characters.
        :param str, None node_names: optional, a list of strings matching the total number of vertices of the graph. Each item in the list becomes the vertex ``name`` attribute sequentially (index-by-index correspondance). Defaults to py:class:`None` (node ``name`` attribute is filled by node indices).
        :raise: ValueError: if the ``graph_name`` argument contains illegal characters or if ``node_names`` is not of the same size of the number of graph vertices.
        :raise: WrongArgumentError: if ``node_names`` is not a list of strings.
        """

        if not isinstance(graph_name, str):
            raise ValueError("'graph_name' must be a string")

        try:
            attribute_name_checker(graph_name)
        except ValueError:
            raise ValueError("'graph_name' contains illegal characters\n")

        self.graph.to_undirected()  # reconvert graph to directed
        if "name" not in self.graph.attributes():
            self.logger.info(u"Adding file name to graph name")
            AddAttributes.add_graph_name(self.graph, graph_name)

        # add vertex names
        if "name" not in self.graph.vs.attributes():
            if node_names is None:
                self.logger.info(u"Adding node names to graph corresponding to their indices")
                self.graph.vs()["name"] = [str(x.index) for x in self.graph.vs()]

            else:
                if not isinstance(node_names, list) or not all(isinstance(item, str) for item in node_names):
                    raise WrongArgumentError(u"`node_names` argument must be a list of strings")

                if len(node_names) != self.graph.vcount():
                    raise ValueError(u"`node_names` argument must be of the same length of vertices")

                self.logger.info(u"Adding node names to graph using the provided node names")
                self.graph.vs["name"] = node_names

        # add parent name to vertices
        if "parent" not in self.graph.vs().attributes():
            self.logger.info(u"Adding reserved attribute 'parent' to the vertices")
            AddAttributes.add_parent_name(self.graph)

        if "adjacent_nodes" not in self.graph.es().attributes():
            # add edge vertices names as an attribute 'adjacent_vertices'
            self.logger.info(u"Adding source and target names as 'adjacent_nodes' attribute to edges")
            AddAttributes.add_edge_names(self.graph)

        # for sif file conversion purposes
        if not "sif_interaction_name" in self.graph.attributes():
            self.graph["sif_interaction_name"] = None

        if not "sif_interaction" in self.graph.es().attributes():
            self.graph.es()["sif_interaction"] = None

        self.prune_isolates() #remove any isolate and store them into the `isolates` graph attribute

        # Adding implementation for functions that require it
        sp_implementation = CmodeEnum.igraph

        n_nodes = self.graph.vcount()

        if n_nodes > 100:
            density = (2 * (self.graph.ecount())) / (n_nodes * (n_nodes - 1))
            if density < 0.5 and n_nodes <= 500:
                sp_implementation = CmodeEnum.igraph
            else:
                if cuda_avail:
                    sp_implementation = CmodeEnum.gpu
                else:
                    if n_cpus >= 2:
                        sp_implementation = CmodeEnum.cpu
                    else:
                        sp_implementation = CmodeEnum.igraph

        self.graph["implementation"] = sp_implementation
        # self.check_graph() #check that everything is in order

    def get_graph(self) -> Graph:
        r"""
        Returns the igraph.Graph object.

        :return igraph.Graph: A :py:class:`~igraph.Graph` object
        """

        return self.graph

