# Benchmark design: GraphTacle (new) vs Pyntacle 1.3.2 (old)

Date: 2026-09-03
Status: design, awaiting approval
Owner: Manuel

## 1. Purpose

Produce the performance-assessment section of the paper: a tool-level,
end-to-end comparison of the rewritten GraphTacle CLI against the released
Pyntacle 1.3.2 CLI, on the axes a user actually feels — time to result, peak
memory, CPU utilisation, parallel scaling, and where each tool stops being
usable at all.

The deliverable of this work is **tables (TSV)**. Plots are made by the user
from those tables. The harness never draws anything.

## 2. Claims the benchmark must support (or refute)

1. New is faster than old for the same command, same input, same result.
2. New uses less peak memory, and stays usable on graph sizes where old dies
   (timeout / OOM).
3. New parallelises better (`-np`) than old (`-O`).
4. New covers analyses old cannot do at all (percolation, mesoscale, extract).

Claim 1 is void unless the two tools produce the same numbers. Result parity
is therefore part of the measurement, not an afterthought.

## 3. Scope

**In scope** — commands present in both tools:
`local`, `global`, `keyplayer kp-info`, `keyplayer kp-finder`,
`groupcentrality gc-info/gr-info`, `groupcentrality gc-finder/gr-finder`,
`communities`, `set`, `convert`.

**Out of scope, reported as a capability table only** (new-only):
`percolation`, `mesoscale`, `extract`, interactive D3 HTML reports.

**Deferred to v2**: py-spy call-stack hotspot tables ("why is it faster").
The harness leaves a hook for it but v1 does not implement it.

## 4. Tools under test

| arm | what | environment |
|---|---|---|
| `old` | Pyntacle 1.3.2, entry point `pyntacle` | conda env `pyntacle_old`, python 3.7 |
| `new` | GraphTacle working tree, entry point `python3 pyntacle/main.py` | conda env `graphtacle_debug`, python 3.10, Cython ext built in-place |
| `new-py` | same tree, `--engine python` | same env; isolates the gain owed to the compiled kernels |

`old` install order: (1) `conda create -n pyntacle_old python=3.7` +
`conda install -c conda-forge -c bfxcss pyntacle=1.3.2`; (2) if the `bfxcss`
channel no longer resolves, fall back to a `git worktree` of commit `478dfe7`
with pinned deps (python-igraph 0.8.x, numpy, numba, psutil, colorama,
seaborn). Whichever path is used is recorded in `env_metadata.tsv`.

The two arms never share a process. Every measurement is a subprocess launched
by the harness with an explicit interpreter path.

## 5. CLI mapping

Flags collide between versions and the collisions are silent, not fatal — in
old, `-t` is the *metric type* and `-f` the *input format*; in new, `-t` is the
*input format* and `-f` the *figure format*. A single mapping module owns this
translation so no cell is ever built by hand.

| operation | old | new |
|---|---|---|
| local metrics | `pyntacle metrics local -f edgelist -i G -d OUT --no-plot -r txt` | `main.py local -t edgelist -i G -o OUT` |
| global metrics | `pyntacle metrics global -f edgelist -i G -d OUT --no-plot` | `main.py global -t edgelist -i G -o OUT` |
| kp-info | `pyntacle keyplayer kp-info -t {F,dF,dR,mreach} -n NODES -O P -M d -m d` | `main.py keyplayer kp-info -oper {F,dF,dR,mreach} -n NODES -np P -m d` |
| kp-finder | `pyntacle keyplayer kp-finder -k K -I {brute-force,greedy,sgd} -O P` | `main.py keyplayer kp-finder -k K -a {brute_force,greedy,gradient_descent} -np P` |
| gc info | `pyntacle groupcentrality gr-info -n NODES -D {min,max,mean}` | `main.py groupcentrality gc-info -n NODES -v {min,max,mean}` |
| gc finder | `pyntacle groupcentrality gr-finder -k K -I ... -O P` | `main.py groupcentrality gc-finder -k K -a ... -np P` |
| communities | `pyntacle communities <algo> ...` | `main.py communities <algo> ...` |
| set ops | `pyntacle set {union,intersection,difference}` | `main.py set {union,intersection,difference}` |
| convert | `pyntacle convert -f X -u Y` | `main.py convert -t X -to Y` |

Defaults that differ (tolerance, max distance, sgd max seconds, greedy seed)
are pinned explicitly on both sides. Nothing is left to a default.

## 6. Fairness rules

These are the rules that decide whether the numbers are publishable.

1. **Same input file on disk.** Graphs are generated once into
   `benchmarks/data/`, in a format both tools parse (edge list), and reused.
   Never generated inside a timed run.
