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

Since we are only consider unidirected graphs, the density D will be defined as:

.. math::
  D_{G} = \frac{2E}{V(V-1)}



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



Avarage Metrics
^^^^^^^^^^^^^^^^

Average shortest path length
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The **average shortest path length** (also known as *characteristic path length*) is the mean of the shortest-path distances among all node pairs in the graph *G*.

.. math::
  \bar{\ell}_{G} = \frac{1}{N(N-1)} \sum_{i \neq j} d(v_i, v_j)

When the graph is **weighted**, distances :math:`d(v_i, v_j)` are computed using edge weights as path lengths. 


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

The **average clustering coefficient** is the arithmetic mean of :math:`CC_i` across all nodes:

.. math::
  CC_G = \frac{1}{N}\sum_{i=1}^{N} CC_i 


Weighted clustering coefficient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pyntacle reports a **degree-weighted** version of clustering, i.e. a weighted average of local clustering coefficients where node degrees act as weights:

.. math::
  CC_{w,G} = \frac{\sum_{i=1}^{N} k_i \, CC_i}{\sum_{i=1}^{N} k_i} 


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

The **average closeness** is the mean closeness centrality over all nodes:

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
  R(v_i) = \frac{\sum_{j \neq i} (D - d(v_i, v_j) + 1)}{D(N-1)}.
  
The **average radiality** is:

.. math::
  \overline{R}_{G} = \frac{1}{N}\sum_{i=1}^{N} R(v_i) 


Average radiality reach
^^^^^^^^^^^^^^^^^^^^^^^

When a graph has multiple components, Pyntacle defines **radiality-reach** by rescaling radiality according to the size :math:`s_k` of the component :math:`k` the node belongs to (so nodes in larger components contribute more):

.. math::
  RR(v_i) = R(v_i)\cdot \frac{s_k}{N} 

The **average radiality reach** is:

.. math::
  \overline{RR}_{G} = \frac{1}{N}\sum_{i=1}^{N} RR(v_i) 


Completeness naive
^^^^^^^^^^^^^^^^^^

The **completeness naive** is a simple sparseness proxy equivalent to graph density (for undirected graphs):

.. math::
  \Delta = \frac{2E}{N(N-1)} 

It ranges from 0 to 1, with values close to 0 indicating sparse networks.


Completeness
^^^^^^^^^^^^

The **completeness index** :math:`\kappa` is a sparseness measure defined as the ratio between the number of edges and the number of missing edges (zeros) in the adjacency matrix:

.. math::
  \kappa = \frac{E}{Z}
         = \frac{\sum_{i \in V}\sum_{j \in V, j\neq i} a_{ij}}
                {\sum_{i \in V}\sum_{j \in V, j\neq i} (1-a_{ij})} 


Compactness
^^^^^^^^^^^

The **compactness index** :math:`\rho` is another sparseness/denseness proxy. In the original formulation reported in the Pyntacle thesis, it is:

.. math::
  \rho = \left(\frac{N^2}{2E} - 1\right)\left(1 - \frac{1}{N}\right) 

This formulation is asymptotical; graphs with :math:`\rho > 1` are classified as dense, while graphs with :math:`\rho < 1` are classified as sparse.

