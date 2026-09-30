import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

from pyntacle.omics.metagenomics import taxonomy

METAPHLAN = ["k__Bacteria", "k__Bacteria|p__Firmicutes",
             "k__Bacteria|p__Firmicutes|c__Clostridia|o__Eubacteriales|f__Lachnospiraceae|g__Blautia",
             "k__Bacteria|p__Firmicutes|c__Clostridia|o__Eubacteriales|f__Lachnospiraceae|g__Blautia"
             "|s__Blautia_obeum",
             "k__Bacteria|p__Firmicutes|c__Clostridia|o__Eubacteriales|f__Oscillospiraceae"
             "|g__Faecalibacterium", "UNCLASSIFIED"]


def _table(index):
    return pd.DataFrame(np.ones((len(index), 3)), index=index, columns=["s1", "s2", "s3"])


def test_rank_of_lineages_from_each_tool():
    assert taxonomy.feature_rank(METAPHLAN[2]) == "g"
    assert taxonomy.feature_rank(METAPHLAN[3]) == "s"
    # QIIME 2: SILVA 138 "d__", padded unassigned levels, Greengenes spaces, SILVA 132 "D_5__"
    assert taxonomy.feature_rank("d__Bacteria;p__Firmicutes;c__Clostridia;o__X;f__Y;__") == "g"
    assert taxonomy.feature_rank("k__Bacteria; p__Firmicutes") == "p"
    assert taxonomy.feature_rank("D_0__Bacteria;D_5__Blautia") == "g"
    assert taxonomy.feature_rank("Blautia") is None and taxonomy.feature_rank("UNCLASSIFIED") is None


def test_mixed_ranks_need_rank_and_keep_one_level():
    with pytest.raises(SystemExit, match="mixes taxonomic ranks.*--rank"):
        taxonomy.select_rank(_table(METAPHLAN))
    out = taxonomy.select_rank(_table(METAPHLAN), "genus")
    assert list(out.index) == ["g__Blautia", "g__Faecalibacterium"]
    with pytest.raises(SystemExit, match="no feature at rank strain"):
        taxonomy.select_rank(_table(METAPHLAN), "strain")


def test_single_rank_table_is_detected_and_unassigned_named_by_parent():
    idx = ["d__Bacteria;p__F;c__C;o__O;f__Lachnospiraceae;g__Blautia",
           "d__Bacteria;p__F;c__C;o__O;f__Lachnospiraceae;__", "Unassigned;__;__;__;__;__"]
    out = taxonomy.select_rank(_table(idx))
    assert list(out.index) == ["g__Blautia", "f__Lachnospiraceae"]


def test_plain_ids_pass_through_and_refuse_rank():
    t = _table(["Blautia", "Prevotella"])
    assert taxonomy.select_rank(t) is t
    with pytest.raises(SystemExit, match="lineages"):
        taxonomy.select_rank(t, "genus")


def test_duplicate_short_names_keep_the_full_lineage():
    idx = ["k__A|p__X|c__C|o__O|f__F|g__Same", "k__B|p__Y|c__C|o__O|f__F|g__Same"]
    assert list(taxonomy.select_rank(_table(idx)).index) == idx
