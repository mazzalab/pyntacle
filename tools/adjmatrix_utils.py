__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t,mazza@css-mendel.it>
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


from config import *
import os
import logging
from exceptions import *
import numpy as np
import sys


class AdjmUtils:

    logger = None

    def __init__(self, file: str, header: bool, sep="\t"):
        r"""
        A series of utilities to check if a given adjacency matrix file is compliant to the Pyntacle `adjacency matrix file format <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html#adjm>`_

        :param str file: a valid path to the input adjacency matrix
        :param bool header: a boolean specifying whether the adjacency matrix contains an header or not (**note** the header must be present on both rows and columns)
        :param str sep: a string specifying the field separator among adjacency matrix cells. Default it ``\t`` (a tab-separated file)
        :raise FileNotFoundError: if the adjacency matrix path is incorrect
        :raise TypeError: if ``sep`` is not a string.
        """

        self.logger = log
        if not os.path.exists(file):
            raise FileNotFoundError(u"Input file does not exist")

        else:
            self.adjfile = file

        if not isinstance(sep, str):
            raise TypeError(u"\"sep\" must be a string, {} found".format(type(sep).__name__))

        else:
            self.sep = sep

        self.header = header  # boolean to check if header is present

        self.adjm = None

    def is_squared(self) -> bool:
        r"""
        Checks whether the adjacency matrix is an :math:`n x n` matrix.

        :return bool: ``True`` if the matrix is squared, ``False`` otherwise
        """

        self.logger.info(u"Checking if adjacency matrix is squared")

        with open(self.adjfile, "r") as file:
            firstline = file.readline()
            nrow = len(firstline.rstrip().split(self.sep))
            ncol = len(firstline.rstrip().split(self.sep))
            for line in file:
                tmp = line.split(self.sep)
                if len(tmp) != nrow or len(tmp) != ncol:
                    self.logger.info(u"Matrix is not squared")
                    return False
        self.logger.info(u"Matrix is squared")
        return True

    def __store_adjm(self):
        if self.adjm is None:
            self.adjm = []
            with open(self.adjfile, "r") as infile:
                if self.header:
                    self.headlist = infile.readline().rstrip().split(self.sep)
                    # print (self.headlist)

                    iterator = iter(infile.readline, '')

                    for line in iterator:
                        # print (line)

                        if self.header:
                            tmp = line.rstrip().split(self.sep)
                            self.adjm.append(tmp[1:])

                        else:
                            tmp = line.rstrip().split(self.sep)
                            self.adjm.append(tmp)

        else:
            return self.adjm

    def set_adjm(self, file: str, header: bool, sep="\t"):
        r"""
        Replace the adjacency matrix with another one, along with the information necessary to understand the new adjacency matrix

        :param str file: valid path to the new input adjacency matrix
        :param bool header: whether the header is present or not
        :param str sep: cell separator. Default is ``\t``
        """

        self.adjfile = file
        self.sep = sep
        self.header = header
        self.adjm = None

    def __write_adjm(self, adjm: list, separator: str, appendix: str) -> str:
        o = os.path.splitext(os.path.abspath(self.adjfile))
        outpath = o[0] + "_" + appendix + o[-1]
        with open(outpath, "w") as out:
            self.logger.info(u"rewriting adjacency matrix at path: {}".format(outpath))

            if self.header:
                out.write(separator.join(self.headlist) + "\n")

                for i, elem in enumerate(adjm, 1):
                    out.write(self.headlist[i] + separator + separator.join(elem) + "\n")
            else:
                for elem in adjm:
                    out.write(separator.join(elem) + "\n")

        return outpath

    def is_weighted(self) -> bool:
        r"""
        Checks whether the adjacency matrix is weighted or not (contains other values rather than 0s and 1s)

        :return  bool: ``True`` if the graph is weighted,``False`` otherwise
        """
        self.__store_adjm()
        self.logger.info("checking if the matrix is weighted")
        self.weightbool = False
        for elem in self.adjm:
            elem = list(filter(lambda elem: float(elem) != 0.0, elem))  # remove all non-zero element
            for el in elem:
                if float(el) != 1.0:
                    self.weightbool = True
                    return self.weightbool

        return self.weightbool

    def remove_weigths(self):
        r"""
        Replaces any value different from ``0`` and ``1`` (removing weights from an ajacency matrix) hence making the matrix binary.
        Writes the mirrored binary adjacency matrix to a file in the same directory with the  ``_unweighted.adjm``
        suffix.

        :return str: the path to the unweighted adjacency matrix. This file will be stored in the same directory of the input adjacencuy matrix, with the ``unweighted.adjm`` suffix.
        """

        self.__store_adjm()  # store adjacency matrix into a list

        if not self.is_weighted():
            self.logger.info(u"matrix is already unweighted")
            return None

        self.logger.info(u"removing weights from adjacency matrix")

        for i, elem in enumerate(self.adjm):
            self.adjm[i] = ["0" if float(x) == 0.0 else "1" for x in elem]

        outpath = self.__write_adjm(self.adjm, separator=self.sep, appendix="unweighted")
        return outpath

    def is_direct(self) -> bool:
        r"""
        Checks whether an adjacency matrix is direct or not (so if the upperand lower triangular matrix match perfectly)

        :return: directbool, a value representing True if the matrix is direct and False otherwise
        """

        self.directbool = False
        self.__store_adjm()  # store adjacency matrix into a list
        self.logger.info(u"checking if the adjacency matrix is direct")
        for i, elem in enumerate(self.adjm):
            for e, el in enumerate(elem):
                if self.adjm[e][i] != el:
                    self.directbool = True
                    return self.directbool

        return self.directbool

    def make_undirect(self) -> str:
        r"""
        Makes a direct adjacency matrix to undirect, hence making the original adjacency matrix `symmetric <https://en.wikipedia.org/wiki/Symmetric_matrix>`_.
        Writes the newly created adjacency matrix to a file with the ``_undirect.adjm`` suffix.

        .. note::If the matrix is weighted, we will take the maximum value in each cell and assign it to the corresponding one.

        :return str: a valid path where the new (undirected) adjacency matrix will be stored with the ``_unweighted.adjm`` extension
        """

        self.__store_adjm()
        if not self.is_direct():
            self.logger.info(u"the input matrix is already undirect, returning the same matrix")
            return self.adjfile

        self.logger.info(u"Converting Matrix to undirect")
        self.adjm = np.array(self.adjm, dtype=float)

        aa = np.maximum(self.adjm, self.adjm.transpose())

        self.adjm = aa.tolist()

        self.adjm = [[str(x) for x in y] for y in self.adjm]

        outpath = self.__write_adjm(self.adjm, separator=self.sep, appendix="undirected")
        return outpath
