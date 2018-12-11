__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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
from functools import wraps
from exceptions.illegal_kpset_size_error import IllegalKpsetSizeError
from tools.enums import KpposEnum, KpnegEnum
import random

"""Utilities for checking the consistency of the parameters passed in greedy or bruteforce optimization"""


def greedy_search_initializer(func):
    """
    checks that the arguments passed to the KP functions for greedy optimization
    are correct according to the parameters that are given as argument

    :param func: the kp-function passed

    :return: the function checked for integrity to the KP-SEARCH function
    """

    @wraps(func)
    def func_wrapper(graph, k, metric, seed=None, *args, **kwargs):
        if not isinstance(k, int):
            raise TypeError("The k argument ('{}') is not an integer number".format(k))

        else:
            if k >= graph.vcount():
                raise IllegalKpsetSizeError("The k must be strictly less than the graph size")

        if seed is not None:
            if not isinstance(seed, int):
                raise ValueError("seed must be an integer")
            else:
                random.seed(seed)

        return func(graph, k, metric, seed, *args, **kwargs)

    return func_wrapper

def bruteforce_search_initializer(func):
    """
    checks that the arguments passed to the KP functions for bruteforce search
    are correct according to the parameters that are given as argument

    :param func: the kp-function passed

    :return: the function checked for integrity to the KP-SEARCH function
    """

    @wraps(func)
    def func_wrapper(graph, k, metric, *args, **kwargs):

        if not isinstance(k, int):
            raise TypeError("The k argument ('{}') is not an integer number".format(k))

        else:
            if k >= graph.vcount():
                raise IllegalKpsetSizeError("The k must be strictly less than the graph size")

        return func(graph, k, metric, *args, **kwargs)

    return func_wrapper
