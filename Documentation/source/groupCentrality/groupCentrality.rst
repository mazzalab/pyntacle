Graph Group Metrics
===================

This class of topological indices is a strict extension of that of their homonym local centrality indices, since they are applied to groups rather than to individual nodes. Differently from local metrics, a group centrality score applies to an array of nodes taken together, neglecting the contributions of the individuals. It is straightforward to notice that these indices can be useful also in Biology, other than in Social Sciences, where these were born from.

The group centrality metrics implemented in Pyntacle are group degree, group closeness and group betweenness. They were firstly described by `Everett and Borgatti`_ in 1999. Pyntacle stays faithful to the definitions reported in this paper, but the reader must be warned that other formulations of these metrics exist in literature.

.. _`Everett and Borgatti`: https://doi.org/10.1080/0022250X.1999.9990219

.. contents::
   :local:
   :depth: 2

.. _group-degree:

Group Degree
------------
.. include:: _parts/groupCentrality_degree.rst

.. _group-closeness:

Group Closeness
---------------
.. include:: _parts/groupCentrality_closeness.rst

.. _group-betweenness:

Group Betweenness
-----------------
.. include:: _parts/groupCentrality_betweenness.rst
