Group betweenness measures how much a group :math:`C` **intercepts geodesics** between pairs of nodes **outside** the group.

Let :math:`\sigma_{st}` be the number of shortest paths (geodesics) between nodes :math:`s` and :math:`t`.
Let :math:`\sigma_{st}(C)` be the number of those shortest paths that pass through **at least one** node in :math:`C` (with :math:`s,t \notin C`).

Pyntacle computes the average fraction of geodesics intercepted by the group:

.. math::
  C_B(C) =
  \frac{2}{(N-k)(N-k-1)}
  \sum_{\substack{s < t \\ s,t \notin C}}
  \frac{\sigma_{st}(C)}{\sigma_{st}}

The score is 1 when the group lies on every shortest path between the other
nodes, as the centre of a star does.

Implementation notes:

* Shortest paths are counted, never listed. From each node outside the group
  the other nodes are settled in order of distance, and :math:`\sigma_{st}`
  and the number of paths that avoid the group are summed over each node's
  shortest-path predecessors. Edge lengths are used when the network is
  weighted (see :doc:`/weights`).
* Pairs that cannot reach each other add nothing.
* Releases up to 1.3.2 divided the sum by :math:`(N-k)(N-k-1)` instead of
  :math:`(N-k)(N-k-1)/2`, so their scores are half of these; the sets they
  found are the same.
