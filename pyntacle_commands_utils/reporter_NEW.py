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
        self.graph = graph

        # initialize graph utility class
        self.utils = gu(graph=self.graph)
        self.utils.graph_checker()  # check that input graph is properly set
        self.report_type = None #this wiull be instanced in create_report
        self.report = [] #this will be used in create_report
        now = datetime.datetime.now()
        self.dat = now.strftime("%d/%m/%Y %I:%M")
        

    def create_report(self, report_type: Reports, report: OrderedDict):
        """
        initialize the report object by writing generic information on the input graph
        """

        if not isinstance(report_type, Reports):
            raise TypeError("\"report_type\" must be on of the \"Reports\" enumerators, {} found".format(type(report_type).__name__))

        if not isinstance(report, OrderedDict):
            raise ValueError("\"report\" must be an ordered Dictionary")


        self.__report_type = report_type
        self.report = []
        self.report.append(" ".join["pyntacle Report", self.dat])
        self.report.append("General Graph Information")
        self.report.append(["graph name", ",".join(self.graph["name"])])
        self.report.append(["components", len(self.graph.components())])
        self.report.append(["nodes", self.graph.vcount()])
        self.report.append(["edges", self.graph.ecount()])
        self.report.append(["\n\n"])
        self.report.append(": ".join(["Pyntacle Command", report_type.name]))

        if report_type == Reports.Local:
            self.__local_report(reportdict=report)
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

        if not self.report:
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

            report_path = os.path.join(os.path.abspath(os.getcwd()), "_".join(["pyntacle_report", self.graph["name"], self.__report_type.name, self.dat])+".tsv")
            extension = ".txt"

        if extension != ".xlsx":

            with open(report_path, "w") as out:

                if extension == ".tsv" or extension == ".txt":
                    self.logger.info("writing pyntacle report to a tab-separated file (tsv)")

                    for elem in self.report:
                        elem.append("\n")

                    out.writelines(["\t".join(x) for x in self.report])

                elif extension == ".csv":
                    self.logger.info("writing pyntacle report to a comma-separated value file (csv)")
                    writer = csv.writer(out)
                    writer.writerows(self.report)

        else:
            self.logger.info("writing pyntacle report to a an excel-Ready file (xlsx)")
            workbook = xlsxwriter.Workbook(report_path, {'constant_memory': True})
            workbook.use_zip64()
            format = workbook.add_format()

            worksheet = workbook.add_worksheet("pyntacle Report")

            for row, elem in enumerate(self.report):
                for col, p in enumerate(elem):
                    worksheet.write(row, col, p, format)

            workbook.close()

        return report_path

    def __local_report(self, reportdict:OrderedDict):

        nodes = reportdict.get("nodes")
        if nodes is None:
            nodes = self.graph.vs["name"]
        else:
            del reportdict["nodes"]

        if not all(isinstance(x, LocalAttribute) for x in reportdict.keys()):
            raise TypeError(("one of the keys in the report dictionary is not of type LocalAttribute (except nodes)"))
        self.report.append(["Results: Local Topology Metrics in Pyntacle for each node queried"])
        self.report.append(["Node Name"] + [x.name for x in reportdict.keys()])

        #todo stuck here
        for i, elem in enumerate(nodes):
            pass

    def __global_report(self, reportdict:OrderedDict):
        if not all(isinstance(x, GlobalAttribute) for x in reportdict.keys()):
            raise TypeError("one of the keys in the report dictionary is not of type GlobalAttribute")

        self.report.append(["Results: Global Topology Metrics for selected graphs"])
        self.report.append(["Metric", "Value"])

        for k in reportdict.keys():
            self.report.append([k.name, str(reportdict[k])])

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
                self.report.append(["maximum mreach distance", reportdict[KPPOSchoices.mreach][2]])

        if KPNEGchoices.F in reportdict.keys():
            init_F = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["initial F value (whole graph)", str(init_F)])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KPPOSchoices.dF in reportdict.keys():
            init_dF = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["initial F value (whole graph)", init_dF])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        self.report.append("Results: Key Player Metrics Info for selected subset of nodes")
        self.report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KPNEGchoices.F or k == KPNEGchoices.dF) and reportdict[k][-1] == 1.0:
                self.report.append([k.name, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.report.append([k.name, ",".join(reportdict[k][0]), str(reportdict[k][1])])

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
                self.report.append(["maximum mreach distance", reportdict[KPPOSchoices.mreach][2]])

        if KPNEGchoices.F in reportdict.keys():
            init_F = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["initial F value (whole graph)", str(init_F)])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KPPOSchoices.dF in reportdict.keys():
            init_dF = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["initial F value (whole graph)", init_dF])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        self.report.append("Results: Greedily-Optimized Search")
        self.report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KPNEGchoices.F or k == KPNEGchoices.dF) and reportdict[k][-1] == 1.0:
                self.report.append([k.name, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.report.append([k.name, ",".join(reportdict[k][0]), str(reportdict[k][1])])

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
                self.report.append(["maximum mreach distance", reportdict[KPPOSchoices.mreach][2]])

        if KPNEGchoices.F in reportdict.keys():
            init_F = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["initial F value (whole graph)", str(init_F)])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KPPOSchoices.dF in reportdict.keys():
            init_dF = reportdict[KPNEGchoices.F][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["initial F value (whole graph)", init_dF])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        self.report.append("Results: Brute-force Search")
        self.report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KPNEGchoices.F or k == KPNEGchoices.dF) and reportdict[k][-1] == 1.0:
                self.report.append([k.name, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                #in this case, the report dictionary can contain more than one set of nodes
                if len(reportdict[k][0]) > 1:
                    self.report.append([k.name, ",".join(reportdict[k][0][0]), str(reportdict[k][1])])
                    del reportdict[k][0][0]
                    for elem in reportdict[k][0]:
                        self.report.append([[], ",".join(elem), str(reportdict[k][1])])
                else:
                    self.report.append([k.name, ",".join(reportdict[k][0]), str(reportdict[k][1])])

    def __communities_report(self, reportdict: OrderedDict):
        pass

