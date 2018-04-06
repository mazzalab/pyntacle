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
import datetime
from igraph import Graph, plot
import os
import random
from tools.graph_utils import GraphUtils as Gu
from importlib import util

pycairo_check = util.find_spec("cairo")
if pycairo_check is None:
    raise EnvironmentError("pyntacle needs the pycairo library to be installed and available "
                           "in order to produce plots. Please install it and try again.")

class PlotGraph():
    """
    This method prepare the igraph.Graph object to be plotted into a file into several formats, by setting proper
    attributes defined by igraph and by defining other external properties such as layouts.
    """
    logger = None

    def __init__(self, graph: Graph, seed=None):
        """
        Initialize the plotter function by importing the graph and (optionally) defining a seed for custom graph
        reproducibility. Will not touch the input `igraph.Graph`, that will  therefore be copied.
        :param Graph graph: the input `igraph.Graph` object. Will be copied into this method in order to preserve the integrity of the input graph
        :param int seed: optionl: define a custom seed to reproduce the graph. plot. By default, a seed (1987) is stored
        """

        self.logger = log

        self.graph = graph.copy()  # creates a copy of the graph to work on
        self.utils = Gu(graph=self.graph)
        self.utils.graph_checker()  # checks that input graph is properly set

        if seed is not None:
            if not isinstance(seed, int):
                raise TypeError("Seed must be an integer")

            else:
                self.seed = seed  # initialize seed
        else:
            self.seed = 1987  # use a special seed if it is not initialized

        self.layout = None #will be replaced by the layout function

    def set_node_labels(self, labels: list):
        """
        Take a list corresponding to node labels that you want to represent in the plot (e.g., node ["name"] attribute)
        and assign it to the "label" attribute in order to be recognized by the `igraph.plot` function.
        **WARNING if a node attribute named "label" exists, will be cancelled and overwritten.
        **WARNING** the labelling is positional, so the first item in `labels` should match the first node, the second
        label the second node, and so on.
        **WARNING** if the `labels` list is shorter than the total number of nodes, remaining nodes won't have a label
        in plot. On the other hand, if the list is longer, it wil be sliced.
        :param: list labels: a list of node labels (must be strings)
        """

        if "label" in self.graph.vs.attributes():
            self.logger.warning("attribute \"label\" already exists, will overwrite")
            self.graph.vs()["label"] = None

        if not isinstance(labels, list):
            raise TypeError("\"labels\" must be a list, {} found".format(type(labels).__name__))

        if not all(isinstance(x, str) for x in labels):
            raise ValueError("One of the items in \"labels\" is not a string")

        tot = self.graph.vcount()

        if len(labels) < tot:
            self.logger.warning(
                "\"labels\" do not cover all the edges, replacing missing ones with Nonetype")

        if len(labels) > tot:
            self.logger.warning("Labels specified exceeds the maximum number of vertices, slicing the input list to the total number of nodes")
            labels = labels[:self.graph.vcount()]

        self.graph.vs["label"] = labels

    def set_node_colors(self, colors: list):
        """
        Take a list corresponding to node colors. (either the literal name, e.g. "white" or the RGB color e.g.#F0000)
        that you want to represent in the plot and assign it to the "color"  node attribute  in the `igraph.Graph` object
        in order to be recognized by the `igraph.plot` function.
        **WARNING if a node attribute named "color" exists, will be cancelled and overwritten.
        **WARNING** the coloring is positional, so the first item in `colors`should match the first node, the second
        label the second node, and so on.
        **WARNING** if the `colors` list is shorter than the total number of nodes, remaining nodes won't be colored
        in plot (defaul is "red"). On the other hand, if the list is longer, it wil be sliced.
        :param: list colors: a list of node colors (must be strings)
        """

        if "color" in self.graph.vs.attributes():
            self.logger.warning("attribute \"color\" already exists, will overwrite")
            self.graph.vs()["color"] = None

        if not isinstance(colors, list):
            raise TypeError("\"colors\" must be a list, {} found".format(type(colors).__name__))

        if not all(isinstance(x, str) for x in colors):
            raise ValueError("One of the items in \"colors\" is not a string")

        tot = self.graph.vcount()

        if len(colors) < tot:
            self.logger.warning(
                "\"colors\" do not cover all the edges, replacing missing ones with Nonetype")

        if len(colors) > tot:
            self.logger.warning("\"colors\" exceed the maximum number of vertices, slicing the input list to the total number of nodes")
            colors = colors[:self.graph.vcount()]

        self.graph.vs["color"] = colors

    def set_node_sizes(self, sizes: list):
        """
        Take a list corresponding to node sizes. (positive float or integers)
        that you want to represent in the plot and assign it to the "size"  node attribute  in the `igraph.Graph` object
        in order to be recognized by the `igraph.plot` function.
        **WARNING if a node attribute named "size" exists, will be cancelled and overwritten.
        **WARNING** the sizing is positional, so the first item in `sizes`should match the first node, the second
        label the second node, and so on.
        **WARNING** if the `sizes` list is shorter than the total number of nodes, remaining nodes will. have the default
        size. On the other hand, if the list is longer, it wil be sliced.
        :param: list sizes: a list of node sizes (must be positive integers or floats)
        """
        if "size" in self.graph.vs.attributes():
            self.logger.warning("attribute \"size\" already exists, will overwrite")
            self.graph.vs()["size"] = None

        if not isinstance(sizes, list):
            raise TypeError("\"sizes\" must be a list, {} found".format(type(sizes).__name__))

        if not all(isinstance(x, (int, float)) and x > 0 for x in sizes):
            raise ValueError("One of the items in \"sizes\" is not positive integer or float")

        tot = self.graph.vcount()

        if len(sizes) < tot:
            self.logger.warning(
                "\"sizes\" do not cover all the edges, replacing missing ones with Nonetype")

        if len(sizes) > tot:
            self.logger.warning("\"sizes\" specified exceed the maximum number of vertices, slicing the input list to the total number of nodes")
            sizes = sizes[:self.graph.vcount()]

        self.graph.vs["size"] = sizes

    def set_node_shapes(self, shapes:list):
        """
        Take a list corresponding to node shapes in order to assign it to the "shape" node attribute, so it will be
        recognized by the `igraph.plot` object. Available shapes that will be plotted are:
        **rectangle*
        **circle*
        **triangle-up*
        **triangle-down*
        **square*
        **hidden* (node won't be shown)
        other values are not supported.
        **WARNING if a node attribute named "shapes" exists, will be cancelled and overwritten
        **WARNING** the node shaping is assigned positionally, so the first item in "shapes" should match the first node,
        the second shape the second node, and so on. Will raise a warning if the two list are not of the same length,
        and slice the list if it's too long.
        :param: list shapes: a list of node shapes (must be strings)
        """

        shapes_legal_values = ["rectangle", "circle", "hidden", "triangle-up", "triangle-down", "square"]

        if "shape" in self.graph.vs.attributes():
            self.logger.warning("attribute \"shape\" already exists, will overwrite")
            self.graph.vs()["shape"] = None

        if not isinstance(shapes, list):
            raise TypeError("\"shapes\" must be a list, {} found".format(type(shapes).__name__))

        if not all(isinstance(x, str) for x in shapes):
            raise ValueError("One of the items in \"shapes\" is not a string")

        if not all(x in shapes_legal_values for x in shapes):
            raise ValueError("One of the items in \"shapes\" does not match the available options (\"{}\")".format(",".join(shapes_legal_values)))

        tot = self.graph.vcount()

        if len(shapes) < tot:
            self.logger.warning(
                "\"shapes\" do not cover all the nodes, replacing missing ones with Nonetype")

        if len(shapes) > tot:
            self.logger.warning("\"shapes\" specified exceed the maximum number of vertices, slicing the input list to the total number of nodes")
            shapes = shapes[:self.graph.vcount()]

        self.graph.vs["shape"] = shapes

    def set_edge_label(self, labels: list):
        """
        Take a list corresponding to edge labels that you want to represent in the plot (e.g., edge ["name"] attribute,
        if present) and assign it to the "label" edge attribute in order to be recognized by the `igraph.plot` function.
        **WARNING if an edge attribute named "labels" exists, will be cancelled and overwritten
        **WARNING** the labelling is positional, so the first item in `labels` should match the first edge, the second
        edge the second node, and so on.
        **WARNING** if the `labels` list is shorter than the total number of edges, remaining edges won't have a label
        in plot. On the other hand, if the list is longer, it wil be sliced.
        :param: list labels: a list of edge labels (must be strings)
        """

        if "label" in self.graph.es.attributes():
            self.logger.warning("attribute \"label\" already exists, will overwrite")
            self.graph.es()["label"] = None

        if not isinstance(labels, list):
            raise TypeError("\"labels\" must be a list, {} found".format(type(labels).__name__))

        if not all(isinstance(x, (str)) for x in labels):
            raise ValueError("One of the items in \"labels\" is not a string")

        tot = self.graph.ecount()

        if len(labels) < tot:
            self.logger.warning(
                "\"labels\" do not cover all the nodes, replacing missing ones with Nonetype")

        if len(labels) > tot:
            self.logger.warning("\"labels\" specified exceed the maximum number of vertices, slicing the input list")
            labels = labels[:self.graph.ecount()]

        self.graph.es["label"] = labels

    def set_edge_widths(self, widths: list):
        """
        Take a list if positive floats or integers  and  assign it to the corresponding edges
        **WARNING if an edge attribute named "widths" exists, will be cancelled and overwritten
        **WARNING** the width assignment is positional, so the first item in `widths` should match the first edge,
        the second width the second edge, and so on.
        **WARNING** if the `widhts` list is shorter than the total number of edges, remaining edges won't have a label
        in plot. On the other hand, if the list is longer, it wil be sliced.
        """

        if "width" in self.graph.es.attributes():
            self.logger.warning("attribute \"width\" already exists, will overwrite")
            self.graph.es()["width"] = None

        if not isinstance(widths, list):
            raise TypeError("\"widths\" must be a list, {} found".format(type(widths).__name__))

        if not all(isinstance(x, (int, float)) and x > 0 for x in widths):
            raise ValueError("One of the items in \"widths\" is not a positive integer or float")

        tot = self.graph.ecount()

        if len(widths) < tot:
            self.logger.warning(
                "\"widths\" do not cover all the edges, replacing missing ones with Nonetype")

        if len(widths) > tot:
            self.logger.warning("\"widths\" specified exceed the maximum number of vertices, slicing the input list to the total number of edges")
            widths = widths[:self.graph.ecount()]

        self.graph.es["width"] = widths

    def set_layouts(self, layout="fruchterman_reingold", **kwargs):
        """
        Define a series of layouts imported from the igraph package in order to plot a given geometry
        :param str layout: one of the following layouts:
        *"circle": circular layout
        *"auto": automatic implementation, chosen by default by `igraph` using node density at a proxy,
        *"fruchterman_reingold"/"fr": force directed, useful for scale free graphs
        *"kamada_kawai"/"kk" (force directed), "large_graph"/"lgl",
        *"random", assign the node and the edges randomly in space
        *"reingold_tilford","rt". useful for tree representation.
        By Default, "fruchterman_reingold" is selected.
        :param str layout: a type of layout that will be assigned to the `layout` parameter in the `igraph.plot` object
        :param kwargs: a list of parameters that can be passed to each of the layout method
        """
        try:

            layout_dic = {"auto": Graph.layout_auto(self.graph, **kwargs), "circle": Graph.layout_circle(self.graph, **kwargs),
                          "fruchterman_reingold": Graph.layout_fruchterman_reingold(self.graph, self.seed, **kwargs),
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
        Plot graph to a specific file. Available formats: "jpg", "pdf", "svg", "png"
        :param path: optional - a path in which results will be plotted (deafulat is the current working directory)
        '''

        formats = ["jpg", "pdf", "svg", "png"]

        if path is None:
            now = datetime.datetime.now()
            now = now.strftime("%d-%m-%A_%H%M")
            path = os.path.join(os.getcwd(), "pyntacle_plot" + now + ".pdf")
            self.logger.info("plot will be stored as PDF at path {}".format(path))

        else:
            if os.path.splitext(path)[-1][1:] not in formats:
                raise ValueError("Format not accepted. Available formats are {}".format(",".join(formats)))

        visual_style = {}  # empty tuple that will contain all the preiously instanced parameters
        if self.layout is not None:
            visual_style["layout"] = self.layout

        additional_params = ["bbox", "margin", "edge_curved", "vertex_label_size", "vertex_frame_color", "keep_aspect_ratio"]

        if kwargs:
            for key in kwargs:
                if key not in additional_params:
                    raise KeyError("param {} cannot be specified".format(key))
                else:
                    visual_style[key] = kwargs[key]
        
        plot(self.graph, **visual_style, target=path)

    def get_graph(self):
        """
        Returns the modified `igraph.Graph` object
        :return Graph: the igraph.Graph object with the label added and used for plotting
        """
        return self.graph