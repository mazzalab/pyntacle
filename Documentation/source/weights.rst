.. _edge-weights:

Edge weights
============

An edge weight can mean opposite things, and different network measures read
it differently. Pyntacle therefore asks what the weights of a network are
(``-w`` together with ``--weight-type``) and gives each measure the reading
it needs.

.. contents::
   :local:
   :depth: 2

Three readings of one number
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Reading
     - Measures that use it
     - A larger weight means
   * - **Length** (distance)
     - shortest paths, closeness, betweenness, radiality, weighted diameter
       and path-length descriptors (``global``), key-player dF and m-reach, group closeness and
       group betweenness
     - the two nodes are farther apart
   * - **Strength** (affinity)
     - clustering coefficient, eigenvector centrality, PageRank (``local``);
       every ``communities`` algorithm; topological importance (``mesoscale``)
     - the two nodes are more tightly tied
   * - **Threshold** (resistance)
     - ``percolation -w``: an edge transmits when P* exceeds its threshold
     - the edge transmits less easily

A strength is the inverse notion of a length: a strong tie is a short edge.
Handing the same number to both kinds of measure inverts one of them, so the
weight type is declared once and Pyntacle derives the other reading.

Weight types
------------

``--weight-type distance`` (default)
   The weights are lengths, as in Pyntacle 1.x: kilometres, costs, times.
   Every weight must be positive. Strength-based measures use 1/w.

``--weight-type affinity``
   The weights are tie strengths: an absolute correlation, a co-occurrence
   count, an interaction confidence. Every weight must be positive. Path-based
   measures use a length obtained by the distance transform (below).

``--weight-type signed``
   The weights are signed strengths, such as correlation or partial
   correlation coefficients: a negative value is an antagonistic tie
   (inhibition, anti-correlation). The magnitude \|w\| is the strength of the
   tie and the sign is kept as the edge attribute ``sign``. Zero is not
   allowed (it is indistinguishable from a missing edge).

Without ``-w`` the network is unweighted and every edge has length and
strength 1. The chosen reading is printed at the start of the run and written
in the report header (``Edge weights``).

Distance transform
------------------

For ``affinity`` and ``signed`` weights, ``--distance-transform`` turns a
strength *a* into the length *d* used by path-based measures:

.. list-table::
   :header-rows: 1
   :widths: 18 18 64

   * - Transform
     - Length
     - Notes
   * - ``inverse`` (default)
     - *d* = 1/*a*
     - The usual convention for shortest paths and path-based centralities in
       weighted networks (`Newman 2001`_; `Brandes 2001`_; `Opsahl et al.
       2010`_; `Rubinov & Sporns 2010`_). Accepts any positive strength. For
       strengths up to 1, such as correlations, every length is at least 1, so
       dR, group closeness and radiality stay within [0, 1].
   * - ``one-minus``
     - *d* = 1 − *a*
     - For strengths in (0, 1]; lengths are floored at 10\ :sup:`−6`.
   * - ``neglog``
     - *d* = −ln *a*
     - For strengths in (0, 1]; the length of a path is minus the logarithm of
       the product of its strengths, so the shortest path is the path with the
       largest product. Floored at 10\ :sup:`−6`.

The three transforms order edges the same way but weigh long paths against
short ones differently, so results that depend on path lengths can change
with the choice. The choice is a convention, not a property of the data:
when a conclusion rests on it, repeat the analysis with another transform and
report whether the conclusion holds.

Percolation thresholds follow the declared type: a length is used as the
threshold directly (it must lie in [0, 1]); a strength *a* in [0, 1] gives the
threshold 1 − *a*, so that a strong tie transmits easily.

Negative weights
----------------

A negative number cannot be a length. On an undirected network an edge of
negative length can be crossed back and forth indefinitely, making every path
through it arbitrarily short: shortest paths do not exist, and no algorithm
can compute them. Pyntacle therefore refuses negative weights under
``distance`` and ``affinity`` and names the fix, instead of silently taking
their absolute value (which earlier versions did).

A network with negative ties can be analysed in three ways:

1. **As an unsigned network** — ``--weight-type signed``: the strength of a tie
   is its magnitude, whatever its sign. This is how unsigned weighted
   co-expression networks are built (`Zhang & Horvath 2005`_). Pyntacle does
   this, keeps the sign and says, at every run, that the measures are
   computed on \|w\|.
2. **As two layers** — split the edge list into positive and negative edges
   and analyse each network on its own, when cooperation and antagonism are
   expected to be organised differently.
3. **With measures defined for signed networks** — for instance the PN
   centrality of `Everett & Borgatti 2014`_, in which negative ties lower a
   node's score. Pyntacle does not implement these.

Commands that only write the network back out (``convert``, ``set``,
``extract``) keep the weights exactly as read, signs included.

Examples
--------

.. code-block:: console

   # lengths (default): road distances
   python3 main.py global -t edgelist -i roads.tsv -w

   # strengths: interaction confidence scores in (0, 1]
   python3 main.py keyplayer kp-finder -t edgelist -i ppi.tsv -w -wt affinity -k 3

   # signed partial correlations, e.g. from `omics`; sensitivity to the transform
   python3 main.py keyplayer kp-finder -t edgelist -i net.tsv -w -wt signed -k 2
   python3 main.py keyplayer kp-finder -t edgelist -i net.tsv -w -wt signed -dt neglog -k 2

References
----------

* `Brandes 2001`_ — A faster algorithm for betweenness centrality. *J Math Sociol* 25:163–177.
* `Everett & Borgatti 2014`_ — Networks containing negative ties. *Soc Networks* 38:111–120.
* `Newman 2001`_ — Scientific collaboration networks. II. Shortest paths, weighted networks, and centrality. *Phys Rev E* 64:016132.
* `Opsahl et al. 2010`_ — Node centrality in weighted networks: generalizing degree and shortest paths. *Soc Networks* 32:245–251.
* `Rubinov & Sporns 2010`_ — Complex network measures of brain connectivity: uses and interpretations. *NeuroImage* 52:1059–1069.
* `Zhang & Horvath 2005`_ — A general framework for weighted gene co-expression network analysis. *Stat Appl Genet Mol Biol* 4:17.

.. _`Brandes 2001`: https://doi.org/10.1080/0022250X.2001.9990249
.. _`Everett & Borgatti 2014`: https://doi.org/10.1016/j.socnet.2014.03.005
.. _`Newman 2001`: https://doi.org/10.1103/PhysRevE.64.016132
.. _`Opsahl et al. 2010`: https://doi.org/10.1016/j.socnet.2010.03.006
.. _`Rubinov & Sporns 2010`: https://doi.org/10.1016/j.neuroimage.2009.10.003
.. _`Zhang & Horvath 2005`: https://doi.org/10.2202/1544-6115.1128
