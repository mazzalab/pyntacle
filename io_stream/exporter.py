__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software; you can use and redistribute it under
  the terms of the BY-NC-ND license as published by
  Creative Commons; either version 4 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  License for more details.

  You should have received a copy of the license along with this
  work. If not, see http://creativecommons.org/licenses/by-nc-nd/4.0/.
  """
"""
Export the `igraph.Graph` object into one of the pyntacle-supported formats
"""

from tools.misc.graph_routines import *
from tools.misc.io_utils import *
from config import *
import pandas as pd
import pickle

class PyntacleExporter:
    """ export your igraph/Pyntacle object to a text file in the following formats:
    *Adjacency Matrix
    *Edge List
    *Simple Interaction Format (SIF)
    *Dot file Format
    *Binary File
    """

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def AdjacencyMatrix(graph, output_file, sep="\t", header=True) -> None:
        """
        Export an igraph.Graph object as Adjacency Matrix. A valid path to a file must be provided and the directory
        that will store the file must be writeable. If the directory tree does not exist, it will be created.
        **WARNING** Node attributes will not be exported, for that, see the `export attributes` method in *REFERENCE*
        :param igraph.Graph graph: an `igraph.Graph` object obtained from Pyntacle. See `Pyntacle Minimum Requirements`
        for the object description.
        :param str output_file: a valid path to a file. If the directory is not specified, the current directory will be used.
        :param str sep: a string that will be used as separator to separate the values in the Adjacency Matrix.
        Default is `\t` (outputs a tab-separated file)
        :param bool header: if `True`(default) the node names (graph.vs["name"] attribute) will be written to rows and
        columns. If false, the node names will not be present and the sequence of values represented in the Adjacency
        Matrix will be ordered by the `index` attribute
        :return None
        """

        if not isinstance(sep, str):
            raise TypeError("`sep` must be a string, {} found".format(type(output_file).__name__))

        adjmatrix = list(graph.get_adjacency())

        if header:
            nameslist = [name for name in graph.vs()["name"]]
            adjmatrix = pd.DataFrame(adjmatrix, columns=nameslist)
            adjmatrix.insert(0, column='', value=nameslist)
            adjmatrix.to_csv(output_file, sep=sep, header=True, index=False)
        else:
            adjmatrix = pd.DataFrame(adjmatrix)
            adjmatrix.to_csv(path_or_buf=output_file, sep=sep, header=False, index=False)


        sys.stdout.write("Graph successfully exported to Adjacency Matrix at path: {}\n".format(os.path.abspath(output_file)))
        return None

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def EdgeList(graph, output_file, sep="\t", header=False) -> None:
        """
        Export an igraph.Graph object to an Edge List. A valid path to a file must be provided and the directory
        that will store the file must be writeable. If the directory tree does not exist, it will be created.
        **WARNING** Node attributes will not be exported, for that, see the `export attributes` method in *REFERENCE*
        :param igraph.Graph graph: an `igraph.Graph` object obtained from Pyntacle. See `Pyntacle Minimum Requirements`
        for the object description.
        :param str output_file: a valid path to a file. If the directory is not specified, the current directory will be used.
        :param str sep: a string that will be used as separator to separate the values in the Edge List.
        Default is `\t` (outputs a tab-separated file)
        :param header: if `True`, a generic header will be produced, separated by the `sep` value (e.g. NodeA\tNodeB)
        :return: None
        """

        if not isinstance(sep, str):
            raise TypeError("`sep` must be a string, {} found".format(type(output_file).__name__))

        adjlist = list(graph.get_adjlist())
        with open(output_file, "w") as outfile:

            if header:
                outfile.write("NodeA\tNodeB\n")

            for i, ver in enumerate(adjlist):
                if not header:
                    #outfile.writelines([str(i) + sep + str(x) + "\n" for x in adjlist[i]])
                    outfile.writelines([sep.join([str(i),str(x)]) + "\n" for x in adjlist[i]])
                else:
                    outfile.writelines([sep.join([graph.vs(i)["name"][0], x]) + "\n" for x in graph.vs(ver)["name"]])
                    
        sys.stdout.write("Graph successfully exported to Adjacency Matrix at path: {}\n".format(
            os.path.abspath(output_file)))
        return None

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def Binary(graph, output_file):
        """
        Export an `igraph.Graph` object to a binary file that can be reopened using the `pickle` library.
        :param igraph.Graph graph: an `igraph.Graph` object obtained from Pyntacle. See `Pyntacle Minimum Requirements`
        for the object description.
        :param str output_file: a valid path to a file. If the directory is not specified, the current directory will be used.
        :return: None
        """
        pickle.dump(graph, open(output_file, "wb"))
        sys.stdout.write("Graph successfully exported to Binary file at path: {}\n".format(
            os.path.abspath(output_file)))

        return None

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def Sif(graph, output_file, sep="\t", header=False):
        """
        Write an igraph.Graph object to a Simple Interaction File format (SIF) useful for visualization and parsing using
        external tools, like Cytoscape.
        **WARNING** Node attributes will not be exported, sauf for the reserved attributes "__sif_interaction_name" (Graph)
        and "__sif_interaction (edges), for exporting other attributes, see the `export attributes` method in *REFERENCE*
        :param igraph.Graph graph: an `igraph.Graph` object obtained from Pyntacle. See `Pyntacle Minimum Requirements`
        for the object description.
        :param str output_file: a valid path to a file. If the directory is not specified, the current directory will be used.
        :param str sep: a string that will be used as separator to separate the values in the SIF file.
        Default is `\t` (outputs a tab-separated file)
        :param header: if `True`, it searches for the reserved attributes "__sif_interaction_name" in graph attributes
        and for "__sif_interaction" in edge attributes and  writes them to file if the attributes are filled.
        Otherwise, reports a generic attribute and the "interacts_with" interaction to the SIF file.
        :return: None
        """

        if not isinstance(sep, str):
            raise TypeError("`sep` must be a string, {} found".format(type(output_file).__name__))

        with open(output_file, "w") as outfile:

            if header:

                if "__sif_interaction_name" not in graph.attributes() or graph["__sif_interaction_name"] is None:
                    head = "\t".join(["Node1", "Interaction", "Node2"]) + "\n"

                else:
                    head = "\t".join(["Node1", graph["__sif_interaction_name"], "Node2"]) + "\n"

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

                    if edge["__sif_interaction"] is None:

                        outfile.write(sep.join([graph.vs(source)["name"][0], "interacts_with",
                                                graph.vs(target)["name"][0]]) + "\n")

                    else:
                        for i in edge["__sif_interaction"]:
                            outfile.write(sep.join([graph.vs(source)["name"][0], i,
                                                    graph.vs(target)["name"][0]]) + "\n")

                else:
                    # print(type(self.graph.vs(edge.target)["name"]))
                    raise ValueError(
                        "node \"name\" attribute is unproperly formatted. Cannot interpret him. Quitting")

            # remove vertices from graph in order to write remaining vertices
            remaining_nodes = list(set(graph.vs().indices) - set(nodes_done_list))

            for i in remaining_nodes:
                outfile.write(graph.vs(i)["name"][0] + "\n")

        sys.stdout.write("Graph successfully exported to SIF at path: {}\n".format(
            os.path.abspath(output_file)))
        return None

    @staticmethod
    @check_graph_consistency
    @output_file_checker
    def Dot(graph, output_file):
        """
        Write the igraph.Graph object to a Dot file. For the Dot file specifications, see https://www.graphviz.org/doc/info/lang.html.
        Dot is often used by third party tools such as GraphViz to import the network. Here, we wraps the `write_dot` function of igraph.
        **WARNING** this feature is experimental so handle it with care
        **WARNING** Node attributes will not be exported, for that, see the `export attributes` method in *REFERENCE*
        :param igraph.Graph graph: an `igraph.Graph` object obtained from Pyntacle. See `Pyntacle Minimum Requirements`
        for the object description.
        :param str output_file: a valid path to a file. If the directory is not specified, the current directory will be used.
        :return: None
        """
        Graph.write_dot(graph, f=output_file)
        sys.stdout.write("Graph successfully exported to DOT at path: {}\n".format(
            os.path.abspath(output_file)))

        return None