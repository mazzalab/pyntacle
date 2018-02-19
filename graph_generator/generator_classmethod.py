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

#test to implement the automatic generation of networks using classmethod rather than standard instances
import logging
from graph_generator.graph_igraph_generator import randomword
from igraph import Graph
from exceptions.illegal_argument_number_error import IllegalArgumentNumberError
from utils.add_attributes import AddAttributes

class Generator():
    '''
    a generic class for the generation of a random network
    '''
    _logger = logging.getLogger()

    def __init__(self):
        self.graph = Graph()

    def get_graph(self):
        return self.graph


    @classmethod
    def random(cls, params):

        if not isinstance(params, list):
            raise ValueError("input must be a list")

        if not len(params) <= 2:
            raise IllegalArgumentNumberError("input list must contain at leastt two cls")
        elif not (isinstance(params[0], int) and isinstance(params[1], (float, int))):
            raise TypeError('Wrong parameter type(s) for Erdos-Renyi graph generation')

        elif not (0 < params[0] and 0 <= params[1]):
            raise ValueError('The value of one or more cls is not allowed')

        else:
            if isinstance(params[1], float) and 0 <= params[1] <= 1:
                cls._logger.info(
                    "Creating an Erdos-Renyi random graph using a probability rewiring of {} ".format(params[1]))
                graph = Graph.Erdos_Renyi(params[0], p=params[1])

            elif isinstance(params[1], int) and params[1] > 1:
                cls._logger.info("Creating an Erdos-Renyi random graph using  a total number of edges of {}".format(
                        str(params[1])))
                graph = Graph.Erdos_Renyi(params[0], m=params[1])

            else:
                raise ValueError('second parameter is not a  positive float or an integer > 1')

            graph_name = "_".join(["Random", str(graph.vcount()), str(graph.ecount()), randomword(10)])

            AddAttributes(graph=graph).graph_initializer(graph_name=graph_name)


            return graph