__author__ = u"Tommaso Mazza"
__copyright__ = u"Copyright 2018-2020, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.3"
__maintainer__ = u"Tommaso Mazza"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"09/07/2020"
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

from config import *
import copy
import csv, os, xlsxwriter, json
from igraph import Graph
from tools.enums import KpnegEnum, KpposEnum, ReportEnum, GroupCentralityEnum, GroupDistanceEnum
from cmds.cmds_utils.pyntacleink_template import html_template, css_template
from exceptions.wrong_argument_error import WrongArgumentError
from collections import OrderedDict
from io_stream.exporter import PyntacleExporter


class PyntacleReporter:
    r"""
    This class creates a report according to the type of analysis performed by Pyntacle
    """
    logger = None

    def __init__(self, graph: Graph):
        self.logger = log
        self.graph = graph

        self.report_type = None  # this will be instanced in create_report
        self.report = []  # this will be used in create_report
        self.dat = runtime_date

    def create_report(self, report_type: ReportEnum, report: OrderedDict):
        r"""
        Initialize the report object by writing generic information on the input graph and calling the internal report
        creators, according to the value passed by the "Report" enumerator

        :param Report report_type: one of the type of the "Report" enumerator
        :param OrderedDict report: a dictionary containing all the information to be reported
        """

        if not isinstance(report_type, ReportEnum):
            raise TypeError(u"'report_type' must be on of the 'ReportEnum' enumerators, {} found".format(
                type(report_type).__name__))

        if not isinstance(report, OrderedDict):
            raise ValueError(u"'report' must be an ordered Dictionary")

        self.report_type = report_type
        self.report = []
        self.report.append(["Pyntacle Report", report_type.name])
        self.report.append(["Run Date", self.dat])
        self.report.append("\n")
        self.report.append(["Network Overview"])
        self.report.append(["Graph name", ",".join(self.graph["name"])])
        self.report.append(["Number of Components", len(self.graph.components())])
        self.report.append(["Nodes", self.graph.vcount()])
        self.report.append(["Edges", self.graph.ecount()])
        self.report.append("\n")

        report_copy = copy.deepcopy(report)

        if report_type == ReportEnum.Local:
            self.__local_report__(reportdict=report_copy)
        elif report_type == ReportEnum.Global:
            self.__global_report__(reportdict=report_copy)
        elif report_type == ReportEnum.KP_info:
            self.__KPinfo_report__(reportdict=report_copy)
        elif report_type == ReportEnum.GR_info:
            self.__GRinfo_report__(reportdict=report_copy)
        elif report_type == ReportEnum.KP_greedy:
            self.__greedy_report__(reportdict=report_copy, algo_type="kp")
        elif report_type == ReportEnum.GR_greedy:
            self.__greedy_report__(reportdict=report_copy, algo_type="gr")
        elif report_type == ReportEnum.KP_bruteforce:
            self.__bruteforce_report__(reportdict=report_copy, type="kp")
        elif report_type == ReportEnum.GR_bruteforce:
            self.__bruteforce_report__(reportdict=report_copy, type="gr")
        elif report_type == ReportEnum.KP_stochasticgradientdescent:
            self.__sgd_report__(reportdict=report_copy, algo_type="kp")
        elif report_type == ReportEnum.GR_stochasticgradientdescent:
            self.__sgd_report__(reportdict=report_copy, algo_type="gr")
        elif report_type == ReportEnum.Communities:
            self.__communities_report__(reportdict=report_copy)
        elif report_type == ReportEnum.Set:
            self.__set_text_report__(reportdict=report_copy)
        else:
            raise ValueError(u"Specified report type does not exist")

    def write_report(self, report_dir=None, format="tsv", choices=report_format) -> str:
        r"""
        Create a text file containing the information created previously by the any of the *report* functions.
        By default, if the `report_path` function is not initialized, a generic name is created and a tab-separated file
        is generated (named *Report_**GRAPHNAME**_**COMMAND**_**DATE**.tsv* where:_

        * **GRAPHNAME** is the value stored in the graph["name"] attribute,
        * **Command** is the name of the command requested by the user and
        * **Date** is the date when the Pyntacle run was completed. This file will be stored in the current directory
        """

        if not self.report:
            raise EnvironmentError(
                u"A report must be created first using the 'create_report()' function")
        else:
            # cast every element of the list of lists to string, just in case:
            for x in self.report:
                list(map(str, x))

            self.report = [list(map(str, x)) for x in self.report]
            # replace all the underscores with spaces
            self.report[0] = [x.replace("_", " ") for x in self.report[0]]

        if format not in choices.keys():
            raise WrongArgumentError(u"file format {} is not supported".format(format))
        if report_dir is None:
            self.logger.info(u"Directory not specified. Using current directory")
            report_dir = os.path.abspath(os.getcwd())
        else:
            if not os.path.isdir(report_dir):
                self.logger.warning(u"Specified directory does not exists, creating it")
                os.makedirs(report_dir, exist_ok=True)
            else:
                report_dir = os.path.abspath(report_dir)

        if len(self.graph["name"]) > 1:
            self.logger.warning(u"Using the first 'name' attribute of graph name since more than one is specified")

        graphname = self.graph["name"][0]
        extension = choices[format]

        if self.report_type.name == 'Set':
            report_path = os.path.join(report_dir,
                                       "_".join(["Report", self.report_type.name, self.dat]) + "." + extension)
        else:
            report_path = os.path.join(report_dir, "_".join(
                ["Report", graphname, self.report_type.name, self.dat]) + "." + extension)

        if extension != "xlsx":
            with open(report_path, "w") as out:
                if extension == "tsv":
                    self.logger.info(u"Writing Pyntacle report to a tab-separated file (tsv)")
                    for elem in self.report:
                        elem.append("\n")
                    out.writelines(["\t".join(x) for x in self.report])
                elif extension == "csv":
                    self.logger.info(u"Writing Pyntacle report to a comma-separated value file (csv)")
                    writer = csv.writer(out)
                    writer.writerows(self.report)
        else:
            self.logger.info(u"Writing Pyntacle report to a an excel file (xlsx)")
            workbook = xlsxwriter.Workbook(report_path, {'constant_memory': True})
            workbook.use_zip64()
            format = workbook.add_format()

            worksheet = workbook.add_worksheet("Pyntacle Report")
            for row, elem in enumerate(self.report):
                for col, p in enumerate(elem):
                    worksheet.write(row, col, p, format)

            workbook.close()

    def __local_report__(self, reportdict: OrderedDict):
        r"""
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
            # nodes = nodes.split(',')
            del reportdict["nodes"]

        self.report.append(["Results - Local centrality indices for the input nodes"])
        self.report.append(["Node Name"] + [x.replace("_", " ") for x in reportdict.keys()])
        addendum = []  # list that will be added to the self.report object

        for i, elem in enumerate(nodes):
            temp = []
            temp.append(elem)  # append the node names to the appendum
            for k in reportdict.keys():
                temp.append(round(reportdict[k][i], 5))  # append the corresponding value to the node name
            addendum.append(temp)
        self.report = self.report + addendum

    def __global_report__(self, reportdict: OrderedDict):
        r"""
        Fill the `report` object with information regarding all the global metrics stored in the reportdict object

        :param reportdict: a dictionary like {name of the global metric: metric}
        """

        self.report.append(["Results - Global Metrics of the input graph"])
        self.report.append(["Metric", "Value"])
        for k in reportdict.keys():
            self.report.append([k, reportdict[k]])

    def __KPinfo_report__(self, reportdict: OrderedDict):
        r"""
        fill the *self.__report* object with all the values stored in the KPINFO Run
        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """
        # this doesn't work for now: keys are strings and not KP choices.
        # if not all(isinstance(x, str) for x in reportdict.keys()):
        #     raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if KpnegEnum.F.name in reportdict.keys():
            init_F = reportdict[KpnegEnum.F.name][2]

            if 0.0 <= init_F <= 1.0:
                self.report.append(["Starting F value", init_F])
            else:
                raise ValueError(u"Initial F must range between 0 and 1")

        if KpnegEnum.dF.name in reportdict.keys():
            init_dF = reportdict[KpnegEnum.dF.name][2]

            if 0.0 <= init_dF <= 1.0:
                self.report.append(["Starting dF value", init_dF])
            else:
                raise ValueError(u"Initial dF must range between 0 and 1")

        if KpposEnum.mreach.name in reportdict.keys():
            m = reportdict[KpposEnum.mreach.name][2]

            if not isinstance(m, int) and m < 1:
                raise ValueError(u"m must be a positive integer")
            else:
                self.report.append(["maximum m-reach distance", reportdict[KpposEnum.mreach.name][2]])

            # change the name `mreach` to `m-reach`
            reportdict["m-reach"] = reportdict[KpposEnum.mreach.name]
            del reportdict[KpposEnum.mreach.name]

        self.report.append(["\n"])
        self.report.append(["Results: key player metrics for the requested node set"])
        self.report.append(["Index", "Nodes", "Key Player value"])

        for k in reportdict.keys():
            if (k == KpnegEnum.F.name or k == KpnegEnum.dF.name) and reportdict[k][-1] == 1.0:
                self.report.append([k, "NA", "MAXIMUM FRAGMENTATION REACHED"])

            else:
                self.report.append([k, ",".join(reportdict[k][0]), round(reportdict[k][1], 5)])

    def __GRinfo_report__(self, reportdict: OrderedDict):
        r"""
        fill the *self.report* object with all the values stored in the GRINFO Run

        :param reportdict: a dictionary with Group centrality indices as `keys` and a list as `values`
        """

        for key in reportdict.keys():
            if key.startswith(GroupCentralityEnum.group_closeness.name):
                dist = key.split("_")[-1]
                self.report.append(["group closeness distance", dist])
                self.report.append(["\n"])

        self.report.append(["Results: group centrality metrics for the input set of nodes"])
        self.report.append(["\n"])
        self.report.append(["Metric", "Nodes", "Value"])

        for k in reportdict.keys():

            if k.startswith(GroupCentralityEnum.group_closeness.name):
                metric_correct = "group closeness"
            else:
                metric_correct = k.replace("_", " ")

            self.report.append([metric_correct, ",".join(reportdict[k][0]), round(reportdict[k][1], 5)])

    def __greedy_report__(self, reportdict: OrderedDict, algo_type: str = "kp"):
        r"""
        fill the *self.__report* object with all the values contained in the Greedy Optimization Run

        :param dict reportdict: a dictionary  with the group distance names as  `keys` and a list as `values`
        """

        if algo_type == "kp":
            if KpnegEnum.F.name in reportdict.keys():
                init_F = reportdict[KpnegEnum.F.name][2]

                if 0.0 <= init_F <= 1.0:
                    self.report.append(["Starting graph F value", init_F])
                else:
                    raise ValueError(u"Initial F must range between 0 and 1")

            if KpnegEnum.dF.name in reportdict.keys():
                init_dF = reportdict[KpnegEnum.dF.name][2]

                if 0.0 <= init_dF <= 1.0:
                    self.report.append(["Starting graph dF value", init_dF])
                else:
                    raise ValueError(u"Initial dF must range between 0 and 1")

            if KpposEnum.mreach.name in reportdict.keys():
                m = reportdict[KpposEnum.mreach.name][2]

                if not isinstance(m, int) and m < 1:
                    raise ValueError(u"'m' must be a positive integer")
                else:
                    self.report.append(["maximum m-reach distance", reportdict[KpposEnum.mreach.name][2]])
                    self.report.append(["\n"])

                reportdict["m-reach"] = reportdict[KpposEnum.mreach.name]
                del reportdict[KpposEnum.mreach.name]

            self.report.append(["Results:"])
            self.report.append(["Index", "Node set", "Value"])

            for k in reportdict.keys():
                if (k == KpnegEnum.F.name or k == KpnegEnum.dF.name) and reportdict[k][-1] == 1.0:
                    self.report.append([k, "NA", "MAXIMUM FRAGMENTATION REACHED"])

                else:
                    self.report.append([k, ",".join(reportdict[k][0]), reportdict[k][1]])

        elif algo_type == "gr":
            for key in reportdict.keys():
                if key.startswith(GroupCentralityEnum.group_closeness.name):
                    dist = key.split("_")[-1]
                    self.report.append(["group closeness distance", dist])
                    self.report.append(["\n"])

            self.report.append(["Results:"])
            self.report.append(["Index", "Node set", "Value"])

            for k in reportdict.keys():
                if k.startswith(GroupCentralityEnum.group_closeness.name):
                    metric_correct = "group closeness"
                else:
                    metric_correct = k.replace("_", " ")

                self.report.append([metric_correct, ",".join(reportdict[k][0]), round(reportdict[k][1], 5)])

        else:
            raise ValueError("Invalid report type (choices are: 'kp', 'gr'")

    def __sgd_report__(self, reportdict: OrderedDict, algo_type: str = "kp"):
        r"""
        fill the *self.__report* object with all the values contained in the stochastic gradient descent Run
        :param dict reportdict: a dictionary  with the group distance names as  `keys` and a list as `values`
        """

        if algo_type == "kp":
            if KpnegEnum.F.name in reportdict.keys():
                init_F = reportdict[KpnegEnum.F.name][2]
                self.report.append(["Starting graph F value", init_F])

            if KpnegEnum.dF.name in reportdict.keys():
                init_dF = reportdict[KpnegEnum.dF.name][2]
                self.report.append(["Starting graph dF value", init_dF])

            if KpposEnum.mreach.name in reportdict.keys():
                m = reportdict[KpposEnum.mreach.name][2]
                self.report.append(["maximum m-reach distance", reportdict[KpposEnum.mreach.name][2]])
                self.report.append(["\n"])
                reportdict["m-reach"] = reportdict[KpposEnum.mreach.name]
                del reportdict[KpposEnum.mreach.name]

            self.report.append(["Results:"])
            self.report.append(["Index", "Node set", "Value"])

            for k in reportdict.keys():
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

        elif algo_type == "gr":
            for key in reportdict.keys():
                if key.startswith(GroupCentralityEnum.group_closeness.name):
                    dist = key.split("_")[-1]
                    self.report.append(["group-closeness distance", dist])
                    self.report.append(["\n"])

            self.report.append(["Results:"])
            self.report.append(["Index", "Node set", "Value"])

            for k in reportdict.keys():
                if k.startswith(GroupCentralityEnum.group_closeness.name):
                    metric_correct = "group-closeness"
                else:
                    metric_correct = k.replace("_", "-")

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

                # self.report.append([metric_correct, ",".join(reportdict[k][0]), round(reportdict[k][1], 5)])
        else:
            raise ValueError("Invalid report type (choices are: 'kp', 'gr'")

    def __bruteforce_report__(self, reportdict: OrderedDict, type: str = "kp"):
        r"""
        Fill the ``self.__report`` object with all the values contained in the brute-force search run

        :param reportdict: a dictionary with KPPOSchoices or KPNEGchoices as  `keys` and a list as `values`
        """

        # if not all(isinstance(x, (KPPOSchoices, KPPOSchoices)) for x in reportdict.keys()):
        #     raise TypeError("one of the keys in the report dictionary is not a KPPOSchoices or KPNEGchoices")

        if type == "kp":

            if KpnegEnum.F.name in reportdict.keys():
                init_F = reportdict[KpnegEnum.F.name][2]

                if 0.0 <= init_F <= 1.0:
                    self.report.append(["Starting graph F", init_F])
                else:
                    raise ValueError(u"Initial F must range between 0 and 1")

            if KpnegEnum.dF.name in reportdict.keys():
                init_dF = reportdict[KpnegEnum.dF.name][2]

                if 0.0 <= init_dF <= 1.0:
                    self.report.append(["Starting graph dF", init_dF])
                else:
                    raise ValueError(u"Initial dF must range between 0 and 1")

            if KpposEnum.mreach.name in reportdict.keys():
                m = reportdict[KpposEnum.mreach.name][2]

                if not isinstance(m, int) and m < 1:
                    raise ValueError(u"'m' must be a positive integer")
                else:
                    self.report.append(["maximum m-reach distance", reportdict[KpposEnum.mreach.name][2]])

                reportdict["m-reach"] = reportdict[KpposEnum.mreach.name]
                del reportdict[KpposEnum.mreach.name]

            self.report.append(["Results:"])
            self.report.append(["Index", "Node set", "Value"])

            for k in reportdict.keys():
                if (k == KpnegEnum.F.name or k == KpnegEnum.dF.name) and reportdict[k][-1] == 1.0:
                    self.report.append([k, "NA", "MAXIMUM FRAGMENTATION REACHED"])

                else:
                    # in this case, the report dictionary can contain more than one set of nodes
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

        elif type == "gr":
            for key in reportdict.keys():
                if key.startswith(GroupCentralityEnum.group_closeness.name):
                    dist = key.split("_")[-1]
                    self.report.append(["group closeness distance", dist])
                    self.report.append(["\n"])

            self.report.append(["Results:"])
            self.report.append(["Index", "Node set", "Value"])

            for k in reportdict.keys():
                if k.startswith(GroupCentralityEnum.group_closeness.name):
                    metric_correct = "group closeness"
                else:
                    metric_correct = k.replace("_", " ")

                if len(reportdict[k][0]) > 1:
                    count = 0
                    for elem in reportdict[k][0]:
                        if count == 0:
                            self.report.append([metric_correct, ",".join(reportdict[k][0][0]), reportdict[k][1]])
                        else:
                            self.report.append(["", ",".join(elem), reportdict[k][1]])
                        count += 1
                else:
                    self.report.append([metric_correct, ",".join(reportdict[k][0][0]), reportdict[k][1]])

        else:
            raise ValueError("Invalid report type (choices are: 'kp', 'gr'")

    def __communities_report__(self, reportdict: OrderedDict):
        r"""
        Report General information regarding the communities (nodes, edges, component, algorithm)
        stored in the ``reportdic``. The reportdic **MUST** also contain a `algorithms` key that will be used to report
        the type of algorithm used

        :param reportdict: a dictionary from Pyntacle communities
        """
        self.report.append(["Results: Community finding of the input graph"])
        self.report.append(["Algorithm:", reportdict["algorithm"]])
        self.report.append(["\n"])
        del reportdict["algorithm"]  # delete the dictionary algorithm
        self.report.append(["\n"])
        self.report.append(["Module Label", "Nodes", "Edges", "Components"])
        for k in reportdict.keys():
            self.report.append([k, reportdict[k][0], reportdict[k][1], reportdict[k][2]])

    def __set_text_report__(self, reportdict: OrderedDict):

        for k in reportdict.keys():
            self.report.append([k, reportdict[k]])

    def pyntacleink_report(self, report_dir: str, report_dict: OrderedDict or None, suffix: str):
        """
        Create a JSON version of the report, possibly appending data to already existing results.
        :return:
        """

        inner_dir = os.path.join(report_dir, "_".join([".pyntacleink", suffix]))

        try:
            os.makedirs(inner_dir)
        except OSError:
            pass
            # log.warning("Internal directory for storing JSON files already exists")

        index_path = os.path.join(report_dir, "_".join(["pyntacleink", suffix]) + ".html")

        index_css_path = os.path.join(inner_dir, 'index.css')
        json_report = os.path.join(inner_dir, 'report.js')
        json_graph = os.path.join(inner_dir, 'graph.js')

        if os.path.exists(json_report):
            json_line = open(json_report).readlines()[0].split(' = ')[1]
            # print("LINEA", json_line)

            with open(json_report, 'r') as f:
                json_data = json.loads(json_line)
        else:
            json_data = {}

        if self.report_type == ReportEnum.KP_bruteforce or self.report_type == ReportEnum.KP_greedy:
            json_data.setdefault("Key-player", {})
            json_data["Key-player"].setdefault(str(self.report_type).split('.')[1], {})
            json_data["Key-player"][str(self.report_type).split('.')[1]].setdefault(self.dat, {})

            # multiple_sol
            for k in report_dict:

                if self.report_type == ReportEnum.KP_greedy:
                    json_data["Key-player"][str(self.report_type).split('.')[1]][self.dat][k] = [
                        ','.join(report_dict[k][0])]

                elif self.report_type == ReportEnum.KP_bruteforce:
                    json_data["Key-player"][str(self.report_type).split('.')[1]][self.dat][k] = [
                        ';'.join(list(','.join(sol) for sol in report_dict[k][0]))]

                # Adding numerical values of solutions
                json_data["Key-player"][str(self.report_type).split('.')[1]][self.dat][k].extend(report_dict[k][1:])

        if self.report_type == ReportEnum.GR_bruteforce or self.report_type == ReportEnum.GR_greedy:
            json_data.setdefault("Group-centrality", {})
            json_data["Group-centrality"].setdefault(str(self.report_type).split('.')[1], {})
            json_data["Group-centrality"][str(self.report_type).split('.')[1]].setdefault(self.dat, {})

            # multiple_solutions
            for k in report_dict:
                # Mauro's print for testing purposes
                # print(report_dict[k][0])

                if self.report_type == ReportEnum.GR_greedy:
                    json_data["Group-centrality"][str(self.report_type).split('.')[1]][self.dat][k] = [
                        ','.join(report_dict[k][0])]

                elif self.report_type == ReportEnum.GR_bruteforce:
                    json_data["Group-centrality"][str(self.report_type).split('.')[1]][self.dat][k] = [
                        ';'.join(list(','.join(sol) for sol in report_dict[k][0]))]

                # Adding numerical values of solutions
                json_data["Group-centrality"][str(self.report_type).split('.')[1]][self.dat][k].extend(
                    report_dict[k][1:])

        if self.report_type == ReportEnum.Communities:
            json_data.setdefault("Communities", {})
            json_data["Communities"].setdefault(report_dict["algorithm"], {})
            json_data["Communities"][report_dict["algorithm"]].setdefault(self.dat, {})

            for i, k in enumerate(report_dict["communities"]):
                json_data["Communities"][report_dict["algorithm"]][self.dat][i] = [report_dict["communities"][i][1]]

        if self.report_type == ReportEnum.Set:

            json_data.setdefault("Set", {})
            json_data["Set"].setdefault(report_dict["algorithm"], {})
            json_data["Set"][report_dict["algorithm"]].setdefault(self.dat, {})

            for k in report_dict.keys():

                if k == 'algorithm':
                    continue
                json_data["Set"][report_dict["algorithm"]][self.dat][k] = [report_dict[k]['nodes'], ';'.join(
                    ['-'.join(e) for e in report_dict[k]['edges']])]

                # for testing purposes only
                # edges = [', '.join(e) for e in report_dict[k]['edges']]
                # for edge in report_dict[k]['edges']:
                #     print(edge)
            # print(edges)

        # Adding minimal graph info
        json_data.setdefault("Info", {})
        json_data["Info"]['graph name'] = self.graph["name"][0]
        json_data["Info"]['nodes'] = len(self.graph.vs())
        json_data["Info"]['edges'] = len(self.graph.es())
        json_data["Info"]['components'] = len(self.graph.components())

        # Adding global metrics to the basic info, if available
        # TODO manca global --no-nodes. Idealmente, dovrebbe essere una parte della tabella ACCANTO alle metriche globali senza aver rimosso i nodi
        # todo per il momento, vengono prodotti due report (file cmds/metrics.py, linea ~385)
        if self.report_type == ReportEnum.Global:

            for i in report_dict.keys():
                json_data["Info"][i] = report_dict[i]

        # todo metrics LOCAL È STATO MESSO COME "FILTRI" SUI NODI (vedi cmds.metrics, line ~229)
        # exporting results in json format
        with open(json_report, 'w') as f:
            f.write("var reportData = ")
            json.dump(json_data, f, ensure_ascii=False)

        # exporting graph in json format
        PyntacleExporter.JSON(self.graph, json_graph, prefix="var graphData = ")

        # modify html template to point it at the correct hidden directory
        html_template_correct = html_template.replace("PLACEHOLDER", suffix)

        # print html_file
        with open(index_path, 'w') as f:
            f.write(html_template_correct)
        with open(index_css_path, 'w') as f:
            f.write(css_template)
