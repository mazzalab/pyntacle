r"""
``io_stream`` is a module that sits at the interface between the outside world and Pyntacle. It handles the
import-export of several supported network file formats and ``igraph``, as well graph, node  or edge attributes that can
be added to the ``igraph.Graph`` object to enriches graph elements of additional layers of information. or can be ported
to external tools (i.e. `Cytoscape <https://cytoscape.org/>`_
Moreover, it provides a subset of utilities to convert quickly a file format without importing it into Pyntacle.
Finally, it produces simulated networks that follows several well-known topologies by wrapping some of the :py:class:`igraph`
network generators into comfortable utilities that initialize them for Pyntacle usage and testing.

For a more comprehensive view on the supported network file format, please visit the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html>`_
on the Pyntacle official page, that is regularly updated and shows examples for each file format.

The module is organized as follows:

* :class:`~pyntacle.io_stream.importer`: Import a network file and transform it into an ``igraph.Graph`` object that is compliant to Pyntacle `Minimum Requirements <http://pyntacle.css-mendel.it/requirements.html>`_
* :class:`~pyntacle.io_stream.exporter`: Export an ``igraph.Graph` object into one of the supported file formats
* :class:`~pyntacle.io_stream.converter`: Quickly converts a network file formats into another
* :class:`~pyntacle.io_stream.generator`: Generates simulated network that follows one of the following topologies:

    * `random <https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93R%C3%A9nyi_model>`_
    * `scale-free <https://en.wikipedia.org/wiki/Barab%C3%A1si%E2%80%93Albert_model>`_
    * `small-world <https://en.wikipedia.org/wiki/Watts%E2%80%93Strogatz_model>`_
    * `tree <https://en.wikipedia.org/wiki/Tree_(graph_theory)>`_

* :class:`~pyntacle.io_stream.import_attributes`: Import network attributes for graph, nodes and edges and adds them to the ``igraph.Graph`` object
* :class:`~pyntacle.io_stream.export_attributes`: Export network attributes into tab-delimited file or some formats compliant with Cytoscape requirements.

"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
