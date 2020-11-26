__author__ = u"Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.3.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2020"
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
from warnings import simplefilter
from io_stream.exporter import PyntacleExporter
from io_stream.converter import PyntacleConverter
from internal.graph_load import GraphLoad, separator_detect


class Convert:
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
                u"Please specify an input file using the `-i/--input-file` option. Quit\n")
            sys.exit(1)

        if not os.path.exists(self.args.input_file):
            sys.stderr.write(u"Cannot find {}. Is the path correct?".format(self.args.input_file))
            sys.exit(1)

        if self.args.input_separator is None:
            separator = separator_detect(self.args.input_file)

        else:
            separator = self.args.input_separator
        
        if self.args.output_file is None:
            self.args.output_file = os.path.splitext(os.path.basename(self.args.input_file))[0]
            sys.stdout.write(
                u"Output file name will be the basename of the input file ({})\n".format(self.args.output_file))

        sys.stdout.write(run_start)
        sys.stdout.write(u"Converting  input file {0} to requested output file: {1}\n".format(
            os.path.basename(self.args.input_file),
            os.path.basename(self.args.output_file)))

        out_format = format_dictionary.get(self.args.output_format, "NA")
        if out_format == "NA":
            sys.stderr.write(
                u"The specified extension for the output file is not supported, see  '--help' for more info. Quit\n")
            sys.exit(1)

        if self.args.output_separator is None:
            sys.stdout.write(u"Using the field separator of the input file in the converted output file\n")
            self.args.output_separator = separator

        if not os.path.isdir(self.args.directory):
            sys.stdout.write(u"WARNING: the output directory does not exist. It will be created at {}\n".format(
                os.path.abspath(self.args.directory)))
            os.makedirs(os.path.abspath(self.args.directory), exist_ok=True)

        output_path = os.path.join(self.args.directory, ".".join([self.args.output_file, out_format]))
        init_graph = GraphLoad(input_file=self.args.input_file, file_format=format_dictionary.get(
            self.args.format, "NA"), header=header, separator=self.args.input_separator)
        input_basename = os.path.basename(self.args.input_file)

        # special cases:
        # 1: convert an edgelist to a sif file
        if format_dictionary.get(self.args.format, "NA") == "egl" and out_format == "sif":
            sys.stdout.write(u"Converting edge-list to SIF\nFull path to the output file:\n{}\n".format(output_path))
            PyntacleConverter.edgelistToSif(file=self.args.input_file, sep=separator, output_sep=self.args.output_separator, header=output_header, output_file=output_path)
        # 2: convert a sif to an edgelist file
        elif format_dictionary.get(self.args.format, "NA") == "sif" and out_format == "egl":
            sys.stdout.write(u"Converting SIF to edge-list\nFull path to the output file:\n{}\n".format(output_path))
            PyntacleConverter.sifToEdgelist(file=self.args.input_file, sep=separator, output_sep=self.args.output_separator,
                                            header=output_header, output_file=output_path)
        else:
            graph = init_graph.graph_load()
            in_form = init_graph.get_format()
            
            if in_form == out_format:
                sys.stderr.write(u"The specified format of the output file is the same as the input file. Quit\n")
                sys.exit(1)
                
            if out_format == "adjm":
                sys.stdout.write(u"Converting the input file {0} to adjacency matrix. Path:\n{1}\n".format(
                    input_basename, output_path))
                PyntacleExporter.AdjacencyMatrix(graph, output_path, sep=self.args.output_separator,
                                         header=output_header)
            elif out_format == "egl":
                sys.stdout.write(
                    u"Converting the input file {0} to edge-list. Path:\n{1}\n".format(
                        input_basename,
                        output_path))
                PyntacleExporter.EdgeList(graph, output_path, sep=self.args.output_separator, header=output_header)
            elif out_format == "sif":
                sys.stdout.write(
                    u"Converting the input file {0} to SIF. Path:\n{1}\n".format(
                        input_basename, output_path))
                PyntacleExporter.Sif(graph, output_path, sep=self.args.output_separator, header=output_header)
            elif out_format == "dot":
                # Ignore ugly RuntimeWarnings while converting to dot
                simplefilter("ignore", RuntimeWarning)

                sys.stdout.write(
                    u"Converting the input file {0} to DOT. Path:\n{1}\n(output separator will be ignored)\n".format(
                        input_basename, output_path))
                PyntacleExporter.Dot(graph, output_path)
            elif out_format == "graph":
                sys.stdout.write(
                    u"Converting the input file {0} to a binary file (with .graph extension). Path:\n{1}\n(output separator will be ignored)\n".format(
                        input_basename, output_path))
                PyntacleExporter.Binary(graph, output_path)

            if not self.args.suppress_cursor:
                cursor.stop()

            sys.stdout.write(section_end)
            sys.stdout.write(u"Pyntacle convert completed successfully. Ending\n".format(os.path.basename(self.args.input_file)))
            sys.exit(0)
