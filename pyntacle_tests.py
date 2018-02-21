# from algorithms.global_topology_NEW import
from algorithms.local_topology_NEW import *
from graph_operations.octopus import *
# from igraph import Graph
# from misc.graph_routines import *
# import time

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
from io_stream.import_attributes import ImportAttributes
from utils.add_attributes import AddAttributes
from io_stream.importer_NEW import PyntacleImporter
from misc.graph_load import *

# adjmatrix = GraphLoad('/home/m.truglio/Desktop/Compiti_Dedalus/figure_8.txt', "adjm", True).graph_load()

adjmat = PyntacleImporter.AdjacencyMatrix(file='/home/m.truglio/Desktop/Compiti_Dedalus/figure_8.txt', sep='\t', header=True)
print("\nGraph in main")
print(adjmat)

input()
gg = Graph.Erdos_Renyi(10, 0.5)
node_names = [str(x) for x in range(0,10)]
AddAttributes(graph=gg).graph_initializer(graph_name="test", node_names=node_names)

print("\nGraph in main")
print(gg)
input()

# #Graph attribute da file
# ImportAttributes(gg).import_graph_attributes('/home/m.truglio/Desktop/Compiti_Dedalus/graph_attributes.txt')
# print(gg["width"])
# #Graph attribute da oggetto
# AddAttributes(gg).add_graph_attributes('lista_a_caso', [33,44,22])
# print(gg["lista_a_caso"])
#
# #Node attribute da file
# ImportAttributes(gg).import_node_attributes('/home/m.truglio/Desktop/Compiti_Dedalus/figure_8_node_attribute_test.txt')
# print(gg.vs["attributotest"])
# print(gg.vs["attributo2"])
# #Node attribute da oggetto
# AddAttributes(gg).add_node_attributes('colore', ['rosso', 'verde'], ['1', '3'])
# print(gg.vs["colore"])
#
# #Edge attribute da file
# ImportAttributes(gg).import_edge_attributes('/home/m.truglio/Desktop/Compiti_Dedalus/figure8_edge_attribute_test.txt')
# print(gg.es["node_names"])
# print(gg.es["attributo1"])
# print(gg.es["attributo2"])
# #Edge attribute da oggetto
# AddAttributes(gg).add_edge_attributes('colore_edge', ['nero', 'magenta'], [('0','1'), ('2', '5')])
# print(gg.es["colore_edge"])


#Test local topology
Octopus.add_degree(gg)
Octopus.add_betweenness(gg)
Octopus.add_clustering_coefficient(gg)
Octopus.add_closeness(gg, '3')
Octopus.add_eccentricity(gg)
Octopus.add_radiality(gg)
Octopus.add_radiality_reach(gg)
Octopus.add_eigenvector_centrality(gg)
Octopus.add_pagerank(gg)
Octopus.add_shortest_path_igraph(gg)
Octopus.add_shortest_path(gg)

Octopus.add_average_closeness(gg)
Octopus.add_pi(gg)
Octopus.add_average_shortest_path_length(gg)
Octopus.add_average_radiality(gg)
# print(LocalTopology.degree(gg, ['1','3']))
#ggg
print(gg)
print("Degree", gg.vs["degree"])
print("Betweenness", gg.vs["betweenness"])
print("Clust coeff", gg.vs["clustering_coefficient"])
print("Closeness", gg.vs["closeness"])
print("Eccentricity", gg.vs["eccentricity"])
print("Radiality reach", gg.vs["radiality_reach"])
print("Eigenvector centrality", gg.vs["eigenvector_centrality"])
print("Pagerank", gg.vs["pagerank"])
print("shortest path igraph", gg.vs["shortest_path_igraph"])
print("shortest path", gg.vs["shortest_path"])

print("\nGraph attributes test")
print("avg closeness", gg["average_closeness"])
print("pi", gg["pi"])
print("avg shortest path length", gg["average_shortest_path_length"])
print("avg radiality", gg["average_radiality"])
#
#

#
#
# LocalTopology.shortest_path_pyntacle(graph=gg, nodes=None,implementation=implementation.gpu)





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


