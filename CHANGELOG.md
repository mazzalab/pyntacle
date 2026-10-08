# Changelog

## 2.0.0

Pyntacle 2.0 is a rewrite of Pyntacle 1.3.2. The command line is new: commands
and flags written for 1.3.2 do not run unchanged, and some single-letter flags
now mean something else (see [Flags that changed meaning](#flags-that-changed-meaning)).
A few metrics also give different values; they are listed under
[Results that differ from 1.3.2](#results-that-differ-from-132).

### Results that differ from 1.3.2

Values reported for the same network can differ from 1.3.2 in these cases. On
unweighted networks, the other metrics match 1.3.2 up to rounding.

| Metric | 1.3.2 | 2.0 |
|---|---|---|
| Group betweenness | divided by the ordered pairs of nodes outside the set, (N−k)(N−k−1): the centre of a star scored 0.5 | divided by the unordered pairs (Everett and Borgatti): the centre of a star scores 1. Every value is twice the 1.3.2 one; the best sets are the same |
| Group closeness, network with several components | could favour a set inside a small component | scaled by the share of nodes the set reaches (Wasserman and Faust); same values on a connected network |
| Radiality, network with several components | a node it cannot reach counted as if at distance 0, so an isolated node scored highest | only the nodes it reaches count, so an isolated node scores 0; same values on a connected network |
| Closeness of an isolated node | NaN | 0 (also in Average Closeness) |
| Average shortest path length, network with several components | a pair that cannot reach each other counted as if at distance N | average over the pairs that reach each other |
| Global clustering coefficient | reported as "Weighted clustering coefficient", although it never used weights | renamed; 0 instead of NaN when the network has no triples |
| Average clustering coefficient | NaN when no node has degree 2 or more | 0 in that case; otherwise unchanged |
| Report precision | 5 decimals | 3 decimals; values below 0.1 keep 3 significant digits |

Edge weights also change results, because 1.3.2 ignored them in most metrics:
see [Edge weights](#edge-weights).

### Commands

| 1.3.2 | 2.0 |
|---|---|
| `pyntacle metrics local` | `pyntacle local` |
| `pyntacle metrics global` | `pyntacle global` |
| `pyntacle keyplayer kp-info` / `kp-finder` | unchanged |
| `pyntacle groupcentrality gr-info` / `gr-finder` | `pyntacle groupcentrality gc-info` / `gc-finder` |
| `pyntacle communities community-walktrap` | `pyntacle communities random-walk` |
| `pyntacle communities fastgreedy` / `infomap` / `leading-eigenvector` | unchanged |
| `pyntacle generate random` / `small-world` / `scale-free` / `tree` | `pyntacle generate erdos-renyi` / `watts-strogatz` / `barabasi` / `tree` |
| `pyntacle set union` / `intersection` / `difference` | unchanged |
| `pyntacle convert` | unchanged |
| `pyntacle test` | removed: run `pytest tests` from the repository |

New commands:

- `mesoscale`: generalised topological overlap (GTOM) and topological importance.
- `percolation`: spreading dynamics with per-edge thresholds, with an interactive report.
- `extract`: keep the largest components, the N-th largest, or the components that contain given nodes.
- `omics`: build networks from RNA-seq counts or microbiome abundances.
- `communities percolation`: clique percolation.
- `generate lattice`: regular lattices.

### Flags

| 1.3.2 | 2.0 |
|---|---|
| `-i`, `--input-file` | `-i`, `--inputFile` |
| `-f`, `--format` (input format) | `-t`, `--fileType`: `matrix`, `edgelist`, `sif`, `dot` |
| `--input-separator` | `-s`, `--sep` |
| `-N`, `--no-header` | `-nh`, `--NoHeader` |
| `-d`, `--directory` | `-o`, `--outdir` |
| `-t`, `--type` (keyplayer: `pos`, `neg`, `all`, `F`, `dF`, `dR`, `mreach`) | `-oper`, `--operation`: `all`, `F`, `dF`, `dR`, `mreach` |
| `-t`, `--type` (groupcentrality) | `-oper`, `--operation`: `all`, `degree`, `closeness`, `betweenness` |
| `-D`, `--group-distance` | `-v`, `--value`: `min`, `max`, `mean` |
| `-m`, `--m-reach` (required for m-reach) | `-m`, `--mdist` (default 2) |
| `-I`, `--implementation`: `brute-force`, `greedy`, `sgd` | `-a`, `--algorithm`: `brute_force`, `greedy`, `gradient_descent` |
| `-O`, `--nprocs` | `-np`, `--nprocs` |
| `-P`, `--swap-probability` | `-p`, `--probability` |
| `-T`, `--tolerance` | `-tol`, `--tolerance` |
| `-x`, `--maxsec` | `-ms`, `--maxsec` |
| `-L`, `--largest-component` | `communities -g`, or `extract -l` before any other command |
| `metrics global -n`, `--no-nodes` | `-r`, `--remove` on every command |
| `set -1`, `-2` | `set -i`, `-i2` |
| `convert -u`, `--output-format` | `convert -to`, `--typeOutput` |
| `convert -o`, `--output-file` | `convert -fo`, `--outputName` |
| `communities --min-nodes -m`, `--max-nodes -M` | `-n`, `--minNodes`; `-N`, `--maxNodes` |
| `communities --clusters` | `-nc`, `--numberCommunities` |
| `generate -R`, `--repeat` | removed |

New flags on the analysis commands:

- `-w`, `-wt`, `-dt`: read edge weights from the network file and say how to read them (see [Edge weights](#edge-weights)).
- `-d`, `--directed`: read the network as directed.
- `-r`, `--remove`: remove nodes before the analysis.
- `--engine {cython,python}`: compiled kernels (default) or the pure-Python implementation.
- `--seed`: repeatable greedy, gradient-descent and percolation runs. Without it, the drawn seed is printed.
- `--max-ties`: how many tied optimal sets a brute-force search lists (default 100); the report always gives the full count.
- `-f`, `--format`: figure format (`svg`, `png`, `pdf`, `ps`, `eps`).

### Flags that changed meaning

These letters exist in both versions with a different meaning:

| Flag | 1.3.2 | 2.0 |
|---|---|---|
| `-t` | metric type | input format |
| `-f` | input format | figure format |
| `-d` | output directory | read the network as directed |
| `-r` | report format | nodes to remove |
| `-v` | log verbosity | groupcentrality: group distance (`min`, `max`, `mean`); `-v`/`--version` at top level |
| `-o` | output file name (convert, generate, communities, set) | output directory |
| `-n` | node set (info), node subset (local), nodes to remove (global) | node set (info, percolation); minimum community size (communities); components to keep (extract); nodes (generate) |

### Defaults that changed

- `kp-finder` and `gc-finder` default to `brute_force` (1.3.2: `greedy`). Brute force is exact but scores every set of size k; pass `-a greedy` on large networks.
- `-m` defaults to 2 (1.3.2 required it for m-reach).

### Edge weights

- 1.3.2 read weights from a separate attribute file (`--weights`, `--weights-format`) and used them only in PageRank and in fastgreedy and walktrap communities.
- 2.0 reads them from the third column of the network file (`-w`). Every metric that can use weights does: shortest-path metrics, key-player indices, group centrality, clustering, PageRank, eigenvector centrality, communities, topological importance (mesoscale) and percolation thresholds.
- `-wt` declares what the weights mean: `distance` (default), `affinity` or `signed`. `-dt` sets how affinities become distances: `inverse` (default), `one-minus` or `neglog`.
- Negative weights are refused unless declared `signed`; they are never turned into absolute values.

### Removed

- Binary `.graph` input and `--save-binary`.
- Report formats `txt`, `csv` and `xlsx` (`-r`, `--report-format`). Every report is a TSV file.
- Separate attribute files (`--weights`, `--weights-format`).
- `-M`, `--max-distance` (keyplayer).
- `local -n` (node subset): `local` reports every node; use `-c` to highlight nodes in the figure.
- `--damping-factor`: PageRank uses 0.85.
- `--suppress-cursor`, and `-v` as log verbosity.
- GPU shortest paths.
- The Dockerfile.

### Reports and output

- Every report is a TSV file. Next to it, unless `--no-plot` is given, there is a figure and, for `local`, `keyplayer`, `groupcentrality` and `percolation`, an interactive HTML report. These replace PyntacleInk.
- A brute-force search lists every tied optimal set (up to `--max-ties`) and reports how many there are.
- Every output goes into `-o`, which is created if missing. Each written file is named on screen.
- `set` and `extract` write networks in the input format.

### Performance

- Key-player and group-centrality searches run in compiled Cython kernels with OpenMP threads (`-np`). The kernels read the network as an edge list, so memory grows with the number of edges, not with N².
- All-pairs distances for `local` and `global` are built in blocks, using breadth-first search when every weight is 1.
- Group betweenness counts shortest paths instead of listing them.

### Installation

- Pip-installable package with a `pyntacle` command; `environment.yml` provides Python 3.10, igraph 0.10 and a C compiler (1.3.2: Python 3.7).
- Licence: GPL-3.0.
