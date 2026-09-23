Group betweenness measures how much a group :math:`C` **intercepts geodesics** between pairs of nodes **outside** the group.

Let :math:`\sigma_{st}` be the number of shortest paths (geodesics) between nodes :math:`s` and :math:`t`.
Let :math:`\sigma_{st}(C)` be the number of those shortest paths that pass through **at least one** node in :math:`C` (with :math:`s,t \notin C`).

Pyntacle computes the average fraction of geodesics intercepted by the group:

.. math::
  C_B(C) =
  \frac{2}{(N-k)(N-k-1)}
  \sum_{\substack{s < t \\ s,t \notin C}}
  \frac{\sigma_{st}(C)}{\sigma_{st}}

Implementation notes:

* The method uses a precomputed matrix of shortest-path counts (``np_counts``) to obtain :math:`\sigma_{st}` efficiently.
* To estimate :math:`\sigma_{st}(C)`, the code removes all edges incident to the group nodes (thus preventing paths from traversing the group), recomputes shortest-path counts in the modified graph, and subtracts from the original counts.
* Rows/columns corresponding to group nodes are then discarded (set to zero) and the final score is normalized by :math:`(N-k)(N-k-1)/2`.
