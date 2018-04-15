__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
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


"""
Octopus is a pyntacle command line utility that adds properties computed by pyntacle to the Graph, both at vertex and at
a Graph level
"""
from config import *
from tools.add_attributes import AddAttributes
from algorithms.local_topology import LocalTopology
from algorithms.global_topology import GlobalTopology
from algorithms.keyplayer import KeyPlayer
from tools.misc.enums import *
from tools.misc.enums import GraphType
from tools.misc.graph_routines import check_graph_consistency
from tools.misc.shortest_path_modifications import ShortestPathModifier
from cmds.cmds_utils.kpsearch_wrapper import KPWrapper as kpw
from cmds.cmds_utils.kpsearch_wrapper import GOWrapper as gow
from cmds.cmds_utils.kpsearch_wrapper import BFWrapper as bfw
from tools.misc.enums import KPNEGchoices, KPPOSchoices, Cmode


# TODO DANIELE: Add SPASENESS

def implementation_check(graph):
    if '__implementation' in graph.attributes():
        return graph["__implementation"]
    else:
        return Cmode.igraph
    
    
class Octopus:
    
    #Global
    @staticmethod
    @check_graph_consistency
    def add_diameter(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.diameter.name, GlobalTopology.diameter(graph))

    @staticmethod
    @check_graph_consistency
    def add_radius(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.radius.name, GlobalTopology.radius(graph))
        
    @staticmethod
    @check_graph_consistency
    def add_components(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.components.name, GlobalTopology.components(graph))

    @staticmethod
    @check_graph_consistency
    def add_density(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.density.name, GlobalTopology.density(graph))
        
    @staticmethod
    @check_graph_consistency
    def add_pi(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.pi.name, GlobalTopology.pi(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_clustering_coefficient(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_clustering_coefficient.name,
                                                  GlobalTopology.average_clustering_coefficient(graph))
    @staticmethod
    @check_graph_consistency
    def add_weighted_clustering_coefficient(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.weighted_clustering_coefficient.name,
                                                  GlobalTopology.weighted_clustering_coefficient(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_degree(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_degree.name, GlobalTopology.average_degree(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_closeness(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_closeness.name,
                                                  GlobalTopology.average_closeness(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_eccentricity(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_eccentricity.name,
                                                  GlobalTopology.average_eccentricity(graph))
    
    @staticmethod
    @check_graph_consistency
    def add_average_radiality(graph):
        implementation = implementation_check(graph)
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_radiality.name,
                                                  GlobalTopology.average_radiality(graph, implementation))
    
    @staticmethod
    @check_graph_consistency
    def add_average_radiality_reach(graph):
        implementation = implementation_check(graph)
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_radiality_reach.name,
                                                  GlobalTopology.average_radiality_reach(graph,
                                                                                         implementation))
    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph):
        implementation = implementation_check(graph)
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.average_shortest_path_length.name,
                                                  GlobalTopology.average_shortest_path_length(graph,
                                                                                              implementation))
        
    # Local
    @staticmethod
    @check_graph_consistency
    def add_degree(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.degree.name, LocalTopology.degree(graph, node_names), node_names)
    
    @staticmethod
    @check_graph_consistency
    def add_betweenness(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.betweenness.name, LocalTopology.betweenness(graph, node_names), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_clustering_coefficient(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.clustering_coefficient.name, LocalTopology.clustering_coefficient(graph, node_names), node_names)
    
    @staticmethod
    @check_graph_consistency
    def add_closeness(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.closeness.name, LocalTopology.closeness(graph, node_names), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_eccentricity(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.eccentricity.name, LocalTopology.eccentricity(graph, node_names), node_names)
    
    @staticmethod
    @check_graph_consistency
    def add_radiality(graph, node_names=None):
        implementation = implementation_check(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.radiality.name, LocalTopology.radiality(graph, node_names, cmode=implementation), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_radiality_reach(graph, node_names=None):
        implementation = implementation_check(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.radiality_reach.name, LocalTopology.radiality_reach(graph, node_names, implementation=implementation), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_eigenvector_centrality(graph, node_names=None, scaled=False):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.eigenvector_centrality.name, LocalTopology.eigenvector_centrality(graph, node_names, scaled), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_pagerank(graph, node_names=None, weights=None, damping=0.85):
        if node_names is None:
            node_names = graph.vs["name"]
        if "weights" in graph.es.attributes():
            weights = graph.es["weights"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.pagerank.name, LocalTopology.pagerank(graph, node_names, weights, damping), node_names)
        
    @staticmethod
    @check_graph_consistency
    def add_shortest_path_igraph(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.shortest_path_igraph.name, LocalTopology.shortest_path_igraph(graph, node_names), node_names)

    @staticmethod
    @check_graph_consistency
    def add_shortest_path(graph, node_names=None, mode=GraphType.undirect_unweighted):
        implementation = implementation_check(graph)
        distances = LocalTopology.shortest_path_pyntacle(graph, node_names, mode, implementation=implementation).tolist()
        if node_names is None:
            node_names = graph.vs["name"]
        distances_with_inf = ShortestPathModifier.igraph_sp_to_inf(distances, graph.vcount()+1)
        AddAttributes(graph).add_node_attributes(LocalAttribute.shortest_path.name, distances_with_inf, node_names)

    @staticmethod
    @check_graph_consistency
    def add_average_shortest_path_length(graph, node_names=None, exclude_inf=True):
        implementation = implementation_check(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.average_shortest_path_length.name,
                                                 LocalTopology.average_shortest_path_length(graph, node_names, exclude_inf, implementation=implementation), node_names)

 
    @staticmethod
    @check_graph_consistency
    def add_median_shortest_path_length(graph, node_names=None, exclude_inf=True):
        implementation = implementation_check(graph)
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes(LocalAttribute.median_shortest_path_length.name,
                                                 LocalTopology.median_shortest_path_length(graph, node_names, exclude_inf, implementation=implementation), node_names)
   
    # Metrics
    
    @staticmethod
    @check_graph_consistency
    def add_F(graph):
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.F.name, KeyPlayer.F(graph))

    @staticmethod
    @check_graph_consistency
    def add_dF(graph, max_distances=None):
        implementation = implementation_check(graph)
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.dF.name, KeyPlayer.dF(graph, implementation=implementation, max_distances=max_distances))

    # KP

    @staticmethod
    @check_graph_consistency
    def add_kp_F(graph, nodes):
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KPNEGchoices.F)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.F.name+'_kpinfo', {tuple(results_dict[KPNEGchoices.F.name][0]): results_dict[KPNEGchoices.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_dF(graph, nodes, max_distances=None):
        implementation = implementation_check(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KPNEGchoices.dF, max_distances=max_distances, implementation=implementation)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.dF.name+'_kpinfo', {tuple(results_dict[KPNEGchoices.dF.name][0]): results_dict[KPNEGchoices.dF.name][1]})


    @staticmethod
    @check_graph_consistency
    def add_kp_dR(graph, nodes, max_distances=None):
        implementation = implementation_check(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KPPOSchoices.dR, max_distances=max_distances, implementation=implementation)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPPOSchoices.dR.name+'_kpinfo', {tuple(results_dict[KPPOSchoices.dR.name][0]): results_dict[KPPOSchoices.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_kp_mreach(graph, nodes, m=None, max_distances=None):
        implementation = implementation_check(graph)
        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KPPOSchoices.mreach,  m=m, max_distances=max_distances, implementation=implementation)
        results_dict = kpobj.get_results()
        attr_name = KPPOSchoices.mreach.name+'_{}_kpinfo'.format(str(m))
        AddAttributes(graph).add_graph_attributes(attr_name, {tuple(results_dict[KPPOSchoices.mreach.name][0]): results_dict[KPPOSchoices.mreach.name][1]})

    # greedy
    @staticmethod
    @check_graph_consistency
    def add_GO_F(graph, kpp_size, seed=None):
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.F, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.F.name+'_greedy', {tuple(results_dict[KPNEGchoices.F.name][0]): results_dict[KPNEGchoices.F.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dF(graph, kpp_size, max_distances=None, seed=None):
        implementation = implementation_check(graph)
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.dF, max_distances=max_distances, seed=seed, implementation=implementation)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.dF.name+'_greedy', {tuple(results_dict[KPNEGchoices.dF.name][0]): results_dict[KPNEGchoices.dF.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_dR(graph, kpp_size, max_distances=None, seed=None):
        implementation = implementation_check(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.dR, max_distances=max_distances, seed=seed, implementation=implementation)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPPOSchoices.dR.name+'_greedy', {tuple(results_dict[KPPOSchoices.dR.name][0]): results_dict[KPPOSchoices.dR.name][1]})

    @staticmethod
    @check_graph_consistency
    def add_GO_mreach(graph, kpp_size, m=None, max_distances=None, seed=None):
        implementation = implementation_check(graph)
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.mreach, m=m, max_distances=max_distances, seed=seed, implementation=implementation)
        results_dict = kpobj.get_results()
        attr_name = KPPOSchoices.mreach.name+'_{}_greedy'.format(str(m))
        AddAttributes(graph).add_graph_attributes(attr_name, {tuple(results_dict[KPPOSchoices.mreach.name][0]): results_dict[KPPOSchoices.mreach.name][1]})
    
    #bruteforce
    
    @staticmethod
    @check_graph_consistency
    def add_BF_F(graph, kpp_size, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.F, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.F.name+'_bruteforce', {tuple(tuple(x) for x in results_dict[KPNEGchoices.F.name][0]): results_dict[KPNEGchoices.F.name][1]})
        
    @staticmethod
    @check_graph_consistency
    def add_BF_dF(graph, kpp_size, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.dF, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPNEGchoices.dF.name+'_bruteforce', {tuple(tuple(x) for x in results_dict[KPNEGchoices.dF.name][0]): results_dict[KPNEGchoices.dF.name][1]})
    
    @staticmethod
    @check_graph_consistency
    def add_BF_dR(graph, kpp_size, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.dR, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes(KPPOSchoices.dR.name+'_bruteforce', {tuple(tuple(x) for x in results_dict[KPPOSchoices.dR.name][0]): results_dict[KPPOSchoices.dR.name][1]})
        
    @staticmethod
    @check_graph_consistency
    def add_BF_mreach(graph, kpp_size, m=None, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.mreach, max_distances=max_distances, m=m)
        results_dict = kpobj.get_results()
        attr_name = KPPOSchoices.mreach.name+'_{}_bruteforce'.format(str(m))
        AddAttributes(graph).add_graph_attributes(attr_name, {tuple(tuple(x) for x in results_dict[KPPOSchoices.mreach.name][0]): results_dict[KPPOSchoices.mreach.name][1]})