"""Tests for the sniffed reading of delimited tables (#47): a one-column file
is read as one column, not split on a letter of its header."""

import gzip
import io
import logging

import pandas
import pytest

from de_toolkit.common import read_delimited, read_id_table, sniff_delimiter

_IDS = ["ENSG01", "ENSG02", "ENSG03"]


@pytest.mark.parametrize(
    "line,expected",
    [
        ("id", None),
        ("gene_id", None),
        ("ENSG00000001.5", None),
        ('"gene_id"', None),
        ("", None),
        ("id,score", ","),
        ("id\tscore", "\t"),
        ("id;score", ";"),
        ("id|score", "|"),
        ("id score", " "),
        ("gene id,score", ","),
    ],
)
def test_sniff_delimiter(line, expected):
    assert sniff_delimiter(line) == expected


@pytest.mark.parametrize("header", ["id", "gene_id"])
def test_read_delimited_one_column_with_header(tmp_path, header):
    fn = tmp_path / "ids.txt"
    fn.write_text("\n".join([header, *_IDS]) + "\n")
    df = read_delimited(str(fn))
    assert list(df.columns) == [header]
    assert list(df[header]) == _IDS


def test_read_delimited_one_column_without_header(tmp_path):
    fn = tmp_path / "ids.txt"
    fn.write_text("\n".join(_IDS) + "\n")
    df = read_delimited(str(fn), header=None)
    assert df.shape == (3, 1)
    assert list(df[0]) == _IDS


@pytest.mark.parametrize("sep", [",", "\t", ";"])
def test_read_delimited_still_splits_on_delimiters(tmp_path, sep):
    fn = tmp_path / "res.txt"
    fn.write_text(
        sep.join(["gene_id", "symbol", "stat"])
        + "\n"
        + "".join(sep.join([i, f"S{n}", str(n)]) + "\n" for n, i in enumerate(_IDS))
    )
    df = read_delimited(str(fn))
    assert list(df.columns) == ["gene_id", "symbol", "stat"]
    assert list(df["gene_id"]) == _IDS
    assert list(df["stat"]) == [0, 1, 2]


def test_read_delimited_quoted_fields_keep_their_delimiter(tmp_path):
    fn = tmp_path / "res.csv"
    fn.write_text('id,desc\nENSG01,"a, b"\n')
    df = read_delimited(str(fn))
    assert df.loc[0, "desc"] == "a, b"


def test_read_delimited_stream_and_gzip(tmp_path):
    text = "gene_id\n" + "\n".join(_IDS) + "\n"
    assert list(read_delimited(io.StringIO(text))["gene_id"]) == _IDS
    assert list(read_delimited(io.BytesIO(text.encode()))["gene_id"]) == _IDS
    fn = tmp_path / "ids.txt.gz"
    fn.write_bytes(gzip.compress(text.encode()))
    assert list(read_delimited(str(fn))["gene_id"]) == _IDS


def test_read_delimited_passes_options_on(tmp_path):
    fn = tmp_path / "ids.txt"
    fn.write_text("gene_id\n007\nNA\n")
    df = read_delimited(str(fn), dtype=str, keep_default_na=False)
    assert list(df["gene_id"]) == ["007", "NA"]


@pytest.mark.parametrize("header", ["id", "gene_id"])
def test_read_id_table_one_column(tmp_path, header):
    fn = tmp_path / "ids.txt"
    fn.write_text("\n".join([header, "007", *_IDS]) + "\n")
    df = read_id_table(str(fn))
    assert df.index.name == header
    assert list(df.index) == ["007", *_IDS]
    assert df.shape[1] == 0


@pytest.mark.parametrize("sep", [",", "\t", ";"])
def test_read_id_table_still_splits_on_delimiters(tmp_path, sep):
    fn = tmp_path / "counts.txt"
    fn.write_text(
        sep.join(["gene", "s1", "s2"])
        + "\n"
        + "".join(sep.join([i, str(n), str(n + 1)]) + "\n" for n, i in enumerate(_IDS))
    )
    df = read_id_table(str(fn))
    assert list(df.index) == _IDS
    assert list(df.columns) == ["s1", "s2"]
    assert df.loc["ENSG02"].tolist() == [1, 2]


# the CLI readers in util and enrich


