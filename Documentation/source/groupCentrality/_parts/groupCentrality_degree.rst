Let :math:`G=(V,E)` be a graph with :math:`|V| = N` nodes, and let :math:`C \subset V` be a **group** of nodes of size :math:`|C| = k`.

The **group degree** quantifies how many **distinct non-group** nodes are directly adjacent to **at least one** node in :math:`C`, normalized by the number of non-group nodes.

Define the *group neighborhood*:

.. math::
  N(C) = \{ u \in V \setminus C \;|\; \exists v \in C : (u,v) \in E \}

Then Pyntacle computes:

.. math::
  C_D(C) = \frac{|N(C)|}{N-k}

This is exactly what the implementation does: it collects the 1-hop neighborhood of every node in the group, removes the group nodes themselves, takes the unique set, and normalizes by :math:`N-k`.
