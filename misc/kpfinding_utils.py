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
from functools import wraps
from exceptions.illegal_kppset_size_error import IllegalKppsetSizeError
from misc.enums import KPPOSchoices, KPNEGchoices

""" Utilities for checking the consistency of the parameters passed in greedy or bruteforce optimization """

def kpchecker(func):
    """
    checks that the arguments passed to the KP functions are correct according to the parameters passed
    :param func: thje kp-function passed
    :return: the function checked for integrity to the KP-SEARCH function
    """

    @wraps(func)
    def func_wrapper(graph, kpp_size, kpp_type, implementation, seed, max_sp, *args, **kwargs):
        if not isinstance(kpp_size, int):
            raise TypeError("The kpp_size argument ('{}') is not an integer number".format(kpp_size))

        else:
            if kpp_size >= graph.vcount():
                raise IllegalKppsetSizeError("The kpp_size must be strictly less than the graph size")

        if seed is not None:
            if not isinstance(seed, int):
                raise ValueError("seed must be an integer")

        if not isinstance(kpp_type, (KPPOSchoices, KPNEGchoices)):
            raise TypeError("\"kpp-type\" must be either a \"KPPOSchoices\" enumerator or a \"KPNEGchoices\",  {} found".format(type(kpp_type).__name__))

        if max_sp is not None and not isinstance(max_sp, int) and max_sp > 1 and max_sp <= graph.vcount():
            raise ValueError("\"max_sp\" must be an integer greater than one and lesser tan the total number of nodes")

        sys.stdout.write("All Good!\n")
        return func(graph, kpp_size, kpp_type, implementation,seed, max_sp, *args, **kwargs)

    return func_wrapper