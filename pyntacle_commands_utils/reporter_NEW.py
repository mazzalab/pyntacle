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

from config import *
import csv, os, xlsxwriter
from math import isnan, isinf
from igraph import Graph
from numpy import median
from misc.enums import KPNEGchoices, KPPOSchoices, Reports, LocalAttribute, GlobalAttribute
from exceptions.wrong_argument_error import WrongArgumentError
from tools.graph_utils import GraphUtils as gu # swiss knife for graph utilities

""" Utility to produce the report for global topology, local topology and modules """

class pyntacleReporter():
    """
    This method creates a pyntacle_commands_utils according to the type of analysis run by pyntacle
    """
    logger = None

    def __init__(self, graph: Graph, report_type:Reports):

        self.logger = log

        # store first graph
        self.__graph = graph

        # initialize graph utility class
        self.__utils = gu(graph=self.__graph)
        self.__utils.graph_checker()  # check that input graph is properly set
        if not isinstance(report_type, Reports):
            raise TypeError("report type must be on of the \"Reports\" enumerators, {} found".format(type(report_type).__name__))
        else:
            self.__report_type = report_type

    def __init_report(self):
        #todo riscrivere tutto con karma
        now = datetime.datetime.now()
        dat = now.strftime("%d/%m/%Y %I:%M")
        self.__report = []
        self.__report.append(" ".join["pyntacle Report", dat])
        self.__report.append("General Graph Information")
        self.__report.append(["graph name", ",".join(self.__graph["name"])])
        self.__report.append(["components", len(self.__graph.components())])
        self.__report.append(["nodes", self.__graph.vcount()])
        self.__report.append(["edges", self.__graph.ecount()])
        self.__report.append(["\n\n"])
        self.__report.append(": ".join(["Pyntacle Command", self.__report_type.name]))

    def report_KP_Results(self, resultsdic: dict, m=None):

        '''
        Creates a reporter for the KP metrics as a list of lists (stored in the self.pyntacle_commands_utils list
        :param resultsdic: a dictionary of results as outputted by kp_runner_OLD.py
        '''

        # initialize empty pyntacle_commands_utils
        self.__init_report()
        self.__report.append(["-Run Info-"])
        self.__report.append(["Requested metrics:", ",".join([x.name for x in resultsdic.keys() if not isinstance(x, str)])])

        self.__report.append(
            ["Algorithm:", resultsdic.get("algorithm", "KP-INFO")])  # added by me to handle the type of algorithm used
        resultsdic.pop("algorithm", None)  # remove the key if present
        #todo arrivato qua





        if _KeyplayerAttribute.F in resultsdic.keys():

            if isinstance(resultsdic[_KeyplayerAttribute.F][0], float):
                self.__report.append(["Starting Value - F (whole graph): ", resultsdic[_KeyplayerAttribute.F][0]])

            else:
                raise WrongArgumentError("Starting F must be specified for the pyntacle_commands_utils")

        if _KeyplayerAttribute.DF in resultsdic.keys():

            if isinstance(resultsdic[_KeyplayerAttribute.DF][0], float):
                self.__report.append(["Starting Value - DF (whole graph): ", resultsdic[_KeyplayerAttribute.DF][0]])

            else:
                raise WrongArgumentError("Starting F must be specified for the pyntacle_commands_utils")

        if _KeyplayerAttribute.MREACH in resultsdic.keys():
            if not isinstance(m, int):
                raise WrongArgumentError("\"m\" must be defined")

            else:
                self.__report.append(["MREACH Value: ", m])

        self.__report.append(["\n"])
        if _KeyplayerAttribute.MREACH in resultsdic.keys():
            self.__report.append(["KP Measure", "KP Set", "KP Value", "Fraction of Nodes Reached (MREACH)"])
        else:
            self.__report.append(["KP Measure", "KP Set", "KP Value"])

        for key in resultsdic.keys():
            if key == _KeyplayerAttribute.MREACH:
                perc_node_reached = (resultsdic[key][2] + m) / self.__graph.vcount()
                self.__report.append(
                    [key.name, ",".join(resultsdic[key][1]), resultsdic[key][2], round(perc_node_reached, 2)])

            else:
                self.__report.append([key.name, ",".join(resultsdic[key][1]), resultsdic[key][2]])
        self.__report = [[str(x) for x in y] for y in self.__report]

    def report_global_topology(self, attributes_list: list):
        '''
        Create a pyntacle_commands_utils (as a list) containing all the global attributes list requested

        :param attributes_list: a list of GlobalAttributes that must be reported
        :param graph_copy: a second graph to be reported
        '''

        self.__utils.check_attributes_types(attributes_list=attributes_list,
                                            attribute_types=[_GlobalAttribute, _SparsenessAttribute])

        attributes_names = self.__utils.get_attribute_names(attribute_list=attributes_list)

        # print(attributes_names)

        self.__init_report(report_type="Metrics - Global Topology")

        self.__report.append(["Metric Name", "Metric Value"])

        for elem in attributes_names:
            self.__report.append([elem, str(self.__graph[elem])])

        # force each element of the list to be a string
        self.__report = [[str(x) for x in y] for y in self.__report]

    def report_global_comparisons(self, attributes_list: list):
        '''
        **[EXPAND]**

        :param attributes_list: a òist of attributes that must be present in both graphs
        :param graph2: another graph object
        :return:
        '''

        self.__utils.check_attributes_types(attributes_list=attributes_list,
                                            attribute_types=[_GlobalAttribute, _SparsenessAttribute])

        self.__utils2.check_attributes_types(attributes_list=attributes_list,
                                             attribute_types=[_GlobalAttribute, _SparsenessAttribute])

        self.__init_report(report_type="Metrics - Global Topology Comparison")
        self.__report.append(["Metric Name", "Metrics - Original Graph", "Metrics - Comparison Graph"])

        attributes_names = self.__utils.get_attribute_names(attribute_list=attributes_list)

        for attr in attributes_names:  # check if attribute exist
            self.__utils2.attribute_in_graph(attr)

        for elem in attributes_names:
            self.__report.append([elem, str(self.__graph[elem]), str(self.__graph2[elem])])

        # force each element of the list to be a string
        self.__report = [[str(x) for x in y] for y in self.__report]

    def report_local_topology(self, node_names: list, local_attributes_list: list):

        '''
        Report all the requested topological indices for the requested nodes

        :param node_names: a list of node names (must be string)
        :param local_attributes_list: a list of LocalAttribute parameter
        '''

        self.__utils.check_name_list(names_list=node_names)  # check integrity of node names

        index_list = self.__utils.get_node_indices(node_names=node_names)

        self.__utils.check_attributes_types(attributes_list=local_attributes_list, attribute_types=_LocalAttribute)

        attribute_names = self.__utils.get_attribute_names(attribute_list=local_attributes_list, type="node")

        attribute_header = []

        for at in attribute_names:

            if at == "shortest_path":
                attribute_header.extend(
                    ("average shortest path", "median shortest path", "maximum shortest path"))

            else:
                attribute_header.append(at)

        # fix the shortest path and add the following fields instead

        self.__init_report(report_type="Metrics - Local Topology")  # initialize standard pyntacle_commands_utils
        if len(node_names) > 1:
            self.__report.append(["Info on selected nodes"])
        else:
            self.__report.append(["Info on selected node"])

        header = ["Node Name"] + attribute_header

        self.__report.append(header)

        for index in index_list:

            elem = []

            node_name = self.__graph.vs(index)["name"][
                0]  # get the node name (is a list of 1 element so we take the first element only
            elem.append(node_name)

            for attr in attribute_names:  # loop through the attributes
                value = self.__graph.vs(index)[attr]  # should be the list corresponding to the queried attribute

                if attr == "shortest_path":

                    if value[0] is None:
                        self.logger.warning("node {0} does not have attribute {1}, returning \"NA\"  instead".format(
                            self.__graph.vs(index)["name"][0], attr))
                        elem.extend(("NA", "NA", "NA", "NA"))

                    else:

                        sp = value[0]  # takes the list of shortest paths, should be a list of 1 element
                        sum = 0

                        cleaned_sp = [x for x in sp if not x <= 0 and not isinf(x) and not isnan(
                            x)]  # remove everything that is a positive integer

                        if cleaned_sp:

                            for val in cleaned_sp:
                                sum = sum + val

                            av_sp = sum / len(cleaned_sp)

                            med_sp = median(cleaned_sp)
                            max_sp = max(cleaned_sp)
                            elem.extend((av_sp, med_sp, max_sp))

                        else:
                            self.logger.warning(
                                "node {0} is an isolate, therefore it will have no sp pyntacle_commands_utils for it, returning \"NA\" instead")
                            elem.extend(("NA", "NA", "NA"))

                else:

                    if value[0] is None:

                        self.logger.warning("node {0} does not have attribute {1}, returning \"NA\"  instead".format(
                            self.__graph.vs(index)["name"][0], attr))
                        elem.append("NA")

                    elif isnan(value[0]):
                        self.logger.warning(
                            "node {0} has an infinite value for attribute {1}, returning \"nan\"".format(
                                self.__graph.vs(index)["name"][0], attr))
                        elem.append("nan")

                    elif isinf(value[0]):
                        self.logger.warning(
                            "node {0} has an infinite value for attribute {1}, returning \"inf\"".format(
                                self.__graph.vs(index)["name"][0], attr))
                        elem.append("inf")

                    else:
                        elem.append(value[0])

            self.__report.append(elem)

        # force each element of the list to be a string
        self.__report = [[str(x) for x in y] for y in self.__report]

    def get_report(self):
        '''
        Return the self.pyntacle_commands_utils list in order to pass it to an external builder

        :return: the self.__report object
        '''

        return self.__report

    def create_report(self, report_path=None):
        extensionlist = [".txt", ".tsv", ".xlsx", ".csv"]

        if not self.__report:
            raise EnvironmentError(
                "a pyntacle_commands_utils must be created first using one of the several pyntacle_commands_utils functions")

        if report_path is not None:
            report_path = os.path.abspath(report_path)
            extension = os.path.splitext(report_path.rstrip())[-1]  # take file name extension

            if extension not in extensionlist:
                raise WrongArgumentError("extension of file {} is not supported".format(extension))

            reportdir = os.path.dirname(os.path.abspath(report_path))
            if not os.path.isdir(reportdir):
                self.logger.warning("directory of pyntacle_commands_utils does not exists, creating it")
                os.makedirs(reportdir, exist_ok=True)

        else:
            self.logger.info("pyntacle_commands_utils path is not specified, using generic name \"pyntacle_report\" "
                             "on the current directory (tab-separated file")

            report_path = os.path.join(os.path.abspath(os.getcwd()), "pyntacle_report.tsv")
            extension = ".txt"

        if extension != ".xlsx":

            with open(report_path, "w") as out:

                if extension == ".tsv" or extension == ".txt":
                    self.logger.info("creating a tab-delimited pyntacle_commands_utils")

                    for elem in self.__report:
                        elem.append("\n")

                    out.writelines(["\t".join(x) for x in self.__report])

                elif extension == ".csv":
                    self.logger.info("creating csv pyntacle_commands_utils")
                    writer = csv.writer(out)
                    writer.writerows(self.__report)

        else:
            self.logger.info("creating an excel pyntacle_commands_utils")
            workbook = xlsxwriter.Workbook(report_path, {'constant_memory': True})
            workbook.use_zip64()
            format = workbook.add_format()

            worksheet = workbook.add_worksheet("pyntacle Report")

            for row, elem in enumerate(self.__report):
                for col, p in enumerate(elem):
                    worksheet.write(row, col, p, format)

            workbook.close()

        return report_path
