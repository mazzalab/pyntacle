__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2020  Tommaso Mazza <t,mazza@css-mendel.it>
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
current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

from io_stream.importer import PyntacleImporter
from graph_operations.set_operations import GraphSetOps
from io_stream.exporter import PyntacleExporter
from pyntacletests import getmd5


class WidgetTestLogicOps(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.graph1 = PyntacleImporter.AdjacencyMatrix(file=os.path.join(current_dir, 'pyntacletests/test_sets/input/set1.txt'), sep='\t', header=True)
        self.graph2 = PyntacleImporter.AdjacencyMatrix(file=os.path.join(current_dir, 'pyntacletests/test_sets/input/set2.txt'), sep='\t', header=True)

    def test_union(self):
        sys.stdout.write("Testing set union\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/result_set.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/set/result_union.adjm')
        output_graph = GraphSetOps.union(self.graph1, self.graph2, new_graph_name='result_set')
        PyntacleExporter.AdjacencyMatrix(graph=output_graph, file=os.path.join(current_dir, 'pyntacletests/test_sets/tmp/result_set.adjm'),
                                         sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, union case')

    def test_intersect(self):
        sys.stdout.write("Testing set intersect\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/result_set.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/set/result_intersect.adjm')
        output_graph = GraphSetOps.intersection(self.graph1, self.graph2, new_graph_name='result_set')
        PyntacleExporter.AdjacencyMatrix(graph=output_graph, file=os.path.join(current_dir, 'pyntacletests/test_sets/tmp/result_set.adjm'),
                                         sep='\t', header=True)
        if sys.version_info >= (3, 6):
            self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, intersect case')

    def test_difference(self):
        sys.stdout.write("Testing set difference\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/result_set.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/set/result_difference.adjm')
        output_graph = GraphSetOps.difference(self.graph1, self.graph2, new_graph_name='result_set')
        PyntacleExporter.AdjacencyMatrix(graph=output_graph, file=os.path.join(current_dir, 'pyntacletests/test_sets/tmp/result_set.adjm'),
                                         sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, difference case')

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'pyntacletests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
