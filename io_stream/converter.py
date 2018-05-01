"""
Provide conversion routines between different graph file formats
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.2"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "30/04/2018"
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


from config import *
from tools.edgelist_utils import EglUtils as egl
from tools.misc.io_utils import input_file_checker, separator_sniffer, randomword
from exceptions.unproperly_formatted_file_error import UnproperlyFormattedFileError


class FileFormatConvert:
    """
    This class is designed to convert one graph file format to another, without resorting to iGraph's internal methods.
    """

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def edgelistToSif(file: str, sep=None, header: bool=False, output_file: str=None) -> str:
        """
        Convert as an edge-list file into a Simple Interaction File Format (*SIF*) file.
        If the edge-list file contains an header line, this will be written into the SIF file. The *interaction type*,
        required by SIF will be always *interacts_with* between any pair of interacting nodes.
        For more info on the SIF file format specification, please visit the official Cytoscape documentation
        at http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html.
        **WARNING** If a header is present, the cells corresponding to columns 1 and 3 will be rewritten.
        :param str file: a valid path to the input edge-list file
        :param str sep: a string that specifies the file separator of both input and output files. If 'None' (default),
        we assume a tabulator character as separator.
        :param bool header: Whether to report the header line from the input (if present) to the output file.
        Default if 'False' (input file contains no header)
        :param str output_file: The path to the output file. If None, the output file will be in the current directory,
        and its file extension will be *sif*
        :return: the path to the output file
        """

        if not output_file:
            output_file = os.path.splitext(os.path.basename(os.path.abspath(file)))[0] + randomword(4) + ".sif"
        elif os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. It will be overwritten\n".format(output_file))

        eglutils = egl(file=file, header=header, sep=sep)
        if eglutils.is_direct():
            raise UnproperlyFormattedFileError(
                "The edge-list file represents a direct graph, which is not currently supported")
        elif eglutils.is_hypergraph():
            raise UnproperlyFormattedFileError("The edge-list file contains multiple edges")
        else:
            with open(file, "r") as infile:
                with open(output_file, "w") as outfile:
                    if header:
                        headerstring = infile.readline().rstrip().split(sep)
                        # edgelist.append([headerstring[0], "Interaction", headerstring[-1]])
                        # TODO: why -1, are you allowing files with more than 2 columns?
                        outfile.write(sep.join([headerstring[0], "interacts_with", headerstring[-1]]) + "\n")

                    for line in infile:
                        pair = line.rstrip().split(sep)
                        outfile.write(sep.join([pair[0], "interacts_with", pair[-1]]))

            sys.stdout.write("File successfully converted\n")
            return output_file

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def sifToEdgelist(file: str, sep=None, header: bool=False, output_file: str=None):
        """
        Convert a Simple Interaction Format file (*SIF*) to an undirected edge-list.
        **CONDITIONS FOR CONVERSIONS:**
        We assume the SIF file contains at least 3 columns, with the *source* nodes in the 1st column and the *target*
        nodes in the 3rd column. All the other values from the 4th column onwards are assumed to be other target nodes
        connected to the input node. Thus, no attributes are present in the sif file.
        For more info on the SIF file format specification, please visit the official Cytoscape documentation
        at http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html.
        **WARNING** If a header is present, the cells corresponding to columns 1 and 3 will be rewritten.
        :param str file: a valid path to the input SIF file
        :param str sep: a string that specifies the file separator of both input and output files. If 'None' (default),
        we assume a tabulator character as separator.
        :param bool header: Whether to report the header line from the input (if present) to the output file.
        Default if 'False' (input file contains no header)
        :param str output_file: The path to the output file. If None, the output file will be in the current directory,
        and its file extension will be *egl*
        :return: the path to the output file
        """

        if not output_file:
            output_file = os.path.join(os.getcwd(),
                                       "_".join([os.path.splitext(os.path.basename(os.path.abspath(file)))[0],
                                                 randomword(4)])) + ".egl"
        elif os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. It will be overwritten\n".format(output_file))

        # TODO: Add sifutils class with these functionalities
        # sifutils = sif(file=file, header=header, sep=sep)
        # if sifutils.is_direct():
        #     raise UnproperlyFormattedFileError(
        #         "The SIF file represents a direct graph, which is not currently supported")
        # elif sifutils.is_hypergraph():
        #     raise UnproperlyFormattedFileError("The SIF file contains multiple edges")
        # else:

        with open(file, "r") as infile:
            with open(output_file, "w") as outfile:
                if header:
                    headerrow = infile.readline().rstrip()
                    outfile.write(headerrow + '\n')

                for line in infile:
                    tmp = line.rstrip().split(sep)
                    del tmp[1]  # remove the interaction column
                    if len(tmp) < 2:
                        sys.stdout.write("node {} is an isolate and will not be included in the edge-list\n".format(tmp[0]))
                    elif len(tmp) > 2:
                        for i in range(1, len(tmp)):
                            outfile.write(tmp[0] + "\t" + tmp[i] + '\n')
                    else:
                        outfile.write(tmp[0] + "\t" + tmp[1] + '\n')

        return output_file
