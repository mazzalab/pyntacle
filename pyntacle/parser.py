import argparse
import textwrap

import os
from importlib.metadata import PackageNotFoundError, version

try:
    from colorama import Fore, Style
except Exception:
    # the parser must import without colorama too
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = _NoColor()

# no ANSI colours when the documentation is being built
if os.environ.get("PYNTACLE_DOCS", "0") == "1":
    class _NoColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = _NoColor()


def _number(kind, test, text):
	def check(value):
		try:
			x = kind(value)
		except ValueError:
			raise argparse.ArgumentTypeError("{!r} is not {}".format(value, text))
		if not test(x):
			raise argparse.ArgumentTypeError("{!r} is not {}".format(value, text))
		return x
	# the documentation's Type column reads this name
	check.__name__ = kind.__name__
	return check


_pos_int = _number(int, lambda x: x >= 1, "a positive integer")
_nonneg_int = _number(int, lambda x: x >= 0, "a non-negative integer")
_fraction = _number(float, lambda x: 0 < x < 1, "a number between 0 and 1")
_stars_beta = _number(float, lambda x: 0 < x < 0.5, "a number between 0 and 0.5")
_unit = _number(float, lambda x: 0 <= x <= 1, "a number between 0 and 1")
_pos_float = _number(float, lambda x: x > 0, "a positive number")
_nonneg_float = _number(float, lambda x: x >= 0, "a non-negative number")
_clique = _number(int, lambda x: x >= 2, "an integer of at least 2")
_seed = _number(int, lambda x: 0 <= x < 2**32, "an integer between 0 and 2**32 - 1")

# image formats the figure writers (cairo and matplotlib) both handle
FORMATS = ["svg", "png", "pdf", "ps", "eps"]


def _dims(value):
	"""Lattice sides as comma-separated positive integers (ex. 4,4)."""
	parts = [p.strip() for p in value.split(",")]
	if not parts or not all(p.isdigit() and int(p) >= 1 for p in parts):
		raise argparse.ArgumentTypeError("{!r} is not a comma-separated list of positive integers".format(value))
	return [int(p) for p in parts]


_dims.__name__ = "int list"


def _prevalence(value):
	return "auto" if value == "auto" else _number(float, lambda x: 0 < x <= 1, "'auto' or a number in (0, 1]")(value)


def _installed_version():
	try:
		return version("pyntacle")
	except PackageNotFoundError:
		return "(not installed)"


