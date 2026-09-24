# `pyntacle omics` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `pyntacle omics {transcriptomics,metagenomics}`, which turns a raw count/abundance matrix plus sample metadata into one Pyntacle-ready network per group, reproducing the CRC paper's networks.

**Architecture:** A self-contained package `pyntacle/omics/` of pure functions (one module per pipeline stage), a thin CLI adapter wired into `parser.py`/`main.py` with a lazy import, and an exporter that writes Pyntacle edge lists (Weight = distance), GraphML and a provenance report. Optional dependencies only.

**Tech Stack:** Python 3.10 (env `graphtacle_debug`), numpy, pandas, scipy, scikit-learn (GaussianMixture, graphical_lasso), statsmodels (lowess), igraph (GraphML), optional mygene; pytest; Sphinx.

**Spec:** `docs/superpowers/specs/2026-09-24-omics-plugin-design.md`

## Global Constraints

- Pyntacle uses flat imports: `pyntacle/` is on `sys.path`, so the package is imported as `omics` (not `pyntacle.omics`). Inside the package use relative imports.
- `import omics` must succeed without scikit-learn/statsmodels; only `omics.require()` and the pipeline modules need them. Existing commands must not import `omics` at all.
- Edge list `Weight` = `1 − min(|r|, 0.999999)` (a distance). Signed r goes only into GraphML (`assoc_weight`).
- Transcriptomics defaults: FDR 0.001, 3 permutations, seed 20260731, GMM random_state 42 n_init 5, LOESS frac 0.3, gate grid 0.00–0.90 step 0.05, gate alpha 0.05, top 100 edges, min 300 genes.
- Metagenomics defaults: prevalence auto on grid 0.05–0.50 step 0.05, StARS β 0.10, 50 subsamples, 30 λ values, λ_min ratio 0.05, seed 0.
- Every chosen value is recorded in provenance with kind `data-driven`, `default` or `user`.
- Isolated nodes are not written to the edge list.
- Do not touch `pyntacle/main.py` or `pyntacle/parser.py` while the benchmark pilot (`benchmarks/results/local-pilot`) is running: each benchmark cell re-imports them.
- Commit messages carry no Claude/AI attribution (user rule). The user runs git; tasks list the files to stage.

## Review Focus

- Matrix orientation ambiguous (sample ids in neither index nor columns, e.g. metadata with a different id format) → clear error naming both id examples, not a silent transpose.
- A group left with fewer than 5 samples after alignment/dedup → error naming the group and its n.
- Metadata group column with NaN for some samples → those samples dropped and counted in the report, not crashing on `groupby`.
- Relative abundances given in percent (rows summing to 100) → closure makes them identical to fractions; must not change the result.
- Gene ids with Ensembl versions (`ENSG….9`) against an annotation without versions → matched on the unversioned id.

---

## File Structure

```
pyntacle/omics/__init__.py                 dependency check (require), public version
pyntacle/omics/provenance.py               Provenance: records values + diagnostics, to_json/to_tsv
pyntacle/omics/loader.py                   read_table, orient, load_inputs, split_groups
pyntacle/omics/covariates.py               design_matrix, residualise
pyntacle/omics/export.py                   safe_name, write_network
pyntacle/omics/transcriptomics/__init__.py run(...) orchestration
pyntacle/omics/transcriptomics/scale.py    detect_scale, to_counts
pyntacle/omics/transcriptomics/tcga.py     sample_type, dedup_by_patient, tcga_groups
pyntacle/omics/transcriptomics/normalize.py median_of_ratios_size_factors, log_normalise
pyntacle/omics/transcriptomics/select.py   expressed_genes, highly_variable_genes, load_annotation,
                                           query_mygene, biotype_filter, sex_linked_mask, SEX_LINKED
pyntacle/omics/transcriptomics/infer.py    zscore_genes, standardised_samples, lw_pcor, permutation_fdr, edges_at_fdr
pyntacle/omics/transcriptomics/gate.py     expression_bias_pvalue, auto_expression_gate
pyntacle/omics/metagenomics/__init__.py    run(...) orchestration
pyntacle/omics/metagenomics/panel.py       prevalence, auto_prevalence, union_panel
pyntacle/omics/metagenomics/coda.py        closure, multiplicative_replacement, clr, drop_allzero, coda_transform
pyntacle/omics/metagenomics/infer.py       stars_glasso
pyntacle/omics/cli.py                      run_omics(args): args → pipeline → export
pyntacle/parser.py                         + omics subparser
pyntacle/main.py                           + early dispatch for "omics"
setup.py                                   + extras_require
tests/omics/test_*.py                      unit tests (synthetic)
tests/omics/test_reproduce_paper.py        slow, article_pynta data
Documentation/source/cli/omics/index.rst   CLI reference
Documentation/source/omics/omics.rst       methods + references
Documentation/source/{index,installation}.rst, cli/index.rst  links
```

Every test file starts with:

```python
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")
```
(the top-level `tests/conftest.py` already puts `pyntacle/` on `sys.path`).

---

### Task 0: Environment

- [ ] **Step 1:** Install the optional deps in the dev env.

Run: `~/miniconda3/envs/graphtacle_debug/bin/pip install scikit-learn statsmodels mygene`
Expected: installs; `python -c "import sklearn, statsmodels, mygene"` succeeds.

- [ ] **Step 2:** Create `tests/omics/` (no `__init__.py`, matching `tests/`).

---

### Task 1: Package skeleton, dependency check, provenance

**Files:**
- Create: `pyntacle/omics/__init__.py`, `pyntacle/omics/provenance.py`
- Test: `tests/omics/test_core.py`

**Interfaces:**
- Produces: `omics.missing_dependencies() -> list[str]`, `omics.require() -> None` (SystemExit with install hint), `Provenance` with `.record(step, name, value, kind, note="")`, `.diagnostic(name, obj)`, `.warn(msg)`, `.to_dict()`, `.write(outdir, prefix)`; `KINDS = ("data-driven", "default", "user")`.

- [ ] **Step 1: failing tests**

```python
import json
import omics
from omics.provenance import Provenance


def test_missing_dependencies_reports_pip_names(monkeypatch):
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda m: None if m == "statsmodels" else real(m))
    assert omics.missing_dependencies() == ["statsmodels"]
    with pytest.raises(SystemExit, match="pip install statsmodels"):
        omics.require()


def test_provenance_records_kind_and_writes(tmp_path):
    p = Provenance("metagenomics")
    p.record("panel", "prevalence", 0.15, "data-driven", "lowest with p < n_min")
    p.record("stars", "beta", 0.10, "default")
    with pytest.raises(ValueError):
        p.record("x", "y", 1, "guess")
    p.diagnostic("stars_tumor", pd.DataFrame({"lambda": [0.1], "instability": [0.02]}))
    p.warn("dropped 1 all-zero sample")
    p.write(str(tmp_path), "crc")
    data = json.loads((tmp_path / "crc_report.json").read_text())
    assert data["values"][0]["kind"] == "data-driven"
    assert data["diagnostics"]["stars_tumor"][0]["lambda"] == 0.1
    tsv = (tmp_path / "crc_report.tsv").read_text()
    assert "prevalence\t0.15\tdata-driven" in tsv
```

- [ ] **Step 2:** Run `pytest tests/omics/test_core.py -v` → FAIL (no module `omics`).

- [ ] **Step 3: implement**

`pyntacle/omics/__init__.py`:
```python
"""Raw omics matrices -> Pyntacle-ready networks (`pyntacle omics`).

Optional part of Pyntacle: it needs scikit-learn and statsmodels, which the
core does not. Importing this package never fails; `require()` does, with the
install command, before any pipeline runs.
"""
import importlib.util

# module name -> pip name
_REQUIRED = {"sklearn": "scikit-learn", "statsmodels": "statsmodels"}


def missing_dependencies():
    return [pip for mod, pip in _REQUIRED.items() if importlib.util.find_spec(mod) is None]


def require():
    missing = missing_dependencies()
    if missing:
        raise SystemExit("ERROR: 'pyntacle omics' needs " + ", ".join(missing)
                         + ". Install with: pip install " + " ".join(missing))
```

`pyntacle/omics/provenance.py`:
```python
"""Every value a pipeline uses, with where it came from.

The report separates what the data decided (data-driven), what a convention
decided (default) and what the user decided (user), so the Methods text can
say which is which.
"""
import csv
import datetime
import json
import os
import platform

KINDS = ("data-driven", "default", "user")


def _plain(obj):
    if hasattr(obj, "to_dict") and hasattr(obj, "columns"):
        return obj.to_dict(orient="records")
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    return obj


class Provenance:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.values, self.diagnostics, self.warnings = [], {}, []

    def record(self, step, name, value, kind, note=""):
        if kind not in KINDS:
            raise ValueError("kind must be one of {}, got {!r}".format(KINDS, kind))
        self.values.append({"step": step, "name": name, "value": _plain(value),
                            "kind": kind, "note": note})

    def diagnostic(self, name, obj):
        self.diagnostics[name] = _plain(obj)

    def warn(self, msg):
        self.warnings.append(msg)

    def to_dict(self):
        import numpy, pandas, scipy, sklearn, statsmodels
        return {"pipeline": self.pipeline,
                "date": datetime.datetime.now().isoformat(timespec="seconds"),
                "versions": {"python": platform.python_version(), "numpy": numpy.__version__,
                             "pandas": pandas.__version__, "scipy": scipy.__version__,
                             "scikit-learn": sklearn.__version__,
                             "statsmodels": statsmodels.__version__},
                "values": self.values, "diagnostics": self.diagnostics,
                "warnings": self.warnings}

    def write(self, outdir, prefix):
        with open(os.path.join(outdir, prefix + "_report.json"), "w") as fh:
            json.dump(self.to_dict(), fh, indent=1, default=str)
        with open(os.path.join(outdir, prefix + "_report.tsv"), "w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            w.writerow(["step", "name", "value", "kind", "note"])
            for v in self.values:
                w.writerow([v["step"], v["name"], v["value"], v["kind"], v["note"]])
```

- [ ] **Step 4:** Run tests → PASS.
- [ ] **Step 5:** Stage `pyntacle/omics/__init__.py pyntacle/omics/provenance.py tests/omics/test_core.py`.

---

### Task 2: Loader (tables, orientation, groups)

**Files:**
- Create: `pyntacle/omics/loader.py`
- Test: `tests/omics/test_loader.py`

**Interfaces:**
- Produces:
  - `read_table(path, sep=None) -> pd.DataFrame` (index = first column; sep from extension: `.csv[.gz]` → `,`, else tab).
  - `orient(matrix, sample_ids) -> pd.DataFrame` features × samples.
  - `load_inputs(matrix_path, metadata_path, group_col, groups=None, sep=None, prov=None) -> (X, labels)`; `X` features × samples (float), `labels` `pd.Series` sample → group (str), only the requested groups, samples in both tables.
  - `check_groups(labels, min_n=5)` raises `SystemExit` naming small groups.

- [ ] **Step 1: failing tests**

