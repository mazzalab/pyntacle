__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
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
Reserved utility to represent a graph into a plot that will be outputted by the pyntacle command line utils
"""

from config import *
from igraph import Graph, plot
import os
import random
from tools.graph_utils import GraphUtils as Gu
from importlib import util

pycairo_check = util.find_spec("cairo")
if pycairo_check is None:
    raise EnvironmentError("pyntacle needs the pycairo library to be installed and available "
                           "in order to produce plots. Please install it and try again.")
from exceptions.wrong_argument_error import WrongArgumentError

class PlotGraph():
    """
    This method creates a report according to the type of analysis run by pyntacle
    """
    logger = None

    def __init__(self, graph: Graph, seed=None):
        """
        Initialize the plotter function by importing the graph and (optionally) defining a seed for custom graph
        reproducibility
        :param Graph graph: the input `igraph.Graph` object
        :param int seed: optionl: define a custom seed to reproduce the graph. plot. By default, a seed (1987) is stored
        """

        self.logger = log

        self.graph = graph.copy()  # creates a copy of the graph to work on
        self.utils = Gu(graph=self.graph)
        self.utils.graph_checker()  # check that input graph is properly set

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("Seed must be an integer")

            else:
                self.seed = seed  # initialize seed
        else:
            self.seed = 1987  # use a special seed if it is not initialized

        # todo these will be erased once the methods are implemented
        # initialize parameters to be passed to the plot function
        self.edge_labels  = []
        self.edge_widths = []
        self.layout = None #will be replaced by the layout function
        self.node_shapes = []
        self.edge_widths = []

    def set_node_label(self, labels:list, attribute="node_label"):
        """
        Take a list corresponding to node properties (e.g.: a graph attribute) and assign it to the "label" function.
        **WARNING** the labelling is positional, so the first item in label should match the first node, the second
        label the second node, and so on. Will raise a warning if the two list are not of the same length, and slice
        the list if it's too long. Will also overwrite any attribute that matches the "attribute" parameter.
        :param: list labels: a list of node labels (must be strings)
        :param str attribute: a vertex attribute on which the node labels will be mapped to
        """

        if not isinstance(attribute, str):
            raise TypeError("\"attribute\" must be a string")

        if attribute in self.graph.attributes():
            self.logger.warning("attribute {} already exists, will overwrite".format(attribute))
            self.graph.vs()[attribute] = None

        if not isinstance(labels, list):
            raise TypeError("\"labels\" must be a string, {} found".format(type(labels).__name__))

        if not all(isinstance(x, str) for x in labels):
            raise ValueError("One of the items in \"labels\" is not a string")

        if len(labels) < self.graph.vcount():
            self.logger.warning(
                "the labels specified does not cover all the node vertices, replacing missing labels with Nonetype")

        if len(labels) > self.graph.vcount():
            self.logger.warning("Labels specified exceeds the maximum number of vertices, slicing the labels list")
            labels = labels[:self.graph.vcount()]

        self.graph.vs[attribute] = labels

    #todo rifai
    def set_node_colors(self, colors: list, attribute="color"):
        """
        Take a list corresponding to node properties (e.g.: a graph attribute) and assign it to the "colors" pòasrameter
        in the `igraph.plot`.
        **WARNING** the labelling is positional, so the first item in "colors" should match the first node, the second
        label the second node, and so on. Will raise a warning if the two list are not of the same length, and slice
        the list if it's too long. Will also overwrite any attribute that matches the "attribute" parameter.
        :param: list colors: a list of node colors (must be strings)
        :param str attribute: a vertex attribute on which the node colors will be mapped to
        """

        if not isinstance(attribute, str):
            raise TypeError("\"attribute\" must be a string")

        if attribute in self.graph.attributes():
            self.logger.warning("attribute {} already exists, will overwrite".format(attribute))
            self.graph.vs()[attribute] = None

        if not isinstance(colors, list):
            raise TypeError("\"colors\" must be a string, {} found".format(type(colors).__name__))

        if not all(isinstance(x, str) for x in colors):
            raise ValueError("One of the items in \"colors\" is not a string")

        if len(colors) < self.graph.vcount():
            self.logger.warning(
                "the labels specified does not cover all the node vertices, replacing missing labels with Nonetype")

        if len(colors) > self.graph.vcount():
            self.logger.warning("Labels specified exceeds the maximum number of vertices, slicing the labels list")
            colors = colors[:self.graph.vcount()]

        self.graph.vs[attribute] = colors

    def set_node_sizes(self, sizes: list, attribute="size"):
    """
    Assign a series of sizes (positive floats or integers stored in a list) to the attribute specified in attribute
    :param sizes:  a list containing positive floats or integers. Ideally, this will match the total number of nodes in the graph. If not, the list will be sliced or some  node won't have the "attribute" filled
    :param str attribute: the name of the attribute in which the attribute will be stored.
    """

    if not isinstance(attribute, str):
        raise TypeError("\"attribute\" must be a string, {} found".format(type(attribute).__name__))

    if attribute in self.graph.attributes():
        self.logger.warning("attribute {} already exists, will overwrite".format(attribute))
        self.graph.vs()[attribute] = None

    if not isinstance(sizes, list):
        raise TypeError("\"sizes\" must be a list, {} found".format(type(sizes).__name__))

    else:
        if any(not isinstance(x, (float, int)) for x in sizes) and any( x < 0 for x in sizes):
            raise ValueError("one of the element in sizes is not a  positive float or integer")

    if len(sizes) < self.graph.vcount():
        self.logger.warning("The length of the \"sizes\" is less than the total number of nodes ({}), some nnodes will not be affected by this parameter".format(self.graph.vcount()))
    elif len(sizes) > self.graph.vcount:
        self.logger.warning(
            "The length of the \"sizes\" is greater than the total number of nodes ({}), slicing this list to the maximum number of nodes".format(self.graph.vcount()))
        sizes = sizes[:self.graph.vcount()]

    self.graph.vs()[attribute] = sizes

    def set_node_shapes(self, shapes, attribute="shape"):

        """
        **[EXPAND]**
        
        :param attribute:
        :param shapes:
        :return:
        """

        shapes_legal_values = ["rectangle", "circle", "hidden", "triangle-up", "triangle-down", "square"]

        if isinstance(shapes, dict):
            if attribute is not None:
                self.utils.attribute_in_nodes(attribute)
                values = self.graph.vs()[attribute]

            else:
                raise MissingAttributeError("attribute must be specified")

            '''
            check that the input values in the colour dictioary belong to the specified attribute
            '''
            for key in shapes.keys():
                if key not in values:
                    raise KeyError("one of the key in the dictionary does not belong to the specified graph attribute.")

                if not isinstance(shapes[key], str):
                    raise ValueError("shapes must be string")

                else:
                    shapes[key] = shapes[key].lower()

                if shapes[key] not in shapes_legal_values:
                    raise WrongArgumentError("{0} is not a legal shape. Legal shapes are {1}".format(shapes[key],
                                                                                                     ",".join(
                                                                                                         shapes_legal_values)))

            if len(shapes.keys()) > len(values):
                raise ValueError(
                    "the number of attributes variable specified is greater than the total number of values for that "
                    "attribute")

            self.node_shapes = [shapes[attr] for attr in values]

        elif isinstance(shapes, list):
            if len(shapes) != self.graph.vcount():
                raise ValueError("length of shapes list must be equal to graph nodes number")

            for elem in shapes:
                if not isinstance(elem, str):
                    raise ValueError("shapes list must be made of strings")
                if elem not in shapes_legal_values:
                    raise WrongArgumentError(
                        "{0} is not a legal shape. Legal shapes are {1}".format(elem, ",".join(shapes_legal_values)))

            self.node_shapes = shapes

        else:
            raise WrongArgumentError("colours must be either a dictionary or a list")

        # todo rifai
    def set_edge_widths(self, widths, attribute=None):
        """
        Assign a series of colours stored in a dictionary to the igraph plot, based on the attribute values

        :type widths: dict or list
        :param widths: either a dictionary whose keys are graph attributes and the widths are either integers or floats e.g. {"foo": 0.4} with "vasco" being in self.graph.vs()["name"] or a list of the same length as number of node with widths inside
        :param attribute: if colours is a dictionary, must be specified
        """

        if isinstance(widths, dict):
            if attribute is not None:
                self.utils.attribute_in_nodes(attribute)
                values = self.graph.es()[attribute]
            else:
                raise MissingAttributeError("attribute must be specified")

            # check that the input values in the colour dictionary belong to the specified attribute
            for key in widths.keys():
                if key not in values:
                    raise KeyError(
                        "one of the key in the dictionary does not belong to the specified graph attribute.")

                if not isinstance(widths[key], (float, int)):
                    raise ValueError("width must be floats or integers")

            if len(widths.keys()) > len(values):
                raise ValueError(
                    "the number of attributes variable specified is greater than the total number of values for that "
                    "attribute")

            self.edge_widths = [widths[attr] for attr in values]

        elif isinstance(widths, list):
            if len(widths) != self.graph.ecount():
                raise ValueError("length of widths list must be equal to graph nodes number")

            for elem in widths:
                if not isinstance(elem, (int, float)) and elem <= 0:
                    raise ValueError("widths list must be made either of positive floats or integers")

            self.edge_widths = widths

        else:
            raise WrongArgumentError("widths must be either a dictionary or a list")

    # todo rifai
    def set_edge_label(self, labels: list, attribute="edge_label"):
        """
        Take a list corresponding to edge properties (e.g.: an edge attribute) and  assign it to the corresponding edges
        **WARNING** the labelling is positional, so the first item in label should match the first edge, the second
        label the second edge, and so on. Will raise a warning if the two list are not of the same length.
        :param: labels: a list of lables (must be strings)
        """

        for elem in labels:
            if not isinstance(elem, str):
                raise ValueError("label must be strings")

        if len(labels) < self.graph.ecount():
            self.logger.warning(
                "the labels specified does not cover all the node vertices, replacing missing labels with \"NA\"")
            diff = self.graph.vcount() - len(labels)
            labels = labels + ["NA" * diff]

        if len(labels) > self.graph.ecount():
            self.logger.warning("Labels specified exceeds the maximum number of vertices, slicing the labels list")
            labels = labels[:self.graph.ecount() - 1]

        self.edge_labels = labels

    # todo rifai
    def set_edge_widths(self, widths, attribute=None):
        """
        Assign a series of colours stored in a dictionary to the igraph plot, based on the attribute values

        :type widths: dict or list
        :param widths: either a dictionary whose keys are graph attributes and the widths are either integers or floats e.g. {"foo": 0.4} with "vasco" being in self.graph.vs()["name"] or a list of the same length as number of node with widths inside
        :param attribute: if colours is a dictionary, must be specified
        """

        if isinstance(widths, dict):
            if attribute is not None:
                self.utils.attribute_in_nodes(attribute)
                values = self.graph.es()[attribute]
            else:
                raise MissingAttributeError("attribute must be specified")

            # check that the input values in the colour dictionary belong to the specified attribute
            for key in widths.keys():
                if key not in values:
                    raise KeyError(
                        "one of the key in the dictionary does not belong to the specified graph attribute.")

                if not isinstance(widths[key], (float, int)):
                    raise ValueError("width must be floats or integers")

            if len(widths.keys()) > len(values):
                raise ValueError(
                    "the number of attributes variable specified is greater than the total number of values for that "
                    "attribute")

            self.edge_widths = [widths[attr] for attr in values]

        elif isinstance(widths, list):
            if len(widths) != self.graph.ecount():
                raise ValueError("length of widths list must be equal to graph nodes number")

            for elem in widths:
                if not isinstance(elem, (int, float)) and elem <= 0:
                    raise ValueError("widths list must be made either of positive floats or integers")

            self.edge_widths = widths

        else:
            raise WrongArgumentError("widths must be either a dictionary or a list")

    def set_layouts(self, layout="auto", **kwargs):
        """
        Define a series of layouts imported from the igraph package in order to plot a given geometry
        :param str layout: one of the following layouts: "circle",
        :param dict **kwargs: option values that will be passed to the layout functions. Will raise an error if the params passed are illegal for the given layout
        "auto" (automatic implementation, choosen by default by igraph using node density at a proxy),
        "fruchterman_reingold"/"fr" (force directed),
        "kamada_kawai"/"kk" (force directed), "large_graph"/"lgl",
        "random",va
        "reingold_tilford",
        "rt" (for trees).
        Default is fruchterman_reingold
        :param kwargs: a list of parameters that can be passed to each of the layout method
        """

        try:
            layout_dic = {"auto": Graph.layout_auto(), "circle": Graph.layout_circle(self.graph, **kwargs),
                          "fruchterman_reingold": Graph.layout_fruchterman_reingold(self.graph, **kwargs),
                          "fr": Graph.layout_fruchterman_reingold(self.graph, **kwargs),
                          "kamada_kawai": Graph.layout_kamada_kawai(self.graph, **kwargs),
                          "kk": Graph.layout_kamada_kawai(self.graph, **kwargs),
                          "large_graph": Graph.layout_lgl(self.graph, **kwargs),
                          "lgl": Graph.layout_lgl(self.graph, **kwargs),
                          "random": Graph.layout_random(self.graph, **kwargs),
                          "reingold_tilford": Graph.layout_reingold_tilford(self.graph, **kwargs),
                          "rt": Graph.layout_reingold_tilford(self.graph, **kwargs)}

        except TypeError:
            raise KeyError("Invalid kwargs passed")

        if layout.lower() not in layout_dic.keys():
            raise KeyError("layout specified is not available")

        else:
            self.layout = layout_dic[layout.lower()]

    def plot_graph(self, path=None, **kwargs):
        '''
        Plot graph to a specific file, in several formats. Available formats: "jpg", "pdf", "svg", "png"
        
        :param path: optional - a path in which results will be plotted (deafulat is the current working directory)
        '''

        formats = ["jpg", "pdf", "svg", "png"]

        if path is None:
            path = os.path.join(os.getcwd(), "pyntacle_plot.pdf")

        else:
            if os.path.splitext(path)[-1][1:] not in formats:
                raise ValueError("Format not accepted. Available formats are {}".format(",".join(formats)))

        visual_style = {}  # empty tuple that will contain all the preiously instanced parameters
        if self.layout is not None:
            visual_style["layout"] = self.layout

        if self.node_labels:
            visual_style["vertex_label"] = self.node_labels

        if self.edge_labels:
            visual_style["edge_label"] = self.node_labels

        if self.edge_widths:
            visual_style["edge_width"] = self.edge_widths

        if self.node_sizes:
            visual_style["vertex_size"] = self.node_sizes

        if self.node_shapes:
            visual_style["vertex_shape"] = self.node_shapes

        if self.node_colours:
            visual_style["vertex_color"] = self.node_colours

        additional_params = ["bbox", "margin", "edge_curved", "vertex_frame_color", "keep_aspect_ratio",
                             "vertex_label_size"]

        for key in kwargs:

            if key not in additional_params:
                raise KeyError("param {} cannot be specified".format(key))
            else:
                visual_style[key] = kwargs[key]
        random.seed(self.seed)
        plot(self.graph, **visual_style, target=path)

    def get_graph(self):
        """
        Returns the modified `igraph.Graph` object
        :return Graph: the igraph.Graph object with the label added and used for plotting
        """
        return self.graph