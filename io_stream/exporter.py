__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """


from config import *
import pandas as pd
import pickle
from igraph import Graph
from internal.graph_routines import check_graph_consistency
from internal.io_utils import output_file_checker

class PyntacleExporter:
    r""" A series of static methods to export a :py:class:`igraph.Graph` object to one of the Pyntacle `supported file formats <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html>`_:

    * Adjacency Matrix
    * Edge List
    * Simple Interaction Format (SIF)
    * Dot file Format
    * Binary File
    """

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def AdjacencyMatrix(graph: Graph, file: str, sep: str ="\t", header: bool=True) -> None:
        r"""
        Exports a py:class`igraph.Graph` object to an Adjacency Matrix. A valid path to a file must be provided and the
        directory that will store the file must be writeable. If the directory tree does not exist, it will be created.
        We refer the user to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#adjm>`_
        for more details on how adjacency matrices are handled by Pyntacle.

        .. warning:: any attribute of the :py:class:`igraph.Graph` will not be exported, as the format does not allow porting of attributes. We recomment using the :class:`~pyntacle.io_stream.export_attributes.ExportAttributes` class for exporting the attribute(s) of interest

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str file: a valid path to a file. If the directory is not specified, the current directory will be used. If the path points to a nonexistent directory tree, it will be created.
        :param str sep: a string that will be used as separator to separate the values in the Adjacency Matrix. Default is ``\t`` (outputs a tab-separated file).
        :param bool header: if ``True``(default) the node names (the vertex ``name`` attribute) will be written in both rows and columns. If ``False``, the node names will not be present and the sequence of values represented in the Adjacency Matrix will be ordered by vertex ``index``

        :return None: None
        """

        if not isinstance(sep, str):
            raise TypeError(u"`sep` must be a string, {} found".format(type(file).__name__))

        adjmatrix = list(graph.get_adjacency())

        if header:
            nameslist = [name for name in graph.vs()["name"]]
            adjmatrix = pd.DataFrame(adjmatrix, columns=nameslist)
            adjmatrix.insert(0, column='', value=nameslist)
            adjmatrix.to_csv(file, sep=sep, header=True, index=False)
        else:
            adjmatrix = pd.DataFrame(adjmatrix)
            adjmatrix.to_csv(path_or_buf=file, sep=sep, header=False, index=False)

        sys.stdout.write(u"Graph successfully exported to adjacency matrix at full path:\n{}\n".format(os.path.abspath(file)))

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def EdgeList(graph: Graph, file, sep: str="\t", header: bool=False) -> None:
        r"""
        Exports a py:class:`igraph.Graph` object to an undirect  edge list. We refer the user to the
        `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#egl>`_
        for more details on the nature of edge lists and how they are handled by Pyntacle.
        A valid path to a file must be provided and the directory that will store the file must be writeable.
        If the directory tree does not exist, it will be created.

        .. warning:: any attribute of the :py:class:`igraph.Graph` will not be exported, as the format does not allow porting of attributes. We recomment using the :class:`~pyntacle.io_stream.export_attributes.ExportAttributes` class for exporting the attribute(s) of interest

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str file: a valid path to a file. If the directory is not specified, the current directory will be used.
        :param str sep: a string that will be used as separator to separate the values in the edge list. Default is ``\t`` (standard tabulation character)
        :param bool header: if ``True``, a generic header will be produced (e.g. **NodeA\tNodeB**)

        :return None: None
        """

        if not isinstance(sep, str):
            raise TypeError(u"`sep` must be a string, {} found".format(type(file).__name__))

        adjlist = list(graph.get_adjlist())

        with open(file, "w") as outfile:

            if header:
                outfile.write("NodeA\tNodeB\n")

            for i, ver in enumerate(adjlist):
                if not header:
                    #outfile.writelines([str(i) + sep + str(x) + "\n" for x in adjlist[i]])
                    outfile.writelines([sep.join([str(i),str(x)]) + "\n" for x in adjlist[i]])
                else:
                    outfile.writelines([sep.join([graph.vs(i)["name"][0], x]) + "\n" for x in graph.vs(ver)["name"]])
                    
        sys.stdout.write(u"Graph successfully exported to edge list at full path:\n{}\n".format(
            os.path.abspath(file)))

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def Binary(graph: Graph, file: str) -> None:
        r"""
        Exports an `igraph.Graph` object to a binary file that contains the :py:class:`igraph.Graph` object. This binary
        file can be later reopened in Python by means of the `pickle <https://docs.python.org/3.5/library/pickle.html>`_
        library

        .. warning:: if any of the :py:class:`igraph.Graph` attributes contain multi-dimensional objects (e.g. :py:class:`class` es) the binary cannot be opened in a Pynthon environment unless the object is first declared.

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str file: a valid path to a file. If the directory is not specified, the current directory will be used.

        :return None: None

        :raise TypeError: if ``sep`` is not a valid string separator
        """

        pickle.dump(graph, open(file, "wb"))
        sys.stdout.write(u"Graph successfully exported to binary at full path:\n{}\n".format(
            os.path.abspath(file)))

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def Sif(graph: Graph, file: str, sep: str="\t", header: bool=False) -> None:
        r"""
        Writes a :py:class:`igraph.Graph` object to a Simple Interaction File (SIF), a flexible network file format used
        by many other network analysis and visualization tools, such as `Cytoscape <https://cytoscape.org>`_.
        For more information on how Pyntacle handles the SIF format, please refer to the `File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#sif>`_
        of the Pyntacle official page.

        .. note:: SIF is a flexible file format, in which the column order is generally not important. Pyntacle limits this flexibility by always reporting the source node in the 1st column, the interaction type in the 2nd column and the target node in the 3rd column.

        .. warning:: any attribute of the :py:class:`igraph.Graph` will not be exported, as the format does not allow the  porting of attributes. We recomment using the :class:`~pyntacle.io_stream.export_attributes.ExportAttributes` class for exporting the attribute(s) of interest

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str file: a valid path to a file. If the directory is not specified, the current  working directory will be used.
        :param str sep: a string that will be used to separate the fields within the SIF. Default is ``\t`` (tabular character)
        :param bool header: if ``True``, it searches for the reserved graph attributes ``sif_interaction_name`` and use it to write the header of the SIF.

        :raise TypeError: if ``sep`` is not a valid string separator
        """

        if not isinstance(sep, str):
            raise TypeError(u"`sep` must be a string, {} found".format(type(file).__name__))

        with open(file, "w") as outfile:

            if header:

                if "sif_interaction_name" not in graph.attributes() or graph["sif_interaction_name"] is None:
                    head = "\t".join(["Node1", "Interaction", "Node2"]) + "\n"

                else:
                    head = "\t".join(["Node1", graph["sif_interaction_name"], "Node2"]) + "\n"

                outfile.write(head)

            # keep  track of the connected indices
            nodes_done_list = []

            for edge in graph.es():

                if "name" in graph.vs.attributes() or len(graph.vs(edge.source)["name"]) == 1 or len(
                        graph.vs(edge.target)["name"]) == 1:
                    source = edge.source
                    target = edge.target

                    if source not in nodes_done_list:
                        nodes_done_list.append(source)

                    if target not in nodes_done_list:
                        nodes_done_list.append(target)

                    if edge["sif_interaction"] is None:

                        outfile.write(sep.join([graph.vs(source)["name"][0], "interacts_with",
                                                graph.vs(target)["name"][0]]) + "\n")

                    else:
                        for i in edge["sif_interaction"]:
                            outfile.write(sep.join([graph.vs(source)["name"][0], i,
                                                    graph.vs(target)["name"][0]]) + "\n")

                else:
                    # print(type(self.graph.vs(edge.target)["name"]))
                    raise ValueError(
                        u"node 'name' attribute is improperly formatted. Cannot interpret him. Quitting")

            # remove vertices from graph in order to write remaining vertices
            remaining_nodes = list(set(graph.vs().indices) - set(nodes_done_list))

            for i in remaining_nodes:
                outfile.write(graph.vs(i)["name"][0] + "\n")

        sys.stdout.write(u"Graph successfully exported to SIF at full path:\n{}\n".format(
            os.path.abspath(file)))

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def Dot(graph: Graph, file: str) -> None:
        r"""
        Writes the igraph.Graph object to a Dot file.  Dot is a network file format designed for network visualization
        by `GraphViz <https://www.graphviz.org/>`_ and other tools to trustfully reproduce network properties graphically .

        The main documentation on Dot can be found `here <https://www.graphviz.org/doc/info/lang.html>`_

        .. note:: This method is a wrapper of the py:class:`~igraph.Graph.write_dot` method in igraph method of igraph

        .. warning:: the attributes of the py:class:`igraph.Graph` object may not be exported correctly. for this reason, we recommend to export these attributes externally by means of the :class:`~pyntacle.io_stream.export_attributes.ExportAttributes` module

        :param igraph.Graph graph: a :class:`igraph.Graph` object. The graph must satisfy a series of requirements, described in the `Minimum requirements specifications <http://pyntacle.css-mendel.it/requirements.html>`_ section of the Pyntacle official page.
        :param str file: a valid path to a file. If the directory is not specified, the current  working directory will be used.

        """
        Graph.write_dot(graph, f=file)
        sys.stdout.write(u"Graph successfully exported to DOT at full path:\n{}\n".format(
            os.path.abspath(file)))
