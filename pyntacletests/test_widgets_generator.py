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
from pyntacletests import getmd5, getmd5_bin
from cmds.generate import Generate as generate_command


class DummyObj:
    pass


class WidgetTestGenerator(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.Args = DummyObj()
        self.Args.directory = os.path.join(current_dir, 'pyntacletests/test_sets/tmp')
        self.Args.no_output_header = False
        self.Args.no_plot = True
        self.Args.output_format = 'adjmat'
        self.Args.input_separator = None
        self.Args.output_separator = None
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.seed = 1
        self.Args.repeat = 1
        self.Args.v = None
        self.Args.suppress_cursor = True

    def test_random(self):
        sys.stdout.write("Testing random generator\n")
        self.Args.which = 'random'
        self.Args.edges = None
        self.Args.nodes = None
        self.Args.probability = None
        self.Args.output_file = 'random'
        gen = generate_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            gen.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/random.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/generate/random/random.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for PyntacleGenerator, random case')

    def test_scalefree(self):
        sys.stdout.write("Testing scale-free generator\n")
        self.Args.which = 'scale-free'
        self.Args.output_file = 'scalefree'
        self.Args.nodes = None
        self.Args.avg_edges = None

        gen = generate_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            gen.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/scalefree.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/generate/scalefree/scalefree.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for PyntacleGenerator, scale-free case')

    def test_tree(self):
        sys.stdout.write("Testing tree generator\n")
        self.Args.which = 'tree'
        self.Args.output_file = 'tree'
        self.Args.nodes = None
        self.Args.children = None

        gen = generate_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            gen.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/tree.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/generate/tree/tree.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for PyntacleGenerator, tree case')

    def test_smallworld(self):
        sys.stdout.write("Testing smallworld generator\n")
        self.Args.which = 'small-world'
        self.Args.output_file = 'smallworld'
        self.Args.nodes = None
        self.Args.lattice = 4
        self.Args.lattice_size = 2
        self.Args.nei = 2
        self.Args.probability = 0.5

        gen = generate_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            gen.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = os.path.join(current_dir, 'pyntacletests/test_sets/tmp/smallworld.adjm')
        expected = os.path.join(current_dir, 'pyntacletests/test_sets/output/generate/smallworld/smallworld.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for PyntacleGenerator, smallworld case')
        
    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'pyntacletests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()