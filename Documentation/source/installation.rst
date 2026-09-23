Installation & Setup
====================

Pyntacle runs inside a pre-configured conda environment called ``graphtacle_debug``
that ships with all required dependencies, including the compiled Cython extensions.

Requirements
------------

* `Anaconda <https://www.anaconda.com/products/distribution>`_ or
  `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ (Python 3.10)
* The ``graphtacle_debug`` environment (see below)

Step 1 — Clone or download the repository
------------------------------------------

.. code-block:: bash

   git clone https://github.com/mazzalab/pyntacle.git
   cd pyntacle_final

Step 2 — Create the conda environment
--------------------------------------

If you already have the ``graphtacle_debug`` environment:

.. code-block:: bash

   conda activate graphtacle_debug

If you need to create it from scratch using the provided environment file:

.. code-block:: bash

   conda env create -f exact_working_env.yml
   conda activate graphtacle_debug

Step 3 — Run Pyntacle
----------------------

All commands must be run from inside the ``pyntacle/`` source directory:

.. code-block:: bash

   cd pyntacle/
   python main.py --help

Expected output::

    usage: python3 main.py command [subcommand] parameters

    The available commands in Pyntacle are:
      local            Computes metrics of local nature for the whole graph
      global           Computes metrics of global nature for the whole graph
      groupcentrality  Computes group centrality metrics
      keyplayer        Identifies key-player node sets
      set              Performs set operations between two networks
      convert          Converts a network file format to another
      communities      Finds communities within a graph
      extract          Extracts components from a fragmented graph
      generate         Generates random graphs
      mesoscale        Computes mesoscale metrics
      percolation      Runs infection-percolation dynamics

Step 4 — Verify the installation
----------------------------------

Run the ``local`` command on the included Figure 8 benchmark network:

.. code-block:: bash

   python main.py local \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -o /tmp/pyntacle_test/

You should see output resembling::

   Working on: ../dev/test/input/figure_8.egl

   No nodes removed

   Number of nodes: 32
   Number of edges: 56
   Number of components: 1
   Function : local

   Done!

The output directory will contain:
- ``report_figure_8_local.tsv`` — per-node metric table
- ``figure_8_local.svg`` — network visualization colored by degree
- ``figure_8_local.html`` — interactive Plotly visualization

Troubleshooting
---------------

**``ModuleNotFoundError: No module named '_ext.cython_metrics'``**

The Cython extensions are not compiled. Rebuild them from inside ``pyntacle/_ext/``:

.. code-block:: bash

   cd pyntacle/_ext/
   python setup.py build_ext --inplace

**``conda: command not found``**

Add conda to your PATH. Typically: ``export PATH="$HOME/miniconda3/bin:$PATH"``

**Build the documentation**

.. code-block:: bash

   cd Documentation/
   conda run -n graphtacle_debug make html
   # Output in Documentation/build/html/index.html
