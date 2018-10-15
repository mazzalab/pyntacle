__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.4"
__maintainer__ = "Daniele Capocefalo"
__email__ = "d.capocefalo@css-mendel.it"
__status__ = "Development"
__date__ = "27 February 2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t,mazza@css-mendel.it>
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

import unittest
import os, sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
current_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
from io_stream.importer import PyntacleImporter
from io_stream.exporter import PyntacleExporter
from io_stream.converter import PyntacleConverter
from pyntacletests import getmd5, getmd5_bin
import re

class WidgetTestConvert(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.graph = PyntacleImporter.AdjacencyMatrix(file=os.path.join(current_dir,
                                                                        'pyntacletests/test_sets/input/figure_8.txt'),
                                                      sep='\t', header=True)

    def test_convert_sif(self):
        sys.stdout.write("Testing sif conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.sif')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.sif')
        PyntacleExporter.Sif(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, sif case')

    def test_convert_egl(self):
        sys.stdout.write("Testing egl conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.egl')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.egl')
        PyntacleExporter.EdgeList(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, edgelist case')

    def test_convert_bin(self):
        sys.stdout.write("Testing bin conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.graph')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.graph')
        PyntacleExporter.Binary(graph=self.graph, file=fileout)
        if sys.version_info >= (3, 6):
            self.assertEqual(getmd5_bin(fileout), getmd5_bin(expected), 'Wrong checksum for Convert, binary case')

    def test_convert_dot(self):
        sys.stdout.write("Testing dot conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.dot')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.dot')
        PyntacleExporter.Dot(graph=self.graph, file=fileout)
        with open(fileout, 'r') as fin:
            next(fin)
            data = fin.read()
            
        with open(expected, 'r') as exp:
            data_exp = exp.read()
        o = set(re.findall(r"name=[A-z0-9]+|[A-z0-9]+ -- [A-z0-9]+", data))
        e = set(re.findall(r"name=[A-z0-9]+|[A-z0-9]+ -- [A-z0-9]+", data_exp))
        self.assertEqual(o, e,
                         'Wrong checksum for Convert, dot case')

    def test_convert_adjm(self):
        sys.stdout.write("Testing adjm conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.txt')
        PyntacleExporter.AdjacencyMatrix(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, adjm case')

    def test_egl_to_sif(self):
        sys.stdout.write("Testing egl to sif conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.egl')
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_egltosif.sif')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8_egltosif.sif')
        PyntacleConverter.edgelistToSif(file=filein, sep='\t',
                                        header=True, output_file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, egl to sif case')

    def test_sif_to_egl(self):
        sys.stdout.write("Testing sif to egl conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.sif')
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_siftoegl.egl')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8_siftoegl.egl')
        PyntacleConverter.sifToEdgelist(file=filein, sep='\t',
                                        header=True, output_file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, sif to egl case')
    
    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'pyntacletests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)

if __name__ == '__main__':
    unittest.main()
