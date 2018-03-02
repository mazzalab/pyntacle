import unittest
import os, sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from io_stream.importer import PyntacleImporter
from io_stream.exporter import PyntacleExporter
from test import getmd5, getmd5_bin


class WidgetTestConvert(unittest.TestCase):
    def setUp(self):
        self.graph = PyntacleImporter.AdjacencyMatrix(file='test/test_sets/input/figure_8.txt', sep='\t', header=True)
        
    def test_convert_sif(self):
        sys.stdout.write("Testing sif conversion\n")
        fileout = 'test/test_sets/tmp/test.sif'
        expected = 'test/test_sets/output/convert/figure8.sif'
        PyntacleExporter.Sif(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, sif case')
    
    def test_convert_egl(self):
        sys.stdout.write("Testing egl conversion\n")
        fileout = 'test/test_sets/tmp/test.egl'
        expected = 'test/test_sets/output/convert/figure8.egl'
        PyntacleExporter.EdgeList(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, edgelist case')

    def test_convert_bin(self):
        sys.stdout.write("Testing bin conversion\n")
        fileout = 'test/test_sets/tmp/test.graph'
        expected = 'test/test_sets/output/convert/figure8.graph'
        PyntacleExporter.Binary(graph=self.graph, file=fileout)
        self.assertEqual(getmd5_bin(fileout), getmd5_bin(expected), 'Wrong checksum for Convert, binary case')

    def test_convert_dot(self):
        sys.stdout.write("Testing dot conversion\n")
        fileout = 'test/test_sets/tmp/test.dot'
        expected = 'test/test_sets/output/convert/figure8.dot'
        PyntacleExporter.Dot(graph=self.graph, file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, dot case')

    def test_convert_adjm(self):
        sys.stdout.write("Testing adjm conversion\n")
        fileout = 'test/test_sets/tmp/test.adjm'
        expected = 'test/test_sets/input/figure_8.txt'
        PyntacleExporter.AdjacencyMatrix(graph=self.graph, file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, adjm case')
        
    def tearDown(self):
        files = glob.glob('test/test_sets/tmp/*')
        for f in files:
            os.remove(f)

if __name__ == '__main__':
    widget_suite = unittest.TestSuite()
    widget_suite.addTest(WidgetTestConvert('test_convert_sif'))
    widget_suite.addTest(WidgetTestConvert('test_convert_egl'))
    widget_suite.addTest(WidgetTestConvert('test_convert_bin'))
    widget_suite.addTest(WidgetTestConvert('test_convert_dot'))
    widget_suite.addTest(WidgetTestConvert('test_convert_adjm'))
    runner = unittest.TextTestRunner()
    runner.run(widget_suite)
