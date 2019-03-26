__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """


from igraph import Graph
from collections import OrderedDict
from tools.enums import GraphOperationEnum
from tools.add_attributes import AddAttributes
from tools.graph_utils import GraphUtils as GUtil

def make_sets(graph1: Graph, graph2: Graph, operation: GraphOperationEnum):
    r"""
    Internal method to deal with the set operations and the handling of the attributes. 
    """

    GUtil(graph=graph1).check_graph()
    GUtil(graph=graph2).check_graph()

    set1v = set(graph1.vs["name"])
    set2v = set(graph2.vs["name"])

    intersect_v = sorted(list(set1v & set2v))
    exclusive1_v = sorted(list(set1v - set2v))
    union_v = {}

    for v in list(set1v | set2v):
        # Looping through the Union set of vertices NAMES
        if v in intersect_v:
            union_v.setdefault(v, []).append(graph1.vs[graph1.vs.find(v).index]["parent"])
            union_v.setdefault(v, []).append(graph2.vs[graph2.vs.find(v).index]["parent"])
        elif v in exclusive1_v:
            union_v.setdefault(v, []).append(graph1.vs[graph1.vs.find(v).index]["parent"])
        else:
            union_v.setdefault(v, []).append(graph2.vs[graph2.vs.find(v).index]["parent"])

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


class GraphSetOps(object):
    r"""
    Perform logical set operations (*union*, *intersection*, *difference*) among two graphs of interest.

    .. warning:: If the same attribute is present at graph, node or edge level, but the same attribute holds a different value in the two graph of origin, only the attribute belonging to the first graph (in order) is preserved.
    """

    @staticmethod
    def union(graph1: Graph, graph2: Graph, new_graph_name: str) -> Graph:
        r"""
        Perform the union among two graphs as described by  `Wolfram <http://mathworld.wolfram.com/GraphUnion.html>`_

        :param igraph.Graph graph1: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param igraph.Graph graph2: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str new_graph_name: a string representing the new name that will be added to the graph ``name`` attribute
        :return igraph.Graph: the resulting :class:`igraph.Graph` object. This network will contain both the first and second noddes and edges. The origin of each node it is determined by the vertex ``parent`` attribute.
        """
        union_v, union_e = make_sets(graph1, graph2, GraphOperationEnum.Union)
        merged_g = Graph()
        merged_g["name"] = [new_graph_name]
        merged_g.add_vertices(list(union_v.keys()))
        merged_g.add_edges(union_e)

        AddAttributes.add_edge_names(graph=merged_g)
        merged_g.vs["parent"] = list(union_v.values())
        GUtil(graph=merged_g).graph_initializer(graph_name=new_graph_name)

        return merged_g

    @staticmethod
    def intersection(graph1: Graph, graph2: Graph, new_graph_name: str) -> Graph:
        r"""
        Perform the intersection among two graphs as described by  `Wolfram <http://mathworld.wolfram.com/GraphIntersection.html>`_

        :param igraph.Graph graph1: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param igraph.Graph graph2: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str new_graph_name: a string representing the new name that will be added to the graph ``name`` attribute
        :return igraph.Graph: the resulting :class:`igraph.Graph` object. This network will contain only common nodes and edges of the two input graphs. The origin of each node it is determined by the vertex ``parent`` attribute.
        """

        intersect_v, intersect_e, union_v = make_sets(graph1, graph2, GraphOperationEnum.Intersection)

        # Intersect: to avoid isolated nodes, we take the intersection of EDGES as a reference.
        # Therefore, removal of nodes not involved in these edges is necessary
        correct_intersect = []
        for v in intersect_v:
            if len([x for x in intersect_e if v in x]) >= 1:
                correct_intersect.append(v)

        # Now we add attributes to the remaining intersection nodes
        intersect_v = {x: union_v[x] for x in correct_intersect}

        intersection_g = Graph()
        intersection_g["name"] = [new_graph_name]
        intersection_g.add_vertices(list(intersect_v.keys()))
        intersection_g.add_edges(intersect_e)

        AddAttributes.add_edge_names(graph=intersection_g)
        intersection_g.vs["parent"] = list(intersect_v.values())
        GUtil(graph=intersection_g).graph_initializer(graph_name=new_graph_name)

        return intersection_g

    @staticmethod
    def difference(graph1: Graph, graph2: Graph, new_graph_name: str) -> Graph:
        r"""
        Perform the intersection among two graphs as described by  `Wolfram <http://mathworld.wolfram.com/GraphDifference.html>`_

        :param igraph.Graph graph1: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param igraph.Graph graph2: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str new_graph_name: a string representing the new name that will be added to the graph ``name`` attribute
        :return igraph.Graph: the resulting :class:`igraph.Graph` object. This network will contain only nodes and edges present in the ``graph1`` network but not in the ``graph2`` argument. The origin of each node it is determined by the vertex ``parent`` attribute.
        """
        exclusive1_v, exclusive1_e, union_v = make_sets(graph1, graph2, GraphOperationEnum.Difference)

        for e in exclusive1_e:
            if e[0] not in exclusive1_v:
                exclusive1_v.append(e[0])
            if e[1] not in exclusive1_v:
                exclusive1_v.append(e[1])

        exclusive1_v = {x: union_v[x] for x in exclusive1_v}
        exclusive1_v = OrderedDict(sorted(exclusive1_v.items()))
        exclusive_g1 = Graph()
        exclusive_g1["name"] = [new_graph_name]
        exclusive_g1.add_vertices(list(exclusive1_v.keys()))
        exclusive_g1.add_edges(exclusive1_e)
        AddAttributes.add_edge_names(graph=exclusive_g1)
        exclusive_g1.vs["parent"] = list(exclusive1_v.values())

        GUtil(graph=exclusive_g1).graph_initializer(graph_name=new_graph_name)
        return exclusive_g1
