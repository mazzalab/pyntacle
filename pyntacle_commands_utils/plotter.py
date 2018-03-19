# external libraries

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
Utility to represent a graph into a plot that will be outputted by the pyntacle command line utils
"""
from config import *
from igraph import Graph, plot
import logging
import os
import random
from tools.graph_utils import GraphUtils as gu
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

    logger = None  # write logger to shell

    def __init__(self, graph: Graph, seed=None):
        """
        Initialize the plotter function by importing the graph and (optionally) defining a seed for custom graph
        reproducibility
        :param Graph graph: the input `igraph.Graph` object
        :param int seed: optionl: define a custom seed to reproduce the graph. plot. By default, a seed (1987) is stored
        """

        self.logger = log
        self.graph = graph.copy()  # creates a copy of the graph to work on
        self.utils = gu(graph=self.graph)
        self.utils.graph_checker()  # check that input graph is properly set

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("Instance ust be a seed")

            else:
                self.seed = seed #initialize seed
        else:
            self.seed = 1987 #use a special seed if it is not initialized

        # initialize parameters to be passed to the plot function
        self.node_labels = []
        self.edge_labels = []
        self.node_colours = []
        self.edge_widths = []
        self.layout = None
        self.node_shapes = []
        self.node_sizes = []
        self.edge_widths = []

    def set_node_label(self, labels: list):
        """
        Take a list corresponding to node properties (e.g.: a graph attribute) and assign it to the "label" function
        :param: list labels: a list of lables (must be strings)
        """

        for elem in labels:
            if not isinstance(elem, str):
                raise ValueError("label must be strings")

        if len(labels) < self.graph.vcount():
            self.logger.warning(
                "the labels specified does not cover all the node vertices, replacing missing labels with \"NA\"")
            diff = self.graph.vcount() - len(labels)
            labels = labels + "NA" * diff

        if len(labels) > self.graph.vcount():
            self.logger.warning("Labels specified exceeds the maximum number of vertices, slicing the labels list")
            labels = labels[:self.graph.vcount() - 1]

        self.node_labels = labels

    def set_edge_label(self, labels: list):
        """
        Take a list corresponding to edge properties (e.g.: a graph attribute) **[HUH?]**
        
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


    #todo sistema questo
    def set_layouts(self, layout="auto", **kwargs):
        """
        Define a series of layouts imported from the igraph package in order to plot a given geometry
        :param str layout: one of the following layouts: "circle",
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

    def set_node_colours(self, colours:dict, attribute=None):
        """
        Assign a series of colours stored in a dictionary (`param` **colours**) to the `ìgraph.plot` object
        :param colours: either a dictionary whose keys are graph attributes and the colours are either RGB or
        literal colour names e.g. {"vasco": "red"} with "vasco" being in self.graph.vs()["name"]
        or a list of the same lenght as number of node with colours inside
        :param attribute: if colours is a dictionary, must be specified
        """

        if isinstance(colours, dict):
            if attribute is not None:
                self.utils.attribute_in_nodes(attribute)
                values = self.graph.vs()[attribute]

            else:
                raise MissingAttributeError("attribute must be specified")

            '''
            check that the input values in the colour dictioary belong to the specified attribute
            '''
            for key in colours.keys():
                if key not in values:
                    raise KeyError("one of the key in the dictionary does not belong to the specified graph attribute.")

                if not isinstance(colours[key], str):
                    raise ValueError("colour codes must be string (either literal colour names or hex RGB")

            if len(colours.keys()) > len(values):
                raise ValueError(
                    "the number of attributes variable specified is greater than the total number of values for that "
                    "attribute")

            self.node_colours = [colours[attr] for attr in values]

        elif isinstance(colours, list):
            if len(colours) != self.graph.vcount():
                raise ValueError("length of colour list must be equal to graph nodes number")

            for elem in colours:
                if not isinstance(elem, str):
                    raise ValueError("colour list must be made of strings")

            self.node_colours = colours

        else:
            raise WrongArgumentError("colours must be either a dictionary or a list, {} found".format(type(colours)))

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


            #check that the input values in the colour dictionary belong to the specified attribute
            for key in widths.keys():
                if key not in values:
                    raise KeyError("one of the key in the dictionary does not belong to the specified graph attribute.")

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

    def set_node_sizes(self, sizes, attribute=None):
        """
        Assign a series of sizes stored as a list r a dictionary
        
        :type widths: dict or list
        :param widths: either a dictionary whose keys are graph attributes and the widths are either integers or floats e.g. {"foo": 0.4} with "vasco" being in self.graph.vs()["name"] or a list of the same lenght as number of node with widths inside
        :param attribute: if colours is a dictionary, must be specified
        """

        if isinstance(sizes, dict):
            if attribute is not None:
                self.utils.attribute_in_nodes(attribute)
                values = self.graph.vs()[attribute]

            else:
                raise MissingAttributeError("attribute must be specified when sizes is a dictionary")
            '''
            check that the input values in the colour dictioary belong to the specified attribute
            '''
            for key in sizes.keys():
                if key not in values:
                    raise KeyError("one of the key in the dictionary does not belong to the specified graph attribute.")

                if not isinstance(sizes[key], (float, int)):
                    raise ValueError("sizes must be a float or integers")

            if len(sizes.keys()) > len(values):
                raise ValueError(
                    "the number of attributes variable specified is greater than the total number of values for that "
                    "attribute")

            self.node_sizes = [sizes[attr] for attr in values]

        elif isinstance(sizes, list):
            if len(sizes) != self.graph.vcount():
                raise ValueError("length of sizes list must be equal to graph nodes number")

            for elem in sizes:
                # print(sizes)
                # input()
                if not isinstance(elem, (float, int)) and elem <= 0:
                    raise ValueError("sizes must be either float or integers")

            self.node_sizes = sizes

        else:
            raise WrongArgumentError("colours must be either a dictionary or a list")

    def set_node_shapes(self, shapes, attribute=None):

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
