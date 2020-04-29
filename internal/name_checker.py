__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t.mazza@css-mendel.it>
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


