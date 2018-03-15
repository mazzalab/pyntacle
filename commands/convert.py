import os
import sys
from warnings import simplefilter

from config import *
from io_stream.edgelist_to_sif import EdgeListToSif
# output format
from io_stream.exporter import PyntacleExporter
from misc.graph_load import *

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


class Convert():
    """
    **[EXPAND]**
    """
    def __init__(self, args):
        self.logging = log
        self.args = args

    def run(self):
        # dictionary that stores the basename of the output file
        cursor = CursorAnimation()
        cursor.daemon = True
        cursor.start()
        if self.args.no_header:
            header = False
        else:
            header = True

        if self.args.no_output_header:
            output_header = False
        else:
            output_header = True

        if self.args.input_file is None:
            self.logging.error(
                "Please specify an input file using the -i option.".format(self.args.input_file))
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            self.logging.error("Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit(1)

        if self.args.output_file is None:
            self.args.output_file = os.path.splitext(os.path.basename(self.args.input_file))[0]
            sys.stdout.write("Output file name will be the basename of the input file ({})\n".format(self.args.output_file))
            #print(self.args.output_file)

        separator = separator_detect(self.args.input_file)

        # self.logging.debug("Header:{}".format(header))
        # self.logging.debug("Separator:{}".format(repr(separator)))

        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: Output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        sys.stdout.write("Converting  input file {0} to requested output file: {1}\n".format(self.args.input_file, self.args.output_file))


        if self.args.output_separator is None:
            sys.stdout.write("Using the same separator used in the input file\n")
            self.args.output_separator = separator

        out_form = format_dictionary.get(self.args.output_format, "NA")

        if out_form == "NA":
            sys.stderr.write("Output extension specified is not supported, see  \"--help\" for more info\n. Quitting")
            sys.exit(1)

        output_path = os.path.join(self.args.directory, ".".join([self.args.output_file, out_form]))
        init_graph = GraphLoad(input_file=self.args.input_file, file_format=format_dictionary.get(self.args.format, "NA"), header=header)

        # special case: convert an edgelist to a sif file

        if format_dictionary.get(self.args.format, "NA") == "egl" and  out_form == "sif":

            sys.stdout.write("Converting edgelist to sif. Path to the output file:{}\n".format(output_path))

            EdgeListToSif(input_file=self.args.input_file, header=header, separator=separator).get_sif(
                output_file=output_path, separator=separator, header=output_header)

        else:

            graph = init_graph.graph_load()
            in_form = init_graph.get_format()
            
            if in_form == out_form:
                sys.stdout.write("The output format specified is the same as the input format. Quitting.\n")
                sys.exit(0)
                
            if out_form == "adjm":
                sys.stdout.write("Converting input file {0} to adjacency matrix at path {1} \n".format(
                    os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.AdjacencyMatrix(graph, output_path, sep=self.args.output_separator,
                                         header=output_header)

            elif out_form == "egl":
                sys.stdout.write(
                    "Converting input file {0} to edge list at path {1} \n".format(
                        os.path.abspath(self.args.input_file),
                        output_path))
                PyntacleExporter.EdgeList(graph, output_path, sep=self.args.output_separator, header=output_header)

            elif out_form == "sif":
                sys.stdout.write(
                    "Converting input file {0} to Simple Interaction Format (sif) at path {1} \n".format(
                        os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.Sif(graph, output_path, sep=self.args.output_separator, header=output_header)

            elif out_form == "dot":
                # Ignore ugly RuntimeWarnings while converting to dot
                simplefilter("ignore", RuntimeWarning)

                sys.stdout.write(
                    "Converting input file {0} to dot file using igraph utilities at path {1} (output separator will be ignored)\n".format(
                        os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.Dot(graph, output_path)


            elif out_form == "graph":
                sys.stdout.write(
                    "Converting input file {0} to a binary file at path {1} (output separator will be ignored)\n".format(
                        os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.Binary(graph, output_path)

            cursor.stop()
            sys.stdout.write("{} converted successfully\n".format(os.path.basename(self.args.input_file)))
            sys.exit(0)
