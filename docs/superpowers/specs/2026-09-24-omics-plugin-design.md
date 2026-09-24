# `pyntacle omics` — from raw omics matrices to Pyntacle-ready networks

Status: implemented 2026-09-24 (plan docs/superpowers/plans/2026-09-24-omics-plugin.md); paper networks reproduced exactly · Date: 2026-09-24 · Requested by the PI

## 1. Goal

Turn the two preprocessing + inference pipelines used for the CRC case study
(`/home/manu/work/article_pynta`) into an optional Pyntacle subcommand:

    pyntacle omics transcriptomics -i counts.tsv   -m metadata.tsv --group-col condition -o out/
    pyntacle omics metagenomics    -i relabund.tsv -m metadata.tsv --group-col Definition -o out/

Input: a raw feature × sample matrix (counts, or relative abundances) plus a
sample metadata table with a grouping column (2 or more levels). Output: one
network per group, in the format Pyntacle reads with `-w`, plus a provenance
report that states every value the pipeline chose and why.

Scope decision (option C): **generic in design, validated by reproducing the
paper's networks.** The plugin is the code the Methods section points to.

### Success criteria

1. On any conforming matrix + metadata, runs end to end with no flag other
   than `-i -m --group-col -o`.
2. From the raw files in `article_pynta`, with the TCGA flags, reproduces:
   - metagenomics — **exactly** the four StARS-glasso networks of
     `pyntacle_export_v2` (genus T/N 31/21 edges, family T/N 29/17; λ̂ 0.2503,
     0.4084, 0.2511, 0.4658; same edge sets, |Δr| < 1e-6);
   - transcriptomics — **statistically equivalent** networks to
     `network_final_gen3` at FDR 0.001 (tumour 1,715 nodes / 3,148 edges,
     normal 824 / 3,371): selected genes Jaccard ≥ 0.99, edge Jaccard ≥ 0.95,
     same gate quantile. Exact equality is not required because the pipeline
     depends on sklearn GMM/LOESS numerics across versions; the MyGene
     annotation is frozen as a file input so it cannot drift.
3. `import pyntacle` and every existing command work unchanged when the
   optional dependencies are absent.

### What the user said vs. what is assumed

- Said: plugin inside Pyntacle; flexible to counts or abundances + metadata
  with two or more conditions; goes all the way to the network by itself;
  data-driven where possible; the non data-driven values become user flags;
  continuous covariates are the one extension in scope.
- Assumed: the reference recipes are `Colon/Preprocessing_v3.ipynb` §9–10.6
  and `metagen/Analysis.ipynb` as reproduced by
  `metagen/metagenomics_output/pyntacle_export_v2/rebuild_export.py`. Gen 1/2,
  the "classic" pipeline, SparCC/Spearman consensus and PC-stable are not
  ported.

## 2. Honesty about "parameter free"

Neither pipeline is parameter free. The plugin separates three kinds of value
and the report labels each one:

- **data-driven** — chosen by a stated criterion on the data (GMM splits,
  expression gate, prevalence threshold, StARS λ, Ledoit-Wolf λ);
- **default** — a conventional value, overridable by flag (FDR 0.001,
  StARS β 0.10, 3 permutations, grids);
- **user** — set explicitly on the command line.

The Methods text should say "data-driven where a criterion exists, with
documented defaults elsewhere".

## 3. Integration with Pyntacle

- `parser.py`: new subparser `omics` with sub-subcommands `transcriptomics`
  and `metagenomics`, same style as `keyplayer {kp-info,kp-finder}`.
- `main.py`: `omics` bypasses graph loading (as `generate` does) and imports
  `pyntacle.omics` lazily, only when invoked.
- Optional dependencies, declared as an extra (`pyntacle[omics]`):
  scikit-learn, statsmodels, scikit-bio, pandas; `mygene` only for
  `--biotype mygene`. `pyntacle/omics/__init__.py` checks them and exits with
  one line naming the missing packages and the install command.

## 4. Package layout

