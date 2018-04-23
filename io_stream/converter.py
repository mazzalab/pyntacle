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

from config import *
from tools.edgelist_utils import EglUtils as egl
from tools.misc.io_utils import *
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
    def EdgelistToSif(file:str, sep=None, header=False, output_file=None):
        """
        convert a file written as an edgelist into a Simple Interaction File Format (*SIF*) at the path specified by
        `output_file' format (or, if not specified, will create the same file in the same directory. if the Edgelist
        contains an header, it will be rewritten into the SIF file. The interaction that the SIF file requires will
        be a column named "Interaction" where each node is connected to any other using the *"interacts_with"* keyword.
        :param str file: a valid path to the input Edgelist
        :param str sep: a string specifying the column separator for both input and output. If 'None' (default), we assume a \t separates each column.
        :param bool header: rewrite the header into the output file. Default if 'False' (inut file contains no header)
        :param str output_file: The path where the resulting file will be stored.If None, the output file will be in the current directory,with the *.egl* extension and a small pseudoword before the inout basename.
        :return: the path to the output file
        """
        if output_file is None:
            output_file = os.path.splitext(os.path.basename(os.path.abspath(file)))[0] + randomword(4) + ".sif"
            sys.stdout.write("writing the output file at {}\n").format(output_file)

        if os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. Will overwrite\n".format(output_file))

        eglutils = egl(file=file, header=header, sep=sep)

        if eglutils.is_direct():
            raise UnproperlyFormattedFileError("Edge List is direct")

        if eglutils.is_pyntacle_ready():
            raise UnproperlyFormattedFileError("Edgelist contains multiple edges containing two vertices")

        edgelist = []

        with open(file, "r") as infile:
            if header:
                headerstring = infile.readline().rstrip().split(sep)
                edgelist.append([headerstring[0], "Interaction", headerstring[-1]]) #the header rewritten

            for line in infile:
                pair = line.rstrip().split(sep)
                edgelist.append(pair)  # a list of lists

        # remove all multiple edges from the edgelist, if present
        siftuple = tuple(tuple(x) for x in edgelist)
        sifcleaned = set(tuple(sorted(l)) for l in siftuple)
        siflist = [list(x) for x in sifcleaned]

        with open(output_file, "w") as outfile:

            for couple in siflist:
                outfile.write(sep.join([couple[0], "interacts_with", couple[1]]) + "\n")

        sys.stdout.write("file successfully converted\n")
        return None

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def SifToEdgelist(file:str, sep=None, header=False, output_file=None):
        """
        Converts a Simple Interaction Format file (*SIF*) to an undirected edgelist readable by pyntacle. **CONDITIONS FOR CONVERSIONS:**
        We assume the SIF file contains at least 3 columns, with the *source* nodes in the 1st column and the *target*
        nodes in the 3rd column. All the other values from the 4th column onwards are assumed to be other target nodes connected by
        the input node (so no attributes are present in the sif file). For more info on file format specification,
        please visit `The official Cytoscape Documentation <http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html> .
        **WARNING** If a header is present, the cells corresponding to column 1 and 3 will be rewritten.
        :param str file: a valid path to the input SIF file
        :param str sep: a string specifying the column separator for both input and output. If 'None' (default), we assume a \t separates each column.
        :param bool header: rewrite the header into the output file. Default if 'False' (input file contains no header)
        :param str output_file: The path where the resulting file will be stored.If None, the output file will be in the current directory,with the *.egl* extension and a small pseudoword before the inout basename.
        :return: the path to the output file
        """
        if output_file is None:
            output_file = os.path.join(os.getcwd(), "_".join([os.path.splitext(os.path.basename(os.path.abspath(file)))[0],randomword(4)])) + ".egl"
            sys.stdout.write("writing the output file at {}\n".format(output_file))

        if os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. Will overwrite\n".format(output_file))

        egl = []
        with open(file, "r") as infile:
            if header:
                headerrow = infile.readline().rstrip()
                #.split(sep)
                # headerrow = egl.append([headerrow[0], headerrow[2]])
                # egl.append(headerrow)

            for line in infile:
                tmp = line.rstrip().split(sep)
                del tmp[1] #remove interaction column

                if len(tmp) < 2:
                    sys.stdout.write("node {} is an isolate, will not be written onto edgelist because it can't be represented\n".format(tmp[0]))

                elif len(tmp) > 2:
                    for i in range(1, len(tmp)):
                        egl.append([tmp[0], tmp[i]])

                else:
                    egl.append(tmp)

        #remove multiple edges
        egl = [list(x) for x in set(tuple(sorted(y)) for y in egl)]

        #rewrite egl as a list of strings
        egl = [sep.join(x) for x in egl]
        # add a newline trailing character to each of the written element
        egl = [x + "\n" for x in egl]
        with open(output_file, "w") as outfile:
            if header:
                outfile.write(headerrow+'\n')
            outfile.writelines(egl)

        return None