2. **Thread environment pinned on both arms.** `OMP_NUM_THREADS`,
   `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `NUMEXPR_NUM_THREADS` are set to
   the cell's thread count for every run. Otherwise numpy silently grabs every
   core in one arm and not the other.
3. **GPU disabled.** Old imports `numba.cuda`; the run is CPU-vs-CPU, so CUDA
   is masked (`CUDA_VISIBLE_DEVICES=""`, `NUMBA_DISABLE_CUDA=1`). A GPU arm, if
   wanted, is a separate table.
4. **Report generation symmetric.** Both arms run with `--no-plot`: the flag
   exists in old, and is added to the new CLI as a prerequisite of phase 3
   (Open decision 1, resolved). Result TSVs are still written — they are what
   parity is checked on.
5. **Interleaved, randomised order.** Cells are executed old/new alternating
   and shuffled within a replicate, never all-old-then-all-new — otherwise
   thermal drift is indistinguishable from a speedup.
6. **Repetitions.** 1 discarded warm-up + R measured runs (R=3 local pilot,
   R=5 HPC). Reported statistic is the median with MAD; mean is not used.
7. **Isolation.** HPC runs go through an exclusive job; cores pinned with
   `taskset`/`numactl`. The local pilot is explicitly labelled indicative and
   never feeds a published figure.
8. **Hard limits.** Per-cell wall timeout and address-space cap (`ulimit -v`
   or a cgroup) so that "old dies here" is a deterministic, recorded outcome
   rather than a swapping machine.

## 7. Measurements per run

| field | source |
|---|---|
| wall_s | `time.perf_counter()` around the subprocess |
| cpu_user_s / cpu_sys_s | `resource.getrusage(RUSAGE_CHILDREN)` delta |
| max_rss_mb | `ru_maxrss` and the psutil sampler max, whichever is larger |
| peak_cpu_pct / mean_cpu_pct | psutil sampler over the whole process tree, 100 ms period |
| read_bytes / write_bytes | psutil `io_counters` (best effort; blank where unsupported) |
| exit_status | `ok` / `timeout` / `oom` / `crash` |
| output_hash | sha256 of the normalised result TSV |

Derived in `summary.tsv`: `speedup = median(wall_old)/median(wall_new)`,
`rss_ratio`, `cpu_efficiency = cpu_total/(wall × threads)`,
parallel `speedup(p) = t(1)/t(p)` and `efficiency(p) = speedup(p)/p`.

Failed cells are censored data, kept in the tables with their status, never
dropped.

## 8. Sweep design

Two profiles, same harness, one config file each. Both cross every cell with
a **weighted axis** — `weighted ∈ {False, True}` — for the four commands
where edge weights change the algorithm actually run (`local`, `global`,
`keyplayer`, `groupcentrality`: unweighted local/global metrics take a BFS
shortest-path, weighted ones take Dijkstra; keyplayer/groupcentrality's dR
and closeness-family operations branch on distance type the same way).
`communities`, `set`, `convert` get a single unweighted cell each — none of
their algorithms consume edge weights, so a weighted cell would just remeasure
graph-loading overhead under a different label. Weighted graphs reuse the same
generated topology with i.i.d. `Uniform(0.1, 1.0)` edge weights (workloads.py,
phase 2) so a weighted/unweighted pair is the same graph in every way that
isn't the weight itself — the comparison isolates the algorithmic branch, not
a confound from a different random graph.

**Profile `local-pilot`** — this machine (20 cores, 23 GB, WSL2). Purpose:
shake out the harness, get an order-of-magnitude picture, find where old dies.
Not for publication.

- sizes: n ∈ {100, 500, 1000, 2000}, ER with m = 3n
- density: at n = 500, also m ∈ {10n} (one extra density point, cheap enough
  to run locally; the full density sweep is `hpc-paper`'s job)
- weighted: {False, True} (see above; local/global/keyplayer/groupcentrality only)
- commands: `local`, `global`, `kp-info`, `kp-finder` (k=2, brute-force + greedy), `gc-finder` (k=2), `convert`
- threads: {1, 4}
- R = 3, timeout 600 s, memory cap 8 GB

**Profile `hpc-paper`** — compute node, exclusive job. Purpose: the numbers in
the paper.

- sizes: n ∈ {100, 500, 1k, 5k, 10k, 25k, 50k}, ER m = 3n
- density: n = 2000 fixed, m ∈ {3n, 10n, 50n}
- weighted: {False, True} (see above)
- topology: ER, Barabási–Albert, Watts–Strogatz, plus 2–3 real networks (PPI/STRING subset)
- k ∈ {2, 3, 4} for both finders, algorithms {brute_force, greedy, gradient_descent}
- threads: {1, 2, 4, 8, 16, 32} on 2–3 fixed cells
- engine arm: `new` vs `new-py` on the mid-size cells
- R = 5, timeout 3600 s, memory cap set from node RAM

**Format-coverage cell (both profiles, one-off, not crossed into the sweep).**
§15's decision made SIF the sweep's format for every timed cell — repeating
the full n × density × weighted × k × threads matrix four times over (matrix,
edgelist, sif, dot) would multiply run count for a question that has nothing
to do with algorithm performance. Instead: one fixed graph (n = 500, ER,
unweighted), all four formats, both tools, single rep. This is the cell that
satisfies "every format gets run at least once" — it lands in `parity.tsv` and
`capability.tsv` (does the format parse, does it parse to the same graph — old's
reciprocal-edgelist requirement included), not in the timing tables.

## 9. Output tables

All TSV, written under `benchmarks/results/<profile>/`.

| file | one row per | key columns |
|---|---|---|
| `runs_raw.tsv` | single execution | run_id, tool, tool_version, cmd, subcmd, graph_id, n, m, density, topology, weighted, fmt, k, oper, algorithm, engine, threads, rep, wall_s, cpu_user_s, cpu_sys_s, max_rss_mb, peak_cpu_pct, mean_cpu_pct, read_bytes, write_bytes, exit_status, output_hash, started_at |
| `summary.tsv` | cell (everything but rep) | n, m, density, topology, weighted, k, oper, algorithm, threads, n_rep, wall_median, wall_mad, wall_min, wall_max, rss_median, cpu_eff, speedup_vs_old, rss_ratio_vs_old, status_summary |
| `scaling.tsv` | cell × threads | n, oper, weighted, threads, wall_median, speedup_p, efficiency_p |
| `parity.tsv` | comparable cell | same_result (yes/no/na), max_abs_delta, max_rel_delta, notes |
| `capability.tsv` | feature | feature, old (yes/no), new (yes/no), notes |
| `env_metadata.tsv` | machine × arm | host, cpu_model, cores, ram_gb, kernel, python, igraph, numpy, tool_version, commit, install_path, governor, date |

`runs_raw.tsv` is append-only; a cell already present is skipped on restart, so
a multi-hour sweep survives interruption.

## 10. Harness layout

```
benchmarks/
  configs/local-pilot.yaml
  configs/hpc-paper.yaml
  workloads.py     # generate + cache graphs, deterministic seeds
  cli_map.py       # old/new flag translation, the single source of truth
  runner.py        # run one cell: subprocess + psutil sampler + rusage + limits
  matrix.py        # expand a config into cells, shuffle, interleave arms
  collect.py       # runs_raw.tsv -> summary.tsv, scaling.tsv
  parity.py        # normalise + compare result files across arms
  results/
  data/