def create_parser() -> argparse.ArgumentParser:

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

	''' +  Style.RESET_ALL , add_help=False, prog="pyntacle", usage="pyntacle" + Fore.RED + " command" + Fore.MAGENTA + " [subcommand]" + Fore.CYAN + " parameters"+Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
	parser.add_argument('-v', '--version', action='version', version='Pyntacle ' + _installed_version(), help='Show version number and quit')
	subparsers = parser.add_subparsers(dest='command', prog='pyntacle', title="Functions",  metavar= Fore.CYAN + Style.BRIGHT + "The available commands in Pyntacle are:\n" + Style.RESET_ALL)
	parser._optionals.title = 'Optional arguments'

	def check_prob(prob):
		try:
			prob = float(prob)
		except ValueError:
			raise argparse.ArgumentTypeError("%r is not a probability between 0 and 1" % prob)
		if prob > 1.0 or prob < 0.0:
			raise argparse.ArgumentTypeError("%r is not a probability between 0 and 1" % prob)
		return prob


	# ---- local ----
	local = subparsers.add_parser('local', usage=Fore.GREEN + Style.BRIGHT +'pyntacle' + Fore.RED +' local ' + Fore.CYAN + '-t {fileType} -i {input_file} [optional parameters] [optional outdir]' + Style.RESET_ALL, help='''Computes metrics of local nature for the whole graph''', 
		description= Fore.YELLOW + '''Measures to be calculated: Degree, Betweenness, Closeness, Radiality, Radiality reach, Clustering Coefficient,  Eccentricity, Eigenvector (Scaled), Pagerank''', formatter_class=argparse.RawDescriptionHelpFormatter)
	local.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	local.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	local.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	local.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	local.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	local.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	local.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	local.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	local.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (Comma separated)', required=False)
	local.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	local.add_argument('-c', '--color', action='store', default=False,help='-[optional] Specify the nodes you want to highlight', required=False)
	local.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	local.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	local._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL


	# ---- global ----
	glb = subparsers.add_parser('global', usage=Fore.GREEN + Style.BRIGHT +'pyntacle ' + Fore.RED +'global' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] [optional outdir]' +  Style.RESET_ALL, help='''Computes metrics of global nature for the whole graph''',
		description= Fore.YELLOW + '''Measures to be calculated: Average shortest path length, Median shortest path length, Diameter, Components, Radius, Density, pi, \n\t  Average clustering coefficient, Global clustering coefficient, Average degree, Average Closeness, \n\t  Average Eccentricity, Average Radiality, Average Radiality Reach, Completeness Naive, Completeness, Compactness''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	glb.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	glb.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	glb.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	glb.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	glb.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	glb.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	glb.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	glb.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	glb.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (Comma separated)', required=False)
	glb.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	glb.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	glb.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	glb._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL


	# ---- groupcentrality ----
	groupcentrality = subparsers.add_parser('groupcentrality',usage=Fore.GREEN + Style.BRIGHT + 'pyntacle ' + Fore.RED +'groupcentrality ' + Fore.MAGENTA + '{gc-info | gc-finder}' +   Fore.CYAN  + ' -t {fileType} -i {input_file} [optional parameters] [-k {k-size} | -n {node-list}] [optional outdir]' +  Style.RESET_ALL, help='''Computes key player metrics for a specific set of nodes (\'gc-info\') or finds a set of nodes of size `k` that owns the optimal or the best score (\'gc-finder\').''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle groupcentrality gc-info''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {node-list} [optional outdir]\n''' + Style.RESET_ALL +  '''  gc-info : Compute all or a selected group-centrality metric for a selected set of nodes 
		\n''' +  Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · pyntacle groupcentrality gc-finder''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -k {k-size} [optional outdir]\n''' + Style.RESET_ALL +  '''  gc-finder : Find the optimal or the best set of size \'k\' for a given group-centrality index'''+  Style.RESET_ALL), formatter_class=argparse.RawDescriptionHelpFormatter)
	groupcentrality.add_argument(dest='subcommand', choices=['gc-info', 'gc-finder'], type= str, help='''Subcommand to run, right after groupcentrality''')
	groupcentrality.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	groupcentrality.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	groupcentrality.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	groupcentrality.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	groupcentrality.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	groupcentrality.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	groupcentrality.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	groupcentrality.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	groupcentrality.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (Comma separated)', required=False)
	subGC = groupcentrality.add_mutually_exclusive_group()
	subGC.add_argument('-n','--nodes', action='store', help='Nodes to select ONLY IN GC-INFO (Comma separated)')
	subGC.add_argument('-k', '--k_size', action='store', type=_pos_int, help='Size of the node set to search, gc-finder only (default=2)', default=2)
	groupcentrality.add_argument('-v', '--value', action='store',choices=["min","max","mean"], default="min",help='-[optional] Value to select when all operation are performed or only "closeness" (default="min")', required=False)
	groupcentrality.add_argument('-oper', '--operation', action='store', choices=["all", "degree", "closeness", "betweenness"],default="all", help='-[optional] Possible metrics to be used (default="all")', required=False)
	groupcentrality.add_argument('-a', '--algorithm', action='store', type=str, choices=["brute_force", "greedy", "gradient_descent"],default="brute_force", help='-[optional] Search algorithm of gc-finder (default=brute_force)', required=False)
	groupcentrality.add_argument('-p', '--probability', action='store', type=_unit, help='gradient_descent only: probability of accepting a swap that lowers the score (default=0)', default=0)
	groupcentrality.add_argument('-tol', '--tolerance', action='store', type=_nonneg_float, help='gradient_descent only: the search stops at the first swap that raises the score by no more than this (default=0.01)', default=0.01)
	groupcentrality.add_argument('-ms', '--maxsec', action='store', type=_pos_int, help='gradient_descent only: time limit of each search, in seconds (default=120)', default=120)
	groupcentrality.add_argument('-np', '--nprocs', action='store', type=_pos_int, help='-[optional] Threads of the compiled kernels (default=1)', default=1)
	groupcentrality.add_argument('--max-ties', action='store', type=_pos_int, default=100, help='-[optional] How many equally-scoring node sets the brute-force report lists (default=100). The reported count of optimal sets is exact even when the list is capped; greedy and gradient_descent ignore this.', required=False)
	groupcentrality.add_argument('--engine', action='store', type=str, choices=["cython", "python"], default="cython", help='-[optional] Metric engine: the compiled kernels (default) or the pure-Python reference implementation. The python engine is single-threaded and ignores -np, and it does not implement brute_force', required=False)
	groupcentrality.add_argument('--seed', action='store', type=_seed, default=None, help='-[optional] Random seed for greedy / gradient_descent, so a run can be reproduced', required=False)
	groupcentrality.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	groupcentrality.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	groupcentrality.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	groupcentrality._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	groupcentrality._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL

	# ---- keyplayer ----
	keyplayer = subparsers.add_parser('keyplayer',usage=Fore.GREEN + Style.BRIGHT + 'pyntacle ' + Fore.RED +'keyplayer ' + Fore.MAGENTA + '{kp-info | kp-finder}' +   Fore.CYAN  + ' -t {fileType} -i {input_file} [optional parameters] [-k {k-size} | -n {node-list}] [optional outdir]'+  Style.RESET_ALL, help='''Computes key player metrics for a specific set of nodes (\'kp-info\') or finds a set of nodes of size `k` that owns the optimal or the best score (\'kp-finder\').'''+ Style.RESET_ALL, 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle keyplayer kp-info''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {node-list} [optional outdir]\n''' + Style.RESET_ALL +  '''  kp-info: Compute individual key-player metrics for a selected set of nodes  
		\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle keyplayer kp-finder''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -k {k-size} [optional outdir]\n''' + Style.RESET_ALL +  '''  kp-finder : Find the best kp-set of size k'''), formatter_class=argparse.RawDescriptionHelpFormatter)
	keyplayer.add_argument(dest='subcommand', choices=['kp-info', 'kp-finder'], help='''Subcommand to run, right after keyplayer''')
	keyplayer.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	keyplayer.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	keyplayer.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	keyplayer.add_argument('-nh', '--NoHeader', action='store_true', help='''\n\n-[optional] Use this flag if your file doesn\'t have an header''', required=False)
	keyplayer.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	keyplayer.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	keyplayer.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	keyplayer.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	keyplayer.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	subKey = keyplayer.add_mutually_exclusive_group()
	subKey.add_argument('-n','--nodes', action='store', help='Nodes to select ONLY IN KP-INFO (Comma separated)')
	subKey.add_argument('-k', '--k_size', action='store', type=_pos_int, help='Size of the node set to search, kp-finder only (default=2)', default=2)
	keyplayer.add_argument('-m', '--mdist', action='store', type=_pos_int, help='-[optional] Number of steps of the m-reach algorithm (default=2)', default=2, required=False)
	keyplayer.add_argument('-oper', '--operation', action='store',choices=["all","F","dF","dR","mreach"],default="all", help='-[optional] Possible types: all | Neg: F, dF | Pos: dR, mreach (default="all")', required=False)
	keyplayer.add_argument('-a', '--algorithm', action='store', type=str, choices=["brute_force", "greedy", "gradient_descent"],default="brute_force", help='-[optional] Search algorithm of kp-finder (default=brute_force)', required=False)
	keyplayer.add_argument('-p', '--probability', action='store', type=_unit, help='gradient_descent only: probability of accepting a swap that lowers the score (default=0)', default=0)
	keyplayer.add_argument('-tol', '--tolerance', action='store', type=_nonneg_float, help='gradient_descent only: the search stops at the first swap that raises the score by no more than this (default=0.01)', default=0.01)
	keyplayer.add_argument('-ms', '--maxsec', action='store', type=_pos_int, help='gradient_descent only: time limit of each search, in seconds (default=120)', default=120)
	keyplayer.add_argument('-np', '--nprocs', action='store', type=_pos_int, help='-[optional] Threads of the compiled kernels (default=1)', default=1, required=False)
	keyplayer.add_argument('--max-ties', action='store', type=_pos_int, default=100, help='-[optional] How many equally-scoring node sets the brute-force report lists (default=100). The reported count of optimal sets is exact even when the list is capped; greedy and gradient_descent ignore this.', required=False)
	keyplayer.add_argument('--engine', action='store', type=str, choices=["cython", "python"], default="cython", help='-[optional] Metric engine: the compiled kernels (default) or the pure-Python reference implementation. The python engine is single-threaded and ignores -np, and it does not implement brute_force', required=False)
	keyplayer.add_argument('--seed', action='store', type=_seed, default=None, help='-[optional] Random seed for greedy / gradient_descent, so a run can be reproduced', required=False)
	keyplayer.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	keyplayer.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	keyplayer.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	keyplayer._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	keyplayer._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL


	# ---- set ----
	setop = subparsers.add_parser('set',usage=Fore.GREEN + Style.BRIGHT + 'pyntacle ' + Fore.RED +'set ' + Fore.MAGENTA + '{union | intersection | difference}' +   Fore.CYAN  + ' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]'+  Style.RESET_ALL, help='''Performs set operations ('union', 'intersection', 'difference') between two networks using graph logical operations''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle set union'''+ Fore.CYAN + Style.BRIGHT + ''' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]\n''' + Style.RESET_ALL + '''  union : Return a resulting merged graph of the original two networks, marking the common nodes among them along with their common connecting edges \n\n''' 
			+ Fore.GREEN + Style.BRIGHT + ''' · pyntacle set intersection''' + Fore.CYAN + Style.BRIGHT +''' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]\n''' + Style.RESET_ALL + '''  intersection : Return only the common nodes and their connecting edges among the two graphs of interest \n\n''' 
			+ Fore.GREEN + Style.BRIGHT + ''' · pyntacle set difference'''  + Fore.CYAN + Style.BRIGHT + ''' -t {fileType} -i {input_file} [optional parameters] -i2 {input_file2} [optional outdir]\n''' + Style.RESET_ALL + '''  difference : Perform the difference between the two input graphs. NOTE: the difference among graphs is not reciprocal'''), formatter_class=argparse.RawDescriptionHelpFormatter)
	setop.add_argument(dest='subcommand', choices=['union', 'intersection', 'difference'], help='''Subcommand to run, right after set''')
	setop.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	setop.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	setop.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	setop.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	setop.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	setop.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	setop.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	setop.add_argument('-i2', '--inputFile2', action='store', type=str, help='-[required] Second network, in the same format as the first: -t, -s, -nh and -w apply to both (use \'convert\' if they differ)', required=True)
	setop.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	setop.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	setop.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	setop._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	setop._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL
	

	# ---- convert ----
	convert = subparsers.add_parser('convert',usage=Fore.GREEN + Style.BRIGHT +'pyntacle ' + Fore.RED +'convert' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -to {fileType2} -fo {output_name} [optional outdir]' +  Style.RESET_ALL, help='''Converts a network file format to another one ''', 
		description=Fore.RED + Style.BRIGHT +'''\nPossible combinations''' + Fore.CYAN + ''' (-t {fileType} | -to {fileType2})''' + Style.RESET_ALL + ''':\n · AdjMatrix and EdgeList (and viceversa)
	· AdjMatrix and Sif (and viceversa)
	· AdjMatrix and Dot (and viceversa)
	· EdgeList and Sif (and viceversa)
	· EdgeList and Dot (and viceversa)
	· Sif and Dot (and viceversa)''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	convert.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	convert.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	convert.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	convert.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	convert.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	convert.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	convert.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	convert.add_argument('-to', '--typeOutput', action='store', choices=["matrix","edgelist","dot","sif"], help='-[required] Output file type', required=True)
	convert.add_argument('-fo', '--outputName', action='store', help='-[required] Output file name (extension will be automatically assigned)', required=True)
	convert.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	convert._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL

	# ---- communities ----
	community = subparsers.add_parser('communities',usage=Fore.GREEN + Style.BRIGHT +'pyntacle ' + Fore.RED +'communities' + Fore.MAGENTA + ' {fastgreedy | infomap | leading-eigenvector | random-walk | percolation}' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} [-nc {NUMBERCOMMUNITIES} | -steps {STEPS}] [optional outdir]' + Style.RESET_ALL, help='''Finds communities within a graph using several community-finding algorithms''', 
		description=textwrap.dedent(Fore.YELLOW + '''Detects communities of tightly connected nodes within a graph by means of different modular decomposition algorithms\n\n''' + Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle communities fastgreedy''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES} [optional outdir]\n\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle communities infomap''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} [optional outdir]\n\n'''
		+ Fore.GREEN + Style.BRIGHT + ''' · pyntacle communities leading-eigenvector''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -nc {NUMBERCOMMUNITIES} [optional outdir]\n\n''' + Style.RESET_ALL
		+ Fore.GREEN + Style.BRIGHT + ''' · pyntacle communities random_walk''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -n {MINNODES} -N {MAXNODES} -c {MINCOMPONENTS} -C {MAXCOMPONENTS} -steps {STEPS} [optional outdir]\n\n''' + Style.RESET_ALL
		+ Fore.GREEN + Style.BRIGHT + ''' · pyntacle communities percolation''' +  Fore.CYAN  + ''' -t {fileType} -i {input_file} [optional parameters] -k {COMMUNITYSIZE} [optional outdir]\n''' + Style.RESET_ALL,), formatter_class=argparse.RawDescriptionHelpFormatter)
	community.add_argument(dest='subcommand', choices=['fastgreedy','infomap','leading-eigenvector','random-walk','percolation'], help='''Subcommand to run, right after communities''')
	community.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	community.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	community.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	community.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	community.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	community.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	community.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	community.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	community.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	community.add_argument('-nc', '--numberCommunities', action='store', type=_pos_int, default=None, help='fastgreedy, leading-eigenvector, random-walk: number of communities (default: the split with the highest modularity)', required=False)
	community.add_argument('-n', '--minNodes', action='store', type=_pos_int, help="Filters the resulting communities and keeps only those with a number of vertices equal or greater than this threshold", required=False,default=None)
	community.add_argument('-N', '--maxNodes', action='store', type=_pos_int, help="Filters the resulting communities and keeps only those with a number of vertices equal or lesser than this threshold", required=False,default=None)
	community.add_argument('-c', '--minComponents', action='store', type=_pos_int, help="Filters the resulting communities and keeps only those with a number of components equal or greater than this threshold", required=False,default=None)
	community.add_argument('-C', '--maxComponents', action='store', type=_pos_int, help="Filters the resulting communities and keeps only those with a number of components equal or lesser than this threshold", required=False,default=None)
	community.add_argument('-steps', '--steps', action='store', type=_pos_int, help="ONLY FOR RANDOM-WALK Length of random walks to perform", required=False,default=4)
	community.add_argument('-k', '--communitySize', action='store', type=_clique, help="ONLY FOR PERCOLATION Size of the cliques to be used as building blocks for the community detection", required=False,default=3)
	community.add_argument('-g', '--giant', action='store_true', help=" Considers only the largest component of the input graph and excludes the smaller ones", required=False)
	community.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	community.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	community.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	community._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	community._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL



	# ---- extract ----
	extract = subparsers.add_parser('extract',usage=Fore.GREEN + Style.BRIGHT + 'pyntacle ' + Fore.RED + 'extract' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] [-l | -l -n N | -n N | -sc N | -nl NODES] [optional outdir]' + Style.RESET_ALL , help='''Return different components from the graph (suggested to use when the graph is fragmented)''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -l {largest} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-l {largest}] argument in order to extract only the LARGEST component of the graph  
		\n'''  + Fore.GREEN + Style.BRIGHT + ''' · pyntacle extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -n {NCOMPONENTS} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-n {NCOMPONENTS}] argument in order to extract the first n components of the graph  
		\n'''  + Fore.GREEN + Style.BRIGHT + ''' · pyntacle extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -l {largest} -n {NCOMPONENTS} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-l {largest} -n {NCOMPONENTS}] arguments in order to extract the n-th largest component of the graph  
		\n'''  + Fore.GREEN + Style.BRIGHT + ''' · pyntacle extract''' +  Fore.CYAN + ''' -t {fileType} -i {input_file} [optional parameters] -sc {SELECTCOMPONENT} [optional outdir]\n''' + Style.RESET_ALL +  '''   [-sc {SELECTCOMPONENT}] argument used in order to extract the components in which the given node/nodes is/are present  
		\n'''), formatter_class=argparse.RawDescriptionHelpFormatter)
	extract.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	extract.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	extract.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	extract.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	extract.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	extract.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	extract.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	extract.add_argument('-n','--ncomponents', action='store', type=_pos_int, help='-[optional] With -l: keep the N largest components. Alone: drop the N smallest components',default=False)
	extract.add_argument('-l', '--largest', action='store_true', help='-[optional] Keep the largest component (with -n, the N largest)', default=False)
	extract.add_argument('-sc', '--selectComponent', action='store', type=_pos_int, help='-[optional] Keep the N-th largest component (1 = the largest)', default=False)
	extract.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	extract.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	extract.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	extract.add_argument('-nl', '--nodeList', action='store', help='-[optional] Select the components that contain the given node/nodes (ex. A,B,C)', required=False, default=False)
	extract._optionals.title = "Arguments"

	# ---- generate ----
	generate = subparsers.add_parser('generate',usage=Fore.GREEN + Style.BRIGHT +'pyntacle ' + Fore.RED +'generate' + Fore.MAGENTA + ' {erdos-renyi | tree | barabasi | watts-strogatz | lattice}' + Fore.CYAN + ' -t {fileType} [model parameters] [-o outdir]' + Style.RESET_ALL, help='''Generates an undirected network from a random or regular model and writes it in the chosen format''', 
		description=textwrap.dedent(Fore.RED + Style.BRIGHT +'''Specific usage:\n''' + Fore.GREEN + Style.BRIGHT + ''' · pyntacle generate erdos-renyi''' +  Fore.CYAN + ''' -t {fileType} -n {nodes} (-e {edges} | -p {probability}) [-l]\n\n''' + Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · pyntacle generate tree''' +  Fore.CYAN  + ''' -t {fileType} -n {nodes} -c {children}\n\n''' + Style.RESET_ALL	+ Fore.GREEN + Style.BRIGHT + ''' · pyntacle generate barabasi''' +  Fore.CYAN + ''' -t {fileType} -n {nodes} -a {edges per new node} [-i {implementation}]\n\n''' + Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · pyntacle generate watts-strogatz''' +  Fore.CYAN + ''' -t {fileType} -s {size} -nei {nei} -p {probability} [-dim {dimensions}] [-l] [-m]\n\n''' + Style.RESET_ALL + Fore.GREEN + Style.BRIGHT + ''' · pyntacle generate lattice''' +  Fore.CYAN + ''' -t {fileType} -dim {size per dimension, ex. 4,4} [-nei {nei}] [-circ]\n\n''' + Style.RESET_ALL + '''The file is named after the model and its size, ex. erdos_renyi_n100_e250.tsv.''' ), formatter_class=argparse.RawDescriptionHelpFormatter)
	generate.add_argument(dest='subcommand', choices=['erdos-renyi', 'tree', 'barabasi', 'watts-strogatz', 'lattice'], help='''Subcommand to run, right after generate''')
	generate.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] Format of the network file to write', required=True)
	generate.add_argument('-n','--numberNodes', action='store', type=_pos_int, help='erdos-renyi, tree, barabasi: number of nodes', default=None)
	generate.add_argument('-e', '--numberEdges', action='store', type=_nonneg_int, help='erdos-renyi: number of edges (or give -p)', default=None)
	generate.add_argument('-p', '--probability', action='store',type=check_prob, help='erdos-renyi: probability of an edge between any two nodes (or give -e); watts-strogatz: probability of rewiring each edge', default=None, metavar="")
	generate.add_argument('-l', '--loops', action='store_true', help='erdos-renyi, watts-strogatz: allow self-loops', default=False)
	generate.add_argument('-c', '--children', action='store', type=_pos_int, help='tree: children of each node', default=None)
	generate.add_argument('-a', '--averageEdge', action='store', type=_pos_int, help='barabasi: edges each new node brings to the network', default=None)
	generate.add_argument('-i', '--implementation', action='store', choices=["bag","psumtree","psumtree_multiple"], help='barabasi: igraph implementation of preferential attachment (default psumtree)', default="psumtree")
	generate.add_argument('-s', '--size', action='store', type=_pos_int, help='watts-strogatz: nodes along each dimension of the starting lattice', default=None)
	generate.add_argument('-m', '--multiple', action='store_true', help='watts-strogatz: allow parallel edges after rewiring', default=False)
	generate.add_argument('-dim', '--dimension', action='store', type=_dims, help='watts-strogatz: dimensions of the starting lattice (default 1, a ring); lattice: nodes along each dimension, comma-separated (ex. 4,4)', default=None)
	generate.add_argument('-nei', '--nei', action='store', type=_pos_int, help='watts-strogatz, lattice: nodes up to this many steps apart are connected (lattice default 1)', default=None)
	generate.add_argument('-circ', '--circular', action='store_true', help='lattice: join the opposite borders (periodic lattice)', default=False)
	generate.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Where to write the network (default: the current working directory)', required=False)
	generate._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	generate._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL

	# ---- mesoscale ----
	mesoscale = subparsers.add_parser('mesoscale',usage=Fore.GREEN + Style.BRIGHT +'pyntacle ' + Fore.RED +'mesoscale' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -k {steps} -th {threshold_increment} ' +  Style.RESET_ALL, help='''Computes mesoscale metrics for all nodes of the given input graph''', 
		description=Fore.RED + Style.BRIGHT +'''Metrics:\n''' + Fore.GREEN + Style.BRIGHT + ''' · Generalized Topological Overlap Measure (GTOM):''' + Style.RESET_ALL +  Fore.CYAN + ''' A measure of neighborhood similarity between all pairs of nodes in a graph. GTOM assigns a value in the range [0,1], this occurs when the neighborhoods of two nodes are identical or one is a subset of the other.\n\n'''  + Fore.GREEN + Style.BRIGHT + ''' · Topological Importance (TI): ''' + Style.RESET_ALL +  Fore.CYAN + '''TI of a node measures its influence in a network through k-step structural propagation. It is computed as the row sum of the k-th power of the edge effect matrix, capturing indirect interactions up to path length k.\n\n'''  + Fore.GREEN + Style.BRIGHT + ''' · Weighted Topological Importance (WI):''' + Style.RESET_ALL +  Fore.CYAN + ''' similar to TI it measures a node's influence in a network by accounting for both the strength and reach of its interactions.\n\n'''  + Fore.GREEN + Style.BRIGHT + ''' · Species Topological Overlap (STO):''' + Style.RESET_ALL +  Fore.CYAN + ''' quantifies pairwise structural similarity based on shared 1-step effects, extended to kk-step propagation. A threshold θθ is applied to filter out weak overlaps.''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	mesoscale.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	mesoscale.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	mesoscale.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	mesoscale.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	mesoscale.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	mesoscale.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	mesoscale.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	mesoscale.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	mesoscale.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	mesoscale.add_argument('-k', '--kSteps', action='store', type=_pos_int, help='-[optional] Maximum effects length considered. Default value is 3.', required=False, default=3)
	mesoscale.add_argument('-th', '--threshold', action='store', type=_nonneg_float, help='-[optional] Threshold that will be used to compute TO. TO will not be computed if no threshold is selected', required=False, default=0.)
	mesoscale.add_argument('--no-plot', action='store_true', help='-[optional] Skip SVG/PNG figure and interactive HTML report generation; only the TSV report is written', required=False)
	mesoscale.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	mesoscale.add_argument('-f', '--format', action='store', type=str, choices=FORMATS, default="svg", help='-[optional] Image format of the figure', required=False)
	mesoscale.add_argument('-v', '--verbose', action='store_true', help='-[optional] Use this flag to receive prints of partial results of the measures.', required=False)

	mesoscale._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL


	# ---- percolation ----
	percolation = subparsers.add_parser('percolation',usage=Fore.GREEN + Style.BRIGHT +'pyntacle ' + Fore.RED +'percolation' + Fore.CYAN + ' -t {fileType} -i {input_file} [optional parameters] -P {global infectivity} -tau {recovery time τ} -tauDist {recovery time distribution} -pth {maximum local threshold} -n {seed node/s} -dist {distribution}' +  Style.RESET_ALL, help='''Computes percolation metrics for all nodes of the given input graph''', 
		description=Fore.RED + Style.BRIGHT + '''Percolation dynamics:\n\n''' + Fore.GREEN + Style.BRIGHT + ''' · Local edge thresholds p_th,ij:''' + Style.RESET_ALL + Fore.CYAN +  ''' for each edge (i,j) a local threshold p_th,ij is drawn in [0, p_thMax] from the chosen distribution.\n''' + Fore.GREEN + Style.BRIGHT + '''\n · Global percolation probability P*:''' + Style.RESET_ALL + Fore.CYAN + ''' controls how many edges become "open". An edge (i,j) can transmit only if\n''' + '''   P* ≥ p_th,ij   →   A*_ij = 1,   otherwise A*_ij = 0.\n''' + Fore.GREEN + Style.BRIGHT + '''\n · Spreading from a seed node:''' + Style.RESET_ALL + Fore.CYAN + ''' starting from the seed s at t = 0, activity spreads along open edges. The active set evolves as\n''' + '''   S_{t+1} = N_open(S_t) \\ R_t, ''' + '''where N_open(S_t) are neighbors reachable through open edges and R_t are recovered nodes.\n''' + Fore.GREEN + Style.BRIGHT + '''\n · Recovery time τ:''' + Style.RESET_ALL + Fore.CYAN + ''' a node activated at time t stays active for τ steps and then recovers (it no longer transmits).\n''' + Style.RESET_ALL, formatter_class=argparse.RawDescriptionHelpFormatter)
	percolation.add_argument('-t', '--fileType', action='store', type=str, choices = ["matrix", "edgelist", "sif", "dot"], help='-[required] File type', required=True)
	percolation.add_argument('-i', '--inputFile', action='store', help='-[required] Specify the input file name', required=True)
	percolation.add_argument('-s', '--sep', action='store', type=str, help='-[optional] Column separator of the input file (ex. \',\'); detected automatically if omitted', required=False)
	percolation.add_argument('-nh', '--NoHeader', action='store_true', help='-[optional] Use this flag if your file doesn\'t have an header', required=False)
	percolation.add_argument('-d', '--directed', action='store_true', help='-[optional] Use this flag if your graph is directed', required=False)
	percolation.add_argument('-w', '--weight', action='store_true', help='-[optional] Use this flag if your graph is weighted', required=False)
	percolation.add_argument('-wt', '--weight-type', dest='weightType', action='store', choices=['distance', 'affinity', 'signed'], default='distance', help='-[optional] With -w, what the weights are: distance (a length, the default), affinity (a tie strength, e.g. |r| or a count) or signed (a signed strength, e.g. a correlation: the magnitude is used, the sign is kept). Negative weights require signed', required=False)
	percolation.add_argument('-dt', '--distance-transform', dest='distanceTransform', action='store', choices=['inverse', 'one-minus', 'neglog'], default='inverse', help='-[optional] With -w and an affinity or signed weight type, how a strength a becomes a length: inverse 1/a (default), one-minus 1-a or neglog -ln(a) (both for 0<a<=1)', required=False)
	percolation.add_argument('-r', '--remove', action='store', help='-[optional] Select the node/nodes to be removed from the graph (ex. A,B,C)', required=False)
	percolation.add_argument('-n', '--nodes', action='store', help='-[optional] ID of the seed node where the process starts. If not provided, a random node in the graph is chosen.', required=False, default=None)
	percolation.add_argument('-P', '--PrInf', action='store', type=_unit, help='-[optional] Global infectivity / Occupation probability (0–1). Higher P* → easier spreading / percolation. Default value is 0.5.', required=False, default=0.5)
	percolation.add_argument('-tau', '--tau', action='store', type=_pos_float, help='-[optional] Recovery time τ (in simulation steps). A node can transmit for τ steps after activation, then becomes recovered. Must be > 0. Default: 4.', required=False, default=4)
	percolation.add_argument('-tauDist', '--tauDistribution', choices=['fixed', 'uniform', 'normal', 'bimodal'], action='store', help='-[optional] Distribution used for recovery times τ. "fixed": single global τ for all nodes (default). "uniform"/"normal"/"bimodal": interpret -tau as τ_max and draw per-node τ_i in (0, τ_max] from the chosen distribution.', required=False, default='fixed')
	percolation.add_argument('-tauFile', '--tauFile', action='store', help=('-[optional] TSV file with fixed per-node recovery times. Must contain two ''columns: "Nodes" and "Recovery_time". Node labels in "Nodes" must match. When provided, these τ_i values ''override -tau and -tauDist.'), required=False, default=None)
	percolation.add_argument('-pth', '--pthMax', action='store', type=_unit, help='-[optional] Maximum local threshold p_th in [0,1]. Each edge (i,j) gets a local threshold p_th,ij drawn in [0, p_thMax]; the edge can transmit only if P* >= p_th,ij. Default: 1.0.', required=False, default=1)
	percolation.add_argument('-dist', '--pthDistribution', choices=['uniform', 'normal', 'bimodal'], action='store', help='-[optional] Distribution used to sample local thresholds p_th,ij in [0, p_thMax]. "uniform": all values equally likely; "normal": thresholds cluster around a central value; "bimodal": two groups of edges with low and high thresholds. Default: uniform.', required=False, default='uniform')
	percolation.add_argument('--seed', action='store', type=_seed, default=None, help='-[optional] Random seed of the seed node, thresholds and recovery times, so a run can be reproduced (default: a new one each run, printed on screen)', required=False)
	percolation.add_argument('-mxs', '--maxSteps', action='store', type=_pos_int, help='-[optional] Maximum number of simulation steps. Default: number of nodes in the graph.', required=False, default=None)
	snapshot_group = percolation.add_mutually_exclusive_group()
	snapshot_group.add_argument("--snapshotInfected", type=_pos_int, default=None, help=" -[optional] If set, take a snapshot when the number of *currently infected* nodes reaches this value. The TSV report will include node states at that time.", required=False )
	snapshot_group.add_argument("--snapshotNode", type=str, default=None, help="-[optional] If set, take a snapshot at the time when this node becomes infected. Can be a node label or a node index (0-based).", required=False )
	percolation.add_argument('--no-plot', action='store_true', help='-[optional] Skip the interactive HTML report; only the TSV report is written', required=False)
	percolation.add_argument('-o', '--outdir', action='store', type=str, help='-[optional] Select where to store the output (if not specified the output will be stored in same directory as the input file)', required=False)
	percolation.add_argument('-v', '--verbose', action='store_true', help='-[optional] Use this flag to receive prints of partial results of the measures.', required=False)

	# ---- omics ----
	omics = subparsers.add_parser('omics', allow_abbrev=False, usage=Fore.GREEN + Style.BRIGHT + 'pyntacle ' + Fore.RED + 'omics ' + Fore.MAGENTA + '{transcriptomics | metagenomics}' + Fore.CYAN + ' -i {matrix} (-m {metadata} --group-col {column} | --tcga) -o {outdir} [optional parameters]' + Style.RESET_ALL,
		help='''Builds one network per sample group from a raw count (transcriptomics) or abundance (metagenomics) matrix, ready for the other Pyntacle commands. Needs: pip install scikit-learn statsmodels''',
		description=Fore.RED + Style.BRIGHT + '''Pipelines:\n''' + Fore.GREEN + Style.BRIGHT + ''' · transcriptomics:''' + Style.RESET_ALL + Fore.CYAN + ''' raw counts (or log2(count+1)) -> median-of-ratios -> GMM gene selection -> expression gate -> Ledoit-Wolf partial correlations -> permutation FDR.\n\n''' + Fore.GREEN + Style.BRIGHT + ''' · metagenomics:''' + Style.RESET_ALL + Fore.CYAN + ''' relative abundances or read counts -> prevalence panel -> closure, multiplicative replacement, CLR -> graphical lasso with StARS.\n\n''' + Style.RESET_ALL + '''The edge list Weight is the signed partial correlation r: analyse the networks with -w --weight-type signed.''',
		formatter_class=argparse.RawDescriptionHelpFormatter)
	omics.add_argument(dest='subcommand', choices=['transcriptomics', 'metagenomics'], help='Select the pipeline')
	omics.add_argument('-i', '--inputFile', required=True, help='-[required] Feature x sample matrix (or sample x feature: detected from the metadata ids). TSV, or CSV by extension; may be compressed')
	omics.add_argument('-m', '--metadata', default=None, help='-[required unless --tcga] Sample metadata table, first column = sample id')
	omics.add_argument('--group-col', default=None, help='-[required with -m] Metadata column with the sample group (one network per group)')
	omics.add_argument('--groups', default=None, help='-[optional] Comma-separated group values to keep (default: all)')
	omics.add_argument('-o', '--outdir', required=True, help='-[required] Output directory (created if missing)')
	omics.add_argument('--prefix', default=None, help='-[optional] Output file prefix (default: input file name without extension)')
	omics.add_argument('--sep', default=None, help='-[optional] Field separator of the matrix and the metadata (default: comma for .csv, tab otherwise)')
	omics.add_argument('--covariates', default=None, help='-[optional] Comma-separated metadata columns regressed out of every feature, per group')
	omics.add_argument('--seed', type=_seed, default=None, help='-[optional] Random seed (default: 20260731 transcriptomics, 0 metagenomics)')
	omics.add_argument('--save-stages', action='store_true', help='-[optional] Also write the intermediate matrices')
	omics.add_argument('--input-scale', choices=['auto', 'counts', 'log2p1'], default='auto', help='-[transcriptomics] Scale of the input values (default: detected)')
	omics.add_argument('--tcga', action='store_true', help='-[transcriptomics] Groups from the TCGA barcodes (see --tcga-types), one sample per patient; replaces -m and --group-col')
	omics.add_argument('--tcga-types', default='01:tumor,11:normal', help='-[transcriptomics] With --tcga: sample type codes to keep and their group names (default 01:tumor,11:normal)')
	omics.add_argument('--biotype', default=None, help="-[transcriptomics] 'mygene' or an annotation file (columns gene,symbol,type_of_gene): keep protein-coding + ncRNA")
	omics.add_argument('--drop-sex-genes', action='store_true', help='-[transcriptomics] Remove 16 sex-linked genes (needs --biotype)')
	omics.add_argument('--gate-alpha', type=_fraction, default=0.05, help='-[transcriptomics] Significance of the expression-bias test (default 0.05)')
	omics.add_argument('--gate-top', type=_pos_int, default=100, help='-[transcriptomics] Strongest edges inspected by the gate (default 100)')
	omics.add_argument('--gate-min-genes', type=_pos_int, default=300, help='-[transcriptomics] Stop raising the gate below this many genes (default 300)')
	omics.add_argument('--fdr', type=_fraction, default=0.001, help='-[transcriptomics] Edge FDR (default 0.001)')
	omics.add_argument('--n-perm', type=_pos_int, default=3, help='-[transcriptomics] Permutations for the null (default 3)')
	omics.add_argument('--rank', choices=['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain'], default=None, help='-[metagenomics] Taxonomic rank to analyse when the feature ids are lineages (MetaPhlAn, QIIME 2)')
	omics.add_argument('--prevalence', type=_prevalence, default='auto', help="-[metagenomics] Prevalence threshold in (0, 1], or 'auto' (default)")
	omics.add_argument('--stars-beta', type=_stars_beta, default=0.10, help='-[metagenomics] StARS instability bound, in (0, 0.5) (default 0.10)')
	omics.add_argument('--n-sub', type=_pos_int, default=50, help='-[metagenomics] StARS subsamples (default 50)')
	omics._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	omics._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL

	return parser