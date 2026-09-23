:orphan:


generate
========

Generate creates synthetic graphs using common random graph models.

Specific usage:

.. code-block:: console

   python3 main.py generate erdos-renyi [OPTIONS]
   python3 main.py generate tree [OPTIONS]
   python3 main.py generate barabasi [OPTIONS]
   python3 main.py generate watts-strogatz [OPTIONS]
   python3 main.py generate lattice [OPTIONS]

Synopsis
--------
.. code-block:: console

   python3 main.py generate <subcommand> [OPTIONS]


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
     - erdos-renyi, tree, barabasi, watts-strogatz, lattice
     - Select one the subfunctions right after generate
   * - ``-t``, ``--fileType``
     - Yes
     - str
     - \ 
     - matrix, edgelist, sif, dot
     - File type
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
   * - ``-n``, ``--numberNodes``
     - No
     - bool
     - False
     - \ 
     - Number of vertices of the resulting random graph
   * - ``-e``, ``--numberEdges``
     - No
     - bool
     - False
     - \ 
     - The resulting number of edges
   * - ``-p``, ``--probability``
     - No
     - check_prob
     - False
     - \ 
     - The wiring probability to connect any two nodes.
   * - ``-l``, ``--loops``
     - No
     - bool
     - False
     - \ 
     - Flag to determine wheter the graph should contain loops
   * - ``-c``, ``--children``
     - No
     - bool
     - False
     - \ 
     - The number of children nodes per parent
   * - ``-a``, ``--averageEdge``
     - No
     - bool
     - False
     - \ 
     - Average number of node neighbours for each vertex in the scale-free network.
   * - ``-i``, ``--implementation``
     - No
     - str
     - psumtree
     - bag, psumtree, psumtree_multiple
     - implementation to use in the Barabasi algorithm
   * - ``-s``, ``--size``
     - No
     - bool
     - False
     - \ 
     - The dimension of a starting lattice (for lattice is a list with the dimensions of the lattice)
   * - ``-m``, ``--multiple``
     - No
     - bool
     - False
     - \ 
     - Flag to determine wheter multiple edges are allowed
   * - ``-dim``, ``--dimension``
     - No
     - bool
     - False
     - \ 
     - The dimension of the lattice which the Watts-Strogatz model will be applied to generate the small-world
   * - ``-nei``, ``--nei``
     - No
     - bool
     - False
     - \ 
     - The distance between any two nodes over which these will not be considered connected
   * - ``-mut``, ``--mutual``
     - No
     - bool
     - False
     - \ 
     - Flag to determine wheter to create all connections as mutual in case of a directed graph.
   * - ``-circ``, ``--circular``
     - No
     - bool
     - False
     - \ 
     - Flag to determine wheter the generated lattice is periodic
   * - ``-o``, ``--outdir``
     - No
     - str
     - False
     - \ 
     - Select where to store the output (if not specified the output will be stored to the current working directory)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output
