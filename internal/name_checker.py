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

from config import *
import re

def attribute_name_checker(name:str):
    #NOTE: this checks the basename of the graph name only
    if not name:
        raise ValueError("Empty string found")

    if not isinstance(name, str):
        raise ValueError("Graph name must be a string, {} found".format(type(name).__name__))

    if name.isspace():
        raise ValueError("Graph name must contain at least a non-empty character")
    if not re.match(r"^[\w\.\-\ \:\+\[\]\(\)\{\}\=]+$", name):
        raise ValueError("Graph name contains illegal characters")


