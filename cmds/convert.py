__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
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
from warnings import simplefilter
from io_stream.exporter import PyntacleExporter
from io_stream.converter import PyntacleConverter
from internal.graph_load import GraphLoad, separator_detect

class Convert():

    def __init__(self, args):
        self.logging = log
        self.args = args

    def run(self):
        # dictionary that stores the basename of the output file
        if not self.args.suppress_cursor:
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
            sys.stderr.write(
                "Please specify an input file using the `-i/--input-file` option. Quitting.\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stderr.write("Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit(1)

        if self.args.output_file is None:
            self.args.output_file = os.path.splitext(os.path.basename(self.args.input_file))[0]
            sys.stdout.write("Output file name will be the basename of the input file ({})\n".format(self.args.output_file))
            #print(self.args.output_file)

        if self.args.input_separator is None:
            self.logging.info("Trying to guess input separator...")
            separator = separator_detect(self.args.input_file)

        else:
            separator = self.args.input_separator

        if self.args.output_separator is None:
            sys.stdout.write("Using the same separator used in the input file.\n")
            self.args.output_separator = separator

        if not os.path.isdir(self.args.directory):
            sys.stdout.write("Warning: output directory does not exist, will create one at {}.\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        sys.stdout.write("Converting  input file {0} to requested output file: {1}...\n".format(self.args.input_file, self.args.output_file))

        out_form = format_dictionary.get(self.args.output_format, "NA")

        if out_form == "NA":
            sys.stderr.write("Output extension specified is not supported, see  '--help' for more info. Quitting.\n")
            sys.exit(1)

        output_path = os.path.join(self.args.directory, ".".join([self.args.output_file, out_form]))
        init_graph = GraphLoad(input_file=self.args.input_file, file_format=format_dictionary.get(self.args.format, "NA"), header=header, separator=self.args.input_separator)

        # special cases:
        #1: convert an edgelist to a sif file
        if format_dictionary.get(self.args.format, "NA") == "egl" and out_form == "sif":

            sys.stdout.write("Converting edge list to Simple Interaction Format (SIF).\nPath to the output file:{}\n".format(output_path))
            PyntacleConverter.edgelistToSif(file=self.args.input_file, sep=separator, output_sep=self.args.output_separator, header=output_header, output_file=output_path)

        #2: convert a sif to an edgelist file
        elif format_dictionary.get(self.args.format, "NA") == "sif" and out_form == "egl":
            sys.stdout.write("Converting Simple Interaction Format (SIF) to edge list.\nPath to the output file:{}\n".format(output_path))
            PyntacleConverter.sifToEdgelist(file=self.args.input_file, sep=separator, output_sep=self.args.output_separator,
                                            header=output_header, output_file=output_path)

        else:

            graph = init_graph.graph_load()
            in_form = init_graph.get_format()
            
            if in_form == out_form:
                sys.stderr.write("The output format specified is the same as the input format. Quitting.\n")

                if not self.args.suppress_cursor:
                    cursor.stop()

                sys.exit(0)
                
            if out_form == "adjm":
                sys.stdout.write("Converting input file {0} to adjacency matrix at path {1}...\n".format(
                    os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.AdjacencyMatrix(graph, output_path, sep=self.args.output_separator,
                                         header=output_header)

            elif out_form == "egl":
                sys.stdout.write(
                    "Converting input file {0} to edge list at path {1}...\n".format(
                        os.path.abspath(self.args.input_file),
                        output_path))
                PyntacleExporter.EdgeList(graph, output_path, sep=self.args.output_separator, header=output_header)

            elif out_form == "sif":
                sys.stdout.write(
                    "Converting input file {0} to Simple Interaction Format (SIF) file at path {1}...\n".format(
                        os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.Sif(graph, output_path, sep=self.args.output_separator, header=output_header)

            elif out_form == "dot":
                # Ignore ugly RuntimeWarnings while converting to dot
                simplefilter("ignore", RuntimeWarning)

                sys.stdout.write(
                    "Converting input file {0} to DOT file using igraph utilities at path {1} (output separator will be ignored)...\n".format(
                        os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.Dot(graph, output_path)


            elif out_form == "graph":
                sys.stdout.write(
                    "Converting input file {0} to a binary file  (ending in .graph) at path {1} (output separator will be ignored)...\n".format(
                        os.path.abspath(self.args.input_file), output_path))
                PyntacleExporter.Binary(graph, output_path)

            if not self.args.suppress_cursor:
                cursor.stop()

            sys.stdout.write("Pyntacle convert completed successfully. Ending.\n".format(os.path.basename(self.args.input_file)))
            sys.exit(0)
