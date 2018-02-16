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
import string
import random

""" Decorators for the Generator Method """

def generatorscanner(func):
    @wraps
    def func_wrapper(params, name, *args, **kwargs):
        if not isinstance(params, list):
            raise TypeError("\"params\" argument must be a list, {} found".format(type(params).__name__))

        if not isinstance(name, str):
            raise TypeError("\"name\" argument must be a list, {} found".format(type(name).__name__))

        for elem in params:
            if not isinstance(elem, (int, float)):
                raise TypeError("{} is not an integer or float, \"params\" must be numerical only")

        return func(params, name, *args, **kwargs)

    return func_wrapper

def randomword(length, prefix=None):

    letters = string.ascii_lowercase

    if prefix is None:
        return ''.join(random.choice(letters) for i in range(length))

    else:
        return "_".join([prefix, ''.join(random.choice(letters) for i in range(length))])