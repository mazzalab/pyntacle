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
     - Use this flag if your graph is weighted (see :doc:`/weights`)
   * - ``-wt``, ``--weight-type``
     - No
     - str
     - distance
     - distance, affinity, signed
     - With ``-w``: what the weights are — lengths, tie strengths, or signed strengths such as correlations (magnitude used, sign kept). Negative weights require ``signed``
   * - ``-dt``, ``--distance-transform``
     - No
     - str
     - inverse
     - inverse, one-minus, neglog
     - With ``-w`` and an ``affinity`` or ``signed`` type: how a strength *a* becomes a length (1/*a*, 1 − *a*, −ln *a*)
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
   * - ``--no-plot``
     - No
     - bool
     - False
     - \ 
     - Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle's ``--no-plot``)
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
     - Use this flag to receive prints of partial results of the measures.

Examples
--------

Compute GTOM and TI with default k=3 steps:

.. code-block:: bash

   python main.py mesoscale \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 3 \
       -o /tmp/out/

Use k=5 steps and enable Topological Overlap with threshold 0.3:

.. code-block:: bash

   python main.py mesoscale \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 5 \
       -th 0.3 \
       -o /tmp/out/

Compute weighted TI on a weighted network:

.. code-block:: bash

   python main.py mesoscale \
       -t edgelist \
       -i weighted_network.egl \
       -w \
       -k 3 \
       -o /tmp/out/

Output files:

- ``report_<graph>_mesoscale.tsv`` — TI matrix, optional WI matrix, GTOM matrix
- ``<graph>_mesoscale.svg`` — network visualization

See :doc:`../../mesoScales/mesoScales` for metric definitions and
:doc:`../../outputs` for report documentation.
