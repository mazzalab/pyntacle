"""The only module that knows both command lines.

Flags collide silently between the two versions (old ``-t`` is the metric
type and ``-f`` the input format; new ``-t`` is the input format and ``-f``
the figure format), so no argv is ever built anywhere else.

Every default that differs between the tools is pinned here explicitly:
m-reach distance, group-closeness distance, algorithm names, thread count,
greedy seed, and how many tied optimal sets the brute force lists (old always
lists all of them, so new is told to as well).
"""

MREACH = 2
GC_DISTANCE = "min"
ALL_TIES = 1000000

_OLD_ALGO = {"brute_force": "brute-force", "greedy": "greedy"}


class Unsupported(Exception):
    """The cell has no meaning for this tool (e.g. weighted paths in old)."""


def _old(tools, cell, graph, outdir):
    cmd = cell["cmd"]
    if cmd == "startup":
        return [tools["old_bin"], "--version"]
    if cell.get("weighted"):
        raise Unsupported("Pyntacle 1.3.2 has no weighted shortest paths")
    common = ["-f", "sif", "-i", graph["sif"], "-d", outdir,
              "--no-plot", "-r", "txt", "--suppress-cursor"]
    if cmd in ("local", "global"):
        return [tools["old_bin"], "metrics", cmd] + common
    if cmd == "kp-info":
        return ([tools["old_bin"], "keyplayer", "kp-info"] + common
                + ["-t", "all", "-m", str(MREACH), "-n", ",".join(graph["probe_nodes"])])
    if cmd == "kp-finder":
        return ([tools["old_bin"], "keyplayer", "kp-finder"] + common
                + ["-t", "all", "-m", str(MREACH), "-k", str(cell["k"]),
                   "-I", _OLD_ALGO[cell["algorithm"]], "-O", str(cell["threads"])])
    if cmd == "gc-info":
        return ([tools["old_bin"], "groupcentrality", "gr-info"] + common
                + ["-t", "all", "-D", GC_DISTANCE, "-n", ",".join(graph["probe_nodes"])])
    if cmd == "gc-finder":
        return ([tools["old_bin"], "groupcentrality", "gr-finder"] + common
                + ["-t", "all", "-D", GC_DISTANCE, "-k", str(cell["k"]),
                   "-I", _OLD_ALGO[cell["algorithm"]], "-O", str(cell["threads"])])
    raise Unsupported(cmd)


def _new(tools, cell, graph, outdir, python_engine=False):
    cmd = cell["cmd"]
    base = [tools["new_python"], tools["new_main"]]
    if cmd == "startup":
        return base + ["--help"]
    if python_engine and cmd in ("local", "global"):
        raise Unsupported("--engine only exists on keyplayer/groupcentrality")
    if python_engine and cell.get("algorithm") == "brute_force":
        raise Unsupported("brute force has no python implementation")

    src = graph["sif_weighted"] if cell.get("weighted") else graph["sif"]
    common = ["-t", "sif", "-i", src, "-o", outdir, "--no-plot"]
    if cell.get("weighted"):
        common.append("-w")
    engine = ["--engine", "python"] if python_engine else []

    if cmd in ("local", "global"):
        return base + [cmd] + common
    if cmd == "kp-info":
        return (base + ["keyplayer", "kp-info"] + common + engine
                + ["-oper", "all", "-m", str(MREACH), "-n", ",".join(graph["probe_nodes"])])
    if cmd == "kp-finder":
        return (base + ["keyplayer", "kp-finder"] + common + engine
                + ["-oper", "all", "-m", str(MREACH), "-k", str(cell["k"]),
                   "-a", cell["algorithm"], "-np", str(cell["threads"]),
                   "--max-ties", str(ALL_TIES), "--seed", "1"])
    if cmd == "gc-info":
        return (base + ["groupcentrality", "gc-info"] + common + engine
                + ["-oper", "all", "-v", GC_DISTANCE, "-n", ",".join(graph["probe_nodes"])])
    if cmd == "gc-finder":
        return (base + ["groupcentrality", "gc-finder"] + common + engine
                + ["-oper", "all", "-v", GC_DISTANCE, "-k", str(cell["k"]),
                   "-a", cell["algorithm"], "-np", str(cell["threads"]),
                   "--max-ties", str(ALL_TIES), "--seed", "1"])
    raise Unsupported(cmd)


def build_argv(tool, tools, cell, graph, outdir):
    """argv for one run. ``graph`` is the workloads metadata dict (None for startup)."""
    if tool == "old":
        return _old(tools, cell, graph, outdir)
    if tool == "new":
        return _new(tools, cell, graph, outdir)
    if tool == "new-py":
        return _new(tools, cell, graph, outdir, python_engine=True)
    raise ValueError("unknown tool: " + tool)
