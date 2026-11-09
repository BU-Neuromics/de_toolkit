"""Tests for detk-util gather (#25)."""

import json
import os
import pathlib

import pandas
import pytest

from de_toolkit import report_specs
from de_toolkit.util import Gather, detect_format, gather, main

DATA = pathlib.Path(__file__).parent / "data" / "gather"
SALMON = sorted(DATA.glob("salmon/*/quant.sf"))
KALLISTO = sorted(DATA.glob("kallisto/*/abundance.tsv"))
HTSEQ = [DATA / "htseq" / "s1.counts.txt", DATA / "htseq" / "s2.counts.txt"]
HTSEQ_OTHER = DATA / "htseq" / "s3_other_gtf.counts.txt"
FC_MULTI = DATA / "featurecounts" / "counts.txt"
FC_ONE = DATA / "featurecounts" / "C.txt"


@pytest.mark.parametrize(
    "path, fmt",
    [
        (SALMON[0], "salmon"),
        (KALLISTO[0], "kallisto"),
        (HTSEQ[0], "htseq"),
        (FC_MULTI, "featurecounts"),
    ],
)
def test_detect_format(path, fmt):
    assert detect_format(path) == fmt


def test_detect_format_unknown(tmp_path):
    fn = tmp_path / "counts.csv"
    fn.write_text("gene,a,b\ng1,1,2\n")
    with pytest.raises(ValueError, match="pass --format"):
        detect_format(fn)


def test_detect_featurecounts_without_comment(tmp_path):
    fn = tmp_path / "fc.txt"
    fn.write_text("Geneid\tChr\tStart\tEnd\tStrand\tLength\tA.bam\ng1\tchr1\t1\t9\t+\t9\t3\n")
    assert detect_format(fn) == "featurecounts"


def test_gather_salmon_defaults():
    obj = Gather(SALMON)
    out = obj.output
    # quant.sf everywhere: samples are named after their directories
    assert list(out.columns) == ["sample_1__salmon_counts", "sample_2__salmon_counts"]
    assert list(out.index) == ["ENST0001.1", "ENST0002.3", "ENST0003.1"]
    assert out.index.name is None
    # NumReads, kept as written
    assert out.loc["ENST0003.1"].tolist() == ["9.512", "6.488"]
    p = obj.properties
    assert p["format"] == "salmon" and p["column"] == "NumReads"
    assert (p["num_samples"], p["num_features"], p["num_values_filled"]) == (2, 3, 0)


def test_gather_salmon_column_and_name_from():
    out = gather(SALMON, column="TPM", name_from=r"(sample_\d+)__salmon_counts")
    assert list(out.columns) == ["sample_1", "sample_2"]
    assert out.loc["ENST0001.1"].tolist() == ["120.5", "98.1"]
    # a pattern without a group names the sample by its whole match
    out = gather(SALMON, name_from=r"sample_\d+")
    assert list(out.columns) == ["sample_1", "sample_2"]


def test_gather_kallisto():
    out = gather(KALLISTO, fmt="kallisto")
    assert list(out.columns) == ["ctrl", "trt"]
    assert out.loc["ENST0003.1"].tolist() == ["9.5", "6.5"]


def test_gather_htseq_counters_left_out():
    obj = Gather(HTSEQ)
    out = obj.output
    assert list(out.columns) == ["s1.counts", "s2.counts"]
    assert list(out.index) == ["ENSG01", "ENSG02", "ENSG03"]
    assert out.loc["ENSG01"].tolist() == ["10", "20"]
    counters = obj.properties["htseq_counters"]
    assert counters["__no_feature"] == {"s1.counts": 100.0, "s2.counts": 90.0}
    assert len(counters) == 5


def test_gather_featurecounts_multi_column_and_single():
    out = gather([FC_MULTI, FC_ONE])
    # each count column is named from its header (the BAM path)
    assert list(out.columns) == ["A", "B", "C"]
    assert out.loc["ENSG01"].tolist() == ["11", "22", "13"]
    out = gather([FC_MULTI], column="bam/B.bam", name_from=r"(\w+)\.bam")
    assert list(out.columns) == ["B"]


def test_gather_featurecounts_column_by_position():
    out = gather([FC_ONE], column=6)
    assert list(out.columns) == ["C"]


