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
Utilities made for common adjacency matrix file operations
"""
from config import *
import os
import logging
from exceptions import *

class AdjmUtils():
    logger = None

    def __init__(self, file: str, header: bool, sep="\t"):
        """
        Initialize the Adjacency Matrix Utils class by giving the parser all the necessary information.
        :param str file: a valid PATH to the input adjacency matrix
        :param bool header: a boolean specifying whether the adjacency matrix contains an header or not on both rows and columns
        :param str sep: a string specifying the delimiter amon adjacency matrix fields. Default it "\t" (tab separated)
        """

        self.logger = log
        if not os.path.exists(file):
            self.logger.fatal("Input file does not exist")
            raise FileNotFoundError

        else:
            self.adjfile = file

        if not isinstance(sep, str):
            raise TypeError("\"sep\" must be a string, {} found".format(type(sep).__name__))

        else:
            self.sep = sep

        self.header = header  # boolean to check if header is present

    def is_squared(self) -> bool:
        """
        Utility to check if an adjaceny matrix is squared or not by checking if the number of rows and columns (must be equal)
        :return: a boolean representing True if the matrix is squared or False otherwise
        """
        self.logger.info("Checking if adjacency matrix is squared")
        with open(self.adjfile, "r") as file:
            firstline = file.readline()
            nrow = len(firstline.rstrip().split(self.sep))
            ncol = len(firstline.rstrip().split(self.sep))
            for line in file:
                tmp = line.split(self.sep)
                if len(tmp) != nrow or len(tmp) != ncol:
                    self.logger.info("Matrix is not squared")
                    return False
        self.logger.info("Matrix is squared")
        return True

    def __store_adjm(self):
        """
        Store the input adjacency matrix in a list (for internal purposes only)
        """
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

    def get_adjm(self, file: str, header: bool, sep="\t"):
        """
        Replace the current adjacency Matrix with another one
        :param str file: valid path to the newl added input adjacency matrix
        :param bool header: Boolean to specify whether the header is present or not
        :param str sep: cell separator. Default is "\t"
        """

        self.adjfile = file
        self.sep = sep
        self.header = header


    def __write_adjm(self, adjm: list, separator: str, appendix: str) -> str:
        """
        Hidden function that rewrite an adjacency matrix to the input path (used internally)
        :return: the path to the (new) adjacency matrix
        """
        o = os.path.splitext(os.path.abspath(self.adjfile))
        outpath = o[0] + "_" + appendix + o[-1]
        with open(outpath, "w") as out:
            self.logger.info("rewriting adjacency matrix")
            self.logger.info("adjacency path: " + outpath)

            if self.header:
                out.write(separator.join(self.headlist) + "\n")

                for i, elem in enumerate(adjm, 1):
                    out.write(self.headlist[i] + separator + separator.join(elem) + "\n")
            else:
                for elem in adjm:
                    out.write(separator.join(elem) + "\n")

        return outpath

    def is_weighted(self) -> bool:
        """
        Function that returns a boolean telling whether the adjacency matrix contains weights (values different from 1s and 0s)
        :return: a boolean with `True` if the graph is weighted and `False` otherwise
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
        """
        Convert matrix to unweighted by setting every value different from 1 to 1 and write it to a new file
        """
        self.__store_adjm()  # store adjacency matrix into a list

        if not self.is_weighted():
            self.logger.info("matrix is already unweighted")
            return None

        self.logger.info("removing weights from adjacency matrix")

        for i, elem in enumerate(self.adjm):
            self.adjm[i] = ["0" if float(x) == 0.0 else "1" for x in elem]

        self.__write_adjm(self.adjm, separator=self.sep, appendix="unweighted")

    def is_direct(self) -> bool:
        """
        Checks whether an adjacency matrix is direct or not (the lower and upper triangulkar matrices, are they equal?)
        :return: directbool, a value representing True if the matrix is direct and False otherwise
        """
        self.directbool = False
        self.__store_adjm()  # store adjacency matrix into a list
        self.logger.info("checking if the adjacency matrix is direct")
        for i, elem in enumerate(self.adjm):
            for e, el in enumerate(elem):
                if self.adjm[e][i] != el:
                    self.directbool = True
                    return self.directbool

        return self.directbool

    def make_undirect(self) -> str:
        """
        Convert an direct Adjacency Matrix to an undirect one into a new file
        :return str outpath: a valid path where the new (undirected) adjacency matrix will be stored
        """

        self.__store_adjm()
        if not self.is_direct():
            self.logger.info("the matrix is already undirect")
            return self.adjfile

        self.logger.info("Converting Matrix to undirect")

        for i, elem in enumerate(self.adjm):
            for e, el in enumerate(elem):
                if el != 0:
                    self.adjm[e][i] = el
        outpath = self.__write_adjm(self.adjm, separator=self.sep, appendix="undirected")
        return outpath
