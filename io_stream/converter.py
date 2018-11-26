"""
Provide conversion routines between different graph file formats
"""

__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
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
from tools.edgelist_utils import EglUtils
from private.io_utils import input_file_checker, separator_sniffer, randomword


class PyntacleConverter:
    """
    This class is designed to convert one graph file format to another, without resorting to iGraph's internal methods.
    """

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def edgelistToSif(file: str, sep=None, header: bool=False, output_file: str=None, output_sep: str="\t") -> str:
        """
        Convert as an edge-list file into a Simple Interaction File Format (*SIF*) file.
        If the edge-list file contains an header line, this will be written into the SIF file. The *interaction type*,
        required by SIF will be always *interacts_with* between any pair of interacting nodes.
        For more info on the SIF file format specification, please visit the official Cytoscape documentation
        at http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html.
        **WARNING** If a header is present, the cells corresponding to columns 1 and 3 will be rewritten.
        :param str file: a valid path to the input edge-list file
        :param str sep: a string that specifies the file separator of both input and output files. If 'None' (default), we will guess it from the first line of the file.
        :param bool header: Whether to report the header line from the input (if present) to the output file.
        Default if 'False' (input file contains no header)
        :param str output_file: The path to the output file. If None, the output file will be in the current directory,
        :param str output_sep: The output separator of choice. By default, we assume a tabular character is the one that is best suited for SIF files.
        and its file extension will be *sif*
        :return: the path to the output file
        """

        if not output_file:
            output_file = os.path.splitext(os.path.basename(os.path.abspath(file)))[0] + randomword(4) + ".sif"

        elif os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. It will be overwritten\n".format(output_file))

        if not isinstance(output_sep, str):
            raise TypeError("\"output_sep\" must be a string, {} found".format(type(output_sep).__name__))

        eglutils = EglUtils(file=file, header=header, sep=sep)

        if eglutils.is_direct():
            raise ValueError(
                "Edgelist is not ready to be parsed by Pyntacle, it's direct. Use the `edgelist_utils` module in `tools` to make it undirect")

        elif eglutils.is_multigraph():
            raise ValueError(
                "Edgelist contains multiple edges. It is not ready to be parsed by Pyntacle, Use the `edgelist_utils` module in `tools` to turn it into a simple graph.")

        else: #import the sif file into memory, transform it into a list of lists (each sublist represent each line), then sort it in order to remove the double occurrence of the link
            with open(file, "r") as infile:
                if header:
                    headlist = infile.readline().rstrip().split(sep)
                    headlist = [output_sep.join([headlist[0],"Interaction",headlist[1]])]

                edglist = [x.rstrip().split(sep) for x in infile.readlines()]
                siflist = sorted(set(tuple(sorted(x)) for x in edglist))
                siflist = [list(x) for x in siflist]
                siflist = [output_sep.join([x[0], "interacts_with", x[1]]) for x in siflist] #this is the final object that wil be written to the output file

            if header:
                siflist = headlist + siflist #re-adds the header

            with open(output_file, "w") as outfile:
                outfile.writelines([x + "\n" for x in siflist]) #convert each sublist into a string and use the writelines method to dump everything into a file quickly.

            sys.stdout.write("Edge list successfully converted to SIF at path {}\n".format(output_file))
            return output_file

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def sifToEdgelist(file: str, sep=None, header: bool=False, output_file: str=None, output_sep: str="\t"):
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
        :param str output_sep: The output separator of choice. By default, we assume a tabular character is the one that is best suited for SIF files.
        and its file extension will be *sif*
        :return: the path to the output file
        """

        if not isinstance(output_sep, str):
            raise TypeError("\"output_sep\" must be a string, {} found".format(type(output_sep).__name__))

        if not output_file:
            output_file = os.path.join(os.getcwd(),
                                       "_".join([os.path.splitext(os.path.basename(os.path.abspath(file)))[0],
                                                 randomword(4)])) + ".egl"
        elif os.path.exists(output_file):
            sys.stdout.write("A file named {} already exists. It will be overwritten\n".format(output_file))

        with open(file, "r") as infile:
            with open(output_file, "w") as outfile:
                if header:
                    headerrow = infile.readline().rstrip().split(sep)
                    del headerrow[1] #delete the name of the interaction
                    outfile.write(output_sep.join(headerrow) + '\n')

                for line in infile:
                    tmp = line.rstrip().split(sep)
                    del tmp[1]  # remove the interaction column
                    if len(tmp) < 2:
                        sys.stdout.write("node {} is an isolate and will not be included in the edge-list (as edge lists just represent connected nodes)\n".format(tmp[0]))
                    elif len(tmp) > 2:
                        for i in range(1, len(tmp)):
                            outfile.write(tmp[0] + "\t" + tmp[i] + '\n')
                            outfile.write(tmp[i] + "\t" + tmp[0] + '\n')
                    else:
                        outfile.write(tmp[0] + "\t" + tmp[1] + '\n')
                        outfile.write(tmp[1] + "\t" + tmp[0] + '\n')
        sys.stdout.write("SIF successfully converted to edge list at path {}\n".format(output_file))
        return output_file
