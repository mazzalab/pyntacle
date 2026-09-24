"""Benchmark driver: plan, run a shard, collect, parity.

    python bench.py plan    configs/hpc-paper.json --shards 5
    python bench.py prepare configs/hpc-paper.json          # build graph corpus
    python bench.py run     configs/hpc-paper.json --shard 0/5 --out results/hpc-paper
    python bench.py collect results/hpc-paper
    python bench.py parity  results/hpc-paper

`run` executes a shard's families (one cell with every n) as chains,
smallest n first, so a timeout at n skips every larger n of the family.
Chains run side by side on disjoint pinned CPU sets: one phase per thread
count, at most `slots` CPUs busy (config; default all allowed), and a cell
starts only if its estimated memory fits `mem_budget_mb` (default 85% of
RAM). Leaving half the cores idle (slots = cores/2) keeps memory-bandwidth
contention between neighbours low; each row records how many cells were
running (`concurrent`). The shard's raw rows go to runs_raw_<shard>.tsv,
appended after every run, so an interrupted job resumes where it stopped.
"""

import argparse
import concurrent.futures
import csv
import datetime
import os
import platform
import queue
import random
import shutil
import socket
import subprocess
import sys
import threading

import psutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cli_map  # noqa: E402
import matrix  # noqa: E402
import runner  # noqa: E402
import workloads  # noqa: E402

RAW_FIELDS = (["run_id", "shard", "host"] + list(matrix.CELL_FIELDS)
              + ["graph_id", "m", "density", "rep", "warmup",
                 "wall_s", "cpu_user_s", "cpu_sys_s", "max_rss_mb", "peak_cpu_pct",
                 "mean_cpu_pct", "read_bytes", "write_bytes", "exit_code", "exit_status",
                 "cpus", "concurrent", "outdir", "started_at"])
CENSORING = ("timeout", "oom")


def _parse_shard(text):
    i, n = text.split("/")
    return int(i), int(n)


def _read_done(path):
    done, censored = set(), {}
    if not os.path.exists(path):
        return done, censored
    with open(path) as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            done.add((row["run_id"], int(row["rep"])))
            if row["exit_status"] in CENSORING:
                fam = row["run_id"].rsplit("#", 1)[1]
                censored[fam] = min(int(row["n"]), censored.get(fam, 10 ** 12))
    return done, censored


def _append(path, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=RAW_FIELDS, delimiter="\t")
        if new:
            w.writeheader()
        w.writerow(row)


