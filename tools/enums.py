"""
A set of enumerators whose values are used as reserved keywords in Pyntacle's functions
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = "0.0.5"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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


import enum


class GraphTypeEnum(enum.Enum):
    """
    An enumerator that specifies the nature of the graph
    """
    undirect_unweighted = 1
    undirect_weighted = 2
    direct_unweighted = 3
    direct_weighted = 4


class CmodeEnum(enum.Enum):
    r"""
    An enumerator that is used to use different heuristics for the computation of the shortest paths among all nodes in the graph
    In detail, the avilable enumerators are:
        * ``igraph``: uses the :meth:`shortest_paths<igraph:igraph.Graph.shortest_paths>` embedded in :class:`~pyntacle.shortest_path.ShortestPath`
        * ``cpu``: uses the `Floyd-Warshall algorithm <https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm>`_  by means of parallel CPU computing to obtain a matrix of distances for all nodes in the graph.This method returns a matrix (:py:class:`numpy.ndarray`) of shortest paths. Infinite distances actually equal the total number of vertices plus one.
        * ``gpu``: same as ``cpu``, but using parallel GPU processing (enabled when a CUDA-supported device is present). This method returns a matrix (:py:class:`numpy.ndarray`) of shortest paths. Infinite distances actually equal the total number of vertices plus one.

        .. warning:: Use this implementation **only** if the `CUDA Toolkit <https://developer.nvidia.com/cuda-toolkit>`_ is installed on your machine and your CUDA device has CUDA 2.0 onwards

        * ``auto``:automatically identifies the best mean to compute shortest paths by looking at the graph size and density
    """
    igraph = 1
    cpu = 2
    gpu = 3
    auto = 4


class KpnegEnum(enum.Enum):
    r"""
    A series of enumerators that stores the possible negative *key player* measures to compute *fragmentation*.
    See the `What are Key Players guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_
    for more info on how fragmentation indices can be used to find critical nodes

    Choices are:

    * ``F``: *fragmentation*, a measure based on the number of components
    * ``dF``: *distance-based fragmentation*, a measure that relies on distances (shortest paths) among nodes.

    """
    F = 1
    dF = 2


class KpposEnum(enum.Enum):
    r"""
    A series of enumerators that stores the possible positive *key player* measures to compute *reachability*.
    See the `What are Key Players guide <http://pyntacle.css-mendel.it/resources/kp_guide/kp_guide.html>`_
    for more info on how reachability indices can be used to find critical nodes responsible for information flow in the graph

    Choices are:

    * ``mreach``: *m-reach*, a measure based on the number of nodes that can be reached by a selected group of nodes
    * ``dR``: *distance based reach*, a measure based on the distances among a group of nodes and the rest of the graph
    """
    mreach = 1
    dR = 2


class GroupCentralityEnum(enum.Enum):
    r"""
    The available group centrality metrics that can be found either by :class:`~pyntacle.algorithms.bruteforce_search.BruteforceSearch` or by :class:`~pyntacle.algorithms.greedy_optimization.GreedyOptimization`
    """
    group_degree = 1
    group_betweenness = 2
    group_closeness = 3


class GroupDistanceEnum(enum.Enum):
    r"""
    Enumerators for considering distances between a group of nodes and the rest of the graph.
    """
    minimum = 1
    maximum = 2
    mean = 3


class GraphOperationEnum(enum.Enum):
    r"""
    The logical operations that can be passed to :func:`~pyntacle.graph_operations.set_operations.GraphOperations.make_sets`
    """
    Union = 1
    Intersection = 2
    Difference = 3


class LocalAttributeEnum(enum.Enum):
    r"""
    A series of internal attributes for local centrality measures
    """
    degree = 1
    betweenness = 2
    radiality = 3
    radiality_reach = 4
    eccentricity = 5
    pagerank = 6
    shortest_paths = 7
    eigenvector_centrality = 8
    closeness = 9
    clustering_coefficient = 10
    average_shortest_path_length = 11
    median_shortest_path_length = 12


class GlobalAttributeEnum(enum.Enum):
    r"""
    A series of internal attributes for global centrality measures
    """
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
    average_global_shortest_path_length = 18
    median_global_shortest_path_length = 19


class ReportEnum(enum.Enum):
    r"""
    Internal enumerators for choosing the type of report that will be outputted by Pyntacle command line utility
    """
    Global = 1
    Local = 2
    KPinfo = 3
    KP_greedy = 4
    KP_bruteforce = 5
    Communities = 6
    Set = 7
