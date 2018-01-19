import unittest
import os, sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from misc.graph_load import GraphLoad, separator_detect
from io_stream.graph_to_adjacencymatrix import GraphToAdjacencyMatrix
from io_stream.graph_to_binary import GraphToBinary
from io_stream.graph_to_dot import GraphToDot
from io_stream.graph_to_edgelist import GraphToEdgeList
from io_stream.graph_to_sif import GraphToSif
from test import getmd5, getmd5_bin




class WidgetTestConvert(unittest.TestCase):
    def setUp(self):
        init_graph = GraphLoad(input_file='test/test_sets/input/figure_8.txt', file_format='adjm', header=True)
        self.graph = init_graph.graph_load()
        
    def test_convert_sif(self):
        sys.stdout.write("Testing sif conversion\n")
        fileout = 'test/test_sets/tmp/test.sif'
        expected = 'test/test_sets/output/convert/figure8.sif'
        GraphToSif(graph=self.graph).export_graph(sep='\t', file_name=fileout, header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, sif case')
    
    def test_convert_egl(self):
        sys.stdout.write("Testing egl conversion\n")
        fileout = 'test/test_sets/tmp/test.egl'
        expected = 'test/test_sets/output/convert/figure8.egl'
        GraphToEdgeList(graph=self.graph).export_graph(sep='\t', file_name=fileout, header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, edgelist case')

    def test_convert_bin(self):
        sys.stdout.write("Testing bin conversion\n")
        fileout = 'test/test_sets/tmp/test.graph'
        expected = 'test/test_sets/output/convert/figure8.graph'
        GraphToBinary(graph=self.graph).save(file_name=fileout)
        self.assertEqual(getmd5_bin(fileout), getmd5_bin(expected), 'Wrong checksum for Convert, binary case')

    def test_convert_dot(self):
        sys.stdout.write("Testing dot conversion\n")
        fileout = 'test/test_sets/tmp/test.dot'
        expected = 'test/test_sets/output/convert/figure8.dot'
        GraphToDot(graph=self.graph).export_graph(file_name=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, dot case')

    def test_convert_adjm(self):
        sys.stdout.write("Testing adjm conversion\n")
        fileout = 'test/test_sets/tmp/test.adjm'
        expected = 'test/test_sets/input/figure_8.txt'
        GraphToAdjacencyMatrix(graph=self.graph).export_graph(sep='\t',
                                                         file_name=fileout,
                                                         header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, adjm case')
        
    def tearDown(self):
        files = glob.glob('test/test_sets/tmp/*')
        for f in files:
            os.remove(f)
