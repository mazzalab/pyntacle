:orphan:


generate
========

Generate writes a synthetic undirected, unweighted network drawn from a
random or regular model.

Specific usage:

.. code-block:: console

   pyntacle generate erdos-renyi    -t {fileType} -n NODES (-e EDGES | -p PROBABILITY) [-l]
   pyntacle generate tree           -t {fileType} -n NODES -c CHILDREN
   pyntacle generate barabasi       -t {fileType} -n NODES -a EDGES_PER_NEW_NODE [-i IMPLEMENTATION]
   pyntacle generate watts-strogatz -t {fileType} -s SIZE -nei NEI -p PROBABILITY [-dim DIMENSIONS] [-l] [-m]
   pyntacle generate lattice        -t {fileType} -dim SIZE_PER_DIMENSION [-nei NEI] [-circ]

Models (igraph generators):

erdos-renyi
  ``-n`` nodes joined by exactly ``-e`` random edges, or by each possible edge
  with probability ``-p``.

tree
  A tree of ``-n`` nodes where every node has ``-c`` children.

barabasi
  Preferential attachment: nodes are added one at a time, each bringing ``-a``
  edges towards nodes in proportion to their degree.

watts-strogatz
  A ring (or, with ``-dim``, a lattice) of ``-s`` nodes per dimension, each
  joined to the nodes up to ``-nei`` steps away, with every edge rewired with
  probability ``-p``.

lattice
  A regular lattice with the given number of nodes along each dimension
  (``-dim 4,4`` is a 4×4 grid); ``-circ`` joins opposite borders.

Output
------

One file in the output directory (``-o``, or the current directory), named
after the model and the size of the network it produced:
``<model>_n<nodes>_e<edges>.<ext>``, for example ``erdos_renyi_n50_e100.tsv``.
A missing parameter stops the command with an error naming it.

Synopsis
--------
.. code-block:: console

   pyntacle generate <subcommand> [OPTIONS]


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
     - Subcommand to run, right after generate
   * - ``-t``, ``--fileType``
     - Yes
     - str
     - \ 
     - matrix, edgelist, sif, dot
     - Format of the network file to write
   * - ``-n``, ``--numberNodes``
     - No
     - int
     - \ 
     - \ 
     - erdos-renyi, tree, barabasi: number of nodes
   * - ``-e``, ``--numberEdges``
     - No
     - int
     - \ 
     - \ 
     - erdos-renyi: number of edges (or give -p)
   * - ``-p``, ``--probability``
     - No
     - check_prob
     - \ 
     - \ 
     - erdos-renyi: probability of an edge between any two nodes (or give -e); watts-strogatz: probability of rewiring each edge
   * - ``-l``, ``--loops``
     - No
     - bool
     - False
     - \ 
     - erdos-renyi, watts-strogatz: allow self-loops
   * - ``-c``, ``--children``
     - No
     - int
     - \ 
     - \ 
     - tree: children of each node
   * - ``-a``, ``--averageEdge``
     - No
     - int
     - \ 
     - \ 
     - barabasi: edges each new node brings to the network
   * - ``-i``, ``--implementation``
     - No
     - str
     - psumtree
     - bag, psumtree, psumtree_multiple
     - barabasi: igraph implementation of preferential attachment (default psumtree)
   * - ``-s``, ``--size``
     - No
     - int
     - \ 
     - \ 
     - watts-strogatz: nodes along each dimension of the starting lattice
   * - ``-m``, ``--multiple``
     - No
     - bool
     - False
     - \ 
     - watts-strogatz: allow parallel edges after rewiring
   * - ``-dim``, ``--dimension``
     - No
     - int list
     - \ 
     - \ 
     - watts-strogatz: dimensions of the starting lattice (default 1, a ring); lattice: nodes along each dimension, comma-separated (ex. 4,4)
   * - ``-nei``, ``--nei``
     - No
     - int
     - \ 
     - \ 
     - watts-strogatz, lattice: nodes up to this many steps apart are connected (lattice default 1)
   * - ``-circ``, ``--circular``
     - No
     - bool
     - False
     - \ 
     - lattice: join the opposite borders (periodic lattice)
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Where to write the network (default: the current working directory)

Examples
--------

An Erdős–Rényi network with 50 nodes and 100 edges:

.. code-block:: bash

   pyntacle generate erdos-renyi \
       -t edgelist \
       -n 50 \
       -e 100 \
       -o /tmp/out/

A Barabási–Albert network with 100 nodes, each new node bringing 3 edges
(mean degree about 6):

.. code-block:: bash

   pyntacle generate barabasi \
       -t edgelist \
       -n 100 \
       -a 3 \
       -o /tmp/out/

A small-world network: a ring of 200 nodes, each joined to the 4 nearest
(``-nei 2``), with 10% of the edges rewired:

.. code-block:: bash

   pyntacle generate watts-strogatz \
       -t edgelist \
       -s 200 \
       -nei 2 \
       -p 0.1 \
       -o /tmp/out/

A 5×5 grid:

.. code-block:: bash

   pyntacle generate lattice \
       -t edgelist \
       -dim 5,5 \
       -o /tmp/out/
