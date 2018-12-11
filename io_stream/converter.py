__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "1.0.0"
__maintainer__ = "Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = "Development"
__date__ = "26/11/2018"
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
    r"""
    A series of methods to convert one graph file format to another, without resorting to igraph's internal methods.

    ..note:: This module is still in its primes, be sure to check the documentation regularly to see which conversion tools were added
    """

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def edgelistToSif(file: str, sep: str or None=None, header: bool=False, output_file: str=None, output_sep: str="\t") -> str:
        r"""
        Converts an edge list file into a Simple Interaction File (*SIF*) format.
        If the edge list file contains an header (a first line stating the nature of the nodes),
        this will be written into the SIF file. The *interaction type*, a field required to generate a SIF, is set to
        ``interacts_with`` for each pair of interacting nodes.

        We refer to the `Pyntacle File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html>`_
        for more information on how these network files are structured.

        For more info on the SIF file format specification, we refer the user to the `official Cytoscape documentation <http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html>`_.

        .. note :: while the SIF file is quite relaxed in terms of columns order, we **force** in Pyntacle the more common way in which a SIF file is written, that is

        +------------+--------------+----------------+
        | Input Node | Interaction  | Target Node    |
        +------------+--------------+----------------+
        | A          | Interaction  |    B           |
        +------------+--------------+----------------+

        .. warning:: If a header is present, the cells corresponding to columns 1 and 3 will be rewritten.

        :param str file: The path to the input edge list file.
        :param str, None sep: A string that specifies the file separator of both input and output files. If py:class:'None' (default), we will attempt to guess it from the first line of the file.
        :param bool header: Whether the input file contains a header line to the output file. This header will be reported intgo the output file  Default if `'False`` (input file contains no header).
        :param str, None output_file: The path to the output file, with no extension. If :py:class:`None`, the output file will be in the current directory and will have the same basename of the input file.

        .. note :: The output file extension will be ``.sif``

        :param str output_sep: The output separator of choice. By default, we assume a tabular character (*\\t*) is the one that is best suited for SIF files

        :return str: the path to the output file

        :raise TypeError: if ``output_sep`` is not a string
        :raise ValueError: if the input edge list represent a direct network or contains multiple edges and self loops
        """

        if not output_file:
            output_file = os.path.splitext(os.path.basename(os.path.abspath(file)))[0] + randomword(4) + ".sif"

        elif os.path.exists(output_file):
            sys.stdout.write(u"A file named {} already exists. It will be overwritten\n".format(output_file))

        if not isinstance(output_sep, str):
            raise TypeError(u"\"output_sep\" must be a string, {} found".format(type(output_sep).__name__))

        eglutils = EglUtils(file=file, header=header, sep=sep)

        if eglutils.is_direct():
            raise ValueError(
                u"Edgelist is not ready to be parsed by Pyntacle, it's direct. Use the `edgelist_utils` module in `tools` to make it undirect")

        elif eglutils.is_multigraph():
            raise ValueError(
                u"Edgelist contains multiple edges. It is not ready to be parsed by Pyntacle, Use the `edgelist_utils` module in `tools` to turn it into a simple graph.")

        else: #import the sif file into memory, transform it into a list of lists (each sublist represent each line), then sort it in order to remove the double occurrence of the link
            with open(file, "r") as infile:
                if header:
                    headlist = infile.readline().rstrip().split(sep)
                    headlist = [output_sep.join([headlist[0], u"Interaction", headlist[1]])]

                edglist = [x.rstrip().split(sep) for x in infile.readlines()]
                siflist = sorted(set(tuple(sorted(x)) for x in edglist))
                siflist = [list(x) for x in siflist]
                siflist = [output_sep.join([x[0], u"interacts_with", x[1]]) for x in siflist] #this is the final object that wil be written to the output file

            if header:
                siflist = headlist + siflist #re-adds the header

            with open(output_file, "w") as outfile:
                outfile.writelines([x + "\n" for x in siflist]) #convert each sublist into a string and use the writelines method to dump everything into a file quickly.

            sys.stdout.write(u"Edge list successfully converted to SIF at path {}\n".format(output_file))
            return output_file

    @staticmethod
    @input_file_checker
    @separator_sniffer
    def sifToEdgelist(file: str, sep=None, header: bool=False, output_file: str=None, output_sep: str="\t"):

        r"""
        Convert a Simple Interaction Format file (*SIF*) to an undirected edge list.

        .. note :: while the SIF file is quite relaxed in terms of columns order, we **force** the user to give Pyntacle the more common way in which a SIF file is written (see below) All the other values from the 4th column onwards are assumed to be other target nodes connected to the input node. Thus, no attributes are present in the sif file.

        +------------+--------------+----------------+
        | Input Node | Interaction  | Target Node    |
        +============+==============+================+
        | A          | Interaction  |    B           |
        +------------+--------------+----------------+



        We refer to the `Pyntacle File Formats Guide <http://pyntacle.css-mendel.it/resources/file_formats/file_formats.html>`_
        for more information on how these network files are structured.

        For more info on the SIF file format specification, we refer the user to the `official Cytoscape documentation <http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html>`_.

        .. warning:: If a header is present, the cells corresponding to columns 1 and 3 will be rewritten.

        :param str file: a valid path to the input SIF file
        :param str, None sep: A string that specifies the file separator of both input and output files. If py:class:'None' (default), we will attempt to guess it from the first line of the file.
        :param bool header: Whether the input file contains a header line to the output file. This header will be reported intgo the output file  Default if `'False`` (input file contains no header).
        :param str, None output_file: The path to the output file, with no extension. If :py:class:`None`, the output file will be in the current directory and will have the same basename of the input file.
        .. note :: The output file extension will be ``.egl``

        :param str output_sep: The output separator of choice. By default, we assume a tabular character (*\\t*) is the one that is best suited for edge lists

        :return str: the path to the output file

        :raise TypeError: if ``output_sep`` is not a string
        """
        if not isinstance(output_sep, str):
            raise TypeError(u"\"output_sep\" must be a string, {} found".format(type(output_sep).__name__))

        if not output_file:
            output_file = os.path.join(os.getcwd(),
                                       "_".join([os.path.splitext(os.path.basename(os.path.abspath(file)))[0],
                                                 randomword(4)])) + ".egl"
        elif os.path.exists(output_file):
            sys.stdout.write(u"A file named {} already exists. It will be overwritten\n".format(output_file))

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
                        sys.stdout.write(u"node {} is an isolate and will not be included in the edge-list (as edge lists just represent connected nodes)\n".format(tmp[0]))
                    elif len(tmp) > 2:
                        for i in range(1, len(tmp)):
                            outfile.write(tmp[0] + "\t" + tmp[i] + '\n')
                            outfile.write(tmp[i] + "\t" + tmp[0] + '\n')
                    else:
                        outfile.write(tmp[0] + "\t" + tmp[1] + '\n')
                        outfile.write(tmp[1] + "\t" + tmp[0] + '\n')
        sys.stdout.write(u"SIF successfully converted to edge list at path {}\n".format(output_file))
        return output_file
