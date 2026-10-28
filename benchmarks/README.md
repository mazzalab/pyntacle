# Benchmark: Pyntacle 2.0 against Pyntacle 1.3.2

This directory runs both versions of Pyntacle from the command line on the
same synthetic networks and measures wall time, CPU time and peak memory of
every run. It also checks that the two versions give the same results. It
produces Table 1 and Supplementary Figs S2–S9 of the Pyntacle 2.0 paper.

Pyntacle 1.3.2 has no weighted shortest paths, so weighted networks are run
with Pyntacle 2.0 only. Only the unweighted runs compare the two versions.

## Contents

| Path | What it is |
|---|---|
| `run.sh` | runs everything: setup, benchmark, tables, figures |
| `setup.sh`, `env.sh` | conda environments and the paths of the two versions |
| `bench.py` | driver: `plan`, `prepare`, `run`, `collect`, `parity` |
| `matrix.py` | expands a config into cells and splits them into shards |
| `cli_map.py` | the command line of each version for each cell |
| `workloads.py` | generates the networks (fixed seed) |
| `runner.py` | runs one command and measures it |
| `collect.py`, `parity.py` | summary tables and the comparison of results |
| `plot_results.py`, `plot_threads.py`, `figstyle.py` | the figures |
| `configs/` | `paper.json`, `paper-threads.json` (the paper), `smoke.json` (a quick check) |
| `data/` | the networks of the three configs, as SIF files |
| `results/paper/`, `results/paper-threads/` | the measurements behind the paper |

## Requirements

- Linux and [conda](https://docs.conda.io/en/latest/miniconda.html).
- Nothing else: the first call of `run.sh` creates two conda environments,
  `pyntacle` from this repository's `environment.yml` and `pyntacle_old` with
  Pyntacle 1.3.2 from the `bfxcss` channel (Python 3.7).

## Usage

From the root of the repository:

```bash
bash benchmarks/run.sh figures          # the paper's tables and figures from the shipped results
bash benchmarks/run.sh smoke            # both versions on networks of 40-120 nodes, a few minutes
bash benchmarks/run.sh paper            # Table 1 and Supplementary Figs S2-S7
bash benchmarks/run.sh paper-threads    # Supplementary Figs S8-S9
```

`figures` runs nothing: it rebuilds the tables and figures from
`results/paper/` and `results/paper-threads/`. The other three run the
benchmark and write to `results/local/<profile>/`, so the shipped results
are never overwritten. A run that is interrupted continues where it stopped
when it is started again.

The first call runs `setup.sh`, which:

- creates the two conda environments if they do not exist;
- compiles the extensions of Pyntacle 2.0 in place;
- generates any network that is not yet in `data/`;
- writes `results/.setup_ok`.

`env.sh` points the benchmark at the two installations:

- `PYNTACLE_PYTHON` is the Python of the Pyntacle 2.0 environment.
- `PYNTACLE_OLD_BIN` is the `pyntacle` command of version 1.3.2.

The environment names can be changed with `PYNTACLE_ENV` and
`PYNTACLE_OLD_ENV`. Other installations can be used by exporting the two
paths before calling `run.sh`.

## Running the paper's benchmark

Use a machine with nothing else running on it: every run is timed, so other
load changes the results.

| Profile | CPUs | Memory | Run time |
|---|---|---|---|
| `paper` | 8 | 48 GB | the runs add up to 216 h on one CPU, about 1–2 days on 8 |
| `paper-threads` | 16 | 16 GB | the runs add up to 40 h |

How runs are scheduled:

- At most `slots` CPUs of the config are busy at once. To use fewer, start
  `run.sh` under `taskset -c`, for example `taskset -c 0-7`.
- A run starts only if its expected memory fits within `mem_budget_mb`.
- Each run stops at `timeout_s` (1 h) or `mem_cap_mb`. When a run stops, the
  larger networks of the same series are skipped.
- `run.sh` warns when the machine has fewer CPUs or less memory than the
  profile uses.

The runs can also be split over several machines of the same CPU model with
`bench.py`:

```bash
source benchmarks/env.sh
cd benchmarks
"$PYNTACLE_PYTHON" bench.py plan configs/paper.json --shards 2
"$PYNTACLE_PYTHON" bench.py run configs/paper.json --shard 0/2 --out results/local/paper   # first machine
"$PYNTACLE_PYTHON" bench.py run configs/paper.json --shard 1/2 --out results/local/paper   # second machine
```

Copy the `runs_raw_*.tsv` files of all shards into one directory, then run
`collect`, `parity` and the plotting scripts on it.

## Tables and figures

`collect` writes `summary.tsv`, `scaling.tsv` and `capability.tsv`. `parity`
writes `parity.tsv`, from the output files of the runs. The figures go to
`plots/`:

| File in `plots/` | Paper |
|---|---|
| `5_speedup_heatmap` | Supplementary Fig. S2 |
| `1_metrics_scaling` | Supplementary Fig. S3 |
| `2_memory` | Supplementary Fig. S4 |
| `6_density` | Supplementary Fig. S5 |
| `3_bruteforce` | Supplementary Fig. S6 |
| `4_greedy` | Supplementary Fig. S7 |
| `T1_strong_scaling` | Supplementary Fig. S8 |
| `T2_bruteforce_16_threads` | Supplementary Fig. S9 |

## Results of the paper

`results/paper/` and `results/paper-threads/` hold the measurements behind the
paper:

- `runs_raw_merged.tsv` has one row per run.
- `env_metadata.tsv` records the machines and the software versions.
- The tables are written by `collect` and `parity`.

`bash benchmarks/run.sh figures` rebuilds the tables and figures from
`runs_raw_merged.tsv`. `parity.tsv` was computed from the output files of the
runs, which are not included: run the benchmark again to recompute it.

The published runs used:

- Compute nodes with Intel Xeon Gold 6240 CPUs (32 cores available) and 503 GB
  of RAM. The host names are anonymised.
- Pyntacle 1.3.2 with Python 3.7, python-igraph 0.8.3 and NumPy 1.21.
- Pyntacle 2.0.0 with Python 3.10, python-igraph 0.10.8 and NumPy 2.2.

## Networks

`workloads.py` generates three kinds of network:

- Erdős–Rényi (`er`);
- Barabási–Albert (`ba`);
- Watts–Strogatz (`ws`), with rewiring probability 0.1.

Each network has `n` nodes and seed 42. It is reduced to its largest connected
component and written as SIF. The `d` of a file name is the number of edges
added per node, so the mean degree is 2d. A second file (`_w.sif`) has the same
edges with weights drawn from Uniform(0.1, 1.0). A JSON file next to each
network records its real size after the reduction.
