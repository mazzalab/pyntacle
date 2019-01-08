__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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

"""A  set of decorators and other function useful for the io_stream/ utilities"""

from config import *
import csv
from functools import wraps
import string
import random

def input_file_checker(func):
    r"""
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

def output_file_checker(func):
    r"""contains a series of operations that can be perfoemrd in order to verify the integrity of the output file"""
    @wraps(func)
    def func_wrapper(graph, file, *args, **kwargs):
        if not isinstance(file, str):
            raise ValueError("\"file \" must be a string, {} found".format(type(file).__name__))

        else:
            if os.path.exists(os.path.abspath(file)):
                sys.stdout.write("A file with the same name exists at {}, will overwrite\n".format(file))

            return func(graph,file, *args, **kwargs)

    return func_wrapper

def separator_sniffer(func):
    r"""
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

def generatorscanner(func):
    """
    Give a look at params'integrity for 'generators' functions. Raise Errors if something's not covered.
    :param func: the input 'iostream.generators' function
    :return: the input function, decorated
    """
    @wraps(func)
    def func_wrapper(params, name="", *args, **kwargs):
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