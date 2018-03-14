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

""" **a series of decorators to improve the usability of some pyntacle's function, like 
checking if the `igraph.Graph` object is compatible with pyntacle's specifications, verify the presence of nodes 
in the input graph, give elapsed time of execution and so on"""

from enum import Enum, auto
from config import *

"""Contains all the enumerators used in pyntacle's methods"""


class GraphType(Enum):
    """
    An enumerator that contains the different modes that will be used to compute internally the shortest path of a graph
    For the record, I still prefer the string method
    """
    undirect_unweighted = auto()
    undirect_weighted = auto()
    direct_unweighted = auto()
    direct_weighted = auto()


class SP_implementations(Enum):
    """
    this enumerator stores the different ways that can be used to parallelize the shortest path search for a set of nodes
    """
    igraph = auto()
    cpu = auto()
    gpu = auto()
    auto = auto()

class KPNEGchoices(Enum):
    """
    this enumerator stores the metrics that can be queried to Kpp-POS calculations
    """
    F = auto()
    dF = auto()

class KPPOSchoices(Enum):
    """
    this enumerator stores the metrics that can be queried to Kpp-POS calculations
    """
    mreach = auto()
    dR = auto()

class LocalAttribute(Enum):
    """
    this enumerator stores all the node attributes that can be instantiated by pyntacle
    """
    degree = auto()
    betweenness = auto()
    radiality = auto()
    radiality_reach = auto()
    eccentricity = auto()
    pagerank = auto()
    shortestpaths = auto()
    eigenvector_centrality = auto()
    closeness = auto()
    clustering_coefficient = auto()

class GlobalAttribute(Enum):
    """
    this enumerator stores all the edge attributes that can be instantiated by pyntacle
    """
    average_shortest_path_length = auto()
    median_shortest_path_length = auto()
    diameter = auto()
    components = auto()
    radius = auto()
    density = auto()
    pi = auto()
    average_clustering_coefficient = auto()
    weighted_clustering_coefficient = auto()
    average_degree = auto()
    average_closeness = auto()
    average_eccentricity = auto()
    average_radiality = auto()
    average_radiality_reach = auto()
    completeness_mazza = auto()
    completeness_XXX = auto()
    compactness = auto()

class Reports(Enum):
    Global = auto()
    Local = auto()
    KPinfo = auto()
    KP_greedy = auto()
    KP_bruteforce = auto()
    Communities = auto()
    Set = auto()

class edge_attributes(Enum):
    """
    this enumerator stores all the edge attributes that can be instantiated by pyntacle
    """
    pass