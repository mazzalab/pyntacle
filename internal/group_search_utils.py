__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t,mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
            raise TypeError("The 'k' argument ({}) is not an integer number".format(k))

        else:
            if k >= graph.vcount():
                raise IllegalKpsetSizeError("The 'k' argument ({}) must be strictly less than the graph size ({})".format(k, graph.vcount()))

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
            raise TypeError("The 'k' argument ({}) is not an integer number".format(k))

        else:
            if k >= graph.vcount():
                raise IllegalKpsetSizeError(
                    "The 'k' argument ({}) must be strictly less than the graph size ({})".format(k, graph.vcount()))

        return func(graph, k, metric, *args, **kwargs)

    return func_wrapper
