:orphan:


set
===

Specific usage
--------------
.. code-block:: console

   python3 main.py set union -t {fileType} -i {input_file} -i2 {input_file2}
   python3 main.py set intersection -t {fileType} -i {input_file} -i2 {input_file2}
   python3 main.py set difference -t {fileType} -i {input_file} -i2 {input_file2}

Subcommand summary
------------------

union
  Return a resulting merged graph of the original two networks, marking the common nodes among them along with their common connecting edges

intersection
  Return only the common nodes and their connecting edges among the two graphs of interest

difference
  Perform the difference between the two input graphs. NOTE: the difference among graphs is not reciprocal

Synopsis
--------
.. code-block:: console

   python3 main.py set <subcommand> [OPTIONS]


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
   * - ``subcommand``
     - Yes
     - \ 
     - \ 
     - union, intersection, difference
     - Select one the subfunctions right after set
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
   * - ``-i2``, ``--inputFile2``
     - Yes
     - str
     - \ 
     - \ 
     - Specify the second input file name (Use same format the first input file or use the 'convert' function if necessary)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output (svg, png)
   * - ``--no-plot``
     - No
     - bool
     - False
     - \ 
     - Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle's ``--no-plot``)
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same direcotry as the input file)

Examples
--------

Compute the union of two networks:

.. code-block:: bash

   python main.py set union \
       -t edgelist \
       -i network1.egl \
       -i2 network2.egl \
       -o /tmp/out/

Find the intersection (shared nodes and edges):

.. code-block:: bash

   python main.py set intersection \
       -t edgelist \
       -i network1.egl \
       -i2 network2.egl \
       -o /tmp/out/

Compute the difference (edges in network1 not in network2):

.. code-block:: bash

   python main.py set difference \
       -t edgelist \
       -i network1.egl \
       -i2 network2.egl \
       -o /tmp/out/
