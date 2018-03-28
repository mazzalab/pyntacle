from config import *
import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from test_widgets_convert import WidgetTestConvert
from test_widgets_logicops import WidgetTestLogicOps
# from test_widgets_metrics import WidgetTestMetrics
from test_widgets_communities import WidgetTestCommunities
from test_widgets_generator import WidgetTestGenerator

def suite():
    suite = unittest.TestSuite()
    suite.addTest(WidgetTestConvert('test_convert_sif'))
    suite.addTest(WidgetTestConvert('test_convert_egl'))
    suite.addTest(WidgetTestConvert('test_convert_bin'))
    suite.addTest(WidgetTestConvert('test_convert_dot'))
    suite.addTest(WidgetTestConvert('test_convert_adjm'))
    suite.addTest(WidgetTestLogicOps('test_union'))
    suite.addTest(WidgetTestLogicOps('test_intersect'))
    suite.addTest(WidgetTestLogicOps('test_difference'))
    # suite.addTest(WidgetTestMetrics('test_global'))
    # suite.addTest(WidgetTestMetrics('test_local'))
    suite.addTest(WidgetTestCommunities('test_fastgreedy'))
    suite.addTest(WidgetTestCommunities('test_infomap'))
    suite.addTest(WidgetTestCommunities('test_leading_eigenvector'))
    suite.addTest(WidgetTestCommunities('test_community_walktrap'))
    suite.addTest(WidgetTestGenerator('test_random'))
    suite.addTest(WidgetTestGenerator('test_scalefree'))
    suite.addTest(WidgetTestGenerator('test_tree'))
    suite.addTest(WidgetTestGenerator('test_smallworld'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
