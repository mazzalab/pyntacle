:orphan:


local
=====
Measures to be calculated: Degree, Betweenness, Closeness, Radiality, Radiality reach, Clustering Coefficient, Eccentricity, Eigenvector (Scaled), Pagerank

Synopsis
--------
.. code-block:: console

   pyntacle local [OPTIONS]


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
     - Select the node/nodes to be removed from the graph (Comma separated)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - svg, png, pdf, ps, eps
     - Image format of the figure
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
     - Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same directory as the input file)

Examples
--------

Compute local metrics for all nodes in an edge-list file:

.. code-block:: bash

   pyntacle local \
       -t edgelist \
       -i examples/figure_8.egl \
       -o /tmp/out/

Highlight specific nodes (shown in green in the output figure):

.. code-block:: bash

   pyntacle local \
       -t edgelist \
       -i examples/figure_8.egl \
       -c KR,BM \
       -o /tmp/out/

Compute metrics on a directed, weighted adjacency matrix, excluding node LR:

.. code-block:: bash

   pyntacle local \
       -t matrix \
       -i network.txt \
       -d -w \
       -r LR \
       -o /tmp/out/

**Expected output** for ``pyntacle local -t edgelist -i examples/figure_8.egl -o /tmp/out/`` (table cut here):

.. code-block:: text

   pyntacle local
   Input: examples/figure_8.egl
   Output directory: /tmp/out
   Network: 32 nodes, 56 edges, 1 component(s)

   Node Name  Degree  Betweenness  Closeness  Radiality  ...
          HS       2        0.000      0.212      5.290  ...
          PS       6       18.500      0.258      6.129  ...
   ...
   ... 12 more rows in the report

   Report: /tmp/out/report_figure_8_local.tsv
   HTML report: /tmp/out/figure_8_local.html
   Figure: /tmp/out/figure_8_local.svg
   Done!

The screen shows at most 20 rows; the report holds every node.

Output files written to ``/tmp/out/``:

- ``report_figure_8_local.tsv`` — per-node metric table
- ``figure_8_local.svg`` — static network visualization
- ``figure_8_local.html`` — interactive network report (D3): search, label
  and edge toggles, node-click popup showing that node's metrics, a min/max
  metric range filter, and SVG/PNG export of the current (filtered) view.
  Graphs above ~3000 nodes / 8000 edges automatically fall back to a
  sortable, free-text-filterable table instead of the network view.

See :doc:`../../outputs` for column definitions.
