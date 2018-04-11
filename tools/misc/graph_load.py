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

# external libraries
from config import *
import csv
import numpy as np
from tools.misc.binarycheck import is_binary_file
from tools.misc.enums import SP_implementations
# pyntacle Libraries
from io_stream.importer import PyntacleImporter
from tools.graph_utils import GraphUtils
from tools.add_attributes import AddAttributes


def separator_detect(filename):
    """
    Uses csv.Sniffer to detect the delimiter in the
    first line of a table.
    :param str filename: input file
    :return: the separator as a string
    """
    with open(filename) as f:
        try:
            firstline = f.readline()
        except UnicodeDecodeError:
            return('\t')
        else:
            sniffer = csv.Sniffer()
            separator = sniffer.sniff(firstline).delimiter
            return separator


class GraphLoad():
    def __init__(self, input_file, file_format, header):
        self.logger = log
        self.input_file = input_file

        self.file_format = file_format
        if self.file_format == "NA":
            self.logger.info("Unspecified or unrecognized file format. Will try to guess it.")

        self.header = header
        
    def get_format(self):
        return self.file_format
    
    def graph_load(self):
        
        # First of all, check if binary. If so, any attempt to read as text would fail with UnicodeDecodeError.

        if is_binary_file(self.input_file) and self.file_format == "NA":
            self.logger.info("Guessed file format: binary")
            self.file_format = 'graph'
            self.header = False
            
        # Separator sniffer
        if self.file_format != 'graph':
            separator = separator_detect(self.input_file)

        # If no format is specified, the header, separator and format itself will be guessed
        if self.file_format == "NA":
            self.logger.info("Trying to guess input format for file {}".format(self.input_file))
            self.file_format, self.header, separator = self.guess_format(self.input_file)

        # Graph import
        if self.file_format == 'egl':
            graph = PyntacleImporter.EdgeList(file_=self.input_file, sep=separator, header=self.header)
            # try:
            #     graph = EdgeListToGraph().import_graph(file_name=self.input_file, header=self.header,
            #                                            separator=separator)

            # except (ValueError):
            #     if not self.header: #in case header has been specified
            #         sys.stderr.write(
            #             "Edge List is direct or edge list file is malformed. Please note that you specified the header is not present, If that's not the case, remove the \"--no-header\" option. Quitting.\n")
            #         sys.exit(1)
            #     else:
            #         sys.stderr.write(
            #             "Edge List is direct or edge list file is malformed. Please note that you specified the header was present. If that's not the case, use the \"--no-header\" option. Quitting.\n")
            #         sys.exit(1)

        elif self.file_format == 'adjm':
            try:
                graph = PyntacleImporter.AdjacencyMatrix(file=self.input_file, sep=separator,
                                                              header=self.header)
            except (ValueError):
                if not self.header: #in case header has been specified
                    sys.stderr.write(
                        "Adjacency Matrix is either direct or malformed. Please note that you specified the header is not present, If that's not the case, remove the \"--no-header\" option. Quitting.\n")
                    sys.exit(1)
                else:
                    sys.stderr.write(
                        "Adjacency Matrix is either direct or malformed. Please note that you specified the header was present. If that's not the case, use the \"--no-header\" option. Quitting.\n")
                    sys.exit(1)

        elif self.file_format == 'graph':
    
            try:
                graph = PyntacleImporter.Binary(self.input_file)
                separator = None

            except IOError:
                sys.stderr.write(
                    "Binary format does not contain an igraph.Graph object or the Graph passed is invalid. check your binary. Quitting.\n")
                sys.exit(1)


        elif self.file_format == 'dot':

            try:
                graph = PyntacleImporter.Dot(self.input_file)
            except:
                sys.stderr.write(
                    "Dot file is not supporter by our parser. Or other formatting errors has occured. Please check our documentation in order to check out DOT file specifications. Quitting.\n")
                sys.exit(1)

        elif self.file_format == 'sif':
            try:
                graph = PyntacleImporter.Sif(file=self.input_file, sep=separator, header=self.header)
            except:
                sys.stderr.write(
                    "Sif is unproperly formatted or a header is present and --no-header was declared in input (also check if the separator is correct). Quitting.\n")
                sys.exit(1)

        else:
            sys.stderr.write("Unsupported file format {}. This should not happen. Please send this line to pyntacle Developer. Quitting\n".format(self.file_format))
            sys.exit(1)

        self.logger.debug("Graph: name:{}\tNodes: {}\tEdges: {}".format(graph["name"], graph.vcount(), graph.ecount()))
        self.logger.debug("Header:{}".format(self.header))
        self.logger.debug("Separator:{}".format(repr(separator)))
        
        GraphUtils(graph=graph).graph_checker()

        return graph

    def guess_format(self, filename):
        """
        Tries to guess the input format using several criteria:
        the extension first and, if unsuccessful, by the matrix shape
        
        :param filename: input text file
        :return: guessed format, header and separator
        """
        self.logger.info(
            "Guessing input format. It could take some time for large files; use the option --format to skip this part.")
        valid_extensions = {'.adjm': 'adjm', '.adjmat': 'adjm', '.egl': 'egl',
                            '.sif': 'sif', '.dot': 'dot', '.graph': 'graph'}
        file_ext = str.lower(os.path.splitext(filename)[-1])
        if file_ext == '.graph' or file_ext == '.bin':
            self.header = False
            separator = ''
        else:
            separator = separator_detect(filename)

        # Guessing by extension
        if file_ext in valid_extensions:
            self.logger.info("Guessed from extension: {}".format(valid_extensions[file_ext]))
            return valid_extensions[file_ext], self.header, separator
        
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
                    n_cols = len(first_line.split())
                    first_char = first_line[0]
                    if first_char.isspace():
                        start_col = 1
                        n_cols += 1
                    else:
                        start_col = 0
                f = np.genfromtxt(filename, skip_header=1, usecols=(tuple(range(start_col, n_cols))),
                                  delimiter=separator, dtype=str)
            except:
                sys.stderr.write("\nCould not load_graph data from file. Please specify --no-header if necessary.\n")
                sys.exit()
        else:
            try:
                f = np.genfromtxt(filename, dtype=str)
            except:
                sys.stderr.write(
                    "\nCould not load_graph data from file. If it is written in one of the supported formats, "
                    "please specify it with the --format option\n")
                sys.exit()

        if len(f.shape) == 1 or (f.shape[1] >= 3 and (f.shape[1] != f.shape[0] or ('1' not in f or '0' not in f))):
            if len(f.shape) == 1:
                self.logger.warning("WARNING: the input file seems to be very small (1 edge).")
            self.logger.info("Guessed file format: Simple Interaction Format")
            return "sif", self.header, separator

        if f.shape[1] == 2:
            if f.shape[0] == 2 and ('1' in f or '0' in f):
                self.logger.info("Guessed file format: Adjacency Matrix")
                return "adjm", self.header, separator
            else:
                self.logger.info("Guessed file format: Edge List")
                return "egl", self.header, separator
        elif f.shape[1] == f.shape[0] and f.shape[1] > 2:
            self.logger.info("Guessed file format: Adjacency Matrix")
            return "adjm", self.header, separator
        else:
            self.logger.error("It was not possible to guess file format. Please specify it with the --format option.")
            sys.exit()

    def get_header(self):
        '''
        Find if the input file has an header
        
        :return: a boolean True if the file has an header, false otherwise
        '''
        return self.header
