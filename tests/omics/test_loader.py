import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from pyntacle.omics import loader


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


def test_read_table_skips_tool_banners_and_keeps_hash_headers(tmp_path):
    (tmp_path / "mp.txt").write_text("#mpa_v30_CHOCOPhlAn_201901\nclade_name\tNCBI_tax_id\ts1\n"
                                     "k__Bacteria\t2\t100.0\n")
    (tmp_path / "biom.tsv").write_text("# Constructed from biom file\n#OTU ID\ts1\ts2\nasv1\t3\t4\n")
    (tmp_path / "q2.tsv").write_text("sample-id\tage\n#q2:types\tnumeric\ns1\t50\ns2\t61\n")
    mp = loader.read_table(str(tmp_path / "mp.txt"))
    assert list(mp.columns) == ["NCBI_tax_id", "s1"] and list(mp.index) == ["k__Bacteria"]
    biom = loader.read_table(str(tmp_path / "biom.tsv"))
    assert list(biom.columns) == ["s1", "s2"] and biom.loc["asv1", "s2"] == 4
    q2 = loader.read_table(str(tmp_path / "q2.tsv"))
    assert list(q2.index) == ["s1", "s2"] and q2["age"].dtype.kind in "if"


def test_read_table_explains_binary_qiime_files(tmp_path):
    (tmp_path / "table.qza").write_bytes(b"PK")
    with pytest.raises(SystemExit, match="qiime tools export"):
        loader.read_table(str(tmp_path / "table.qza"))


def test_load_inputs_drops_annotation_columns(tmp_path):
    ids = ["s{}".format(i) for i in range(10)]
    X = pd.DataFrame(np.arange(20).reshape(2, 10), index=["t1", "t2"], columns=ids)
    X["taxonomy"] = ["k__A", "k__B"]
    X.to_csv(tmp_path / "x.tsv", sep="\t")
    _meta(ids, ["T"] * 5 + ["N"] * 5).to_csv(tmp_path / "m.tsv", sep="\t")
    Xa, _ = loader.load_inputs(str(tmp_path / "x.tsv"), str(tmp_path / "m.tsv"), "cond")
    assert list(Xa.columns) == ids


@pytest.mark.parametrize("problem", ["dup_sample", "dup_feature", "nan"])
def test_load_inputs_refuses_ambiguous_tables(tmp_path, problem):
    ids = ["s{}".format(i) for i in range(10)]
    X = pd.DataFrame(np.arange(20, dtype=float).reshape(2, 10), index=["g1", "g2"], columns=ids)
    meta = _meta(ids, ["T"] * 5 + ["N"] * 5)
    if problem == "dup_sample":
        meta = pd.concat([meta, meta.iloc[:1]])
    elif problem == "dup_feature":
        X.index = ["g1", "g1"]
    else:
        X.iloc[0, 3] = np.nan
    X.to_csv(tmp_path / "x.tsv", sep="\t")
    meta.to_csv(tmp_path / "m.tsv", sep="\t")
    with pytest.raises(SystemExit, match={"dup_sample": "metadata", "dup_feature": "feature id",
                                          "nan": "missing value"}[problem]):
        loader.load_inputs(str(tmp_path / "x.tsv"), str(tmp_path / "m.tsv"), "cond")
