Distance-weighted reach (dR)
""""""""""""""""""""""""""""

Positive key players are intended as **seeds for diffusion**: good kp-sets should be close (in graph distance) to many nodes. Borgatti’s **distance-weighted reach** assigns each node a contribution inversely proportional to its distance from the kp-set.

Define the distance from the set :math:`K` to a node :math:`j` as the minimum distance from any kp node:

.. math::
  d_{Kj} = \min_{i \in K} d_{ij}

Then Pyntacle computes:

.. math::
  dR(K) = \frac{1}{n}\sum_{j \in V \setminus K}\frac{1}{d_{Kj}}

The score is maximized when many nodes are adjacent (distance 1) to the kp-set and decreases as nodes become farther.

Implementation note: in Pyntacle, unreachable distances are replaced by :math:`n+1` (rather than contributing exactly 0), yielding a very small contribution :math:`1/(n+1)` for disconnected nodes.

m-reach (mreach)
"""""""""""""""""

The **m-reach** metric counts how many unique nodes outside the kp-set can be reached within at most :math:`m` steps from at least one kp node.

Let :math:`\mathbf{1}[\cdot]` be the indicator function. Then:

.. math::
  \mathrm{mreach}(K,m) = \sum_{j \in V \setminus K} \mathbf{1}\left[d_{Kj} \le m\right]

This measure is easy to interpret (coverage within a distance budget), but treats all distances :math:`\le m` as equally valuable, and all distances :math:`>m` as irrelevant.
