API Reference
=============

This section documents the public Python API of Pyntacle. After
:doc:`installation`, every module is importable from the ``pyntacle`` package:

.. code-block:: python

   from pyntacle.GraphTacle import Graphtacle
   from pyntacle.algorithms.key_player import keyplayer_kpInfo

.. note::

   Most users will interact with Pyntacle through the ``pyntacle`` command.
   The Python API is useful for embedding analyses in notebooks or custom scripts.

.. contents::
   :local:
   :depth: 2

Core Graph Class
-----------------

.. autoclass:: pyntacle.GraphTacle.Graphtacle
   :members:
   :show-inheritance:

Key-Player Metrics
------------------

.. automodule:: pyntacle.algorithms.key_player
   :members: fragmentation, distance_fragmentation, distance_weighted_reach, reachability, keyplayer_kpInfo

Group Centrality Metrics
-------------------------

.. automodule:: pyntacle.algorithms.group_centrality
   :members:

Mesoscale Metrics
-----------------

.. automodule:: pyntacle.mesoscale
   :members: gtom, ti

Community Detection
--------------------

.. automodule:: pyntacle.communities
   :members: communities, communities_filtering, communities_to_df

Graph Generation
-----------------

.. automodule:: pyntacle.generate
   :members: erdos_renyi, tree_generate, barabasi, watts_strogatz, lattice

Graph I/O Utilities
--------------------

.. automodule:: pyntacle.utility
   :members: import_adjMatrix, import_edgeList, import_sif, import_dot, output_decision, get_connected_subgraph, extract_and_df
