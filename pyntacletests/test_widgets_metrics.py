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

from config import *
import re
from cmds.metrics import Metrics as metrics_command
from internal.graph_load import GraphLoad
from algorithms.shortest_path import ShortestPath
from tools.enums import *


class DummyObj:
    pass


class WidgetTestMetrics(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.Args = DummyObj()
        self.Args.directory = os.path.join(current_dir, 'pyntacletests/test_sets/tmp')
        self.Args.format = None
        self.Args.input_file = os.path.join(current_dir, 'pyntacletests/test_sets/input/figure_8.txt')
        self.Args.largest_component = False
        self.Args.no_header = False
        self.Args.no_nodes = None
        self.Args.no_plot = True
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.report_format = 'txt'
        self.Args.input_separator = '\t'
        self.Args.save_binary = False
        self.Args.v = None
        self.Args.suppress_cursor = True
        self.Args.nodes = None
        self.Args.weights = None


    def test_global(self):
        sys.stdout.write("Testing global metrics\n")
        self.Args.which = 'global'
        mt = metrics_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            mt.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/Report_*_Global_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
            next(fin)
            data = fin.read()
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/metrics/figure8_global.txt')
        with open(expected, 'r') as exp:
            data_exp = exp.read()
        o = set(re.findall(r"[-+]?\d*\.\d+|\d+", data))
        e = set(re.findall(r"[-+]?\d*\.\d+|\d+", data_exp))

        self.assertEqual(o, e,
                         'Wrong checksum for Metrics, global case')

        # CPU, GPU, igraph coherence check
        graph = GraphLoad(self.Args.input_file, "adjm", header=True, separator=self.Args.input_separator).graph_load()

        implementation = CmodeEnum.igraph
        igraph_result = round(ShortestPath.average_global_shortest_path_length(graph, implementation), 5)

        #todo: Check the reason why this fails in the test suite if uncommented and the test for gr bruteforce is active
        implementation = CmodeEnum.cpu
        cpu_result = ShortestPath.average_global_shortest_path_length(graph, implementation)

        # self.assertEqual(igraph_result, cpu_result, 'Discrepancy between igraph and cpu result, global case')

        if cuda_avail:
            implementation = CmodeEnum.gpu
            gpu_result = ShortestPath.average_global_shortest_path_length(graph, implementation)
            self.assertEqual(igraph_result, gpu_result,
                             'Discrepancy between igraph and gpu result, global case')

    def test_local(self):
        sys.stdout.write("Testing local metrics\n")
        self.Args.damping_factor = 0.85
        self.Args.which = 'local'
        self.Args.nodes = 'HS,BR,WD,PS,WS'

        mt = metrics_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            mt.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = glob.glob(os.path.join(current_dir, "pyntacletests/test_sets/tmp/Report_*_Local_*"))[0]
        with open(fileout, 'r') as fin:
            next(fin)
            next(fin)
            data = fin.read()
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/metrics/figure8_local.txt')
        with open(expected, 'r') as exp:
            data_exp = exp.read()
        o = set(re.findall(r"[-+]?\d*\.\d+|\d+", data))
        e = set(re.findall(r"[-+]?\d*\.\d+|\d+", data_exp))
        self.assertEqual(o, e,
                         'Wrong checksum for Metrics, local case')
        
    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'pyntacletests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)
            
if __name__ == '__main__':
    unittest.main()