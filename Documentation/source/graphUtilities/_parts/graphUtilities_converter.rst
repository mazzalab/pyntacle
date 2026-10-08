The ``convert`` command exports the current graph into one of the supported output formats:

* adjacency matrix
* edge list (2 columns for unweighted, 3 columns for weighted)
* SIF
* DOT

.. note::

   For a detailed description of the supported input/output formats (including separators, headers, and examples),
   see :ref:`Supported File Formats in Pyntacle <supported-file-formats-in-pyntacle>`.

Implementation notes:

* directed exports are currently not implemented in the converter utilities.
* weights are written with every digit they were read with.
* an edge list or a SIF file cannot hold a node without edges: such nodes are
  left out, with a warning naming them; a matrix or a DOT file keeps them.
