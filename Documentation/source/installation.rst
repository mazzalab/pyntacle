Installation & Setup
====================

Pyntacle is installed from source into a conda environment. Conda provides
Python and the dependencies; ``pip`` then compiles Pyntacle's Cython
extensions with the system's C compiler and installs the ``pyntacle`` command.

Requirements
------------

* Linux or macOS
* A C compiler: gcc on Linux (``build-essential`` on Debian and Ubuntu), the
  Xcode Command Line Tools on macOS (``xcode-select --install``)
* `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ or
  `Anaconda <https://www.anaconda.com/download>`_
* Git

Step 1 — Get the source
-----------------------

.. code-block:: bash

   git clone https://github.com/mazzalab/pyntacle.git
   cd pyntacle

Step 2 — Create the conda environment
-------------------------------------

``environment.yml`` lists Python, igraph, Cython and every runtime
dependency, including the optional ones of
:doc:`omics <cli/omics/index>`:

.. code-block:: bash

   conda env create -f environment.yml
   conda activate pyntacle

On macOS, also install the OpenMP runtime, which the searches use to run on
several threads (``-np``):

.. code-block:: bash

   conda install llvm-openmp

Step 3 — Install Pyntacle
-------------------------

From the root of the repository, with the environment active:

.. code-block:: bash

   pip install .

This compiles the extensions and puts the ``pyntacle`` command on the
``PATH``. The build prints the OpenMP flags it uses, or a warning when the
compiler has no OpenMP: Pyntacle then works the same, but the key-player and
group-centrality searches run on one thread and ``-np`` is ignored.
Setting ``PYNTACLE_NO_OPENMP=1`` builds without OpenMP on purpose.

For development, ``pip install -e .`` installs in editable mode:
Python changes take effect immediately, while changes to ``pyntacle/_ext/*.pyx``
need ``python setup.py build_ext --inplace``.

Check the installation:

.. code-block:: bash

   pyntacle --version
   pyntacle --help

The help lists the available commands:

.. code-block:: text

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
   omics            Builds networks from raw omics matrices

``python -m pyntacle`` is equivalent to ``pyntacle``.

Optional — online gene annotation
---------------------------------

:doc:`omics <cli/omics/index>` can map Ensembl identifiers to gene symbols
online through ``mygene``, which is not in the environment:

.. code-block:: bash

   pip install mygene

Step 4 — Run a first analysis
-----------------------------

From the root of the repository, run ``local`` on the example network shipped
in ``examples/``:

.. code-block:: bash

   pyntacle local \
       -t edgelist \
       -i examples/figure_8.egl \
       -o pyntacle_test/

You should see output resembling (table cut here)::

   pyntacle local
   Input: examples/figure_8.egl
   Output directory: /home/you/pyntacle/pyntacle_test
   Network: 32 nodes, 56 edges, 1 component(s)

   Node Name  Degree  Betweenness  Closeness  Radiality  ...
          HS       2        0.000      0.212      5.290  ...
          PS       6       18.500      0.258      6.129  ...
   ...
   ... 12 more rows in the report

   Report: /home/you/pyntacle/pyntacle_test/report_figure_8_local.tsv
   HTML report: /home/you/pyntacle/pyntacle_test/figure_8_local.html
   Figure: /home/you/pyntacle/pyntacle_test/figure_8_local.svg
   Done!

The screen shows at most 20 rows of the result; the report holds all of them.

The output directory is created if it does not exist and will contain:

- ``report_figure_8_local.tsv`` — per-node metric table
- ``figure_8_local.svg`` — network visualization colored by degree
- ``figure_8_local.html`` — interactive visualization

Step 5 — Run the tests (optional)
---------------------------------

The tests import Pyntacle from the source tree, so the extensions must be
compiled there first:

.. code-block:: bash

   python setup.py build_ext --inplace
   pytest tests                # add --runslow for the performance tests

Troubleshooting
---------------

**``WARNING: this Pyntacle was compiled without OpenMP``**

The build found no OpenMP for the compiler, so ``-np`` has no effect. On
macOS, run ``conda install llvm-openmp`` in the environment (or, outside conda,
``brew install libomp``), then ``pip install .`` again.

**``ModuleNotFoundError: No module named 'pyntacle._ext.cython_metrics'``**

The extensions are not compiled, typically after editing a ``.pyx`` file in an
editable install. Rebuild them from the root of the repository:

.. code-block:: bash

   python setup.py build_ext --inplace

**``conda: command not found``**

Add conda to your ``PATH``, typically ``export PATH="$HOME/miniconda3/bin:$PATH"``.

Build the documentation
-----------------------

.. code-block:: bash

   pip install -r Documentation/requirements.txt
   cd Documentation/
   make html
   # open Documentation/build/html/index.html
