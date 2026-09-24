import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("statsmodels")

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
