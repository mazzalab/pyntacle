.. .. sidebar:: Abbreviations
..    :subtitle: da cambiare

..    · Graph » *G*

..    · Total number of **edges** » *E*

..    · Total number of **nodes**

In the formulas graph is referred as *G*, the total edges as *E* and *N* for the total nodes.



Degree
^^^^^^^^^^^^^^^^^^^^^^

Let *G = (V, E)* be a (**non-empty**) graph. The set of neighbours of a
vertex *v* in *G* is denoted by |NG(v)|, or briefly by *N(v)*. More generally *N(v)*
for *U ⊆ V* , the neighbours in *V\\U* of vertices in *U* are called *neighbours*
of *U*; their set is denoted by *N(U)*.
The degree (or valency) *dG(v) = d(v)* of a vertex v is the number degree *d(v)*
*\|E(v)\|* of edges at *v*; by our definition of a graph, this is equal to the
number of neighbours of *v*. A vertex of degree 0 is *isolated*. 


.. |NG(v)| replace:: *N*\ :sub:`G`\ *(v)*




.. figure:: /img/DegreeCentrality.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of degree; the color (green for lower values and red for higher values) of node represent its degree.


Betweenness
^^^^^^^^^^^^^^^^^^^^^^
The betweenness centrality of a node *v* is given by the expression:

	* **Non-Weighted**
		.. math::
   			g(v) = \sum_{s≠v≠t} \frac{\sigma_{st}(v)}{\sigma_{st}}


	  where :math:`\sigma_{st}` is the total number of shortest paths from node *s* to node *t* and :math:`\sigma_{st}(v)` is the number of those paths that pass through *v* (not where *v* is an end point).


	* **Weighted**

	  In a weighted network, the connections between nodes are not simply regarded as binary interactions. Instead, these connections are assigned weights that correspond to factors such as capacity, influence, frequency, etc. This introduces an additional layer of heterogeneity within the network, going beyond the topological effects. The strength of a node in a weighted network is determined by the total sum of weights associated with its neighboring edges.
		
		.. math::
   			s(i) = \sum_{j=1}^{N} a_{ij} \sigma_{st}


	  With :math:`a_{ij}` and :math:`w_{ij}` being adjacency and weight matrices between nodes *i* and *j*, respectively. Analogous to the power law distribution of degree found in scale free networks, the strength of a given node follows a power law distribution as well.


.. figure:: /img/BetweennessCentrality.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of betweenness; the color (green for lower values and red for higher values) of node represent its betweenness.


Closeness
^^^^^^^^^^^^^^^^^^^^^^

Computes the closeness centralities for specified vertices within a graph.

Closeness centrality for a vertex assesses the ease with which other vertices can be accessed from it (or vice versa: how easily it can be reached from other vertices). This metric is calculated as the reciprocal of the sum of the lengths of all geodesics from/to the designated vertex, normalized by the total number of vertices minus one

.. math::
   			C(v) = \frac{N-1}{\sum_{y}d(u,v)}

where :math:`d(u,v)` is the distance (length of the shortest path) between vertices *v* *u*.

.. figure:: /img/ClosenessCentrality.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of closeness; the color (green for lower values and red for higher values) of node represent its closeness.

Radiality
^^^^^^^^^^^^^^^^^^^^^^

The radiality of a node *v* is calculated by computing the **shortest path** between the node *v* and all other nodes in the graph *sp(v, u)*. The value of each path is then subtracted by the value of the diameter *+1 (ΔG + 1)* and the resulting values are summated. Finally, the obtained value is divided for the number of nodes *−1 (n − 1)*.

.. math::
	C_{rad}(v) = \frac{\sum_{u∈N}(ΔG + 1 - sp(v,u))}{n-1}

.. figure:: /img/Radiality.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of radiality; the color (green for lower values and red for higher values) of node represent its radiality.


Radiality reach
^^^^^^^^^^^^^^^^^^^^^^

