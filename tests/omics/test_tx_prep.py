import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

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
    # g1, g2 geometric means sqrt(200), sqrt(800); g3 enters with s2 only (ratio 1)
    assert np.allclose(sf.values, [1 / np.sqrt(2), np.sqrt(2)])
    log_norm, _ = normalize.log_normalise(counts)
    assert np.isclose(log_norm.loc["g1", "s1"], np.log2(10 * np.sqrt(2) + 1))
