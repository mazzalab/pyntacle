r"""
The purpose of this module is to provide a series of utilities for Pyntacle-related objects, namely:

* the igraph :py:class:`~igraph.Graph` object and its layers (the whole graph nodes and edges)
* the adjacency matrix representation of a network
* the edge list network representation
* the enumerators that Pyntacle uses to keep track of internal and graph-related attributes

These utilities can be freely accessible and can be used by developers and users alike. Of notable interest among this
module is :class:`~pyntacle.tools.octopus`, a method that runs all the available Pyntacle indices available in
:class:`~pyntacle.algorithms` and automatically adds the result to the :py:class:`~igraph.Graph`

In brief, This module is arranged as follows:


**Graph tools:**

* :class:`~pyntacle.tools.add_attributes`: adds attributes to the whole graph, nodes and edges. These attrbutes can be either custom attributes or Pyntacle-reserved attributes
* :class:`~pyntacle.tools.graph_utils`: a series of utilities to initialize graph attributes, perform graph checks and automatize a series of common operations on graph objects

**Network file representation tools**

* :class:`~pyntacle.tools.adjmatrix_utils`: a series of tools to check the integrity of adjacency matrix file and make adjacency matrices compliant to the `adjacency matrix file specifications <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#adjm>`_
* :class:`~pyntacle.tools.edgelist_utils`: a series of tools to check the integrity of edge list file and make edge lists compliant to the `edge list file specifications <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#egl>`_

**Other Tools**

* :class:`~pyntacle.tools.enums`: The enumerators that are used by Pyntacle to deal with graph name attributes and to initialize many of the arguments of the :class:`~pyntacle.algorithms`
* :class:`~pyntacle.tools.octopus`: A special class that automatically adds Pyntacle indices to the Graph objects at different levels and take care of all the redundant parameters. Useful for performing operations on the graph and produce ready-to-use :py:class:`~igraph.Graph`  objects for an interactive Python shell or a notebook.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