```python
from omics import loader


def _meta(ids, groups):
    return pd.DataFrame({"cond": groups}, index=ids)


def test_orient_transposes_samples_by_features():
    m = pd.DataFrame(np.ones((3, 2)), index=["s1", "s2", "s3"], columns=["g1", "g2"])
    assert list(loader.orient(m, ["s1", "s2", "s3"]).columns) == ["s1", "s2", "s3"]


def test_orient_refuses_when_no_ids_match():
    m = pd.DataFrame(np.ones((2, 2)), index=["a", "b"], columns=["c", "d"])
    with pytest.raises(SystemExit, match="no sample id"):
        loader.orient(m, ["TCGA-1", "TCGA-2"])


def test_load_inputs_aligns_drops_nan_and_filters_groups(tmp_path):
    ids = ["s{}".format(i) for i in range(12)]
    X = pd.DataFrame(np.arange(24).reshape(2, 12), index=["g1", "g2"], columns=ids)
    X.to_csv(tmp_path / "x.tsv", sep="\t")
    groups = ["T"] * 6 + ["N"] * 5 + [np.nan]
    _meta(ids, groups).to_csv(tmp_path / "m.csv")
    Xa, lab = loader.load_inputs(str(tmp_path / "x.tsv"), str(tmp_path / "m.csv"), "cond")
    assert sorted(lab.unique()) == ["N", "T"] and len(lab) == 11
    assert list(Xa.columns) == list(lab.index)
    _, lab2 = loader.load_inputs(str(tmp_path / "x.tsv"), str(tmp_path / "m.csv"), "cond", groups=["T"])
    assert set(lab2) == {"T"}


def test_check_groups_names_small_group():
    lab = pd.Series(["T"] * 6 + ["N"] * 3)
    with pytest.raises(SystemExit, match="N.*n=3"):
        loader.check_groups(lab)
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: implement** `pyntacle/omics/loader.py`:
```python
"""Read the matrix and the metadata, put samples in columns, keep the groups."""
import os

import pandas as pd


def read_table(path, sep=None):
    if sep is None:
        name = path.lower()
        for ext in (".gz", ".bz2", ".zip", ".xz"):
            if name.endswith(ext):
                name = name[: -len(ext)]
        sep = "," if name.endswith(".csv") else "\t"
    if not os.path.exists(path):
        raise SystemExit("ERROR: file not found: " + path)
    return pd.read_csv(path, sep=sep, index_col=0)


def orient(matrix, sample_ids):
    """Features x samples, whichever way the file was written."""
    ids = set(map(str, sample_ids))
    in_cols = len(ids & set(map(str, matrix.columns)))
    in_rows = len(ids & set(map(str, matrix.index)))
    if in_cols == 0 and in_rows == 0:
        raise SystemExit("ERROR: no sample id is shared by the matrix and the metadata "
                         "(matrix columns look like {!r}, metadata ids like {!r})".format(
                             list(matrix.columns[:2]), list(sample_ids)[:2]))
    return matrix if in_cols >= in_rows else matrix.T


def check_groups(labels, min_n=5):
    counts = labels.value_counts()
    small = counts[counts < min_n]
    if len(counts) < 1:
        raise SystemExit("ERROR: no sample left in any group")
    if len(small):
        raise SystemExit("ERROR: groups need at least {} samples: {}".format(
            min_n, ", ".join("{} n={}".format(g, n) for g, n in small.items())))


def load_inputs(matrix_path, metadata_path, group_col, groups=None, sep=None, prov=None):
    meta = read_table(metadata_path, sep)
    meta.index = meta.index.astype(str)
    if group_col not in meta.columns:
        raise SystemExit("ERROR: --group-col {!r} not in metadata columns: {}".format(
            group_col, ", ".join(map(str, meta.columns[:20]))))
    X = orient(read_table(matrix_path, sep), meta.index)
    X.columns = X.columns.astype(str)
    labels = meta[group_col]
    n_nan = int(labels.isna().sum())
    labels = labels.dropna().astype(str)
    if groups:
        labels = labels[labels.isin(groups)]
        unknown = set(groups) - set(labels)
        if unknown:
            raise SystemExit("ERROR: --groups not found in column {!r}: {}".format(
                group_col, ", ".join(sorted(unknown))))
    shared = [s for s in X.columns if s in labels.index]
    if prov is not None:
        prov.record("input", "samples_in_matrix", X.shape[1], "user")
        prov.record("input", "samples_used", len(shared), "data-driven",
                    "{} without group label, {} not in metadata".format(
                        n_nan, X.shape[1] - len(set(X.columns) & set(meta.index))))
    return X[shared].astype(float), labels.loc[shared]
```

- [ ] **Step 4:** Run → PASS. **Step 5:** stage files.

---

### Task 3: Covariates

**Files:** Create `pyntacle/omics/covariates.py`; Test `tests/omics/test_covariates.py`

**Interfaces:**
- Produces: `design_matrix(meta, columns) -> pd.DataFrame` (numeric as is, non-numeric one-hot with drop_first, intercept added; `SystemExit` on missing column or NaN); `residualise(Y, design) -> pd.DataFrame` where `Y` is samples × features, returns residuals (same shape, index, columns).

- [ ] **Step 1: failing tests**

```python
from omics import covariates


def test_residualise_removes_planted_confounder():
    rng = np.random.default_rng(0)
    n = 200
    age = rng.normal(60, 10, n)
    base = rng.normal(size=(n, 2))
    Y = pd.DataFrame(base + np.outer(age, [0.5, -0.3]), columns=["a", "b"])
    meta = pd.DataFrame({"age": age, "sex": rng.choice(["F", "M"], n)})
    D = covariates.design_matrix(meta, ["age", "sex"])
    assert list(D.columns) == ["intercept", "age", "sex_M"]
    R = covariates.residualise(Y, D)
    assert abs(np.corrcoef(R["a"], age)[0, 1]) < 1e-8
    assert np.corrcoef(R["a"], base[:, 0])[0, 1] > 0.99


def test_design_matrix_refuses_missing_values():
    meta = pd.DataFrame({"age": [1.0, np.nan, 3.0]})
    with pytest.raises(SystemExit, match="missing values"):
        covariates.design_matrix(meta, ["age"])
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement**
```python
"""Regress sample covariates (age, purity, batch, ...) out of every feature.

Run per group, right before association is estimated: partial correlations
of the residuals are conditional on the covariates as well.
"""
import numpy as np
import pandas as pd


def design_matrix(meta, columns):
    missing = [c for c in columns if c not in meta.columns]
    if missing:
        raise SystemExit("ERROR: --covariates not in metadata: " + ", ".join(missing))
    sub = meta[columns]
    if sub.isna().any().any():
        bad = [c for c in columns if sub[c].isna().any()]
        raise SystemExit("ERROR: covariates with missing values in this group: " + ", ".join(bad))
    parts = [pd.Series(1.0, index=meta.index, name="intercept")]
    for c in columns:
        if pd.api.types.is_numeric_dtype(sub[c]):
            parts.append(sub[c].astype(float))
        else:
            parts.append(pd.get_dummies(sub[c].astype(str), prefix=c, drop_first=True).astype(float))
    return pd.concat(parts, axis=1)


def residualise(Y, design):
    B, *_ = np.linalg.lstsq(design.values, Y.values, rcond=None)
    return pd.DataFrame(Y.values - design.values @ B, index=Y.index, columns=Y.columns)
```
- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 4: Export

**Files:** Create `pyntacle/omics/export.py`; Test `tests/omics/test_export.py`

**Interfaces:**
- Consumes: none.
- Produces: `safe_name(label) -> str`; `write_network(edges, nodes, outdir, prefix, group) -> dict` with keys `edgelist`, `graphml`, `n_nodes`, `n_edges`. `edges`: DataFrame columns `source, target, r` (+ optional `q_value`); `nodes`: DataFrame indexed by node id with any attribute columns (may be empty).

- [ ] **Step 1: failing tests**

```python
import igraph as ig
from omics import export


def test_weight_is_distance_and_sign_kept(tmp_path):
    edges = pd.DataFrame({"source": ["a", "b"], "target": ["b", "c"], "r": [0.9, -1.0]})
    nodes = pd.DataFrame({"symbol": ["A", "B", "C", "D"]}, index=["a", "b", "c", "d"])
    out = export.write_network(edges, nodes, str(tmp_path), "crc", "Primary Tumor")
    el = pd.read_csv(out["edgelist"], sep="\t")
    assert list(el.columns) == ["N1", "N2", "Weight"]
    assert el["Weight"].round(6).tolist() == [0.1, 1e-06]
    g = ig.Graph.Read_GraphML(out["graphml"])
    assert sorted(g.es["assoc_weight"]) == [-1.0, 0.9]
    assert g.vcount() == 3 and out["n_nodes"] == 3   # isolate "d" not written
    assert out["edgelist"].endswith("crc_primary_tumor.tsv")


def test_exported_edgelist_loads_in_pyntacle(tmp_path):
    from GraphTacle import Graphtacle
    edges = pd.DataFrame({"source": ["a", "b"], "target": ["b", "c"], "r": [0.5, 0.2]})
    out = export.write_network(edges, pd.DataFrame(), str(tmp_path), "t", "g")
    g = Graphtacle.from_file(out["edgelist"], "local", "edgelist", None, True, False, True)
    assert g.vcount() == 3 and sorted(g.es["weight"]) == [0.5, 0.8]
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement**
```python
"""Write one group's network the way Pyntacle reads it.

Pyntacle uses edge weights as shortest-path distances, so the edge list's
Weight is 1 - |r|: a strong association is a short edge. The signed r lives
in the GraphML only, where nothing treats it as a distance.
"""
import os
import re

import igraph as ig
import numpy as np

MAX_ABS_R = 0.999999


def safe_name(label):
    return re.sub(r"[^a-z0-9]+", "_", str(label).lower()).strip("_") or "group"


def write_network(edges, nodes, outdir, prefix, group):
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.join(outdir, "{}_{}".format(prefix, safe_name(group)))
    e = edges.copy()
    e["source"], e["target"] = e["source"].astype(str), e["target"].astype(str)
    e["abs_r"] = e["r"].abs()
    e["pyntacle_weight"] = 1.0 - np.minimum(e["abs_r"], MAX_ABS_R)
    e = e.sort_values(["source", "target"]).reset_index(drop=True)

    e[["source", "target", "pyntacle_weight"]].rename(
        columns={"source": "N1", "target": "N2", "pyntacle_weight": "Weight"}).to_csv(
        stem + ".tsv", sep="\t", index=False, float_format="%.6f")

    names = sorted(set(e["source"]) | set(e["target"]))
    idx = {n: i for i, n in enumerate(names)}
    g = ig.Graph(n=len(names), edges=[(idx[a], idx[b]) for a, b in zip(e["source"], e["target"])])
    g.vs["name"] = names
    for col in nodes.columns:
        values = nodes[col].reindex(names)
        g.vs[col] = [None if (isinstance(v, float) and np.isnan(v)) else
                     (float(v) if isinstance(v, (int, float, np.floating)) else str(v)) for v in values]
    g.es["assoc_weight"] = e["r"].astype(float).tolist()
    g.es["abs_r"] = e["abs_r"].astype(float).tolist()
    g.es["pyntacle_weight"] = e["pyntacle_weight"].astype(float).tolist()
    if "q_value" in e.columns:
        g.es["q_value"] = e["q_value"].astype(float).tolist()
    g.write_graphml(stem + ".graphml")
    return {"edgelist": stem + ".tsv", "graphml": stem + ".graphml",
            "n_nodes": len(names), "n_edges": len(e)}
