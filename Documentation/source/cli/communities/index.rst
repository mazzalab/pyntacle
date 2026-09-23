:orphan:


communities
===========
Detects communities of tightly connected nodes within a graph by means of different modular decomposition algorithms

Specific usage
--------------
.. code-block:: console

   python3 main.py communities fastgreedy -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES}
   python3 main.py communities infomap -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS}
   python3 main.py communities leading-eigenvector -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES}
   python3 main.py communities random_walk -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -steps {STEPS}
   python3 main.py communities percolation -t {fileType} -i {input_file} -k {COMMUNITYSIZE}

Synopsis
--------
.. code-block:: console

   python3 main.py communities <subcommand> [OPTIONS]


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
     - fastgreedy, infomap, leading-eigenvector, random-walk, percolation
     - Select one the subfunctions right after communities
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
   * - ``-nc``, ``--numberCommunities``
     - No
     - \ 
     - \ 
     - \ 
     - ONLY FOR FASTGREEDY Specify the number of clusters around which the modular decomposition algorithm will optimize its module search
   * - ``-n``, ``--minNodes``
     - No
     - \ 
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of vertices equal or greater than this treshold
   * - ``-N``, ``--maxNodes``
     - No
     - \ 
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of vertices equal or lesser than this threshold
   * - ``-c``, ``--minComponents``
     - No
     - \ 
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of components equal or greater than this threshold
   * - ``-C``, ``--maxComponents``
     - No
     - \ 
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of components equal or greater than this threshold
   * - ``-steps``, ``--steps``
     - No
     - int
     - 4
     - \ 
     - ONLY FOR RANDOM-WALK Length of random walks to perform
   * - ``-k``, ``--communitySize``
     - No
     - int
     - 3
     - \ 
     - ONLY FOR PERCOLATION Size of the cliques to be used as building blocks for the community detection
   * - ``-g``, ``--giant``
     - No
     - bool
     - False
     - \ 
     - Considers only the largest component of the input graph and excludes the smaller ones
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

Examples
--------

Detect communities using the fastgreedy algorithm:

.. code-block:: bash

   python main.py communities fastgreedy \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -nc 4 \
       -o /tmp/out/

Run infomap and keep only communities with 3–10 nodes:

.. code-block:: bash

   python main.py communities infomap \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n 3 -N 10 \
       -o /tmp/out/

Run clique percolation (k=3 cliques) on the largest component:

.. code-block:: bash

   python main.py communities percolation \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 3 \
       -g \
       -o /tmp/out/

See :doc:`../../graphUtilities/graphUtilities` for further graph utilities.
