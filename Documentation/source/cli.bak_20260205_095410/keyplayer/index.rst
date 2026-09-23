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
     - Use this flag if your graph is weighted
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
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output (svg, png)
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