```
pyntacle/omics/
├── __init__.py          dependency check
├── io.py                load matrix (orientation auto-detected against the
│                        metadata index), load metadata, align samples, split
│                        by --group-col / --groups; report what was dropped
├── covariates.py        residualise features on --covariates (per group)
├── provenance.py        records every value with its kind (data-driven /
│                        default / user) and the diagnostics behind it
├── export.py            per group: edge list, GraphML, report
├── transcriptomics/
│   ├── scale.py         input scale: counts | log2(x+1) → counts
│   ├── tcga.py          --tcga: sample type from barcode, one aliquot/patient
│   ├── normalize.py     DESeq2 median-of-ratios on all groups jointly, log2(x+1)
│   ├── select.py        GMM expressed/silent · LOESS mean-variance + GMM on
│   │                    residuals (HVG) · union across groups · biotype ·
│   │                    sex-linked genes
│   ├── gate.py          self-terminating expression gate
│   └── infer.py         Ledoit-Wolf partial correlation + permutation FDR
└── metagenomics/
    ├── panel.py         prevalence threshold (auto) · union across groups
    ├── coda.py          drop all-zero samples · closure · multiplicative
    │                    replacement · CLR (per group)
    └── infer.py         graphical lasso with λ selected by StARS
```

Each module is a set of pure functions on pandas/numpy objects: no file I/O
outside `io.py` and `export.py`, no printing (the CLI prints the provenance).

## 5. Transcriptomics pipeline

Per the reference notebook, in order:

