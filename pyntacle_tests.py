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
from io_stream.importer_NEW import *



path = "/home/local/MENDEL/d.capocefalo/Desktop/pyntacle-test/pippo.adjm"

a = PyntacleImporter.AdjacencyMatrix(path, "\t", False)

print(a)


# print(len(aa.components()))
# aa["graph_name"] = "test"
# bb = Graph.copy(aa)
# bb.add_vertex("test")
#
# bb.add_vertex("test2")
#
# bb.add_edge(source="test", target="test2")
# bb.add_vertex("isolato")
#
# # print (lt(graph=aa).radiality())
# # print(LocalTopology.radiality(aa))
# # print(LocalTopology.radiality_reach(bb, ["WD","BS2", "test"]))
# #sp_classic = LocalTopology.shortest_path_igraph(graph=bb)
#
# from graph_generator.graph_igraph_generator import ErdosRenyiGenerator
# gg = ErdosRenyiGenerator().generate([10,0.5])
# gg["graph_name"] = "boh"
# print(KeyPlayer.mreach(graph=gg,implementation="igraph", m=1, nodes=["0", "2"], max_sp=None))
# #print(KeyPlayer.dF(graph=gg,implementation="igraph"))
# print(KeyPlayer.mreach(graph=gg,implementation="pyntacle",m=1, nodes=["0", "2"], max_sp=None))



