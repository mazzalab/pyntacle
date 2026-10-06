:orphan:


groupcentrality
===============

Specific usage
--------------
.. code-block:: console

   pyntacle groupcentrality gc-info -t {fileType} -i {input_file} -n {node-list}
   pyntacle groupcentrality gc-finder -t {fileType} -i {input_file} -k {k-size}

Subcommand summary
------------------

gc-info
  Compute all or a selected group-centrality metric for a selected set of nodes

gc-finder
  Find the optimal or the best set of size 'k' for a given group-centrality index

Search algorithms
-----------------

``gc-finder`` looks for the set of ``-k`` nodes with the best score in one of three ways (``-a``):

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
  ``-ms`` seconds.

Synopsis
--------
.. code-block:: console

   pyntacle groupcentrality <subcommand> [OPTIONS]


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
     - str
     - \ 
     - gc-info, gc-finder
     - Subcommand to run, right after groupcentrality
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
     - Select the node/nodes to be removed from the graph (Comma separated)
   * - ``-n``, ``--nodes``
     - No
     - \ 
     - \ 
     - \ 
     - Nodes to select ONLY IN GC-INFO (Comma separated)
   * - ``-k``, ``--k_size``
     - No
     - int
     - 2
     - \ 
     - Size of the node set to search, gc-finder only (default=2)
   * - ``-v``, ``--value``
     - No
     - str
     - min
     - min, max, mean
     - Value to select when all operation are performed or only "closeness" (default="min")
   * - ``-oper``, ``--operation``
     - No
     - str
     - all
     - all, degree, closeness, betweenness
     - Possible metrics to be used (default="all")
   * - ``-a``, ``--algorithm``
     - No
     - str
     - brute_force
     - brute_force, greedy, gradient_descent
     - Search algorithm of gc-finder (default=brute_force)
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

Find the best 2-node group for all centrality metrics (greedy):

.. code-block:: bash

   pyntacle groupcentrality gc-finder \
       -t edgelist \
       -i examples/figure_8.egl \
       -k 2 \
       -oper all \
       -a greedy \
       -o /tmp/out/

Evaluate group centrality for a specific node set:

.. code-block:: bash

   pyntacle groupcentrality gc-info \
       -t edgelist \
       -i examples/figure_8.egl \
       -n KR,BS3 \
       -oper all \
       -o /tmp/out/

Find best 3-node group for betweenness using brute-force:

.. code-block:: bash

   pyntacle groupcentrality gc-finder \
       -t edgelist \
       -i examples/figure_8.egl \
       -k 3 \
       -oper betweenness \
       -a brute_force \
       -np 4 \
       -o /tmp/out/

Output files:

- ``report_<graph>_groupcentrality_finder_<operation>_<algorithm>.tsv``
  (``gc-finder``) or ``report_<graph>_groupcentrality_info_<operation>.tsv``
  (``gc-info``) — results table
- ``<graph>_groupcentrality_finder_<operation>_<algorithm>.<format>`` or
  ``<graph>_groupcentrality_info_<operation>.<format>`` — the network with the
  found set (``gc-finder``) or the given set (``gc-info``) highlighted. With
  ``-oper all`` each metric's set has its own colour, and a node in several
  sets is drawn as nested discs. With ties only the first optimal set is drawn.
- ``<graph>_groupcentrality.html`` — interactive network report (D3), same
  metric-highlight/search/edge-toggle/SVG+PNG-export pattern as the
  keyplayer report. Written by both ``gc-finder`` and ``gc-info``.

``gc-info`` needs the node set (``-n``) and stops with an error if it is
missing or names nodes that are not in the network.

See :doc:`../../groupCentrality/groupCentrality` for metric definitions and
:doc:`../../outputs` for report documentation.
