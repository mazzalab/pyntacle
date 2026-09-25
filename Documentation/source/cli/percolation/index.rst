:orphan:


percolation
===========

Percolation simulates a spreading process on a graph where an edge can transmit only if a global infectivity level exceeds an edge-specific threshold.

Model ingredients:

- **Local edge thresholds** ``p_th,ij``: each edge (i,j) draws a threshold in ``[0, p_thMax]`` using ``--pthDistribution``.
- **Global infectivity / occupation probability** ``P*`` (``--PrInf``): controls how many edges become open. Edge (i,j) transmits only if ``P* >= p_th,ij``.
- **Seed node** (``--nodes``): starting from the seed at t = 0, infection propagates along open edges.
- **Recovery time** ``tau`` (``--tau``): a node can transmit for ``tau`` steps after activation, then becomes recovered (it no longer transmits). ``--tauDistribution`` and/or ``--tauFile`` enable per-node recovery times.

Synopsis
--------
.. code-block:: console

   python3 main.py percolation [OPTIONS]


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
   * - ``-n``, ``--nodes``
     - No
     - \ 
     - \ 
     - \ 
     - ID of the seed node where the process starts. If not provided, a random node in the graph is chosen.
   * - ``-P``, ``--PrInf``
     - No
     - float
     - 0.5
     - \ 
     - Global infectivity / Occupation probability (0–1). Higher P* → easier spreading / percolation. Defautl value is 0.5.
   * - ``-tau``, ``--tau``
     - No
     - float
     - 1.5
     - \ 
     - Recovery time τ (in simulation steps). A node can transmit for τ steps after activation, then becomes recovered. Must be > 0. Default: 4.
   * - ``-tauDist``, ``--tauDistribution``
     - No
     - str
     - fixed
     - fixed, uniform, normal, bimodal
     - Distribution used for recovery times τ. "fixed": single global τ for all nodes (default). "uniform"/"normal"/"bimodal": interpret -tau as τ_max and draw per-node τ_i in (0, τ_max] from the chosen distribution.
   * - ``-tauFile``, ``--tauFile``
     - No
     - \ 
     - \ 
     - \ 
     - TSV file with fixed per-node recovery times. Must contain two columns: "Nodes" and "Recovery_time". Node labels in "Nodes" must match. When provided, these τ_i values override -tau and -tauDist.
   * - ``-pth``, ``--pthMax``
     - No
     - int
     - 1
     - \ 
     - Maximum local threshold p_th in [0,1]. Each edge (i,j) gets a local threshold p_th,ij drawn in [0, p_thMax]; the edge can transmit only if P* >= p_th,ij. Default: 1.0.
   * - ``-dist``, ``--pthDistribution``
     - No
     - str
     - uniform
     - uniform, normal, bimodal
     - Distribution used to sample local thresholds p_th,ij in [0, p_thMax]. "uniform": all values equally likely; "normal": thresholds cluster around a central value; "bimodal": two groups of edges with low and high thresholds. Default: uniform.
   * - ``-mxs``, ``--maxSteps``
     - No
     - int
     - \
     - \
     - Maximum number of simulation steps. Default: number of nodes in the graph.
   * - ``--snapshotInfected``
     - No
     - int
     - \ 
     - \ 
     - If set, take a snapshot when the number of *currently infected* nodes reaches this value. The TSV report will include node states at that time.
   * - ``--snapshotNode``
     - No
     - str
     - \ 
     - \ 
     - If set, take a snapshot at the time when this node becomes infected. Can be a node label or a node index (0-based).
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

Run percolation starting from node SR with default parameters:

.. code-block:: bash

   python main.py percolation \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n SR \
       -o /tmp/out/

Run with high infectivity (P*=0.9) and fixed recovery time of 3 steps:

.. code-block:: bash

   python main.py percolation \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n SR \
       -P 0.9 \
       -tau 3 \
       -tauDist fixed \
       -o /tmp/out/

Run with bimodal edge threshold distribution (easy/hard edges):

.. code-block:: bash

   python main.py percolation \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n SR \
       -P 0.6 \
       -dist bimodal \
       -pth 0.8 \
       -o /tmp/out/

Take a snapshot when 5 nodes are simultaneously infected:

.. code-block:: bash

   python main.py percolation \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n SR \
       -P 0.7 \
       --snapshotInfected 5 \
       -o /tmp/out/

**Example TSV output (time-series section):**

.. code-block:: text

   Time  Infected  Non-Infected  Recovered
   0     1         31            0
   1     2         30            0
   2     3         28            1
   3     4         26            2
   4     4         24            4
   5     2         24            6
   6     0         24            8

Cap a long-running simulation at 20 steps:

.. code-block:: bash

   python main.py percolation \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n SR \
       -mxs 20 \
       -o /tmp/out/

Output files:

- ``report_<graph>_percolation*.tsv`` — summary block + time-series table
- ``<graph>_percolation.html`` — interactive report: the network animation
  (time slider with play/pause/step/speed, nodes coloured susceptible /
  infected / recovered, infection edges shown per step or cumulatively) with
  the epidemic curve (S, I and R counts over time) below it, whose marker
  follows the slider and which jumps the animation to the clicked time. The
  sidebar shows the counts at the current time, a node search (state, degree,
  infection and recovery times, infecting neighbour), display switches, the
  outcome (nodes ever infected, peak, duration) and the run parameters. Both
  plots export to PNG.

See :doc:`../../percolation/percolation` for the full mathematical model and
:doc:`../../outputs` for complete report documentation.
