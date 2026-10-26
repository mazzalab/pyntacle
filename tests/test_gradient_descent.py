"""The gradient descent and the set scorer it uses with the compiled engine.

The descent stopped at the first swap that raised the score by no more than
-tol (0.01 by default), so on any network where single swaps move a
normalised score by less than that it returned the random starting set after
a handful of swaps. Each set it scored also rebuilt the network and all its
distances, and -np was ignored.
"""
import random

import igraph as ig
import pytest

from conftest import make_graphtacle
from pyntacle._ext.wrapper import KernelScorer, cython_wrapper_greedy, cython_wrapper_info
from pyntacle.algorithms.greedy import operation_selector as python_metric
from pyntacle.algorithms.stochastic_gradient_descent import call_stochastic_gradient_descent
from pyntacle.main import kernel_scorer

KP_METRICS = ["F", "dF", "dR", "mreach"]
GROUP_METRICS = ["degree", "betweenness", "closeness"]


@pytest.fixture
def weighted_er():
    random.seed(0)  # igraph draws from Python's random module
    g = ig.Graph.Erdos_Renyi(n=80, m=240)
    g = g.components().giant()
    rng = random.Random(3)
    return make_graphtacle(g, weights=[rng.uniform(1.0, 4.0) for _ in range(g.ecount())], name="wer")


def random_sets(graph, k, count, seed=0):
    rng = random.Random(seed)
    names = graph.vs()["name"]
    return [rng.sample(names, k) for _ in range(count)]


@pytest.mark.parametrize("metric", KP_METRICS + GROUP_METRICS)
def test_one_scorer_matches_a_fresh_one_on_every_set(weighted_er, metric):
    # the scorer reuses its distances and scratch buffers across sets
    scorer = KernelScorer(weighted_er, metric, "min", 2, 1)
    for nodes in random_sets(weighted_er, 3, 25):
        fresh = cython_wrapper_info(weighted_er, nodes, metric, distance_type="min", mdist=2, n_threads=1)
        assert scorer(nodes) == pytest.approx(fresh)


@pytest.mark.parametrize("metric", ["dR", "mreach", "closeness"])
def test_distance_matrix_is_the_same_with_any_thread_count(weighted_er, metric):
    one = KernelScorer(weighted_er, metric, "min", 2, 1)
    four = KernelScorer(weighted_er, metric, "min", 2, 4)
    for nodes in random_sets(weighted_er, 3, 25, seed=1):
        assert one(nodes) == four(nodes)


@pytest.mark.parametrize("metric", ["dR", "closeness"])
def test_weighted_distances_match_the_python_engine(weighted_er, metric):
    scorer = KernelScorer(weighted_er, metric, "min", 2, 2)
    for nodes in random_sets(weighted_er, 3, 10, seed=2):
        assert scorer(nodes) == pytest.approx(python_metric(weighted_er, metric, nodes, distance_type="min", mdist=2))


def test_kernel_scorer_holds_one_distance_matrix_at_a_time(zachary):
    score = kernel_scorer(zachary, "min", 2, 1)
    nodes = ["0", "33"]
    assert score(nodes, "dR") == pytest.approx(cython_wrapper_info(zachary, nodes, "dR", "min", 2, 1))
    assert score(nodes, "mreach") == pytest.approx(cython_wrapper_info(zachary, nodes, "mreach", "min", 2, 1))
    held = [c.cell_contents for c in score.__closure__ if isinstance(c.cell_contents, dict)]
    assert [list(h) for h in held] == [["mreach"]]


@pytest.mark.parametrize("metric", KP_METRICS + GROUP_METRICS)
def test_descent_ends_at_a_local_optimum(weighted_er, metric):
    # no single swap of the returned set may raise its score
    scorer = kernel_scorer(weighted_er, "min", 2, 1)
    found, score = call_stochastic_gradient_descent(weighted_er, 3, metric, distance_type="min", mdist=2,
                                                    maxsec=60, seed=4, scorer=scorer)
    assert score == pytest.approx(scorer(found, metric))
    others = [x for x in weighted_er.vs()["name"] if x not in found]
    for out in found:
        for into in others:
            swapped = [into if x == out else x for x in found]
            assert scorer(swapped, metric) <= score + 1e-12, (out, into)


def test_descent_reaches_the_greedy_score_on_small_normalised_gains():
    # dR moves by far less than 0.01 per swap here; the old rule stopped at the first gain
    random.seed(0)
    g = make_graphtacle(ig.Graph.Barabasi(400, 2), name="ba")
    _, greedy = cython_wrapper_greedy(g, 4, "dR", mdist=2, n_threads=1, seed=1)
    _, descent = call_stochastic_gradient_descent(g, 4, "dR", maxsec=60, seed=1,
                                                  scorer=kernel_scorer(g, "min", 2, 1))
    assert descent >= greedy - 0.02


def test_tolerance_ignores_smaller_gains(zachary):
    # with a tolerance above every possible gain no swap is taken: the start comes back
    scores = []
    def scorer(names, oper):
        scores.append(names)
        return len(set(names) & {"0", "33"})
    found, score = call_stochastic_gradient_descent(zachary, 2, "dR", tolerance=5, maxsec=30, seed=1, scorer=scorer)
    assert sorted(found) == sorted(scores[0])


def test_probability_returns_the_best_set_met(zachary):
    seen = []
    def scorer(names, oper):
        s = len(set(names) & {"0", "33", "32"}) + 0.001 * random.Random(",".join(sorted(names))).random()
        seen.append(s)
        return s
    _, score = call_stochastic_gradient_descent(zachary, 3, "dR", probability=0.9, maxsec=1, seed=2, scorer=scorer)
    assert score == max(seen)
