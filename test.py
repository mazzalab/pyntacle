import sys

# load the connectome with Pyntacle Importer
#you can replace `connectome path` with the appropriate $PATH to your connectome
connectome_path = "/home/local/MENDEL/d.capocefalo/Dropbox/Research/BFX_Mendel/BFX Lab/Pyntacle/site_material/Case_Study_3/CAEEL_Connectome.txt"

from io_stream.importer import PyntacleImporter as pyimp
graph = pyimp.Sif(connectome_path) #this is an `igraph.Graph` object
graph.summary() #returns the graph summary

########################################################################################################################

#evaluate the small-world phenomenon

from tools.octopus import Octopus
Octopus.add_average_degree(graph)
Octopus.add_average_global_shortest_path_length(graph)

print(graph["average_degree"])
print(graph["average_global_shortest_path_length"])

########################################################################################################################

#compute and rank the nodes by degree
Octopus.add_degree(graph)

#store the result into a pd.DataFrame and then rank by degree
import pandas as pd

df = pd.DataFrame({"Degree":graph.vs["degree"]}, index=graph.vs["name"])
df = df.sort_values(by=["Degree"], ascending=False)

########################################################################################################################


#Compute the group centralities for the rich club core

rc = ["AVAR", "AVAL", "AVBL",
      "AVBR", "AVER", "AVDR",
      "AVEL", "PVCL", "PVCR",
      "DVA", "AVDL"]


Octopus.add_group_degree(graph, rc)
print("group degree:", graph["group_degree_info"], sep="\t")

Octopus.add_group_betweenness(graph, rc)
print("group  betweenness:", graph["group_betweenness_info"], sep="\t")

Octopus.add_group_closeness(graph, rc)
print("group  closeness:", graph["group_closeness_minimum_info"], sep="\t")


#condense all the group centralities into a pandas dataframe
rc_ind = " ".join(rc)
rc_key = tuple(rc)

dfdict = {"group degree": graph["group_degree_info"][rc_key],
          "group betweenness": graph["group_betweenness_info"][rc_key],
          "group closeness (min)": graph["group_closeness_minimum_info"][rc_key]}

df = pd.DataFrame(dfdict, index=[rc_ind])

df.index = ["rich club core"]
print(df)
#save the dataframe to dictionary
df.to_csv("/home/local/MENDEL/d.capocefalo/Dropbox/Research/BFX_Mendel/BFX Lab/Pyntacle/site_material/Case_Study_3/CS3_rich_club_groupcentralities.tsv", sep="\t")

#######################################################################################################################

#Greedily-optimized search for GC
Octopus.add_GO_group_degree(graph, 11, seed=1)
print (graph["group_degree_greedy"])

for e in graph["group_degree_greedy"].keys():
    for elem in e:
        print(elem, graph.vs.select(name=elem)["degree"])


test = ['AIAL', 'AVAR', 'AVBL', 'AVKR', 'CEPDR', 'DVA', 'PVCL', 'RIAR', 'RIBL', 'RIH', 'VC03']
Octopus.add_group_degree(graph, test)
print(graph["group_degree_info"])

sys.exit()
input()
Octopus.add_GO_group_closeness(graph, 11, seed=1)
print (graph["group_closeness_minimum_greedy"])


input()
Octopus.add_GO_group_betweeness(graph, 11, seed=1)
print (graph["group_betweeness_greedy"])