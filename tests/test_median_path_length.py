"""The median shortest-path length of the global report.

It is read off the histogram of hop counts, a block of rows at a time, so it
must equal the plain median over every connected ordered pair, odd and even
pair counts and disconnected networks included.
"""
import random

import igraph as ig
import numpy as np
import pytest

from conftest import make_graphtacle


def by_definition(g):
    d = np.array(g.distances(), dtype=float)
    finite = d[np.isfinite(d) & (d != 0)]
    return float(np.median(finite)) if finite.size else float("nan")


@pytest.mark.parametrize("seed", range(10))
def test_random_networks(seed):
    rng = random.Random(seed)
    n = rng.randint(5, 60)
    g = ig.Graph.Erdos_Renyi(n, m=rng.randint(n // 2, 2 * n))
    assert make_graphtacle(g).median_global_shortest_path_length() == by_definition(g)


def test_even_number_of_pairs_averages_the_two_middle_values():
    # path 0-1-2: ordered pairs at 1, 1, 1, 1, 2, 2 hops -> median 1
    # path 0-1-2-3: 1 x6, 2 x4, 3 x2 -> middle values 1 and 2 -> 1.5
    assert make_graphtacle(ig.Graph(3, [(0, 1), (1, 2)])).median_global_shortest_path_length() == 1.0
    assert make_graphtacle(ig.Graph(4, [(0, 1), (1, 2), (2, 3)])).median_global_shortest_path_length() == 1.5


def test_blocks_smaller_than_the_network():
    g = ig.Graph.Barabasi(300, 2)
    graph = make_graphtacle(g)
    assert graph.median_global_shortest_path_length(chunk=7) == by_definition(g)


def test_disconnected_pairs_are_left_out():
    g = ig.Graph.Ring(5) + ig.Graph.Ring(8)
    assert make_graphtacle(g).median_global_shortest_path_length() == by_definition(g)


def test_no_connected_pair_gives_nan():
    assert np.isnan(make_graphtacle(ig.Graph(4)).median_global_shortest_path_length())