```

Design constraints: `runner.py` knows nothing about pyntacle (it runs an argv
and measures it); `cli_map.py` is the only file that knows both CLIs; nothing
imports either tool in-process.

## 11. Phases

1. **Feasibility gate** — build `pyntacle_old`, run one small graph through
   both arms, confirm the outputs agree. If they do not agree, stop and
   explain the divergence before any timing work.
2. Workload generator + cached graph corpus.
3. `cli_map.py` + `runner.py` with the measurement fields of §7.
4. `matrix.py` + config profiles; run `local-pilot` end to end.
5. `collect.py` + `parity.py`; produce the six tables for the pilot.
6. Review the pilot tables, fix the sweep ranges (drop cells that are
   pointless, add the ones where old dies).
7. Port to the HPC node, run `hpc-paper`, deliver the final tables.

## 12. Open decisions

1. ~~Report generation asymmetry.~~ **DONE 2026-09-03.** `--no-plot` added to
   every new-tool subcommand that plots (`local`, `global`, `groupcentrality`,
   `keyplayer`, `set`, `communities`, `extract`, `mesoscale`, `percolation`);
   `convert`/`generate` never plotted, so they were left alone. TSV report is
   unaffected — that is the benchmark's parity data. 11 new tests
   (`tests/test_no_plot.py`); full suite 222 passed, 7 skipped. Docs updated
   for all nine subcommands, Sphinx rebuild clean.
2. **Real networks.** Which ones, and where do the files come from. Still open.
3. ~~Old-tool source.~~ **DECIDED at the gate: the conda package.** See §14.
4. ~~Format coverage.~~ **DECIDED 2026-09-03.** Every format gets run at least
   once, but not swept — see the format-coverage cell in §8.

## 13. Risks

- `bfxcss` conda channel dead → worktree fallback (planned, not a blocker).
- Old and new disagree numerically on some metric → parity table turns from a
  formality into a finding; timing for that metric is reported separately with
  the divergence stated.
- WSL2 timings are noisy → pilot only, never published.
- Brute-force finder cells at k≥3 explode combinatorially → timeout policy is
  what makes them a result instead of a hang.

## 14. Phase 1 — feasibility gate results (2026-09-03, this machine)

**Verdict: passed.** Both arms run, on the same graph, and agree numerically.

Environment: `conda create -n pyntacle_old -c conda-forge -c bfxcss python=3.7
pyntacle=1.3.2` resolved and installed (`pyntacle 1.3.2 py37hd844fa7_0`, bfxcss).
The git-worktree fallback is not needed. Open decision 3 is closed: use the
conda package.

Workload: ER n=50, m=150, seed 42, single component,
`benchmarks/data/smoke_er_n50_m150.txt`.

### Findings that change the design

1. **Old refuses a single-direction edge list.** `ValueError: Edgelist is not
   ready to be parsed by Pyntacle, it's direct.` Old requires every edge listed
   in both directions; new accepts either. Consequence: the corpus stores two
   files per graph, generated from the same seeded igraph object — `*.txt`
   (one direction, for new) and `*_recip.txt` (both directions, for old). The
   harness asserts that the two tools report the same node and edge counts
   before any timing is kept. Both arms then pay only their own parse cost,
   which is what we want to measure. This is also a usability finding for the
   paper: old needs a preprocessing step new does not.
