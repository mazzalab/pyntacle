**Topological Importance (TI)** quantifies how strongly the effect originating from a node can spread through the network within a maximum path length :math:`k`.
The implementation in Pyntacle follows the approach used in the CoSBiLab Graph software line of “influence by propagation”.

Core idea
^^^^^^^^^

1. Build a **direct effect** matrix :math:`E`:

   * Unweighted case:

     .. math::

        E_{ij} = a_{ij}\,\frac{1}{\deg(j)}

   * Weighted case:

     .. math::

        E_{ij} = w_{ij}\,\frac{1}{s(j)}

     where :math:`s(j)` is the strength of node :math:`j`.

2. Propagate effects by matrix powers:

   .. math::

      E^{(l)} = E^l

3. Average effects up to :math:`k` steps and summarize per source node.

In the current implementation, the returned matrix corresponds to the **average effect** from each source node to all targets:

.. math::

   \bar{E} = \frac{1}{k}\sum_{l=1}^{k} E^l

and TI for node :math:`i` is computed as:

.. math::

   TI_i(k) = \sum_{j} \bar{E}_{ij}

Implementation notes (TI)
^^^^^^^^^^^^^^^^^^^^^^^^^

* **Undirected graph**: if the input graph is directed, TI is computed on the undirected version (the adjacency is symmetrised); a message is shown. This mirrors GTOM.
* **Self-loops are ignored** (warning if present).
* The output is a full matrix of averaged effects (source rows → target columns) plus summary columns.
* Optional **Topological Overlap (TO)** is computed from the :math:`k`-step effect matrix by thresholding and comparing “reachable sets” induced by strong effects.


* an :math:`n \times n` block with the averaged effects (rows = sources, columns = targets),
* a summary column:

  * ``TI_k`` for unweighted graphs
  * ``WI_k`` for weighted graphs

* optionally: ``TO_k`` when ``threshold > 0``.
