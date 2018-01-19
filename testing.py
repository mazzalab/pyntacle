from algorithms.local_topology import *
from config import *
from io_stream.adjacencymatrix_to_graph import *
from io_stream.graph_to_sif import *
from io_stream.binary_to_graph import *
from algorithms.bruteforce_search import *
from algorithms.greedy_optimization import *
from algorithms.local_topology import LocalTopology as lt
#g = AdjacencyMatrixToGraph().import_graph("/home/d.capocefalo/Desktop/figure_8.adjm", separator="\t", header=True)

g = BinaryToGraph().load_graph(file_name="/home/d.capocefalo/Desktop/save_graph_04010")
#print(g)

l = lt(g)
for elem in l.radiality_reach(recalculate=True):
    print (elem)
#GraphToSif(g).export_graph(file_name="/home/d.capocefalo/Desktop/figure_8.sif", header=True, sep="\t")



# print(BruteforceSearch(graph=g).bruteforce_fragmentation(kpp_size=3, kpp_type=KeyplayerAttribute.F))
#
# print(BruteforceSearch(graph=g).bruteforce_reachability(kpp_size=3, kpp_type=KeyplayerAttribute.MREACH, m=2))
#
#
# print(GreedyOptimization(graph=g).optimize_kpp_neg(kpp_size=3, kpp_type=KeyplayerAttribute.F))
# print(GreedyOptimization(graph=g).optimize_kpp_pos(kpp_size=3, m = 2, kpp_type=KeyplayerAttribute.MREACH))



# lt = LocalTopology(graph=g)
# print(lt.radiality(index_list=[0, 1, 2]))
# print(lt.radiality_reach(index_list=[0, 1, 2], recalculate=True))
# print (lt.radiality_reach(recalculate=True))


