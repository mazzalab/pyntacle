.. _supported-file-formats-in-pyntacle:

Supported File Formats in Pyntacle
==================================

.. contents::
   :local:
   :depth: 2

Reading rules
-------------

These hold for every format:

* Node names are read as text, so ``1`` and ``01`` are two different nodes
  and ``-n 1`` finds node ``1``.
* Self-loops are removed and parallel edges are merged into one, keeping the
  largest weight; a warning gives how many.
* Without ``-w`` the weights in the file are ignored and every edge has
  weight 1. See :doc:`/weights` for what ``-w`` reads.
* A node with no edges can only be written in a matrix or a DOT file; an edge
  list or a SIF file cannot hold it, and ``convert``, ``set`` and ``extract``
  warn when they leave such nodes out.

.. _format-adjacency-matrix:

Adjacency Matrix
----------------
.. include:: _parts/format_adjacency_matrix.rst

.. _format-edge-list:

Edge List
---------
.. include:: _parts/format_edge_list.rst

.. _format-sif:

Simple Interaction Format (SIF)
-------------------------------
.. include:: _parts/format_sif.rst

.. _format-dot:

DOT Files
---------
.. include:: _parts/format_dot.rst

.. _format-attribute-files:

Attribute Files
---------------
.. include:: _parts/format_attribute_files.rst
