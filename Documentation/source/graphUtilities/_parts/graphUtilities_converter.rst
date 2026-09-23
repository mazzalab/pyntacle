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
* when exporting a matrix, weights are rounded to 3 decimals.
