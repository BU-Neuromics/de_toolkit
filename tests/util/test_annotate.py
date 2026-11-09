"""Tests for detk-util annotate (#29)."""

import json
import os

import pandas
import pytest

from de_toolkit import report_specs
from de_toolkit.util import Annotate, annotate, main


@pytest.fixture
def result():
    # shaped like detk-de output read without an index: the IDs in column 0
    return pandas.DataFrame(
        {
            "Unnamed: 0": ["ENSG01.3", "ENSG02.1", "ENSG03.2"],
            "log2FoldChange": [1.5, -2.0, 0.1],
            "padj": [0.01, 0.2, 0.9],
        }
    )


@pytest.fixture
def mapping():
    return pandas.DataFrame(
        {
            "gene_id": ["ENSG01", "ENSG02", "ENSG02", "ENSG04"],
            "symbol": ["A1BG", "A2M", "A2M", "NAT1"],
            "entrez": ["1", "2", "3", "9"],
        }
    )


def test_annotate_without_strip_versions_maps_nothing(result, mapping):
    obj = Annotate(result, mapping)
    assert obj.properties["num_mapped"] == 0
    assert obj.properties["num_unmapped"] == 3
    assert obj.output["symbol"].isna().all()


def test_annotate_strip_versions(result, mapping):
    obj = Annotate(result, mapping, strip_versions=True)
    out = obj.output
    # rows keep their order, number and original (versioned) IDs
    assert list(out.index) == ["ENSG01.3", "ENSG02.1", "ENSG03.2"]
    assert out.index.name is None
    assert list(out.columns) == ["log2FoldChange", "padj", "symbol", "entrez"]
    assert out.loc["ENSG01.3", "symbol"] == "A1BG"
    # several mapping rows collapse to their distinct values
    assert out.loc["ENSG02.1", "symbol"] == "A2M"
    assert out.loc["ENSG02.1", "entrez"] == "2;3"
    assert pandas.isna(out.loc["ENSG03.2", "symbol"])
    p = obj.properties
    assert (p["num_features"], p["num_mapped"], p["num_unmapped"]) == (3, 2, 1)
    assert p["num_multimapped"] == 1
    assert p["columns_added"] == ["symbol", "entrez"]
    assert p["unmapped_examples"] == ["ENSG03.2"]


def test_annotate_map_to_and_names(result, mapping):
    out = annotate(
        result,
        mapping,
        idcol="Unnamed: 0",
        map_from="gene_id",
        map_to="symbol",
        strip_versions=True,
    )
    assert list(out.columns) == ["log2FoldChange", "padj", "symbol"]


def test_annotate_map_to_positions(result, mapping):
    out = annotate(result, mapping, map_to=[2], strip_versions=True)
    assert list(out.columns) == ["log2FoldChange", "padj", "entrez"]


def test_annotate_drop_unmapped(result, mapping):
    obj = Annotate(result, mapping, strip_versions=True, drop_unmapped=True)
    assert list(obj.output.index) == ["ENSG01.3", "ENSG02.1"]
    assert obj.properties["num_dropped"] == 1


def test_annotate_column_collision_is_suffixed(result, mapping):
    result = result.assign(symbol=["x", "y", "z"])
    out = annotate(result, mapping, strip_versions=True)
    assert out["symbol"].tolist() == ["x", "y", "z"]
    assert out.loc["ENSG01.3", "symbol_annot"] == "A1BG"


def test_annotate_bad_column(result, mapping):
    with pytest.raises(ValueError, match="--map-from"):
        Annotate(result, mapping, map_from="nope")
    with pytest.raises(ValueError, match="no mapping columns"):
        Annotate(result, mapping, map_to="gene_id")


def test_annotate_cli(tmp_path, result, mapping):
    res_fn = tmp_path / "res.csv"
    map_fn = tmp_path / "map.tsv"
    out_fn = tmp_path / "out.csv"
    report_dir = tmp_path / "report"
    # written as detk-de writes: an unnamed index column
    result.set_index("Unnamed: 0").rename_axis(None).to_csv(res_fn)
    mapping.to_csv(map_fn, sep="\t", index=False)

    main(
        [
            "detk-util",
            "annotate",
            "--strip-versions",
            "--map-to=symbol",
            "-o",
            str(out_fn),
            f"--report-dir={report_dir}",
            str(res_fn),
            str(map_fn),
        ]
    )
    out = pandas.read_csv(out_fn, index_col=0)
    assert list(out.columns) == ["log2FoldChange", "padj", "symbol"]
    assert out.loc["ENSG02.1", "symbol"] == "A2M"

    (json_fn,) = os.listdir(report_dir / "json")
    with open(report_dir / "json" / json_fn) as f:
        mod = json.load(f)
    assert mod["name"] == "annotate"
    assert mod["properties"]["num_mapped"] == 2
    assert mod["params"]["strip_versions"] is True
    assert mod["params"]["mapping_fn"] == str(map_fn)


def test_annotate_cli_bad_column_exits(tmp_path, result, mapping):
    res_fn = tmp_path / "res.csv"
    map_fn = tmp_path / "map.csv"
    result.to_csv(res_fn, index=False)
    mapping.to_csv(map_fn, index=False)
    with pytest.raises(SystemExit):
        main(["detk-util", "annotate", "--no-report", "--map-from=nope", str(res_fn), str(map_fn)])


def test_annotate_report_view(result, mapping):
    obj = Annotate(result.assign(**{"Unnamed: 0": ["<b>.1", "ENSG02.1", "x"]}), mapping)
    family, title, _, view = report_specs.view_for(obj.json)
    assert family == "util" and title
    assert view["type"] == "kv"
    labels = {it["label"]: it["value"] for it in view["items"]}
    assert labels["features in"] == 3
    assert labels["mapped"] == 0
    # the note is plain text (the page renders it as text, #65): IDs as written
    assert "<b>" in view["note"] and "&lt;" not in view["note"]