| # | Step | Kind | Flag |
|---|------|------|------|
| 1 | Detect input scale: non-integers with max ≤ ~30 → `log2(x+1)`, back-transform and round | data-driven | `--input-scale {auto,counts,log2p1}` |
| 2 | `--tcga`: keep sample types 01/11 by barcode (or whatever `--groups` names), one aliquot per patient preferring vial A | user | `--tcga` |
| 3 | Size factors by median-of-ratios on all retained samples jointly; `log2(norm+1)` | fixed method | — |
| 4 | Per group: 2-component GMM on mean expression → expressed genes | data-driven | — |
| 5 | Per group: LOESS (frac 0.3) of log variance on mean; 2-component GMM on residuals → HVG | data-driven | — |
| 6 | Union of HVG across groups (one panel) | fixed | — |
| 7 | Biotype filter: keep protein-coding + ncRNA, rescue `LINC*`/`*-ASn` from unknown | off by default | `--biotype {off,mygene,<annotation.tsv>}` |
| 8 | Drop sex-linked genes (fixed literature list of 16 symbols; needs symbols from step 7's annotation) | off by default | `--drop-sex-genes` |
| 9 | Continuous/categorical covariates: residualise each gene on them, per group | off by default | `--covariates age,purity` |
| 10 | Per group: expression gate — raise the mean-expression quantile along a grid until the top-100 |pcor| edges are no longer enriched in low-expression genes (one-sided Mann–Whitney) | data-driven | `--gate-alpha 0.05`, `--gate-top 100`, `--gate-min-genes 300` |
| 11 | Per group: z-score, Ledoit-Wolf shrinkage, partial correlations | data-driven λ | — |
| 12 | Permutation null (each gene shuffled independently, λ frozen at observed), FDR curve on ranks | default | `--n-perm 3`, `--seed 20260731`, `--fdr 0.001` |

Gate failure (no quantile removes the bias) is an error with the diagnostic
table printed, not a silent fallback — same as the notebook.

## 6. Metagenomics pipeline

| # | Step | Kind | Flag |
|---|------|------|------|
| 1 | Align relabund (taxa × samples, transposed on load) with metadata | — | — |
| 2 | Prevalence threshold: lowest value on a 5% grid for which the union panel (taxon kept if prevalent in **any** group) has fewer taxa than the smallest group's n. On the paper data this yields 15% | data-driven | `--prevalence {auto,<float>}` |
| 3 | Per group: drop all-zero samples, closure, multiplicative replacement, CLR | fixed | — |
| 4 | Covariates, if any: residualise the CLR coordinates on them, per group | off by default | `--covariates` |
| 5 | Per group: StARS over a log-spaced λ path (30 values, λ_min = 0.05 λ_max), 50 subsamples of size 10√n (n > 144) or 0.8 n, monotonised instability ≤ β; refit glasso on full data at λ̂ | data-driven λ | `--stars-beta 0.10`, `--n-sub 50`, `--seed 0` |

## 7. Output (per group `<g>`, prefix from `-o`/`--prefix`)

- `<prefix>_<g>.tsv` — Pyntacle edge list, header `N1 N2 Weight`, where
  **Weight is a distance**: `1 − min(|r|, 0.999999)`. Pyntacle uses weights as
  shortest-path distances, so a strong association must be short (this is the
  v1→v2 export fix).
- `<prefix>_<g>.graphml` — same edges with `assoc_weight` (signed r),
  `abs_r`, `pyntacle_weight`, and for transcriptomics `q_value`; node
  attributes: mean expression/abundance, symbol and biotype when known.
- `<prefix>_report.json` + `<prefix>_report.tsv` — every value with its kind,
  diagnostics (gate table, StARS instability curve, null separation, n/p per
  group, samples and features dropped with reasons), versions and seed.
- `--save-stages` (off by default): the intermediate matrices, as the notebook
  did, for inspection.

Isolated nodes are not written: Pyntacle's edge-list readers cannot carry
them, and the paper counts nodes as genes with at least one edge.

## 8. Error handling

Fail loudly, with the reason and the fix, on: fewer than 2 groups; a group
with n < 5; features ≥ n in the smallest group for glasso (report the
prevalence that would fix it); metadata/matrix with no shared samples;
`--drop-sex-genes` without an annotation; `--covariates` naming a missing
column or a column with missing values in a group; gate or StARS not
converging. Warnings (not errors) for: dropped samples, all-zero samples,
failed glasso fits during StARS (counted in the report).

## 9. Testing

- `tests/omics/test_units.py` — fast, synthetic: scale detection; median of
  ratios against a hand-computed example; GMM selection recovers planted
  expressed/variable genes; gate stops on a planted low-expression artefact;
  permutation FDR recovers a planted sparse precision matrix; CLR/closure
  identities; StARS recovers a planted sparse graph; prevalence rule; covariate
  residualisation removes a planted confounder; export weight semantics and
  sign preservation; CLI refuses clearly without the extras.
- `tests/omics/test_reproduce_paper.py` — marked `slow`, skipped when
  `article_pynta` is absent; asserts success criterion 2 from the raw files,
  with the MyGene cache (`preprocessing_gen3/mygene_biotype_cache_hvg.csv`) as
  `--biotype` input.
- End to end: the exported edge list loads in `pyntacle local -w` without the
  "weights below 1" warning misfiring on semantics (weights are distances by
  construction).

## 10. Documentation

A full section in the Sphinx docs (`Documentation/`, built with
`conda run -n graphtacle_debug make html`, 0 warnings), in the style of the
existing command pages:

- `omics` overview: what the plugin does, when to use it, install extra;
- one page per sub-command: input formats, every flag with its default and
  kind (data-driven / default / user), output files, worked example on a toy
  dataset shipped with the tests, and the CRC case-study command lines;
- a "Methods and references" page: each step with its citation and DOI/PMID
  link (the reference list of `article/methods_final_draft.md`: Love 2014,
  Anders & Huber 2010, McLachlan & Peel 2000, Cleveland 1979, Mann & Whitney
  1947, Ledoit & Wolf 2004, Schäfer & Strimmer 2005, Storey & Tibshirani 2003,
  Aitchison 1982, Martín-Fernández 2003, Gloor 2017, Friedman 2008, Liu 2010,
  Zhao 2012, Kurtz 2015, …), plus the note on weight semantics (distance).
- CLI `--help` texts consistent with the docs.

## 11. Out of scope

PC-stable control networks, differential networks between groups, paired
multi-omics integration, count models other than median-of-ratios, R/Julia
back-ends (SPIEC-EASI, FlashWeave).

## 12. Open risks

- The transcriptomics run on the full TCGA-COAD matrix (60k × 514) needs a few
  GB of RAM and minutes of CPU; the permutation step is O(p³) per permutation
  (p ≈ 3,400). Fine on a workstation; documented in the help text.
- Signed weights elsewhere in Pyntacle (`GraphTacle.py`, silent `abs()`) are a
  separate pending bug. The plugin never writes a negative `Weight`, so it
  does not depend on that fix.
