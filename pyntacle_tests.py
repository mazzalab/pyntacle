from config import *
from algorithms.global_topology import *
from algorithms.local_topology import *
from algorithms.keyplayer import KeyPlayer
from tools.misc.graph_load import *
from tools.misc.enums import KPPOSchoices, KPNEGchoices
from algorithms.greedy_optimization import *
from graph_operations.octopus import Octopus
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


# adjmatrix = GraphLoad('/home/m.truglio/Desktop/Compiti_Dedalus/edgelist.txt.sif', "sif", True).graph_load()
# print(adjmatrix)
# print(list(adjmatrix.es))
# AddAttributes(adjmatrix).add_edge_attributes('colore_edge', ['nero'], [('1','0')])
# print(list(adjmatrix.es))
# input()


if __name__ == '__main__':
    mat = PyntacleImporter.AdjacencyMatrix(
        file=r'C:\Users\t.mazza\Desktop\CSS-Bioinformatics\pyntacle\test\test_sets\input\figure_8.txt', header=True)
    print("\nGraph in main")
    print(mat.summary())
    from algorithms.bruteforce_search import BruteforceSearch

    # bf = BruteforceSearch.fragmentation(mat, kpp_size=2, kpp_type=KPNEGchoices.dF, parallel=True)
    bf2 = BruteforceSearch.reachability(mat, kpp_size=2, kpp_type=KPPOSchoices.dR, parallel=True)

    a = 3

# #
# print('gpu')
# print(LocalTopology.shortest_path_pyntacle(graph=mat, implementation=SP_implementations.gpu))
#
# print('\n\ncpu')
#
# print(LocalTopology.shortest_path_pyntacle(graph=mat, implementation=SP_implementations.cpu))
# # input()
# #
# #
# print('\n\nIGRAph')
#
# print(LocalTopology.shortest_path_pyntacle(graph=mat, implementation=SP_implementations.igraph))
#
# print('\n\n Igraph puro')
#
# print(LocalTopology.shortest_path_igraph(graph=mat))

# print(KeyPlayer.dF(graph=mat, implementation=imps.cpu))
# print(KeyPlayer.dF(graph=mat, implementation=imps.igraph))


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


# #Test local topology
# Octopus.add_degree(mat, 'HS')
# Octopus.add_betweenness(mat)
# Octopus.add_clustering_coefficient(mat)
# Octopus.add_closeness(mat, ['HS'])
# Octopus.add_eccentricity(mat)
# Octopus.add_radiality(mat)
# Octopus.add_radiality_reach(mat)
# Octopus.add_eigenvector_centrality(mat)
# Octopus.add_pagerank(mat)
# Octopus.add_shortest_path_igraph(mat)
# Octopus.add_shortest_path(mat)
#
# #Test global topology
# Octopus.add_average_closeness(mat)
# Octopus.add_pi(mat)
# Octopus.add_average_shortest_path_length(mat)
# Octopus.add_average_radiality(mat)
#
#
# # print(LocalTopology.degree(gg, ['1','3']))
# #ggg
# print("Degree", mat.vs["degree"])
# print("Betweenness", mat.vs["betweenness"])
# print("Clust coeff", mat.vs["clustering_coefficient"])
# print("Closeness", mat.vs["closeness"])
# print("Eccentricity", mat.vs["eccentricity"])
# print("Radiality reach", mat.vs["radiality_reach"])
# print("Eigenvector centrality", mat.vs["eigenvector_centrality"])
# print("Pagerank", mat.vs["pagerank"])
# print("shortest path igraph", mat.vs["shortest_path_igraph"])
# print("shortest path", mat.vs["shortest_path"])
#
# print("\nGraph attributes test")
# print("avg closeness", mat["average_closeness"])
# print("pi", mat["pi"])
# print("avg shortest path length", mat["average_shortest_path_length"])
# print("avg radiality", mat["average_radiality"])


# Test KeyPlayer

#F
#
# Octopus.add_F(mat)
# Octopus.add_kp_F(mat, ['HS'])
#
# #dF
#
# Octopus.add_dF(mat)
# Octopus.add_kp_dF(mat, ['HS'])


#
# #dR
#
# Octopus.add_dR(mat, ['SR', 'TO'])
# Octopus.add_dR(mat, ['HS', 'PS'])
#
# # mreach
# m = 1
# Octopus.add_mreach(mat, ['HS'], m)
# Octopus.add_mreach(mat, ['LK'], m)
#
# m = 3
# Octopus.add_mreach(mat, ['TO', 'CD'], m)


# GO

# # # go F
# Octopus.add_GO_F(mat, 2)
# #
# # # go dF
# Octopus.add_GO_dF(mat, 2)
# #
# # # go dR
# Octopus.add_GO_dR(mat, 2)

# go mreach
# m = 1
# Octopus.add_GO_mreach(mat, 1, m)
# Octopus.add_GO_mreach(mat, 3, m)
#
# m = 1
# Octopus.add_GO_mreach(mat, 2, m)
#
#
# bf F
# Octopus.add_BF_F(mat, 2)

# bf dF
# Octopus.add_BF_dF(mat, 2)

# bf dR
# Octopus.add_BF_dR(mat, 2)

# bf dR
# Octopus.add_BF_mreach(mat, 2, 1)
# Octopus.add_BF_mreach(mat, 3, 3)


# print("\n\nGraph attributes:")
# for attr in mat.attributes():
#     print(attr, mat[attr])
#
# print("\n\nNode attributes:")
# for attr in mat.vs.attributes():
#     print(attr,'\n', mat.vs.get_attribute_values(attr))
    
    
    
# old BF

# from algorithms.bruteforce_search import BruteforceSearch
# from algorithms.key_player import KeyPlayer, _KeyplayerAttribute
#
# print(BruteforceSearch(mat).bruteforce_fragmentation(kpp_size=2, kpp_type=_KeyplayerAttribute.F))
# print(BruteforceSearch(mat).bruteforce_fragmentation(kpp_size=2, kpp_type=_KeyplayerAttribute.DF))
# print(BruteforceSearch(mat).bruteforce_reachability(kpp_size=2, kpp_type=_KeyplayerAttribute.DR))
# print(BruteforceSearch(mat).bruteforce_reachability(kpp_size=2, kpp_type=_KeyplayerAttribute.MREACH, m=1))


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