@pytest.mark.parametrize("header", ["id", "gene_id"])
def test_annotate_cli_one_column_result(tmp_path, header):
    from de_toolkit.util import main

    res_fn = tmp_path / "ids.txt"
    map_fn = tmp_path / "map.tsv"
    out_fn = tmp_path / "out.csv"
    res_fn.write_text("\n".join([header, "ENSG01.1", "ENSG02.3", "ENSG09.1"]) + "\n")
    map_fn.write_text("gene_id\tsymbol\nENSG01\tA1BG\nENSG02\tA2M\n")
    main(
        [
            "detk-util",
            "annotate",
            "--no-report",
            "--strip-versions",
            "--map-to=symbol",
            "-o",
            str(out_fn),
            str(res_fn),
            str(map_fn),
        ]
    )
    out = pandas.read_csv(out_fn, dtype=str, keep_default_na=False)
    assert list(out.columns) == [header, "symbol"]
    assert list(out["symbol"]) == ["A1BG", "A2M", ""]


@pytest.mark.parametrize("sep", [",", "\t", ";"])
def test_annotate_cli_delimited_files(tmp_path, sep):
    from de_toolkit.util import main

    res_fn = tmp_path / "res.txt"
    map_fn = tmp_path / "map.txt"
    out_fn = tmp_path / "out.csv"
    res_fn.write_text(sep.join(["id", "stat"]) + "\n" + sep.join(["ENSG01", "1.5"]) + "\n")
    map_fn.write_text(sep.join(["gene_id", "symbol"]) + "\n" + sep.join(["ENSG01", "A1BG"]) + "\n")
    main(["detk-util", "annotate", "--no-report", "-o", str(out_fn), str(res_fn), str(map_fn)])
    out = pandas.read_csv(out_fn, dtype=str)
    assert list(out.columns) == ["id", "stat", "symbol"]
    assert out.iloc[0].tolist() == ["ENSG01", "1.5", "A1BG"]


def test_annotate_cli_one_column_mapping(tmp_path):
    # a one-column mapping has nothing to add; it must not be split into
    # columns named after letters of its header
    from de_toolkit.util import main

    res_fn = tmp_path / "res.csv"
    map_fn = tmp_path / "map.txt"
    res_fn.write_text("id,stat\nENSG01,1.5\n")
    map_fn.write_text("gene_id\nENSG01\n")
    with pytest.raises(SystemExit):
        main(["detk-util", "annotate", "--no-report", str(res_fn), str(map_fn)])


@pytest.mark.parametrize("header", ["id", "gene_id"])
def test_tidy_cli_one_column_covs(tmp_path, header):
    # a column-data file that only names the samples (names that hold the
    # letter the sniffer used to split "id" and "gene_id" on)
    from de_toolkit.util import main

    counts_fn = tmp_path / "counts.csv"
    covs_fn = tmp_path / "covs.txt"
    out_fn = tmp_path / "out.csv"
    counts_fn.write_text("gene,tie1,tie2,tie3\nENSG01,1,2,3\nENSG02,4,5,6\n")
    covs_fn.write_text(f"{header}\ntie3\ntie1\n")
    main(["detk-util", "tidy-counts", "-o", str(out_fn), str(counts_fn), str(covs_fn)])
    out = pandas.read_csv(out_fn, index_col=0)
    assert sorted(out.columns) == ["tie1", "tie3"]


def _gmt(tmp_path):
    fn = tmp_path / "sets.gmt"
    fn.write_text("set1\tdesc\tENSG01\tENSG02\n")
    return fn


@pytest.mark.parametrize(
    "text,shape",
    [
        ("gene_id\nENSG01\nENSG02\n", (2, 1)),
        ("id\nENSG01\nENSG02\n", (2, 1)),
        ("id,stat\nENSG01,1\nENSG02,2\n", (2, 2)),
        ("id\tstat\nENSG01\t1\nENSG02\t2\n", (2, 2)),
        ("id;stat\nENSG01;1\nENSG02;2\n", (2, 2)),
    ],
    ids=["gene_id", "id", "comma", "tab", "semicolon"],
)
def test_enrich_fgsea_cli_reads_result(tmp_path, caplog, text, shape):
    # the reading only: a statistic column that is not there stops the run
    # before fgsea (and R) is needed
    from de_toolkit.enrich import main

    res_fn = tmp_path / "res.txt"
    res_fn.write_text(text)
    with caplog.at_level(logging.INFO, logger="de_toolkit.enrich"):
        with pytest.raises(SystemExit):
            main(["detk-enrich", "fgsea", "--statcol=nope", str(_gmt(tmp_path)), str(res_fn)])
    assert f"result data frame shape: {shape}" in caplog.text
