# Edge-weight semantics: distance, affinity, signed

Status: implemented 2026-09-25 (308 tests incl. slow pass; docs 0 warnings) · Date: 2026-09-25 · Supersedes the plan in
memory `project_pyntacle_signed_weights` (2026-07-20)

## 1. Problem

Pyntacle feeds one edge attribute, `weight`, to functions that read it with
opposite meanings:

| Meaning | Consumers | large weight = |
|---|---|---|
| distance (path length) | shortest paths, closeness, betweenness, radiality, diameter, `global`, key-player dF / m-reach (Python and Cython), group closeness / betweenness | far, weak tie |
| affinity (tie strength) | `local` clustering (Barrat), eigenvector, PageRank (`main.py:250-253`); all four `communities` algorithms (`communities.py:14-29`); `mesoscale` topological importance (`mesoscale.py:229-234`) | close, strong tie |
| threshold (resistance) | `percolation -w`: edge open iff p_th < P* | hard to cross |

Whatever a user supplies, part of the tool reads it inverted. On top of
that, `GraphTacle.from_file` takes `abs()` of every weight
(`GraphTacle.py:123`), silently merging positive and negative ties, and
`convert`/`set`/`extract` then write the absolute values back out.

`pyntacle omics` currently exports `Weight = 1 − |r|` (a distance): right
for path metrics and percolation, inverted for clustering, eigenvector,
PageRank, communities and mesoscale.

## 2. Decisions (agreed 2026-09-25)

1. The user declares what the weights are; Pyntacle derives a distance view
   and an affinity view and each metric reads the one it needs.
2. Weight types: `distance` (default, Pyntacle 1.x semantics), `affinity`,
   `signed`.
3. Affinity → distance by the inverse, `d = 1/a` (Newman 2001; Brandes
   2001; Opsahl et al. 2010; Rubinov & Sporns 2010). `1 − a` and `−log a`
   are available for sensitivity analyses.
4. Signed weights: strength = |w| (unsigned analysis, as in unsigned
   weighted co-expression networks, Zhang & Horvath 2005), sign kept as an
   edge attribute and reported; never dropped silently. Metrics that ignore
   the sign say so.
5. `omics` exports the signed partial correlation itself; the recommended
   command line is `-w --weight-type signed`.
6. The case study uses key-player indices only; sensitivity of the
   key-player sets to the transform is reported in the paper.

## 3. Semantics

Input weight `w` per edge, type `T`, transform `f`:

| T | valid w | affinity a | distance d | sign |
|---|---|---|---|---|
| distance | w > 0 | 1/w | w | +1 |
| affinity | w > 0 | w | f(w) | +1 |
| signed | w ≠ 0 | \|w\| | f(\|w\|) | sign(w) |

`f` (`--distance-transform`): `inverse` d = 1/a (default, any a > 0);
`one-minus` d = max(1 − a, ε); `neglog` d = max(−ln a, ε); the last two
require a ≤ 1 and fail loudly otherwise. ε = 1e-6: a positive distance keeps
the harmonic 1/d in dF and closeness finite.

Invalid input fails with a message naming the offending edges and the fix:
negative weight with `distance`/`affinity` → "use --weight-type signed";
a > 1 with `one-minus`/`neglog` → "use inverse". Zero weights keep failing
as today (`validate_weights`).

Percolation thresholds: `distance` → p_th = w (must lie in [0, 1], as
today); `affinity`/`signed` → p_th = 1 − a (a must lie in [0, 1]).

Side effect worth noting: with `inverse`, correlations |r| ≤ 1 give d ≥ 1,
so dR, group closeness and radiality stay in [0, 1] and the "weights below
1" warning no longer fires for correlation networks.

## 4. Implementation shape

- `utility.weight_views(raw, weight_type, transform)` → `(distance,
  affinity, sign)` as lists; all validation lives here. Pure function.
- `GraphTacle.from_file` / `re`: `abs()` removed. For the analysis
  commands (`local`, `global`, `keyplayer`, `groupcentrality`,
  `communities`, `mesoscale`, `percolation`) the graph carries
  `es["weight"] = distance` — so every existing path consumer, Python and
  Cython, is correct without change — plus `es["affinity"]`, `es["sign"]`,
  `es["raw_weight"]`, and graph attributes `weight_type`,
  `distance_transform`. `re()` (rebuild after `-r`) carries all of them.