```
Note: `Graphtacle.from_file` signature is `(path, command, fileType, sep, header, directed, weighted)`; check how the edgelist reader parses a 3-column header file and adapt the test call if it differs (keep the assertion on weights).

- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 5: Transcriptomics — scale, TCGA helpers, normalisation

**Files:** Create `pyntacle/omics/transcriptomics/{__init__.py (empty for now),scale.py,tcga.py,normalize.py}`; Test `tests/omics/test_tx_prep.py`

**Interfaces:**
- Produces:
  - `scale.detect_scale(X) -> "counts" | "log2p1"` (SystemExit if neither).
  - `scale.to_counts(X, scale) -> DataFrame` (rounded, clipped ≥ 0).
  - `tcga.sample_type(barcode) -> str|None`, `tcga.dedup_by_patient(cols, prefer_vial="A") -> (keep, dropped)`, `tcga.tcga_groups(columns, codes={"01": "tumor", "11": "normal"}) -> (labels Series, dropped dict)`.
  - `normalize.median_of_ratios_size_factors(counts) -> Series`, `normalize.log_normalise(counts) -> (log_norm DataFrame, size_factors Series)`.

- [ ] **Step 1: failing tests**

```python
from omics.transcriptomics import normalize, scale, tcga


def test_detect_scale():
    counts = pd.DataFrame([[0, 5], [10, 200]], dtype=float)
    assert scale.detect_scale(counts) == "counts"
    assert scale.detect_scale(np.log2(counts + 1)) == "log2p1"
    with pytest.raises(SystemExit):
        scale.detect_scale(pd.DataFrame([[-1.5, 2.2]]))


def test_to_counts_round_trips_xena():
    counts = pd.DataFrame([[0, 5], [10, 200]], dtype=float)
    assert scale.to_counts(np.log2(counts + 1), "log2p1").equals(counts)


def test_tcga_groups_and_dedup():
    cols = ["TCGA-AA-0001-01A-11R", "TCGA-AA-0001-01B-11R", "TCGA-AA-0002-11A-01R",
            "TCGA-AA-0003-06A-01R"]
    labels, dropped = tcga.tcga_groups(cols)
    assert labels.to_dict() == {"TCGA-AA-0001-01A-11R": "tumor", "TCGA-AA-0002-11A-01R": "normal"}
    assert dropped["other_type"] == ["TCGA-AA-0003-06A-01R"]
    assert dropped["duplicate"] == ["TCGA-AA-0001-01B-11R"]


def test_median_of_ratios_matches_hand_computation():
    counts = pd.DataFrame({"s1": [10, 20, 0], "s2": [20, 40, 5]}, index=["g1", "g2", "g3"], dtype=float)
    sf = normalize.median_of_ratios_size_factors(counts)
    # geometric means over genes with no zero: g1 sqrt(200), g2 sqrt(800)
    assert np.allclose(sf.values, [1 / np.sqrt(2), np.sqrt(2)])
    log_norm, _ = normalize.log_normalise(counts)
    assert np.isclose(log_norm.loc["g1", "s1"], np.log2(10 * np.sqrt(2) + 1))
```

Note on the TCGA barcode: the vial letter is the character after the two-digit sample type (`01A`); Xena columns may be 16 characters (`TCGA-AA-0001-01A`). `dedup_by_patient` prefers a barcode whose 4th field ends with the preferred vial, i.e. `barcode.split("-")[3].endswith(prefer_vial)` — generalising the notebook's `str.endswith(prefer_vial)` to barcodes with trailing fields. On 16-character barcodes both behave identically.

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement**

`scale.py`:
```python
"""Counts in, whatever the file holds.

UCSC Xena distributes STAR counts as log2(count + 1); normalising those as if
they were counts is the silent error this module exists to prevent.
"""
import numpy as np

LOG_MAX = 50.0   # log2(count+1) of any real library stays far below this


def detect_scale(X):
    v = X.values
    if np.nanmin(v) < 0:
        raise SystemExit("ERROR: negative values in the matrix: not counts nor log2(count+1). "
                         "Pass raw counts.")
    if np.allclose(v, np.round(v)):
        return "counts"
    if np.nanmax(v) <= LOG_MAX:
        return "log2p1"
    raise SystemExit("ERROR: non-integer values above {}: the matrix looks normalised. "
                     "Pass raw counts, or --input-scale counts if they are.".format(LOG_MAX))


def to_counts(X, scale):
    if scale == "counts":
        C = X.round()
    elif scale == "log2p1":
        C = (np.power(2.0, X) - 1.0).round()
    else:
        raise ValueError(scale)
    return C.clip(lower=0.0)
```

`tcga.py`:
```python
"""TCGA barcodes: sample type and one aliquot per patient (--tcga)."""
import pandas as pd

TYPE_NAMES = {"01": "tumor", "11": "normal"}


def sample_type(barcode):
    parts = barcode.split("-")
    return parts[3][:2] if len(parts) >= 4 else None


def patient_id(barcode):
    return barcode[:12]


def _vial(barcode):
    parts = barcode.split("-")
    return parts[3][2:3] if len(parts) >= 4 else ""


def dedup_by_patient(cols, prefer_vial="A"):
    df = pd.DataFrame({"barcode": list(cols), "patient": [patient_id(c) for c in cols]})
    keep, dropped = [], []
    for _, grp in df.groupby("patient", sort=True):
        if len(grp) == 1:
            keep.append(grp["barcode"].iloc[0])
            continue
        pref = grp[[_vial(b) == prefer_vial for b in grp["barcode"]]]
        chosen = pref["barcode"].iloc[0] if len(pref) else grp["barcode"].iloc[0]
        keep.append(chosen)
        dropped.extend(b for b in grp["barcode"] if b != chosen)
    return keep, dropped


def tcga_groups(columns, codes=TYPE_NAMES):
    types = {c: sample_type(c) for c in columns}
    other = [c for c in columns if types[c] not in codes]
    labels, dup = {}, []
    for code, name in codes.items():
        keep, dropped = dedup_by_patient([c for c in columns if types[c] == code])
        labels.update({c: name for c in keep})
        dup.extend(dropped)
    order = [c for c in columns if c in labels]
    return pd.Series({c: labels[c] for c in order}), {"other_type": other, "duplicate": dup}
```

`normalize.py`:
```python
"""DESeq2 median-of-ratios size factors (Anders & Huber 2010), then log2(x+1).

Size factors are estimated on all groups together, so every group sits on
the same scale.
"""
import numpy as np


def median_of_ratios_size_factors(counts):
    log_counts = np.log(counts.where(counts > 0))
    log_geomean = log_counts.mean(axis=1)          # NaN if any zero: gene left out
    valid = log_geomean.notna() & np.isfinite(log_geomean) & log_counts.notna().all(axis=1)
    ratios = log_counts.loc[valid].sub(log_geomean[valid], axis=0)
    return np.exp(ratios.median(axis=0))


def log_normalise(counts):
    sf = median_of_ratios_size_factors(counts)
    return np.log2(counts.div(sf, axis=1) + 1.0), sf
```
Note: `DataFrame.mean` skips NaN by default, so the notebook's `log_geomean` was computed over the non-zero samples only; `valid` there did not exclude genes with a zero. To stay faithful to the paper, keep the notebook's behaviour: **drop** the `& log_counts.notna().all(axis=1)` term if the reproduction test (Task 11) shows a mismatch; the hand-computed unit test above uses `g3` (zero in s1) and must then be updated to include g3's ratio. Decide by running Task 11 — the paper numbers win.

- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 6: Transcriptomics — gene selection

**Files:** Create `pyntacle/omics/transcriptomics/select.py`; Test `tests/omics/test_tx_select.py`

**Interfaces:**
- Produces:
  - `expressed_genes(df, random_state=42) -> (pd.Series mean of kept genes, dict info)`
  - `highly_variable_genes(df, random_state=42) -> (set, dict info)` — info has `n_expressed`, `n_hvg`, `gmm_means`, `rho_residual_mean`.
  - `load_annotation(path) -> DataFrame` indexed by unversioned id with columns `symbol`, `type_of_gene`.
  - `query_mygene(gene_ids) -> DataFrame` same shape (network).
  - `biotype_filter(genes, annotation) -> (list kept, int n_rescued)`.
  - `SEX_LINKED` (frozenset of 16 symbols); `sex_linked_mask(genes, annotation) -> np.ndarray[bool]`.
  - `base_id(gene) -> str` (strip `.version`).

- [ ] **Step 1: failing tests**

```python
from omics.transcriptomics import select


def _planted(n_samples=60, seed=0):
    rng = np.random.default_rng(seed)
    silent = rng.normal(0.5, 0.2, (300, n_samples)).clip(0)
    expressed = rng.normal(8, 0.3, (300, n_samples))
    variable = rng.normal(8, 2.0, (40, n_samples))
    idx = ["s{}".format(i) for i in range(300)] + ["e{}".format(i) for i in range(300)] \
        + ["v{}".format(i) for i in range(40)]
    return pd.DataFrame(np.vstack([silent, expressed, variable]), index=idx)


def test_expressed_genes_separates_silent():
    kept, info = select.expressed_genes(_planted())
    assert not any(g.startswith("s") for g in kept.index)
    assert info["n_expressed"] == 340


def test_hvg_recovers_planted_variable_genes():
    hvg, info = select.highly_variable_genes(_planted())
    v = {g for g in hvg if g.startswith("v")}
    assert len(v) >= 36 and len(hvg - v) <= 10


