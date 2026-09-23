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
