__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
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



import itertools
from config import *
import os
import pandas as pd
from exceptions.unproperly_formatted_file_error import UnproperlyFormattedFileError

class EglUtils:
    r"""
    A series of utilities to perform several checks and file parsing operations on edge list files
    """

    logger = None

    def __init__(self, file: str, header: bool, sep="\t"):
        u"""
        Initialize the EdgeList Utils object

        :param str file: a file PATH to the edgelist file
        :param bool header: specify whether the edgelist has an header or not
        :param str sep: a string specified the separator between Edgelist cells. Default is "\t"
        """
        self.logger = log
        if not isinstance(header, bool):
            raise TypeError(u"\"header ust be a string, {} found".format(type(header).__name__))

        if not isinstance(sep, str):
            raise TypeError(u"\"sep\" must be a string, {} found".format(type(sep).__name__))
        else:
            self.sep = sep

        if not os.path.exists(file):
            raise FileNotFoundError(u"Input file at path {} does not exist".format(file))

        else: #read the edgelist and store it into a list of lists using the egl_to_list function

            self.edglfile = file
            if header:
                edgl = pd.read_csv(self.edglfile, dtype = str, sep = self.sep, header = 0)

                with open(file, "r") as hh:
                    self.header = hh.readline().rstrip().split(self.sep)  # store the header and strip all trailing characters
            else:
                edgl = pd.read_csv(self.edglfile, dtype=str, sep=self.sep, header=None)
                self.header = None

            #remove all empty lines (these should be removed by default but just in case)
            edgl.dropna(how="all", inplace=True)

            #check if there are more than 2 columns and raise error, if so)
            if len(edgl.columns) != 2:
                raise UnproperlyFormattedFileError(
                    u"Edgelist should contain 2 columns, {0} found. found separator is \"{1}\"".format(len(edgl.columns),
                                                                                                      self.sep))
            #create the self.edgl object, storing the rows of the pandas dataframe as list of lists:
            self.edgl = edgl.values.tolist()

    def get_edgelist(self) -> list:
        r"""
        Returns the edge list object as a list of lists (useful for igraph porting)

        :return: a list containing all the values in the input graph BUT the header
        """
        return self.edgl

    def get_header(self) -> list:
        r"""
        return the header object as a list of strings, if present or None otherwise

        :return:a list containing the header of the input edge list
        """

        if self.header is not None:
            return self.header

        else:
            sys.stdout.write("No header present, returning \"None\"")

    def set_edgelist(self, edgl:list):
        r"""
        replace the edgelist (list of list) with another one of choice. Must be a list of lists of string.

        :param list edgl: a list of lists of strings. Each nested list must have length 2
        """

        self.edgl = edgl

    def set_header(self, header:list):
        r"""replaces the header imported in the __init__ with another one (or add an header to the current input file).

        :param str header: a list of strings of length 2. Must be a list of strings of length 2
        :raise: ValueError if ``header`` is not a list of length 2 and if at least one element is not a string
        """

        if len(header) != 2:
            raise ValueError(u"'header' must be a string with 2 elements")
        if any(isinstance(x, str) for x in header):
            raise ValueError(u"'header' has at least one non-string element")

        self.header = header

    def set_sep(self, sep: str):
        r"""replaces the separator imported in the __init__ with another one. The separator must be a string

        :param str sep: a separator of choice. Must be a string.
        :raise: TypeError if ``sep`` is not a string
        """
        if not isinstance(sep, str):
            raise TypeError(u"'sep' must be a string")
        self.sep = sep

    def is_direct(self) -> bool:
        r"""
        Returns a boolean if the edge list contains at least one direct edge

        :return: a boolean; True if the edgelist is direct and False otherwise
        """

        set_direct = list(set((tuple(sorted(x)) for x in self.edgl)))

        if len(set_direct) == len(self.edgl) / 2:
            direct = False

        else:
            direct = True

        return direct

    def is_multigraph(self) -> bool:
        r"""
        Check that the edge-list does not have more than one edge between each vertex pair. Multiple edges between two nodes are not accepted by Pyntacle.

        :return bool: a boolean; `True` if the edgelist is a multigraph, `False` otherwise
        """
        egl_tuple = [tuple(sorted(x)) for x in self.edgl]

        if len(set(egl_tuple)) != (len(self.edgl)/2):
            return True

        else:
            return False

    def make_undirect(self):
        r"""
        Converts the edge list to undirect (add reciprocal pairs if missing). Write the edge list to a file with header
        (if initialized) with the "_undirected" suffix to the output edge list file

        :return str: the path to the valid output file (the name of the input edge list + "_undirected.egl"). If the edge list is already undirect, returns the input edge list file
        """

        if not self.is_direct():
            self.logger.info(u"Graph is already undirect, no operations to perform")
            return self.edglfile

        else:
            single_pairs = set([tuple(sorted(x)) for x in self.edgl])
            single_pairs = [list(x) for x in single_pairs]
            final = []
            for elem in single_pairs:
                final += list(itertools.permutations(elem, 2))

            final = [list(x) for x in self.edgl]

            outpath = "_".join([os.path.splitext(os.path.abspath(self.edglfile))[0], "undirected.egl"])

            self.__write_edgelist(edgelist=final, path=outpath)

            return outpath

    def make_simple(self):
        r"""
        Converts the edge list to a simple edge list (remove duplicated lines). Write the edge list to a file with header
        (if initialized) appending the "_simple" extension to the output edge list file

        :return str: the path to the valid output file (the name of the input edge list + "_simple.egl"). If the edge list is already simple, returns the input edgelist file
        """

        if not self.is_multigraph():
            self.logger.info(u"Edgelist is already simple, will not return any file")
            return self.edglfile

        else:
            final= [list(x) for x in set(tuple(y) for y in self.edgl)]

            outpath = "_".join([os.path.splitext(os.path.abspath(self.edglfile))[0], "simple.egl"])

            self.__write_edgelist(edgelist=final, path=outpath)

            return outpath

    def __write_edgelist(self, edgelist:list, path:str):
        r"""
        Internal method to write an edge list into a file at a specified path

        :param edgelist:
        :param path:
        """

        with open(path, "w") as outfile:
            if self.header is not None:
                outfile.write(self.sep.join(self.header) + "\n")

            oo = [self.sep.join(x) + "\n" for x in edgelist]

            outfile.writelines(oo)




