# Pyntacle

Pyntacle is a command-line toolkit for network analysis. It finds the groups
of nodes that matter most in a network — key players and central groups — and
computes local, global and mesoscale metrics, communities and percolation
dynamics. The `omics` command builds the networks themselves from raw
transcriptomics or microbiome data. The compute-heavy searches run in
parallel, compiled code.

## Features

| Command | What it does |
|---|---|
| `local`, `global` | node-level and whole-network metrics |
| `keyplayer` | key-player indices (F, dF, dR, m-reach) for a node set, or the best set of size *k* (brute force, greedy, gradient descent) |
| `groupcentrality` | group degree, closeness and betweenness, or the best group of size *k* |
| `mesoscale` | topological overlap (GTOM) and topological importance |
| `communities` | fastgreedy, infomap, leading eigenvector, random walk, percolation |
| `percolation` | spreading dynamics with per-edge thresholds, with an interactive report |
| `omics` | association networks (partial correlations) from RNA-seq counts or microbiome abundances |
| `set`, `convert`, `extract`, `generate` | set operations between networks, format conversion, components, random graphs |

Edge weights can be declared as distances, affinities or signed associations:
each metric reads the view it needs.

## Installation

Pyntacle runs on Linux and needs [conda](https://docs.conda.io/en/latest/miniconda.html),
which provides igraph's C library for the compiled extensions.

```bash
git clone https://github.com/mazzalab/pyntacle.git
cd pyntacle
conda env create -f environment.yml
conda activate pyntacle
pip install .
pyntacle --help
```

## Quick start

From the root of the repository:

```bash
# per-node metrics
pyntacle local -t edgelist -i examples/figure_8.egl -o out/

# the best pair of key players for every index, greedy search
pyntacle keyplayer kp-finder -t edgelist -i examples/figure_8.egl -k 2 -oper all -a greedy -o out/

# one network per sample group from microbiome abundances, then its key players
pyntacle omics metagenomics -i relabund.tsv -m samples.tsv --group-col condition -o nets/
pyntacle keyplayer kp-finder -t edgelist -w -wt signed -i nets/relabund_tumor.tsv -k 2 -oper all -a greedy -o kp/
```

Every analysis writes a TSV report and, unless `--no-plot` is given, a figure
and an interactive HTML report.

## Documentation

The documentation covers installation, a tutorial, every command and the
definition of every metric. Build it with:

```bash
pip install sphinx sphinx-design sphinx-rtd-theme
cd Documentation && make html
# open Documentation/build/html/index.html
```

## Tests

```bash
python setup.py build_ext --inplace
pytest tests
```

## Citation

If you use Pyntacle, please cite:

> Parca L, Truglio M, Biagini T, Castellana S, Petrizzelli F, Capocefalo D,
> Jordán F, Carella M, Mazza T. Pyntacle: a parallel computing-enabled framework
> for large-scale network biology analysis. *GigaScience* 2020;9(10):giaa115.
> [doi:10.1093/gigascience/giaa115](https://doi.org/10.1093/gigascience/giaa115)

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
