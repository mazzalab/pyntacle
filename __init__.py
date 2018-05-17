"""
Imports for using pyntacle as package
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from .config import *
from .algorithms import *
from .cmds import *
from .cmds.cmds_utils import *
from .exceptions import *
from .graph_operations import *
from .io_stream import *
from .pyntacletests import *
from .tools import *
from .tools.misc import *

import algorithms
if cuda_avail:
    import algorithms.shortestpath_gpu
import algorithms.scalefree_inference
import algorithms.sparseness
import algorithms.shortest_path
import algorithms.global_topology
import algorithms.keyplayer
import algorithms.local_topology
import algorithms.bruteforce_search
import algorithms.greedy_optimization

import cmds
import cmds.set
import cmds.communities
import cmds.generate
import cmds.metrics
import cmds.convert
import cmds.keyplayer

import cmds.cmds_utils
import cmds.cmds_utils.plotter
import cmds.cmds_utils.kpsearch_wrapper
import cmds.cmds_utils.reporter

import exceptions
import exceptions.unproperly_formatted_file_error
import exceptions.illegal_graph_size_error
import exceptions.illegal_argument_number_error
import exceptions.wrong_argument_error
import exceptions.missing_attribute_error
import exceptions.multiple_solutions_error
import exceptions.notagraph_error
import exceptions.generic_error
import exceptions.unsupported_graph_error
import exceptions.illegal_kppset_size_error

import graph_operations
import graph_operations.set_operations
import graph_operations.modules_finder

import io_stream
import io_stream.generator
import io_stream.exporter
import io_stream.format_converter
import io_stream.importer
import io_stream.import_attributes
import io_stream.export_attributes

import pyntacletests
import pyntacletests.test_widgets_setoperations
import pyntacletests.test_widgets_convert
import pyntacletests.test_widgets_keyplayer
import pyntacletests.test_widgets_metrics
import pyntacletests.test_suite
import pyntacletests.test_widgets_generator
import pyntacletests.test_widgets_communities

import tools
import tools.modules_utils
import tools.graph_utils
import tools.enums
import tools.edgelist_utils
import tools.add_attributes
import tools.adjmatrix_utils
import tools.octopus

import tools.misc
import tools.misc.timeit
import tools.misc.graph_routines
import tools.misc.kpsearch_utils
import tools.misc.shortest_path_modifications
import tools.misc.binarycheck
import tools.misc.graph_load
import tools.misc.io_utils
