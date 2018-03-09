from pyntacle_commands_utils.kpsearch_wrapper_NEW import KPWrapper
from misc.enums import KPNEGchoices
from io_stream.importer import PyntacleImporter as pi
from igraph import Graph

graph = pi.AdjacencyMatrix(file="", sep="\t", header=True)