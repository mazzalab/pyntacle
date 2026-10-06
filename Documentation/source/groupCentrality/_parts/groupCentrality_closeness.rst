Group closeness extends node closeness by defining the distance between a node :math:`u \notin C` and a group :math:`C` as an **aggregation** of the distances from :math:`u` to each node in :math:`C`.

Let :math:`d(u,v)` be the shortest-path distance between nodes :math:`u` and :math:`v`. Pyntacle defines a *node-to-group distance* as:

.. math::
  d(u,C) = \operatorname{capo}\left(\{ d(u,v) \;|\; v \in C \}\right)

where ``capo`` is the aggregation chosen by the user via the ``distance_type`` argument. The default is ``min``, which corresponds to the Everett & Borgatti definition:

.. math::
  d(u,C) = \min_{v \in C} d(u,v)

Finally, **group closeness** is computed as:

.. math::
  C_C(C) = \frac{r}{N-k} \cdot \frac{r}{\sum_{u \in R} d(u,C)}

where :math:`R` is the set of non-group nodes that the group reaches and :math:`r = |R|`.
This is the correction of Wasserman & Faust (*Social Network Analysis*, Cambridge University
Press, 1994) for networks split into several components.
On a connected network :math:`r = N-k` and the score reduces to

.. math::
  C_C(C) = \frac{N-k}{\sum_{u \in V \setminus C} d(u,C)}

Implementation notes:

* Pyntacle computes :math:`d(u,C)` for each non-group node :math:`u` and sums these distances.
* Unreachable distances (disconnected cases) are ignored when building the set of distances to aggregate.
* The factor :math:`r/(N-k)` charges a set for the nodes it cannot reach. Without it, a set
  inside a small component would score above a set at the centre of the largest one.
* If the group reaches no other node, the function returns ``0.0`` (and prints a warning).
