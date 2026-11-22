"""Tests for the sniffed reading of delimited tables (#47): a one-column file
is read as one column, not split on a letter of its header."""

import gzip
import http.server
import io
import logging
import threading

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
        # pipe wins over the spaces in a header (BioMart's export)
        ("g|sample 1|sample 2", "|"),
        ("Gene stable ID|Gene name", "|"),
        # R's write.table default: quoted, space-separated
        ('"s1" "s2"', " "),
        # a comma inside quotes does not beat space
        ('"gene, id" s1 s2', " "),
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


def test_read_delimited_pipe_with_spaces_in_headers(tmp_path):
    fn = tmp_path / "mart.txt"
    fn.write_text("Gene stable ID|Gene name\nENSG01|A B\nENSG02|C\n")
    df = read_delimited(str(fn))
    assert list(df.columns) == ["Gene stable ID", "Gene name"]
    assert list(df["Gene name"]) == ["A B", "C"]


def test_read_id_table_pipe_with_spaces_in_headers(tmp_path):
    fn = tmp_path / "counts.txt"
    fn.write_text(
        "g|sample 1|sample 2\n" + "".join(f"{i}|{n}|{n + 1}\n" for n, i in enumerate(_IDS))
    )
    df = read_id_table(str(fn))
    assert list(df.index) == _IDS
    assert list(df.columns) == ["sample 1", "sample 2"]
    assert df.loc["ENSG02"].tolist() == [1, 2]


def test_read_id_table_r_write_table(tmp_path):
    # R's write.table(counts) default: quoted, space-separated, and the
    # header omits the row names' field
    fn = tmp_path / "counts.txt"
    fn.write_text('"s1" "s2"\n' + "".join(f'"{i}" {n} {n + 1}\n' for n, i in enumerate(_IDS)))
    df = read_id_table(str(fn))
    assert list(df.index) == _IDS
    assert list(df.columns) == ["s1", "s2"]
    assert df.loc["ENSG02"].tolist() == [1, 2]
    assert list(read_delimited(str(fn)).columns) == ["s1", "s2"]


@pytest.fixture
def http_table():
    """
    Serve a counts table over HTTP from a local server in a thread; yield
    its URL and the list of request paths the server received.
    """
    body = ("gene,s1,s2\n" + "".join(f"{i},{n},{n + 1}\n" for n, i in enumerate(_IDS))).encode()
    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/counts.csv", requests
    finally:
        server.shutdown()
        server.server_close()


def test_read_delimited_fetches_a_url_once(http_table):
    url, requests = http_table
    df = read_delimited(url)
    assert list(df.columns) == ["gene", "s1", "s2"]
    assert requests == ["/counts.csv"]


def test_read_id_table_fetches_a_url_once(http_table):
    url, requests = http_table
    df = read_id_table(url)
    assert list(df.index) == _IDS
    assert df.loc["ENSG02"].tolist() == [1, 2]
    assert requests == ["/counts.csv"]


def test_read_delimited_gzipped_url(tmp_path):
    # a file:// URL is fetched by pandas' opener too, and its compression is
    # taken from its name
    fn = tmp_path / "ids.txt.gz"
    fn.write_bytes(gzip.compress(("gene_id\n" + "\n".join(_IDS) + "\n").encode()))
    assert list(read_delimited(fn.as_uri())["gene_id"]) == _IDS
    assert list(read_id_table(fn.as_uri()).index) == _IDS


@pytest.mark.parametrize("name", ["counts.csv.gz", "counts.csv"])
def test_url_with_content_encoding_gzip(name):
    # a server (S3 with ContentEncoding=gzip, say) may send gzip bytes with
    # Content-Encoding: gzip; pandas undoes the encoding, so a .gz name must
    # not be decompressed a second time
    body = gzip.compress(("gene,s1,s2\n" + "".join(f"{i},1,2\n" for i in _IDS)).encode())

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{name}"
        main = pandas.read_csv(url, index_col=0, dtype={0: str})
        assert list(read_delimited(url)["gene"]) == _IDS
        assert list(read_id_table(url).index) == _IDS
        assert read_id_table(url).shape == main.shape
    finally:
        server.shutdown()
        server.server_close()


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


# ------------------------------------- a one-field header over wider rows
#
# R's write.table(sep=...) leaves out the header cell over the row names, so
# a sheet with one column has a header with no delimiter and rows with one
# (release/short-header). The delimiter is sniffed from the first data line;
# the table is one column only when that line has none either.

_SHORT_HEADER = {
    "quoted": '"condition"\n"S1","a"\n"S2","b"\n',
    "unquoted": 'condition\n"S1","a"\n"S2","b"\n',
    "tab": "condition\nS1\ta\nS2\tb\n",
    "quoted tab": '"condition"\n"S1"\t"a"\n"S2"\t"b"\n',
    # R's default write.table: quoted, space-separated (DETK-0320)
    "quoted space": '"condition"\n"S1" "a"\n"S2" "b"\n',
}


@pytest.mark.parametrize("text", _SHORT_HEADER.values(), ids=_SHORT_HEADER.keys())
def test_read_delimited_one_field_header_over_wider_rows(tmp_path, text):
    fn = tmp_path / "samples.csv"
    fn.write_text(text)
    df = read_delimited(str(fn))
    assert list(df.index) == ["S1", "S2"]
    assert list(df.columns) == ["condition"]
    assert list(df["condition"]) == ["a", "b"]


@pytest.mark.parametrize("text", _SHORT_HEADER.values(), ids=_SHORT_HEADER.keys())
def test_read_id_table_one_field_header_over_wider_rows(tmp_path, text):
    fn = tmp_path / "samples.csv"
    fn.write_text(text)
    df = read_id_table(str(fn))
    assert list(df.index) == ["S1", "S2"]
    assert list(df.columns) == ["condition"]
    assert list(df["condition"]) == ["a", "b"]


