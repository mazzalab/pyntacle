Output File Formats
===================

Every Pyntacle command writes a TSV (tab-separated) report file plus one or more
image files. This page documents every column and section in those reports.

.. contents::
   :local:
   :depth: 2

Common Report Header
---------------------

All TSV reports share a common header block:

.. code-block:: text

   Pyntacle report    <filename>
   Analysis type      <command>

   Network Overview
   Removed nodes      <None | list of node names>
   Number of components   <int>
   Number of Nodes    <int>
   Number of Edges    <int>
   Edge weights       <unweighted | distance | affinity, distance = 1/w | signed, distance = 1/|w| | ...>

``Edge weights`` states how ``-w``, ``--weight-type`` and
``--distance-transform`` read the weights (see :doc:`weights`).

Local Metrics Report
---------------------

**Filename pattern:** ``report_<graph>_local.tsv``

**Command:** ``pyntacle local``

The data section is a tab-separated table with one row per node:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Column
     - Description
   * - ``Node Name``
     - Node identifier (label from the input file)
   * - ``Degree``
     - Number of edges incident to the node
   * - ``Betweenness``
     - Fraction of shortest paths that pass through the node (normalized by igraph's
       convention: divided by (N-1)(N-2)/2 for undirected graphs)
   * - ``Closeness``
     - Reciprocal of the mean shortest-path distance to all other reachable nodes
   * - ``Radiality``
     - ``(diameter + 1) - mean_distance_to_all``.
       Higher values indicate nodes more central to the network periphery.
   * - ``Radiality reach``
     - Same as Radiality but scaled by the fraction of nodes in the same connected
       component. Equals Radiality for connected graphs.
   * - ``Clustering Coefficient``
     - Local clustering coefficient: fraction of node's neighbors that are also
       neighbors of each other (``mode="zero"`` for isolated nodes)
   * - ``Eccentricity``
     - Maximum shortest-path distance from this node to any other node
   * - ``Eigenvector (Scaled)``
     - Eigenvector centrality, normalized so the maximum value equals 1
   * - ``Pagerank``
     - Google PageRank score (stationary distribution of a random walk)

**Example:**

.. code-block:: text

   Node Name  Degree  Betweenness  Closeness  Radiality  Radiality reach  Clustering Coefficient  Eccentricity  Eigenvector (Scaled)  Pagerank
   KR         9       36.417       0.265      6.226      6.226            0.472                   8.0           1.0                  0.056
   BM         6       251.0        0.36       7.226      7.226            0.133                   5.0           0.03                 0.065

Global Metrics Report
----------------------

**Filename pattern:** ``report_<graph>_global.tsv``

**Command:** ``pyntacle global``

The data section is a two-column ``Measure / Score`` table (one metric per row):

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Measure
     - Description
   * - ``Average shortest path length``
     - Mean over all finite node-pair shortest paths
   * - ``Median shortest path length``
     - Median over all finite node-pair shortest paths
   * - ``Diameter``
     - Longest shortest path in the graph
   * - ``Components``
     - Number of connected components
   * - ``Radius``
     - Minimum eccentricity over all nodes
   * - ``Density``
     - Fraction of possible edges that are present
   * - ``pi``
     - Edge count divided by diameter (a compactness proxy)
   * - ``Average clustering coefficient``
     - Mean of all local clustering coefficients (unweighted mean)
   * - ``Weighted clustering coefficient``
     - Global (transitivity) clustering coefficient: 3 × triangles / triads
   * - ``Average degree``
     - Mean degree over all nodes
   * - ``Average Closeness``
     - Mean closeness centrality over all nodes
   * - ``Average Eccentricity``
     - Mean eccentricity over all nodes
   * - ``Average Radiality``
     - Mean radiality over all nodes
   * - ``Average Radiality Reach``
     - Mean radiality-reach over all nodes
   * - ``Completeness Naive``
     - Ratio of present edges to absent edges
   * - ``Completeness``
     - Mazza–Capocefalo completeness score (see :ref:`localMetrics/localMetrics:Global Topology`)
   * - ``Compactness``
     - Mazza compactness score (reciprocal product formulation)

Key-Player Report
------------------

**Filename pattern:** ``report_<graph>_keyplayer_finder_<operation>_<algorithm>.tsv``
(``kp-finder``) or ``report_<graph>_keyplayer_info_<operation>.tsv`` (``kp-info``)

**Command:** ``pyntacle keyplayer kp-finder`` or ``kp-info``

For ``--operation all``, the data section has three columns:

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Column
     - Values
     - Description
   * - ``operation``
     - ``F``, ``dF``, ``dR``, ``mreach``
     - Which KPP metric this row reports
   * - ``Key-player``
     - ``['NodeA', 'NodeB']``
     - The optimal (or best-found) node set of size k
   * - ``score``
     - float in [0, 1] or count
     - Metric score for that node set. F, dF, dR ∈ [0,1]; mreach is a raw count.

**Example (greedy, k=2, operation=all):**

.. code-block:: text

   operation  Key-player    score
   F          ['PH', 'BM']  0.63
   dF         ['HB', 'WD']  0.815
   dR         ['KR', 'HB']  0.683
   mreach     ['HA', 'NP']  25.0

For a single ``--operation``, the ``kp-finder`` table has two columns:
``Key-player`` and the operation name (e.g., ``F``). With ``-a brute_force``,
every set that reaches the optimum is listed, numbered in a ``SetID`` column,
and the report header states how many optimal sets exist.

``kp-info`` scores the node set given with ``-n``. Its table always has the
columns ``Operation``, ``Key-player`` and ``Score``, one row per operation
(four rows with ``-oper all``, one otherwise):