def test_annotate_report_view_without_properties_is_raw():
    _, _, _, view = report_specs.view_for({"name": "annotate", "properties": {}})
    assert view["type"] == "raw"


def _run_cli(tmp_path, result_text, mapping_text, *opts):
    res_fn = tmp_path / "res.csv"
    map_fn = tmp_path / "map.tsv"
    out_fn = tmp_path / "out.csv"
    res_fn.write_text(result_text)
    map_fn.write_text(mapping_text)
    main(
        ["detk-util", "annotate", "--no-report", "-o", str(out_fn), *opts, str(res_fn), str(map_fn)]
    )
    return out_fn.read_text()


def test_annotate_cli_numeric_ids_with_gaps(tmp_path):
    # Entrez-keyed results with a missing and an empty ID: no float IDs, no
    # crash, every row written back as it was read
    out = _run_cli(
        tmp_path,
        "entrez,lfc\n1,0.50\nNA,0.2\n,0.3\n3,1e-05\n",
        "entrez\tsymbol\n1\tA1BG\n3\tC3\n",
    )
    assert out.splitlines() == [
        "entrez,lfc,symbol",
        "1,0.50,A1BG",
        "NA,0.2,",
        ",0.3,",
        "3,1e-05,C3",
    ]


def test_annotate_cli_numeric_ids_leading_zeros(tmp_path):
    out = _run_cli(tmp_path, "id,lfc\n007,1\n42,2\n", "id\tsymbol\n007\tBOND\n7\tSEVEN\n")
    assert out.splitlines() == ["id,lfc,symbol", "007,1,BOND", "42,2,"]


def test_annotate_missing_ids_are_never_joined():
    result = pandas.DataFrame({"id": ["1", None, "", "NA", "3"], "lfc": [1, 2, 3, 4, 5]})
    mapping = pandas.DataFrame({"id": ["1", "3", "NA"], "symbol": ["A", "C", "N"]})
    obj = Annotate(result, mapping)
    assert obj.output["symbol"].tolist()[0] == "A"
    assert obj.output["symbol"].iloc[1:4].isna().all()
    p = obj.properties
    assert (p["num_mapped"], p["num_unmapped"], p["num_missing_ids"]) == (2, 3, 3)
    assert p["unmapped_examples"] == []


def test_annotate_float_ids_with_nan_do_not_crash():
    # a library caller passing a float ID column gets no crash in the warning
    result = pandas.DataFrame({"id": [1.0, float("nan"), 3.0], "lfc": [1, 2, 3]})
    mapping = pandas.DataFrame({"id": ["1.0"], "symbol": ["A"]})
    obj = Annotate(result, mapping)
    assert obj.properties["num_missing_ids"] == 1
    assert obj.properties["unmapped_examples"] == ["3.0"]


def test_annotate_empty_mapped_value_is_unmapped():
    result = pandas.DataFrame({"id": ["g1", "g2", "g3"], "lfc": [1, 2, 3]})
    mapping = pandas.DataFrame(
        {
            "id": ["g1", "g2", "g3", "g3"],
            "symbol": ["A", None, "", "  "],
            "entrez": ["1", "2", None, None],
        }
    )
    # only symbol added: g2 and g3 have no symbol, so they are unmapped
    obj = Annotate(result, mapping, map_to="symbol")
    assert obj.properties["num_mapped"] == 1
    assert obj.properties["num_multimapped"] == 0
    obj = Annotate(result, mapping, map_to="symbol", drop_unmapped=True)
    assert list(obj.output.index) == ["g1"]
    # with entrez too, g2 has a value and counts as mapped; g3 still does not
    obj = Annotate(result, mapping, drop_unmapped=True)
    assert list(obj.output.index) == ["g1", "g2"]
    assert pandas.isna(obj.output.loc["g2", "symbol"])


def test_annotate_duplicate_result_ids(result, mapping):
    result = pandas.concat([result, result.iloc[[1, 2]]], ignore_index=True)
    obj = Annotate(result, mapping, strip_versions=True)
    out = obj.output
    assert list(out.index) == ["ENSG01.3", "ENSG02.1", "ENSG03.2", "ENSG02.1", "ENSG03.2"]
    assert out["entrez"].tolist()[1] == out["entrez"].tolist()[3] == "2;3"
    p = obj.properties
    assert (p["num_features"], p["num_mapped"], p["num_unmapped"]) == (5, 3, 2)
    assert p["num_multimapped"] == 2
    # rows are counted, example IDs are not repeated
    assert p["unmapped_examples"] == ["ENSG03.2"]


def test_annotate_cli_header_only_mapping(tmp_path):
    out = _run_cli(tmp_path, "id,lfc\ng1,1\ng2,2\n", "id\tsymbol\n")
    assert out.splitlines() == ["id,lfc,symbol", "g1,1,", "g2,2,"]
    out = _run_cli(tmp_path, "id,lfc\ng1,1\n", "id\tsymbol\n", "--drop-unmapped")
    assert out.splitlines() == ["id,lfc,symbol"]


def test_annotate_idcol_not_first_keeps_column_order(tmp_path):
    out = _run_cli(
        tmp_path, "idx,gene,lfc\n0,g1,1\n1,g2,2\n", "gene\tsymbol\ng2\tB\n", "-i", "gene"
    )
    assert out.splitlines() == ["idx,gene,lfc,symbol", "0,g1,1,", "1,g2,2,B"]
