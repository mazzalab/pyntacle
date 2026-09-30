import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from pyntacle.omics.transcriptomics import normalize, scale, tcga


def test_detect_scale():
    counts = pd.DataFrame([[0, 5], [10, 200]], dtype=float)
    assert scale.detect_scale(counts) == "counts"
    assert scale.detect_scale(np.log2(counts + 1)) == "log2p1"
    with pytest.raises(SystemExit):
        scale.detect_scale(pd.DataFrame([[-1.5, 2.2]]))


def test_detect_scale_refuses_log_tpm():
    rng = np.random.default_rng(0)
    log_tpm = pd.DataFrame(np.round(np.log2(rng.lognormal(1, 2, (200, 10)) + 1), 4))
    with pytest.raises(SystemExit, match="TPM"):
        scale.detect_scale(log_tpm)


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
    # g1, g2 geometric means sqrt(200), sqrt(800); g3 enters with s2 only (ratio 1)
    assert np.allclose(sf.values, [1 / np.sqrt(2), np.sqrt(2)])
    log_norm, _ = normalize.log_normalise(counts)
    assert np.isclose(log_norm.loc["g1", "s1"], np.log2(10 * np.sqrt(2) + 1))


def test_tcga_types_parse_and_barcode_orientation():
    assert tcga.parse_types("01:tumor, 06:metastatic") == {"01": "tumor", "06": "metastatic"}
    for bad in ("1:tumor", "01", "01:a,11:a"):
        with pytest.raises(SystemExit, match="--tcga-types"):
            tcga.parse_types(bad)
    X = pd.DataFrame(np.ones((2, 3)), index=["TCGA-AA-0001-01A", "TCGA-AA-0002-11A"],
                     columns=["g1", "g2", "g3"])
    assert list(tcga.orient_barcodes(X).columns) == list(X.index)
    with pytest.raises(SystemExit, match="TCGA barcodes"):
        tcga.orient_barcodes(pd.DataFrame(np.ones((2, 2)), index=["a", "b"], columns=["c", "d"]))


def test_tcga_groups_with_other_codes():
    cols = ["TCGA-AA-0001-01A", "TCGA-AA-0002-06A", "TCGA-AA-0003-06A", "sample_x"]
    labels, dropped = tcga.tcga_groups(cols, {"06": "metastatic"})
    assert set(labels) == {"metastatic"} and len(labels) == 2
    assert dropped["other_type"] == ["TCGA-AA-0001-01A", "sample_x"]
