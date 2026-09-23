:orphan:


mesoscale
=========

Mesoscale metrics capture intermediate-scale structure by combining neighborhood overlap and multi-step influence measures.

Available metrics:

- **GTOM (Generalized Topological Overlap Measure)**: neighborhood similarity between all pairs of nodes. Values lie in ``[0, 1]``; it approaches 1 when neighborhoods are identical or one is a subset of the other.
- **TI (Topological Importance)**: node influence via k-step structural propagation. Computed from powers of the edge-effect matrix to capture indirect interactions up to path length k.
- **WI (Weighted Topological Importance)**: TI variant that also accounts for interaction strengths (edge weights).
- **STO (Species Topological Overlap)**: pairwise structural similarity based on shared 1-step effects, extended to k-step propagation; a threshold ``θ`` can be applied to filter weak overlaps.

Synopsis
--------
.. code-block:: console

   python3 main.py mesoscale [OPTIONS]


Options
-------
.. list-table::
   :header-rows: 1
   :widths: 18 8 12 12 14 36

   * - Option
     - Required
     - Type
     - Default
     - Choices
     - Help
   * - ``-t``, ``--fileType``
     - Yes
     - str
     - \ 
     - matrix, edgelist, sif, dot
     - File type
   * - ``-i``, ``--inputFile``
     - Yes
     - \ 
     - \ 
     - \ 
     - Specify the input file name
   * - ``-s``, ``--sep``
     - No
     - str
     - \ 
     - \ 
     - Use this flag if your file has a specific separator (ex. '\t')
   * - ``-nh``, ``--NoHeader``
     - No
     - bool
     - False
     - \ 
     - Use this flag if your file doesn't have an header
   * - ``-d``, ``--directed``
     - No
     - bool
     - False
     - \ 
     - Use this flag if your graph is directed
   * - ``-w``, ``--weight``
     - No
     - bool
     - False
     - \ 
     - Use this flag if your graph is weighted
   * - ``-r``, ``--remove``
     - No
     - \ 
     - \ 
     - \ 
     - Select the node/nodes to be removed from the graph (ex. A,B,C)
   * - ``-k``, ``--kSteps``
     - No
     - int
     - 3
     - \ 
     - Maximum effects lenght considered. Defautl value is 3.
   * - ``-th``, ``--threshold``
     - No
     - float
     - 0.0
     - \ 
     - Threshold that will be used to compute TO. TO will not be computed if no threshold is selected
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same direcotry as the input file)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output
   * - ``-v``, ``--verbose``
     - No
     - bool
     - False
     - \ 
     - Use this flag to recive prints of partial results of the measures.
