__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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


from igraph import Graph
from collections import OrderedDict
from tools.enums import GraphOperationEnum
from tools.add_attributes import AddAttributes
from tools.graph_utils import GraphUtils as GUtil

#TODO we don't port the attributes of one of the original graphs, fix ASAP

def make_sets(graph1: Graph, graph2: Graph, operation: GraphOperationEnum):
    r"""
    :param graph1:
    :param graph2:
    :param operation:
    :return igraph.Graph:
    """

    GUtil(graph=graph1).check_graph()
    GUtil(graph=graph2).check_graph()

    set1v = set(graph1.vs["name"])
    set2v = set(graph2.vs["name"])

    intersect_v = sorted(list(set1v & set2v))
    exclusive1_v = sorted(list(set1v - set2v))
    # exclusive2_v = list(set2v - set1v)
    union_v = {}

    for v in list(set1v | set2v):
        # Looping through the Union set of vertices NAMES
        if v in intersect_v:
            union_v.setdefault(v, []).append(graph1.vs[graph1.vs.find(v).index]["__parent"])
            union_v.setdefault(v, []).append(graph2.vs[graph2.vs.find(v).index]["__parent"])
        elif v in exclusive1_v:
            union_v.setdefault(v, []).append(graph1.vs[graph1.vs.find(v).index]["__parent"])
        else:
            union_v.setdefault(v, []).append(graph2.vs[graph2.vs.find(v).index]["__parent"])

    union_v = OrderedDict(sorted(union_v.items()))
    set1e = set(tuple(sorted(l)) for l in graph1.es["adjacent_nodes"])
    set2e = set(tuple(sorted(l)) for l in graph2.es["adjacent_nodes"])

    intersect_e = list(set1e & set2e)
    exclusive1_e = list(set1e - set2e)
    # exclusive2_e = list(set2e - set1e)
    union_e = list(set1e | set2e)

    if operation == GraphOperationEnum.Union:
        return union_v, union_e
    elif operation == GraphOperationEnum.Intersection:
        return intersect_v, intersect_e, union_v
    elif operation == GraphOperationEnum.Difference:
        return exclusive1_v, exclusive1_e, union_v


class GraphOperations(object):
    r"""
    Perform logical set operations (*union*, *intersection*, *difference*) among two graphs of interest.

    .. warning:: If the same attribute is present at graph, node or edge level, but the same attribute holds a different value in the two graph of origin, only the attribute belonging to the first graph (in order) is preserved.
    """

    @staticmethod
    def union(graph1: Graph, graph2: Graph, new_graph_name: str) -> Graph:
        r"""
        Perform the union among two graph as described by  `Wolfram <http://mathworld.wolfram.com/GraphUnion.html>`_

        :param igraph.Graph graph1:
        :param igraph.Graph graph2:
        :param str new_graph_name:
        :return igraph.Graph:
        """
        union_v, union_e = make_sets(graph1, graph2, GraphOperationEnum.Union)
        merged_g = Graph()
        merged_g["name"] = [new_graph_name]
        merged_g.add_vertices(list(union_v.keys()))
        merged_g.add_edges(union_e)

        AddAttributes.add_edge_names(graph=merged_g)
        merged_g.vs["__parent"] = list(union_v.values())
        GUtil(graph=merged_g).graph_initializer(graph_name=new_graph_name)

        return merged_g

    @staticmethod
    def intersection(graph1: Graph, graph2: Graph, new_graph_name: str) -> Graph:
        r"""
        Perform the intersection among two graph as described by  `Wolfram <http://mathworld.wolfram.com/GraphIntersection.html>`_

        :param igraph.Graph graph1:
        :param igraph.Graph graph2:
        :param str new_graph_name:
        :return igraph.Graph:
        """

        intersect_v, intersect_e, union_v = make_sets(graph1, graph2, GraphOperationEnum.Intersection)

        # Intersect: to avoid isolated nodes, we take the intersection of EDGES as a reference.
        # Therefore, removal of nodes not involved in these edges is necessary
        correct_intersect = []
        for v in intersect_v:
            if len([x for x in intersect_e if v in x]) >= 1:
                correct_intersect.append(v)

        # Now we add attributes to the remainig intersection nodes
        intersect_v = {x: union_v[x] for x in correct_intersect}

        intersection_g = Graph()
        intersection_g["name"] = [new_graph_name]
        intersection_g.add_vertices(list(intersect_v.keys()))
        intersection_g.add_edges(intersect_e)

        AddAttributes.add_edge_names(graph=intersection_g)
        intersection_g.vs["__parent"] = list(intersect_v.values())
        GUtil(graph=intersection_g).graph_initializer(graph_name=new_graph_name)

        return intersection_g

    @staticmethod
    def difference(graph1: Graph, graph2: Graph, new_graph_name: str) -> Graph:
        r"""
        Perform the intersection among two graph as described by  `Wolfram <http://mathworld.wolfram.com/GraphDifference.html>`_

        :param igraph.Graph graph1:
        :param igraph.Graph graph2:
        :param str new_graph_name:
        :return igraph.Graph:
        """
        exclusive1_v, exclusive1_e, union_v = make_sets(graph1, graph2, GraphOperationEnum.Difference)

        for e in exclusive1_e:
            if e[0] not in exclusive1_v:
                exclusive1_v.append(e[0])
            if e[1] not in exclusive1_v:
                exclusive1_v.append(e[1])

        # for e in exclusive2_e:
        #     if e[0] not in exclusive2_v:
        #         exclusive2_v.append(e[0])
        #     if e[1] not in exclusive2_v:
        #         exclusive2_v.append(e[1])

        exclusive1_v = {x: union_v[x] for x in exclusive1_v}
        exclusive1_v = OrderedDict(sorted(exclusive1_v.items()))
        exclusive_g1 = Graph()
        exclusive_g1["name"] = [new_graph_name]
        exclusive_g1.add_vertices(list(exclusive1_v.keys()))
        exclusive_g1.add_edges(exclusive1_e)
        AddAttributes.add_edge_names(graph=exclusive_g1)
        exclusive_g1.vs["__parent"] = list(exclusive1_v.values())

        # exclusive2_v = {x: union_v[x] for x in exclusive2_v}
        #
        # exclusive_g2 = Graph()
        # exclusive_g2["name"] = [self.newname]
        # exclusive_g2.add_vertices(list(exclusive2_v.keys()))
        # exclusive_g2.add_edges(exclusive2_e)
        # AddAttributes(graph=exclusive_g2).add_edge_names()
        # exclusive_g2.vs["__parent"] = list(exclusive2_v.values())

        # print("\n\n### RESULTS OF THE DIFFERENCE PROCESS:")
        # print(exclusive_g1)
        # for v in exclusive_g1.vs():
        #     print(v)
        #
        # print(exclusive_g2)
        # for v in exclusive_g2.vs():
        #     print(v)

        GUtil(graph=exclusive_g1).graph_initializer(graph_name=new_graph_name)
        return exclusive_g1