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
from algorithms.local_topology_NEW import LocalTopology
from algorithms.global_topology_NEW import GlobalTopology
from misc.enums import *
from misc.enums import GraphType
from misc.enums import SP_implementations as imps
from misc.shortest_path_modifications import ShortestPathModifier
from pyntacle_commands_utils.kpsearch_wrapper_NEW import KPWrapper as kpw
from pyntacle_commands_utils.kpsearch_wrapper_NEW import GOWrapper as gow
from pyntacle_commands_utils.kpsearch_wrapper_NEW import BFWrapper as bfw
from misc.enums import KPNEGchoices, KPPOSchoices

class Octopus:
    
    #Global
    @staticmethod
    def add_diameter(graph):
        AddAttributes(graph).add_graph_attributes(GlobalAttribute.diameter.name, GlobalTopology.diameter(graph))

    @staticmethod
    def add_radius(graph):
        AddAttributes(graph).add_graph_attributes('radius', GlobalTopology.radius(graph))
        
    @staticmethod
    def add_components(graph):
        AddAttributes(graph).add_graph_attributes('components', GlobalTopology.components(graph))

    @staticmethod
    def add_density(graph):
        AddAttributes(graph).add_graph_attributes('density', GlobalTopology.density(graph))
        
    @staticmethod
    def add_pi(graph):
        AddAttributes(graph).add_graph_attributes('pi', GlobalTopology.pi(graph))
    
    @staticmethod
    def add_average_clustering_coefficient(graph):
        AddAttributes(graph).add_graph_attributes('average_clustering_coefficient',
                                                  GlobalTopology.average_clustering_coefficient(graph))

    @staticmethod
    def add_weighted_clustering_coefficient(graph):
        AddAttributes(graph).add_graph_attributes('weighted_clustering_coefficient',
                                                  GlobalTopology.weighted_clustering_coefficient(graph))
    
    @staticmethod
    def add_average_degree(graph):
        AddAttributes(graph).add_graph_attributes('average_degree', GlobalTopology.average_degree(graph))
    
    @staticmethod
    def add_average_closeness(graph):
        AddAttributes(graph).add_graph_attributes('average_closeness',
                                                  GlobalTopology.average_closeness(graph))
    
    @staticmethod
    def add_average_eccentricity(graph):
        AddAttributes(graph).add_graph_attributes('average_eccentricity',
                                                  GlobalTopology.average_eccentricity(graph))
    
    @staticmethod
    def add_average_radiality(graph):
        implementation = imps.igraph  # Todo: qui va creato il decisore che determina se usare gpu o cpu
        AddAttributes(graph).add_graph_attributes('average_radiality',
                                                  GlobalTopology.average_radiality(graph, implementation))
    
    @staticmethod
    def add_average_radiality_reach(graph):
        implementation = imps.igraph  # Todo: qui va creato il decisore che determina se usare gpu o cpu
        AddAttributes(graph).add_graph_attributes('average_radiality_reach',
                                                  GlobalTopology.average_radiality_reach(graph,
                                                                                         implementation))
    @staticmethod
    def add_average_shortest_path_length(graph):
        implementation = imps.igraph  # Todo: qui va creato il decisore che determina se usare gpu o cpu
        AddAttributes(graph).add_graph_attributes('average_shortest_path_length',
                                                  GlobalTopology.average_shortest_path_length(graph,
                                                                                              implementation))
    
    
    # Local
    @staticmethod
    def add_degree(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('degree', LocalTopology.degree(graph, node_names), node_names)
    
    @staticmethod
    def add_betweenness(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('betweenness', LocalTopology.betweenness(graph, node_names), node_names)
        
    @staticmethod
    def add_clustering_coefficient(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('clustering_coefficient', LocalTopology.clustering_coefficient(graph, node_names), node_names)
    
    @staticmethod
    def add_closeness(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('closeness', LocalTopology.closeness(graph, node_names), node_names)
        
    @staticmethod
    def add_eccentricity(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('eccentricity', LocalTopology.eccentricity(graph, node_names), node_names)
    
    @staticmethod
    def add_radiality(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('radiality', LocalTopology.radiality(graph, node_names), node_names)
        
    @staticmethod
    def add_radiality_reach(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('radiality_reach', LocalTopology.radiality_reach(graph, node_names), node_names)
        
    @staticmethod
    def add_eigenvector_centrality(graph, node_names=None, scaled=False):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('eigenvector_centrality', LocalTopology.eigenvector_centrality(graph, node_names, scaled), node_names)
        
    @staticmethod
    def add_pagerank(graph, node_names=None, weights=None, damping=0.85):
        if node_names is None:
            node_names = graph.vs["name"]
        if "weights" in graph.es.attributes():
            weights = graph.es["weights"]
        AddAttributes(graph).add_node_attributes('pagerank', LocalTopology.pagerank(graph, node_names, weights, damping), node_names)
        
    @staticmethod
    def add_shortest_path_igraph(graph, node_names=None):
        if node_names is None:
            node_names = graph.vs["name"]
        AddAttributes(graph).add_node_attributes('shortest_path_igraph', LocalTopology.shortest_path_igraph(graph, node_names), node_names)

    @staticmethod
    ## Guarda il grafo e decide quale implementazione usare per lo shortest path, in automatico.
    # Per ora solo cpu ma piu' avanti aggiungi il resto
    def add_shortest_path(graph, node_names=None, mode=GraphType.undirect_unweighted):
        implementation = imps.cpu #Todo: qui va creato il decisore che determina se usare gpu o cpu
       
        distances = LocalTopology.shortest_path_pyntacle(graph, node_names, mode, implementation).tolist()
        if node_names is None:
            node_names = graph.vs["name"]
        distances_with_inf = ShortestPathModifier.igraph_sp_to_inf(distances, graph.vcount()+1)
        AddAttributes(graph).add_node_attributes("shortest_path", distances_with_inf, node_names)

    
    
    # KP
    
    @staticmethod
    def add_F(graph, nodes):
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KPNEGchoices.F)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('F', {tuple(results_dict['F'][0]): results_dict['F'][1]})

    @staticmethod
    def add_dF(graph, nodes, max_distances=None):
        kpobj = kpw(graph=graph)
        kpobj.run_KPNeg(nodes, KPNEGchoices.dF, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('dF', {tuple(results_dict['dF'][0]): results_dict['dF'][1]})


    @staticmethod
    def add_dR(graph, nodes, max_distances=None):
        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KPPOSchoices.dR, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('dR', {tuple(results_dict['dR'][0]): results_dict['dR'][1]})

            
    @staticmethod
    def add_mreach(graph, nodes, m=None, max_distances=None):
        kpobj = kpw(graph=graph)
        kpobj.run_KPPos(nodes, KPPOSchoices.mreach,  m=m, max_distances=max_distances)
        results_dict = kpobj.get_results()
        attr_name = 'mreach_{}'.format(str(m))
        AddAttributes(graph).add_graph_attributes(attr_name, {tuple(results_dict['mreach'][0]): results_dict['mreach'][1]})


    # greedy
    @staticmethod
    def add_GO_F(graph, kpp_size, seed=None):
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.F, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('F'+'_greedy', {tuple(results_dict['F'][0]): results_dict['F'][1]})

    @staticmethod
    def add_GO_dF(graph, kpp_size, max_distances=None, seed=None):
        kpobj = gow(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.dF, max_distances=max_distances, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('dF'+'_greedy', {tuple(results_dict['dF'][0]): results_dict['dF'][1]})

    @staticmethod
    def add_GO_dR(graph, kpp_size, max_distances=None, seed=None):
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.dR, max_distances=max_distances, seed=seed)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('dR'+'_greedy', {tuple(results_dict['dR'][0]): results_dict['dR'][1]})

    @staticmethod
    def add_GO_mreach(graph, kpp_size, m=None, max_distances=None, seed=None):
        kpobj = gow(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.mreach, m=m, max_distances=max_distances, seed=seed)
        results_dict = kpobj.get_results()
        attr_name = 'mreach_{}_greedy'.format(str(m))
        AddAttributes(graph).add_graph_attributes(attr_name, {tuple(results_dict['mreach'][0]): results_dict['mreach'][1]})
        
    
    #bruteforce
    
    @staticmethod
    def add_BF_F(graph, kpp_size, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.F, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('F'+'_bruteforce', {tuple(tuple(x) for x in results_dict['F'][0]): results_dict['F'][1]})
        
    @staticmethod
    def add_BF_dF(graph, kpp_size, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_fragmentation(kpp_size, KPNEGchoices.dF, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('dF'+'_bruteforce', {tuple(tuple(x) for x in results_dict['dF'][0]): results_dict['dF'][1]})
    
    @staticmethod
    def add_BF_dR(graph, kpp_size, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.dR, max_distances=max_distances)
        results_dict = kpobj.get_results()
        AddAttributes(graph).add_graph_attributes('dR'+'_bruteforce', {tuple(tuple(x) for x in results_dict['dR'][0]): results_dict['dR'][1]})
        
    @staticmethod
    def add_BF_mreach(graph, kpp_size, m=None, max_distances=None):
        kpobj = bfw(graph=graph)
        kpobj.run_reachability(kpp_size, KPPOSchoices.mreach, max_distances=max_distances, m=m)
        results_dict = kpobj.get_results()
        attr_name = 'mreach_{}_bruteforce'.format(str(m))
        AddAttributes(graph).add_graph_attributes(attr_name, {tuple(tuple(x) for x in results_dict['mreach'][0]): results_dict['mreach'][1]})
