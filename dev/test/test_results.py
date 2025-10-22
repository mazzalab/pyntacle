import pandas as pd 
import subprocess
import ast
import numpy as np


input_path = './input'
ourOutput_path = './ourOutput'
output_path = './output'

output_expected_local= output_path + "figure8_local.txt"
output_expected_global= output_path + "figure8_global.txt"
output_expected_keyplayer_finder= output_path + "figure8_kpfinder_bruteforce.txt"
output_expected_keyplayer_info= output_path + "figure8_kpinfo.txt"
output_expected_groupcentrality_finder= output_path + "figure8_grfinder_bruteforce.txt"
output_expected_groupcentrality_info= output_path + "figure8_grinfo.txt"
output_expected_set_union= output_path + "result_union.txt"
output_expected_set_intersection= output_path + "result_intersect.txt"
output_expected_set_difference= output_path + "result_difference.txt"
output_expected_mesoscale= output_path + "tesi_graph_3stepX.tsv"


 # Function to sort tuples within each list
def sort_tuples_in_list(k_set_str):
    k_set_list = ast.literal_eval(k_set_str)
    sorted_k_set = sorted([tuple(sorted(tup)) for tup in k_set_list])
    return str(sorted_k_set)


def test_local():	

 subprocess.call(f"python3 main.py local -t matrix -i {input_path}/figure_8.txt -o {ourOutput_path}/",shell=True)

 df_expected=pd.read_csv(output_expected_local,sep="\t")
 df=pd.read_csv(f"{ourOutput_path}/Report_figure_8_local.tsv",sep="\t",skiprows=9)[:5]

 ### remove Eigenvector perchè fatta diversamente da capocefalo (noi scaliamo ed utilizziamo igraph func)
 df.drop(["Eigenvector (Scaled)"],axis=1,inplace=True)
 df_expected.drop(["Eigenvector (Scaled)"],axis=1,inplace=True)

 v=(df==df_expected).all()
 assert all(v)==True

def test_global():	

 subprocess.call(f"python3 main.py global -t matrix -i {input_path}/figure_8.txt -o {ourOutput_path}/",shell=True)

 df_expected=pd.read_csv(output_expected_global,sep="\t")
 df=pd.read_csv(f"{ourOutput_path}/Report_figure_8_global.tsv",sep="\t",skiprows=10)

 ### remove Compactness perchè diversamente fatta da capocefalo
 df=df[:-1]
 df_expected=df_expected[:-1]

 v=(df==df_expected).all()
 assert all(v)==True


def test_keyplayer_finder():	

 subprocess.call(f"python3 main.py keyplayer kp-finder -t matrix -i {input_path}/figure_8.txt -o {ourOutput_path}/",shell=True)

 df_expected=pd.read_csv(output_expected_keyplayer_finder,sep="\t")
 df=pd.read_csv(f"{ourOutput_path}/Report_figure_8_keyplayer_finder_all.tsv",sep="\t",skiprows=9)

 # Sort the tuples within the 'K-set' column
 df_expected['K-set'] = df_expected['K-set'].apply(sort_tuples_in_list)
 df['K-set'] = df['K-set'].apply(sort_tuples_in_list)

 v=(df==df_expected).all()
 assert all(v)==True


def test_keyplayer_info():	

 subprocess.call(f"python3 main.py keyplayer kp-info -t matrix -n HS,HA,GM -i {input_path}/figure_8.txt -o {ourOutput_path}/",shell=True)

 df_expected=pd.read_csv(output_expected_keyplayer_info,sep="\t")
 df=pd.read_csv(f"{ourOutput_path}/Report_figure_8_keyplayer_info_all.tsv",sep="\t",skiprows=9)

 df_expected["Key-player"] = df_expected["Key-player"].apply(lambda x: sorted(x) if isinstance(x, list) else x)
 df["Key-player"] = df["Key-player"].apply(lambda x: sorted(x) if isinstance(x, list) else x)
 v=(df==df_expected).all()

 assert all(v)==True