@pytest.mark.parametrize(
    "text",
    ['"condition"\n"001","a"\n"002","b"\n', "condition\n001\ta\n002\tb\n"],
    ids=["quoted", "tab"],
)
def test_one_field_header_keeps_padded_ids_as_written(tmp_path, text):
    fn = tmp_path / "samples.csv"
    fn.write_text(text)
    # read_id_table reads the IDs as text (pandas types the index it infers
    # from a short header, whatever dtype it is given)
    df = read_id_table(str(fn))
    assert list(df.index) == ["001", "002"]
    assert list(df["condition"]) == ["a", "b"]


def test_one_field_header_after_skiprows(tmp_path):
    fn = tmp_path / "samples.csv"
    fn.write_text('# written by R\n"condition"\n"S1","a"\n"S2","b"\n')
    df = read_delimited(str(fn), skiprows=1)
    assert list(df.index) == ["S1", "S2"]
    assert list(df.columns) == ["condition"]


@pytest.mark.parametrize(
    "text, header, ids",
    [
        ('"gene_id"\n"ENSG1"\n"ENSG2"\n', "gene_id", ["ENSG1", "ENSG2"]),
        ("gene_id\nENSG1\nENSG2\n", "gene_id", ["ENSG1", "ENSG2"]),
        # a space inside quotes does not split an ID
        ('"sample"\n"sample 1"\n"sample 2"\n', "sample", ["sample 1", "sample 2"]),
        ('"gene_id"\n', "gene_id", []),
        ("gene_id\n", "gene_id", []),
        ("gene_id", "gene_id", []),
    ],
    ids=["quoted", "unquoted", "quoted space", "header only quoted", "header only", "no newline"],
)
def test_a_real_one_column_table_stays_one_column(tmp_path, text, header, ids):
    fn = tmp_path / "ids.txt"
    fn.write_text(text)
    df = read_delimited(str(fn))
    assert list(df.columns) == [header]
    assert list(df[header]) == ids


# DETK-0320: space from a data line counts only when the line's first field
# is quoted, and the first data lines must split alike into 2 or more fields

_SPACED_LISTS = {
    # one ID with a space, as Excel exports it (unquoted)
    "first spaced": ("sample\nctrl 1\nS2\nS3\n", ["ctrl 1", "S2", "S3"]),
    "every spaced": ("sample\nsample 1\nsample 2\n", ["sample 1", "sample 2"]),
    "later spaced": ("sample\nS2\nctrl 1\nS3\n", ["S2", "ctrl 1", "S3"]),
}


@pytest.mark.parametrize("text, ids", _SPACED_LISTS.values(), ids=_SPACED_LISTS.keys())
def test_an_unquoted_id_list_with_spaces_stays_one_column(tmp_path, text, ids):
    fn = tmp_path / "ids.txt"
    fn.write_text(text)
    df = read_delimited(str(fn))
    assert list(df.columns) == ["sample"]
    assert list(df["sample"]) == ids
    # read_id_table indexes by the one column
    assert list(read_id_table(str(fn)).index) == ids


def test_an_unquoted_space_separated_short_header_is_one_column(tmp_path):
    # R's write.table(quote=FALSE, sep=" ") cannot be told from a list of
    # IDs with spaces; it is read as one, as before #136 (DETK-0320)
    fn = tmp_path / "samples.txt"
    fn.write_text("condition\nS1 a\nS2 b\n")
    df = read_delimited(str(fn))
    assert list(df.columns) == ["condition"]
    assert list(df["condition"]) == ["S1 a", "S2 b"]


@pytest.mark.parametrize(
    "text, values",
    [
        ("condition\nS1,a\nS2\nS3\n", ["S1,a", "S2", "S3"]),
        ("condition\nS1,a\nS2,b,c\n", ["S1,a", "S2,b,c"]),
    ],
    ids=["then one field", "then three fields"],
)
def test_data_lines_that_split_unalike_mean_one_column(tmp_path, text, values):
    fn = tmp_path / "samples.txt"
    fn.write_text(text)
    df = read_delimited(str(fn))
    assert list(df.columns) == ["condition"]
    assert list(df["condition"]) == values


def test_data_lines_past_the_sniffed_ones_do_not_count(tmp_path):
    # only the first lines are sniffed; a short header sheet of many rows
    # still reads by its rows' delimiter
    fn = tmp_path / "samples.csv"
    fn.write_text('"condition"\n' + "".join(f'"S{i}","a"\n' for i in range(50)))
    df = read_id_table(str(fn))
    assert list(df.columns) == ["condition"]
    assert len(df) == 50


def test_filter_cli_reads_a_one_field_short_header_sheet(tmp_path, monkeypatch):
    # a command that reads column data through read_id_table: detk-filter
    # groups by the sheet's one column (release/short-header)
    from de_toolkit.filter import main

    monkeypatch.chdir(tmp_path)
    (tmp_path / "counts.csv").write_text("gene,S1,S2,S3,S4\ng1,10,20,30,40\ng2,5,0,15,25\n")
    (tmp_path / "cov.csv").write_text('"condition"\n"S1","A"\n"S2","A"\n"S3","B"\n"S4","B"\n')
    main(
        ["detk-filter", "--no-report", "-o", "out.csv", "mean(condition[A]) > 12"]
        + ["counts.csv", "cov.csv"]
    )
    kept = [line.split(",")[0] for line in (tmp_path / "out.csv").read_text().splitlines()[1:]]
    # g1's mean in A is 15, g2's 2.5
    assert kept == ["g1"]
