__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.1"
__maintainer__ = u"Tommaso Mazza"
__email__ = "o@css-mendel.it"
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

from cmds.keyplayer import KeyPlayer as keyplayer_command
from tools.enums import *
import re
from pyntacletests import getmd5
from multiprocessing import cpu_count
n_cpus = cpu_count()-1

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
        self.Args.max_distance = None
        self.Args.no_header = False
        self.Args.no_plot = True
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.report_format = 'txt'
        self.Args.save_binary = False
        self.Args.threads = n_cpus
        self.Args.type = 'all'
        self.Args.v = None
        self.Args.suppress_cursor = True
        
    def test_kpinfo(self):
        sys.stdout.write("Testing kp-info\n")
        self.Args.which = 'kp-info'
        self.Args.nodes = 'HS,HA,GM'
        kp = keyplayer_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            kp.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/Report_*_KP_info_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
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
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/Report_*_KP_greedy_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
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
        sys.stdout.write("Testing kp-finder bruteforce with {} cpus\n".format(n_cpus))
        self.Args.which = 'kp-finder'
        self.Args.implementation = 'brute-force'
        self.Args.k_size = 2
        self.Args.seed = 2
        kp = keyplayer_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            kp.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/Report_*_KP_bruteforce_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
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