def test_biotype_filter_rescues_lincs_and_matches_unversioned(tmp_path):
    ann = pd.DataFrame({"gene": ["ENSG1.3", "ENSG2.1", "ENSG3.1", "ENSG4.2"],
                        "symbol": ["TP53", "LINC00470", "FOO", "XIST"],
                        "type_of_gene": ["protein-coding", "unknown", "pseudo", "ncRNA"]})
    ann.to_csv(tmp_path / "a.csv", index=False)
    a = select.load_annotation(str(tmp_path / "a.csv"))
    kept, rescued = select.biotype_filter(["ENSG1.9", "ENSG2.1", "ENSG3.1", "ENSG4.2"], a)
    assert kept == ["ENSG1.9", "ENSG2.1", "ENSG4.2"] and rescued == 1
    assert select.sex_linked_mask(["ENSG1.9", "ENSG4.2"], a).tolist() == [False, True]
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement**
```python
"""Which genes enter the network.

Two 2-component Gaussian mixtures, no hand-set threshold: one on mean
expression (expressed vs silent), one on the residual of a LOESS fit of log
variance on mean (more variable than expected at that expression level).
Biotype and sex-linked filters need gene annotation and are optional.
"""
import re

import numpy as np
import pandas as pd

KEEP_TYPES = {"protein-coding", "ncRNA"}
LNCRNA_SYMBOL = re.compile(r"^LINC\d+$|-AS\d+$")
SEX_LINKED = frozenset({
    "TBL1Y", "RPS4Y1", "RPS4Y2", "DDX3Y", "USP9Y", "UTY", "KDM5D", "EIF1AY",
    "NLGN4Y", "ZFY", "TXLNGY", "TMSB4Y", "PRKY", "XIST", "TSIX", "PRKX",
})


def base_id(gene):
    return str(gene).split(".")[0]


def _gmm_high(values, random_state):
    from sklearn.mixture import GaussianMixture
    x = np.asarray(values).reshape(-1, 1)
    gm = GaussianMixture(n_components=2, random_state=random_state, n_init=5).fit(x)
    high = int(np.argmax(gm.means_.ravel()))
    return gm.predict_proba(x)[:, high] > 0.5, gm


def expressed_genes(df, random_state=42):
    mean_expr = df.mean(axis=1)
    keep, gm = _gmm_high(mean_expr.values, random_state)
    return mean_expr[keep], {"n_expressed": int(keep.sum()),
                             "gmm_means": np.round(gm.means_.ravel(), 3).tolist()}


def highly_variable_genes(df, random_state=42):
    from scipy.stats import spearmanr
    from statsmodels.nonparametric.smoothers_lowess import lowess
    mean_expressed, info = expressed_genes(df, random_state)
    var_expr = df.loc[mean_expressed.index].var(axis=1)
    valid = var_expr > 0
    x = mean_expressed[valid].values
    y = np.log(var_expr[valid].values)
    order = np.argsort(x)
    span = x[order].max() - x[order].min()
    trend_sorted = lowess(y[order], x[order], frac=0.3, delta=0.01 * span, return_sorted=False)
    trend = np.empty_like(trend_sorted)
    trend[order] = trend_sorted
    residual = pd.Series(y - trend, index=mean_expressed[valid].index)
    keep, gm = _gmm_high(residual.values, random_state)
    rho, _ = spearmanr(residual.values, mean_expressed.loc[residual.index].values)
    hvg = set(residual.index[keep])
    info.update({"n_hvg": len(hvg), "gmm_residual_means": np.round(gm.means_.ravel(), 3).tolist(),
                 "rho_residual_mean": round(float(rho), 4)})
    return hvg, info


def load_annotation(path):
    from ..loader import read_table
    ann = read_table(path).reset_index()
    idcol = "gene" if "gene" in ann.columns else ann.columns[0]
    missing = {"symbol", "type_of_gene"} - set(ann.columns)
    if missing:
        raise SystemExit("ERROR: annotation file needs columns symbol and type_of_gene "
                         "(missing: {})".format(", ".join(sorted(missing))))
    ann["base"] = ann[idcol].map(base_id)
    return ann.drop_duplicates("base").set_index("base")[["symbol", "type_of_gene"]]


def query_mygene(gene_ids):
    try:
        import mygene
    except ImportError:
        raise SystemExit("ERROR: --biotype mygene needs the mygene package: pip install mygene")
    ids = sorted({base_id(g) for g in gene_ids})
    res = mygene.MyGeneInfo().querymany(ids, scopes="ensembl.gene", fields="symbol,type_of_gene",
                                        species="human", as_dataframe=True, verbose=False)
    res = res[~res.index.duplicated()]
    return res.reindex(ids)[["symbol", "type_of_gene"]].fillna({"type_of_gene": "unknown"})


def biotype_filter(genes, annotation):
    base = [base_id(g) for g in genes]
    types = annotation["type_of_gene"].reindex(base).fillna("unknown").astype(str).values
    symbols = annotation["symbol"].reindex(base).fillna("").astype(str).values
    rescue = (types == "unknown") & np.array([bool(LNCRNA_SYMBOL.search(s)) for s in symbols])
    types = np.where(rescue, "ncRNA", types)
    kept = [g for g, t in zip(genes, types) if t in KEEP_TYPES]
    return kept, int(rescue.sum())


def sex_linked_mask(genes, annotation):
    symbols = annotation["symbol"].reindex([base_id(g) for g in genes])
    return symbols.isin(SEX_LINKED).values
```
Note: `LNCRNA_SYMBOL.search` vs the notebook's `str.match`: `match` anchors at the start, so the notebook's `-AS\d+$` branch only matched symbols *starting* with `-AS` (never). Use `re.match` semantics (`LNCRNA_SYMBOL.match(s)`) to reproduce the paper; record this as a known quirk in the report note. If Task 11 matches with `.match`, keep `.match` and adjust the test (LINC00470 is still rescued).

- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 7: Transcriptomics — partial correlation, permutation FDR, gate

**Files:** Create `pyntacle/omics/transcriptomics/{infer.py,gate.py}`; Test `tests/omics/test_tx_infer.py`

**Interfaces:**
- Produces:
  - `infer.zscore_genes(df) -> DataFrame` (genes × samples).
  - `infer.standardised_samples(df, design=None) -> np.ndarray` samples × genes: z-scored, residualised on `design` and re-standardised when given.
  - `infer.lw_pcor(X, lam=None) -> (pcor float32[npairs], iu tuple, lam_hat float)`.
  - `infer.permutation_fdr(X, n_perm, seed) -> dict` keys `pcor, iu, order, sorted_abs, ranks, fdr, lam, null_max`.
  - `infer.edges_at_fdr(res, genes, level) -> DataFrame` columns `source, target, r, q_value` (empty if none).
  - `gate.auto_expression_gate(df, design=None, alpha=0.05, top=100, min_genes=300, grid=None) -> (quantile|None, diag DataFrame)`.

- [ ] **Step 1: failing tests**

```python
from omics.transcriptomics import gate, infer


def _ggm(n=300, p=40, seed=1):
    """Chain graph 0-1-2-...: known sparse precision matrix."""
    rng = np.random.default_rng(seed)
    P = np.eye(p)
    for i in range(0, p - 1, 2):
        P[i, i + 1] = P[i + 1, i] = 0.45
    X = rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=n)
    genes = ["g{}".format(i) for i in range(p)]
    return pd.DataFrame(X.T + 8.0, index=genes), {("g{}".format(i), "g{}".format(i + 1)) for i in range(0, p - 1, 2)}


def test_lw_pcor_with_frozen_lambda_is_deterministic():
    df, _ = _ggm()
    X = infer.standardised_samples(df)
    a, iu, lam = infer.lw_pcor(X)
    b, _, _ = infer.lw_pcor(X, lam=lam)
    assert 0 <= lam <= 1 and np.array_equal(a, b)


def test_permutation_fdr_recovers_planted_edges():
    df, truth = _ggm()
    res = infer.permutation_fdr(infer.standardised_samples(df), n_perm=3, seed=7)
    edges = infer.edges_at_fdr(res, np.array(df.index), 0.01)
    found = {tuple(sorted(e)) for e in zip(edges["source"], edges["target"])}
    assert len(found & truth) >= 0.9 * len(truth)
    assert len(found - truth) <= 2
    assert (edges["q_value"] <= 0.01).all() and (edges["r"] < 0).sum() == 0


def test_gate_stops_when_low_expression_artefact_is_removed():
    rng = np.random.default_rng(3)
    df, _ = _ggm(p=400)
    low = pd.DataFrame(rng.poisson(0.3, (100, 300)).astype(float), index=["z{}".format(i) for i in range(100)])
    shared = rng.normal(size=300)
    low.iloc[:50] += (shared > 1.2).astype(float) * 3   # zero-inflated co-occurrence
    q, diag = gate.auto_expression_gate(pd.concat([df, low]), min_genes=100)
    assert q is not None and q > 0 and diag["bias"].iloc[-1] == "no"
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement** — `infer.py` (functions copied from the notebook §10, restructured):
```python
"""Gene association network: Ledoit-Wolf shrinkage partial correlations,
edges called by a permutation FDR (Schäfer & Strimmer 2005; Tusher 2001).

Shrinkage is frozen at the observed value when the null is computed:
re-estimating it on permuted data inflates it and makes the null too narrow.
"""
import gc

import numpy as np
import pandas as pd

from ..covariates import residualise

N_RANKS = 800


def zscore_genes(df):
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0).dropna()


def standardised_samples(df, design=None):
    Z = zscore_genes(df)
    X = Z.T
    if design is not None:
        X = residualise(X, design.loc[X.index])
        X = (X - X.mean()) / X.std()
        X = X.dropna(axis=1)
    return X.values.astype(np.float64)


def lw_pcor(X, lam=None):
    n, p = X.shape
    Xc = X - X.mean(axis=0, keepdims=True)
    S = (Xc.T @ Xc) / n
    mu = np.trace(S) / p
    S2 = np.sum(S * S)
    d2 = (S2 - p * mu * mu) / p
    norms2 = np.einsum("ij,ij->i", Xc, Xc)
    b2 = (np.sum(norms2 ** 2) - n * S2) / (n * n * p)
    lam_hat = min(b2, d2) / d2
    lam_use = lam_hat if lam is None else lam
    Sh = (1.0 - lam_use) * S
    Sh.flat[:: p + 1] += lam_use * mu
    del S
    Theta = np.linalg.inv(Sh)
    del Sh
    d = np.sqrt(np.diag(Theta))
    Theta /= d[:, None]
    Theta /= d[None, :]
    iu = np.triu_indices(p, k=1)
    pcor = -Theta[iu].astype(np.float32)
    del Theta
    gc.collect()
    return pcor, iu, lam_hat


def permutation_fdr(X, n_perm=3, seed=20260731):
    n, p = X.shape
    pcor, iu, lam_obs = lw_pcor(X)
    absv = np.abs(pcor)
    rng = np.random.default_rng(seed)
    null_chunks = []
    for _ in range(n_perm):
        Xp = np.empty_like(X)
        for j in range(p):
            Xp[:, j] = X[rng.permutation(n), j]
        pcor_p, _, _ = lw_pcor(Xp, lam=lam_obs)
        null_chunks.append(np.abs(pcor_p))
        del Xp, pcor_p
    null = np.sort(np.concatenate(null_chunks))
    order = np.argsort(-absv)
    sorted_abs = absv[order]
    ranks = np.unique(np.round(np.geomspace(20, absv.size, N_RANKS)).astype(np.int64))
    exceed = (null.size - np.searchsorted(null, sorted_abs[ranks - 1], side="left")) / n_perm
    fdr = np.minimum(exceed / ranks, 1.0)
    fdr = np.minimum.accumulate(fdr[::-1])[::-1]
    return {"pcor": pcor, "iu": iu, "order": order, "sorted_abs": sorted_abs, "ranks": ranks,
            "fdr": fdr, "lam": float(lam_obs), "null_max": float(null[-1])}


