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
from algorithms.local_topology_NEW import LocalTopology

from misc.enums import SP_implementations as imps
path = "/home/local/MENDEL/d.capocefalo/Desktop/pyntacle-test/figure_8.adjm"

#a = PyntacleImporter.AdjacencyMatrix(path, "\t", True)
#bb = LocalTopology.shortest_path_pyntacle(a,None, implementation=imps.gpu)

# from igraph import Graph
# gg = Graph.Barabasi(10, 2)
# gg["name"] = "bar a bas i"
# gg.vs()["name"] = [str(x) for x in range(0,10)]
# gg.vs()["AHSTRONZO"] = ["ao", "bella", "so", "Lele", "se", "magnamo", "na", "surgelata", "?"]
# gg.es()["simboli"] = ["io" "sono", "papa", "francesco", "il", "distruttore", "di", "mondi"]

# Graph.write_dot(gg, "testmauro.py")

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