def _cmd_out(argv):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def write_env(cfg, out, shard_tag):
    import igraph
    import numpy
    tools = cfg["tools"]
    old_py = os.path.join(os.path.dirname(tools["old_bin"]), "python")
    cpu = ""
    try:
        with open("/proc/cpuinfo") as fh:
            cpu = next(l.split(":", 1)[1].strip() for l in fh if l.startswith("model name"))
    except (OSError, StopIteration):
        pass
    gov = ""
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") as fh:
            gov = fh.read().strip()
    except OSError:
        pass
    import psutil
    rows = [
        {"arm": "old",
         "tool_version": _cmd_out([tools["old_bin"], "--version"]).splitlines()[-1:] or [""],
         "python": _cmd_out([old_py, "-c", "import sys;print(sys.version.split()[0])"]),
         "igraph": _cmd_out([old_py, "-c", "import igraph;print(igraph.__version__)"]),
         "numpy": _cmd_out([old_py, "-c", "import numpy;print(numpy.__version__)"]),
         "install_path": tools["old_bin"], "commit": ""},
        {"arm": "new", "tool_version": "graphtacle",
         "python": _cmd_out([tools["new_python"], "-c", "import sys;print(sys.version.split()[0])"]),
         "igraph": _cmd_out([tools["new_python"], "-c", "import igraph;print(igraph.__version__)"]),
         "numpy": _cmd_out([tools["new_python"], "-c", "import numpy;print(numpy.__version__)"]),
         "install_path": tools["new_main"],
         "commit": _cmd_out(["git", "-C", os.path.dirname(tools["new_main"]), "rev-parse", "--short", "HEAD"])
                   + ("+dirty" if _cmd_out(["git", "-C", os.path.dirname(tools["new_main"]),
                                            "status", "--porcelain", "--untracked-files=no"]) else "")},
    ]
    path = os.path.join(out, "env_metadata_{}.tsv".format(shard_tag))
    fields = ["host", "arm", "cpu_model", "cores_allowed", "ram_gb", "kernel", "python", "igraph",
              "numpy", "tool_version", "commit", "install_path", "governor", "date", "harness_numpy",
              "harness_igraph"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        w.writeheader()
        for r in rows:
            if isinstance(r["tool_version"], list):
                r["tool_version"] = r["tool_version"][0] if r["tool_version"] else ""
            r.update({"host": socket.gethostname(), "cpu_model": cpu,
                      "cores_allowed": len(os.sched_getaffinity(0)),
                      "ram_gb": round(psutil.virtual_memory().total / 2 ** 30, 1),
                      "kernel": platform.release(), "governor": gov,
                      "date": datetime.datetime.now().isoformat(timespec="seconds"),
                      "harness_numpy": numpy.__version__, "harness_igraph": igraph.__version__})
            w.writerow(r)


def check_tools(cfg):
    """Refuse to start if the arms are not what they claim to be: a days-long
    run comparing the new tool with itself is worse than no run."""
    tools = cfg["tools"]
    old = _cmd_out([tools["old_bin"], "--version"])
    if "1.3.2" not in old:
        raise SystemExit("old_bin {} does not report Pyntacle 1.3.2 (got: {!r})".format(
            tools["old_bin"], old.splitlines()[-1:] if old else old))
    for path in (tools["new_python"], tools["new_main"]):
        if not os.path.exists(path):
            raise SystemExit("missing: " + path)
    probe = _cmd_out([tools["new_python"], "-c",
                      "import sys; sys.path.insert(0, {!r}); import _ext.wrapper; print('ok')".format(
                          os.path.dirname(tools["new_main"]))])
    if probe != "ok":
        raise SystemExit("new tool's compiled kernels do not import -- run setup.py build_ext --inplace")


def cmd_plan(args):
    cfg = matrix.load_config(args.config)
    cells = matrix.expand(cfg)
    print("profile {}: {} cells, {} graphs".format(cfg["profile"], len(cells), len(matrix.graphs_of(cfg))))
    by_tool = {}
    for c in cells:
        by_tool[c["tool"]] = by_tool.get(c["tool"], 0) + 1
    print("  per tool:", by_tool)
    for i in range(args.shards):
        mine = matrix.shard(cells, i, args.shards)
        print("  shard {}/{}: {} cells, {} families".format(
            i, args.shards, len(mine), len({matrix.family_key(c) for c in mine})))


def cmd_prepare(args):
    cfg = matrix.load_config(args.config)
    check_tools(cfg)
    for topo, n, d in matrix.graphs_of(cfg):
        meta = workloads.ensure_graph(topo, n, d, cfg.get("seed", 42))
        print("{graph_id}\tn={n}\tm={m}".format(**meta), flush=True)


def cmd_run(args):
    cfg = matrix.load_config(args.config)
    idx, count = _parse_shard(args.shard)
    shard_tag = "{}of{}".format(idx, count)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    raw = os.path.join(out, "runs_raw_{}.tsv".format(shard_tag))
    work = os.path.join(out, "outputs")
    logs = os.path.join(out, "logs")
    os.makedirs(work, exist_ok=True)
    os.makedirs(logs, exist_ok=True)
    check_tools(cfg)
    write_env(cfg, out, shard_tag)

    cells = matrix.shard(matrix.expand(cfg), idx, count)
    # a startup baseline per arm in every shard: small cells are startup-bound
    for tool in sorted({c["tool"] for c in cells}):
        cells.append({"group": "startup", "cmd": "startup", "tool": tool, "topology": "",
                      "n": 0, "d": "", "weighted": False, "k": "", "algorithm": "", "threads": 1})

    graphs = {}
    for c in cells:
        if c["cmd"] != "startup":
            key = (c["topology"], c["n"], c["d"])
            if key not in graphs:
                graphs[key] = workloads.ensure_graph(*key, seed=cfg.get("seed", 42))

    repeats = cfg.get("repeats", 3)
    long_s = cfg.get("long_cell_s", 120)
    long_reps = cfg.get("long_cell_repeats", repeats)
    done, censored = _read_done(raw)
    first_wall = {}
    if os.path.exists(raw):
        with open(raw) as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                if row["warmup"] == "1" and row["exit_status"] == "ok":
                    first_wall[row["run_id"]] = float(row["wall_s"])

    allowed = sorted(os.sched_getaffinity(0))
    slots = min(cfg.get("slots") or len(allowed), len(allowed))
    budget = cfg.get("mem_budget_mb") or int(0.85 * psutil.virtual_memory().total / 2 ** 20)
    state = {"step": 0, "running": 0, "reserved": 0}
    lock = threading.Condition()
    total = len(cells) * (repeats + 1)

    def reserve(mb):
        # a cell starts only if its expected footprint fits next to the ones
        # already running; the first one always starts, however big
        with lock:
            while state["reserved"] and state["reserved"] + mb > budget:
                lock.wait()
            state["reserved"] += mb
            state["running"] += 1
            return state["running"]

    def release(mb):
        with lock:
            state["reserved"] -= mb
            state["running"] -= 1
            lock.notify_all()

    def record(cell, run_id, rep, res, outdir, load):
        graph = graphs.get((cell["topology"], cell["n"], cell["d"])) or {}
        row = dict(cell)
        row.update(res)
        row.update({"run_id": run_id, "shard": shard_tag, "host": socket.gethostname(),
                    "graph_id": graph.get("graph_id", ""), "m": graph.get("m", ""),
                    "density": graph.get("density", ""), "rep": rep, "warmup": int(rep == 0),
                    "outdir": outdir, "concurrent": load,
                    "started_at": datetime.datetime.now().isoformat(timespec="seconds")})
        if graph:
            row["n"] = graph["n"]  # real size after the giant-component cut
        with lock:
            state["step"] += 1
            _append(raw, row)
            print("[{}/{}] rep{} {:<6} {:<9} {} -> {} {}s (x{})".format(
                state["step"], total, rep, cell["tool"], cell["cmd"], matrix.cell_key(cell),
                row.get("exit_status"), row.get("wall_s", ""), load), flush=True)

    def run_chain(chain, cpus):
        """One family, smallest n first: a timeout at n spares every larger n."""
        for cell in chain:
            fam = matrix.family_key(cell)
            run_id = matrix.cell_key(cell) + "#" + fam
            if cell["cmd"] != "startup" and fam in censored and cell["n"] >= censored[fam]:
                if (run_id, 0) not in done:
                    record(cell, run_id, 0, {"exit_status": "skipped"}, "", 0)
                continue
            for rep in range(repeats + 1):
                if (run_id, rep) in done:
                    continue
                if rep > 0 and run_id not in first_wall:
                    break  # warm-up failed: nothing to repeat
                if rep > long_reps and first_wall[run_id] > long_s:
                    break  # long cells: fewer repeats, noise is small next to the signal
                graph = graphs.get((cell["topology"], cell["n"], cell["d"]))
                outdir = os.path.join(work, cell["tool"], matrix.cell_key(cell).replace("|", "_"),
                                      "rep{}".format(rep))
                try:
                    argv = cli_map.build_argv(cell["tool"], cfg["tools"], cell, graph, outdir)
                except cli_map.Unsupported:
                    break
                shutil.rmtree(outdir, ignore_errors=True)
                os.makedirs(outdir)
                log_path = os.path.join(logs, "{}_{}_rep{}.log".format(
                    cell["tool"], matrix.cell_key(cell).replace("|", "_"), rep))
                need = min(cfg["mem_cap_mb"], _mem_estimate_mb(cell))
                load = reserve(need)
                try:
                    res = runner.run(argv, threads=cell["threads"], timeout_s=cfg["timeout_s"],
                                     mem_cap_mb=cfg["mem_cap_mb"], cwd=outdir, log_path=log_path,
                                     cpus=cpus)
                finally:
                    release(need)
                if res["exit_status"] == "ok" and rep > 0:
                    # only the warm-up's output is kept, for parity
                    shutil.rmtree(outdir, ignore_errors=True)
                    outdir = ""
                    os.remove(log_path)
                if rep == 0 and res["exit_status"] == "ok":
                    first_wall[run_id] = res["wall_s"]
                record(cell, run_id, rep, res, outdir, load)
                if res["exit_status"] in CENSORING and cell["cmd"] != "startup":
                    censored[fam] = min(cell["n"], censored.get(fam, 10 ** 12))
                    break

    chains = {}
    for c in cells:
        chains.setdefault(matrix.family_key(c), []).append(c)
    by_threads = {}
    for chain in chains.values():
        chain.sort(key=lambda c: c["n"])
        by_threads.setdefault(min(chain[0]["threads"], len(allowed)), []).append(chain)

    rng = random.Random("{}-{}".format(cfg.get("seed", 42), shard_tag))
    # one phase per thread count, widest first: every cell of a phase runs
    # next to cells of the same width only, and a whole-node cell runs alone
    for threads in sorted(by_threads, reverse=True):
        blocks = _cpu_blocks(allowed, threads, slots)
        order = by_threads[threads]
        rng.shuffle(order)  # old and new chains interleave in time
        print("phase threads={}: {} families on {} blocks {}".format(
            threads, len(order), len(blocks), blocks), flush=True)
        free = queue.Queue()
        for b in blocks:
            free.put(b)

        def worker(chain):
            cpus = free.get()
            try:
                run_chain(chain, cpus)
            finally:
                free.put(cpus)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(blocks)) as pool:
            for fut in [pool.submit(worker, ch) for ch in order]:
                fut.result()
    # the step counter's total assumes every repeat of every cell runs; censored
    # and failed cells never do, so say explicitly that the shard is complete
    print("shard {} complete: {} rows written this run".format(shard_tag, state["step"]), flush=True)


