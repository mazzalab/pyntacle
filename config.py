__author__ = ["Daniele Capocefalo", "Mauro Truglio", "Tommaso Mazza"]
__copyright__ = u"Copyright 2018, The Pyntacle Project"
__credits__ = [u"Ferenc Jordan"]
__version__ = u"1.0.0"
__maintainer__ = u"Daniele Capocefalo"
__email__ = "bioinformatics@css-mendel.it"
__status__ = u"Development"
__date__ = u"26/11/2018"
__license__ = u"""
  Copyright (C) 2016-2018  Tommaso Mazza <t.mazza@css-mendel.it>
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
import copy
import os, sys
import logging
import datetime
import threading
import time
from numba import cuda
from numba.config import *
from multiprocessing import cpu_count
from psutil import virtual_memory
import seaborn as sns
import importlib
from colorama import Fore, Style

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
format_dictionary = {"adjmat": "adjm", "edgelist": "egl", "sif": "sif", "dot": "dot", "bin": "graph", "adjm": "adjm",
                     "graph": "graph", "edgl": "egl", "egl": "egl", "binary": "bin", "adjacencymatrix": "adjm",
                     "edge_list": "egl", "adjacency_matrix": "adjm"}
report_format = {"tsv": "tsv", "txt": "tsv", "csv": "csv", "xlsx": "xlsx", "xlx": "xlsx"}

runtime_date = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")


pycairo_message = u"WARNING: It seems that the pycairo library is not installed/available. Graph plot(s) will not be produced\n"

#generic lines
sep_line = Fore.LIGHTGREEN_EX + Style.BRIGHT + u"*" *100 + "\n" + Style.RESET_ALL
section_end = Fore.RED + Style.BRIGHT + u"*"*100 + "\n" + Style.RESET_ALL

#dedicated lines
import_start = Fore.RED + Style.BRIGHT + u"*" * 42 + "  FILE IMPORT  " + "*" * 43 + "\n" + Style.RESET_ALL
run_start = Fore.RED + Style.BRIGHT + u"*" * 43 + "  RUN START  " + "*" * 44 + "\n" + Style.RESET_ALL
summary_start = Fore.RED + Style.BRIGHT + u"*" * 42 + "  RUN SUMMARY  " + "*" * 43 + "\n" + Style.RESET_ALL
report_start = Fore.RED + Style.BRIGHT + u"*" * 45 + "  REPORT  " + "*" * 45 + "\n" + Style.RESET_ALL

# Add system info
n_cpus = cpu_count()-1 # Leaving one thread out
NUMBA_NUM_THREADS = n_cpus
mem = virtual_memory().total
cuda_avail = cuda.is_available()
threadsperblock = 32


sigkill_message = "\nReceived SIGKILL from keyboard\n"

class CursorAnimation(threading.Thread):
    """
    Just a waiting animation, common to several commands.
    """
    def __init__(self):
        self.flag = True

        if os.name == "nt":
            self.animation_char = u"|/-\""
        else:
            self.animation_char = u'⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
        self.idx = 0
        threading.Thread.__init__(self)

    def run(self):
        while self.flag:
            sys.stdout.write("Processing...", )
            sys.stdout.write(self.animation_char[self.idx % len(self.animation_char)] + "\r", )
            self.idx += 1
            time.sleep(0.1)

    def stop(self):
        self.flag = False
