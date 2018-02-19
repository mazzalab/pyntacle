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

from config import *
from functools import wraps


def filechecker(func):
    """Export Utility for checking the existence and the integrity of the output file"""
    @wraps(func)
    def func_wrapper(graph, file, *args, **kwargs):
        if not isinstance(file, str):
            raise TypeError("`file` must be a string, {} found".format(type(file).__name__))

        directory = os.path.dirname(file)  # returns '' if the directory does not exist

        if not directory:
            file = os.path.join(os.getcwd(), file)

        elif not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        return func(graph, file, *args, **kwargs)

    return func_wrapper