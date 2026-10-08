:orphan:


keyplayer
=========

Specific usage
--------------
.. code-block:: console

   pyntacle keyplayer kp-info -t {fileType} -i {input_file} -n {node-list}
   pyntacle keyplayer kp-finder -t {fileType} -i {input_file} -k {k-size}

Subcommand summary
------------------

kp-info
  Compute individual key-player metrics for a selected set of nodes

kp-finder
  Find the best kp-set of size k

Search algorithms
-----------------

``kp-finder`` looks for the set of ``-k`` nodes with the best score in one of three ways (``-a``):

``brute_force`` (default)
  Scores every set of ``-k`` nodes, so the result is the optimum. Sets tied
  at the optimum are all counted and listed in the report (up to
  ``--max-ties``). The work grows with the number of sets, n choose k.

``greedy``
  Starts from a random set and keeps making the swap of one member with one
  non-member that raises the score most, until no swap raises it. The result
  is a local optimum; ``--seed`` fixes the starting set.

``gradient_descent``
  Starts from a random set and tries random swaps, moving to any that raises
  the score (and, with ``-p``, to one that lowers it with that probability).
  It stops at the first swap that raises the score by no more than ``-tol``,
  when every swap of the current set has been tried without a move, or after
  ``-ms`` seconds. Sets are scored by the engine chosen with ``--engine``.

Synopsis
--------
.. code-block:: console

   pyntacle keyplayer <subcommand> [OPTIONS]


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
     - Subcommand to run, right after keyplayer
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
     - Column separator of the input file (ex. ','); detected automatically if omitted
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
     - Size of the node set to search, kp-finder only (default=2)
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
     - Search algorithm of kp-finder (default=brute_force)
   * - ``-p``, ``--probability``
     - No
     - float
     - 0
     - \ 
     - gradient_descent only: probability of accepting a swap that lowers the score (default=0)
   * - ``-tol``, ``--tolerance``
     - No
     - float
     - 0.01
     - \ 
     - gradient_descent only: the search stops at the first swap that raises the score by no more than this (default=0.01)
   * - ``-ms``, ``--maxsec``
     - No
     - int
     - 120
     - \ 
     - gradient_descent only: time limit of each search, in seconds (default=120)
   * - ``-np``, ``--nprocs``
     - No
     - int
     - 1
     - \ 
     - Threads of the compiled kernels (default=1)
   * - ``--max-ties``
     - No
     - int
     - 100
     - \ 
     - Maximum number of equally-scoring node sets listed by the brute-force report. The reported count of optimal sets is exact even when the list is capped; ``greedy`` and ``gradient_descent`` ignore it
   * - ``--engine``
     - No
     - str
     - cython
     - cython, python
     - Metric engine: the compiled kernels (default) or the pure-Python reference implementation. The python engine is single-threaded and ignores -np, and it does not implement brute_force
   * - ``--seed``
     - No
     - int
     - \ 
     - \ 
     - Random seed for greedy / gradient_descent, so a run can be reproduced
   * - ``--no-plot``
     - No
     - bool
     - False
     - \ 
     - Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - svg, png, pdf, ps, eps
     - Image format of the figure
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same directory as the input file)

Examples
--------

Find the best 2-node key-player set using the greedy algorithm (all 4 metrics):

.. code-block:: bash

   pyntacle keyplayer kp-finder \
       -t edgelist \
       -i examples/figure_8.egl \
       -k 2 \
       -oper all \
       -a greedy \
       -m 2 \
       --seed 1 \
       -o /tmp/out/

Find the optimal set using exhaustive brute-force with 4 threads:

.. code-block:: bash

   pyntacle keyplayer kp-finder \
       -t edgelist \
       -i examples/figure_8.egl \
       -k 2 \
       -oper all \
       -a brute_force \
       -m 2 \
       -np 4 \
       -o /tmp/out/

Evaluate a specific node set (kp-info) for all metrics:

.. code-block:: bash

   pyntacle keyplayer kp-info \
       -t edgelist \
       -i examples/figure_8.egl \
       -n BM,KR \
       -oper all \
       -o /tmp/out/

Compute only the mreach metric with m=3:

.. code-block:: bash

   pyntacle keyplayer kp-finder \
       -t edgelist \
       -i examples/figure_8.egl \
       -k 3 \
       -oper mreach \
       -m 3 \
       -a greedy \
       -o /tmp/out/

**Expected output for the first example (kp-finder greedy, operation=all, k=2, --seed 1):**

.. code-block:: text

   Operation Key-player  Score
           F   [HA, HB]  0.706
          dF   [HB, WD]  0.815
          dR   [KR, HB]  0.641
      mreach   [WD, SR]     23

Greedy reaches a local optimum from a random starting set; ``--seed`` fixes
that set, so the same seed gives the same result.

Output files:

- ``report_figure_8_keyplayer_finder_all_greedy.tsv`` — results table
- ``figure_8_keyplayer_finder_all_greedy.svg`` — the network with each metric's set in its own colour; a node in several sets is drawn as nested discs. With ties only the first optimal set is drawn
- ``figure_8_keyplayer.html`` — interactive network report (D3): a metric
  dropdown auto-highlights that metric's key-player node set with its score;
  when brute force finds several optimal sets, the report says how many and
  lets you choose among them. Also has search, edge toggle, and SVG/PNG
  export. Same size-tiered fallback as the local report. Written by both
  ``kp-finder`` and ``kp-info``.

``kp-info`` needs the node set (``-n``) and stops with an error if it is
missing, names nodes that are not in the network, or leaves fewer than 2 nodes
outside it; a node named twice counts once. For the same reason ``-k`` of
``kp-finder`` is at most the number of nodes minus 2.

See :doc:`../../keyPlayers/keyPlayers` for metric definitions and
:doc:`../../outputs` for column documentation.
