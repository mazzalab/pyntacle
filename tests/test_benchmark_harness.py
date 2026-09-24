"""The old-vs-new benchmark harness (benchmarks/): cell expansion, sharding,
flag translation, report parsing and the runner's exit classification.

None of these run either pyntacle; they pin the rules that decide whether
the benchmark's numbers are comparable at all.
"""

import os
import sys

import pytest

BENCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "benchmarks")
sys.path.insert(0, BENCH)

import cli_map  # noqa: E402
import matrix  # noqa: E402
import parity  # noqa: E402
import runner  # noqa: E402

TOOLS = {"old_bin": "/old/pyntacle", "new_python": "/new/python", "new_main": "/repo/main.py"}
GRAPH = {"sif": "/d/g.sif", "sif_weighted": "/d/g_w.sif", "probe_nodes": ["a", "b"]}

CFG = {"groups": [
    {"name": "m", "cmds": ["local", "kp-info"], "topologies": ["er"], "n": [10, 20],
     "weighted": [False, True], "tools": ["old", "new", "new-py"]},
    {"name": "f", "cmds": ["kp-finder", "gc-finder"], "topologies": ["er", "ba"], "n": [10, 20],
     "k": [2], "algorithms": ["brute_force", "greedy"], "threads": [1, 4],
     "tools": ["old", "new", "new-py"]},
]}


def test_expansion_skips_meaningless_cells():
    cells = matrix.expand(CFG)
    assert not [c for c in cells if c["tool"] == "old" and c["weighted"]], "old has no weighted paths"
    assert not [c for c in cells if c["tool"] == "new-py" and c["algorithm"] == "brute_force"]
    assert not [c for c in cells if c["tool"] == "new-py" and c["cmd"] == "local"]
    assert not [c for c in cells if c["algorithm"] == "greedy" and c["threads"] != 1]
    keys = [matrix.cell_key(c) for c in cells]
    assert len(keys) == len(set(keys))


def test_shards_partition_cells_and_keep_tools_together():
    cells = matrix.expand(CFG)
    shards = [matrix.shard(cells, i, 3) for i in range(3)]
    flat = [matrix.cell_key(c) for s in shards for c in s]
    assert sorted(flat) == sorted(matrix.cell_key(c) for c in cells)
    for s in shards:
        for c in s:
            # every tool of the same parameters lands on the same node
            twins = [d for d in cells if matrix._shard_key(d) == matrix._shard_key(c)]
            assert all(t in s for t in twins)


def test_flag_collisions_are_translated():
    cell = {"cmd": "kp-finder", "k": 3, "algorithm": "brute_force", "threads": 4, "weighted": False}
    old = cli_map.build_argv("old", TOOLS, cell, GRAPH, "/out")
    new = cli_map.build_argv("new", TOOLS, cell, GRAPH, "/out")
    # old: -f is the input format, -t the metric; new: -t is the input format
    assert old[old.index("-f") + 1] == "sif" and old[old.index("-t") + 1] == "all"
    assert new[new.index("-t") + 1] == "sif" and new[new.index("-oper") + 1] == "all"
    assert old[old.index("-I") + 1] == "brute-force" and new[new.index("-a") + 1] == "brute_force"
    assert old[old.index("-O") + 1] == "4" and new[new.index("-np") + 1] == "4"
    assert "--no-plot" in old and "--no-plot" in new
    assert int(new[new.index("--max-ties") + 1]) >= 10 ** 6, "old lists every tie; new must too"


def test_weighted_cells_are_new_only():
    cell = {"cmd": "local", "weighted": True, "k": "", "algorithm": "", "threads": 1}
    with pytest.raises(cli_map.Unsupported):
        cli_map.build_argv("old", TOOLS, cell, GRAPH, "/out")
    new = cli_map.build_argv("new", TOOLS, cell, GRAPH, "/out")
    assert "-w" in new and GRAPH["sif_weighted"] in new


def _report(tmp_path, name, text):
    d = tmp_path / name
    d.mkdir()
    (d / "Report_x.tsv").write_text(text)
    return str(d)


def test_finder_parity_compares_the_whole_tie_family(tmp_path):
    old = _report(tmp_path, "old", "Pyntacle Report\tKP\t\nResults:\t\nIndex\tNode set\tValue\t\n"
                  "F\ta,b\t0.04167\t\n\tb,c\t0.04167\t\nm-reach\ta,c\t12\t\n")
    new = _report(tmp_path, "new", "Pyntacle report\tx\noperation\tSetID\tKey-player\tscore\n"
                  "F\t1\t['b', 'a']\t0.042\nF\t2\t['c', 'b']\t0.042\nmreach\t1\t['c', 'a']\t12.0\n")
    o, n = parity.parse("kp-finder", "old", old), parity.parse("kp-finder", "new", new)
    assert parity.compare("kp-finder", "brute_force", o, n)[0] == "yes"
    n["f"]["sets"].pop()
    same, _, _, notes = parity.compare("kp-finder", "brute_force", o, n)
    assert same == "no" and "optimal sets differ" in notes


def test_global_parity_inverts_old_compactness(tmp_path):
    old = _report(tmp_path, "old", "Metric\tValue\t\ncompactness\t8.85\t\ndensity\t0.12245\t\n")
    new = _report(tmp_path, "new", "Measure\tScore\nCompactness\t0.113\nDensity\t0.122\n")
    o, n = parity.parse("global", "old", old), parity.parse("global", "new", new)
    assert parity.compare("global", "", o, n)[0] == "yes"


@pytest.mark.parametrize("code,kwargs,status", [
    ("pass", {}, "ok"),
    ("import sys; sys.exit(3)", {}, "crash"),
    ("import time; time.sleep(30)", {"timeout_s": 0.5}, "timeout"),
    ("x = bytearray(400 * 2**20); import time; time.sleep(5)", {"mem_cap_mb": 150}, "oom"),
])
def test_runner_classifies_exits(code, kwargs, status):
    res = runner.run([sys.executable, "-c", code], **kwargs)
    assert res["exit_status"] == status
    assert res["wall_s"] < 10


def test_cpu_blocks_are_disjoint_and_respect_slots():
    import bench
    allowed = list(range(32))
    for threads, slots in [(1, 16), (4, 16), (8, 32), (32, 16), (2, 20)]:
        blocks = bench._cpu_blocks(allowed, threads, slots)
        flat = [c for b in blocks for c in b]
        assert len(flat) == len(set(flat)), "blocks overlap"
        assert all(len(b) == threads for b in blocks)
        # a cell wider than the slot budget still runs, alone
        assert len(flat) <= max(slots, threads)
    # half the cores busy: every other CPU, not the first sixteen
    assert bench._cpu_blocks(allowed, 1, 16)[:3] == [[0], [2], [4]]


def test_runner_pins_to_given_cpus():
    cpu = sorted(os.sched_getaffinity(0))[-1]
    res = runner.run([sys.executable, "-c", "pass"], cpus=[cpu])
    assert res["exit_status"] == "ok" and res["cpus"] == str(cpu)
