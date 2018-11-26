"""
A set of enumerators whose values are used as reserved keywords in Pyntacle's functions
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.5"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "02/10/2018"
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


from enum import Enum


class GraphTypeEnum(Enum):
    undirect_unweighted = 1
    undirect_weighted = 2
    direct_unweighted = 3
    direct_weighted = 4


class CmodeEnum(Enum):
    igraph = 1
    cpu = 2
    gpu = 3
    auto = 4


class KpnegEnum(Enum):
    F = 1
    dF = 2


class KpposEnum(Enum):
    mreach = 1
    dR = 2


class LocalAttributeEnum(Enum):
    degree = 1
    betweenness = 2
    radiality = 3
    radiality_reach = 4
    eccentricity = 5
    pagerank = 6
    shortest_path_igraph = 7
    shortest_path = 8
    eigenvector_centrality = 9
    closeness = 10
    clustering_coefficient = 11
    average_shortest_path_length = 12
    median_shortest_path_length = 13


class GroupCentralityEnum(Enum):
    group_degree = 1
    group_betweenness = 2
    group_closeness = 3


class GlobalAttributeEnum(Enum):
    average_shortest_path_length = 1
    median_shortest_path_length = 2
    diameter = 3
    components = 4
    radius = 5
    density = 6
    pi = 7
    average_clustering_coefficient = 8
    weighted_clustering_coefficient = 9
    average_degree = 10
    average_closeness = 11
    average_eccentricity = 12
    average_radiality = 13
    average_radiality_reach = 14
    completeness_naive = 15
    completeness = 16
    compactness = 17
    compactness_correct = 18


class ReportEnum(Enum):
    Global = 1
    Local = 2
    KPinfo = 3
    KP_greedy = 4
    KP_bruteforce = 5
    Communities = 6
    Set = 7


class GraphOperationEnum(Enum):
    Union = 1
    Intersection = 2
    Difference = 3


class GroupDistanceEnum(Enum):
    minimum = 1
    maximum = 2
    mean = 3