def edges_at_fdr(res, genes, level):
    ok = np.where(res["fdr"] <= level)[0]
    if not ok.size:
        return pd.DataFrame(columns=["source", "target", "r", "q_value"])
    k = int(res["ranks"][ok[-1]])
    sel = res["order"][:k]
    # q of the edge at rank i: FDR at the first evaluated rank >= i
    pos = np.searchsorted(res["ranks"], np.arange(1, k + 1), side="left")
    return pd.DataFrame({"source": genes[res["iu"][0][sel]], "target": genes[res["iu"][1][sel]],
                         "r": res["pcor"][sel].astype(float), "q_value": res["fdr"][pos]})
```
Note: the planted-edge test uses positive precision entries, so the partial correlations are negative (`pcor = −Θij/√…`). Fix the assertion to `(edges["r"] > 0).sum() == 0` if that is what the maths gives — assert the sign the maths gives, not the other way round. Ranks below 20 are not evaluated (notebook grid starts at 20); `pos` maps them to rank 20.

`gate.py`:
```python
"""Self-terminating expression gate.

Weakly expressed genes, with their frequent zero counts, produce spurious
strong partial correlations. Raise a mean-expression quantile until the
strongest edges are no longer concentrated among the least expressed genes
(one-sided Mann-Whitney). The stopping point is chosen by the data.
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from .infer import lw_pcor, standardised_samples, zscore_genes

GRID = np.arange(0.0, 0.91, 0.05)


def expression_bias_pvalue(df, design=None, top=100):
    genes = zscore_genes(df).index
    X = standardised_samples(df.loc[genes], design)
    mean_expr = df.loc[genes].mean(axis=1).values
    pcor, iu, _ = lw_pcor(X)
    best = np.argsort(-np.abs(pcor))[:top]
    mask = np.zeros(X.shape[1], dtype=bool)
    mask[np.unique(np.concatenate([iu[0][best], iu[1][best]]))] = True
    pval = mannwhitneyu(mean_expr[mask], mean_expr[~mask], alternative="less").pvalue
    return float(pval), X.shape[1], float(mean_expr[mask].mean()), float(mean_expr[~mask].mean())


def auto_expression_gate(df, design=None, alpha=0.05, top=100, min_genes=300, grid=None):
    mean_expr = df.mean(axis=1)
    rows, chosen = [], None
    for q in (GRID if grid is None else grid):
        sub = df.loc[mean_expr >= mean_expr.quantile(q)]
        if sub.shape[0] < min_genes:
            break
        pval, p_eff, m_top, m_bg = expression_bias_pvalue(sub, design, top)
        rows.append({"quantile": round(float(q), 2), "genes": p_eff, "mean_top": round(m_top, 2),
                     "mean_background": round(m_bg, 2), "p_value": pval,
                     "bias": "yes" if pval < alpha else "no"})
        if pval >= alpha:
            chosen = round(float(q), 2)
            break
    return chosen, pd.DataFrame(rows)
```
Note: the notebook's `expression_bias_pvalue` z-scores then drops genes with zero variance (`dropna`) before computing means — the version above does the same via `zscore_genes(df).index`.

- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 8: Transcriptomics orchestration

**Files:** Modify `pyntacle/omics/transcriptomics/__init__.py`; Test `tests/omics/test_tx_run.py`

**Interfaces:**
- Consumes: Tasks 1–7.
- Produces: `transcriptomics.run(X, labels, *, meta=None, input_scale="auto", annotation=None, drop_sex_genes=False, covariates=None, gate_alpha=0.05, gate_top=100, gate_min_genes=300, fdr=0.001, n_perm=3, seed=20260731, random_state=42, prov) -> dict[group -> {"edges": DataFrame, "nodes": DataFrame, "stages": dict}]`. `annotation` is a DataFrame from `load_annotation`/`query_mygene` or None. `meta` is the metadata aligned on samples (needed for covariates). `prov` a `Provenance`. Values passed by the user are recorded as `user`; the CLI passes a set `user_set` of option names given explicitly, as keyword `user_set=frozenset()`.

- [ ] **Step 1: failing test**

```python
from omics.provenance import Provenance
from omics import transcriptomics


def test_run_end_to_end_on_synthetic_counts():
    rng = np.random.default_rng(5)
    n_t, n_n, p = 60, 40, 120
    P = np.eye(p)
    for i in range(0, 40, 2):
        P[i, i + 1] = P[i + 1, i] = 0.4
    lat = rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=n_t + n_n)
    mu = np.r_[np.full(80, 7.0), np.full(40, 0.3)]
    sd = np.r_[np.full(40, 1.2), np.full(40, 0.2), np.full(40, 0.2)]
    counts = rng.poisson(np.exp2(mu + sd * lat)).T
    X = pd.DataFrame(counts, index=["g{}".format(i) for i in range(p)],
                     columns=["s{}".format(i) for i in range(n_t + n_n)]).astype(float)
    labels = pd.Series(["T"] * n_t + ["N"] * n_n, index=X.columns)
    prov = Provenance("transcriptomics")
    out = transcriptomics.run(X, labels, gate_min_genes=20, fdr=0.01, prov=prov)
    assert set(out) == {"T", "N"}
    for g in out.values():
        assert len(g["edges"]) > 0
        assert set(g["edges"]["source"]) | set(g["edges"]["target"]) <= {"g{}".format(i) for i in range(40)}
    kinds = {(v["name"], v["kind"]) for v in prov.values}
    assert ("input_scale", "data-driven") in kinds and ("fdr", "default") in kinds
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement** `transcriptomics/__init__.py`:
```python
"""Bulk RNA-seq counts -> one gene association network per group.

Order follows the CRC case study (Preprocessing_v3 §9-10): counts, joint
median-of-ratios, per-group GMM selection, union, optional biotype and
sex-linked filters, per-group expression gate, Ledoit-Wolf partial
correlations with a permutation FDR.
"""
import numpy as np
import pandas as pd

from .. import covariates as cov
from . import gate as gate_mod
from . import infer, normalize, scale, select

DEFAULTS = {"gate_alpha": 0.05, "gate_top": 100, "gate_min_genes": 300,
            "fdr": 0.001, "n_perm": 3, "seed": 20260731}


def _kind(name, user_set):
    return "user" if name in user_set else "default"


def run(X, labels, *, prov, meta=None, input_scale="auto", annotation=None,
        drop_sex_genes=False, covariates=None, gate_alpha=0.05, gate_top=100,
        gate_min_genes=300, fdr=0.001, n_perm=3, seed=20260731, random_state=42,
        user_set=frozenset()):
    for name in DEFAULTS:
        prov.record("parameters", name, locals()[name], _kind(name, user_set))

    detected = scale.detect_scale(X) if input_scale == "auto" else input_scale
    prov.record("scale", "input_scale", detected,
                "data-driven" if input_scale == "auto" else "user")
    counts = scale.to_counts(X, detected)

    log_norm, sf = normalize.log_normalise(counts)
    prov.diagnostic("size_factors", sf.describe().round(4).to_dict())

    groups = list(dict.fromkeys(labels))
    per_group = {g: log_norm[labels.index[labels == g]] for g in groups}

    union = set()
    for g in groups:
        hvg, info = select.highly_variable_genes(per_group[g], random_state)
        prov.record("selection", "hvg_" + g, len(hvg), "data-driven",
                    "GMM expressed {}; rho(residual, mean) {}".format(
                        info["n_expressed"], info["rho_residual_mean"]))
        union |= hvg
    genes = sorted(union)
    prov.record("selection", "hvg_union", len(genes), "data-driven")

    if annotation is not None:
        genes, rescued = select.biotype_filter(genes, annotation)
        prov.record("selection", "after_biotype", len(genes), "user",
                    "protein-coding + ncRNA; {} lncRNA rescued by symbol".format(rescued))
    if drop_sex_genes:
        if annotation is None:
            raise SystemExit("ERROR: --drop-sex-genes needs gene symbols: pass --biotype")
        mask = select.sex_linked_mask(genes, annotation)
        genes = [g for g, m in zip(genes, mask) if not m]
        prov.record("selection", "sex_linked_removed", int(mask.sum()), "user")

    results = {}
    for g in groups:
        D = per_group[g].loc[genes]
        design = cov.design_matrix(meta.loc[D.columns], covariates) if covariates else None
        q, diag = gate_mod.auto_expression_gate(D, design, gate_alpha, gate_top, gate_min_genes)
        prov.diagnostic("gate_" + g, diag)
        if q is None:
            raise SystemExit("ERROR: group {}: no expression quantile removes the "
                             "low-expression bias (see report diagnostics gate_{})".format(g, g))
        mean_expr = D.mean(axis=1)
        D = D.loc[mean_expr >= mean_expr.quantile(q)]
        prov.record("gate", "quantile_" + g, q, "data-driven", "{} genes kept".format(D.shape[0]))

        kept = infer.zscore_genes(D).index
        X_s = infer.standardised_samples(D.loc[kept], design)
        res = infer.permutation_fdr(X_s, n_perm=n_perm, seed=seed)
        edges = infer.edges_at_fdr(res, np.array(kept), fdr)
        prov.record("network", "lambda_LW_" + g, round(res["lam"], 4), "data-driven")
        prov.record("network", "null_separation_" + g,
                    round(float(res["sorted_abs"][0] / res["null_max"]), 2), "data-driven",
                    "max |pcor| observed / under permutation")
        prov.record("network", "edges_" + g, len(edges), "data-driven",
                    "n={} p={}".format(D.shape[1], len(kept)))
        nodes = pd.DataFrame({"mean_log2_expr": D.mean(axis=1)})
        if annotation is not None:
            base = [select.base_id(i) for i in nodes.index]
            nodes["symbol"] = annotation["symbol"].reindex(base).values
            nodes["biotype"] = annotation["type_of_gene"].reindex(base).values
        results[g] = {"edges": edges, "nodes": nodes, "stages": {"log_norm": per_group[g], "final": D}}
    return results
```
Note: `locals()[name]` inside the loop reads the function arguments — it works because they are locals of `run`; if a linter objects, replace with an explicit dict `{"gate_alpha": gate_alpha, ...}`.

- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 9: Metagenomics — panel, CoDA, StARS, orchestration

**Files:** Create `pyntacle/omics/metagenomics/{__init__.py,panel.py,coda.py,infer.py}`; Test `tests/omics/test_metagenomics.py`

**Interfaces:**
- Produces:
  - `panel.prevalence(df) -> Series` (df samples × taxa); `panel.auto_prevalence(groups_dfs, grid) -> (threshold, table DataFrame)`; `panel.union_panel(groups_dfs, threshold) -> list`.
  - `coda.closure(a)`, `coda.multiplicative_replacement(a, delta=None)`, `coda.clr(a)` on numpy arrays (rows = samples); `coda.drop_allzero(df) -> (df, dropped list)`; `coda.coda_transform(df) -> DataFrame` CLR.
  - `infer.stars_glasso(X_df, n_subsample=50, beta=0.10, nlambda=30, lambda_min_ratio=0.05, random_state=0) -> dict` keys `edges` (DataFrame source,target,r), `lambda_hat`, `b`, `n_failed_fits`, `instability` (DataFrame lambda, instability).
  - `metagenomics.run(X, labels, *, prov, meta=None, prevalence="auto", covariates=None, stars_beta=0.10, n_sub=50, seed=0, user_set=frozenset()) -> dict[group -> {"edges","nodes","stages"}]`. `X` is features (taxa) × samples, as from `loader.load_inputs`.

- [ ] **Step 1: failing tests**

```python
from omics import metagenomics
from omics.metagenomics import coda, infer as minfer, panel
from omics.provenance import Provenance


def test_coda_matches_definitions_and_is_scale_invariant():
    a = np.array([[0.5, 0.0, 0.25, 0.25], [0.1, 0.2, 0.3, 0.4]])
    r = coda.multiplicative_replacement(a)
    assert np.allclose(r.sum(axis=1), 1) and (r > 0).all()
    assert np.isclose(r[0, 1], (1 / 4) ** 2)
    c = coda.clr(r)
    assert np.allclose(c.sum(axis=1), 0)
    pct = pd.DataFrame(a * 100)
    assert np.allclose(coda.coda_transform(pct).values, coda.coda_transform(pd.DataFrame(a)).values)


def test_auto_prevalence_is_lowest_threshold_below_min_n():
    rng = np.random.default_rng(0)
    big = pd.DataFrame(rng.random((50, 30)) * (rng.random((50, 30)) < np.linspace(0.05, 0.9, 30)))
    small = pd.DataFrame(rng.random((12, 30)) * (rng.random((12, 30)) < np.linspace(0.05, 0.9, 30)))
    th, table = panel.auto_prevalence({"A": big, "B": small}, np.round(np.arange(0.05, 0.51, 0.05), 2))
    kept = panel.union_panel({"A": big, "B": small}, th)
    assert len(kept) < 12
    lower = table[table["threshold"] < th]
    assert (lower["n_taxa"] >= 12).all()


def test_stars_recovers_planted_graph_and_is_deterministic():
    rng = np.random.default_rng(2)
    p = 12
    P = np.eye(p)
    for i in range(0, p - 1, 2):
        P[i, i + 1] = P[i + 1, i] = 0.45
    X = pd.DataFrame(rng.multivariate_normal(np.zeros(p), np.linalg.inv(P), size=300),
                     columns=["t{}".format(i) for i in range(p)])
    a = minfer.stars_glasso(X, n_subsample=20)
    b = minfer.stars_glasso(X, n_subsample=20)
    pairs = {tuple(sorted(e)) for e in zip(a["edges"]["source"], a["edges"]["target"])}
    truth = {("t{}".format(i), "t{}".format(i + 1)) for i in range(0, p - 1, 2)}
    assert truth <= pairs and a["lambda_hat"] == b["lambda_hat"]


def test_run_builds_one_network_per_group_on_shared_panel():
    rng = np.random.default_rng(4)
    taxa = ["t{}".format(i) for i in range(10)]
    X = pd.DataFrame(rng.dirichlet(np.ones(10), size=80).T, index=taxa,
                     columns=["s{}".format(i) for i in range(80)])
    labels = pd.Series(["T"] * 50 + ["N"] * 30, index=X.columns)
    prov = Provenance("metagenomics")
    out = metagenomics.run(X, labels, prov=prov, n_sub=10)
    assert set(out) == {"T", "N"}
    assert ("prevalence", "data-driven") in {(v["name"], v["kind"]) for v in prov.values}
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: implement**

`coda.py`:
```python
"""Compositional data: closure, zero replacement, centred log-ratio
(Aitchison 1982; Martín-Fernández et al. 2003). Same formulas as
scikit-bio's closure / multi_replace / clr, without the dependency."""
import numpy as np
import pandas as pd


