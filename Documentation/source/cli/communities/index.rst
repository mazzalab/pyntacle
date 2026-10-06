:orphan:


communities
===========
Detects communities of tightly connected nodes within a graph by means of different modular decomposition algorithms

Specific usage
--------------
.. code-block:: console

   pyntacle communities fastgreedy -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES}
   pyntacle communities infomap -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS}
   pyntacle communities leading-eigenvector -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES}
   pyntacle communities random-walk -t {fileType} -i {input_file} -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -steps {STEPS}
   pyntacle communities percolation -t {fileType} -i {input_file} -k {COMMUNITYSIZE}

Synopsis
--------
.. code-block:: console

   pyntacle communities <subcommand> [OPTIONS]


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
     - Subcommand to run, right after communities
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
   * - ``-nc``, ``--numberCommunities``
     - No
     - int
     - \ 
     - \ 
     - fastgreedy, leading-eigenvector, random-walk: number of communities (default: the split with the highest modularity)
   * - ``-n``, ``--minNodes``
     - No
     - int
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of vertices equal or greater than this threshold
   * - ``-N``, ``--maxNodes``
     - No
     - int
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of vertices equal or lesser than this threshold
   * - ``-c``, ``--minComponents``
     - No
     - int
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of components equal or greater than this threshold
   * - ``-C``, ``--maxComponents``
     - No
     - int
     - \ 
     - \ 
     - Filters the resulting communities and keeps only those with a number of components equal or lesser than this threshold
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
     - Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same directory as the input file)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - svg, png, pdf, ps, eps
     - Image format of the figure

Output
------

``report_<graph>_communities.tsv`` lists each node with the community it belongs
to, numbered from 1. Clique percolation lets a node sit in several communities:
its ``Community`` cell lists them all and ``Clique`` the cliques that put it
there. With ``-n``, ``-N``, ``-c`` or ``-C`` only the communities that pass the
filters are reported and drawn; they keep their numbers. A run where none passes
stops with an error that lists the community sizes found.

Each community of at most 20 nodes is drawn in ``<graph>_community_<n>.<format>``.

Examples
--------

Detect communities using the fastgreedy algorithm:

.. code-block:: bash

   pyntacle communities fastgreedy \
       -t edgelist \
       -i examples/figure_8.egl \
       -nc 4 \
       -o /tmp/out/

Run infomap and keep only communities with 3–10 nodes:

.. code-block:: bash

   pyntacle communities infomap \
       -t edgelist \
       -i examples/figure_8.egl \
       -n 3 -N 10 \
       -o /tmp/out/

Run clique percolation (k=3 cliques) on the largest component:

.. code-block:: bash

   pyntacle communities percolation \
       -t edgelist \
       -i examples/figure_8.egl \
       -k 3 \
       -g \
       -o /tmp/out/

See :doc:`../../graphUtilities/graphUtilities` for further graph utilities.
