r"""
This module wraps a series of graph operations that can be used to transform the input graphs and create new network
structures. These operations can be inter and intra graph.

In the first case a series of logical set operations among graph (union, intersection, difference) are performed among
two input graphs of interest. The resulting graph (a :py:class:`~igraph.Graph` object) holds some of the structural
properties of the original graphs, according to the set operation performed.

The latter is a series of community finding algorithms to discover groups of tightly related vertices in a graph
using different heuristics. These algorithms are taken directly from the
`Python iGraph library <https://igraph.org/python/>`_ and wrapped in order to unify the output of the corresponding
igraph methods. Specifically, the methods always returns a list of induced subgraphs each holding the same attributes
of the original :py:class:`~igraph.Graph` object.

This module is organized as follows:

* :class:`~pyntacle.graph_operations.set_operations`: union, intersection and difference among two input graph that produces a third graph.

.. warning:: The attributes of the original graphs will be lost when performing set operations

.. note:: The original graph ``name`` attribute of each starting graph will be added to the resulting graph. Furthermore, the vertex ``parent`` attribute, storing the graph name, will be present in the resulting graph and will store the origin of each resulting vertex.

* :class:`~pyntacle.graph_operations.communities`: A wrapper around a series of well-established algorithms for community detection in a graph that were choosen to fit in biological and real networks and their occurrence in literature. specifically, these algorithms are:
    * *fastgreedy*: an algorithm based on the notorious modularity score by Clauset and Newman (https://doi.org/10.1103/PhysRevE.70.066111)
    * *infomap*: an algorithm based on information flow and designed by Rosvall and Bergstrom (https://doi.org/10.1073/pnas.0706851105)
    * *leading eigenvector*: find clusters of nodes by computing the modularity matrix of the graph and to derive the eigenvector of the matrix, as described by newman (https://doi.org/10.1103/PhysRevE.74.036104)
    * *walktrap*: a community-finding algorithm desgiend by Pons and Latapy (https://arxiv.org/abs/physics/0512106) based on random walks to identify groups of densely connected  vertices in a sparse graph.

"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