def test_groupcentrality_finder():	

 subprocess.call(f"python3 main.py groupcentrality gc-finder -t matrix -k 2 -i {input_path}/figure_8.txt -o {ourOutput_path}/",shell=True)

 df_expected=pd.read_csv(output_expected_groupcentrality_finder,sep="\t")
 df=pd.read_csv(f"{ourOutput_path}/Report_figure_8_groupcentrality_finder_all.tsv",sep="\t",skiprows=9)

 # Sort the tuples within the 'K-set' column
 df_expected['Nodes Set'] = df_expected['Nodes Set'].apply(sort_tuples_in_list)
 df['Nodes Set'] = df['Nodes Set'].apply(sort_tuples_in_list)

 v=(df==df_expected).all()
 assert all(v)==True


def test_groupcentrality_info():	

 subprocess.call(f"python3 main.py groupcentrality gc-info -t matrix -n HS,HA,GM -i {input_path}/figure_8.txt -o {ourOutput_path}/",shell=True)

 df_expected=pd.read_csv(output_expected_groupcentrality_info,sep="\t")
 df=pd.read_csv(f"{ourOutput_path}/Report_figure_8_groupcentrality_info_all.tsv",sep="\t",skiprows=9)

 df_expected["Nodes_set"] = df_expected["Nodes_set"].apply(lambda x: sorted(x) if isinstance(x, list) else x)
 df["Nodes_set"] = df["Nodes_set"].apply(lambda x: sorted(x) if isinstance(x, list) else x)
	
 v=(df==df_expected).all()
 assert all(v)==True



def test_set_union():	

	subprocess.call(f"python3 main.py set union -t matrix -i {input_path}/set1.txt -i2 {input_path}/set2.txt -o {ourOutput_path}/",shell=True)

	df_expected=pd.read_csv(output_expected_set_union,sep="\t",index_col=0)
	df=pd.read_csv(f"{ourOutput_path}/set1_&_set2_union.txt",sep="\t", index_col=0)

	df = df.sort_index(axis=0).sort_index(axis=1)
	
	v=(df==df_expected).all()
	assert all(v)==True


def test_set_difference():

	subprocess.call(f"python3 main.py set difference -t matrix -i {input_path}/set1.txt -i2 {input_path}/set2.txt -o {ourOutput_path}/",shell=True)

	df_expected=pd.read_csv(output_expected_set_difference,sep="\t",index_col=0)
	df=pd.read_csv(f"{ourOutput_path}/set1_&_set2_difference.txt",sep="\t", index_col=0)

	df = df.sort_index(axis=0).sort_index(axis=1)
	
	v=(df==df_expected).all()
	assert all(v)==True



def test_set_intersect():	

	subprocess.call(f"python3 main.py set intersection -t matrix -i {input_path}/set1.txt -i2 {input_path}/set2.txt -o {ourOutput_path}/",shell=True)

	df_expected=pd.read_csv(output_expected_set_intersection,sep="\t",index_col=0)
	df=pd.read_csv(f"{ourOutput_path}/set1_&_set2_intersection.txt",sep="\t", index_col=0)

	df = df.sort_index(axis=0).sort_index(axis=1)
	
	v=(df==df_expected).all()
	assert all(v)==True


# output_expected_mesoscale
def test_mesoscale():

	subprocess.call(f"python3 main.py mesoscale -t dot -i {input_path}/tesi_graph.dot -k 3 -o {ourOutput_path}/",shell=True)

	df_expected=pd.read_csv(output_expected_mesoscale,sep="\t",index_col=0)
	df=pd.read_csv(f"{ourOutput_path}/Report_tesi_graph_mesoscale.tsv",sep="\t", index_col=0,skiprows=9)

	df_expected.drop(["Unnamed: 9"],axis=1,inplace=True)
	
	# Confronto ignorando colonne e indici
	v=(df.values==df_expected.values).all()
	assert v==True