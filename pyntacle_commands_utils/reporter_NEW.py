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
from collections import OrderedDict

""" Utility to produce the report for global topology, local topology and modules """

class pyntacleReporter():
    """
    This method creates a pyntacle_commands_utils according to the type of analysis run by pyntacle
    """
    logger = None

    def __init__(self, graph: Graph):

        self.logger = log

        # store first graph
        self.__graph = graph

        # initialize graph utility class
        self.__utils = gu(graph=self.__graph)
        self.__utils.graph_checker()  # check that input graph is properly set
        self.__report_type = None #this wiull be instanced in create_report
        self.__report = [] #this will be used in create_report

    def create_report(self, report_type: Reports, report: OrderedDict):
        """
        initialize the report object by writing generic information on the input graph
        """

        if not isinstance(report_type, Reports):
            raise TypeError("\"report_type\" must be on of the \"Reports\" enumerators, {} found".format(type(report_type).__name__))

        if not isinstance(report, OrderedDict):
            raise ValueError("\"report\" must be an ordered Dictionary")


        self.__report_type = report_type

        now = datetime.datetime.now()
        self.dat = now.strftime("%d/%m/%Y %I:%M")
        self.__report = []
        self.__report.append(" ".join["pyntacle Report", self.dat])
        self.__report.append("General Graph Information")
        self.__report.append(["graph name", ",".join(self.__graph["name"])])
        self.__report.append(["components", len(self.__graph.components())])
        self.__report.append(["nodes", self.__graph.vcount()])
        self.__report.append(["edges", self.__graph.ecount()])
        self.__report.append(["\n\n"])
        self.__report.append(": ".join(["Pyntacle Command", report_type.name]))

        if report_type == Reports.Local:
            self.__local_report()
        elif report_type == Reports.Global:
            self.__global_report(reportdict=report)
        elif report_type == Reports.KPinfo:
            self.__KPinfo_report(reportdict=report)
        elif report_type == Reports.KP_greedy:
            self.__greedy_report(reportdict=report)
        elif report_type == Reports.KP_bruteforce:
            self.__bruteforce_report(reportdict=report)
        elif report_type == Reports.Communities:
            self.__communities_report()

        else:
            if report_type == Reports.Set:
                self.logger.warning("Set operation needs another report builder, use the \"Report_Sets\" class contained in this module. Quitting")
                sys.exit(1)

            else:
                raise ValueError("Report specified does not exists")

    def write_report(self, report_path=None) -> str:
        """
        Create a text file containing the information created previously by the any of the *report* functions.
        By default, if the `report_path` function is not initialized, a generic name is created and a tab-separated file
        is generated (named *pyntacle_report_**GRAPHNAME**_**COMMAND**_**DATE**.tsv* where **GRAPHNAME** is the value
        stroed in the graph["name"] attribute, **COMMAND** is the name of the command requested by the user and
        **DATE** is the date when the pyntacle run was completed. This file will be stored in the current directory
        :param str report_path: a :type: str containing a valid path to a file. If not specified (default is  None. Read above)
        :return: the path where the report is stored
        """
        extensionlist = [".txt", ".tsv", ".xlsx", ".csv"]

        if not self.__report:
            raise EnvironmentError(
                "a pyntacle_commands_utils must be created first using the \"create_report()\" function")

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
            self.logger.info("pyntacle_commands_utils path is not specified, using generic name and saving file into "
                             "the current directory (as tab-separated file")

            report_path = os.path.join(os.path.abspath(os.getcwd()), "_".join(["pyntacle_report", self.__graph["name"], self.__report_type.name, self.now])+".tsv")
            extension = ".txt"

        if extension != ".xlsx":

            with open(report_path, "w") as out:

                if extension == ".tsv" or extension == ".txt":
                    self.logger.info("writing pyntacle report to a tab-separated file (tsv)")

                    for elem in self.__report:
                        elem.append("\n")

                    out.writelines(["\t".join(x) for x in self.__report])

                elif extension == ".csv":
                    self.logger.info("writing pyntacle report to a comma-separated value file (csv)")
                    writer = csv.writer(out)
                    writer.writerows(self.__report)

        else:
            self.logger.info("writing pyntacle report to a an excel-Ready file (xlsx)")
            workbook = xlsxwriter.Workbook(report_path, {'constant_memory': True})
            workbook.use_zip64()
            format = workbook.add_format()

            worksheet = workbook.add_worksheet("pyntacle Report")

            for row, elem in enumerate(self.__report):
                for col, p in enumerate(elem):
                    worksheet.write(row, col, p, format)

            workbook.close()

        return report_path

    def __local_report(self, reportdict:OrderedDict):
        pass
    def __global_report(self, reportdict:OrderedDict):
        if not all(isinstance(x, GlobalAttribute) for x in reportdict.keys()):
            raise TypeError("one of the keys in the report dictionary is not a GlobalAttribute")

        self.__report.append(["Results: Global Topology Metrics for selected graphs"])
        self.__report.append(["Metric", "Value"])

        for k in reportdict.keys():
            self.__report.append([k.name, str(reportdict[k])])

    def __KPinfo_report(self, reportdict:OrderedDict):
        """
        fill the *self.__report* object with all the values conatined in the KPINFO Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """

        if not all(isinstance(x, (KPPOSchoices, KPPOSchoices)) for x in reportdict.keys()):
            raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KPPOSchoices.mreach in reportdict.keys():
            m = reportdict[KPPOSchoices.mreach][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError("m must be a positive integer")
            else:
                self.__report.append(["maximum mreach distance", reportdict[KPPOSchoices.mreach][2]])

        if KPNEGchoices.F in reportdict.keys():
            init_F = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_F <= 1.0:
                self.__report.append(["initial F value (whole graph)", str(init_F)])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KPPOSchoices.dF in reportdict.keys():
            init_dF = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_dF <= 1.0:
                self.__report.append(["initial F value (whole graph)", init_dF])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        self.__report.append("Results: Key Player Metrics Info for selected node subset")
        self.__report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KPNEGchoices.F or k == KPNEGchoices.dF) and reportdict[k][-1] == 1.0:
                self.__report.append([k.name, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.__report.append([k.name, ",".join(reportdict[k][0]), str(reportdict[k][1])])

    def __greedy_report(self, reportdict: OrderedDict):
        """
        fill the *self.__report* object with all the values contained in the Greedy Optimization Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """

        if not all(isinstance(x, (KPPOSchoices, KPPOSchoices)) for x in reportdict.keys()):
            raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KPPOSchoices.mreach in reportdict.keys():
            m = reportdict[KPPOSchoices.mreach][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError("m must be a positive integer")
            else:
                self.__report.append(["maximum mreach distance", reportdict[KPPOSchoices.mreach][2]])

        if KPNEGchoices.F in reportdict.keys():
            init_F = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_F <= 1.0:
                self.__report.append(["initial F value (whole graph)", str(init_F)])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KPPOSchoices.dF in reportdict.keys():
            init_dF = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_dF <= 1.0:
                self.__report.append(["initial F value (whole graph)", init_dF])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        self.__report.append("Results: Greedily-Optimized Search")
        self.__report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KPNEGchoices.F or k == KPNEGchoices.dF) and reportdict[k][-1] == 1.0:
                self.__report.append([k.name, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.__report.append([k.name, ",".join(reportdict[k][0]), str(reportdict[k][1])])

    def __bruteforce_report(self, reportdict: OrderedDict):
        """
        fill the *self.__report* object with all the values contained in the Greedy Optimization Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """

        if not all(isinstance(x, (KPPOSchoices, KPPOSchoices)) for x in reportdict.keys()):
            raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KPPOSchoices.mreach in reportdict.keys():
            m = reportdict[KPPOSchoices.mreach][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError("m must be a positive integer")
            else:
                self.__report.append(["maximum mreach distance", reportdict[KPPOSchoices.mreach][2]])

        if KPNEGchoices.F in reportdict.keys():
            init_F = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_F <= 1.0:
                self.__report.append(["initial F value (whole graph)", str(init_F)])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KPPOSchoices.dF in reportdict.keys():
            init_dF = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_dF <= 1.0:
                self.__report.append(["initial F value (whole graph)", init_dF])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        self.__report.append("Results: Brute-force Search")
        self.__report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KPNEGchoices.F or k == KPNEGchoices.dF) and reportdict[k][-1] == 1.0:
                self.__report.append([k.name, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                #in this case, the report dictionary can contain more than one set of nodes
                if len(reportdict[k][0]) > 1:
                    self.__report.append([k.name, ",".join(reportdict[k][0][0]), str(reportdict[k][1])])
                    del reportdict[k][0][0]
                    for elem in reportdict[k][0]:
                        self.__report.append([[], ",".join(elem), str(reportdict[k][1])])
                else:
                    self.__report.append([k.name, ",".join(reportdict[k][0]), str(reportdict[k][1])])

    def __communities_report(self, reportdict: OrderedDict):
        pass


    # def report_global_topology(self):
    #     '''
    #     Create a pyntacle_commands_utils (as a list) containing all the global attributes list requested
    #
    #     :param attributes_list: a list of GlobalAttributes that must be reported
    #     :param graph_copy: a second graph to be reported
    #     '''
    #
    #     self.__utils.check_attributes_types(attributes_list=attributes_list,
    #                                         attribute_types=[_GlobalAttribute, _SparsenessAttribute])
    #
    #     attributes_names = self.__utils.get_attribute_names(attribute_list=attributes_list)
    #
    #     # print(attributes_names)
    #
    #     self.create_report()
    #
    #     self.__report.append(["Metric Name", "Metric Value"])
    #
    #     for elem in attributes_names:
    #         self.__report.append([elem, str(self.__graph[elem])])
    #
    #     # force each element of the list to be a string
    #     self.__report = [[str(x) for x in y] for y in self.__report]

    # def report_KP_Results(self, resultsdic: dict):
    #
    #     '''
    #     Creates a reporter for the KP metrics as a list of lists (stored in the self.pyntacle_commands_utils list
    #     :param resultsdic: a dictionary of results as outputted by kp_runner_OLD.py
    #     '''
    #
    #     # initialize empty pyntacle_commands_utils
    #     self.__init_report()
    #     self.__report.append(["--- Summary of Key Player search---"])
    #
    #     self.__report.append(["Requested metrics:", ",".join([x.name for x in resultsdic.keys()])])
    #
    #     self.__report.append(
    #         ["Algorithm:", resultsdic.get("algorithm", "KP-INFO")])  # added by me to handle the type of algorithm used
    #     resultsdic.pop("algorithm", None)  # remove the key if present
    #     #todo arrivato qua
    #
    #
    #     if _KeyplayerAttribute.F in resultsdic.keys():
    #
    #         if isinstance(resultsdic[_KeyplayerAttribute.F][0], float):
    #             self.__report.append(["Starting Value - F (whole graph): ", resultsdic[_KeyplayerAttribute.F][0]])
    #
    #         else:
    #             raise WrongArgumentError("Starting F must be specified for the pyntacle_commands_utils")
    #
    #     if _KeyplayerAttribute.DF in resultsdic.keys():
    #
    #         if isinstance(resultsdic[_KeyplayerAttribute.DF][0], float):
    #             self.__report.append(["Starting Value - DF (whole graph): ", resultsdic[_KeyplayerAttribute.DF][0]])
    #
    #         else:
    #             raise WrongArgumentError("Starting F must be specified for the pyntacle_commands_utils")
    #
    #     if _KeyplayerAttribute.MREACH in resultsdic.keys():
    #         if not isinstance(m, int):
    #             raise WrongArgumentError("\"m\" must be defined")
    #
    #         else:
    #             self.__report.append(["MREACH Value: ", m])
    #
    #     self.__report.append(["\n"])
    #     if _KeyplayerAttribute.MREACH in resultsdic.keys():
    #         self.__report.append(["KP Measure", "KP Set", "KP Value", "Fraction of Nodes Reached (MREACH)"])
    #     else:
    #         self.__report.append(["KP Measure", "KP Set", "KP Value"])
    #
    #     for key in resultsdic.keys():
    #         if key == _KeyplayerAttribute.MREACH:
    #             perc_node_reached = (resultsdic[key][2] + m) / self.__graph.vcount()
    #             self.__report.append(
    #                 [key.name, ",".join(resultsdic[key][1]), resultsdic[key][2], round(perc_node_reached, 2)])
    #
    #         else:
    #             self.__report.append([key.name, ",".join(resultsdic[key][1]), resultsdic[key][2]])
    #     self.__report = [[str(x) for x in y] for y in self.__report]
    #
    # def report_sets(self):
    #     pass
    #
    # def report_modules(self):
    #     pass
    #
    #
    # def report_local_topology(self, node_names: list, local_attributes_list: list):
    #
    #     '''
    #     Report all the requested topological indices for the requested nodes
    #
    #     :param node_names: a list of node names (must be string)
    #     :param local_attributes_list: a list of LocalAttribute parameter
    #     '''
    #
    #     self.__utils.check_name_list(names_list=node_names)  # check integrity of node names
    #
    #     index_list = self.__utils.get_node_indices(node_names=node_names)
    #
    #     self.__utils.check_attributes_types(attributes_list=local_attributes_list, attribute_types=_LocalAttribute)
    #
    #     attribute_names = self.__utils.get_attribute_names(attribute_list=local_attributes_list, type="node")
    #
    #     attribute_header = []
    #
    #     for at in attribute_names:
    #
    #         if at == "shortest_path":
    #             attribute_header.extend(
    #                 ("average shortest path", "median shortest path", "maximum shortest path"))
    #
    #         else:
    #             attribute_header.append(at)
    #
    #     # fix the shortest path and add the following fields instead
    #
    #     self.__init_report()  # initialize standard pyntacle_commands_utils
    #     if len(node_names) > 1:
    #         self.__report.append(["Info on selected nodes"])
    #     else:
    #         self.__report.append(["Info on selected node"])
    #
    #     header = ["Node Name"] + attribute_header
    #
    #     self.__report.append(header)
    #
    #     for index in index_list:
    #
    #         elem = []
    #
    #         node_name = self.__graph.vs(index)["name"][
    #             0]  # get the node name (is a list of 1 element so we take the first element only
    #         elem.append(node_name)
    #
    #         for attr in attribute_names:  # loop through the attributes
    #             value = self.__graph.vs(index)[attr]  # should be the list corresponding to the queried attribute
    #
    #             if attr == "shortest_path":
    #
    #                 if value[0] is None:
    #                     self.logger.warning("node {0} does not have attribute {1}, returning \"NA\"  instead".format(
    #                         self.__graph.vs(index)["name"][0], attr))
    #                     elem.extend(("NA", "NA", "NA", "NA"))
    #
    #                 else:
    #
    #                     sp = value[0]  # takes the list of shortest paths, should be a list of 1 element
    #                     sum = 0
    #
    #                     cleaned_sp = [x for x in sp if not x <= 0 and not isinf(x) and not isnan(
    #                         x)]  # remove everything that is a positive integer
    #
    #                     if cleaned_sp:
    #
    #                         for val in cleaned_sp:
    #                             sum = sum + val
    #
    #                         av_sp = sum / len(cleaned_sp)
    #
    #                         med_sp = median(cleaned_sp)
    #                         max_sp = max(cleaned_sp)
    #                         elem.extend((av_sp, med_sp, max_sp))
    #
    #                     else:
    #                         self.logger.warning(
    #                             "node {0} is an isolate, therefore it will have no sp pyntacle_commands_utils for it, returning \"NA\" instead")
    #                         elem.extend(("NA", "NA", "NA"))
    #
    #             else:
    #
    #                 if value[0] is None:
    #
    #                     self.logger.warning("node {0} does not have attribute {1}, returning \"NA\"  instead".format(
    #                         self.__graph.vs(index)["name"][0], attr))
    #                     elem.append("NA")
    #
    #                 elif isnan(value[0]):
    #                     self.logger.warning(
    #                         "node {0} has an infinite value for attribute {1}, returning \"nan\"".format(
    #                             self.__graph.vs(index)["name"][0], attr))
    #                     elem.append("nan")
    #
    #                 elif isinf(value[0]):
    #                     self.logger.warning(
    #                         "node {0} has an infinite value for attribute {1}, returning \"inf\"".format(
    #                             self.__graph.vs(index)["name"][0], attr))
    #                     elem.append("inf")
    #
    #                 else:
    #                     elem.append(value[0])
    #
    #         self.__report.append(elem)
    #
    #     # force each element of the list to be a string
    #     self.__report = [[str(x) for x in y] for y in self.__report]