The radiality reach of a vertex *v* is an index that assign high centrality to nodes that are at a short distance to every other node *u* in its reachable neighbors with respect to the graph.

.. math::
	RadialityReach(v) = C_{rad}(v) · \frac{N}{N_{c}}

where :math:`C_{rad}(v)` is the radiality of the *v* node, *N* is the total number of nodes in the graph *G* and :math:`N_{c}` is the number of nodes in the *c* component in which the *v* lies.
 
.. figure:: /img/RadialityReach.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of radiality reach; the color (green for lower values and red for higher values) of node represent its radiality reach.

Clustering Coefficient
^^^^^^^^^^^^^^^^^^^^^^

Clustering coefficient quantifies the degree to which nodes in a graph *G* form tight-knit groups. In Pyntacle we consider **local** clustering coefficient which quantifies how close its neighbours are to being a clique (complete graph).


.. math::
	C_{i} = \frac{2|\{e_{jk}:v_{j},v_{k}∈N_{i},e_{jk}∈E\}|}{k_{i}(k_{i}-1)}

The neighbourhood :math:`N_{i}` for a vertex :math:`v_{i}` is defined as its immediately connected neighbours as follows:

.. math::
	N_{i}=\{v_{j}:e_{ij}∈E∨e_{ij}∈E\}

where we define :math:`k_{i}` as the number of vertices, :math:`|N_{i}|`, in the neighbourhood, :math:`N_{i}`, of vertex :math:`v_{i}`.

.. figure:: /img/ClusteringCoefficient.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of clustering coefficient; the color (green for lower values and red for higher values) of node represent its clustering coefficient.

Eccentricity
^^^^^^^^^^^^^^^^^^^^^^

The eccentricity :math:`\epsilon(v)` of a vertex *v* is the maximum graph distance between *v* and any other vertex *u* of *G* (for a disconnected graph, all vertices are defined to have infinite eccentricity)

.. math::
	 \epsilon_{v} = max(dist(v,u))


where :math:`u∈V`

.. figure:: /img/Eccentricity.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of eccentricity; the color (green for lower values and red for higher values) of node represent its eccentricity.

Eigenvector (Scaled)
^^^^^^^^^^^^^^^^^^^^^^

Eigenvector centrality, alternatively named eigencentrality or prestige score, functions as a quantitative measure delineating the influence exerted by a node within a connected network
let :math:`A = (a_{v,t})` be the adjacency matrix, i.e. :math:`a_{v,t} = 1` if vertex *v* is linked to vertex *t*, and :math:`a_{v,t} = 0` otherwise. The relative centrality score, :math:`x_{v}`, of vertex *v* can be defined as:

.. math::
	x_{v} = \frac{1}{\lambda}\sum_{t∈M(v)}x_{t} = \frac{1}{\lambda}\sum_{t∈V}a_{v,t}x_{t}

where *M(v)* is the set of neighbors of *v* and :math:`\lambda`  is a constant. With a small rearrangement this can be rewritten in vector notation as the eigenvector equation.

.. figure:: /img/EigenvectorScaled.png 
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of eigenvector (scaled); the color (green for lower values and red for higher values) of node represent its eigenvectorv (scaled).


PageRank
^^^^^^^^

PageRank, an algorithm used for link analysis, assigns a numerical weight to each component within a set of interconnected documents, like those found on the World Wide Web. Its objective is to gauge the relative significance of each element within the set.

Generally, PageRank of a node *v* can be defined as

.. math::
	PR(v) = \sum_{u∈B_{v}} \frac{PR(u)}{L(u)}


where :math:`B_{v}` is the set containing all pages linking to page *v* and *L(u)* is the number of links from "*page*" *u*.

.. figure:: /img/PageRank.png
  :figwidth: 600
  :align: left

  Quick example to graphically explain the concept of PageRank; the color (green for lower values and red for higher values) of node represent its eigenvectorv (scaled).


