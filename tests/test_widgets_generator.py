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
current_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
from tests import getmd5, getmd5_bin
from cmds.generate import Generate as generate_command


class DummyObj:
    pass


class WidgetTestGenerator(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.Args = DummyObj()
        self.Args.directory = os.path.join(current_dir, 'tests/test_sets/tmp')
        self.Args.no_output_header = False
        self.Args.no_plot = True
        self.Args.output_format = 'adjmat'
        self.Args.output_separator = None
        self.Args.plot_dim = None
        self.Args.plot_format = 'pdf'
        self.Args.seed = 1
        self.Args.v = None

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
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/random.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/generate/random/generated.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Generator, random case')

    def test_scalefree(self):
        sys.stdout.write("Testing scale-free generator\n")
        self.Args.which = 'scale-free'
        self.Args.output_file = 'scalefree'
        self.Args.nodes = None
        self.Args.outgoing_edges = None

        gen = generate_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            gen.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/scalefree.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/generate/scalefree/generated.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected), 'Wrong checksum for Generator, scale-free case')

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
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/tree.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/generate/tree/generated.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Generator, tree case')

    def test_smallworld(self):
        sys.stdout.write("Testing smallworld generator\n")
        self.Args.which = 'small-world'
        self.Args.output_file = 'smallworld'
        self.Args.nodes = None
        self.Args.lattice = 2
        self.Args.lattice_size = None
        self.Args.nei = None
        self.Args.probability = 0.5

        gen = generate_command(self.Args)
        with self.assertRaises(SystemExit) as cm:
            gen.run()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)
        fileout = os.path.join(current_dir, 'tests/test_sets/tmp/smallworld.adjm')
        expected = os.path.join(current_dir, 'tests/test_sets/output/generate/smallworld/generated.adjm')
        self.assertEqual(getmd5(fileout), getmd5(expected),
                         'Wrong checksum for Generator, smallworld case')
        
    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        files = glob.glob(os.path.join(current_dir, 'tests/test_sets/tmp/*'))
        for f in files:
            os.remove(f)


if __name__ == '__main__':
    unittest.main()