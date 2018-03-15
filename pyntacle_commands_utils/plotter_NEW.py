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
import logging
import os
import random

# Checking presence of pycairo, needed for plotting
from importlib import util
pycairo_check = util.find_spec("cairo")
if pycairo_check is None:
    raise EnvironmentError("pyntacle needs the pycairo library to be installed and available "
                           "in order to produce plots. Please install it and try again.")

from igraph import Graph, plot

from exceptions.missing_attribute_error import MissingAttributeError
from exceptions.wrong_argument_error import WrongArgumentError
from tools.graph_utils import GraphUtils as gu

""" Utilities used by the pyntacle command line  to produce small reports"""