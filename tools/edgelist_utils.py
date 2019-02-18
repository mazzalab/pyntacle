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
from exceptions.improperly_formatted_file_error import ImproperlyFormattedFileError

class EglUtils:

    logger = None

    def __init__(self, file: str, header: bool, sep="\t"):
        u"""
        This class contains a series of tools to assess the integrity of an edge list file and its compatibility to
        Pyntacle `accepted edge list formats <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#egl>`_.
        Finally, it contains methods to make an edge list compliant to these standards.

        :param str file: a valid path pointing to the edge list file
        :param bool header: specify if the edge list contains an header on the first line
        :param str sep: the separator between cells. Defaults to ``\t``
        :raise FileNotFoundError: if the path to the edge list is invalid
        :raise TypeError: if ``header`` or ``sep`` are not strings
        :raise ImproperlyFormattedFileError: if the edge list file contains more than 2 columns
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
                    # store the header and strip all trailing characters
                    self.header = hh.readline().rstrip().split(self.sep)
            else:
                edgl = pd.read_csv(self.edglfile, dtype=str, sep=self.sep, header=None)
                self.header = None

            #remove all empty lines (these should be removed by default, this is only a double check.
            edgl.dropna(how="all", inplace=True)

            #check if there are more than 2 columns and raise error, if so)
            if len(edgl.columns) != 2:
                raise ImproperlyFormattedFileError(
                    u"Edgelist should contain 2 columns, {0} found. found separator is \"{1}\"".format(len(edgl.columns),
                                                                                                      self.sep))
            #create the self.edgl object, storing the rows of the pandas dataframe as list of lists:
            self.edgl = edgl.values.tolist()

    def get_edgelist_obj(self) -> list:
        r"""
        Returns the edge list as a list of lists, each sublist containing the connected node pair.

        :return list: The edge list as a list of lists, each sublist of size 2.
        """
        return self.edgl

    def get_header(self) -> list or None:
        r"""
        Returns the edge list header. if present as a list of strings. Returns :py:class:`None` if the stored edge list has no header.

        :return list, None: either the header of the input edge list as a list of list or :py:class:`None` if the input edge list did not have any header.
        """

        if self.header is not None:
            return self.header

        else:
            sys.stdout.write("No header present, returning \"None\"")
            return None

    def set_edgelist_obj(self, edgl: list):
        r"""
        Replaces the edge list object (a list of lists, each sublist storing the connected node pair)
        with another one. Must be a list of lists of string.

        :param list edgl: a list of lists of strings. Each nested list must have length 2
        """

        self.edgl = edgl

    def set_header_obj(self, header: list):
        r"""
        Replaces the header initialized in this class with another one. The header must be a list of strings of size 2.

        :param str header: a list of strings of length 2. Must be a list of strings of length 2
        :raise: ValueError if ``header`` is not a list of length 2 and if at least one element is not a string
        """

        if len(header) != 2:
            raise ValueError(u"'header' must be a string with 2 elements")
        if any(isinstance(x, str) for x in header):
            raise ValueError(u"'header' has at least one non-string element")

        self.header = header

    def set_sep(self, sep: str):
        r"""
        Replaces the initialized separator with another one. The separator must be a string.

        :param str sep: a separator of choice.
        :raise: TypeError if ``sep`` is not a string
        """
        if not isinstance(sep, str):
            raise TypeError(u"'sep' must be a string")
        self.sep = sep

    def is_direct(self) -> bool:
        r"""
        Returns ``True`` if the edge list contains at least one direct edge, ``False`` otherwise.

        :return bool: ``True`` if the edge list is direct, ``False`` otherwise
        """

        set_direct = list(set((tuple(sorted(x)) for x in self.edgl)))

        if len(set_direct) == len(self.edgl) / 2:
            direct = False

        else:
            direct = True

        return direct

    def is_multigraph(self) -> bool:
        r"""
        Check that the edge list does not have more than one edge between each node pair. In other terms, it checks
        that the edge list does not store a multigraph, a construct that is not accepted by Pyntacle.

        :return bool: ``True`` if the edgelist is a multigraph, ``False`` otherwise
        """
        egl_tuple = [tuple(sorted(x)) for x in self.edgl]

        if len(set(egl_tuple)) != (len(self.edgl)/2):
            return True

        else:
            return False

    def make_undirect(self) -> str:
        r"""
        Converts an edge list with one or more direct links to undirect (add reciprocal pairs if missing).
        Write the edge list to a file with the same name as the initial edge list and the  "_undirected.egl" suffix
        if it was direct, otherwise returns the initial path of the edge list file.

        :return str: The path to transformed undirect edge list (the name of the initialized edge list + "_undirected.egl") if it was direct. Otherwise, returns the starting edge list file.
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

    def make_simple(self) -> str:
        r"""
        Converts the input edge list containing redundant node pair (a multigraph) to a simple edge list with no repetitions.
        Write the edge list to a file ending with the ``_simple.egl`` suffix, or the original edge list file if it was
        already simple.

        :return str: The path to the valid output file (the name of the input edge list + "_simple.egl") if the edge list stored a multigraph. Otherwise, returns the input edgelist file
        """

        if not self.is_multigraph():
            self.logger.info(u"Edgelist is already simple, will not return any file")
            return self.edglfile

        else:
            final = [list(x) for x in set(tuple(y) for y in self.edgl)]

            outpath = "_".join([os.path.splitext(os.path.abspath(self.edglfile))[0], "simple.egl"])

            self.__write_edgelist(edgelist=final, path=outpath)

            return outpath

    def __write_edgelist(self, edgelist: list, path: str):
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




