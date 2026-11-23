"""detk-util tidy, tidy-counts and tidy-covs: the tidied column data is written
as it was read, and each subcommand records its step in the report and the
Process Run Crate (#114)."""

import json
from importlib.resources import files as pkg_files

import jsonschema
import pandas
import pytest

from de_toolkit.util import Tidy, main

# the counts have samples S1..S3 and P1; the sample sheet is out of order,
# misses P1 and has X9, which is not counted
COUNTS = "gene,S1,S2,S3,P1\ng1,1,2,3,4\ng2,5,6,7,8\n"
SHEET = 'sample,condition,note\nS3,ctrl,"a, b"\nS1,ctrl,\nX9,treat,x\nS2,treat,1.50\n'
# the sheet's rows, as written, by sample
SHEET_ROWS = {
    "S3": 'S3,ctrl,"a, b"',
    "S1": "S1,ctrl,",
    "X9": "X9,treat,x",
    "S2": "S2,treat,1.50",
}


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text(COUNTS)
    (tmp_path / "samples.csv").write_text(SHEET)
    return tmp_path


def lines(path):
    return path.read_text().splitlines()


def module_docs(cwd, report_dir="detk_report"):
    json_dir = cwd / report_dir / "json"
    return [json.loads(p.read_text()) for p in sorted(json_dir.glob("*.json"))]


def crate_graph(cwd, report_dir="detk_report"):
    "the crate's graph; it is in the report directory, rooted there (DETK-0280)"
    crate = json.loads((cwd / report_dir / "ro-crate-metadata.json").read_text())
    return {e["@id"]: e for e in crate["@graph"]}


# ------------------------------------------------------- the column data


def test_tidy_p_writes_the_sheet_as_read(work):
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    # the input's header, its columns in its order, no counts column added;
    # the rows of the samples in both, in the counts' order, as written
    assert lines(work / "s.csv") == ["sample,condition,note"] + [
        SHEET_ROWS[s] for s in ("S1", "S2", "S3")
    ]


def test_tidy_covs_writes_the_sheet_as_read(work):
    (work / "counts3.csv").write_text("gene,S2,S3,S1\ng1,1,2,3\n")
    main(["detk-util", "tidy-covs", "--no-report", "-o", "s.csv", "counts3.csv", "samples.csv"])
    assert lines(work / "s.csv") == ["sample,condition,note"] + [
        SHEET_ROWS[s] for s in ("S2", "S3", "S1")
    ]


def test_a_sheet_with_its_own_counts_column_keeps_it(work):
    (work / "samples.csv").write_text("sample,counts,condition\nS1,10,a\nS2,20,b\nS3,30,a\n")
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "s.csv") == ["sample,counts,condition", "S1,10,a", "S2,20,b", "S3,30,a"]


def test_an_unnamed_first_header_cell_stays_unnamed(work):
    (work / "samples.csv").write_text(",condition\nS1,a\nS2,b\nS3,a\n")
    (work / "c3.csv").write_text("gene,S1,S2,S3\ng1,1,2,3\n")
    main(["detk-util", "tidy-covs", "--no-report", "-o", "s.csv", "c3.csv", "samples.csv"])
    assert lines(work / "s.csv") == [",condition", "S1,a", "S2,b", "S3,a"]


@pytest.mark.parametrize("ids", [("001", "002"), ("1", "3")])
def test_a_short_header_sheet_with_numeric_looking_ids(work, ids):
    # R's write.table(sep=","): no header cell over the row names
    a, b = ids
    (work / "counts.csv").write_text(f"gene,{a},{b},S3,P1\ng1,1,2,3,4\n")
    (work / "samples.csv").write_text(
        f'"condition","dose"\n"{b}","treat",""\n"{a}","ctrl","1.50"\n'
    )
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "c.csv") == [f"gene,{a},{b}", "g1,1,2"]
    assert lines(work / "s.csv") == [",condition,dose", f"{a},ctrl,1.50", f"{b},treat,"]


@pytest.mark.parametrize(
    "sheet",
    [
        '"condition"\n"S1","a"\n"S2","b"\n',
        'condition\n"S1","a"\n"S2","b"\n',
        "condition\nS1\ta\nS2\tb\n",
        '"condition"\n"S1" "a"\n"S2" "b"\n',
    ],
    ids=["quoted", "unquoted", "tab", "quoted space"],
)
def test_a_one_field_short_header_sheet(work, sheet):
    # R's write.table(sep=...) with one column: the header has no delimiter,
    # its rows do (release/short-header)
    (work / "counts.csv").write_text("gene,S1,S2\ng1,1,2\ng2,3,4\n")
    (work / "samples.csv").write_text(sheet)
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "c.csv") == ["gene,S1,S2", "g1,1,2", "g2,3,4"]
    assert lines(work / "s.csv") == [",condition", "S1,a", "S2,b"]


