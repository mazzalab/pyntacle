r"""
This module is the backbone of Pyntacle. It computes several indices of **global** and **local** nature. The latter class
includes group centralities, such as *key players* that can be used to assess the centralities of groups of (possibly unconnected) nodes,
enriching the information on centralities focused on single nodes, also reported.
Additionally,this module contains the heuristics needed to perform group-centrality searches of optimal or best node sets
that optimize group centrality indice and wraps methods from `igraph <https://igraph.org/python/>`_ to infer network topology.

This module is organized as follows:

**Local centrality submodules:**

* :class:`~pyntacle.algorithms.local_topology`: contains local centrality indices for single nodes or groups of nodes (e.g. *node degree* and *group degree*)
* :class:`~pyntacle.algorithms.shortest_path`: a series of centralities that revolves around the minimum least distance among node pairs.
* :class:`~pyntacle.algorithms.shortest_path_gpu`: uses GPU acceleration by means of `numba <http://numba.pydata.org/>`_ to compute a matrix of distances

.. note:: The distances are computed either using a single cpu or by parallelizing the task by means of `numba <http://numba.pydata.org/>`_

.. warning:: Import this module **only** if you have a CUDA compatible GPU and the `Cuda Toolkit <https://developer.nvidia.com/cuda-toolkit>`_ is installed

**Global centrality submodules:**

* :class:`~pyntacle.algorithms.global_topology`: metrics that are used to infer graph general properties (e.g. *average degree*)
* :class:`~pyntacle.algorithms.sparseness`: a series of indices to assess whether the graph is dense (high edge-to-node ratio) or sparse (low end-to-node ratio)

**Other centralities submodules:**

* :class:`~pyntacle.algorithms.keyplayer`: the *fragmentation* and *reachability* metrics as originally proposed by Borgatti (https://doi.org/10.1007/s10588-006-7084-x)

**Group Centrality Heuristics:**

* :class:`~pyntacle.algorithms.bruteforce_search`: find the best set of nodes of size *k* that maximize on of the proposed group centrality metrics by exploring all the spaced of possible combinations using multi thred processing
* :class:`~pyntacle.algorithms.greedy_optimization`: find an optimal set of nodes of size *k* through a greedy approach

**Miscellanea:**

* :class:`~pyntacle.algorithms.scalefree_inference`: find how does the fist of a power law on the degree distribution can be used to infer whether the network follows a scale-free distribution

"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

