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

from algorithms.local_topology import LocalTopology
from io_stream.importer import PyntacleImporter as pyimp
from algorithms.global_topology import GlobalTopology
from tools.octopus import Octopus
from tools.enums import CmodeEnum
from algorithms.shortest_path import ShortestPath
import numpy as np



# def culo(graph: Graph):
#     cmode = get_cmode(graph)
#     print(cmode)
#     return GlobalTopology.average_radiality(graph, cmode)

def main():
    gg = pyimp.AdjacencyMatrix(
        "/home/local/MENDEL/d.capocefalo/Dropbox/Research/BFX_Mendel/BFX Lab/Pyntacle/site_material/Case_Study_2/APID_CAEEL_Level2_maincomponent.adjm  ")

    sp_cpu = ShortestPath.get_shortestpaths(graph=gg, nodes=None, cmode=CmodeEnum.cpu)
    print(sp_cpu)
    print("\n"*2)
    sp_gpu = ShortestPath.get_shortestpaths(graph=gg, nodes=None, cmode=CmodeEnum.gpu)
    print(sp_gpu)
    print("\n" * 2)
    print(np.array_equal(sp_cpu, sp_gpu))

    # print(gg["implementation"])
    # a = GlobalTopology.average_radiality(gg, cmode=CmodeEnum.gpu)
    # print(a)
    # input()
    # b = culo(gg)
    # Octopus.add_average_radiality(gg)
    #
    # Octopus.add_average_shortest_path_length(gg)
    # Octopus.add_average_global_shortest_path_length(gg)
    # print(a)
    # print(b)
    # print(gg["average_radiality"])
    # print(gg["average_global_shortest_path_length"])
    # print(gg.vs()["average_shortest_path_length"])
    # print("#" * 100)
    # print(ShortestPath.get_shortestpaths(gg, cmode=CmodeEnum.cpu))
    # print("#"*100)
    # print(ShortestPath.get_shortestpaths(gg, cmode=CmodeEnum.gpu))


    # print(gg["average_radiality"])


if __name__ == "__main__":
    main()

