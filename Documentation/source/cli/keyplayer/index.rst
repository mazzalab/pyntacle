:orphan:


keyplayer
=========

Specific usage
--------------
.. code-block:: console

   python3 main.py keyplayer kp-info -t {fileType} -i {input_file} -n {node-list}
   python3 main.py keyplayer kp-finder -t {fileType} -i {input_file} -k {k-size}

Subcommand summary
------------------

kp-info
  Compute individual key-player metrics for a selected set of nodes

kp-finder
  Find the best kp-set of size k

Synopsis
--------
.. code-block:: console

   python3 main.py keyplayer <subcommand> [OPTIONS]


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
   * - ``subcommand``
     - Yes
     - \ 
     - \ 
     - kp-info, kp-finder
     - Select one the subfunctions right after keyplayer
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
     - Use this flag if your file has a specific header (ex. ',')
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
     - Select the node/nodes to be romev from the graph (ex. A,B,C)
   * - ``-n``, ``--nodes``
     - No
     - \ 
     - \ 
     - \ 
     - Nodes to select ONLY IN KP-INFO (Comma separated)
   * - ``-k``, ``--k_size``
     - No
     - int
     - 2
     - \ 
     - Number of nodes ONLY IN KP-FINDER (default=2)
   * - ``-m``, ``--mdist``
     - No
     - int
     - 2
     - \ 
     - Number of steps of the m-reach algorithm (default=2)
   * - ``-oper``, ``--operation``
     - No
     - str
     - all
     - all, F, dF, dR, mreach
     - Possible types: all | Neg: F, dF | Pos: dR, mreach (default="all")
   * - ``-a``, ``--algorithm``
     - No
     - str
     - brute_force
     - brute_force, greedy, gradient_descent
     - Select the algorithm to use when using the GC-FINDER command (default=brute_force)
   * - ``-p``, ``--probability``
     - No
     - float
     - 0
     - \ 
     - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0)
   * - ``-tol``, ``--tolerance``
     - No
     - float
     - 0.01
     - \ 
     - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0.01)
   * - ``-ms``, ``--maxsec``
     - No
     - int
     - 120
     - \ 
     - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=120)
   * - ``-np``, ``--nprocs``
     - No
     - int
     - 1
     - \ 
     - Number of process (default=1)
   * - ``--max-ties``
     - No
     - int
     - 100
     - \ 
     - Maximum number of equally-scoring node sets listed by the brute-force report. The reported count of optimal sets is exact even when the list is capped; ``greedy`` and ``gradient_descent`` ignore it
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output (svg, png)
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
   * - ``-c``, ``--cuda``
     - No
     - bool
     - False
     - \
     - Use this flag if you want to speed up computation by enabling parallel computing of APSP through CUDA.

Examples
--------

Find the best 2-node key-player set using the greedy algorithm (all 4 metrics):

.. code-block:: bash

   python main.py keyplayer kp-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 2 \
       -oper all \
       -a greedy \
       -m 2 \
       -o /tmp/out/

Find the optimal set using exhaustive brute-force with 4 threads:

.. code-block:: bash

   python main.py keyplayer kp-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 2 \
       -oper all \
       -a brute_force \
       -m 2 \
       -np 4 \
       -o /tmp/out/

Evaluate a specific node set (kp-info) for all metrics:

.. code-block:: bash

   python main.py keyplayer kp-info \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n BM,KR \
       -oper all \
       -o /tmp/out/

Compute only the mreach metric with m=3:

.. code-block:: bash

   python main.py keyplayer kp-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 3 \
       -oper mreach \
       -m 3 \
       -a greedy \
       -o /tmp/out/

**Expected output for kp-finder greedy (operation=all, k=2):**

.. code-block:: text

   operation  Key-player    score
   F          ['PH', 'BM']  0.63
   dF         ['HB', 'WD']  0.815
   dR         ['KR', 'HB']  0.683
   mreach     ['HA', 'NP']  25.0

Output files:

- ``report_figure_8_keyplayer_finder_all_greedy.tsv`` — results table
- ``figure_8_keyplayer_finder_all_greedy.svg`` — multi-metric static visualization
- ``figure_8_keyplayer.html`` — interactive network report (D3): a metric
  dropdown auto-highlights that metric's key-player node set with its score
  (one set at a time — Pyntacle's algorithms return a single optimal set per
  metric, not multiple candidates to browse). Also has search, edge toggle,
  and SVG/PNG export. Same size-tiered fallback as the local report. Written
  by both ``kp-finder`` and ``kp-info``.

See :doc:`../../keyPlayers/keyPlayers` for metric definitions and
:doc:`../../outputs` for column documentation.
