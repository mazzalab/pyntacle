__author__ = u"Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2019  Tommaso Mazza <t,mazza@css-mendel.it>
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
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test.sif')
        PyntacleExporter.Sif(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, sif case')

    def test_convert_egl(self):
        sys.stdout.write("Testing egl conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.egl')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test.egl')
        PyntacleExporter.EdgeList(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, edgelist case')

    def test_convert_bin(self):
        sys.stdout.write("Testing bin conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.graph')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test.graph')
        PyntacleExporter.Binary(graph=self.graph, file=fileout)
        if sys.version_info >= (3, 6):
            self.assertEqual(getmd5_bin(fileout), getmd5_bin(expected), 'Wrong checksum for Convert, binary case')

    def test_convert_dot(self):
        sys.stdout.write("Testing dot conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.dot')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test.dot')
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
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test.adjm')
        PyntacleExporter.AdjacencyMatrix(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, adjm case')

    def test_egl_to_sif(self):
        sys.stdout.write("Testing egl to sif conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.egl')
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_egltosif.sif')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test_egltosif.sif')
        PyntacleConverter.edgelistToSif(file=filein, sep='\t',
                                        header=True, output_file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, egl to sif case')

    def test_sif_to_egl(self):
        sys.stdout.write("Testing sif to egl conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.sif')
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_siftoegl.egl')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test_siftoegl.egl')
        PyntacleConverter.sifToEdgelist(file=filein, sep='\t',
                                        header=True, output_file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, sif to egl case')

    def test_dot_to_adjm(self):
        sys.stdout.write("Testing dot to adjm conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.dot')
        self.graph = PyntacleImporter.Dot(file=os.path.join(current_dir, filein))
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_dottoeadjm.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/test_dottoeadjm.adjm')
        PyntacleExporter.AdjacencyMatrix(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, dot to adjm case')
    
    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'pyntacletests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)

if __name__ == '__main__':
    unittest.main()
