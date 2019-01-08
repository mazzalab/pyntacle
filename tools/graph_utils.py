"""
Generic utilities for graph management and safety checks
"""

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
import numpy as np
from exceptions.illegal_graph_size_error import IllegalGraphSizeError
from exceptions.missing_attribute_error import MissingAttributeError
from exceptions.notagraph_error import NotAGraphError
from exceptions.unsupported_graph_error import UnsupportedGraphError
from exceptions.wrong_argument_error import WrongArgumentError
from exceptions.multiple_solutions_error import MultipleSolutionsError
from exceptions.illegal_argument_number_error import IllegalArgumentNumberError
from tools.enums import CmodeEnum
from tools.add_attributes import AddAttributes
from internal.name_checker import attribute_name_checker

class GraphUtils:
    r"""
    A set of generic utilities for determining the structural integrity of the graph and retrieve its properties.
    """

    logger = None

    def __init__(self, graph: Graph):
        self.logger = log

        if not isinstance(graph, Graph):
            raise NotAGraphError(u"input graph is not a graph")

        if graph.vcount() < 1:
            raise IllegalGraphSizeError(u"This graph does not contain vertices")

        elif graph.ecount() < 1:
            raise IllegalGraphSizeError(u"This graph does not contain edges")

        else:
            self.__graph = graph

    def check_graph(self) -> bool:
        r"""
        Check that the input graph is consistent according to the Pyntacle's minimum requirements

        :return: Whether the graph is sound. If it is not, an exception is raised

        :raise UnsupportedGraphError: An error occurred because the graph is not compliant with the Pyhtacle's minimum requirements
        :raise KeyError: An error occurred because nodes must hold a 'name' attribute
        :raise TypeError: An error occurred because node's name attribute must be of type *string*
        """

        # TODO: Handle exceptions wherever this method is used

        if Graph.is_directed(self.__graph):
            raise UnsupportedGraphError(u"Input graph is direct, pyntacle supports only undirected graphs")
        elif not Graph.is_simple(self.__graph):
            raise UnsupportedGraphError(u"Input Graph contains self loops and multiple edges")
        elif "name" not in self.__graph.vs().attributes():
            raise KeyError(u"nodes must have the attribute  \"name\"")
        elif not all(isinstance(item, str) for item in self.__graph.vs()["name"]):
            raise TypeError(u"node \"name\" attribute must be a string")
        elif len(set(self.__graph.vs()["name"])) != len(self.__graph.vs()["name"]):
            raise UnsupportedGraphError(u"Node names must be unique, check the \"name\" attribute in graph")
        else:
            return True

    def check_index_list(self, index_list):
        r"""
        Check that an index list is consistent with respect to the input `igraph.Graph` object (so, that indices are not
        negative integers and that are within the total number of vertices' boundaries

        :param list index_list: a list of integers
        """
        self.check_graph()

        if not isinstance(index_list, list):
            raise ValueError(u"index list is not a list")

        if len(index_list) < 0:
            raise WrongArgumentError(u"List is empty")

        for ind in index_list:
            if not isinstance(ind, int) or ind < 0:
                raise ValueError("indices must be positive integers")

        if set(index_list) > set(self.__graph.vs.indices):
            self.logger.error(u"The input node index '{}' does not exist in the graph".format(index_list))
            raise WrongArgumentError(u"The input node index '{}' does not exist in the graph".format(index_list))

        return None

    def check_name_list(self, names_list: list):
        r"""
        Checks that a single node or a list of node *names* (the graph.vs["name"] attribute) is present in the graph

        :param names_list: a single node name (as a string) or a list of node names (a list of strings)
        """
        self.check_graph()
        # print(names_list)
        # print (self.graph.vs()["name"])
        if isinstance(names_list, str):
            names_list = [names_list]

        if not isinstance(names_list, list):
            raise ValueError(u"node names list is not a list")

        if len(names_list) < 0:
            raise WrongArgumentError(u"List is empty")

        for name in names_list:
            if not isinstance(name, str):
                raise ValueError(u"node names must be strings")

            if name not in self.__graph.vs()["name"]:
                raise MissingAttributeError(u"node {} is not in vertex \"name\" attribute".format(name))

        if len(list(set(names_list))) != len(names_list):
            self.logger.warning(u"The names list contains duplicated node names, "
                                "so there will be a double index in index list")

    def attribute_in_nodes(self, attribute):
        r"""
        Checks that a given attribute (such as the ones stored in `tools/internal/enums`) is present as  node attribute
        (so is in graph.vs.attributes())
        :param attribute: the attribute you're looking for

        :raise MissingAttributeError: if the attribute is in node attributes
        """
        self.check_graph()

        if attribute not in self.__graph.vs().attributes():
            raise MissingAttributeError(u"Attribute specified has not been initialized in node attributes")

    def attribute_in_edges(self, attribute):
        r"""
        Checks that a given attribute (such as the ones stored in `tools/internal/enums`) is present as edge attribute
        (so is in graph.es.attributes())

        :param attribute: the attribute you're looking for

        :raise MissingAttributeError: if the attribute is not in edge attributes()
        """
        self.check_graph()

        if attribute not in self.__graph.es().attributes():
            raise MissingAttributeError(u"attribute specified has not been initialized in edge attributes")

    def attribute_in_graph(self, attribute):
        r"""
        Checks that a given attribute (such as the ones stored in `tools/internal/enums`) is present as graph attribute
        (so is in graph.attributes())

        :param attribute: the attribute you're looking for

        :raise MissingAttributeError: if the attribute is not in graph attributes()
        """
        self.check_graph()

        if attribute not in self.__graph.attributes():
            raise MissingAttributeError("attribute specified has not been initialized in graph attributes")

    def check_attribute_type(self, attribute, attribute_types):
        r"""
        Check that attributes are of the specified type in the input `igraph.Graph` object

        :param attribute: a the input attribute to be checked
        :param attribute_types: a type of enumerator that will be screened

        :raise ValueError: if the attribute type is not of the selected enumerator
        """
        attribute_types = (attribute_types,)
        if not isinstance(attribute, attribute_types):
            raise MissingAttributeError("the value {} is not a  legal AttributeType".format(str(attribute)))

    def check_attributes_types(self, attributes_list: list, attribute_types):
        r"""
        Check that attributes are coherent and present in the graph

        :param attributes_list: a list of attributes asked to be reported
        :param attribute_types: a type of enumerator or a list of enumerators that will be screened

        :raise ValueError: if the attribute type is not of the selected enumerator
        """

        if isinstance(attribute_types, list):
            attribute_types = tuple(attribute_types)

        else:
            attribute_types = (attribute_types,)

        for elem in attributes_list:
            if not isinstance(elem, attribute_types):
                raise MissingAttributeError(u"the value {} is not a  legal AttributeType".format(str(elem)))

    def get_node_names(self, index_list: list) -> list:
        r"""
        Take a list of integers returns the corresponding graph.vs["name"] attribute of the node that matches each index

        :param list index_list: a list of integers containing indices present in graph (will check for that)

        :return: a list of the corresponding graph.vs["name"] strings
        """
        self.check_graph()
        self.check_index_list(index_list)
        names_list = self.__graph.vs(index_list)["name"]
        return names_list

    def get_node_indices(self, node_names: str or list) -> list:
        r"""
        Return a list of integers representing the corresponding indices of the input ``node_names`` argument.

        :param str, list node_names: A single string or a list of strings containing the vertex ``name`` attribute
        :return list: a list of indices of the corresponding node names given in input. The order of the input list is preserved
        """

        if not isinstance(node_names, list):
            names = [node_names]
        else:
            names = node_names

        self.check_graph()
        self.check_name_list(node_names)
        index_list = []

        for name in names:
            select = self.__graph.vs.select(name=name)
            if len(select) > 1:
                raise IndexError(u"name is not unique, node names must be unique, plese check your graph")

            else:
                index = select[0].index
                index_list.append(index)

        return index_list

    def get_attribute_names(self, attribute_list: list, layer:str = "graph") -> list:
        r"""
        given a specified enumerator (such as the ones stored in `tools/internal/enums`, check if the attribute is initialized
        at the corresponding `layer` level (``graph``, ``node``, ``edge``)

        :param list attribute_list: a list storing enumerators object such as the ones in :class:`tools.enums`
        :param str layer: the layer in which the attributes will bhe searched. Choices are ``graph``, ``node``, ``edge``

        :return list: A list of the corresponding name of the enumerator attribute
        """
        self.check_graph()

        attribute_names = []

        if layer == "graph":  # search for graph attributes
            for attribute in attribute_list:
                try:
                    attr = self.__graph[attribute.name]
                    attribute_names.append(attribute.name)
                    if attr is None:
                        self.logger.warning(u"Attribute specified has None value")

                except KeyError:
                    self.logger.warning(u"Attribute {} is not in graph".format(attribute))

        elif layer == "node":  # search for node attributes
            for attribute in attribute_list:

                if attribute.name not in self.__graph.vs().attributes():
                    self.logger.warning(u"Attribute {} not present in nodee attributes".format(attribute))

                else:
                    attribute_names.append(attribute.name)

        elif layer == "edge":
            for attribute in attribute_list:

                if attribute.name not in self.__graph.es().attributes():
                    self.logger.warning(u"Attribute {} not present in edge attributes".format(attribute))

                else:
                    attribute_names.append(attribute.name)

        else:
            raise ValueError(u"Attribute layer not supported. Legal options are \"graph\", \"node\", \"edge\"")

        return attribute_names

    def get_largest_component(self):
        r"""
        Return the maximum component of a graph (as an induced subgraph).

        :return igraph.Graph: a graph object with the only the largest component. If more than one component if present
        :raise MultipleSolutionsError: if there is more than one largest component
        """
        
        self.logger.info(u"Getting the largest component of the input graph")

        components = self.__graph.components()

        comp_len = [len(comp) for comp in components]
        self.logger.info(u"Graph has the following components: {}".format(",".join(map(str, comp_len))))

        max_comp = max(comp_len)
        max_ind= np.argmax(comp_len)

        max_list = [i for i, x in enumerate(comp_len) if x == max_comp]

        if len(max_list) > 1:
            raise MultipleSolutionsError(u"There are {} largest components, cannot choose one".format(len(max_list)))

        else:
            subgraph = self.__graph.induced_subgraph(components[max_ind])

            self.logger.info(
                u"Largest component has {0} nodes and {1} edges (out of {2} nodes and {3} edges in total)".format(
                    subgraph.vcount(), subgraph.ecount(), self.__graph.vcount(), self.__graph.ecount()))

            return subgraph

    def graph_initializer(self, graph_name: str, node_names: list or None = None):
        r"""
        Turns the input :py:class:`igraph.Graph` object into a Ptyntacle-ready network by making it compliant to the
        Pyntacle `Minimum requirements <http://pyntacle.css-mendel.it/requirements.html>`_

        :param str graph_name: The network name (will be stored in the graph ``name`` attribute)
        :param str, None node_names: optional, a list of strings matching the total number of vertices of the graph. Each item in the list becomes the vertex ``name`` attribute sequentially (index-by-index correspondance). Defaults to py:class:`None` (node ``name`` attribute is filled by node indices).
        """

        try:
            attribute_name_checker(graph_name)
        except ValueError:
            sys.stderr.write("'graph_name' is invalid\n")
            sys.exit(1)

        self.__graph.to_undirected()  # reconvert graph to directed
        if "name" not in self.__graph.attributes():
            self.logger.info(u"adding file name to graph name")
            AddAttributes.add_graph_name(self.__graph, graph_name)

        # add vertex names
        if "name" not in self.__graph.vs.attributes():
            if node_names is None:
                self.logger.info(u"Adding node names to graph corresponding to their indices")
                self.__graph.vs()["name"] = [str(x.index) for x in self.__graph.vs()]

            else:
                if not isinstance(node_names, list) or not all(isinstance(item, str) for item in node_names):
                    raise WrongArgumentError(u"node names must be a list of strings")

                if len(node_names) != self.__graph.vcount():
                    raise IllegalArgumentNumberError(u"node names must be of the same length of vertices")

                self.logger.info(u"Adding node names to graph using the provided node names")
                self.__graph.vs["name"] = node_names

        # add parent name to vertices
        if "__parent" not in self.__graph.vs().attributes():
            self.logger.info(u"Adding reserved attribute '__parent' to the vertices")
            AddAttributes.add_parent_name(self.__graph)

        if "adjacent_nodes" not in self.__graph.es().attributes():
            # add edge vertices names as an attribute 'adjacent_vertices'
            self.logger.info(u"Adding source and target names as \"adjacent_nodes\" attribute to edges")
            AddAttributes.add_edge_names(self.__graph)

        # for sif file conversion purposes
        if not "__sif_interaction_name" in self.__graph.attributes():
            self.__graph["__sif_interaction_name"] = None

        if not "__sif_interaction" in self.__graph.es().attributes():
            self.__graph.es()["__sif_interaction"] = None

        # Adding implementation info for functions that require it
        sp_implementation = CmodeEnum.igraph

        n_nodes = self.__graph.vcount()

        if n_nodes > 100:
            density = (2 * (self.__graph.ecount())) / (n_nodes * (n_nodes - 1))
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

        self.__graph["__implementation"] = sp_implementation