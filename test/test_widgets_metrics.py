import unittest
import os, sys, glob
from collections import namedtuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from commands.metrics import Metrics as metrics_command


from test import getmd5


class DummyObj:
    pass


class WidgetTestMetrics(unittest.TestCase):
    def setUp(self):
        self.Args = DummyObj()
        self.Args.directory = 'test/test_sets/tmp'
        self.Args.format = None
        self.Args.input_file = 'test/test_sets/input/figure_8.txt'
        self.Args.largest_component = False
        self.Args.no_header = False
        self.Args.no_nodes = None
        self.Args.no_plot = True
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.report_format = 'txt'
        self.Args.save_binary = False
        self.Args.v = None

    def test_global(self):
        sys.stdout.write("Testing global metrics\n")
        self.Args.which = 'global'
        mt = metrics_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            mt.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob("test/test_sets/tmp/Dedalus*_global_metrics*")[0]
        expected = 'test/test_sets/output/metrics/figure8_global.txt'
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Metrics, global case')
        
    def test_local(self):
        sys.stdout.write("Testing local metrics\n")
        self.Args.damping_factor = 0.85
        self.Args.which = 'local'
        self.Args.nodes = 'HS,BR,WD,PS,WS'
        self.Args.weights = None
        
        mt = metrics_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            mt.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob("test/test_sets/tmp/Dedalus*_local_metrics*")[0]
        expected = 'test/test_sets/output/metrics/figure8_local.txt'
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Metrics, local case')
        
    def tearDown(self):
        files = glob.glob('test/test_sets/tmp/*')
        for f in files:
            os.remove(f)
