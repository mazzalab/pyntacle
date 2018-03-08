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

"""**Decorators for checking the integrity of files**"""
from config import *
import csv
from igraph import Graph
from tools.add_attributes import AddAttributes
from misc.binarycheck import is_binary_file
from functools import wraps
def filechecker(func):
    """
    decorator to check the integrity of an input file
    :param func:  function given in input
    :return: the same function with checked properties
    """
    @wraps(func)
    def func_wrapper(file, *args,**kwargs):
        if not isinstance(file, str):
            raise ValueError("\"file\" must be a string, {} found".format(type(file).__name__))

        if not os.path.exists(file):
            raise FileNotFoundError("Input file does not exist")

        return func(file, *args, **kwargs)

    return func_wrapper


def separator_sniffer(func):
    """
    a function imported from graph_load.py that automatically detects the separator of the input file (if not provided)
    and replace the "sep" argument in the Importers function's call
    :param func:
    :return:
    """
    @wraps(func)
    def func_wrapper(file, sep=None, *args, **kwargs):
        if sep is None:
            with open(file, "r") as f:
                try:
                    firstline = f.readline()

                except UnicodeDecodeError:
                    return ('\t')

                else:
                    sniffer = csv.Sniffer()
                    sep = sniffer.sniff(firstline).delimiter

        else:
            if not isinstance(sep, str):
                raise ValueError("\"sep\" must be a string {} found".format(type(sep).__name__))

        return func(file,sep,*args, **kwargs)

    return func_wrapper
