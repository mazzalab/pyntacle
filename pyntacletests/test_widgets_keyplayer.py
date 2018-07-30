__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.2"
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
current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

from cmds.keyplayer import KeyPlayer as keyplayer_command
from tools.enums import *
import re
from pyntacletests import getmd5


class DummyObj:
    pass


class WidgetTestKeyplayer(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.Args = DummyObj()
        self.Args.directory = os.path.join(current_dir, 'pyntacletests/test_sets/tmp')
        self.Args.format = None
        self.Args.input_separator = '\t'
        self.Args.input_file = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.txt')
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
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/pyntacle_report_*_KPinfo_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
            data = fin.read()
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/keyplayer/figure8_kpinfo.txt')
        with open(expected, 'r') as exp:
            data_exp = exp.read()
        o = set(re.findall(r"[-+]?\d*\.\d+|\d+", data))
        e = set(re.findall(r"[-+]?\d*\.\d+|\d+", data_exp))
        self.assertEqual(o,e,
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
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/pyntacle_report_*_KP_greedy_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
            data = fin.read()
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/keyplayer/figure8_kpfinder_greedy.txt')
        with open(expected, 'r') as exp:
            data_exp = exp.read()
        o = set(re.findall(r"[^A-z:\t][0-9]*\.\d+|[^A-z:\t][ 0-9]+", data))
        e = set(re.findall(r"[^A-z:\t][0-9]*\.\d+|[^A-z:\t][ 0-9]+", data_exp))
        print(o)
        print(e)
        self.assertEqual(o,e,
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
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/pyntacle_report_*_KP_bruteforce_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
            data = fin.read()
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/keyplayer/figure8_kpfinder_bruteforce.txt')
        with open(expected, 'r') as exp:
            data_exp = exp.read()
        o = set(re.findall(r"[-+]?\d*\.\d+|\d+", data))
        e = set(re.findall(r"[-+]?\d*\.\d+|\d+", data_exp))
        self.assertEqual(o,e,
                         'Wrong checksum for KeyPlayer, kp-finder bruteforce case')

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'pyntacletests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)
        
if __name__ == '__main__':
    unittest.main()