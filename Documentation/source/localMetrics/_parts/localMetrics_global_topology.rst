In the formulas graph is referred as *G*, the total edges as *E* and *N* for the total nodes.



Diameter
^^^^^^^^^^^^^^^^^^^^^^

The diameter *d* of a graph is the maximum eccentricity of any vertex in the graph *G*. That is, *d* is the greatest distance between any pair of vertices or, alternatively,


.. math::
  d_{G} = \max_{u∈V} \epsilon_{v} = \max_{u∈V} \max_{v∈V} d(v,u)



Components
^^^^^^^^^^^^^^^^^^^^^^


The number of components in a graph is the count of connected subgraphs *g* in the graph *G*. A component of an undirected graph *G* is a connected subgraph *g* that is not part of any larger connected subgraph


.. figure:: /img/Single_Component_graph.png
  :figwidth: 600
  :align: left


.. figure:: /img/Components_graph.png
  :figwidth: 600
  :align: left



Density
^^^^^^^^^^^^^^^^^^^^^^^^

The graph density of a graph *G* is defined as the ratio of the number of edges *E* with respect to the maximum possible edges. 

For an undirected graph the density is:

.. math::
  D_{G} = \frac{2E}{N(N-1)}

and :math:`E / (N(N-1))` for a directed one (``-d``).



Radius
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We define the radius as the minimum eccentricity of a given graph *G*:


.. math::
  radius_{G} = \min_{}\{\epsilon_{v}|v∈V\}



Pi
^^^^^^^^^^^^^^^^

*Pi* is defined as the ratio between the total number of edges and the diameter.


.. math::
  Pi_{G} = \frac{E}{d_{G}}



Average Metrics
^^^^^^^^^^^^^^^

Average shortest path length
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The **average shortest path length** (also known as *characteristic path length*) is the mean of the shortest-path distances among all node pairs in the graph *G*.

.. math::
  \bar{\ell}_{G} = \frac{1}{N(N-1)} \sum_{i \neq j} d(v_i, v_j)

Distances are counted in hops (edges), also when the graph is weighted, as for the median below. On a network split into several components only the pairs that reach each other are averaged.


Median shortest path length
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The **median shortest path length** is the median value of the distribution of shortest-path distances among all node pairs (considering only finite distances).

.. math::
  \tilde{\ell}_{G} = \mathrm{median}\left(\{ d(v_i, v_j) \mid i \neq j \}\right)


Average clustering coefficient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The (local) **clustering coefficient** of a node :math:`v_i` is defined as the proportion of links among neighbors of :math:`v_i` over the maximum possible number of such links.

.. math::
  CC_i = \frac{\text{number of closed triangles connected to } v_i}{\text{number of triples centered around } v_i}

The **average clustering coefficient** is the arithmetic mean of :math:`CC_i` over the :math:`N_2` nodes of degree 2 or more, the only ones with triples centred on them:

.. math::
  CC_G = \frac{1}{N_2}\sum_{i:\ k_i \geq 2} CC_i

It ignores edge weights, and is 0 when no node has degree 2. The ``Clustering Coefficient`` column of the local report gives 0 to the other nodes, so its mean can be lower.


Global clustering coefficient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The **global clustering coefficient** (transitivity) is the fraction of connected triples that close into a triangle:

.. math::
  C_G = \frac{3 \times \text{number of triangles}}{\text{number of connected triples}} = \frac{\sum_{i=1}^{N} k_i (k_i - 1) \, CC_i}{\sum_{i=1}^{N} k_i (k_i - 1)}

It is a weighted average of the local clustering coefficients, each weighted by the number of triples centred on the node,
so high-degree nodes count more than in the average clustering coefficient. It ignores edge weights and direction, and is 0 when there is no connected triple.
Releases up to 1.3.2 reported this value as "Weighted clustering coefficient".


Average degree
^^^^^^^^^^^^^^

The **average degree** is the mean of node degrees.

.. math::
  \langle k \rangle = \frac{1}{N}\sum_{i=1}^{N} k_i 

For undirected graphs, this is equivalently:

.. math::
  \langle k \rangle = \frac{2E}{N}


Average closeness
^^^^^^^^^^^^^^^^^

The **average closeness** is the mean closeness centrality over all nodes, a node that reaches no other counting 0:

.. math::
  \overline{C}_{G} = \frac{1}{N}\sum_{i=1}^{N} C(v_i)

Closeness centrality is based on shortest-path distances (the more central a node, the closer it is to all others). 


Average eccentricity
^^^^^^^^^^^^^^^^^^^^

The **eccentricity** of a node is the maximum shortest-path distance from that node to any other node. The **average eccentricity** is:

.. math::
  \overline{\epsilon}_{G} = \frac{1}{N}\sum_{i=1}^{N} \epsilon(v_i)


Average radiality
^^^^^^^^^^^^^^^^^

The **radiality** of a node is an integration-like centrality based on the graph diameter :math:`D` and shortest-path distances:

.. math::
  R(v_i) = \frac{\sum_{j\ \text{reached by}\ i} (D - d(v_i, v_j) + 1)}{N-1}.

Nodes that :math:`v_i` cannot reach add nothing.
  
The **average radiality** is:

.. math::
  \overline{R}_{G} = \frac{1}{N}\sum_{i=1}^{N} R(v_i) 


Average radiality reach
^^^^^^^^^^^^^^^^^^^^^^^

When a graph has multiple components, Pyntacle defines **radiality-reach** by computing radiality inside the component :math:`k` the node belongs to, :math:`R_k(v_i)`, and rescaling it by the size :math:`s_k` of that component (so nodes in larger components contribute more):

.. math::
  RR(v_i) = R_k(v_i)\cdot \frac{s_k}{N} 

The **average radiality reach** is:

.. math::
  \overline{RR}_{G} = \frac{1}{N}\sum_{i=1}^{N} RR(v_i) 


Completeness naive
^^^^^^^^^^^^^^^^^^

The **completeness naive** is the ratio between the non-zero and the zero
cells of the adjacency matrix, diagonal excluded. For an undirected graph each
edge fills two cells:

.. math::
  \kappa_{naive} = \frac{2E}{N(N-1) - 2E}

(:math:`E / (N(N-1) - E)` for a directed one). It is close to the density on
sparse networks, exceeds 1 once more than half of the node pairs are linked,
and is reported as 1 for a complete graph.


Completeness
^^^^^^^^^^^^

The **completeness index** is computed from the number :math:`Z` of zero cells
of the :math:`N \times N` adjacency matrix, diagonal included
(:math:`Z = N^2 - 2E` for an undirected graph, :math:`N^2 - E` for a directed one):

.. math::
  \kappa = (N - 1)\left(\frac{N^2}{Z} - 1\right)

It can exceed 1; the definition is the one of release 1.3.2.


Compactness
^^^^^^^^^^^

The **compactness index** is the reciprocal of the Randić and DeAlba product

.. math::
  \rho = \left(\frac{N^2}{e} - 1\right)\left(1 - \frac{1}{N}\right)

where :math:`e` is the number of non-zero cells of the adjacency matrix
(:math:`2E` undirected, :math:`E` directed). Pyntacle reports :math:`1/\rho`:
values above 1 mark dense graphs and values below 1 sparse ones.