def closure(a):
    a = np.asarray(a, dtype=float)
    return a / a.sum(axis=1, keepdims=True)


def multiplicative_replacement(a, delta=None):
    a = closure(a)
    d = (1.0 / a.shape[1]) ** 2 if delta is None else delta
    zeros = a == 0
    k = zeros.sum(axis=1, keepdims=True)
    out = np.where(zeros, d, a * (1.0 - k * d))
    return closure(out)


def clr(a):
    la = np.log(a)
    return la - la.mean(axis=1, keepdims=True)


def drop_allzero(df):
    zero = df.sum(axis=1) == 0
    return df.loc[~zero], list(df.index[zero])


def coda_transform(df):
    return pd.DataFrame(clr(multiplicative_replacement(closure(df.values))),
                        index=df.index, columns=df.columns)
```
Verify against scikit-bio once in the `omics` env (Task 11 does: identical networks ⇒ identical transform).

`panel.py`:
```python
"""Taxon panel shared by all groups (prevalence in any group, union).

Auto threshold: the lowest prevalence on the grid that leaves fewer taxa than
samples in the smallest group -- the limiting case for any covariance-based
estimator."""
import numpy as np
import pandas as pd

GRID = np.round(np.arange(0.05, 0.51, 0.05), 2)


def prevalence(df):
    return (df > 0).mean(axis=0)


def union_panel(groups_dfs, threshold):
    keep = set()
    for df in groups_dfs.values():
        pr = prevalence(df)
        keep |= set(pr.index[pr >= threshold])
    return sorted(keep)


def auto_prevalence(groups_dfs, grid=GRID):
    n_min = min(df.shape[0] for df in groups_dfs.values())
    rows, chosen = [], None
    for th in grid:
        n_taxa = len(union_panel(groups_dfs, th))
        rows.append({"threshold": float(th), "n_taxa": n_taxa, "n_min": n_min})
        if chosen is None and 2 <= n_taxa < n_min:
            chosen = float(th)
    if chosen is None:
        raise SystemExit("ERROR: no prevalence threshold on the grid leaves between 2 and {} "
                         "taxa; pass --prevalence explicitly".format(n_min - 1))
    return chosen, pd.DataFrame(rows)
```

`infer.py` — `stars_glasso` copied from `rebuild_export.py` (lines 43–110 of that file), with two changes: default `beta=0.10`, and returning an edges DataFrame instead of a networkx graph:
```python
"""Graphical lasso with the penalty chosen by StARS (Liu et al. 2010), the
estimator behind SPIEC-EASI (Kurtz et al. 2015). Deterministic for a seed."""
import warnings

import numpy as np
import pandas as pd


def _standardize(X):
    return (X - X.mean(axis=0)) / X.std(axis=0, ddof=1)


def _fit_precision(corr, alpha):
    from sklearn.covariance import graphical_lasso
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        for mode in ("cd", "lars"):
            try:
                _, prec = graphical_lasso(corr, alpha=alpha, mode=mode, max_iter=200)
            except Exception:
                continue
            if np.all(np.isfinite(prec)):
                return prec
    return None


def stars_glasso(X_df, n_subsample=50, beta=0.10, nlambda=30, lambda_min_ratio=0.05,
                 random_state=0):
    X = X_df.values
    n, p = X.shape
    taxa = np.array(X_df.columns, dtype=str)
    rng = np.random.default_rng(random_state)
    corr_full = np.corrcoef(_standardize(X), rowvar=False)
    lambda_max = np.abs(corr_full - np.diag(np.diag(corr_full))).max()
    lambda_path = np.logspace(np.log10(lambda_max), np.log10(lambda_max * lambda_min_ratio), nlambda)
    b = int(np.floor(((10 * np.sqrt(n) / n) if n > 144 else 0.8) * n))
    iu = np.triu_indices(p, k=1)
    presence = np.full((nlambda, n_subsample, len(iu[0])), np.nan)
    n_failed = 0
    for rep in range(n_subsample):
        idx = rng.choice(n, size=b, replace=False)
        corr_sub = np.corrcoef(_standardize(X[idx]), rowvar=False)
        for li, lam in enumerate(lambda_path):
            prec = _fit_precision(corr_sub, lam)
            if prec is None:
                n_failed += 1
                continue
            adj = np.abs(prec) > 1e-10
            np.fill_diagonal(adj, False)
            presence[li, rep] = adj[iu]
    theta = np.nanmean(presence, axis=1)
    instability = np.maximum.accumulate(np.nanmean(2 * theta * (1 - theta), axis=1))
    valid = np.where(instability <= beta)[0]
    k_sel = valid.max() if len(valid) else 0
    lambda_hat = lambda_path[k_sel]
    prec = _fit_precision(corr_full, lambda_hat)
    if prec is None:
        raise SystemExit("ERROR: graphical lasso did not converge at the selected lambda")
    d = np.sqrt(np.diag(prec))
    pcorr = -prec / np.outer(d, d)
    sel = [(i, j) for i, j in zip(*iu) if abs(prec[i, j]) > 1e-10]
    edges = pd.DataFrame({"source": [taxa[i] for i, _ in sel], "target": [taxa[j] for _, j in sel],
                          "r": [float(pcorr[i, j]) for i, j in sel]})
    return {"edges": edges, "lambda_hat": float(lambda_hat), "b": b, "n_failed_fits": n_failed,
            "instability": pd.DataFrame({"lambda": lambda_path, "instability": instability})}
```

`metagenomics/__init__.py`:
```python
"""Relative abundances -> one microbial association network per group.

Shared taxon panel (union prevalence), per-group closure, multiplicative
zero replacement and CLR, then StARS-selected graphical lasso -- the
SPIEC-EASI recipe, as in the CRC case study."""
import pandas as pd

from .. import covariates as cov
from . import coda, panel
from .infer import stars_glasso

DEFAULTS = {"stars_beta": 0.10, "n_sub": 50, "seed": 0}


def run(X, labels, *, prov, meta=None, prevalence="auto", covariates=None,
        stars_beta=0.10, n_sub=50, seed=0, user_set=frozenset()):
    values = {"stars_beta": stars_beta, "n_sub": n_sub, "seed": seed}
    for name, v in values.items():
        prov.record("parameters", name, v, "user" if name in user_set else "default")
    A = X.T.astype(float)                       # samples x taxa
    groups = list(dict.fromkeys(labels))
    by_group = {g: A.loc[labels.index[labels == g]] for g in groups}

    if prevalence == "auto":
        th, table = panel.auto_prevalence(by_group)
        prov.diagnostic("prevalence_grid", table)
        prov.record("panel", "prevalence", th, "data-driven",
                    "lowest threshold leaving fewer taxa than the smallest group's n")
    else:
        th = float(prevalence)
        prov.record("panel", "prevalence", th, "user")
    taxa = panel.union_panel(by_group, th)
    prov.record("panel", "n_taxa", len(taxa), "data-driven")

    results = {}
    for g in groups:
        sub, dropped = coda.drop_allzero(by_group[g][taxa])
        if dropped:
            prov.warn("group {}: dropped all-zero sample(s) {}".format(g, dropped))
        Z = coda.coda_transform(sub)
        if covariates:
            Z = cov.residualise(Z, cov.design_matrix(meta.loc[Z.index], covariates))
        fit = stars_glasso(Z, n_subsample=n_sub, beta=stars_beta, random_state=seed)
        prov.record("network", "lambda_" + g, round(fit["lambda_hat"], 4), "data-driven",
                    "StARS, subsample size {}, {} failed fits".format(fit["b"], fit["n_failed_fits"]))
        prov.record("network", "edges_" + g, len(fit["edges"]), "data-driven",
                    "n={} p={}".format(Z.shape[0], Z.shape[1]))
        prov.diagnostic("stars_" + g, fit["instability"])
        nodes = pd.DataFrame({"mean_rel_abundance": by_group[g][taxa].mean(axis=0),
                              "prevalence": panel.prevalence(by_group[g][taxa])})
        results[g] = {"edges": fit["edges"], "nodes": nodes, "stages": {"clr": Z}}
    return results
