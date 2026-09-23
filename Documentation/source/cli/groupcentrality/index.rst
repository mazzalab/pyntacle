:orphan:


groupcentrality
===============

Specific usage
--------------
.. code-block:: console

   python3 main.py groupcentrality gc-info -t {fileType} -i {input_file} -n {node-list}
   python3 main.py groupcentrality gc-finder -t {fileType} -i {input_file} -k {k-size}

Subcommand summary
------------------

gc-info
  Compute all or a selected group-centrality metric for a selected set of nodes

gc-finder
  Find the optimal or the best set of size 'k' for a given group-centrality index

Synopsis
--------
.. code-block:: console

   python3 main.py groupcentrality <subcommand> [OPTIONS]


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
     - Select one the subcuntions right after groupcentrality
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
     - Use this flag if your graph is weighted
   * - ``-r``, ``--remove``
     - No
     - \ 
     - \ 
     - \ 
     - Select the node/nodes to be romev from the graph (Comma separated)
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
     - Number of nodes ONLY IN GC-FINDER (default=2)
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
     - Select the algorithm to use when using the GC-FINDER command (default=brute_force)
   * - ``-p``, ``--probability``
     - No
     - float
     - 0
     - \ 
     - The probability of accepting a swap of nodes (values between 0 and 1) - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0)
   * - ``-tol``, ``--tolerance``
     - No
     - float
     - 0.01
     - \ 
     - The minimum accepted increase by a two-nodes swap - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0.01)
   * - ``-ms``, ``--maxsec``
     - No
     - int
     - 120
     - \ 
     - Maximum allowed computation time (seconds) - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=120)
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

Examples
--------

Find the best 2-node group for all centrality metrics (greedy):

.. code-block:: bash

   python main.py groupcentrality gc-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 2 \
       -oper all \
       -a greedy \
       -o /tmp/out/

Evaluate group centrality for a specific node set:

.. code-block:: bash

   python main.py groupcentrality gc-info \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n KR,BS3 \
       -oper all \
       -o /tmp/out/

Find best 3-node group for betweenness using brute-force:

.. code-block:: bash

   python main.py groupcentrality gc-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 3 \
       -oper betweenness \
       -a brute_force \
       -np 4 \
       -o /tmp/out/

Output files:

- ``report_<graph>_groupcentrality_<subcommand>_<operation>_<algorithm>.tsv`` — results table
- ``<graph>_groupcentrality.html`` — interactive network report (D3), same
  metric-highlight/search/edge-toggle/SVG+PNG-export pattern as the
  keyplayer report. **Only produced by** ``gc-finder`` — ``gc-info`` writes
  its TSV report but does not generate an HTML view.

See :doc:`../../groupCentrality/groupCentrality` for metric definitions and
:doc:`../../outputs` for report documentation.