def test_a_one_field_short_header_sheet_with_padded_ids(work):
    (work / "counts.csv").write_text("gene,001,002\ng1,1,2\n")
    (work / "samples.csv").write_text('"condition"\n"002","b"\n"001","a"\n')
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "s.csv") == [",condition", "001,a", "002,b"]


def test_a_bare_quoted_id_list_stays_one_column(work):
    (work / "counts.csv").write_text("gene,S1,S2,S3\ng1,1,2,3\n")
    (work / "samples.csv").write_text('"sample"\n"S3"\n"S1"\n')
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "c.csv") == ["gene,S1,S3", "g1,1,3"]
    assert lines(work / "s.csv") == ["sample", "S1", "S3"]


def test_an_unquoted_id_list_with_a_spaced_first_id_keeps_it(work):
    # DETK-0320: Excel does not quote "ctrl 1", and the list stays one
    # column, so tidy keeps the sample rather than dropping it
    (work / "counts.csv").write_text("gene,ctrl 1,S2,S3\ng1,1,2,3\n")
    (work / "samples.csv").write_text("sample\nctrl 1\nS2\nS3\n")
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "c.csv") == ["gene,ctrl 1,S2,S3", "g1,1,2,3"]
    assert lines(work / "s.csv") == ["sample", "ctrl 1", "S2", "S3"]


def test_an_unquoted_id_list_with_every_id_spaced(work):
    (work / "counts.csv").write_text("gene,sample 1,sample 2\ng1,1,2\n")
    (work / "samples.csv").write_text("sample\nsample 2\nsample 1\n")
    main(
        [
            "detk-util",
            "tidy",
            "--no-report",
            "-o",
            "c.csv",
            "-p",
            "s.csv",
            "counts.csv",
            "samples.csv",
        ]
    )
    assert lines(work / "c.csv") == ["gene,sample 1,sample 2", "g1,1,2"]
    assert lines(work / "s.csv") == ["sample", "sample 1", "sample 2"]


def test_a_header_neither_as_long_nor_one_short_is_an_error(work):
    (work / "samples.csv").write_text("condition\nS1,a,b\nS2,a,b\n")
    with pytest.raises(SystemExit):
        main(["detk-util", "tidy", "--no-report", "-o", "c.csv", "counts.csv", "samples.csv"])


def test_a_ragged_one_field_header_sheet_is_an_error(work, capsys):
    # release/ragged-sheet: the sheet read as one column, so S1 ('S1,a')
    # matched no counts column and tidy exited 0 without it
    (work / "counts.csv").write_text("gene,S1,S2,S3\ng1,1,2,3\n")
    (work / "samples.csv").write_text("condition\nS1,a\nS2\nS3\n")
    with pytest.raises(SystemExit) as e:
        main(
            ["detk-util", "tidy", "--no-report", "-o", "c.csv", "-p", "out.csv"]
            + ["counts.csv", "samples.csv"]
        )
    assert e.value.code == 1
    err = capsys.readouterr().err.splitlines()
    assert err == [
        "detk-util: error: samples.csv: the header 'condition' has one field and its data"
        " lines split unalike on comma: line 2 'S1,a' has 2 fields, line 3 'S2' has 1"
        " field; quote a field that holds the delimiter, or give every line the same"
        " fields (--verbose for the traceback)"
    ]
    assert not (work / "c.csv").exists()
    assert not (work / "out.csv").exists()


def test_the_out_delimiter_applies_to_the_sheet(work):
    main(
        ["detk-util", "tidy", "--no-report", "-d", "\t", "-o", "c.tsv", "-p", "s.tsv"]
        + ["counts.csv", "samples.csv"]
    )
    assert lines(work / "s.tsv")[:2] == ["sample\tcondition\tnote", "S1\tctrl\t"]


# ------------------------------------------------------------ the counts


def test_tidy_and_tidy_counts_write_the_counts_as_before(work):
    main(["detk-util", "tidy", "--no-report", "-o", "c.csv", "counts.csv", "samples.csv"])
    assert lines(work / "c.csv") == ["gene,S1,S2,S3", "g1,1,2,3", "g2,5,6,7"]

    (work / "samples3.csv").write_text("sample,condition\nS3,a\nS1,b\n")
    main(["detk-util", "tidy-counts", "--no-report", "-o", "c.csv", "counts.csv", "samples3.csv"])
    assert lines(work / "c.csv") == ["gene,S1,S3", "g1,1,3", "g2,5,7"]


