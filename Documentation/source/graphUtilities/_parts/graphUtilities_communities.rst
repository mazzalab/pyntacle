The ``communities`` command detects modules (communities) using one of the supported algorithms:

* **fastgreedy**
* **infomap**
* **leading-eigenvector**
* **random-walk** (Walktrap)
* **percolation** (Clique Percolation Method, parameter :math:`k`)

The output is a list of modules that can optionally be filtered by constraints such as minimum/maximum module size or number of components.
