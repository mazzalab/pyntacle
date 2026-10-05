:orphan:


set
===

Specific usage
--------------
.. code-block:: console

   pyntacle set union -t {fileType} -i {input_file} -i2 {input_file2}
   pyntacle set intersection -t {fileType} -i {input_file} -i2 {input_file2}
   pyntacle set difference -t {fileType} -i {input_file} -i2 {input_file2}

Subcommand summary
------------------

Both networks are matched by node name. ``-t``, ``-s``, ``-nh`` and ``-w``
apply to both files, so they must share format, separator and header (use
:doc:`../convert/index` first if they do not).

union
  Every node and every edge of the two networks.

intersection
  The edges present in both networks, and the nodes they touch.

difference
  The edges of the first network that the second lacks, and the nodes they
  touch. The operation is not symmetric: swap ``-i`` and ``-i2`` for the other
  direction.

With ``-w`` an edge keeps the weight it has in the first network, or in the
second for an edge only the second has. Every component of the result is
kept. A result with no edges stops the command with an error.

Output
------

In the output directory (``-o``, or the folder of the first input file):

- ``<first>_<subcommand>_<second>.<ext>`` — the resulting network, in the
  input format (``.tsv`` edge list, ``.sif``, ``.dot``, ``.txt`` matrix);
- ``report_<first>_<subcommand>_<second>_set.tsv`` — one row per node with its
  component (1 = the largest) and degree;
- a figure of the result, unless ``--no-plot`` is given.

Synopsis
--------
.. code-block:: console

   pyntacle set <subcommand> [OPTIONS]


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
     - union, intersection, difference
     - Subcommand to run, right after set
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
     - Use this flag if your graph is weighted
   * - ``-r``, ``--remove``
     - No
     - \ 
     - \ 
     - \ 
     - Select the node/nodes to be removed from the graph (ex. A,B,C)
   * - ``-i2``, ``--inputFile2``
     - Yes
     - str
     - \ 
     - \ 
     - Second network, in the same format as the first: -t, -s, -nh and -w apply to both (use 'convert' if they differ)
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
     - \ 
     - Specify the format of the image output (svg, png)
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same directory as the input file)

Examples
--------

Compute the union of two networks:

.. code-block:: bash

   pyntacle set union \
       -t edgelist \
       -i network1.egl \
       -i2 network2.egl \
       -o /tmp/out/

Find the intersection (shared nodes and edges):

.. code-block:: bash

   pyntacle set intersection \
       -t edgelist \
       -i network1.egl \
       -i2 network2.egl \
       -o /tmp/out/

Compute the difference (edges in network1 not in network2):

.. code-block:: bash

   pyntacle set difference \
       -t edgelist \
       -i network1.egl \
       -i2 network2.egl \
       -o /tmp/out/