def test_the_module_leaves_its_inputs_as_they_were():
    counts = pandas.DataFrame([[1, 2, 3]], columns=["A", "B", "C"], index=["g"])
    sheet = pandas.DataFrame({"x": ["a", "b"]}, index=pandas.Index(["B", "A"], name="sample"))
    tidied = Tidy(counts, sheet, command="tidy")
    assert list(sheet.columns) == ["x"]
    assert list(tidied.column_data.columns) == ["x"]
    assert tidied.column_data.index.name == "sample"
    assert list(tidied.column_data.index) == ["A", "B"]
    assert tidied.properties["counts_samples_dropped"] == ["C"]
    assert tidied.properties["column_data_samples_dropped"] == []


# ---------------------------------------------------- report and crate


def schema():
    return json.loads(pkg_files("de_toolkit").joinpath("module_schema.json").read_text())


def test_tidy_p_records_in_the_report_and_the_crate(work):
    main(
        ["detk-util", "tidy", "--report-dir=rep", "-o", "c.csv", "-p", "s.csv"]
        + ["counts.csv", "samples.csv"]
    )
    (doc,) = module_docs(work, "rep")
    jsonschema.validate(doc, schema())
    assert doc["name"] == "tidy"
    assert doc["in_file_path"] == "counts.csv"
    assert doc["column_data_path"] == "samples.csv"
    assert doc["out_file_path"] == "c.csv"
    assert doc["in_file_paths"] == ["counts.csv", "samples.csv"]
    assert doc["out_file_paths"] == ["c.csv", "s.csv"]
    p = doc["properties"]
    assert p["num_samples"] == 3
    assert p["counts_samples_dropped"] == ["P1"]
    assert p["column_data_samples_dropped"] == ["X9"]
    assert (work / "rep" / "detk_report.html").exists()

    g = crate_graph(work, "rep")
    (action,) = [e for e in g.values() if e["@type"] == "CreateAction"]
    assert action["name"] == "detk-util tidy run"
    assert g[action["instrument"]["@id"]]["name"] == "detk-util tidy"
    files = [o["@id"] for o in action["object"] if g[o["@id"]]["@type"] == "File"]
    assert files == ["../counts.csv", "../samples.csv"]
    assert [r["@id"] for r in action["result"]] == ["../c.csv", "../s.csv"]


@pytest.mark.parametrize(
    "command,name,out",
    [("tidy-counts", "tidycounts", "c.csv"), ("tidy-covs", "tidycovs", "s.csv")],
)
def test_tidy_counts_and_covs_record(work, command, name, out):
    (work / "samples3.csv").write_text("sample,condition\nS1,a\nS2,b\nS3,a\nP1,b\n")
    main(["detk-util", command, "-o", out, "counts.csv", "samples3.csv"])
    (doc,) = module_docs(work)
    jsonschema.validate(doc, schema())
    assert doc["name"] == name
    assert doc["in_file_paths"] == ["counts.csv", "samples3.csv"]
    assert doc["out_file_paths"] == [out]

    g = crate_graph(work)
    (action,) = [e for e in g.values() if e["@type"] == "CreateAction"]
    assert action["name"] == f"detk-util {command} run"
    assert [r["@id"] for r in action["result"]] == [f"../{out}"]


@pytest.mark.parametrize("command", ["tidy", "tidy-counts", "tidy-covs"])
def test_no_report_writes_no_report(work, command):
    (work / "samples3.csv").write_text("sample,condition\nS1,a\nS2,b\nS3,a\nP1,b\n")
    main(["detk-util", command, "--no-report", "-o", "out.csv", "counts.csv", "samples3.csv"])
    assert (work / "out.csv").exists()
    assert not (work / "detk_report").exists()
    assert not (work / "ro-crate-metadata.json").exists()


@pytest.mark.parametrize(
    "command,counts_samples,sheet_samples",
    [
        ("tidy", ["A", "B", "C"], ["B", "A", "D"]),
        ("tidy-counts", ["A", "B", "C"], ["B", "A"]),
        ("tidy-covs", ["A", "B"], ["B", "A", "D"]),
    ],
)
def test_tidy_report_view(command, counts_samples, sheet_samples):
    from de_toolkit import report_specs

    counts = pandas.DataFrame([range(len(counts_samples))], columns=counts_samples, index=["g"])
    sheet = pandas.DataFrame({"x": "a"}, index=sheet_samples)
    family, _, _, view = report_specs.view_for(Tidy(counts, sheet, command).json)
    assert family == "util"
    assert view["type"] == "kv"
    assert {"label": "samples kept", "value": 2} in view["items"]


def test_tidy_report_view_without_properties_is_raw():
    from de_toolkit import report_specs

    assert report_specs.view_for({"name": "tidy", "properties": {}})[3] == {"type": "raw"}
