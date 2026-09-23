Key Players
===========

The **Key Player Problem** (KPP) aims at identifying (or evaluating) *sets* of nodes (kp-sets) that are crucial for a network, depending on the analyst’s goal. In Pyntacle, a kp-set of order :math:`k` is a subset of nodes :math:`K \subset V` with :math:`|K|=k`.

Borgatti formalized two complementary goals (`Borgatti (2006)`_):

* **KPP-Neg (negative key players)**: find sets whose *removal* maximally disrupts the network (fragmentation / loss of cohesion).
* **KPP-Pos (positive key players)**: find sets that are *optimally positioned* to reach the rest of the network (diffusion / coverage).

Accordingly, Pyntacle implements four **kp-set evaluation metrics**:

* **Negative**: Fragmentation (:math:`F`) and Distance fragmentation (:math:`dF`)
* **Positive**: Distance-weighted reach (:math:`dR`) and :math:`m`-reach (``mreach``)

In the implementation, negative metrics are computed on the **residual graph** obtained by removing the kp-set from the original graph, while positive metrics are computed on the original graph using the kp-set as seeds.

.. _`Borgatti (2006)`: https://doi.org/10.1007/s10588-006-7084-x

.. contents::
   :local:
   :depth: 2

.. _kpp-neg:

KPP-Neg metrics
---------------
.. include:: _parts/keyPlayers_kpp_neg.rst

.. _kpp-pos:

KPP-Pos metrics
---------------
.. include:: _parts/keyPlayers_kpp_pos.rst
