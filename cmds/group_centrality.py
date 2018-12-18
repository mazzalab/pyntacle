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
from cmds.cmds_utils.group_search_wrapper import InfoWrapper as kpw
from cmds.cmds_utils.group_search_wrapper import GOWrapper as gow
from cmds.cmds_utils.group_search_wrapper import BFWrapper as bfw
from algorithms.keyplayer import KeyPlayer as kpp
from itertools import chain
from exceptions.generic_error import Error
from io_stream.exporter import PyntacleExporter
from cmds.cmds_utils.plotter import *
from cmds.cmds_utils.reporter import *
from tools.graph_utils import *
from internal.graph_load import GraphLoad, separator_detect
from tools.enums import ReportEnum, CmodeEnum
from tools.add_attributes import AddAttributes
from colorama import Fore, Style


class GrpupCentrality():
    def __init__(self, args):
        self.logging = log
        self.args = None
        self.args = args
        if self.args.seed:
            random.seed(self.args.seed)