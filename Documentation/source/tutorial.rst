Tutorial: Analyzing the Figure 8 Network
==========================================

This tutorial walks through a complete analysis of the **Figure 8 benchmark network**,
a 32-node protein-interaction network included in the Pyntacle repository.
It covers: local metrics, key-player identification (brute-force and greedy),
and group centrality.

The input file is ``dev/test/input/figure_8.egl`` — a tab-separated edge list with
a header row (``Node1``, ``Node2``).

.. contents::
   :local:
   :depth: 2

Setup
-----

Activate the environment and move to the source directory:

.. code-block:: bash

   conda activate graphtacle_debug
   cd /path/to/pyntacle_final/pyntacle

The Figure 8 network has 32 nodes and 56 edges. It represents a subset of a
protein–protein interaction network used to benchmark network topology tools.

Step 1 — Local Metrics
-----------------------

Compute per-node topology metrics (degree, betweenness, closeness, radiality,
clustering coefficient, eccentricity, eigenvector centrality, PageRank):

.. code-block:: bash

   python main.py local \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -o /tmp/fig8_out/

**Output files:**

- ``/tmp/fig8_out/report_figure_8_local.tsv`` — tab-separated metric table
- ``/tmp/fig8_out/figure_8_local.svg`` — static network plot
- ``/tmp/fig8_out/figure_8_local.html`` — interactive Plotly visualization

**Example output** (first 5 rows of the TSV report):

.. code-block:: text

   Pyntacle report   report_figure_8_local.tsv
   Analysisi type    local

   Network Overview
   Removed nodes     None
   Number of components   1
   Number of Nodes   32
   Number of Edges   56

   Node Name  Degree  Betweenness  Closeness  Radiality  Radiality reach  Clustering Coefficient  Eccentricity  Eigenvector (Scaled)  Pagerank
   HS         2       0.0          0.212      5.29       5.29             1.0                     9.0           0.296                0.015
   BR         4       0.0          0.254      6.065      6.065            1.0                     8.0           0.623                0.026
   WD         7       210.75       0.313      6.806      6.806            0.571                   7.0           0.845                0.046
   KR         9       36.417       0.265      6.226      6.226            0.472                   8.0           1.0                  0.056
   BM         6       251.0        0.36       7.226      7.226            0.133                   5.0           0.03                 0.065

For column definitions see :doc:`outputs`.

**Visualization:**

.. figure:: _static/figure_8_local.svg
   :width: 80%
   :align: center
   :alt: Figure 8 local metrics visualization

   Figure 8 network. Node size proportional to degree. Red = all nodes.

Highlight specific nodes (e.g., ``KR`` and ``BM``) in the visualization:

.. code-block:: bash

   python main.py local \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -c KR,BM \
       -o /tmp/fig8_out/

Step 2 — Key-Player Identification (Greedy)
--------------------------------------------

Find the 2-node set that maximizes each KPP metric using the greedy algorithm:

.. code-block:: bash

   python main.py keyplayer kp-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 2 \
       -oper all \
       -a greedy \
       -m 2 \
       -o /tmp/fig8_out/

**Output files:**

- ``/tmp/fig8_out/report_figure_8_keyplayer_finder_all_greedy.tsv``
- ``/tmp/fig8_out/figure_8_keyplayer_finder_all_greedy.svg``
- ``/tmp/fig8_out/figure_8_keyplayer.html``

**Example TSV output:**

.. code-block:: text

   operation  Key-player    score
   F          ['PH', 'BM']  0.63
   dF         ['HB', 'WD']  0.815
   dR         ['KR', 'HB']  0.683
   mreach     ['HA', 'NP']  25.0

Interpretation:

- **F** = Fragmentation: removing ``PH`` and ``BM`` leaves 63% of node pairs disconnected
- **dF** = Distance-fragmentation: ``HB`` and ``WD`` maximize distance-weighted disruption
- **dR** = Distance-weighted reach: ``KR`` and ``HB`` are optimally positioned to reach the graph
- **mreach** = m-reach (m=2): ``HA`` and ``NP`` can reach 25 nodes within 2 hops

**Visualization:**

.. figure:: _static/figure_8_keyplayer_finder_all_greedy.svg
   :width: 80%
   :align: center
   :alt: Key-player greedy result

   Key-players identified by the greedy algorithm. Colors: yellow=F, green=dF, blue=dR, red=mreach.
   Node size scales with how many metrics name that node as a key player.

Step 3 — Key-Player Identification (Brute Force)
-------------------------------------------------

For small graphs, brute force guarantees the optimal solution. This exhaustively
tests all C(32, 2) = 496 node pairs:

.. code-block:: bash

   python main.py keyplayer kp-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 2 \
       -oper all \
       -a brute_force \
       -m 2 \
       -np 4 \
       -o /tmp/fig8_out/

.. note::

   Use ``-np`` to enable multi-threaded computation. For graphs with >50 nodes,
   prefer the ``greedy`` or ``gradient_descent`` algorithms for performance.

**Visualization:**

.. figure:: _static/figure_8_keyplayer_finder_all_brute_force.svg
   :width: 80%
   :align: center
   :alt: Key-player brute-force result

   Key-players identified by exhaustive search. Same color scheme as above.

Step 4 — Key-Player Info (Evaluate a Specific Set)
----------------------------------------------------

Check the KPP scores for a manually chosen node set (e.g., ``BM`` and ``KR``):

.. code-block:: bash

   python main.py keyplayer kp-info \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n BM,KR \
       -oper all \
       -o /tmp/fig8_out/

Step 5 — Group Centrality
--------------------------

Find the 2-node group that maximizes group degree, betweenness, and closeness:

.. code-block:: bash

   python main.py groupcentrality gc-finder \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -k 2 \
       -oper all \
       -a greedy \
       -o /tmp/fig8_out/

To evaluate a specific set:

.. code-block:: bash

   python main.py groupcentrality gc-info \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -n KR,BS3 \
       -oper all \
       -o /tmp/fig8_out/

Step 6 — Removing Nodes Before Analysis
-----------------------------------------

To study the network after removing specific nodes (e.g., simulating a knockout):

.. code-block:: bash

   python main.py local \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -r BM,KR \
       -o /tmp/fig8_out/

The output TSV will reflect the 30-node residual graph and the report will note
``Removed nodes: ['BM', 'KR']``.

Next Steps
----------

- See :doc:`cli/keyplayer/index` for the full key-player CLI reference
- See :doc:`cli/percolation/index` for infection-percolation dynamics
- See :doc:`cli/mesoscale/index` for GTOM and Topological Importance
- See :doc:`outputs` for a complete guide to output file formats
