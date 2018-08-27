__author__ = "Daniele Capocefalo, Mauro Truglio, Tommaso Mazza"
__copyright__ = "Copyright 2018, The Pyntacle Project"
__credits__ = ["Ferenc Jordan"]
__version__ = "0.2.3.1"
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
from igraph import Graph
from tools.enums import KpnegEnum, KpposEnum, ReportEnum
from exceptions.wrong_argument_error import WrongArgumentError
from tools.graph_utils import GraphUtils as gu # swiss knife for graph utilities
from collections import OrderedDict

""" Utility to produce the report for global topology, local topology and modules """


class pyntacleReporter():
    """
    This method creates a report according to the type of analysis run by pyntacle
    """
    logger = None

    def __init__(self, graph: Graph):

        self.logger = log

        # store first graph
        self.graph = graph

        # initialize graph utility class
        self.utils = gu(graph=self.graph)
        self.utils.check_graph()  # check that input graph is properly set
        self.report_type = None #this will be instanced in create_report
        self.report = [] #this will be used in create_report
        self.dat = runtime_date
        
    def create_report(self, report_type: ReportEnum, report: OrderedDict):
        """
        initialize the report object by writing generic information on the input graph and calling the internal report
        creators, according to the value passed by the "Report" enumerator
        :param Report  report_type: one of the type onside the "Report" enumerator
        :param OrderedDict report: a dictionary containing all the information to be reported
        """

        if not isinstance(report_type, ReportEnum):
            raise TypeError("\"report_type\" must be on of the \"ReportEnum\" enumerators, {} found".format(type(report_type).__name__))

        if not isinstance(report, OrderedDict):
            raise ValueError("\"report\" must be an ordered Dictionary")

        self.report_type = report_type
        self.report = []
        self.report.append([" ".join(["pyntacle Report", self.dat])])
        self.report.append(["Quick Graph Overview"])
        self.report.append(["graph name", ",".join(self.graph["name"])])
        self.report.append(["components", len(self.graph.components())])
        self.report.append(["nodes", self.graph.vcount()])
        self.report.append(["edges", self.graph.ecount()])
        self.report.append(["\n"])
        self.report.append(["Pyntacle Command:", report_type.name])

        if report_type == ReportEnum.Local:
            self.__local_report(reportdict=report)
        elif report_type == ReportEnum.Global:
            self.__global_report(reportdict=report)
        elif report_type == ReportEnum.KPinfo:
            self.__KPinfo_report(reportdict=report)
        elif report_type == ReportEnum.KP_greedy:
            self.__greedy_report(reportdict=report)
        elif report_type == ReportEnum.KP_bruteforce:
            self.__bruteforce_report(reportdict=report)
        elif report_type == ReportEnum.Communities:
            self.__communities_report(reportdict=report)
        elif report_type == ReportEnum.Set:
            self.__set_report(reportdict=report)
        else:
            raise ValueError("Report specified does not exists")

    def write_report(self, report_dir=None, format="tsv", choices=report_format) -> str:
        """
        Create a text file containing the information created previously by the any of the *report* functions.
        By default, if the `report_path` function is not initialized, a generic name is created and a tab-separated file
        is generated (named *pyntacle_report_**GRAPHNAME**_**COMMAND**_**DATE**.tsv* where **GRAPHNAME** is the value
        stroed in the graph["name"] attribute, **COMMAND** is the name of the command requested by the user and
        **DATE** is the date when the pyntacle run was completed. This file will be stored in the current directory
        :param str report_path: a :type: str containing a valid path to a file. If not specified (default is  None. Read above)
        :return: the path where the report is stored
        """

        if not self.report:
            raise EnvironmentError(
                "a report must be created first using the \"create_report()\" function")

        else:
            #cast every element of the list of lists to string, just in case:
            for x in self.report:
                list(map(str, x))

            self.report = [ list(map(str,x)) for x in self.report ]

        if format not in choices.keys():
            raise WrongArgumentError("file format {} is not supported".format(format))

        if report_dir is None:
            self.logger.info("Directory not specified. Using current directory")
            report_dir = os.path.abspath(os.getcwd())

        else:
            if not os.path.isdir(report_dir):
                self.logger.warning("Specified directory does not exists, creating it")
                os.makedirs(report_dir, exist_ok=True)

            else:
                report_dir = os.path.abspath(report_dir)

        if len(self.graph["name"]) > 1:
            self.logger.warning("using first \"name\" attribute of graph name since more than one is specified")
        
        graphname = self.graph["name"][0]
        
        if self.report_type.name == 'Set':
            report_path = os.path.join(report_dir, "_".join(["pyntacle_report", self.report_type.name, self.dat])+".tsv")
        else:
            report_path = os.path.join(report_dir, "_".join(["pyntacle_report", graphname, self.report_type.name, self.dat])+".tsv")

        extension = choices[format]

        if extension != "xlsx":

            with open(report_path, "w") as out:

                if extension == "tsv":
                    self.logger.info("writing pyntacle report to a tab-separated file (tsv)")
                    for elem in self.report:
                        elem.append("\n")
                    out.writelines(["\t".join(x) for x in self.report])
                    
                elif extension == "csv":
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
        """
        Fill the `report` object  with information regarding the metrics for each node (nodes must be specified in
        the reportdic `nodes' key. if that kjey is not specified, it will assume that the local metrics are
        reported for all nodes)
        :param reportdict: a report dictionary object with each local attribute as key and a list of values as value,
        representing the corresponding the value of the metrics for the corresponding node
        """

        nodes = reportdict.get("nodes")

        if nodes is None:
            nodes = self.graph.vs["name"]
        else:
            nodes = nodes.split(',')
            del reportdict["nodes"]

        self.report.append(["Results - Local Metrics for each Node in input"])
        self.report.append(["Node Name"] + [x for x in reportdict.keys()])
        addendum = [] #list that will be added to the self.report object
        for i, elem in enumerate(nodes):
            temp = []
            temp.append(elem) #append the node names to the appendum
            for k in reportdict.keys():
                temp.append(round(reportdict[k][i],5)) #append the corresponding value to the node name
            addendum.append(temp)
        self.report = self.report + addendum

    def __global_report(self, reportdict:OrderedDict):
        """
        Fill the `report` o0bject with information regarding all the global metrics stored in the reportdict object
        :param reportdict: a dictionary like {name of the global metric: metric}
        """

        self.report.append(["Results - Global Metrics of the input graph"])
        self.report.append(["Metric", "Value"])
        for k in reportdict.keys():
            self.report.append([k, reportdict[k]])
        

    def __KPinfo_report(self, reportdict:OrderedDict):
        """
        fill the *self.__report* object with all the values conatined in the KPINFO Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """
        # this doesn't work for now: keys are strings and not KP choices.
        # if not all(isinstance(x, str) for x in reportdict.keys()):
        #     raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KpposEnum.mreach.name in reportdict.keys():
            m = reportdict[KpposEnum.mreach.name][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError("m must be a positive integer")
            else:
                self.report.append(["maximum mreach distance", reportdict[KpposEnum.mreach.name][2]])

        if KpnegEnum.F.name in reportdict.keys():
            init_F = reportdict[KpnegEnum.F.name][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["initial F value (whole graph)", init_F])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KpnegEnum.dF.name in reportdict.keys():
            init_dF = reportdict[KpnegEnum.dF.name][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["initial dF value (whole graph)", init_dF])
            else:
                raise ValueError("Initial dF must range between 0 and 1")

        self.report.append(["\n"])
        self.report.append(["Results: Key-Player Metrics for the input set of nodes"])
        self.report.append(["Metric", "Nodes", "Value"])
 
        for k in reportdict.keys():
            if (k == KpnegEnum.F.name or k == KpnegEnum.dF.name) and reportdict[k][-1] == 1.0:
                self.report.append([k, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.report.append([k, ",".join(reportdict[k][0]), round(reportdict[k][1],5)])

    def __greedy_report(self, reportdict: OrderedDict):
        """
        fill the *self.__report* object with all the values contained in the Greedy Optimization Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """

        # if not all(isinstance(x, (KPPOSchoices, KPPOSchoices)) for x in reportdict.keys()):
        #     raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KpposEnum.mreach.name in reportdict.keys():
            m = reportdict[KpposEnum.mreach.name][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError("m must be a positive integer")
            else:
                self.report.append(["maximum mreach distance", reportdict[KpposEnum.mreach.name][2]])

        if KpnegEnum.F.name in reportdict.keys():
            init_F = reportdict[KpnegEnum.F.name][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["initial F value (whole graph)", init_F])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KpnegEnum.dF.name in reportdict.keys():
            init_dF = reportdict[KpnegEnum.dF.name][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["initial dF value (whole graph)", init_dF])
            else:
                raise ValueError("Initial dF must range between 0 and 1")

        self.report.append(["Results: Greedily-Optimized Search for selected KP Metrics"])
        self.report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KpnegEnum.F.name or k == KpnegEnum.dF.name) and reportdict[k][-1] == 1.0:
                self.report.append([k, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.report.append([k, ",".join(reportdict[k][0]), reportdict[k][1]])

    def __bruteforce_report(self, reportdict: OrderedDict):
        """
        fill the *self.__report* object with all the values contained in the Greedy Optimization Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """

        # if not all(isinstance(x, (KPPOSchoices, KPPOSchoices)) for x in reportdict.keys()):
        #     raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KpposEnum.mreach.name in reportdict.keys():
            m = reportdict[KpposEnum.mreach.name][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError("m must be a positive integer")
            else:
                self.report.append(["maximum mreach distance", reportdict[KpposEnum.mreach.name][2]])

        if KpnegEnum.F.name in reportdict.keys():
            init_F = reportdict[KpnegEnum.F.name][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["initial F value (whole graph)", init_F])
            else:
                raise ValueError("Initial F must range between 0 and 1")

        if KpnegEnum.dF.name in reportdict.keys():
            init_dF = reportdict[KpnegEnum.dF.name][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["initial dF value (whole graph)", init_dF])
            else:
                raise ValueError("Initial dF must range between 0 and 1")

        self.report.append(["Results: Brute-force Search"])
        self.report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():
            if (k == KpnegEnum.F.name or k == KpnegEnum.dF.name) and reportdict[k][-1] == 1.0:
                self.report.append([k, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                #in this case, the report dictionary can contain more than one set of nodes
                if len(reportdict[k][0]) > 1:
                    count = 0
                    for elem in reportdict[k][0]:
                        if count == 0:
                            self.report.append([k, ",".join(reportdict[k][0][0]), reportdict[k][1]])
                        else:
                            self.report.append(["", ",".join(elem), reportdict[k][1]])
                        count += 1
                else:
                    self.report.append([k, ",".join(reportdict[k][0][0]), reportdict[k][1]])

    def __communities_report(self, reportdict: OrderedDict):
        """
        Report General information regarding the communities (nodes, edges, component, algorithm)
        stored in the reportdic. The reportdic **MUST** also contain a `algorithms` key that will be used to report the
        type of algorithm used
        :param reportdict: a dictionary from pyntacle communities
        """
        self.report.append(["Results: Community finding in input graph"])
        self.report.append(["Algorithm:", reportdict["algorithm"]])
        self.report.append(["\n"])
        self.report.append(["Module", "Nodes", "Edges", "Components"])
        del reportdict["algorithm"] #delete the dictionary algorithm

        for k in reportdict.keys():
            self.report.append([k, reportdict[k][0], reportdict[k][1], reportdict[k][2]])
            
    def __set_report(self, reportdict: OrderedDict):
        for k in reportdict.keys():
            self.report.append([k, reportdict[k]])
