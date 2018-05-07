import unittest
import os, sys, glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
current_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
from io_stream.importer import PyntacleImporter
from io_stream.exporter import PyntacleExporter
from io_stream.format_converter import FileFormatConvert
from pyntacletests import getmd5, getmd5_bin


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
        PyntacleExporter.Sif(graph=self.graph, output_file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, sif case')

    def test_convert_egl(self):
        sys.stdout.write("Testing egl conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.egl')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.egl')
        PyntacleExporter.EdgeList(graph=self.graph, output_file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Convert, edgelist case')

    def test_convert_bin(self):
        sys.stdout.write("Testing bin conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.graph')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.graph')
        PyntacleExporter.Binary(graph=self.graph, output_file=fileout)
        self.assertEqual(getmd5_bin(fileout), getmd5_bin(expected), 'Wrong checksum for Convert, binary case')

    def test_convert_dot(self):
        sys.stdout.write("Testing dot conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.dot')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8.dot')
        PyntacleExporter.Dot(graph=self.graph, output_file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, dot case')

    def test_convert_adjm(self):
        sys.stdout.write("Testing adjm conversion\n")
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.txt')
        PyntacleExporter.AdjacencyMatrix(graph=self.graph, output_file=fileout, sep='\t', header=True)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, adjm case')

    def test_egl_to_sif(self):
        sys.stdout.write("Testing egl to sif conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.egl')
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_egltosif.sif')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8_egltosif.sif')
        FileFormatConvert.edgelistToSif(file=filein, sep='\t',
                                        header=True, output_file=fileout)
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Convert, egl to sif case')

    def test_sif_to_egl(self):
        sys.stdout.write("Testing sif to egl conversion\n")
        filein = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.sif')
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/test_siftoegl.egl')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/convert/figure8_siftoegl.egl')
        FileFormatConvert.sifToEdgelist(file=filein, sep='\t',
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
