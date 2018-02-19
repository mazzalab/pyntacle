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

""" **a series of decorators to improve the usability of some pyntacle's function, like 
checking if the `igraph.Graph` object is compatible with pyntacle's specifications, verify the presence of nodes 
in the input graph, give elapsed time of execution and so on"""


from enum import Enum, auto
from config import *

"""Contains all the enumerators used in pyntacle's methods"""


class graph_type(Enum):
    """
    An enumerator that contains the different modes that will be used to compute internally the shortest path of a graph
    For the record, I still prefer the string method
    """
    undirect_unweighted = auto()
    undirect_weighted = auto()
    direct_unweighted = auto()
    direct_weighted = auto()


class implementations(Enum):
    """
    this enumerator stores the different ways that can be used to parallelize the shortest path
    """
    igraph = auto()
    cpu = auto()
    gpu = auto()
    auto = auto()
    
class node_attributes(Enum):
    """
    this enumerator stores all the node attributes that can be instantiated by pyntacle
    """
    #todo aggiungi tutti
    degree = auto()

class graph_attributes(Enum):
    """
    this enumerator stores all the edge attributes that can be instantiated by pyntacle
    """
    #todo aggiungi tutti
    pass

class edge_attributes(Enum):
    """
    this enumerator stores all the edge attributes that can be instantiated by pyntacle
    """
    pass