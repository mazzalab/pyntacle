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
this class covers the processing of an edgelist to a  simple interaction format (sif) that can be passed to cytoscape
'''

import pandas as pd
from config import *
from tools import edgelist_utils

#todo rework all this
class EdgeListToCytoscape:
    '''
    This class converts an edge list into a sif file (simple interaction format) in the most basic way:
    a tab delimited file in which each line represent an edge (so node A \t node B)
    '''

    def __init__(self, input_file: str, header=False, separator=None):
        self.logger = log

        if not os.path.exists(input_file):
            raise FileNotFoundError("File does not exist")

        else:

            eglutils = edgelist_utils.EglUtils(file=input_file, header=header, separator=separator)
            isdirect = eglutils.is_direct()
            ismulti = eglutils.is_pyntacle_ready()

            if isdirect:
                self.logger.warning("The edge list is not direct.")

            if ismulti:
                self.logger.warning(
                    "The edge list is a multigraph. Be advised that it will not work with other pyntacle Features")

            self.infile = input_file
            self.headerflag = header

            if separator is None:
                self.logger.warning("No separator specified, using \"\\t\" as default separator")
                self.separator = "\t"

            else:
                if not isinstance(separator, str):
                    self.logger.error("separator must be a string. Quitting.")
                    sys.exit(1)

                else:
                    self.separator = separator

            # check that the file contains 2 columns
            checkfile = pd.read_csv(filepath_or_buffer=self.infile, sep=self.separator)
            if len(checkfile.columns) != 2:
                self.logger.error("Input file is not an edgelist (does not have 2 columns")
                sys.exit(1)

    def __edgelist_parser(self):
        '''
        Hidden function that stores and edgelist into a list of lists
        '''

        self.edgelist = []
        with open(self.infile, "r") as inf:
            if self.headerflag:
                self.headerstring = inf.readline().rstrip().split(self.separator)
                # print(self.headerstring)
                # input()

            for line in inf:
                pair = line.rstrip().split(self.separator)
                self.edgelist.append(pair)  # a list of lists

    def get_sif(self, output_file=None, separator=None, header=False):
        '''
        **[EXPAND]**
        
        :param output_file: path to output file. Default: None. If not specified, a file with the same name will be used but with the .sif extension
        :param separator: which separator to use when building a sif file. Default is "\t"
        '''

        self.__edgelist_parser()  # reparse edgelist

        if output_file is None:
            output_file = os.path.splitext(os.path.abspath(self.infile))[0] + ".sif"
            self.logger.info("No output file specified. Output file will be {}".format(os.path.abspath(output_file)))

        if os.path.exists(output_file):
            self.logger.error("Output file already exists, specify a different file name")
            sys.exit(1)

        if separator is None:
            self.logger.warning("No separator specified, using \"\\t\" as output separator")
            separator = "\t"

        else:
            if not isinstance(separator, str):
                self.logger.error("separator must be a string. Quitting.")
                sys.exit(1)

        # remove all multiple istances from the edgelist
        siftuple = tuple(tuple(x) for x in self.edgelist)
        sifcleaned = set(tuple(sorted(l)) for l in siftuple)
        siflist = [list(x) for x in sifcleaned]

        with open(output_file, "w") as outfile:
            self.logger.info("Creating sif file")

            if header:
                outfile.write(separator.join([self.headerstring[0], "Interaction", self.headerstring[-1]]) + "\n")

            for couple in siflist:
                outfile.write(separator.join([couple[0], "interacts_with", couple[1]]) + "\n")

        self.logger.info("file converted")
        self.logger.info("path to file is %s".format(output_file))

