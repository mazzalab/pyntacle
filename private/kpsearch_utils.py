__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.3"
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
from functools import wraps
from exceptions.illegal_kppset_size_error import IllegalKppsetSizeError
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
    def func_wrapper(graph, kp_size, kp_type, seed=None, max_distance=None, *args, **kwargs):
        if not isinstance(kp_size, int):
            raise TypeError("The kp_size argument ('{}') is not an integer number".format(kp_size))

        else:
            if kp_size >= graph.vcount():
                raise IllegalKppsetSizeError("The kp_size must be strictly less than the graph size")

        if seed is not None:
            if not isinstance(seed, int):
                raise ValueError("seed must be an integer")
            else:
                random.seed(seed)

        if not isinstance(kp_type, (KpposEnum, KpnegEnum)):
            raise TypeError("\"kpp-type\" must be either a \"KPPOSchoices\" enumerator or a \"KPNEGchoices\",  {} found".format(type(kp_type).__name__))

        if max_distance is not None and not isinstance(max_distance, int) and max_distance > 1 and max_distance <= graph.vcount():
            raise ValueError("\"max_sp\" must be an integer greater than one and lesser tan the total number of nodes")

        return func(graph, kp_size, kp_type, seed, max_distance, *args, **kwargs)

    return func_wrapper

def bruteforce_search_initializer(func):
    """
    checks that the arguments passed to the KP functions for bruteforce search
    are correct according to the parameters that are given as argument
    :param func: the kp-function passed
    :return: the function checked for integrity to the KP-SEARCH function
    """

    @wraps(func)
    def func_wrapper(graph, kp_size, kp_type, max_distance=None, *args, **kwargs):

        if not isinstance(kp_size, int):
            raise TypeError("The kp_size argument ('{}') is not an integer number".format(kp_size))

        else:
            if kp_size >= graph.vcount():
                raise IllegalKppsetSizeError("The kp_size must be strictly less than the graph size")

        if not isinstance(kp_type, (KpposEnum, KpnegEnum)):
            raise TypeError("\"kpp-type\" must be either a \"KPPOSchoices\" enumerator or a \"KPNEGchoices\",  {} found".format(type(kp_type).__name__))

        if max_distance is not None and not isinstance(max_distance, int) and max_distance > 1 and max_distance <= graph.vcount():
            raise ValueError("\"max_sp\" must be an integer greater than one and lesser than the total number of nodes")

        # sys.stdout.write("Brute-force search of the best kpp-set of size {}\n".format(kp_size))

        return func(graph, kp_size, kp_type,max_distance, *args, **kwargs)

    return func_wrapper
