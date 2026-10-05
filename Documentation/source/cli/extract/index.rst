:orphan:


extract
=======

Extract writes part of a fragmented network: one or more of its connected
components, ranked by size.

Specific usage:

.. code-block:: console

   pyntacle extract -t {fileType} -i {input_file} -l            # the largest component
   pyntacle extract -t {fileType} -i {input_file} -l -n N       # the N largest components
   pyntacle extract -t {fileType} -i {input_file} -n N          # all but the N smallest components
   pyntacle extract -t {fileType} -i {input_file} -sc N         # the N-th largest component
   pyntacle extract -t {fileType} -i {input_file} -nl A,B       # the components holding A or B

Components of equal size are ranked by their first node in the input. A
request the network cannot satisfy (``-sc`` beyond the number of components,
a node not in the network) stops with an error.

Output
------

In the output directory (``-o``, or the folder of the input file):

- ``<input>_extract_<selection>.<ext>`` — the extracted network, in the input
  format; ``<selection>`` is ``largest_component``, ``largest_subgraphs``,
  ``removed_subgraphs``, ``selected_subgraph`` or ``selected_by_nodes``;
- ``report_<input>_extract_<selection>.tsv`` — one row per node with its
  component (1 = the largest) and degree;
- a figure of the result, unless ``--no-plot`` is given.

Synopsis
--------
.. code-block:: console

   pyntacle extract [OPTIONS]


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
     - Column separator of the input file (ex. ','); detected automatically if omitted
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
     - Select the node/nodes to be removed from the graph (ex. A,B,C)
   * - ``-n``, ``--ncomponents``
     - No
     - bool
     - False
     - \ 
     - With -l: keep the N largest components. Alone: drop the N smallest components
   * - ``-l``, ``--largest``
     - No
     - bool
     - False
     - \ 
     - Keep the largest component (with -n, the N largest)
   * - ``-sc``, ``--selectComponent``
     - No
     - bool
     - False
     - \ 
     - Keep the N-th largest component (1 = the largest)
   * - ``--no-plot``
     - No
     - bool
     - False
     - \ 
     - Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written
   * - ``-o``, ``--outdir``
     - No
     - str
     - \ 
     - \ 
     - Select where to store the output (if not specified the output will be stored in same directory as the input file)
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

Examples
--------

Extract only the largest connected component:

.. code-block:: bash

   pyntacle extract \
       -t edgelist \
       -i fragmented_network.egl \
       -l \
       -o /tmp/out/

Extract the top 3 largest components:

.. code-block:: bash

   pyntacle extract \
       -t edgelist \
       -i fragmented_network.egl \
       -l -n 3 \
       -o /tmp/out/

Extract the component containing a specific node:

.. code-block:: bash

   pyntacle extract \
       -t edgelist \
       -i fragmented_network.egl \
       -nl KR \
       -o /tmp/out/