def _cpu_blocks(allowed, threads, slots):
    """Disjoint CPU sets of `threads` CPUs, at most `slots` CPUs in total,
    spread over the allowed range so that concurrent cells land on different
    cores/sockets rather than on neighbouring (possibly SMT-sibling) CPUs."""
    width = max(1, min(slots, len(allowed)) // threads)
    stride = len(allowed) // width
    return [allowed[i * stride:i * stride + threads] for i in range(width)]


def _mem_estimate_mb(cell):
    """Expected peak of one cell, used only to decide how many run together
    (the hard per-cell cap is mem_cap_mb). Calibrated on the local pilot: the
    new tool's `global` went past 6 GB at n = 10,000, i.e. about 8 dense
    n x n float64 matrices."""
    n = cell["n"] or 0
    return 512 + 8 * 8 * n * n // 2 ** 20


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="action", required=True)
    p = sub.add_parser("plan"); p.add_argument("config"); p.add_argument("--shards", type=int, default=1)
    p = sub.add_parser("prepare"); p.add_argument("config")
    p = sub.add_parser("run"); p.add_argument("config"); p.add_argument("--shard", default="0/1")
    p.add_argument("--out", required=True)
    p = sub.add_parser("collect"); p.add_argument("out")
    p = sub.add_parser("parity"); p.add_argument("out")
    args = ap.parse_args()
    if args.action == "plan":
        cmd_plan(args)
    elif args.action == "prepare":
        cmd_prepare(args)
    elif args.action == "run":
        cmd_run(args)
    elif args.action == "collect":
        import collect
        collect.main(args.out)
    elif args.action == "parity":
        import parity
        parity.main(args.out)


if __name__ == "__main__":
    main()
