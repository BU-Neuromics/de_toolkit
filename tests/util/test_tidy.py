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


def crate_graph(cwd):
    crate = json.loads((cwd / "ro-crate-metadata.json").read_text())
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

    g = crate_graph(work)
    (action,) = [e for e in g.values() if e["@type"] == "CreateAction"]
    assert action["name"] == "detk-util tidy run"
    assert g[action["instrument"]["@id"]]["name"] == "detk-util tidy"
    files = [o["@id"] for o in action["object"] if g[o["@id"]]["@type"] == "File"]
    assert files == ["counts.csv", "samples.csv"]
    assert [r["@id"] for r in action["result"]] == ["c.csv", "s.csv"]


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
    assert [r["@id"] for r in action["result"]] == [out]


@pytest.mark.parametrize("command", ["tidy", "tidy-counts", "tidy-covs"])
def test_no_report_writes_no_report(work, command):
    (work / "samples3.csv").write_text("sample,condition\nS1,a\nS2,b\nS3,a\nP1,b\n")
    main(["detk-util", command, "--no-report", "-o", "out.csv", "counts.csv", "samples3.csv"])
    assert (work / "out.csv").exists()
    assert not (work / "detk_report").exists()
    assert not (work / "ro-crate-metadata.json").exists()
