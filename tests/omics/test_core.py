import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

import json

import omics
from omics.provenance import Provenance


def test_missing_dependencies_reports_pip_names(monkeypatch):
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec",
                        lambda m, *a: None if m == "statsmodels" else real(m, *a))
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
