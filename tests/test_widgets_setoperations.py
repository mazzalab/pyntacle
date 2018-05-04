import unittest
import os, sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

from io_stream.importer import PyntacleImporter
from graph_operations.set_operations import GraphOperations
from io_stream.exporter import PyntacleExporter
from tests import getmd5


class WidgetTestLogicOps(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.graph1 = PyntacleImporter.AdjacencyMatrix(file=os.path.join(current_dir, 'tests/test_sets/input/set1.txt'), sep='\t', header=True)
        self.graph2 = PyntacleImporter.AdjacencyMatrix(file=os.path.join(current_dir, 'tests/test_sets/input/set2.txt'), sep='\t', header=True)

    def test_union(self):
        sys.stdout.write("Testing set union\n")
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/result_set.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/set/result_union.adjm')
        output_graph = GraphOperations.union(self.graph1, self.graph2, new_graph_name='result_set')
        PyntacleExporter.AdjacencyMatrix(graph=output_graph, output_file=os.path.join(current_dir, 'tests/test_sets/tmp/result_set.adjm'),
                                         sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, union case')

    def test_intersect(self):
        sys.stdout.write("Testing set intersect\n")
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/result_set.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/set/result_intersect.adjm')
        output_graph = GraphOperations.intersection(self.graph1, self.graph2, new_graph_name='result_set')
        PyntacleExporter.AdjacencyMatrix(graph=output_graph, output_file=os.path.join(current_dir, 'tests/test_sets/tmp/result_set.adjm'),
                                         sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, intersect case')

    def test_difference(self):
        sys.stdout.write("Testing set difference\n")
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/result_set.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/set/result_difference.adjm')
        output_graph = GraphOperations.difference(self.graph1, self.graph2, new_graph_name='result_set')
        PyntacleExporter.AdjacencyMatrix(graph=output_graph, output_file=os.path.join(current_dir, 'tests/test_sets/tmp/result_set.adjm'),
                                         sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, difference case')

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'tests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()
