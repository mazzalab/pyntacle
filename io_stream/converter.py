__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
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

'''
Contains a series of quick file converters in order to parse one graph atored into  format and mmedately rewrite onto
another
'''

import pandas as pd
from config import *
from tools.edgelist_utils import EglUtils as egl
from misc.io_utils import *
from exceptions.unproperlyformattedfile_error import UnproperlyFormattedFileError


class QuickConvert:
    '''
    This class is designed to quickly convert one file format to another, without passing to the Graph object
    and the Importing/Exporting. At the moment, we quickly convert Sif to Edgelist and Vice-Versa using the
    'EdgelistToSif' and the 'SifToEdgelist' methods.
    '''

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def EdgelistToSif(input_file:str, sep=None, header=False, output_file=None):
        """
        **ASCRIVI**
        :param str input_file: a valid path to the input Edgelist
        :param str separator: a string specifiny the column separator for both input and output. If 'None' (default), we assume a \t separates each column.
        :param bool header: rewrite the header into the output file. Default if 'False' (inut file contains no header)
        :param str output_file: The path where the resulting file will be stored.If None, the output file will be in the current directory,with the *.egl* extension and a small pseudoword before the inout basename.
        :return: the path to the output file
        """
        if output_file is None:
            output_file = os.path.splitext(os.path.basename(os.path.abspath(input_file)))[0] + randomword(4) + ".sif"
            sys.stdout.write("writing the output file at {}\n").format(output_file)

        if os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. Will overwrite\n".format(output_file))

        eglutils = egl(file=input_file, header=header, separator=sep)

        if eglutils.is_direct():
            raise UnproperlyFormattedFileError("Edge List is direct")

        if eglutils.is_pyntacle_ready():
            raise UnproperlyFormattedFileError("Edgelist contains multiple edges containing two vertices")

        edgelist = []

        with open(input_file, "r") as infile:
            if header:
                headerstring = infile.readline().rstrip().split(sep)
                # print(self.headerstring)
                # input()

            for line in infile:
                pair = line.rstrip().split(sep)
                edgelist.append(pair)  # a list of lists

        # remove all multiple istances from the edgelist
        siftuple = tuple(tuple(x) for x in edgelist)
        sifcleaned = set(tuple(sorted(l)) for l in siftuple)
        siflist = [list(x) for x in sifcleaned]

        with open(output_file, "w") as outfile:
            if header:
                outfile.write(sep.join([headerstring[0], "Interaction", headerstring[-1]]) + "\n")

            for couple in siflist:
                outfile.write(" ".join([couple[0], "interacts_with", couple[1]]) + "\n")

        sys.stdout.write("file successfully converted\n")
        return  output_file

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def SifToEdgelist(input_file:str, sep=None, header=False, output_file=None) -> str:
        """
        Converts a Simple Interaction Format file (*SIF*) to an undirected edgelist readable by pyntacle. We assume the
        SIF file contains at least 3 columns, with the *source* nodes in the 1st column and the *target* nodes in the
        3rd column. Any other information other thant the interaction will be lost. If a header is present, the cells
        corresponding to column 1 and 3 will be rewritten.
        :param str input_file: a valid path to the input SIF file
        :param str separator: a string specifiny the column separator for both input and output. If 'None' (default), we assume a \t separates each column.
        :param bool header: rewrite the header into the output file. Default if 'False' (inut file contains no header)
        :param str output_file: The path where the resulting file will be stored.If None, the output file will be in the current directory,with the *.egl* extension and a small pseudoword before the inout basename.
        :return: the path to the output file
        """
        if output_file is None:
            output_file = os.path.splitext(os.path.basename(os.path.abspath(input_file)))[0] + randomword(4) + ".egl"
            sys.stdout.write("writing the output file at {}\n").format(output_file)

        if os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. Will overwrite\n".format(output_file))

        egl = []
        with open(input_file, "w") as infile:
            if header:
                headerrow = infile.readline().split(sep)
                headerrow = sep.join([headerrow[0], headerrow[2]])
                egl.append(headerrow)

            for line in infile:
                tmp = line.split(sep)
                del tmp[1] #remove interaction column

                if len(tmp) < 2:
                    sys.stdout.write()

                elif len(tmp) > 2:

                else:
                    egl.append(sep.join(tmp))


        with open(output_file, "w") as outfile:


        return output_file