- File-writing commands (`convert`, `set`, `extract`, `generate`) keep the
  raw weights untouched (no transform, no abs).
- Affinity consumers switch to `es["affinity"]`: `main.py` local
  clustering / eigenvector / PageRank; `communities.py`; `mesoscale.ti`.
- `percolation.run_percolation(use_edge_weights_as_pth=True)` derives p_th
  per §3 from the graph attributes.
- Cython guard: `_ext/wrapper._edges` raises if a negative distance ever
  reaches Dijkstra.
- CLI (`parser.py`), on every command that has `-w`: `-wt/--weight-type
  {distance,affinity,signed}` (default distance) and `-dt/--distance-transform
  {inverse,one-minus,neglog}` (default inverse); both ignored without `-w`.
  With `signed`, one line per run lists the metrics computed on |w|.
- Reports: weight type and transform in the printed header and in the TSV
  report header of every analysis command.
- `omics/export.py`: edge list `N1 N2 Weight` with Weight = signed r;
  GraphML keeps `r`, `abs_r`, `q_value` (transcriptomics); `pyntacle_weight`
  removed; the run summary prints the Pyntacle command line to use.

## 5. Tests

- `weight_views`: each type × transform on hand-computed values; every
  refusal (negative with distance/affinity, a > 1 with one-minus/neglog,
  zero).
- Distance default is backward compatible: outputs of `local`, `global`,
  `kp-info` on a positive-weight fixture identical to before.
- Affinity vs distance equivalence: a graph given as affinity a and the same
  graph given as distance 1/a produce identical path metrics, and identical
  affinity metrics.
- Affinity consumers read affinity: eigenvector/PageRank on a star whose
  heavy edge is a strong tie rank the right leaf first under `affinity`.
- Signed: sign survives load, `re()` after `-r`, and `convert` round trip;
  metrics equal those of the `affinity` run on |w|.
- Cython and Python engines agree under each type.
- Percolation p_th derivation for each type.
- `omics`: exported Weight equals the signed r; the slow reproduction test
  compares r against the paper's `assoc_weight`.

## 6. Documentation

- New page `Documentation/source/weights.rst` ("Edge weights"): the three
  meanings table, the three types, the transforms with their references,
  signed networks (unsigned analysis, layer split, signed centralities —
  Everett & Borgatti 2014 — with what Pyntacle does and does not do), worked
  examples.
- Every command page with `-w`: the two flags.
- `omics/omics.rst` "Weights and distances" rewritten; `cli/omics` usage
  examples gain `-wt signed`.

References (DOIs verified against Crossref, 2026-09-25):
Newman 2001, Phys Rev E 64:016132, doi:10.1103/PhysRevE.64.016132 ·
Brandes 2001, J Math Sociol 25:163–177, doi:10.1080/0022250X.2001.9990249 ·
Opsahl, Agneessens & Skvoretz 2010, Soc Networks 32:245–251,
doi:10.1016/j.socnet.2010.03.006 · Rubinov & Sporns 2010, NeuroImage
52:1059–1069, doi:10.1016/j.neuroimage.2009.10.003 · Zhang & Horvath 2005,
Stat Appl Genet Mol Biol 4:17, doi:10.2202/1544-6115.1128 · Everett &
Borgatti 2014, Soc Networks 38:111–120, doi:10.1016/j.socnet.2014.03.005.

## 7. Out of scope

Signed-specific centralities (PN centrality) and automatic G⁺/G⁻ layer
split: documented as alternatives, not implemented. Directed signed
networks. Re-running the case study (a paper task once the code lands).

## 8. Consequences for the paper

- All six networks are regenerated with the new export and analysed with
  `-w -wt signed` (inverse transform). The transcriptome caveat in
  `02_case_studies_CRC.md` ("Network export and edge-weight convention",
  "Declared limitations") becomes obsolete: both layers now share one
  convention.
- Key-player sets change (the transform changed from 1 − |r|, and from |r|
  used as a distance in the transcriptome layer); the sensitivity analysis
  runs `-dt one-minus` and `-dt neglog` and reports set overlap.
