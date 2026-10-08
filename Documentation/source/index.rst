Pyntacle — Network Analysis Toolkit
=====================================

**Pyntacle** is an open-source Python toolkit for network analysis and visualization.
It provides a command-line interface and Python API for importing, manipulating, and
analyzing network data — from local and global topology metrics to advanced key-player
identification, mesoscale analysis, and infection-percolation dynamics.

.. grid:: 2

   .. grid-item-card:: Quick Install
      :link: installation
      :link-type: doc

      Create the conda environment, install with pip and start analyzing networks.

   .. grid-item-card:: CLI Reference
      :link: cli/index
      :link-type: doc

      Full reference for all 12 commands: local, global, keyplayer, groupcentrality,
      mesoscale, percolation, communities, set, convert, extract, generate, omics.

.. grid:: 2

   .. grid-item-card:: Omics to Networks
      :link: omics/omics
      :link-type: doc

      Build tumour/normal networks from raw RNA-seq counts or microbiome
      abundances with ``omics``, ready for every other command.

.. grid:: 2

   .. grid-item-card:: Tutorial
      :link: tutorial
      :link-type: doc

      Step-by-step walkthrough using the Figure 8 benchmark network: local metrics,
      key-player identification, and percolation analysis.

   .. grid-item-card:: Algorithm Reference
      :link: localMetrics/localMetrics
      :link-type: doc

      Mathematical definitions and implementation details for every metric.

Quick Start
-----------

.. code-block:: bash

   # 1. Activate the environment (see Installation)
   conda activate pyntacle

   # 2. Compute local metrics on an edge-list file
   pyntacle local -t edgelist -i my_network.egl -o output/

   # 3. Find the 2 best key-player nodes (greedy algorithm)
   pyntacle keyplayer kp-finder -t edgelist -i my_network.egl \
       -k 2 -oper all -a greedy -o output/

   # 4. Run a percolation simulation from a seed node
   pyntacle percolation -t edgelist -i my_network.egl \
       -n NodeA -P 0.7 -tau 3 -o output/

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   installation
   tutorial
   changelog

.. toctree::
   :maxdepth: 2
   :caption: Algorithm Reference

   localMetrics/localMetrics
   groupCentrality/groupCentrality
   keyPlayers/keyPlayers
   mesoScales/mesoScales
   percolation/percolation
   omics/omics
   graphUtilities/graphUtilities

.. toctree::
   :maxdepth: 1
   :caption: File Formats

   format/format
   weights
   outputs

.. toctree::
   :maxdepth: 2
   :caption: Command-Line Interface

   cli/index

.. toctree::
   :maxdepth: 1
   :caption: API Reference

   api

.. include:: _parts/cli_dropdown.rst

Links
-----

* `GitHub <https://github.com/mazzalab/pyntacle/>`_
* `Website <https://pyntacle.css-mendel.it/>`_
