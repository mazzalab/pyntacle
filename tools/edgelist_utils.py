__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 October 2016"
__license__ = u"""
  Copyright (C) 20016-2017  Tommaso Mazza <t,mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software; you can use and redistribute it under
  the terms of the BY-NC-ND license as published by
  Creative Commons; either version 4 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc.,  51 Franklin Street, Fifth Floor, Boston, MA
  02110-1301 USA
  """

"""
Utilities made for common operations on edge lists input files
"""

import itertools
from config import *
import os
import pandas as pd
from exceptions.unproperly_formatted_file_error import UnproperlyFormattedFileError

class EglUtils:
    logger = None

    def __init__(self, file: str, header: bool, sep="\t"):
        """
        Initialize the EdgeList Utils object
        :param str file: a file PATH to the edgelist file
        :param bool header: whether the edgelist has an header or not
        :param str sep: a string specified the separator between edgelist fields. Default is "\t" (tab separated edgelist)
        """
        self.logger = log

        if not isinstance(sep, str):
            raise ValueError("\"sep\" must be a string, {} found".format(type(sep).__name__))
        else:
            self.sep = sep

        if not os.path.exists(file):
            raise FileNotFoundError("Input file does not exist")

        else:
            checkfile = pd.read_csv(filepath_or_buffer=file, sep=self.sep)
            if len(checkfile.columns) != 2:
                raise UnproperlyFormattedFileError("Edgelist should contain 2 columns, {} found. Is the separator specified correct?".format(len(checkfile.columns)))

            self.eglfile = file

        self.headerbool = header

        self.edgl = None

    def egl_to_list(self):
        """
        Reparses an edgelist and store it into a list of lists (for internal purposes only)
        """

        self.edgl = []

        with open(self.eglfile, "r") as edg:

            if self.headerbool:
                self.header = edg.readline()
            else:
                self.header = None

            for elem in edg:
                # print(elem)
                tmp = elem.rstrip().split(self.sep)[:2]
                self.edgl.append(tmp)

    def get_edgelist(self) -> list:
        """
        return the edgelist object as a list of lists (useful for igraph porting)
        :return: a list containing all the stuff in the input file, header included, sorted by line
        """
        if self.edgl is not None:
            if self.edgl:
                return self.edgl
            else:
                raise ValueError("the edgelist is empty")
        else:
            raise ValueError("the edgelist is not ")

    def get_header(self) -> list:
        """
        return the header object as a list of string
        :return:a list containing the header of the input edge list
        """

        if self.header is not None:
            return self.header

        else:
            self.logger.warning("Header was not initialized since it's not present, returning \"None\"")
            return None

    def is_direct(self) -> bool:
        """
        Function that returns a boolean if the edgelist contains at least one direct edge
        :return: a boolean; True if the edgelist is direct and False otherwise
        """

        if self.edgl is None:
            self.egl_to_list()

        set_direct = set()

        for elem in self.edgl:
            sorted_elem = tuple(sorted(elem))
            set_direct.add(sorted_elem)

        if len(set_direct) == len(self.edgl) / 2:
            direct = False

        else:
            direct = True

        return direct

    def is_multigraph(self) -> bool:
        """
        Check that the edge-list does not represent a multigraph. Multiple edges between two nodes are not allowed
        :return: Whether ot not the edge-list represents a multigraph
        """

        if self.edgl is None:
            self.egl_to_list()
            
        egl_tuple = [tuple(sorted(x)) for x in self.edgl]

        if len(set(egl_tuple)) != (len(self.edgl)/2):
            return True
        else:
            return False

    def to_undirect(self):
        """
        Converts the edgelist to undirect (add reciprocal pairs if missing)
        """
        if self.edgl is None:
            self.egl_to_list()

        if not self.is_direct():
            self.logger.info("Graph is already undirect, no operations to perform")

        else:
            single_pairs = set([tuple(sorted(x)) for x in self.edgl])
            single_pairs = [list(x) for x in  single_pairs]
            self.edgl = []
            for elem in single_pairs:
                self.edgl += list(itertools.permutations(elem, 2))

            self.edgl = [list(x) for x in self.edgl]

    def set_edgelist_igraph(self):
        """
        Creates a formatted edge list ready to be used by `igraph.Graph` object as edgelist.
        """

        if self.edgl is None:
            self.egl_to_list()

        else:
            self.logger.info("converting edgelist to an igraph edgelist")
            self.edgl = list(set([tuple(sorted(x)) for x in self.edgl]))
            self.edgl = [list(x) for x in self.edgl]