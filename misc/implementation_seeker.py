__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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

from config import *
from misc.enums import SP_implementations
from igraph import Graph
from numba import cuda

""" Choose the best shortest path implementation based on Graph criterion """


def implementation_seeker(graph: Graph):
    """
    *TO BE PERFECTIONED* return the correct implementation based on several paramenters
    :param graph: an iGraph.Graph object pyntacle ready
    :return: an SP_implementations representing the correct implementation
    """

    # todo: decide the thresholds that will be used for SP search decision
    if graph.ecount() <= 3500:  # random number
        imp = SP_implementations.igraph  # default

    else:
        if not cuda.is_available():
            sys.stdout.write("GPU implementation is not available, using CPU instead\n")

            imp = SP_implementations.cpu

        else:
            # todo this should return GPU when tested, commented for the moment
            # imp = SP_implementations.gpu
            imp = SP_implementations.cpu

    return imp
