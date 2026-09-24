"""Expand a benchmark config into cells, and split cells across nodes.

A config is JSON (no extra dependency on the cluster):

    {
      "profile": "hpc-paper", "seed": 42,
      "repeats": 5, "long_cell_s": 120, "long_cell_repeats": 3,
      "timeout_s": 3600, "mem_cap_mb": 400000,
      "tools": {"old_bin": "...", "new_python": "...", "new_main": "..."},
      "groups": [
        {"name": "local-size", "cmds": ["local", "global"],
         "topologies": ["er", "ba", "ws"], "n": [100, 1000], "d": [3],
         "weighted": [false, true], "tools": ["old", "new"]},
        ...
      ]
    }

Group keys that a command does not use (k, algorithms, threads for local)
are simply ignored for it, so one group can mix commands.

A *family* is a cell without its size n. Families are the unit of both
censoring (once n times out, larger n in the same family are skipped) and
sharding (a family never straddles two nodes, or censoring would not see its
own failures). Sharding goes one step further and keeps all tools of the
same parameters together.
"""

import hashlib
import itertools
import json
import os

FINDERS = ("kp-finder", "gc-finder")
CELL_FIELDS = ("group", "cmd", "tool", "topology", "n", "d", "weighted", "k", "algorithm", "threads")


def load_config(path):
    with open(path) as fh:
        cfg = json.load(fh)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools = {}
    for name, value in cfg["tools"].items():
        value = os.path.expanduser(os.path.expandvars(value))
        # relative paths are relative to the repo, so one config works on any checkout
        tools[name] = value if os.path.isabs(value) else os.path.join(repo, value)
    cfg["tools"] = tools
    return cfg


def _cells_of_group(grp):
    for cmd, tool, topo, n, d, weighted in itertools.product(
            grp["cmds"], grp["tools"], grp["topologies"], grp["n"],
            grp.get("d", [3]), grp.get("weighted", [False])):
        if cmd in FINDERS:
            combos = itertools.product(grp.get("k", [2]), grp.get("algorithms", ["brute_force"]),
                                       grp.get("threads", [1]))
        else:
            combos = [("", "", 1)]
        for k, algo, threads in combos:
            # weighted distances do not exist in old; brute force has no python engine
            if weighted and tool == "old":
                continue
            if tool == "new-py" and (cmd in ("local", "global") or algo == "brute_force"):
                continue
            # old brute force only takes a process count; greedy is single-threaded in both
            if cmd in FINDERS and algo != "brute_force" and threads != 1:
                continue
            yield {"group": grp["name"], "cmd": cmd, "tool": tool, "topology": topo,
                   "n": n, "d": d, "weighted": bool(weighted), "k": k,
                   "algorithm": algo, "threads": threads}


def expand(cfg):
    """All cells of a config, deduplicated (groups may overlap)."""
    seen, cells = set(), []
    for grp in cfg["groups"]:
        for cell in _cells_of_group(grp):
            key = cell_key(cell, with_group=False)
            if key not in seen:
                seen.add(key)
                cells.append(cell)
    return cells


def graphs_of(cfg):
    return sorted({(c["topology"], c["n"], c["d"]) for c in expand(cfg)})


def cell_key(cell, with_group=False):
    fields = CELL_FIELDS if with_group else CELL_FIELDS[1:]
    return "|".join(str(cell[f]) for f in fields)


def family_key(cell):
    return "|".join(str(cell[f]) for f in CELL_FIELDS[1:] if f != "n")


def _shard_key(cell):
    # old, new and new-py of the same parameters share a node, so every
    # speed-up is a ratio measured on one machine, interleaved in time
    return "|".join(str(cell[f]) for f in CELL_FIELDS[1:] if f not in ("n", "tool"))


def _cost(cell):
    # rough relative cost, only used to balance shards
    n, k = cell["n"], cell["k"] or 1
    if cell["cmd"] in FINDERS and cell["algorithm"] == "brute_force":
        from math import comb
        return comb(n, k) * n / max(1, cell["threads"])
    return n * n


def shard(cells, index, count):
    """Cells of shard `index` (0-based) out of `count`, balanced by family cost."""
    families = {}
    for c in cells:
        families.setdefault(_shard_key(c), []).append(c)
    # longest-processing-time first: heaviest family to the lightest shard
    order = sorted(families.items(),
                   key=lambda kv: (-sum(_cost(c) for c in kv[1]),
                                   hashlib.sha1(kv[0].encode()).hexdigest()))
    loads = [0.0] * count
    mine = []
    for _, fam in order:
        target = loads.index(min(loads))
        loads[target] += sum(_cost(c) for c in fam)
        if target == index:
            mine.extend(fam)
    return mine
