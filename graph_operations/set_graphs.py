from igraph import Graph
from utils.add_attributes import AddAttributes
from utils.graph_utils import GraphUtils
from config import *
from collections import OrderedDict

'''
this module merges two graphs if they have any node names in common.
'''

__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2016, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "14 November 2016"
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
  License for more details.

  You should have received a copy of the license along with this
  work. If not, see http://creativecommons.org/licenses/by-nc-nd/4.0/.
  """


class GraphSetter(object):
    def __init__(self, graph1: Graph, graph2: Graph, new_name):
        self.logging = log
        self.graph1 = graph1
        self.graph2 = graph2
        self.newname = new_name

        # check input graphs
        utils1 = GraphUtils(graph=self.graph1)
        utils2 = GraphUtils(graph=self.graph2)
        utils1.graph_checker()
        utils2.graph_checker()

    def union(self):
        """
        **[EXPAND]**
        
        :return:
        """
        union_v, union_e = self.calculate_sets('union')
        merged_g = Graph()
        merged_g["name"] = [self.newname]
        merged_g.add_vertices(list(union_v.keys()))
        merged_g.add_edges(union_e)
        AddAttributes(graph=merged_g).add_edge_names()

        merged_g.vs["__parent"] = list(union_v.values())

        # print("\n\n### RESULTS OF THE UNION PROCESS:")
        # print(merged_g)
        # for v in merged_g.vs():
        #     print(v)

        AddAttributes(graph=merged_g).graph_initializer(graph_name=self.newname)
        return merged_g

    def intersection(self):
        """
        **[EXPAND]**
        
        :return:
        """
        intersect_v, intersect_e, union_v = self.calculate_sets('intersection')

        # Intersect: to avoid isolated nodes, we take the intersection of EDGES as a reference.
        # Therefore, removal of nodes not involved in these edges is necessary
        correct_intersect = []
        for v in intersect_v:
            if len([x for x in intersect_e if v in x]) >= 1:
                correct_intersect.append(v)

        # Now we add attributes to the remainig intersection nodes
        intersect_v = {x: union_v[x] for x in correct_intersect}

        intersection_g = Graph()
        intersection_g["name"] = [self.newname]
        intersection_g.add_vertices(list(intersect_v.keys()))
        intersection_g.add_edges(intersect_e)
        AddAttributes(graph=intersection_g).add_edge_names()

        intersection_g.vs["__parent"] = list(intersect_v.values())

        # print("\n\n### RESULTS OF THE INTERSECTION PROCESS:")
        # print(intersection_g)
        # for v in intersection_g.vs():
        #     print(v)
        AddAttributes(graph=intersection_g).graph_initializer(graph_name=self.newname)
        return intersection_g

    def difference(self):
        """
        **[EXPAND]**
        
        :return:
        """
        exclusive1_v, exclusive1_e, union_v = self.calculate_sets('difference')

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
        # print(exclusive1_v)
        exclusive_g1 = Graph()
        exclusive_g1["name"] = [self.newname]
        exclusive_g1.add_vertices(list(exclusive1_v.keys()))
        exclusive_g1.add_edges(exclusive1_e)
        AddAttributes(graph=exclusive_g1).add_edge_names()
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

        AddAttributes(graph=exclusive_g1).graph_initializer(graph_name=self.newname)
        return exclusive_g1

    def calculate_sets(self, operation):
        """
        **[EXPAND]**
        
        :param operation:
        :return:
        """
        set1v = set(self.graph1.vs["name"])
        set2v = set(self.graph2.vs["name"])

        intersect_v = sorted(list(set1v & set2v))
        exclusive1_v = sorted(list(set1v - set2v))

        # exclusive2_v = list(set2v - set1v)
        union_v = {}

        for v in list(set1v | set2v):

            # Looping through the Union set of vertices NAMES
            if v in intersect_v:
                union_v.setdefault(v, []).append(self.graph1.vs[self.graph1.vs.find(v).index]["__parent"])
                union_v.setdefault(v, []).append(self.graph2.vs[self.graph2.vs.find(v).index]["__parent"])
            elif v in exclusive1_v:
                union_v.setdefault(v, []).append(self.graph1.vs[self.graph1.vs.find(v).index]["__parent"])
            else:
                union_v.setdefault(v, []).append(self.graph2.vs[self.graph2.vs.find(v).index]["__parent"])
        
        union_v = OrderedDict(sorted(union_v.items()))
        set1e = set(tuple(sorted(l)) for l in self.graph1.es["node_names"])
        set2e = set(tuple(sorted(l)) for l in self.graph2.es["node_names"])

        intersect_e = list(set1e & set2e)
        exclusive1_e = list(set1e - set2e)
        # exclusive2_e = list(set2e - set1e)
        union_e = list(set1e | set2e)

        if operation == 'union':
            return union_v, union_e
        elif operation == 'intersection':
            return intersect_v, intersect_e, union_v
        elif operation == 'difference':
            return exclusive1_v, exclusive1_e, union_v