```

- [ ] **Step 4:** PASS. **Step 5:** stage.

---

### Task 10: CLI (parser, main dispatch, cli adapter, setup extra)

**Precondition:** the benchmark pilot has finished (`pgrep -f "bench.py run"` empty).

**Files:**
- Create: `pyntacle/omics/cli.py`
- Modify: `pyntacle/parser.py` (add subparser after `percolation`), `pyntacle/main.py` (first lines of `main()`), `setup.py` (`extras_require`)
- Test: `tests/omics/test_cli.py`

**Interfaces:**
- Consumes: `loader.load_inputs`, `tcga.tcga_groups`, `select.load_annotation/query_mygene`, `transcriptomics.run`, `metagenomics.run`, `export.write_network`, `Provenance`.
- Produces: `cli.run_omics(args) -> dict[group -> write_network result]`; parser `omics` with `dest="subcommand"`.

- [ ] **Step 1: failing tests**

```python
import subprocess
import sys

MAIN = __import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..", "pyntacle", "main.py")


def _abund(tmp_path):
    rng = np.random.default_rng(4)
    taxa = ["t{}".format(i) for i in range(10)]
    ids = ["s{}".format(i) for i in range(80)]
    pd.DataFrame(rng.dirichlet(np.ones(10), size=80).T, index=taxa, columns=ids).to_csv(
        tmp_path / "ab.tsv", sep="\t")
    pd.DataFrame({"grp": ["Tumor"] * 50 + ["Normal"] * 30}, index=ids).to_csv(tmp_path / "meta.tsv", sep="\t")


def test_cli_metagenomics_writes_networks_and_report(tmp_path):
    _abund(tmp_path)
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, MAIN, "omics", "metagenomics", "-i", str(tmp_path / "ab.tsv"),
                        "-m", str(tmp_path / "meta.tsv"), "--group-col", "grp", "-o", str(out),
                        "--n-sub", "10"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for f in ("ab_tumor.tsv", "ab_normal.graphml", "ab_report.json", "ab_report.tsv"):
        assert (out / f).exists(), f


def test_cli_requires_metadata_unless_tcga(tmp_path):
    _abund(tmp_path)
    r = subprocess.run([sys.executable, MAIN, "omics", "metagenomics", "-i", str(tmp_path / "ab.tsv"),
                        "-o", str(tmp_path / "o")], capture_output=True, text=True)
    assert r.returncode != 0 and "--metadata" in (r.stderr + r.stdout)


def test_existing_commands_do_not_import_omics():
    code = ("import sys; sys.path.insert(0, 'pyntacle'); import main; "
            "print('omics' in sys.modules)")
    root = __import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=root)
    assert r.stdout.strip().endswith("False"), r.stderr
```

- [ ] **Step 2:** Run → FAIL.

- [ ] **Step 3: implement**

`parser.py` — add before the final `return parser` (after the percolation block), in the file's tab indentation:
```python
	### Omics ###
	omics = subparsers.add_parser('omics', usage=Fore.GREEN + Style.BRIGHT + 'python3 main.py ' + Fore.RED + 'omics ' + Fore.MAGENTA + '{transcriptomics | metagenomics}' + Fore.CYAN + ' -i {matrix} -m {metadata} --group-col {column} -o {outdir} [optional parameters]' + Style.RESET_ALL,
		help='''Builds one network per sample group from a raw count (transcriptomics) or relative-abundance (metagenomics) matrix, ready for the other Pyntacle commands. Needs: pip install scikit-learn statsmodels''',
		description=Fore.RED + Style.BRIGHT + '''Pipelines:\n''' + Fore.GREEN + Style.BRIGHT + ''' · transcriptomics:''' + Style.RESET_ALL + Fore.CYAN + ''' raw counts (or log2(count+1)) -> median-of-ratios -> GMM gene selection -> expression gate -> Ledoit-Wolf partial correlations -> permutation FDR.\n\n''' + Fore.GREEN + Style.BRIGHT + ''' · metagenomics:''' + Style.RESET_ALL + Fore.CYAN + ''' relative abundances -> prevalence panel -> closure, multiplicative replacement, CLR -> graphical lasso with StARS.\n\n''' + Style.RESET_ALL + '''Edge list Weight = 1 - |r| (a distance, as Pyntacle expects); the signed r is in the GraphML.''',
		formatter_class=argparse.RawDescriptionHelpFormatter)
	omics.add_argument(dest='subcommand', choices=['transcriptomics', 'metagenomics'], help='Select the pipeline')
	omics.add_argument('-i', '--inputFile', required=True, help='-[required] Feature x sample matrix (or sample x feature: detected from the metadata ids). TSV, or CSV by extension; may be gzipped')
	omics.add_argument('-m', '--metadata', default=None, help='-[required unless --tcga] Sample metadata table, first column = sample id')
	omics.add_argument('--group-col', default=None, help='-[required with -m] Metadata column with the sample group (one network per group)')
	omics.add_argument('--groups', default=None, help='-[optional] Comma-separated group values to keep (default: all)')
	omics.add_argument('-o', '--outdir', required=True, help='-[required] Output directory (created if missing)')
	omics.add_argument('--prefix', default=None, help='-[optional] Output file prefix (default: input file name)')
	omics.add_argument('--sep', default=None, help='-[optional] Field separator (default: comma for .csv, tab otherwise)')
	omics.add_argument('--covariates', default=None, help='-[optional] Comma-separated metadata columns regressed out of every feature, per group')
	omics.add_argument('--seed', type=int, default=None, help='-[optional] Random seed (default: 20260731 transcriptomics, 0 metagenomics)')
	omics.add_argument('--save-stages', action='store_true', help='-[optional] Also write the intermediate matrices')
	omics.add_argument('--input-scale', choices=['auto', 'counts', 'log2p1'], default='auto', help='-[transcriptomics] Scale of the input values (default: detected)')
	omics.add_argument('--tcga', action='store_true', help='-[transcriptomics] Groups from TCGA barcodes (01 tumor, 11 normal), one aliquot per patient; -m not needed')
	omics.add_argument('--biotype', default=None, help="-[transcriptomics] 'mygene' or an annotation file (columns gene,symbol,type_of_gene): keep protein-coding + ncRNA")
	omics.add_argument('--drop-sex-genes', action='store_true', help='-[transcriptomics] Remove 16 sex-linked genes (needs --biotype)')
	omics.add_argument('--gate-alpha', type=float, default=0.05, help='-[transcriptomics] Significance of the expression-bias test (default 0.05)')
	omics.add_argument('--gate-top', type=int, default=100, help='-[transcriptomics] Strongest edges inspected by the gate (default 100)')
	omics.add_argument('--gate-min-genes', type=int, default=300, help='-[transcriptomics] Stop raising the gate below this many genes (default 300)')
	omics.add_argument('--fdr', type=float, default=0.001, help='-[transcriptomics] Edge FDR (default 0.001)')
	omics.add_argument('--n-perm', type=int, default=3, help='-[transcriptomics] Permutations for the null (default 3)')
	omics.add_argument('--prevalence', default='auto', help="-[metagenomics] Prevalence threshold, or 'auto' (default)")
	omics.add_argument('--stars-beta', type=float, default=0.10, help='-[metagenomics] StARS instability bound (default 0.10)')
	omics.add_argument('--n-sub', type=int, default=50, help='-[metagenomics] StARS subsamples (default 50)')
	omics._optionals.title = Fore.CYAN + Style.BRIGHT + "Arguments" + Style.RESET_ALL
	omics._positionals.title = Fore.MAGENTA + Style.BRIGHT + "Subcommand" + Style.RESET_ALL
```

`main.py` — first statements of `main(args)`, before `if args.directed:`:
```python
	# omics builds networks, it does not read one: none of the graph flags below
	# exist on its parser. Imported here so the other commands never load its
	# optional dependencies.
	if args.command == "omics":
		from omics.cli import run_omics
		run_omics(args)
		return
```

`omics/cli.py`:
```python
"""`pyntacle omics` arguments -> pipeline -> files."""
import os
import sys

from . import require
from .export import write_network
from .loader import check_groups, load_inputs, read_table
from .provenance import Provenance

# CLI option -> run() keyword, for options whose explicit use is recorded as "user"
_TX = {"gate_alpha": "gate_alpha", "gate_top": "gate_top", "gate_min_genes": "gate_min_genes",
       "fdr": "fdr", "n_perm": "n_perm", "seed": "seed"}
_MG = {"stars_beta": "stars_beta", "n_sub": "n_sub", "seed": "seed"}


def _given(argv):
    """Option names the user typed, as argparse dests."""
    return frozenset(a.lstrip("-").split("=")[0].replace("-", "_") for a in argv if a.startswith("--"))


def run_omics(args, argv=None):
    require()
    given = _given(sys.argv if argv is None else argv)
    prov = Provenance(args.subcommand)
    groups = args.groups.split(",") if args.groups else None
    covariates = args.covariates.split(",") if args.covariates else None
    meta = None

    if args.subcommand == "transcriptomics" and args.tcga:
        from .transcriptomics.tcga import tcga_groups
        X = read_table(args.inputFile, args.sep)
        labels, dropped = tcga_groups(list(X.columns))
        if groups:
            labels = labels[labels.isin(groups)]
        X = X[labels.index].astype(float)
        prov.record("input", "tcga_dropped_other_type", len(dropped["other_type"]), "user")
        prov.record("input", "tcga_dropped_duplicate", len(dropped["duplicate"]), "user")
        if args.metadata and covariates:
            meta = read_table(args.metadata, args.sep)
            meta.index = meta.index.astype(str)
    else:
        if not args.metadata or not args.group_col:
            raise SystemExit("ERROR: --metadata and --group-col are required"
                             + (" (or --tcga)" if args.subcommand == "transcriptomics" else ""))
        X, labels = load_inputs(args.inputFile, args.metadata, args.group_col, groups, args.sep, prov)
        if covariates:
            meta = read_table(args.metadata, args.sep)
            meta.index = meta.index.astype(str)
    check_groups(labels)
    for g, n in labels.value_counts().items():
        prov.record("input", "n_" + str(g), int(n), "data-driven")

    if args.subcommand == "transcriptomics":
        from . import transcriptomics
        from .transcriptomics import select
        annotation = None
        if args.biotype == "mygene":
            annotation = select.query_mygene(X.index)
        elif args.biotype:
            annotation = select.load_annotation(args.biotype)
        result = transcriptomics.run(
            X, labels, prov=prov, meta=meta, input_scale=args.input_scale, annotation=annotation,
            drop_sex_genes=args.drop_sex_genes, covariates=covariates, gate_alpha=args.gate_alpha,
            gate_top=args.gate_top, gate_min_genes=args.gate_min_genes, fdr=args.fdr,
            n_perm=args.n_perm, seed=20260731 if args.seed is None else args.seed,
            user_set=frozenset(v for k, v in _TX.items() if k in given))
    else:
        from . import metagenomics
        result = metagenomics.run(
            X, labels, prov=prov, meta=meta, prevalence=args.prevalence, covariates=covariates,
            stars_beta=args.stars_beta, n_sub=args.n_sub, seed=0 if args.seed is None else args.seed,
            user_set=frozenset(v for k, v in _MG.items() if k in given))

    prefix = args.prefix or os.path.basename(args.inputFile).split(".")[0]
    os.makedirs(args.outdir, exist_ok=True)
    written = {}
    for g, res in result.items():
        written[g] = write_network(res["edges"], res["nodes"], args.outdir, prefix, g)
        print("{}: {} nodes, {} edges -> {}".format(g, written[g]["n_nodes"], written[g]["n_edges"],
                                                    written[g]["edgelist"]))
        if args.save_stages:
            from .export import safe_name
            for name, df in res["stages"].items():
                df.to_csv(os.path.join(args.outdir, "{}_{}_{}.tsv.gz".format(prefix, safe_name(g), name)),
                          sep="\t")
    prov.write(args.outdir, prefix)
    for w in prov.warnings:
        print("WARNING: " + w)
    print("Report: " + os.path.join(args.outdir, prefix + "_report.tsv"))
    return written
