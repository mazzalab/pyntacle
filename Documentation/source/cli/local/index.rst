:orphan:


local
=====
Measures to be calculated: Degree, Betweenness, Closeness, Radiality, Radiality reach, Clustering Coefficient, Eccentricity, Eigenvector (Scaled), Pagerank

Synopsis
--------
.. code-block:: console

   python3 main.py local [OPTIONS]


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
     - Select the node/nodes to be removed from the graph (Comma separated)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output (svg, png)
   * - ``-c``, ``--color``
     - No
     - bool
     - False
     - \ 
     - Specify the nodes you want to highlight
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

Compute local metrics for all nodes in an edge-list file:

.. code-block:: bash

   python main.py local \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -o /tmp/out/

Highlight specific nodes (shown in green in the output figure):

.. code-block:: bash

   python main.py local \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -c KR,BM \
       -o /tmp/out/

Compute metrics on a directed, weighted adjacency matrix, excluding node LR:

.. code-block:: bash

   python main.py local \
       -t matrix \
       -i network.txt \
       -d -w \
       -r LR \
       -o /tmp/out/

**Expected output (partial):**

.. code-block:: text

   Working on: ../dev/test/input/figure_8.egl

   No nodes removed

   Number of nodes: 32
   Number of edges: 56
   Number of components: 1
   Function : local

   Done!

Output files written to ``/tmp/out/``:

- ``report_figure_8_local.tsv`` — per-node metric table
- ``figure_8_local.svg`` — static network visualization
- ``figure_8_local.html`` — interactive network report (D3): search, label
  and edge toggles, node-click popup showing that node's metrics, a min/max
  metric range filter, and SVG/PNG export of the current (filtered) view.
  Graphs above ~3000 nodes / 8000 edges automatically fall back to a
  sortable, free-text-filterable table instead of the network view.

See :doc:`../../outputs` for column definitions.
