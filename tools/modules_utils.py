__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
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

"""
This utility performs several operations on modules found through community detection algorithms
"""


from config import *
from igraph import Graph
from tools.graph_utils import GraphUtils

class ModuleUtils():
    logger = None

    def __init__(self, modules: list, graph: Graph, algorithm: str):
        """
        Implements all the necessary step to check a graph object and add the reserved attribute "__module_number" to
        each submodule in order to retrace it back. If a graph attribute with that name aòready exist, it will be
        overwritten
        :param modules:a list of graphs already divided by the CommunityFinder class
        :param graph: the input graph used  to find modules
        :param str algorithm: the name of the algorithm used to perform community detection
        """

        self.logger = log

        GraphUtils(graph=graph).check_graph()

        self.graph = graph


        for i, elem in enumerate(modules):
            if elem.vcount() == 0:
                self.logger.warning("Module {} is empty, and therefore will be discarded".format(i))
                del (modules[i])

            if elem["name"] != graph["name"]:
                raise ValueError("Module {} does not come from the input Graph".format(i))

            if not set(elem.vs()["name"]).issubset(set(graph.vs()["name"])):
                raise ValueError("Module {} does not come from the input Graph".format(i))

            if elem.vcount() > graph.vcount() or elem.ecount() > graph.ecount():
                raise ValueError("Module {} does not come from the input Graph".format(i))

            if "__module_number" in graph.attributes():

                self.logger.info(
                    "Attribute \"__module_number\" already exist in the module {}, will overwrite".format(str(i)))

            elem["__module_number"] = i  # this should traceroute the module back to its original number

        self.modules = modules

        #checks that the input graph is properly formatted

        if not isinstance(algorithm, str):
            raise TypeError("\"algorithm\" must be a string, {} found".format(type(algorithm).__name__))

        else:
            self.algorithm = algorithm

    def filter_subgraphs(self, min_nodes=None, max_nodes=None, min_components=None, max_components=None):
        """
        :param min_nodes: minimum set size. Default is None (no component will be filtered according to this criteria)
        :param max_nodes: maximum set size. Default is None (no component will be filtered according to this criteria)
        :param min_components: minimum number of components that graph must have. Default is None (no component will be filtered according to this criteria)
        :param max_components: maximum number of components that graph must have. Default is None (no component will be filtered according to this criteria)
        """

        if min_nodes is not None and min_nodes < 0:
            raise ValueError("minset must be a positive integer")

        if max_nodes is not None and max_nodes < 1:
            raise ValueError("maxset must be a positive integer greater than one")

        if max_components is not None and max_components < 1:
            raise ValueError("max_components must be a positive integer greater than one")

        if min_components is not None and min_components < 1:
            raise ValueError("min_components must be a positive integer greater than one ")

        info = [str(x) if x is not None else "NA" for x in (min_nodes, max_nodes, min_components, max_components)]

        self.logger.info(
            "Filtering Subgraphs according to your criteria:\nminimum number of nodes per modules: {0}\nmaximum number of nodes per module: {1}\nminimum number of components: {2}\nmaximum number of components: {3}\n".format(
                *info))

        if not all(x == None for x in [min_nodes, max_nodes, min_components, max_components]):
            self.modules = list(filter(lambda x: x.vcount() > min_nodes if min_nodes is not None else x, self.modules))
            self.modules = list(filter(lambda x: x.vcount() < max_nodes if max_nodes is not None else x, self.modules))
            self.modules = list(
                filter(lambda x: len(x.components()) > min_components if min_components is not None else x,
                       self.modules))
            self.modules = list(
                filter(lambda x: len(x.components()) < max_components if max_components is not None else x,
                       self.modules))

    def get_modules(self):
        """
        Returns the list of graph modules (a list of igraph.Graph objects)
        """
        return self.modules

    def add_modules_info(self):
        """
        adds all the information regarding the modules to each subgraph found using community detection algorithms.
        These information are, specifically:
        #. an hidden attribute named "__module_algorithm" that store the type of algorithm that was used to identify the community
        #. an hidden attribute named "__origin_graph" the first element of the graph["name"] attribute (ideally, the name of the input graph)
        """

        if len(self.graph["name"]) > 1:
            self.logger.warning(
                "graph attribute \"name\" must be unique, found {} instead, will use first name only.".format(
                    ",".join[self.graph["name"]]))

        self.logger.info("adding algorithm used to each module in the \"__module_algorithm\" private attribute")
        self.logger.info("adding original graph name to each module in the \"__origin_graph\" private attribute")

        for subgraph in self.modules:
            if "__module_algorithm" not in subgraph.attributes():
                subgraph["__module_algorithm"] = self.algorithm

            if "__origin_graph" not in subgraph.attributes():
                subgraph["__origin_graph"] = self.graph["name"][0]

    def label_modules_in_graph(self):
        """
        Add to each node and edge an attribute that trace it to each module (a way to distinguish each components).
        Specifically, two reserved attributed will be filled in each of the elemenf in `modules`:
        #. a "__module" name will be assigned to the reserved "__module" attribute for each  subgraph, node and edge the element in the modules was found into. specifying the name of the module (usually a string representing a positive integer)
        #- an "__algorithm" attribute will be assigned to each subgraph, node, and edge attributes showing the name of the algorithm that was passed to the ModuleUtils() class specifying the name of the algorithm that was used to find communities.
        """

        self.logger.info("Adding attribute \"__module\" to each node")

        for i, subgraph in enumerate(self.modules):

            if "__module" in subgraph.vs.attributes():
                self.logger.warning(
                    "module {} already have a \"__module\" vertex attribute name, will overwrite it".format(i))
                subgraph.vs["__module"] = None

            if "__algorithm" in subgraph.vs.attributes():
                self.logger.warning(
                    "module {} already have a \"__algorithm\" vertex attribute name, will overwrite it".format(i))
                subgraph.vs["__algorithm"] = None

            if "__module" in subgraph.es.attributes():
                self.logger.warning(
                    "module {} already have a \"__module\" edge attribute name, will overwrite it".format(i))
                subgraph.es["__module"] = None

            if "__algorithm" in subgraph.es.attributes():
                self.logger.warning(
                    "module {} already have a \"__algorithm\" edge attribute name, will overwrite it".format(i))
                subgraph.es["__algorithm"] = None

            node_names = subgraph.vs()["name"]
            edge_names = subgraph.es()["node_names"]
            select_nodes = self.graph.vs().select(name_in=node_names)

            if len(node_names) != len(select_nodes):
                different_nodes = list(set(node_names) - set([x["name"] for x in select_nodes]))
                self.logger.warning("Nodes {} not found in input graph".format(",".join(different_nodes)))

            else:
                self.graph.vs(select_nodes.indices)["__module"] = i
                self.graph.vs(select_nodes.indices)["__algorthm"] = self.algorithm

            select_edges = select_nodes = self.graph.es().select(node_names_in=edge_names)
            if len(edge_names) != len(select_edges):
                different_nodes = list(set(edge_names) - set([x["name"] for x in select_edges]))
                self.logger.warning(
                    "edges {} not found in input graph".format(",".join("--".join(list(different_nodes)))))

            else:
                self.graph.es(select_nodes.indices)["__module"] = i
                self.graph.es(select_nodes.indices)["__algorithm"] = self.algorithm