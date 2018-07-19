"""
Octopus is a Pyntacle's command line tool that adds properties computed by Pyntacle itself to vertices or to the Graph
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "29/04/2018"
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


from tools.add_attributes import AddAttributes
from algorithms.local_topology import LocalTopology
from algorithms.global_topology import GlobalTopology
from algorithms.shortest_path import ShortestPath
from algorithms.sparseness import Sparseness
from algorithms.keyplayer import KeyPlayer
from tools.enums import *
from tools.misc.graph_routines import check_graph_consistency
from tools.misc.shortest_path_modifications import ShortestPathModifier
from cmds.cmds_utils.kpsearch_wrapper import KPWrapper as kpw
from cmds.cmds_utils.kpsearch_wrapper import GOWrapper as gow
from cmds.cmds_utils.kpsearch_wrapper import BFWrapper as bfw


def get_cmode(graph):
    if '__implementation' in graph.attributes():
        return graph["__implementation"]
    else:
        return CmodeEnum.igraph
    
    
class Octopus:
    
    # Global properties
    @staticmethod
    @check_graph_consistency
    def add_diameter(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.diameter.name, GlobalTopology.diameter(graph))

    @staticmethod
    @check_graph_consistency
    def add_radius(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.radius.name, GlobalTopology.radius(graph))
        
    @staticmethod
    @check_graph_consistency
    def add_components(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.components.name, GlobalTopology.components(graph))

    @staticmethod
    @check_graph_consistency
    def add_density(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.density.name, GlobalTopology.density(graph))
        
    @staticmethod
    @check_graph_consistency
    def add_pi(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.pi.name, GlobalTopology.pi(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_clustering_coefficient(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_clustering_coefficient.name,
                                                  GlobalTopology.average_clustering_coefficient(graph))

    @staticmethod
    @check_graph_consistency
    def add_weighted_clustering_coefficient(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.weighted_clustering_coefficient.name,
                                                  GlobalTopology.weighted_clustering_coefficient(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_degree(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_degree.name,
                                                  GlobalTopology.average_degree(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_closeness(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_closeness.name,
                                                  GlobalTopology.average_closeness(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_eccentricity(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_eccentricity.name,
                                                  GlobalTopology.average_eccentricity(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_radiality(graph):
        cmode = get_cmode(graph)
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_radiality.name,
                                                  GlobalTopology.average_radiality(graph, cmode))
    
    @staticmethod
    @check_graph_consistency
    def add_average_radiality_reach(graph):
        cmode = get_cmode(graph)
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_radiality_reach.name,
                                                  GlobalTopology.average_radiality_reach(graph, cmode))

    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph):
        cmode = get_cmode(graph)
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.average_shortest_path_length.name,
                                                  ShortestPath.average_global_shortest_path_length(
                                                      graph, cmode))
    
    @staticmethod
    @check_graph_consistency
    def add_completeness_naive(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.completeness_naive.name,
                                                  Sparseness.completeness_naive(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_completeness(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.completeness.name,
                                                  Sparseness.completeness(graph))
        
    @staticmethod
    @check_graph_consistency
    def add_compactness(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.compactness.name,
                                                  Sparseness.compactness(graph))

    @staticmethod
    @check_graph_consistency
    def add_compactness_correct(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttributeEnum.compactness_correct.name,
                                                  Sparseness.compactness_correct(graph))
        
    # Local properties
    @staticmethod
    @check_graph_consistency
    def add_degree(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.degree.name, 
                                                 LocalTopology.degree(graph, node_names), node_names)
    
    @staticmethod
    @check_graph_consistency
    def add_betweenness(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.betweenness.name, 
                                                 LocalTopology.betweenness(graph, node_names), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_clustering_coefficient(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.clustering_coefficient.name, 
                                                 LocalTopology.clustering_coefficient(graph, node_names), node_names)
    
    @staticmethod
    @check_graph_consistency
    def add_closeness(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.closeness.name, 
                                                 LocalTopology.closeness(graph, node_names), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_eccentricity(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.eccentricity.name, 
                                                 LocalTopology.eccentricity(graph, node_names), node_names)
    
    @staticmethod
    @check_graph_consistency
    def add_radiality(graph, node_names=None):
        cmode = get_cmode(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.radiality.name, 
                                                 LocalTopology.radiality(graph, node_names, cmode),
                                                 node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_radiality_reach(graph, node_names=None):
        cmode = get_cmode(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.radiality_reach.name,
                                                 LocalTopology.radiality_reach(graph, node_names, cmode), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_eigenvector_centrality(graph, node_names=None, scaled=False):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.eigenvector_centrality.name,
                                                 LocalTopology.eigenvector_centrality(graph, node_names, scaled),
                                                 node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_pagerank(graph, node_names=None, weights=None, damping=0.85):
        if node_names is None:
            node_names = graph.vs["name"]
        if "weights" in graph.es.attributes():
            weights = graph.es["weights"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.pagerank.name,
                                                 LocalTopology.pagerank(graph, node_names, weights, damping),
                                                 node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_shortest_path_igraph(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.shortest_path_igraph.name,
                                                 ShortestPath.get_shortestpaths(graph, node_names, CmodeEnum.igraph),
                                                 node_names)

    @staticmethod
    @check_graph_consistency
    def add_shortest_path(graph, node_names=None):
        cmode = get_cmode(graph)
        distances = ShortestPath.get_shortestpaths(graph, node_names, cmode=cmode)
        if node_names is None:
            node_names = graph.vs["name"]
        distances_with_inf = ShortestPathModifier.set_nparray_to_inf(distances, graph.vcount() + 1)
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.shortest_path.name, distances_with_inf, node_names)

    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph, node_names=None):
        cmode = get_cmode(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.average_shortest_path_length.name,
                                                 ShortestPath.average_shortest_path_lengths(graph, node_names, cmode),
                                                 node_names)

    @staticmethod
    @check_graph_consistency
    def add_median_shortest_path_length(graph, node_names=None):
        cmode = get_cmode(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttributeEnum.median_shortest_path_length.name,
                                                 ShortestPath.median_shortest_path_lengths(graph, node_names, cmode),
                                                 node_names)
   
    # Topology metrics
    @staticmethod
    @check_graph_consistency
    def add_F(graph):
        AddAttributes(graph).add_graph_attributes(KpnegEnum.F.name, KeyPlayer.F(graph))

    @staticmethod
    @check_graph_consistency
    def add_dF(graph, max_distance=None):
        cmode = get_cmode(graph)
        AddAttributes(graph).add_graph_attributes(KpnegEnum.dF.name, KeyPlayer.dF(graph, implementation=cmode,
                                                                                  max_distance=max_distance))

    @staticmethod
    @check_graph_consistency
    def add_kp_F(graph, nodes):
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KpnegEnum.F)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.F.name + '_kpinfo', {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dF(graph, nodes, max_distance=None):
        cmode = get_cmode(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KpnegEnum.dF, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.dF.name + '_kpinfo',
            {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dR(graph, nodes, max_distance=None):
        cmode = get_cmode(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KpposEnum.dR, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpposEnum.dR.name + '_kpinfo',
            {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_mreach(graph, nodes, m=None, max_distance=None):
        cmode = get_cmode(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KpposEnum.mreach, m=m, max_distance=max_distance, implementation=cmode)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_kpinfo'.format(str(m))
        AddAttributes(graph).add_graph_attributes(
            attr_name, {tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][1]})

    # Greedy optimization
    @staticmethod
    @check_graph_consistency
    def add_GO_F(graph, kpp_size, seed=None):
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kpp_size, KpnegEnum.F, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.F.name + '_greedy', {tuple(sorted(results_dict[KpnegEnum.F.name][0])): results_dict[KpnegEnum.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dF(graph, kpp_size, max_distance=None, seed=None):
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kpp_size, KpnegEnum.dF, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.dF.name + '_greedy',
            {tuple(sorted(results_dict[KpnegEnum.dF.name][0])): results_dict[KpnegEnum.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dR(graph, kpp_size, max_distance=None, seed=None):
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kpp_size, KpposEnum.dR, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpposEnum.dR.name + '_greedy',
            {tuple(sorted(results_dict[KpposEnum.dR.name][0])): results_dict[KpposEnum.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_mreach(graph, kpp_size, m=None, max_distance=None, seed=None):
        cmode = get_cmode(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kpp_size, KpposEnum.mreach, m=m, max_distance=max_distance, seed=seed, implementation=cmode)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_greedy'.format(str(m))
        AddAttributes(graph).add_graph_attributes(
            attr_name, {tuple(sorted(results_dict[KpposEnum.mreach.name][0])): results_dict[KpposEnum.mreach.name][1]})
    
    # Brute-force optimization
    @staticmethod
    @check_graph_consistency
    def add_BF_F(graph, kpp_size, max_distance=None):
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kpp_size, KpnegEnum.F, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.F.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.F.name][0]): results_dict[KpnegEnum.F.name][1]})
        
    @staticmethod
    @check_graph_consistency
    def add_BF_dF(graph, kpp_size, max_distance=None):
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kpp_size, KpnegEnum.dF, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpnegEnum.dF.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpnegEnum.dF.name][0]): results_dict[KpnegEnum.dF.name][1]})
    
    @staticmethod
    @check_graph_consistency
    def add_BF_dR(graph, kpp_size, max_distance=None):
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kpp_size, KpposEnum.dR, max_distance=max_distance)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(
            KpposEnum.dR.name + '_bruteforce',
            {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.dR.name][0]): results_dict[KpposEnum.dR.name][1]})
        
    @staticmethod
    @check_graph_consistency
    def add_BF_mreach(graph, kpp_size, m=None, max_distance=None):
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kpp_size, KpposEnum.mreach, max_distance=max_distance, m=m)
        results_dict = kpobj.get_results()
        attr_name = KpposEnum.mreach.name + '_{}_bruteforce'.format(str(m))
        AddAttributes(graph).add_graph_attributes(
            attr_name,
            {tuple(tuple(sorted(x)) for x in results_dict[KpposEnum.mreach.name][0]): results_dict[KpposEnum.mreach.name][1]})
