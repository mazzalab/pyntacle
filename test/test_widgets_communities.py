__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.0.1"
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
from test import getmd5, getmd5_bin
from commands.communities import Communities as communities_command

class DummyObj:
    pass


class WidgetTestCommunities(unittest.TestCase):
    def setUp(self):
        self.Args = DummyObj()
        self.Args.clusters = None
        self.Args.directory = 'test/test_sets/tmp'
        self.Args.format = None
        self.Args.input_file = 'test/test_sets/input/figure_8.txt'
        self.Args.largest_component = False
        self.Args.max_components = None
        self.Args.max_nodes = None
        self.Args.min_components = None
        self.Args.min_nodes = None
        self.Args.no_header = False
        self.Args.no_output_header = False
        self.Args.no_plot = True
        self.Args.output_format = 'adjm'
        self.Args.output_separator = '\t'
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.save_binary = False
        self.Args.weights = None
        self.Args.weights_format = 'standard'
        self.Args.weights_name = None
        self.Args.v = None

    def test_fastgreedy(self):
        sys.stdout.write("Testing fastgreedy community finder\n")
        self.Args.which = 'fastgreedy'
        self.Args.output_file = 'fastgreedy'
        comm = communities_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            comm.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        files_out = sorted(glob.glob("test/test_sets/tmp/fastgreedy*"))
        expected_files = sorted(glob.glob('test/test_sets/output/communities/fastgreedy/module*'))
        
        for f, e in zip(files_out, expected_files):
            self.assertEqual(getmd5(f), getmd5(e), 'Wrong checksum for communities, fastgreedy case')

    def test_infomap(self):
        sys.stdout.write("Testing infomap community finder\n")
        self.Args.which = 'infomap'
        self.Args.output_file = 'infomap'
        comm = communities_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            comm.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        files_out = sorted(glob.glob("test/test_sets/tmp/infomap*"))
        expected_files = sorted(glob.glob('test/test_sets/output/communities/infomap/module*'))

        for f, e in zip(files_out, expected_files):
            self.assertEqual(getmd5(f), getmd5(e), 'Wrong checksum for communities, infomap case')

    def test_leading_eigenvector(self):
        sys.stdout.write("Testing leading-eigenvector community finder\n")
        self.Args.which = 'leading-eigenvector'
        self.Args.output_file = 'leading-eigenvector'
        comm = communities_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            comm.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        files_out = sorted(glob.glob("test/test_sets/tmp/leading-eigenvector*"))
        expected_files = sorted(glob.glob('test/test_sets/output/communities/leading-eigenvector/module*'))

        for f, e in zip(files_out, expected_files):
            self.assertEqual(getmd5(f), getmd5(e), 'Wrong checksum for communities, leading-eigenvector case')

    def test_community_walktrap(self):
        sys.stdout.write("Testing community-walktrap community finder\n")
        self.Args.which = 'community-walktrap'
        self.Args.output_file = 'community-walktrap'
        self.Args.steps = 3
        comm = communities_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            comm.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        files_out = sorted(glob.glob("test/test_sets/tmp/community-walktrap*"))
        expected_files = sorted(
            glob.glob('test/test_sets/output/communities/community-walktrap/module*'))

        for f, e in zip(files_out, expected_files):
            self.assertEqual(getmd5(f), getmd5(e),
                             'Wrong checksum for communities, community-walktrap case')

    def tearDown(self):
        files = glob.glob('test/test_sets/tmp/*')
        for f in files:
            os.remove(f)
        
        
if __name__ == '__main__':
    widget_suite = unittest.TestSuite()
    widget_suite.addTest(WidgetTestCommunities('test_fastgreedy'))
    widget_suite.addTest(WidgetTestCommunities('test_infomap'))
    widget_suite.addTest(WidgetTestCommunities('test_leading_eigenvector'))
    widget_suite.addTest(WidgetTestCommunities('test_community_walktrap'))

    runner = unittest.TextTestRunner()
    runner.run(widget_suite)