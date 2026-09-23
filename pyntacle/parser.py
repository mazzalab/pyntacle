# from colorama import Fore, Style
import argparse
import textwrap

import os

try:
    from colorama import Fore, Style
except Exception:
    # fallback: parser importabile anche senza colorama
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = _NoColor()

# Se stiamo buildando la documentazione (Sphinx), niente colori ANSI
if os.environ.get("PYNTACLE_DOCS", "0") == "1":
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = _NoColor()


# build parser 
def create_parser() -> argparse.ArgumentParser:

	#### principal parser
	parser = argparse.ArgumentParser(description= Fore.GREEN + Style.BRIGHT +'''\n\n

	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀       ⢀⡤⠒⠉⠉⠉⠒⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⢠⠋⠀⠀⠐⠤⠂⠀⠀⠱⡀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⢊⣍⡶⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢳⠀⠀⢶⣭⡱⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠦⣜⠒⠒⠲⣼⡇⠀⠀⠀⢪⠀⡕⠀⠀⠀⢸⢤⠒⠒⢚⣠⠞⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⢀⣀⠤⠤⠤⣉⠒⢼⠃⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠸⠥⠒⣉⠤⠤⠤⣀⡀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⣠⠊⢁⡤⠖⠤⣄⠀⠙⢆⠀⠘⣄⠠⠒⠄⠀⠠⠒⠄⣠⠃⠀⡰⠋⠀⣠⠤⠲⢤⡈⠑⣄⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⢣⠤⠊⠀⠀⠀⠀⠱⡄⠈⠳⣄⡬⠗⠀⠀⠀⠀⠀⠺⢥⣀⠞⠁⢠⠎⠀⠀⠀⠀⠑⠤⡞⠀⠀⠀⠀⠀
	⠀⠀⢀⡤⠒⢒⡒⠒⠒⠒⠂⠀⠈⠁⠀⠀⠀⠀⠀⠀⠰⠤⠆⠀⠀⠀⠀⠀⠀⠈⠁⠀⠐⠒⠒⠒⢒⡒⠒⢤⡀⠀⠀
	⢀⠔⠋⡤⠚⠁⢉⣉⣐⠋⠀⠀⠉⠉⡩⠚⠀⠀⣀⢀⠀⠀⠀⡀⣀⠀⠀⠒⢍⠉⠁⠀⠀⠈⣒⣉⣉⠉⠓⢤⠙⠦⡀
	⠙⢆⠀⢧⡀⠀⢈⡙⠒⠛⠀⢀⠔⠋⠀⡠⠔⠊⠁⠘⡇⠀⢸⠃⠈⠑⠢⣄⠀⠙⠢⡀⠀⠘⠓⢋⡁⠀⢀⡼⠀⡱⠋
	⠀⠀⠑⢄⣉⡩⠤⠝⠀⠀⢰⠃⠀⡞⠉⢀⣀⠀PYNTACLE ⣀⡀⠉⢳⠀⠘⡆⠀⠀⠫⠤⢍⣉⡠⠊⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢧⠈⠧⡸⠁⠈⢱⠀⠀ ⠀ ⠀⠀⡎⠁⠈⢇⠼⠁⡸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠱⠤⠤⠤⠔⠊⠀⠀ ⠀ ⠀⠀⠑⠢⠄⠤⠤⠞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
				⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀     ⠀⠀⠀⠀⠀⠀  ⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀
	#####################################################################################################
	##       Pyntacle is an open-source software package for network analysis and visualization.       ##
	##       Pyntacle allows users to import, visualize, manipulate, and analyze network data,         ##
	##       and it provides a range of tools for network topology analysis.                           ##
	#####################################################################################################

	''' +  Style.RESET_ALL , add_help=False,  usage=" python3 main.py" + Fore.RED + " command" + Fore.MAGENTA + " [subcommand]" + Fore.CYAN + " parameters"+Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
	parser.add_argument('-v', '--version', action='help', default=argparse.SUPPRESS, help='Show version number and quit')
	subparsers = parser.add_subparsers(dest='command', title="Functions",  metavar= Fore.CYAN + Style.BRIGHT + "The available commands in Pyntacle are:\n" + Style.RESET_ALL)
	parser._optionals.title = 'Optional arguments'

	#########parser_functions##########
	def check_prob(prob):
		try:
			prob = float(prob)
		except ValueError:
			raise argparse.ArgumentTypeError("%r invalid probability value'" % prob)
		if prob > 1.0 or prob < 0.0:
			raise argparse.ArgumentTypeError("%r invalid probability value'" % prob)
		return prob
	###################################


	### LOCAL ###
	local = subparsers.add_parser('local', usage=Fore.GREEN + Style.BRIGHT +'python3 main.py' + Fore.RED +' local ' + Fore.CYAN + '-t {fileType} -i {input_file} [optional parameters] [optional outdir]' + Style.RESET_ALL, help='''Computes metrics of local nature for the whole graph''', 
		description= Fore.YELLOW + '''Measures to be calculated: Degree, Betweenness, Closeness, Radiality, Radiality reach, Clustering Coefficient,  Eccentricity, Eigenvector (Scaled), Pagerank''', formatter_class=argparse.RawDescriptionHelpFormatter)
	local.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	local.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	local.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	local.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	local.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	local.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	local.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (Comma separated)', required=False)
	local.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output (svg, png)', required=False)
	local.add_argument('-c', '--color', action='store', default=False,help='-[optional] Specify the nodes you want to highlight', required=False)
	local.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	local.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	local._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL


	### GLOBAL ###
	glb = subparsers.add_parser('global', usage=Fore.GREEN + Style.BRIGHT +'python3 main.py ' + Fore.RED +'global' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] [optional outdir]' +  Style.RESET_ALL, help='''Computes metrics of global nature for the whole graph''',
		description= Fore.YELLOW + '''Measures to be calculated: Average shortest path length, Median shortest path length, Diameter, Components, Radius, Density, pi, \n\t  Average clustering coefficient, Weighted clustering coefficient, Average degree, Average Closeness, \n\t  Average Eccentricity, Average Radiality, Average Radiality Reach, Completeness Naive, Completeness, Compactness''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	glb.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	glb.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	glb.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	glb.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	glb.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	glb.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	glb.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (Comma separated)', required=False)
	glb.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output (svg, png)', required=False)
	glb.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	glb.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	glb._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL


	### GROUPCENTRALITY ###
	groupcentrality = subparsers.add_parser('groupcentrality',usage=Fore.GREEN + Style.BRIGHT + 'python3 main.py ' + Fore.RED +'groupcentrality ' + Fore.MAGENTA + '{gc-info | gc-finder}' +   Fore.CYAN  + ' -t {fileType} -i {input_file} [optional parameters] [-k {k-size} | -n {node-list}] [optional outdir]' +  Style.RESET_ALL, help='''Computes key player metrics for a specific set of nodes (\'gc-info\') or finds a set of nodes of size `k` that owns the optimal or the best score (\'gc-finder\').''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py groupcentrality gc-info''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {node-list} [optional outdir]\n''' + Style.RESET_ALL +  '''  gc-info : Compute all or a selected group-centrality metric for a selected set of nodes 
		\n''' +  Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py groupcentrality gc-finder''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -k {k-size} [optional outdir]\n''' + Style.RESET_ALL +  '''  gc-finder : Find the optimal or the best set of size \'k\' for a given group-centrality index'''+  Style.RESET_ALL), formatter_class=argparse.RawDescriptionHelpFormatter)
	groupcentrality.add_argument(dest='subcommand', choices=['gc-info', 'gc-finder'], type= str, help='''Select one the subcuntions right after groupcentrality''')
	groupcentrality.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	groupcentrality.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	groupcentrality.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	groupcentrality.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	groupcentrality.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	groupcentrality.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	groupcentrality.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (Comma separated)', required=False)
	subGC = groupcentrality.add_mutually_exclusive_group()
	subGC.add_argument('-n','--nodes', action='store', help='Nodes to select ONLY IN GC-INFO (Comma separated)')
	subGC.add_argument('-k', '--k_size', action='store', help='Number of nodes ONLY IN GC-FINDER (default=2)', default=2)
	groupcentrality.add_argument('-v', '--value', action='store',choices=["min","max","mean"], default="min",help='-[optional] Value to select when all operation are performed or only "closeness" (default="min")', required=False)
	groupcentrality.add_argument('-oper', '--operation', action='store', choices=["all", "degree", "closeness", "betweenness"],default="all", help='-[optional] Possible metrics to be used (default="all")', required=False)
	groupcentrality.add_argument('-a', '--algorithm', action='store', type=str, choices=["brute_force", "greedy", "gradient_descent"],default="brute_force", help='-[optional] Select the algorithm to use when using the GC-FINDER command (default=brute_force)', required=False)
	groupcentrality.add_argument('-p', '--probability', action='store',type=float, help='The probability of accepting a swap of nodes (values between 0 and 1) - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0)', default=0)
	groupcentrality.add_argument('-tol', '--tolerance', action='store',type=float, help='The minimum accepted increase by a two-nodes swap - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0.01)', default=0.01)
	groupcentrality.add_argument('-ms', '--maxsec', action='store',type=int, help='Maximum allowed computation time (seconds) - ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=120)', default=120)
	groupcentrality.add_argument('-np', '--nprocs', action='store',type=int, help='-[optional] Number of process (default=1)', default=1)
	groupcentrality.add_argument('--max-ties', action='store', type=int, default=100, help='-[optional] How many equally-scoring node sets the brute-force report lists (default=100). The reported count of optimal sets is exact even when the list is capped; greedy and gradient_descent ignore this.', required=False)
	groupcentrality.add_argument('--engine', action='store', type=str, choices=["cython", "python"], default="cython", help='-[optional] Metric engine: the compiled kernels (default) or the pure-Python reference implementation. The python engine is single-threaded and ignores -np, and it does not implement brute_force', required=False)
	groupcentrality.add_argument('--seed', action='store', type=int, default=None, help='-[optional] Random seed for greedy / gradient_descent, so a run can be reproduced', required=False)
	groupcentrality.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	groupcentrality.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output (svg, png)', required=False)
	groupcentrality.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	groupcentrality._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	groupcentrality._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL

	### KEYPLAYER ###
	keyplayer = subparsers.add_parser('keyplayer',usage=Fore.GREEN + Style.BRIGHT + 'python3 main.py ' + Fore.RED +'keyplayer ' + Fore.MAGENTA + '{kp-info | kp-finder}' +   Fore.CYAN  + ' -t {fileType} -i {input_file} [optional parameters] [-k {k-size} | -n {node-list}] [optional outdir]'+  Style.RESET_ALL, help='''Computes key player metrics for a specific set of nodes (\'kp-info\') or finds a set of nodes of size `k` that owns the optimal or the best score (\'kp-finder\').'''+ Style.RESET_ALL, 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py keyplayer kp-info''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {node-list} [optional outdir]\n''' + Style.RESET_ALL +  '''  kp-info: Compute individual key-player metrics for a selected set of nodes  
		\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py keyplayer kp-finder''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -k {k-size} [optional outdir]\n''' + Style.RESET_ALL +  '''  kp-finder : Find the best kp-set of size k'''), formatter_class=argparse.RawDescriptionHelpFormatter)
	keyplayer.add_argument(dest='subcommand', choices=['kp-info', 'kp-finder'], help='''Select one the subfunctions right after keyplayer''')
	keyplayer.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	keyplayer.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	keyplayer.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	keyplayer.add_argument('-nh', '--NoHeader', action='store_true', help='''\n\n-[optional] Use this flag if your file doesn\'t have an header''', required=False)
	keyplayer.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	keyplayer.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	keyplayer.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	subKey = keyplayer.add_mutually_exclusive_group()
	subKey.add_argument('-n','--nodes', action='store', help='Nodes to select ONLY IN KP-INFO (Comma separated)')
	subKey.add_argument('-k', '--k_size', action='store', help='Number of nodes ONLY IN KP-FINDER (default=2)', default=2)
	keyplayer.add_argument('-m', '--mdist', action='store', help='-[optional] Number of steps of the m-reach algorithm (default=2)', default=2, required=False)
	keyplayer.add_argument('-oper', '--operation', action='store',choices=["all","F","dF","dR","mreach"],default="all", help='-[optional] Possible types: all | Neg: F, dF | Pos: dR, mreach (default="all")', required=False)
	keyplayer.add_argument('-a', '--algorithm', action='store', type=str, choices=["brute_force", "greedy", "gradient_descent"],default="brute_force", help='-[optional] Select the algorithm to use when using the GC-FINDER command (default=brute_force)', required=False)
	keyplayer.add_argument('-p', '--probability', action='store',type=float, help='ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0)', default=0)
	keyplayer.add_argument('-tol', '--tolerance', action='store',type=float, help='ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=0.01)', default=0.01)
	keyplayer.add_argument('-ms', '--maxsec', action='store',type=int, help='ONLY WHEN USING STOCHASTIC-GRADIENT-DESCENT as algorithm (default=120)', default=120)
	keyplayer.add_argument('-np', '--nprocs', action='store',type=int, help='-[optional] Number of process (default=1)', default=1, required=False)
	keyplayer.add_argument('--max-ties', action='store', type=int, default=100, help='-[optional] How many equally-scoring node sets the brute-force report lists (default=100). The reported count of optimal sets is exact even when the list is capped; greedy and gradient_descent ignore this.', required=False)
	keyplayer.add_argument('--engine', action='store', type=str, choices=["cython", "python"], default="cython", help='-[optional] Metric engine: the compiled kernels (default) or the pure-Python reference implementation. The python engine is single-threaded and ignores -np, and it does not implement brute_force', required=False)
	keyplayer.add_argument('--seed', action='store', type=int, default=None, help='-[optional] Random seed for greedy / gradient_descent, so a run can be reproduced', required=False)
	keyplayer.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	keyplayer.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output (svg, png)', required=False)
	keyplayer.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	keyplayer._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	keyplayer._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL


	### SET ###
	setop = subparsers.add_parser('set',usage=Fore.GREEN + Style.BRIGHT + 'python3 main.py ' + Fore.RED +'set ' + Fore.MAGENTA + '{union | intersection | difference}' +   Fore.CYAN  + ' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]'+  Style.RESET_ALL, help='''Performs set operations ('union', 'intersection', 'difference') between two networks using graph logical operations''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py set union'''+ Fore.CYAN + Style.BRIGHT + ''' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]\n''' + Style.RESET_ALL + '''  union : Return a resulting merged graph of the original two networks, marking the common nodes among them along with their common connecting edges \n\n''' 
			+ Fore.GREEN + Style.BRIGHT + ''' · python3 main.py set intersection''' + Fore.CYAN + Style.BRIGHT +''' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]\n''' + Style.RESET_ALL + '''  intersection : Return only the common nodes and their connecting edges among the two graphs of interest \n\n''' 
			+ Fore.GREEN + Style.BRIGHT + ''' · python3 main.py set difference'''  + Fore.CYAN + Style.BRIGHT + ''' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]\n''' + Style.RESET_ALL + '''  difference : Perform the difference between the two input graphs. NOTE: the difference among graphs is not reciprocal'''), formatter_class=argparse.RawDescriptionHelpFormatter)
	setop.add_argument(dest='subcommand', choices=['union', 'intersection', 'difference'], help='''Select one the subfunctions right after set''')
	setop.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	setop.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	setop.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	setop.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	setop.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	setop.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	setop.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	setop.add_argument('-i2', '--inputFile2', action='store', type=str, help='-[required] Specify the second input file name (Use same format the first input file or use the \'convert\' function if necessary)', required=True)
	setop.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	setop.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output (svg, png)', required=False)
	setop.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	setop._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	setop._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL
	

	### CONVERT ###
	convert = subparsers.add_parser('convert',usage=Fore.GREEN + Style.BRIGHT +'python3 main.py ' + Fore.RED +'convert' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -to {fileType2} -fo {output_name} [optional outdir]' +  Style.RESET_ALL, help='''Converts a network file format to another one ''', 
		description=Fore.RED + Style.BRIGHT +'''\nPossible combinations''' + Fore.CYAN + ''' (-t {fileType} | -to {fileType2})''' + Style.RESET_ALL + ''':\n · AdjMatrix and EdgeList (and viceversa)
	· AdjMatrix and Sif (and viceversa)
	· AdjMatrix and Dot (and viceversa)
	· EdgeList and Sif (and viceversa)
	· EdgeList and Dot (and viceversa)
	· Sif and Dot (and viceversa)''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	convert.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	convert.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	convert.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	convert.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	convert.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	convert.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	convert.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	convert.add_argument('-to', '--typeOutput', action='store', choices=["matrix","edgelist","dot","sif"], help='-[required] Output file type', required=True)
	convert.add_argument('-fo', '--outputName', action='store', help='-[required] Output file name (extension will be automatically assigned)', required=True)
	convert.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output (svg, png)', required=False)
	convert.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	convert._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL

	### COMMUNITIES ### 
	community = subparsers.add_parser('communities',usage=Fore.GREEN + Style.BRIGHT +'python3 main.py ' + Fore.RED +'communities' + Fore.MAGENTA + ' {fastgreedy | infomap | leading-eigenvector | random-walk | percolation}' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} [-nc {NUMBERCOMMUNITIES} | -steps {STEPS}] [optional outdir]' + Style.RESET_ALL, help='''Finds communities within a graph using several community-finding algorithms''', 
		description=textwrap.dedent(Fore.YELLOW + '''Detects communities of tightly connected nodes within a graph by means of different modular decomposition algorithms\n\n''' + Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py communities fastgreedy''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES} [optional outdir]\n\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py communities infomap''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} [optional outdir]\n\n'''
		+ Fore.GREEN + Style.BRIGHT + ''' · python3 main.py communities leading-eigenvector''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES} [optional outdir]\n\n''' + Style.RESET_ALL
		+ Fore.GREEN + Style.BRIGHT + ''' · python3 main.py communities random_walk''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -steps {STEPS} [optional outdir]\n\n''' + Style.RESET_ALL
		+ Fore.GREEN + Style.BRIGHT + ''' · python3 main.py communities percolation''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -k {COMMUNITYSIZE} [optional outdir]\n''' + Style.RESET_ALL,), formatter_class=argparse.RawDescriptionHelpFormatter)
	community.add_argument(dest='subcommand', choices=['fastgreedy','infomap','leading-eigenvector','random-walk','percolation'], help='''Select one the subfunctions right after communities''')
	community.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	community.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	community.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	community.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	community.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	community.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	community.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	community.add_argument('-nc', '--numberCommunities', action='store', default = None, help='ONLY FOR FASTGREEDY Specify the number of clusters around which the modular decomposition algorithm will optimize its module search', required=False)
	community.add_argument('-n', '--minNodes', action='store', help="Filters the resulting communities and keeps only those with a number of vertices equal or greater than this threshold", required=False,default=None)
	community.add_argument('-N', '--maxNodes', action='store', help="Filters the resulting communities and keeps only those with a number of vertices equal or lesser than this threshold", required=False,default=None)
	community.add_argument('-c', '--minComponents', action='store', help="Filters the resulting communities and keeps only those with a number of components equal or greater than this threshold", required=False,default=None)
	community.add_argument('-C', '--maxComponents', action='store', help="Filters the resulting communities and keeps only those with a number of components equal or greater than this threshold", required=False,default=None)
	community.add_argument('-steps', '--steps', action='store', help="ONLY FOR RANDOM-WALK Length of random walks to perform", required=False,default=4)
	community.add_argument('-k', '--communitySize', action='store', help="ONLY FOR PERCOLATION Size of the cliques to be used as building blocks for the community detection", required=False,default=3)
	community.add_argument('-g', '--giant', action='store_true', help=" Considers only the largest component of the input graph and excludes the smaller ones", required=False)
	community.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	community.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	community.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output', required=False)
	community._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	community._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL



	### Extract ###
	extract = subparsers.add_parser('extract',usage=Fore.GREEN + Style.BRIGHT + 'python3 main.py ' + Fore.RED + 'extract' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] [-l | -n | -l -n | -sc] [optional outdir]' + Style.RESET_ALL , help='''Return different components from the graph (suggested to use when the graph is fragmented)''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -l {largest} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-l {largest}] argument in order to extract only the LARGEST component of the graph  
		\n'''  + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {NCOMPONENTS} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-n {NCOMPONENTS}] argument in order to extract the first n components of the graph  
		\n'''  + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -l {largest} -n {NCOMPONENTS} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-l {largest} -n {NCOMPONENTS}] arguments in order to extract the n-th largest component of the graph  
		\n'''  + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -sc {SELECTCOMPONENT} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-sc {SELECTCOMPONENT}] argument used in order to extract the components in which the given node/nodes is/are present  
		\n'''), formatter_class=argparse.RawDescriptionHelpFormatter)
	extract.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	extract.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	extract.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific header (ex. \',\')', required=False)
	extract.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	extract.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	extract.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	extract.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	extract.add_argument('-n','--ncomponents', action='store', help='number of components',default=False)
	extract.add_argument('-l', '--largest', action='store_true', help='Largest component of the graph', default=False)
	extract.add_argument('-sc', '--selectComponent', action='store', help='Node/Nodes of the graph (ex. A,B,C)', default=False)
	extract.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	extract.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	extract.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output', required=False)
	extract.add_argument('-nl', '--nodeList', action='store', help='-[optional] Select the components that contain the given node/nodes (ex. A,B,C)', required=False, default=False)
	extract._optionals.title = "Arguments"

	### Generate ###
	generate = subparsers.add_parser('generate',usage=Fore.GREEN + Style.BRIGHT +'python3 main.py ' + Fore.RED +'generate' + Fore.MAGENTA + ' {erdos-renyi | tree | barabasi | watts-strogatz | lattice}' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] [optional outdir]' + Style.RESET_ALL, help='''Generates a graph using different algorithms given some parameters and outputs the file in the desired format''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py generate erdos-renyi''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {number of nodes} -e {number of edges} -p {probability} -l {loops} [optional outdir]\n\n''' + Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py generate tree''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {number of nodes} -c {children} [optional outdir]\n\n''' + Style.RESET_ALL	+ Fore.GREEN + Style.BRIGHT + ''' · python3 main.py generate barabasi''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {number of nodes} -a {avarage edge} -i {implementation} [optional outdir]\n\n''' + Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py generate watts-strogatz''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -dim {dimesion} -s {size} -nei {nei} -p {probability} -l {loops} -m {multiple}
	[optional outdir]\n\n''' + Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · python3 main.py generate lattice''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -dim {dimension} -nei {nei} -mut {mutual} -circ {circular} [optional outdir]''' + Style.RESET_ALL ), formatter_class=argparse.RawDescriptionHelpFormatter)
	generate.add_argument(dest='subcommand', choices=['erdos-renyi', 'tree', 'barabasi', 'watts-strogatz', 'lattice'], help='''Select one the subfunctions right after generate''')
	generate.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	generate.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	generate.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	generate.add_argument('-n','--numberNodes', action='store', help='Number of vertices of the resulting random graph', default=False)
	generate.add_argument('-e', '--numberEdges', action='store', help='The resulting number of edges', default=False)
	generate.add_argument('-p', '--probability', action='store',type=check_prob, help='The wiring probability to connect any two nodes.', default=False, metavar="")
	generate.add_argument('-l', '--loops', action='store_true', help='Flag to determine wheter the graph should contain loops', default=False)
	generate.add_argument('-c', '--children', action='store', help='The number of children nodes per parent', default=False)
	generate.add_argument('-a', '--averageEdge', action='store', help='Average number of node neighbours for each vertex in the scale-free network.', default=False)
	generate.add_argument('-i', '--implementation', action='store', choices=["bag","psumtree","psumtree_multiple"], help='implementation to use in the Barabasi algorithm', default="psumtree")
	generate.add_argument('-s', '--size', action='store', help='The dimension of a starting lattice (for lattice is a list with the dimensions of the lattice)', default=False)
	generate.add_argument('-m', '--multiple', action='store_true', help='Flag to determine wheter multiple edges are allowed', default=False)
	generate.add_argument('-dim', '--dimension', action='store', help='The dimension of the lattice which the Watts-Strogatz model will be applied to generate the small-world', default=False)
	generate.add_argument('-nei', '--nei', action='store', help='The distance between any two nodes over which these will not be considered connected', default=False)
	generate.add_argument('-mut', '--mutual', action='store_true', help='Flag to determine wheter to create all connections as mutual in case of a directed graph.', default=False)
	generate.add_argument('-circ', '--circular', action='store_true', help='Flag to determine wheter the generated lattice is periodic', default=False)
	generate.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored to the current working directory)', default=False, required=False)
	generate.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output', required=False)
	generate._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	generate._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL

	### Mesoscale ###
	mesoscale = subparsers.add_parser('mesoscale',usage=Fore.GREEN + Style.BRIGHT +'python3 main.py ' + Fore.RED +'mesoscale' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -k {steps} -th {threshold_increment} ' +  Style.RESET_ALL, help='''Computes mesoscale metrics for all nodes of the given input graph''', 
		description=Fore.RED + Style.BRIGHT +'''Metrics:\n''' + Fore.GREEN + Style.BRIGHT + ''' · Generalized Topological Overlap Measure (GTOM):''' + Style.RESET_ALL +  Fore.CYAN + ''' A measure of neighborhood similarity between all pairs of nodes in a graph. GTOM assigns a value in the range [0,1], this occurs when the neighborhoods of two nodes are identical or one is a subset of the other.\n\n'''  + Fore.GREEN + Style.BRIGHT + ''' · Topological Importance (TI): ''' + Style.RESET_ALL +  Fore.CYAN + '''TI of a node measures its influence in a network through k-step structural propagation. It is computed as the row sum of the k-th power of the edge effect matrix, capturing indirect interactions up to path length k.\n\n'''  + Fore.GREEN + Style.BRIGHT + ''' · Weighted Topological Importance (WI):''' + Style.RESET_ALL +  Fore.CYAN + ''' similar to TI it measures a node's influence in a network by accounting for both the strength and reach of its interactions.\n\n'''  + Fore.GREEN + Style.BRIGHT + ''' · Species Topological Overlap (STO):''' + Style.RESET_ALL +  Fore.CYAN + ''' quantifies pairwise structural similarity based on shared 1-step effects, extended to kk-step propagation. A threshold θθ is applied to filter out weak overlaps.''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	mesoscale.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	mesoscale.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	mesoscale.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific separator (ex. \'\\t\')', required=False)
	mesoscale.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	mesoscale.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	mesoscale.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	mesoscale.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	# mesoscale.add_argument('-n', '--nodes', action='store', help='-[optional] Nodes to select. If not specified, the metrics are computed for all nodes', required=False, default=None)
	mesoscale.add_argument('-k', '--kSteps', action='store', type=int, help='-[optional] Maximum effects length considered. Default value is 3.', required=False, default=3)
	mesoscale.add_argument('-th', '--threshold', action='store', type=float, help='-[optional] Threshold that will be used to compute TO. TO will not be computed if no threshold is selected', required=False, default=0.)
	# mesoscale.add_argument('-thrInc', '--thrInc', action='store', help='-[optional] Increment of threshold value from 0 to 1. Default value is 0.1.', required=False, default=0.1)
	mesoscale.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	mesoscale.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	mesoscale.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output', required=False)
	mesoscale.add_argument('-v', '--verbose', action='store_true', help='-[optional] Use this flag to recive prints of partial results of the measures.', required=False)

	mesoscale._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL


 	### Percolation ###
	percolation = subparsers.add_parser('percolation',usage=Fore.GREEN + Style.BRIGHT +'python3 main.py ' + Fore.RED +'percolation' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -P {global infectivity} -tau {recovery time τ} -tauDist {recovery time distribution} -pth {maximum local threshold} -n {seed node/s} -dist {distribution}' +  Style.RESET_ALL, help='''Computes percolation metrics for all nodes of the given input graph''', 
		description=Fore.RED + Style.BRIGHT + '''Percolation dynamics:\n\n''' + Fore.GREEN + Style.BRIGHT + ''' · Local edge thresholds p_th,ij:''' + Style.RESET_ALL + Fore.CYAN +  ''' for each edge (i,j) a local threshold p_th,ij is drawn in [0, p_thMax] from the chosen distribution.\n''' + Fore.GREEN + Style.BRIGHT + '''\n · Global percolation probability P*:''' + Style.RESET_ALL + Fore.CYAN + ''' controls how many edges become "open". An edge (i,j) can transmit only if\n''' + '''   P* ≥ p_th,ij   →   A*_ij = 1,   otherwise A*_ij = 0.\n''' + Fore.GREEN + Style.BRIGHT + '''\n · Spreading from a seed node:''' + Style.RESET_ALL + Fore.CYAN + ''' starting from the seed s at t = 0, activity spreads along open edges. The active set evolves as\n''' + '''   S_{t+1} = N_open(S_t) \\ R_t, ''' + '''where N_open(S_t) are neighbors reachable through open edges and R_t are recovered nodes.\n''' + Fore.GREEN + Style.BRIGHT + '''\n · Recovery time τ:''' + Style.RESET_ALL + Fore.CYAN + ''' a node activated at time t stays active for τ steps and then recovers (it no longer transmits).\n''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	percolation.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	percolation.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	percolation.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Use this flag if your file has a specific separator (ex. \'\\t\')', required=False)
	percolation.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	percolation.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	percolation.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	percolation.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	percolation.add_argument('-n', '--nodes', action='store', help='-[optional] ID of the seed node where the process starts. If not provided, a random node in the graph is chosen.', required=False, default=None)
	percolation.add_argument('-P', '--PrInf', action='store', help='-[optional] Global infectivity / Occupation probability (0–1). Higher P* → easier spreading / percolation. Default value is 0.5.', required=False, default=0.5)
	percolation.add_argument('-tau', '--tau', action='store', help='-[optional] Recovery time τ (in simulation steps). A node can transmit for τ steps after activation, then becomes recovered. Must be > 0. Default: 4.', required=False, default=4)
	percolation.add_argument('-tauDist', '--tauDistribution', choices=['fixed', 'uniform', 'normal', 'bimodal'], action='store', help='-[optional] Distribution used for recovery times τ. "fixed": single global τ for all nodes (default). "uniform"/"normal"/"bimodal": interpret -tau as τ_max and draw per-node τ_i in (0, τ_max] from the chosen distribution.', required=False, default='fixed')
	percolation.add_argument('-tauFile', '--tauFile', action='store', help=('-[optional] TSV file with fixed per-node recovery times. Must contain two ''columns: "Nodes" and "Recovery_time". Node labels in "Nodes" must match. When provided, these τ_i values ''override -tau and -tauDist.'), required=False, default=None)
	percolation.add_argument('-pth', '--pthMax', action='store', help='-[optional] Maximum local threshold p_th in [0,1]. Each edge (i,j) gets a local threshold p_th,ij drawn in [0, p_thMax]; the edge can transmit only if P* >= p_th,ij. Default: 1.0.', required=False, default=1)
	percolation.add_argument('-dist', '--pthDistribution', choices=['uniform', 'normal', 'bimodal'], action='store', help='-[optional] Distribution used to sample local thresholds p_th,ij in [0, p_thMax]. "uniform": all values equally likely; "normal": thresholds cluster around a central value; "bimodal": two groups of edges with low and high thresholds. Default: uniform.', required=False, default='uniform')
	percolation.add_argument('-mxs', '--maxSteps', action='store', type=int, help='-[optional] Maximum number of simulation steps. Default: number of nodes in the graph.', required=False, default=None)
	snapshot_group = percolation.add_mutually_exclusive_group()
	snapshot_group.add_argument("--snapshotInfected", type=int, default=None, help=" -[optional] If set, take a snapshot when the number of *currently infected* nodes reaches this value. The TSV report will include node states at that time.", required=False )
	snapshot_group.add_argument("--snapshotNode", type=str, default=None, help="-[optional] If set, take a snapshot at the time when this node becomes infected. Can be a node label or a node index (0-based).", required=False )
	percolation.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written (matches old Pyntacle no-plot semantics)', required=False)
	percolation.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same direcotry as the input file)', required=False)
	percolation.add_argument('-f', '--format', action='store', type=str, default="svg", help='-[optional] Specify the format of the image output', required=False)
	percolation.add_argument('-v', '--verbose', action='store_true', help='-[optional] Use this flag to recive prints of partial results of the measures.', required=False)

	return parser