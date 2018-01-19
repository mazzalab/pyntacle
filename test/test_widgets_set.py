import unittest
import os, sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from misc.graph_load import GraphLoad, separator_detect
from graph_operations.set_graphs import GraphSetter
from io_stream.graph_to_adjacencymatrix import GraphToAdjacencyMatrix
from test import getmd5

class WidgetTestSet(unittest.TestCase):
    def setUp(self):
        init_graph1 = GraphLoad(input_file='test/test_sets/input/set1.txt', file_format='adjm', header=True)
        self.graph1 = init_graph1.graph_load()
        
        init_graph2 = GraphLoad(input_file='test/test_sets/input/set2.txt', file_format='adjm', header=True)
        self.graph2 = init_graph2.graph_load()
        self.setter = GraphSetter(graph1=self.graph1, graph2=self.graph2, new_name='result_set')

    def test_union(self):
        sys.stdout.write("Testing set union\n")
        fileout = 'test/test_sets/tmp/result_set.adjm'
        expected = 'test/test_sets/output/set/result_union.adjm'
        output_graph = self.setter.union()
        GraphToAdjacencyMatrix(graph=output_graph).export_graph(sep='\t',
                                                         file_name='test/test_sets/tmp/result_set.adjm',
                                                         header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, union case')

    def test_intersect(self):
        sys.stdout.write("Testing set intersect\n")
        fileout = 'test/test_sets/tmp/result_set.adjm'
        expected = 'test/test_sets/output/set/result_intersect.adjm'
        output_graph = self.setter.intersection()
        GraphToAdjacencyMatrix(graph=output_graph).export_graph(sep='\t',
                                                                file_name='test/test_sets/tmp/result_set.adjm',
                                                                header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, intersect case')

    def test_difference(self):
        sys.stdout.write("Testing set difference\n")
        fileout = 'test/test_sets/tmp/result_set.adjm'
        expected = 'test/test_sets/output/set/result_difference.adjm'
        output_graph = self.setter.difference()
        GraphToAdjacencyMatrix(graph=output_graph).export_graph(sep='\t',
                                                                file_name='test/test_sets/tmp/result_set.adjm',
                                                                header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Set, difference case')

    def tearDown(self):
        files = glob.glob('test/test_sets/tmp/*')
        for f in files:
            os.remove(f)
