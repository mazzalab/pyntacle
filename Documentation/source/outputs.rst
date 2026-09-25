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
   Analysisi type     <command>

   Network Overview
   Removed nodes      <None | list of node names>
   Number of components   <int>
   Number of Nodes    <int>
   Number of Edges    <int>

.. note::

   "Analysisi type" is the spelling used in the current output — future versions
   will correct this typo.

Local Metrics Report
---------------------

**Filename pattern:** ``report_<graph>_local.tsv``

**Command:** ``python main.py local``

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

**Command:** ``python main.py global``

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

**Filename pattern:** ``report_<graph>_keyplayer_<subcommand>_<operation>_<algorithm>.tsv``

**Command:** ``python main.py keyplayer kp-finder`` or ``kp-info``

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

For a single ``--operation``, the table has two columns: ``Key-player`` and the
operation name (e.g., ``F``).

For ``kp-info``, the table has ``Key-player``, ``Operation``, and ``Score`` columns.

Group Centrality Report
------------------------

**Filename pattern:** ``report_<graph>_groupcentrality_<subcommand>_<operation>_<algorithm>.tsv``

**Command:** ``python main.py groupcentrality gc-finder`` or ``gc-info``

Same structure as the key-player report but the metric names are:
``degree``, ``betweenness``, ``closeness`` (scored in [0, 1]).

Mesoscale Report
-----------------

**Filename pattern:** ``report_<graph>_mesoscale.tsv``

**Command:** ``python main.py mesoscale``

The report contains three concatenated sections:

1. **Topological Importance (k steps)** — an n×n matrix where row i, column j gives
   the averaged k-step effect of node i on node j, plus a summary column ``TI_k``.
2. **Weighted Topological Importance** (if ``-w`` flag was used) — same structure, ``WI_k``.
3. **Topological Overlap Measure (k steps)** — an n×n GTOM similarity matrix.

Percolation Report
------------------

**Filename pattern:** ``report_<graph>_percolation*.tsv``

**Command:** ``python main.py percolation``

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
  metric's key-player node set with its score — one set at a time, since
  every KPP algorithm returns a single optimal (or best-found) set per
  metric rather than several candidates. No filtering UI. Search,
  edge-toggle, and SVG/PNG export are also available.
- ``groupcentrality`` writes ``<graph>_groupcentrality.html`` **only from**
  ``gc-finder`` — ``gc-info`` writes a TSV report but currently generates no
  HTML view. Same metric-select-highlight/search/edge-toggle/export pattern
  as the keyplayer report (degree/betweenness/closeness instead of the four
  KPP metrics).
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

Set Theory Reports
-------------------

**Command:** ``python main.py set``

The TSV report contains a summary comparison table with the node/edge counts for
each input graph and the result graph (union, intersection, or difference).
The result graph is also written as an adjacency matrix file (``union.tsv``,
``intersection.tsv``, or ``difference.tsv``).
