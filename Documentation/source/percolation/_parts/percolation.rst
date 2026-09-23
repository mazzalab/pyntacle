Percolation on networks
-----------------------

**Percolation** is a general framework to study how a process propagates through a network when connectivity is *imperfect* or *heterogeneous*. In classical bond percolation, each edge is either **available** (open) or **unavailable** (closed); as the fraction of open edges increases, the graph may transition from fragmented components to a regime where large-scale connectivity emerges (often discussed in terms of a “giant component”).

In **infection percolation**, the same percolation idea is used to model spreading phenomena (e.g., contagion, information diffusion) where transmission is constrained by (i) **structural accessibility** of edges and (ii) **temporal limits** of infectiousness. In the specific formulation adopted here, each edge :math:`(i,j)` is assigned a *local transmission threshold* :math:`\theta_{ij}`; an infection process with global infectivity :math:`P^\*` can traverse only those edges satisfying :math:`P^\* \ge \theta_{ij}`. This turns the original graph into an **open-edge backbone** :math:`G^\*(P^\*)` on which a discrete-time **S–I–R** cascade is simulated (`Browne CA, et al. (2021)`_).

Why this model in Pyntacle?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This design captures two realistic sources of heterogeneity:

- **Edge-level variability** (some connections are easier/harder to transmit across) via :math:`\theta_{ij}`.
- **Finite infectious lifetime** via a recovery time :math:`\tau` (or node-specific :math:`\tau_i`), which limits how long infected nodes can transmit.

Together, they allow you to separate:

1. what is **structurally possible** (edges open under :math:`P^\*`), from
2. what is **dynamically realized** (edges actually used during the cascade).

.. _`Browne CA, et al. (2021)`: https://doi.org/10.3389/fphy.2021.645954


.. rubric:: Concept

This algorithm implements an **infection–percolation** dynamics on a graph by combining two ingredients:

1. **Edge heterogeneity**: each edge :math:`(i,j)` has a *local threshold* :math:`\theta_{ij}` that controls whether transmission along that edge is possible.
2. **Finite infectious lifetime**: an infected node can transmit only for a limited time (a recovery time :math:`\tau` or node-specific :math:`\tau_i`), after which it becomes inactive.

Operationally, the model proceeds in two stages:

- **Stage 1 (structural filtering)**: build an “open-edge backbone” by comparing a global infectivity :math:`P^\*` against each edge threshold.
- **Stage 2 (discrete cascade)**: simulate a synchronous spreading process (S–I–R) constrained to the open edges.


.. rubric:: Graph and notation

Let:

.. math::

   G=(V,E), \qquad |V|=N,\quad |E|=M.

Let :math:`A` be the adjacency matrix:

.. math::

   A_{ij}=
   \begin{cases}
   1 & (i,j)\in E\\
   0 & \text{otherwise}
   \end{cases}

Each node :math:`i` has a discrete state at time :math:`t`:

.. math::

   x_i(t)\in\{S,I,R\}

where:

- :math:`S`: susceptible
- :math:`I`: infected (active and potentially transmitting)
- :math:`R`: recovered (inactive; does not transmit)

Key inputs:

- :math:`P^\*\in[0,1]`: **global infectivity** (global “percolation probability”)
- :math:`\theta_{ij}`: **local edge threshold** on :math:`(i,j)`
- :math:`\tau` or :math:`\tau_i`: **recovery time** (infectious lifetime)
- :math:`S_0\subseteq V`: **seed set** infected at :math:`t=0`


.. rubric:: Local edge thresholds

Each edge :math:`(i,j)\in E` is assigned a threshold:

.. math::

   \theta_{ij}\in[0,p_{\mathrm{th,max}}].

Interpretation: :math:`\theta_{ij}` is the minimum infectivity required for that edge to be transmissible.

Two common constructions:

- **Sampled thresholds**: draw :math:`\theta_{ij}` from a specified distribution on :math:`[0,p_{\mathrm{th,max}}]`
  (e.g. uniform, truncated normal-like, bimodal “easy/hard” mixture).
