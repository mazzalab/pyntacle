"""Shared fixtures for the Pyntacle test-suite.

The pyntacle package uses flat sibling imports (``from utility import *``), so the
``pyntacle/`` directory itself has to be on ``sys.path`` before anything is imported.
"""
import os
import sys

import igraph as ig
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_DIR = os.path.join(REPO_ROOT, "pyntacle")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from GraphTacle import Graphtacle  # noqa: E402


def make_graphtacle(g, weights=None, directed=False, name="test"):
    """Wrap a plain igraph graph into a Graphtacle without touching the filesystem.

    Mirrors what Graphtacle.from_file() produces, minus the file parsing.
    """
    n = g.vcount()
    names = [str(i) for i in range(n)]
    if weights is None:
        weights = [1.0] * g.ecount()
    return Graphtacle(n, g.get_edgelist(), names, list(names), list(weights),
                      directed, "edgelist", None, True, name, "keyplayer")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: performance test, run with --runslow")


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="run the performance regression tests")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip_slow = pytest.mark.skip(reason="need --runslow to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


# --------------------------------------------------------------------------
# Graph fixtures. Each yields (Graphtacle, list-of-node-names-forming-K).
# --------------------------------------------------------------------------

@pytest.fixture
def zachary():
    return make_graphtacle(ig.Graph.Famous("Zachary"), name="zachary")


@pytest.fixture
def er_connected():
    g = ig.Graph.Erdos_Renyi(n=60, m=180)
    # keep only the giant component so the graph is genuinely connected
    g = g.components().giant()
    return make_graphtacle(g, name="er")


@pytest.fixture
def three_components():
    g = ig.Graph(12)
    g.add_edges([(0, 1), (1, 2), (2, 3), (3, 0),
                 (4, 5), (5, 6), (6, 4),
                 (7, 8), (8, 9), (9, 10), (10, 11)])
    return make_graphtacle(g, name="three_comp")


@pytest.fixture
def weighted_path():
    g = ig.Graph(6)
    g.add_edges([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    return make_graphtacle(g, weights=[1.0, 2.5, 0.5, 3.0, 1.5], name="wpath")


@pytest.fixture
def star():
    g = ig.Graph.Star(15, mode="undirected", center=0)
    return make_graphtacle(g, name="star")
