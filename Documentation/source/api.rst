API Reference
=============

This section documents the public Python API of Pyntacle.
All modules live under the ``pyntacle/`` source directory.

.. note::

   To use the API directly, add the ``pyntacle/`` directory to your Python path:

   .. code-block:: python

      import sys
      sys.path.insert(0, '/path/to/pyntacle_final/pyntacle')

   Most users will interact with Pyntacle through the CLI (``python main.py``).
   The Python API is useful for embedding analyses in notebooks or custom scripts.

.. contents::
   :local:
   :depth: 2

Core Graph Class
-----------------

.. autoclass:: GraphTacle.Graphtacle
   :members:
   :show-inheritance:

Key-Player Metrics
------------------

.. automodule:: algorithms.key_player
   :members: fragmentation, distance_fragmentation, distance_weighted_reach, reachability, keyplayer_kpInfo

Group Centrality Metrics
-------------------------

.. automodule:: algorithms.group_centrality
   :members:

Mesoscale Metrics
-----------------

.. automodule:: mesoscale
   :members: gtom, ti

Community Detection
--------------------

.. automodule:: communities
   :members: communities, communities_filtering, communities_to_df

Graph Generation
-----------------

.. automodule:: generate
   :members: erdos_renyi, tree_generate, barabasi, watts_strogatz, lattice

Graph I/O Utilities
--------------------

.. automodule:: utility
   :members: import_adjMatrix, import_edgeList, import_sif, import_dot, output_decision, get_connected_subgraph, extract_and_df