- **Weight-as-threshold**: if the graph carries an edge attribute already in :math:`[0,1]`, interpret it directly as :math:`\theta_{ij}`
  (data-driven heterogeneity).


.. rubric:: Stage 1 — open-edge backbone

Given :math:`P^\*`, define the open-edge indicator:

.. math::

   O_{ij}=
   \begin{cases}
   1 & A_{ij}=1\ \wedge\ P^\*\ge\theta_{ij}\\
   0 & \text{otherwise}
   \end{cases}

This yields the open subgraph:

.. math::

   G^\*(P^\*)=(V,E^\*),\qquad
   E^\*=\{(i,j)\in E:\ P^\*\ge\theta_{ij}\}.

Interpretation:

- smaller :math:`P^\*` → fewer open edges → fragmented backbone → limited reach
- larger :math:`P^\*` → more open edges → better connectivity → larger cascades


.. rubric:: Recovery time (infectious lifetime)

Infected nodes remain infectious for a limited number of steps.

- **Fixed**: all nodes share the same :math:`\tau`.
- **Heterogeneous**: each node has :math:`\tau_i` (sampled from a chosen distribution or provided externally).

Recovery times are discrete durations measured in simulation steps.


.. rubric:: Stage 2 — discrete-time spreading on open edges

Time evolves in synchronous steps :math:`t=0,1,2,\dots`.

**Initialization.** Choose a seed set :math:`S_0`:

.. math::

   x_i(0)=
   \begin{cases}
   I & i\in S_0\\
   S & i\notin S_0
   \end{cases}

Define two derived (inferred) timestamps:

- **activation time** :math:`t_i^{(I)}` = first time :math:`i` becomes infected
- **recovery time** :math:`t_i^{(R)}` = first time :math:`i` becomes recovered

**Infection rule (S → I).** A susceptible node becomes infected if it has at least one infected neighbor connected by an open edge:

.. math::

   x_v(t)=S \ \wedge\ \exists u:\ x_u(t)=I \ \wedge\ O_{uv}=1
   \ \Longrightarrow\ x_v(t+1)=I.

**Recovery rule (I → R).** Let :math:`a_i(t)` be the “infection age” (steps since activation). Then:

.. math::

   x_i(t)=I \ \wedge\ a_i(t+1)\ge\tau_i
   \ \Longrightarrow\ x_i(t+1)=R.

Recovered nodes remain recovered and do not transmit further.


.. rubric:: Standard outputs and summary measures

At each time step, compartment sizes are:

.. math::

   S(t)=|\{i:\ x_i(t)=S\}|,\quad
   I(t)=|\{i:\ x_i(t)=I\}|,\quad
   R(t)=|\{i:\ x_i(t)=R\}|.

Typical derived summaries:

**Final reached (ever infected):**

.. math::

   \mathrm{Reached}=|\{i:\ t_i^{(I)}<\infty\}|.

**Peak prevalence and its time:**

.. math::

   I_{\max}=\max_t I(t),\qquad
   t_{\mathrm{peak}}=\arg\max_t I(t).

**Extinction time:**

.. math::

   t_{\mathrm{end}}=\max\{t:\ I(t)>0\}.


.. rubric:: Transmission edges and cascade depth

For interpretability, infection events can be represented as a set of realized transmission edges with time:

.. math::

   \mathcal{E}_{\mathrm{inf}}=\{(\{u,v\},t)\}

meaning that transmission across :math:`\{u,v\}` is first realized at step :math:`t`.
This induces an infection forest rooted at :math:`S_0`, from which a **cascade depth**
(maximum hop-distance from the seed set) can be computed.


.. rubric:: Edge categories: blocked, open-unused, used

At the end of the simulation, each original edge can be classified:

- **Blocked**: :math:`O_{ij}=0` (threshold too high: :math:`P^\*<\theta_{ij}`)
- **Open but unused**: :math:`O_{ij}=1` but never realized as transmission
- **Used**: edges that appear in :math:`\mathcal{E}_{\mathrm{inf}}`

This separates what is structurally possible (open backbone) from what is dynamically realized (observed cascade).
