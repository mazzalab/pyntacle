import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from misc.graph_load import GraphLoad, separator_detect
from test_widgets_convert import WidgetTestConvert
from test_widgets_set import WidgetTestSet
from test_widgets_metrics import WidgetTestMetrics


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WidgetTestConvert('test_convert_sif'))
    suite.addTest(WidgetTestConvert('test_convert_egl'))
    suite.addTest(WidgetTestConvert('test_convert_bin'))
    suite.addTest(WidgetTestConvert('test_convert_dot'))
    suite.addTest(WidgetTestConvert('test_convert_adjm'))
    suite.addTest(WidgetTestSet('test_union'))
    suite.addTest(WidgetTestSet('test_intersect'))
    suite.addTest(WidgetTestSet('test_difference'))
    suite.addTest(WidgetTestMetrics('test_global'))
    suite.addTest(WidgetTestMetrics('test_local'))


    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
