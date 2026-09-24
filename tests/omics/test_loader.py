import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

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
    with pytest.raises(SystemExit, match="N n=3"):
        loader.check_groups(lab)
