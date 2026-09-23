:orphan:


convert
=======

Convert translates a network from one supported file format to another.

Supported conversions:

- ``AdjMatrix`` ↔ ``EdgeList``
- ``AdjMatrix`` ↔ ``SIF``
- ``AdjMatrix`` ↔ ``DOT``
- ``EdgeList`` ↔ ``SIF``
- ``EdgeList`` ↔ ``DOT``
- ``SIF`` ↔ ``DOT``

Synopsis
--------
.. code-block:: console

   python3 main.py convert [OPTIONS]


Options
-------
.. list-table::
   :header-rows: 1
   :widths: 18 8 12 12 14 36

   * - Option
     - Required
     - Type
     - Default
     - Choices
     - Help
   * - ``-t``, ``--fileType``
     - Yes
     - str
     - \ 
     - matrix, edgelist, sif, dot
     - File type
   * - ``-i``, ``--inputFile``
     - Yes
     - \ 
     - \ 
     - \ 
     - Specify the input file name
   * - ``-s``, ``--sep``
     - No
     - str
     - \ 
     - \ 
     - Use this flag if your file has a specific header (ex. ',')
   * - ``-nh``, ``--NoHeader``
     - No
     - bool
     - False
     - \ 
     - Use this flag if your file doesn't have an header
   * - ``-d``, ``--directed``
     - No
     - bool
     - False
     - \ 
     - Use this flag if your graph is directed
   * - ``-w``, ``--weight``
     - No
     - bool
     - False
     - \ 
     - Use this flag if your graph is weighted
   * - ``-r``, ``--remove``
     - No
     - \ 
     - \ 
     - \ 
     - Select the node/nodes to be romev from the graph (ex. A,B,C)
   * - ``-to``, ``--typeOutput``
     - Yes
     - \ 
     - \ 
     - matrix, edgelist, dot, sif
     - Output file type
   * - ``-fo``, ``--outputName``
     - Yes
     - \ 
     - \ 
     - \ 
     - Output file name (extension will be automatically assigned)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output (svg, png)
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same direcotry as the input file)

Examples
--------

Convert an edge-list to an adjacency matrix:

.. code-block:: bash

   python main.py convert \
       -t edgelist \
       -i ../dev/test/input/figure_8.egl \
       -to matrix \
       -fo figure_8_matrix \
       -o /tmp/out/

Convert adjacency matrix to SIF format:

.. code-block:: bash

   python main.py convert \
       -t matrix \
       -i ../dev/test/input/figure_8.txt \
       -to sif \
       -fo figure_8 \
       -o /tmp/out/

See :doc:`../../format/format` for supported format specifications.