def test_gather_ids_kept_as_written(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("007\t1\n7\t2\n")
    b.write_text("007\t3\n7\t4\n")
    out = gather([a, b])
    assert list(out.index) == ["007", "7"]
    assert out.loc["007"].tolist() == ["1", "3"]


def test_gather_mismatch_is_an_error():
    with pytest.raises(ValueError, match="do not list the same features") as e:
        Gather(HTSEQ + [HTSEQ_OTHER])
    assert "s1.counts lacks 1 (e.g. ENSG04)" in str(e.value)
    assert "s3_other_gtf.counts lacks 1 (e.g. ENSG02)" in str(e.value)


def test_gather_mismatch_fill():
    obj = Gather(HTSEQ + [HTSEQ_OTHER], on_mismatch="fill")
    out = obj.output
    assert list(out.index) == ["ENSG01", "ENSG02", "ENSG03", "ENSG04"]
    assert out.loc["ENSG02"].tolist() == ["0", "1", "0"]
    assert out.loc["ENSG04"].tolist() == ["0", "0", "1"]
    p = obj.properties
    assert (p["num_features_filled"], p["num_values_filled"], p["num_features_dropped"]) == (
        2,
        3,
        0,
    )
    assert p["mismatch_examples"] == ["ENSG02", "ENSG04"]


def test_gather_mismatch_drop():
    obj = Gather(HTSEQ + [HTSEQ_OTHER], on_mismatch="drop")
    assert list(obj.output.index) == ["ENSG01", "ENSG03"]
    assert obj.properties["num_features_dropped"] == 2


def test_gather_mixed_formats_refused():
    with pytest.raises(ValueError, match="not all the same format"):
        Gather([SALMON[0], KALLISTO[0]])


def test_gather_duplicate_names_refused():
    with pytest.raises(ValueError, match="more than once|more than one file"):
        Gather(SALMON, name_from=r"salmon")


def test_gather_name_from_no_match():
    with pytest.raises(ValueError, match="does not match"):
        Gather(SALMON, name_from=r"nope_(\d+)")


def test_gather_non_numeric_values(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("g1\t1\ng2\tlots\n")
    with pytest.raises(ValueError, match="non-numeric"):
        Gather([a], fmt="htseq")


def test_gather_duplicate_feature(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("g1\t1\ng1\t2\n")
    with pytest.raises(ValueError, match="more than once"):
        Gather([a])


def test_gather_bad_column():
    with pytest.raises(ValueError, match="--column"):
        Gather(SALMON, column="Counts")


def test_gather_cli(tmp_path):
    out_fn = tmp_path / "counts.csv"
    report_dir = tmp_path / "report"
    main(
        [
            "detk-util",
            "gather",
            "--name-from=(sample_\\d+)",
            "-o",
            str(out_fn),
            f"--report-dir={report_dir}",
            # a quoted glob is expanded by gather itself
            str(DATA / "salmon" / "*" / "quant.sf"),
        ]
    )
    assert out_fn.read_text().splitlines() == [
        ",sample_1,sample_2",
        "ENST0001.1,42.000,35.000",
        "ENST0002.3,0.000,7.000",
        "ENST0003.1,9.512,6.488",
    ]
    # the matrix reads back as detk reads a counts file
    counts = pandas.read_csv(out_fn, index_col=0)
    assert counts.shape == (3, 2)

    (json_fn,) = os.listdir(report_dir / "json")
    with open(report_dir / "json" / json_fn) as f:
        mod = json.load(f)
    assert mod["name"] == "gather"
    assert mod["in_file_path"] is None
    assert mod["params"]["files"] == [str(p) for p in SALMON]
    assert mod["params"]["format"] == "salmon"
    assert mod["properties"]["num_samples"] == 2


def test_gather_cli_mismatch_exits(tmp_path):
    with pytest.raises(SystemExit):
        main(["detk-util", "gather", "--no-report", *map(str, HTSEQ + [HTSEQ_OTHER])])


def test_gather_cli_glob_without_match_exits(tmp_path):
    with pytest.raises(SystemExit):
        main(["detk-util", "gather", "--no-report", str(tmp_path / "*.sf")])


def test_gather_report_view():
    obj = Gather(HTSEQ + [HTSEQ_OTHER], on_mismatch="fill")
    family, title, _, view = report_specs.view_for(obj.json)
    assert family == "util" and title
    assert view["type"] == "kv"
    labels = {it["label"]: it["value"] for it in view["items"]}
    assert labels["samples"] == 3
    assert labels["features"] == 4
    assert labels["features filled with 0"] == 2
    assert "ENSG04" in view["note"]


def test_gather_report_view_without_properties_is_raw():
    _, _, _, view = report_specs.view_for({"name": "gather", "properties": {}})
    assert view["type"] == "raw"
