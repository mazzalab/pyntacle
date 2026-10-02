"""The compiled group betweenness must equal its definition.

The kernel counts shortest paths instead of listing them, so it is checked
against the definition computed the slow way: list every shortest path with
igraph and count the ones with an inner node in the group. The brute force
returns the exact (unrounded) best score and every optimal set, so both are
compared on every set of size k.
"""
import itertools
import random
from collections import defaultdict

import igraph as ig
import pytest

from conftest import make_graphtacle
from pyntacle._ext.wrapper import cython_wrapper_bruteforce


def by_definition(g, group, weights=None):
    n, k = g.vcount(), len(group)
    inside = set(group)
    others = [v for v in range(n) if v not in inside]
    total = 0.
    for i, s in enumerate(others):
        rest = others[i + 1:]
        if not rest:
            continue
        paths = defaultdict(list)
        for p in g.get_all_shortest_paths(s, to=rest, weights=weights):
            paths[p[-1]].append(p)
        for ps in paths.values():
            total += sum(any(v in inside for v in p[1:-1]) for p in ps) / len(ps)
    return total / ((n - k) * (n - k - 1))


def check(g, k, weights=None):
    graph = make_graphtacle(g, weights=weights, name="g")
    _, score, tied, n_optimal = cython_wrapper_bruteforce(graph, k, "betweenness", max_ties=10 ** 6)
    values = {S: by_definition(g, S, weights) for S in itertools.combinations(range(g.vcount()), k)}
    best = max(values.values())
    expected = {S for S, v in values.items() if abs(v - best) <= 1e-9 * max(1., best)}
    assert score == pytest.approx(best, abs=1e-12)
    assert {tuple(sorted(int(x) for x in S)) for S in tied} == expected
    assert n_optimal == len(expected)


def test_a_bridge_carries_every_path_between_the_two_sides():
    """Two triangles joined by the path 2-6-3. Node 6 is an inner node of all
    9 shortest paths between {0,1,2} and {3,4,5}; node 2 (or 3) of only 8.
    Score: 9 / (6 * 5)."""
    g = ig.Graph(7, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 6), (6, 3)])
    _, score, tied, n_optimal = cython_wrapper_bruteforce(make_graphtacle(g, name="bridge"), 1, "betweenness")
    assert score == pytest.approx(9 / 30, abs=1e-12)
    assert [[int(x) for x in S] for S in tied] == [[6]]
    assert n_optimal == 1


@pytest.mark.parametrize("seed", range(12))
def test_unweighted_random_graphs(seed):
    rng = random.Random(seed)
    n = rng.randint(8, 16)
    g = ig.Graph.Erdos_Renyi(n, m=rng.randint(n, 2 * n))
    g.simplify()
    check(g, rng.choice([1, 2]))


@pytest.mark.parametrize("seed", range(12))
def test_weighted_graphs_with_tied_lengths(seed):
    # integer lengths make equal-length alternatives, the case where counting
    # predecessors goes wrong if the length comparison is off
    rng = random.Random(100 + seed)
    n = rng.randint(8, 14)
    g = ig.Graph.Erdos_Renyi(n, m=rng.randint(n, 2 * n))
    g.simplify()
    check(g, rng.choice([1, 2]), weights=[float(rng.randint(1, 3)) for _ in range(g.ecount())])


def test_fractional_lengths_that_sum_to_the_same_value():
    # 0.1 + 0.2 != 0.3 in floating point: both routes from 0 to 3 are shortest
    g = ig.Graph(4, [(0, 1), (1, 3), (0, 2), (2, 3)])
    check(g, 1, weights=[0.1, 0.2, 0.2, 0.1])


def test_lattice_with_many_equivalent_paths():
    check(ig.Graph.Lattice([4, 4], circular=False), 2)


def test_disconnected_pairs_are_skipped():
    g = ig.Graph.Ring(5) + ig.Graph.Ring(4)
    check(g, 1)
    check(g, 2)
