"""
Imports for using Pyntacle as Python package
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from .config import *

if cuda_avail:
    pass
