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

""" insert your method description here """

from tools.octopus import Octopus
from io_stream.importer import PyntacleImporter as pyimp

gg = pyimp.AdjacencyMatrix("/home/local/MENDEL/d.capocefalo/Desktop/Pyntacle_benchmarks/test_networks/Real_Borgatti_figure_8.adjm",sep="\t")

print(gg.summary())
k = 2
Octopus.add_GO_dR(gg, k=k)
print(gg.summary())
print (gg["dR_greedy"])
k = 3
Octopus.add_GO_dR(gg, k=k)
print(gg.summary())
print(gg["dR_greedy"])

Octopus.add_group_degree(gg, nodes=["LK", "MJ"])
print(gg.summary())
print (gg["group_degree_info"])

k=2
Octopus.add_group_degree(gg, nodes=["LK", "MJ", "ciaone"])
print(gg.summary())
print (gg["group_degree_info"])

# Octopus.add_GO_dR(gg, k=k)
#
# Octopus.add_GO_group_betweeness(gg, k=k)
#
# print(gg.attributes())
# print(gg["group_betweenness_greedy"])
# print(gg["dR_greedy"])
#
# Octopus.add_group_closeness(graph=gg, nodes=['PS', 'LK'])
# print (gg.attributes())
# print(gg["group_closeness_minimum"])

# Octopus.add_BF_group_degree()
# Octopus.add_BF_group_closeness()
# Octopus.add_GO_group_betweeness()
# Octopus.add_GO_group_degree()
# Octopus.add_GO_group_closeness()
# Octopus.add_group_betweenness()
# Octopus.add_group_closeness()
# Octopus.add_group_degree()