__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t.mazza@css-mendel.it>
  Viale Regina Margherita 261, 00198 Rome, Italy

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
  """

from config import *
import csv
import numpy as np
from internal.binarycheck import is_binary_file
from io_stream.importer import PyntacleImporter
from tools.graph_utils import GraphUtils
from exceptions.improperly_formatted_file_error import ImproperlyFormattedFileError
import codecs


def unescaped_str(arg_str):
    return codecs.decode(str(arg_str), u'unicode_escape')


def separator_detect(filename):
    r"""
    Uses csv.Sniffer to detect the delimiter in the
    first line of a table.

    :param str filename: input file
    :return: the separator as a string
    """
    with open(filename) as f:
        try:
            firstline = f.readline()
        except UnicodeDecodeError:
            return(u'\t')
        else:
            sniffer = csv.Sniffer()
            separator = sniffer.sniff(firstline).delimiter
            return separator

class GraphLoad():
    def __init__(self, input_file, file_format, header, separator=None):
        self.logger = log
        self.input_file = input_file
        self.file_format = file_format
        if self.file_format == "NA":
            self.logger.info(u"Unspecified or unrecognized file format. Will try to guess it.")

        self.header = header
        self.separator = separator
        
    def get_format(self):
        return self.file_format

    def graph_load(self):
        
        # First of all, check if binary. If so, any attempt to read as text would fail with UnicodeDecodeError.

        if is_binary_file(self.input_file) and self.file_format == "NA":
            self.logger.info(u"Guessed file format: binary")
            self.file_format = 'graph'
            self.header = False
            
        # Separator sniffer
        if self.file_format != 'graph':
            if not self.separator:
                self.separator = separator_detect(self.input_file)

        # If no format is specified, the header, separator and format itself will be guessed
        if self.file_format == "NA":
            self.logger.info(u"Trying to guess input format for file {}".format(self.input_file))
            self.file_format, self.header, self.separator = self.guess_format(self.input_file)

        # Graph import
        if self.file_format == 'egl':
            graph = PyntacleImporter.EdgeList(file=self.input_file, sep=self.separator, header=self.header)

        elif self.file_format == 'adjm':
            try:
                graph = PyntacleImporter.AdjacencyMatrix(file=self.input_file, sep=self.separator, header=self.header)
            except (ValueError):
                if not self.header: #in case header has been specified
                    sys.stderr.write(
                        u"The adjacency matrix is either malformed or represents a directed graph. "
                        "Please note that you specified that the header is not present, If this is not the case, "
                        "remove the \"--no-header\" option\n")
                    sys.exit(1)
                else:
                    sys.stderr.write(
                        u"The adjacency matrix is either malformed or represents a directed graph. "
                        "Please note that you specified that the header is present, If this is not the case,"
                        " use the \"--no-header\" option")
                    sys.exit(1)

        elif self.file_format == 'graph':
    
            try:
                graph = PyntacleImporter.Binary(self.input_file)
                separator = None

            except IOError:
                sys.stderr.write(
                    u"Binary format does not contain an 'igraph.Graph' object or the graph is not compliant to Pyntacle"
                    u"minimum requirements. Quitting\n")
                sys.exit(1)


        elif self.file_format == 'dot':

            try:
                graph = PyntacleImporter.Dot(self.input_file)
            except:
                sys.stderr.write(
                    u"Dot file is not supporter by our parser. Or other formatting errors occurred. "
                    "Please check our documentation in order to check out the DOT file specifications. "
                    "Quitting\n")
                sys.exit(1)

        elif self.file_format == 'sif':
            try:
                graph = PyntacleImporter.Sif(file=self.input_file, sep=self.separator, header=self.header)
            except ImproperlyFormattedFileError:
                sys.stderr.write(
                    u"Sif is unproperly formatted or a header is present and --no-header was declared in "
                    "input (also check if the separator is correct). Quitting\n")
                sys.exit(1)

        else:
            sys.stderr.write(u"Unsupported file format {}. This should not happen. Please send this line to "
                             "pyntacle Developer. Quitting\n".format(self.file_format))
            sys.exit(1)

        self.logger.debug(u"Graph: name:{}\tNodes: {}\tEdges: {}".format(graph["name"], graph.vcount(),
                                                                        graph.ecount()))
        self.logger.debug(u"Header:{}".format(self.header))
        self.logger.debug(u"Separator:{}".format(repr(self.separator)))

        return graph

    def guess_format(self, filename):
        r"""
        Tries to guess the input format using several criteria:
        the extension first and, if unsuccessful, by the matrix shape
        
        :param filename: input text file
        :return: guessed format, header and separator
        """
        self.logger.info(
            "Guessing input format. It could take some time for large files; use the option --format to "
            "skip this part.")
        valid_extensions = {'.adjm': 'adjm', '.adjmat': 'adjm', '.egl': 'egl',
                            '.sif': 'sif', '.dot': 'dot', '.gv': 'dot', '.graph': 'graph'}
        file_ext = str.lower(os.path.splitext(filename)[-1])
        if file_ext == '.graph' or file_ext == '.bin':
            self.header = False
            self.separator = ''
        else:
            if not self.separator:
                self.separator = separator_detect(filename)
            else:
                self.logger.info(u"Separator provided: {}".format(self.separator))
                self.separator = unescaped_str(self.separator)
            
        # Guessing by extension
        if file_ext in valid_extensions:
            self.logger.info(u"Guessed from extension: {}".format(valid_extensions[file_ext]))
            return valid_extensions[file_ext], self.header, self.separator
        
        # Easy .dot guessing by keyword at the beginning
        with open(filename, "r") as filein:
            for line in filein:
                if line.lstrip().startswith('graph'):
                    self.logger.info("Guessed file format: DOT.")
                    return "dot", False, None

        # Real guessing here
        if self.header:
            try:
                with open(filename, "r") as filein:
                    iterator = iter(filein.readline, '')
                    first_line = next(iterator, None).rstrip()
                    n_cols = len(first_line.split(self.separator))
                    first_char = first_line[0]
                    if first_char.isspace() or first_char == self.separator:
                        start_col = 1
                    else:
                        start_col = 0
                f = np.genfromtxt(filename, skip_header=1, usecols=(tuple(range(start_col, n_cols))),
                                  delimiter=self.separator, dtype=str)

            except:
                sys.stderr.write(u"\nCould not load_graph data from file. Please specify --no-header if "
                                 "necessary\n")
                sys.exit()
        else:
            try:
                with open(filename, "r") as filein:
                    iterator = iter(filein.readline, '')
                    first_line = next(iterator, None).rstrip()
                    n_cols = len(first_line.split(self.separator))
                    start_col = 0
                f = np.genfromtxt(filename, skip_header=0, usecols=(tuple(range(start_col, n_cols))),
                                  delimiter=self.separator, dtype=str)
            except:
                sys.stderr.write(
                    u"\nCould not load_graph data from file. If it is written in one of the supported formats,"
                    "please specify it with the --format option, and/or specify the correct field delimiter with --input-separator\n")
                sys.exit()

        if len(f.shape) == 1 or (f.shape[1] >= 3 and (f.shape[1] != f.shape[0] or ('1' not in f or '0' not in f))):
            if len(f.shape) == 1:
                self.logger.warning(u"WARNING: the input file seems to be very small (1 edge).")
            self.logger.info(u"Guessed file format: Simple Interaction Format")
            return "sif", self.header, self.separator

        if f.shape[1] == 2:
            if f.shape[0] == 2 and ('1' in f or '0' in f):
                self.logger.info(u"Guessed file format: Adjacency Matrix")
                return "adjm", self.header, self.separator
            else:
                self.logger.info(u"Guessed file format: Edge List")
                return "egl", self.header, self.separator
        elif f.shape[1] == f.shape[0] and f.shape[1] > 2:
            self.logger.info(u"Guessed file format: Adjacency Matrix")
            return "adjm", self.header, self.separator
        else:
            self.logger.error(u"It was not possible to guess file format. Please specify it with the "
                              " '--format' option.")
            sys.exit()

    def get_header(self):
        r'''
        Finds if the input file has an header.

        :return bool: a boolean True if the file has an header, false otherwise
        '''
        return self.header