.. code-block:: text

   Operation  Key-player    Score
   F          ['HS', 'BR']  0.0
   dF         ['HS', 'BR']  0.646
   dR         ['HS', 'BR']  0.365
   mreach     ['HS', 'BR']  10.0

Group Centrality Report
------------------------

**Filename pattern:** ``report_<graph>_groupcentrality_finder_<operation>_<algorithm>.tsv``
(``gc-finder``) or ``report_<graph>_groupcentrality_info_<operation>.tsv`` (``gc-info``)

**Command:** ``pyntacle groupcentrality gc-finder`` or ``gc-info``

Same structure as the key-player report but the metric names are:
``degree``, ``closeness``, ``betweenness`` (scored in [0, 1]). The ``gc-info``
table has the columns ``Operation``, ``Node-set`` and ``Score``, one row per
operation.

Mesoscale Report
-----------------

**Filename pattern:** ``report_<graph>_mesoscale.tsv``

**Command:** ``pyntacle mesoscale``

The report contains three concatenated sections:

1. **Topological Importance (k steps)** — an n×n matrix where row i, column j gives
   the averaged k-step effect of node i on node j, plus a summary column ``TI_k``.
2. **Weighted Topological Importance** (if ``-w`` flag was used) — same structure, ``WI_k``.
3. **Topological Overlap Measure (k steps)** — an n×n GTOM similarity matrix.

Percolation Report
------------------

**Filename pattern:** ``report_<graph>_percolation*.tsv``

**Command:** ``pyntacle percolation``

The report has a human-readable summary block followed by a time-series table:

**Summary block fields:**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Field
     - Description
   * - ``Seed node``
     - Starting node label and index
   * - ``P*``
     - Global infectivity used
   * - ``τ_r``
     - Recovery time used
   * - ``Edges: blocked``
     - Edges with threshold above P* (never transmit)
   * - ``Edges: eligible-but-slow``
     - Open edges not used because recovery intervened
   * - ``Edges: usable``
     - Edges that actually transmitted infection
   * - ``Final reached``
     - Number (and %) of nodes ever infected
   * - ``Peak infectious I_max``
     - Maximum number of simultaneously infected nodes and the time step
   * - ``End time``
     - Simulation step at which the last node recovered
   * - ``Infection tree depth``
     - Maximum hop-distance from seed to any infected node

**Time-series table columns:**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Description
   * - ``Time``
     - Simulation step t
   * - ``Infected``
     - Number of currently infectious nodes I(t)
   * - ``Non-Infected``
     - Number of susceptible nodes S(t)
   * - ``Recovered``
     - Number of recovered nodes R(t)

**Example:**

.. code-block:: text

   Time  Infected  Non-Infected  Recovered
   0     1         31            0
   1     2         30            0
   2     3         28            1
   3     4         26            2
   4     4         24            4
   5     2         24            6
   6     0         24            8

Image Outputs
--------------

Every command that produces a graph visualization writes a file named
``<graph>_<command>[_<subcommand>].<format>`` (default: ``.svg``).

- Use ``-f png`` to switch to PNG output.

Three of these commands also write a standalone interactive HTML report,
each self-contained (no external files, D3 loaded from the one JS include
each needs) and each with three size-tiered rendering modes chosen
automatically from node/edge count: a **live** force-simulation view for
small graphs, a **static** (pre-settled, still pan/zoom/search-able) view for
mid-sized graphs, and a **table-only fallback** with a warning banner for
graphs too large to render as a network at all.

- ``local`` writes ``<graph>_local.html``: search, label/edge toggles, a
  node-click popup with that node's computed metrics, a min/max metric range
  filter, and SVG/PNG export of the currently filtered view.
- ``keyplayer`` (both ``kp-finder`` and ``kp-info``) writes
  ``<graph>_keyplayer.html``: a metric dropdown auto-highlights that
  metric's key-player node set with its score. When brute force finds
  several optimal sets, the report says how many and lets you step through
  them. Search, edge-toggle, and SVG/PNG export are also available.
- ``groupcentrality`` (both ``gc-finder`` and ``gc-info``) writes
  ``<graph>_groupcentrality.html``, with the same metric-select-highlight/
  search/edge-toggle/export pattern as the keyplayer report
  (degree/closeness/betweenness instead of the four KPP metrics).
- ``percolation`` writes ``<graph>_percolation.html``: a different kind of
  report (Plotly, not D3) since it visualizes a *time-evolving* process
  rather than a single static/optimal state — an animated network view
  driven by a time slider (play/pause/step/speed) with the S/I/R epidemic
  curve below it, in the same page layout as the other reports: live state
  counts, node search with per-node infection details, display switches
  (cumulative infection edges, other edges, labels), outcome and parameter
  panels, PNG export. See
  :doc:`cli/percolation/index` for the ``-mxs/--maxSteps`` flag that caps
  how many steps the underlying simulation (and therefore the animation)
  runs for.

Set and Extract Reports
------------------------

**Commands:** ``pyntacle set``, ``pyntacle extract``

Both commands write a network back out, in the input format, next to a TSV
report. The report has the common header (computed on the resulting network)
and one row per node of the result:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Description
   * - ``Node``
     - Node name
   * - ``Component``
     - Connected component of the result the node belongs to, 1 being the
       largest; components of equal size are numbered in input order
   * - ``Degree``
     - Number of edges of the node in the result

File names:

- ``set``: ``<first>_<subcommand>_<second>.<ext>`` and
  ``report_<first>_<subcommand>_<second>_set.tsv``;
- ``extract``: ``<input>_extract_<selection>.<ext>`` and
  ``report_<input>_extract_<selection>.tsv``.

``<ext>`` follows the input format: ``.tsv`` (edge list), ``.sif``, ``.dot``
or ``.txt`` (adjacency matrix).
