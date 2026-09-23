:orphan:


extract
=======

Extract returns components or subgraphs derived from the input network.

Specific usage:

.. code-block:: console

   python3 main.py extract -t {fileType} -i {input_file} -l
   python3 main.py extract -t {fileType} -i {input_file} -n {NCOMPONENTS}
   python3 main.py extract -t {fileType} -i {input_file} -l -n {NCOMPONENTS}
   python3 main.py extract -t {fileType} -i {input_file} -sc {SELECTCOMPONENT} -nl {node_list}

Synopsis
--------
.. code-block:: console

   python3 main.py extract [OPTIONS]


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
   * - ``-n``, ``--ncomponents``
     - No
     - bool
     - False
     - \ 
     - number of components
   * - ``-l``, ``--largest``
     - No
     - bool
     - False
     - \ 
     - Largest component of the graph
   * - ``-sc``, ``--selectComponent``
     - No
     - bool
     - False
     - \ 
     - Node/Nodes of the graph (ex. A,B,C)
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same direcotry as the input file)
   * - ``-f``, ``--format``
     - No
     - str
     - svg
     - \ 
     - Specify the format of the image output
   * - ``-nl``, ``--nodeList``
     - No
     - bool
     - False
     - \ 
     - Select the components that contain the given node/nodes (ex. A,B,C)
