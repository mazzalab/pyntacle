#test for creating the new pyntacle iteration
# erd = Graph.Erdos_Renyi(10, 0.5)
# print(GlobalTopology.diameter(erd))
# print(GlobalTopology.radius(erd))

# erd = Graph()
# erd.add_vertex("aoaoao")
# erd.add_vertex("test")
# erd.add_vertex("ao")
# erd.add_edge(source=1, target=2)
# erd.add_edge(source=1, target=0)
# # erd.add_edge(source=1, target=3)
# # erd.add_edge(4,5)
# print(GlobalTopology.diameter(erd))
# print(GlobalTopology.radius(erd))
# print(GlobalTopology.components(erd))
# print(GlobalTopology.density(erd))

from igraph import Graph
from io_stream.importer import PyntacleImporter
from algorithms.greedy_optimization_NEW import GreedyOptimization as GO
from algorithms.greedy_optimization import GreedyOptimization
from misc.enums import KPNEGchoices

path = "/home/local/MENDEL/d.capocefalo/Programming/pyntacle-test/figure_8.adjm"

a = PyntacleImporter.AdjacencyMatrix(path, "\t", True)


import random
random.seed(123)

go = GreedyOptimization(graph=a).optimize_kpp_neg(kpp_size=3, kpp_type=KPNEGchoices.dF)
print("kp-OLD:",go)

gonew = GO.kpp_neg_greedy(a, 3, KPNEGchoices.dF, seed=123)
print("kp-NEW",gonew)