```

`setup.py` — add to `setup(...)`:
```python
    extras_require={"omics": ["scikit-learn", "statsmodels"], "omics-annotation": ["mygene"]},
```

- [ ] **Step 4:** Run `pytest tests/omics -v` and the full suite `pytest -q tests` → all pass (the full suite guards the main.py change).
- [ ] **Step 5:** stage `pyntacle/omics/cli.py pyntacle/parser.py pyntacle/main.py setup.py tests/omics/test_cli.py`.

---

### Task 11: Reproduction of the paper

**Files:** Create `tests/omics/test_reproduce_paper.py`

- [ ] **Step 1: write the test**

```python
"""Slow: rebuild the CRC case-study networks from the raw files.

Runs only with PYNTACLE_SLOW=1 and the article_pynta data present.
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

ART = "/home/manu/work/article_pynta"
MAIN = os.path.join(os.path.dirname(__file__), "..", "..", "pyntacle", "main.py")
pytestmark = pytest.mark.skipif(not (os.environ.get("PYNTACLE_SLOW") and os.path.isdir(ART)),
                                reason="slow reproduction test: set PYNTACLE_SLOW=1")


def _pairs(df, a, b):
    return {tuple(sorted(x)) for x in zip(df[a].astype(str), df[b].astype(str))}


def _jaccard(x, y):
    return len(x & y) / len(x | y)


@pytest.mark.parametrize("level", ["genus", "family"])
def test_metagenomics_matches_export_v2_exactly(tmp_path, level):
    d = os.path.join(ART, "metagen", "data")
    r = subprocess.run([sys.executable, MAIN, "omics", "metagenomics",
                        "-i", os.path.join(d, "bacteria.sample.relabund.{}.txt".format(level)),
                        "-m", os.path.join(d, "sample_metadata_{}.txt".format(level)),
                        "--group-col", "Definition",
                        "--groups", "Primary Solid Tumor,Solid Tissue Normal",
                        "-o", str(tmp_path), "--prefix", level], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    ref_dir = os.path.join(ART, "metagen", "metagenomics_output", "pyntacle_export_v2")
    for grp, ref in (("primary_solid_tumor", "tumor"), ("solid_tissue_normal", "normal")):
        g = __import__("igraph").Graph.Read_GraphML(str(tmp_path / "{}_{}.graphml".format(level, grp)))
        mine = {tuple(sorted((g.vs[e.source]["name"], g.vs[e.target]["name"]))): e["assoc_weight"]
                for e in g.es}
        refdf = pd.read_csv(os.path.join(ref_dir, "{}_{}_glasso_dual.tsv".format(level, ref)), sep="\t")
        theirs = {tuple(sorted((a, b))): w for a, b, w in zip(refdf["N1"], refdf["N2"], refdf["assoc_weight"])}
        assert set(mine) == set(theirs)
        assert max(abs(mine[k] - theirs[k]) for k in mine) < 1e-5
    report = pd.read_csv(tmp_path / "{}_report.tsv".format(level), sep="\t")
    assert float(report.loc[report["name"] == "prevalence", "value"].iloc[0]) == 0.15


def test_transcriptomics_is_equivalent_to_network_final_gen3(tmp_path):
    c = os.path.join(ART, "Colon")
    r = subprocess.run([sys.executable, MAIN, "omics", "transcriptomics",
                        "-i", os.path.join(c, "GeneExp_COAD-Xena_StarCount", "TCGA-COAD.star_counts.tsv"),
                        "--tcga", "--biotype", os.path.join(c, "preprocessing_gen3", "mygene_biotype_cache_hvg.csv"),
                        "--drop-sex-genes", "-o", str(tmp_path), "--prefix", "coad"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for grp, ref in (("tumor", "tumore"), ("normal", "normale")):
        mine = pd.read_csv(tmp_path / "coad_{}.tsv".format(grp), sep="\t")
        theirs = pd.read_csv(os.path.join(c, "network_final_gen3", "edges_{}_FDR0.001.csv.gz".format(ref)))
        me, th = _pairs(mine, "N1", "N2"), _pairs(theirs, "gene1", "gene2")
        nodes_me = set(mine["N1"]) | set(mine["N2"])
        nodes_th = set(theirs["gene1"]) | set(theirs["gene2"])
        assert _jaccard(me, th) >= 0.95, (len(me), len(th))
        assert _jaccard(nodes_me, nodes_th) >= 0.95
```

- [ ] **Step 2:** Run `PYNTACLE_SLOW=1 pytest tests/omics/test_reproduce_paper.py -v -s`.
Expected: metagenomics PASS; transcriptomics PASS. On a transcriptomics mismatch, resolve the two faithfulness notes in Task 5 (`valid` in median-of-ratios) and Task 6 (`match` vs `search` for lncRNA rescue) in favour of whichever reproduces the reference, then rerun. The reference networks were built from `hvg_final_*` which already included the biotype filter from a MyGene cache covering exactly the HVG union; a Jaccard below 0.95 that survives both fixes must be investigated (compare the HVG union sizes: reference 3,364 tumour / 1,963 normal genes after the gate), not papered over by lowering the threshold.

- [ ] **Step 3:** stage the test file.

---

### Task 12: Documentation

**Files:**
- Create: `Documentation/source/cli/omics/index.rst`, `Documentation/source/omics/omics.rst`
- Modify: `Documentation/source/cli/index.rst` (toctree + `omics/index`), `Documentation/source/index.rst` (CLI card: "12 commands", add omics; new card "Omics to network"), `Documentation/source/installation.rst` (optional extra)

- [ ] **Step 1:** Write `cli/omics/index.rst` in the style of `cli/generate/index.rst` (`:orphan:` header is **not** used here since it is in the toctree): title, one-paragraph purpose, "Specific usage" console block with both sub-commands, "Synopsis" table of every option with default and kind (data-driven/default/user) copied from spec §5–§6, "Outputs" (edge list with Weight = distance, GraphML attributes, report JSON/TSV, `--save-stages`), "Examples": a toy run on the synthetic abundance table used by `tests/omics/test_cli.py`, and the exact CRC case-study command lines of Task 11, followed by `python main.py keyplayer kp-finder -t edgelist -i out/genus_primary_solid_tumor.tsv -w -k 2 -a greedy -o kp/`.

- [ ] **Step 2:** Write `omics/omics.rst` "Methods and references": one subsection per pipeline step, each ending with its citation as an RST external link to the DOI (same link style as `keyPlayers/keyPlayers.rst:18`). References (DOIs from `article_pynta/article/methods_final_draft.md`):
  - Anders & Huber 2010 — https://doi.org/10.1186/gb-2010-11-10-r106
  - Love et al. 2014 — https://doi.org/10.1186/s13059-014-0550-8
  - McLachlan & Peel 2000 — https://doi.org/10.1002/0471721182
  - Cleveland 1979 — https://doi.org/10.1080/01621459.1979.10481038
  - Wu et al. 2013 (MyGene.info) — https://doi.org/10.1093/nar/gks1114; Xin et al. 2016 — https://doi.org/10.1186/s13059-016-0953-9
  - Mann & Whitney 1947 — https://doi.org/10.1214/aoms/1177730491
  - Ledoit & Wolf 2004 — https://doi.org/10.1016/S0047-259X(03)00096-4
  - Schäfer & Strimmer 2005 — https://doi.org/10.2202/1544-6115.1175
  - Tusher et al. 2001 — https://doi.org/10.1073/pnas.091062498; Storey & Tibshirani 2003 — https://doi.org/10.1073/pnas.1530509100
  - Aitchison 1982 — https://doi.org/10.1111/j.2517-6161.1982.tb01195.x; Lovell et al. 2015 — https://doi.org/10.1371/journal.pcbi.1004075; Gloor et al. 2017 — https://doi.org/10.3389/fmicb.2017.02224
  - Martín-Fernández et al. 2003 — https://doi.org/10.1023/A:1023866030544
  - Friedman et al. 2008 — https://doi.org/10.1093/biostatistics/kxm045
  - Liu et al. 2010 (StARS) — https://pubmed.ncbi.nlm.nih.gov/25152607/
  - Zhao et al. 2012 (huge) — https://pubmed.ncbi.nlm.nih.gov/26834510/
  - Kurtz et al. 2015 (SPIEC-EASI) — https://doi.org/10.1371/journal.pcbi.1004226
  - Goldman et al. 2020 (UCSC Xena) — https://doi.org/10.1038/s41587-020-0546-8; Dohlman et al. 2021 (TCMA) — https://doi.org/10.1016/j.chom.2020.12.001
  Include a "Weights and distances" subsection (why Weight = 1 − |r|) and a "What is data-driven" table.

- [ ] **Step 3:** Update the three existing pages as listed above.

- [ ] **Step 4:** Build: `cd Documentation && conda run -n graphtacle_debug make html 2>&1 | tail -5`
Expected: `build succeeded`, 0 warnings (the docs were at 0 warnings before; keep it).

- [ ] **Step 5:** stage the doc files.

---

### Task 13: Final verification

- [ ] **Step 1:** `pytest -q tests` (full suite) → all pass, count = previous + new.
- [ ] **Step 2:** `PYNTACLE_SLOW=1 pytest tests/omics/test_reproduce_paper.py -q` → pass.
- [ ] **Step 3:** Update the spec status line and the memory note; give the user the git commands (no attribution) listing every file of Tasks 1–12.
