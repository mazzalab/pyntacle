import logging
import datetime
import importlib
import seaborn as sns
import threading
import time
import sys
import os

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
format_dictionary = {"adjmat": "adjm", "edgelist": "egl", "sif": "sif", "dot": "dot", "bin": "graph", "adjm": "adjm",
                     "graph": "graph", "edgl": "egl", "egl": "egl", "binary": "bin", "adjacencymatrix": "adjm",
                     "edge_list": "egl", "adjacency_matrix": "adjm"}
runtime_date = datetime.datetime.now().strftime("%d%m%Y%H%M")


class CursorAnimation(threading.Thread):
    """
    Just a waiting animation, common to several commands.
    """
    def __init__(self):
        self.flag = True

        if os.name == "nt":
            self.animation_char = u'|/-\\'
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
