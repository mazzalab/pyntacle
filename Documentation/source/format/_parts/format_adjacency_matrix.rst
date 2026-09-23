**In command line:** ``-t/--fileType matrix``

An adjacency matrix is a squared *nxn* matrix, where row *i* and column *j* indices refer to nodes in a network. A non-zero value filling a cell :math:`a_{ij}`  indicates the presence of a connecting edge between the nodes *i* and *j*.

.. |aij| replace:: a :sub:`ij`

.. csv-table:: Header
   :width: 30%
   :header: , A, B, C
   :widths: 10, 10, 10, 10

   A, 0, 1, 1
   B, 1, 0, 1
   C, 1, 1, 0

.. csv-table:: No header
   :width: 30%
   :widths: 10, 10, 10

   0, 1, 1
   1, 0, 1
   1, 1, 0

In the weighted case a non-zero float number indicates the weight on the corresponding edge.

.. csv-table:: Header
   :width: 30%
   :header: , A, B, C
   :widths: 10, 10, 10, 10

   A, 0.0, 0.7, 0.3
   B, 0.7, 0.0, 0.9
   C, 0.3, 0.9, 0.0

.. csv-table:: No header
   :width: 30%
   :widths: 10, 10, 10

   0.0, 0.7, 0.3
   0.7, 0.0, 0.9
   0.3, 0.9, 0.0
