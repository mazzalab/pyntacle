import unittest
import os, sys, glob
from argparse import ArgumentParser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from cmds.keyplayer import KeyPlayer as keyplayer_command
from tools.misc.graph_load import GraphLoad
from algorithms.global_topology import GlobalTopology
from tools.misc.enums import *

from test import getmd5


class DummyObj:
    pass


class WidgetTestKeyplayer(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.Args = DummyObj()
        self.Args.directory = 'test/test_sets/tmp'
        self.Args.format = None
        self.Args.input_file = 'test/test_sets/input/figure_8.txt'
        self.Args.largest_component = False
        self.Args.m_reach = 2
        self.Args.max_distances = None
        self.Args.no_header = False
        self.Args.no_plot = True
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.report_format = 'txt'
        self.Args.save_binary = False
        self.Args.threads = 1
        self.Args.type = 'all'
        self.Args.v = None
        
        
    def test_kpinfo(self):
        sys.stdout.write("Testing kp-info\n")
        self.Args.which = 'kp-info'
        self.Args.nodes = 'HS,HA,GM'
        kp = keyplayer_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            kp.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        
        fileout = glob.glob("test/test_sets/tmp/pyntacle_report_*_KPinfo_*")[0]
        with open(fileout, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(fileout, 'w') as fout:
            fout.writelines(data[1:])
        expected = 'test/test_sets/output/keyplayer/figure8_kpinfo.txt'
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for KeyPlayer, kp-info case')

    def test_kpfinder_greedy(self):
        sys.stdout.write("Testing kp-finder greedy\n")
        self.Args.which = 'kp-finder'
        self.Args.implementation = 'greedy'
        self.Args.k_size = 2
        self.Args.seed = 2
        kp = keyplayer_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            kp.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob("test/test_sets/tmp/pyntacle_report_*_KP_greedy_*")[0]
        with open(fileout, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(fileout, 'w') as fout:
            fout.writelines(data[1:])
        expected = 'test/test_sets/output/keyplayer/figure8_kpfinder_greedy.txt'
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for KeyPlayer, kp-finder greedy case')
        
    def test_kpfinder_bf(self):
        sys.stdout.write("Testing kp-finder bruteforce\n")
        self.Args.which = 'kp-finder'
        self.Args.implementation = 'brute-force'
        self.Args.k_size = 2
        self.Args.seed = 2
        kp = keyplayer_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            kp.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob("test/test_sets/tmp/pyntacle_report_*_KP_bruteforce_*")[0]
        with open(fileout, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(fileout, 'w') as fout:
            fout.writelines(data[1:])
        expected = 'test/test_sets/output/keyplayer/figure8_kpfinder_bruteforce.txt'
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for KeyPlayer, kp-finder bruteforce case')
    
    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob('test/test_sets/tmp/*')
        for f in files:
            os.remove(f)
        
if __name__ == '__main__':
    unittest.main()