2. **New rounds report values to 3 decimals**, old writes 5. For the local
   metrics table this is the report writer. For the finder score it was the
   kernel itself (`round(max_score, 3)` on the way out of `cython_bruteforce`),
   which threw precision away before anything could ask for it — **now removed**,
   see §15. Parity tolerance stays 1e-3 absolute for the tables that are still
   rounded at write time.
3. **Eigenvector centrality is normalised differently.** New reports
   "Eigenvector (Scaled)" with max = 1.0; old reports the unscaled vector. The
   two are proportional (ratio constant to within 0.6% across all 50 nodes), so
   parity for this column compares vectors after rescaling both to max = 1.
4. **kp-finder result shape differed.** Old enumerates every optimal set (50
   sets at k=2 on this graph, all scoring 0.04167); new reported one and dropped
   the rest. **Fixed in the new tool** (§15), so parity now compares the full
   optimal-set family, not just the score. Verified on the smoke graph: both
   tools return the same 50 sets, `old_sets == new_sets`.
5. **Startup cost is not negligible and is asymmetric**, so small-n cells are
   dominated by it:

   | arm | startup wall (3 runs) | startup peak RSS |
   |---|---|---|
   | old (`pyntacle --version`) | 0.95 / 0.95 / 0.96 s | ~214 MB |
   | new (`main.py --help`) | 0.48 / 0.45 / 0.50 s | ~105 MB |

   The harness therefore measures a **startup baseline cell per arm** in every
   session, records it in `runs_raw.tsv` like any other cell, and `summary.tsv`
   carries both raw wall time and startup-subtracted compute time. Without it,
   an n=50 cell reads as "both tools take 1 s" when in fact neither is
   computing anything.

### Parity measured (local metrics, n=50)

degree, betweenness, closeness, radiality, radiality reach, clustering
coefficient, eccentricity, pagerank: max absolute difference ≤ 5e-4, i.e.
rounding only. Eigenvector: proportional, see finding 3.

kp-finder (brute force, F, k=2): old 0.04167, new 0.042, same optimal set
family. Wall time at this size is startup-bound for both arms (~1.0 s each).


## 15. Changes made to the new tool during the gate (2026-09-03)

The gate is a comparison, and two of its findings were defects on the new side.
Both are fixed rather than documented as differences.

1. **Brute force now reports every optimal set.** `cython_metrics.pyx` kept one
   winning index per worker, so ties — the normal case on symmetric networks —
   were invisible. Each worker now keeps the indices sitting at its own best
   score, capped, plus an uncapped counter; the reduction merges the workers that
   reached the global optimum. Cost is one extra comparison per candidate; the
   per-candidate perf tests are unchanged (F: 0.78 / 0.98 / 1.80 µs at n = 50 /
   100 / 200, budgets 3 / 5 / 10).
   - TSV reports gain a `SetID` column and an `Optimal sets	N (showing M)`
     header line.
   - Both HTML reports gain a set selector next to the metric selector, and say
     how many sets reach the score.
   - New optional flag `--max-ties` (default 100) on `keyplayer` and
     `groupcentrality`. Heuristic searches ignore it.
   - Covered by `tests/test_tied_sets.py` (14 tests); full suite 211 passed,
     7 skipped.
2. **The kernel no longer rounds the score to 3 decimals.** Rounding happens at
   report time, so the comparison against old Pyntacle's 5 decimals is no longer
   limited by the new tool's own output.

### Input format decision

SIF is the benchmark's primary format: the *same file*, one direction, is
accepted by both tools and yields the same graph and the same metrics
(verified — 50 nodes, 150 edges, all local metrics equal within rounding on both
arms). Edge list keeps a dedicated cell of its own, where old's reciprocal-file
requirement is measured as the usability and I/O cost it is, instead of
contaminating every timing.
