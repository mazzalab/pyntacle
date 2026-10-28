# Examples

Small inputs to try every part of Pyntacle, each in less than a minute. Run the commands
from the root of the repository; each writes its reports to the directory
given with `-o`.

| File | What it is |
|---|---|
| `figure_8.egl` | the 32-node network of the tutorial, as an edge list |
| `figure_8.txt` | the same network as an adjacency matrix |
| `omics/relabund.tsv` | a simulated microbiome: 30 taxa in 180 samples, relative abundances in percent |
| `omics/samples.tsv` | the group of each sample (`control` or `tumor`) |
| `omics/make_toy_microbiome.py` | the script that simulated the two files above |

## Networks

```bash
# per-node metrics: degree, betweenness, closeness, PageRank, ...
pyntacle local -t edgelist -i examples/figure_8.egl -o out/local

# whole-network metrics, from the adjacency matrix
pyntacle global -t matrix -i examples/figure_8.txt -o out/global

# the best pair of key players for every index, by exhaustive search
pyntacle keyplayer kp-finder -t edgelist -i examples/figure_8.egl -k 2 -oper all -o out/kp

# the group of three nodes with the highest group betweenness, greedy search
pyntacle groupcentrality gc-finder -t edgelist -i examples/figure_8.egl -k 3 -oper betweenness -a greedy --seed 1 -o out/gc

# communities
pyntacle communities fastgreedy -t edgelist -i examples/figure_8.egl -o out/communities

# spreading from one node
pyntacle percolation -t edgelist -i examples/figure_8.egl -n HS --seed 1 -o out/percolation
```

## Omics

`omics metagenomics` builds one network per group of samples. Each edge is
a partial correlation between two taxa; the report lists every value used
and who chose it. Pass the networks to the other commands as signed weights:

```bash
pyntacle omics metagenomics -i examples/omics/relabund.tsv -m examples/omics/samples.tsv --group-col condition -o out/nets
pyntacle keyplayer kp-finder -t edgelist -w -wt signed -i out/nets/relabund_tumor.tsv -k 2 -oper all -a greedy -o out/kp_tumor
```

The microbiome is simulated, so the result is known in advance. In both
groups `taxon_01` to `taxon_06` vary together and `taxon_07` to `taxon_10`
vary against them. `taxon_25` to `taxon_28` are rare in the control samples
and linked to one another only in the tumor network. To simulate it again
(`N_TAXA`, `N_PER_GROUP` and `SEED` at the top of the script set the sizes and the seed):

```bash
python examples/omics/make_toy_microbiome.py
```
