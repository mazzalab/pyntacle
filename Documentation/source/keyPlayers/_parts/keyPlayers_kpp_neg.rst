Fragmentation (F)
"""""""""""""""""

Let :math:`G=(V,E)` be an undirected graph with :math:`|V|=n`, and let :math:`K` be a kp-set.
Let :math:`G' = G \setminus K` be the residual graph obtained by removing the nodes in :math:`K`.
Assume :math:`G'` has :math:`c` connected components with sizes :math:`s_1,\dots,s_c`.

The **fragmentation** index :math:`F` measures the proportion of node pairs that become disconnected in :math:`G'`:

.. math::
  F(G') = 1 - \frac{\sum_{t=1}^{c} s_t(s_t-1)}{n'(n'-1)}

where :math:`n' = |V(G')| = n-k`. The measure is 0 when :math:`G'` is connected, and approaches 1 as the residual network becomes maximally fragmented (all isolates).

Distance fragmentation (dF)
"""""""""""""""""""""""""""

Fragmentation alone does not distinguish between components with different internal structure (e.g., cliques vs. paths).
To incorporate *within-component cohesion*, Borgatti defines **distance fragmentation** using the reciprocals of shortest-path distances, adopting the convention that :math:`1/\infty = 0`.

Let :math:`d_{ij}` be the shortest-path distance between nodes :math:`i` and :math:`j` in the residual graph :math:`G'`. Then:

.. math::
  dF(G') = 1 - \frac{2\sum_{i>j}\frac{1}{d_{ij}}}{n'(n'-1)}

This score increases when the residual network is more “virtually disconnected”, either because it splits into many components or because path lengths within components are large.

Implementation note: in Pyntacle, shortest paths for :math:`dF` are computed using edge weights (if present).
