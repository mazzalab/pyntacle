__author__ = u"Mauro Truglio, Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.2"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"07/06/2020"
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
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from pyntacletests.test_widgets_convert import WidgetTestConvert
from pyntacletests.test_widgets_setoperations import WidgetTestLogicOps
from pyntacletests.test_widgets_metrics import WidgetTestMetrics
from pyntacletests.test_widgets_communities import WidgetTestCommunities
from pyntacletests.test_widgets_generator import WidgetTestGenerator
from pyntacletests.test_widgets_keyplayer import WidgetTestKeyplayer
from pyntacletests.test_widgets_groupcentrality import WidgetTestGroupcentrality



def Suite():
    suite = unittest.TestSuite()
    suite.addTest(WidgetTestConvert('test_convert_sif'))
    suite.addTest(WidgetTestConvert('test_convert_egl'))
    suite.addTest(WidgetTestConvert('test_convert_bin'))
    suite.addTest(WidgetTestConvert('test_convert_dot'))
    suite.addTest(WidgetTestConvert('test_convert_adjm'))
    suite.addTest(WidgetTestConvert('test_egl_to_sif'))
    suite.addTest(WidgetTestConvert('test_sif_to_egl'))
    suite.addTest(WidgetTestConvert('test_dot_to_adjm'))

    suite.addTest(WidgetTestLogicOps('test_union'))
    suite.addTest(WidgetTestLogicOps('test_intersect'))
    suite.addTest(WidgetTestLogicOps('test_difference'))
    suite.addTest(WidgetTestMetrics('test_global'))
    suite.addTest(WidgetTestMetrics('test_local'))
    suite.addTest(WidgetTestCommunities('test_fastgreedy'))
    suite.addTest(WidgetTestCommunities('test_infomap'))
    suite.addTest(WidgetTestCommunities('test_leading_eigenvector'))
    suite.addTest(WidgetTestCommunities('test_community_walktrap'))
    suite.addTest(WidgetTestGenerator('test_random'))
    suite.addTest(WidgetTestGenerator('test_scalefree'))
    suite.addTest(WidgetTestGenerator('test_tree'))
    suite.addTest(WidgetTestGenerator('test_smallworld'))
    suite.addTest(WidgetTestKeyplayer('test_kpinfo'))
    suite.addTest(WidgetTestKeyplayer('test_kpfinder_greedy'))
    suite.addTest(WidgetTestKeyplayer('test_kpfinder_bf'))
    suite.addTest(WidgetTestGroupcentrality('test_grinfo'))
    suite.addTest(WidgetTestGroupcentrality('test_grfinder_greedy'))
    suite.addTest(WidgetTestGroupcentrality('test_grfinder_bf'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(Suite())
