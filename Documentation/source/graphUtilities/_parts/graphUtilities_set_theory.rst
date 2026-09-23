Pyntacle supports set-like operations between **two graphs**. The second input file must have the **same format** as the first one (same separator and header handling).

Given two graphs :math:`G_1=(V_1,E_1)` and :math:`G_2=(V_2,E_2)` the following operations are available:

Union
^^^^^

The **union** combines the information of both graphs:

.. math::
  V = V_1 \cup V_2,\quad E = E_1 \cup E_2

Implementation note: internally, Pyntacle builds undirected working copies and calls igraph union.
For consistent results, the two inputs should be defined on the same node universe (same vertex set / labels).

Intersection
^^^^^^^^^^^^

The **intersection** retains only what is common to both graphs:

* vertices: :math:`V = V_1 \cap V_2`
* edges: keep :math:`(u,v)` only if it exists in both graphs and :math:`u,v \in V`

.. math::
  E = E_1 \cap E_2

Difference
^^^^^^^^^^

The **difference** removes from :math:`G_1` the edges that also appear in :math:`G_2` (restricted to vertices present in :math:`G_2`).
After edge removal, isolated vertices are discarded.

In practice, this returns the portion of :math:`G_1` that is *not explained* by :math:`G_2`.
