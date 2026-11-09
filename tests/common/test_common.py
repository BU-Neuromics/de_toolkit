import os
import docopt
import pandas
import pytest
from de_toolkit.common import main, InvalidDesignException, DetkModule


def test_cli():
    with pytest.raises(docopt.DocoptExit):
        main()


def test_cli_version(monkeypatch):
    from io import StringIO

    import sys

    stdout = StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)

    main(["detk", "--version"])

    from de_toolkit.common import __version__

    assert stdout.getvalue().strip() == __version__


def test_CountMatrix(fake_counts_pandas_dataframe, fake_column_data_pandas_dataframe):

    from de_toolkit import CountMatrix
    from de_toolkit.common import SampleMismatchException

    # with no column data
    mat = CountMatrix(fake_counts_pandas_dataframe)

    # with column data
    mat = CountMatrix(fake_counts_pandas_dataframe, column_data=fake_column_data_pandas_dataframe)
    assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
    assert all(mat.feature_names == fake_counts_pandas_dataframe.index)

    # with column data and design
    mat = CountMatrix(
        fake_counts_pandas_dataframe,
        column_data=fake_column_data_pandas_dataframe,
        design="cont_cov ~ category[case] + counts",
    )
    print(mat.column_data.columns)
    assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
    assert all(mat.feature_names == fake_counts_pandas_dataframe.index)
    assert mat.design == "cont_cov ~ Intercept + category__cont + counts"

    # missing a counts column
    with pytest.raises(InvalidDesignException):
        mat = CountMatrix(
            fake_counts_pandas_dataframe,
            column_data=fake_column_data_pandas_dataframe,
            design="cont_cov ~ category[case]",
        )

    # set invalid design
    with pytest.raises(InvalidDesignException):
        mat = CountMatrix(
            fake_counts_pandas_dataframe,
            column_data=fake_column_data_pandas_dataframe,
            design="cont_cov ~ category[case] + counts",
        )
        mat.design = "oogabooga"

    # with strict
    mat = CountMatrix(
        fake_counts_pandas_dataframe, column_data=fake_column_data_pandas_dataframe, strict=True
    )
    assert all(mat.sample_names == fake_column_data_pandas_dataframe.index)
    assert all(mat.feature_names == fake_counts_pandas_dataframe.index)

    # with violations of strict
    # change the order of count columns wrt column data
    fake_counts_pandas_dataframe.columns = fake_counts_pandas_dataframe.columns[::-1]
    with pytest.raises(SampleMismatchException):
        mat = CountMatrix(
            fake_counts_pandas_dataframe, column_data=fake_column_data_pandas_dataframe, strict=True
        )

    # add an additional column
    fake_counts_pandas_dataframe["d"] = 0
    with pytest.raises(SampleMismatchException):
        mat = CountMatrix(
            fake_counts_pandas_dataframe, column_data=fake_column_data_pandas_dataframe, strict=True
        )

    # with different sample names and not strict
    mat = CountMatrix(
        fake_counts_pandas_dataframe, column_data=fake_column_data_pandas_dataframe, strict=False
    )
    assert sorted(mat.sample_names) == sorted(fake_column_data_pandas_dataframe.index)

    # bad cov
    with pytest.raises(InvalidDesignException):
        mat.design = "category ~ cont_covx + counts"

    # test warning when the design matrix samples get truncated due
    # to missing data
    fake_coldata_with_na = fake_column_data_pandas_dataframe.copy()
    fake_coldata_with_na.loc["a", "cont_cov"] = None
    with pytest.warns(UserWarning):
        mat = CountMatrix(
            fake_counts_pandas_dataframe,
            fake_coldata_with_na,
            design="category ~ cont_cov + counts",
        )
        assert (mat.counts.columns == mat.column_data.index).all()
        assert (mat.counts.columns == mat.design_matrix.full_matrix.index).all()
        assert (mat.column_data.index == mat.design_matrix.full_matrix.index).all()


def test_CountMatrixFile(fake_counts_csv, fake_column_data_csv):
    from de_toolkit import CountMatrixFile

    CountMatrixFile(fake_counts_csv, column_data_f=fake_column_data_csv)


################################################################################
# DetkModule base class
def test_DetkModule():
    stat = DetkModule()
    assert stat.json == {"name": "detkmodule", "params": {}, "properties": {}}
    assert stat.name == "detkmodule"
    assert stat.params == {}
    assert stat.output == []
    assert stat.properties == {}


################################################################################
# feature and sample IDs are read as text (#48)

# every ID looks like a number, so pandas would type the column as integers:
# zero-padded IDs and Entrez gene IDs (5290, 42)
_PADDED_IDS = ["007", "010", "5290", "42", "0099"]
_PADDED_COUNTS = [
    [10, 20, 30, 40],
    [5, 0, 7, 9],
    [100, 120, 90, 80],
    [50, 60, 70, 55],
    [3, 4, 5, 6],
]


def _padded_counts_text(header="gene", sep=","):
    lines = [
        sep.join([header, "s1", "s2", "s3", "s4"])
        if header is not None
        else sep.join(["s1", "s2", "s3", "s4"])
    ]
    for fid, row in zip(_PADDED_IDS, _PADDED_COUNTS):
        lines.append(sep.join([fid] + [str(v) for v in row]))
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize(
    "header,sep",
    [("gene", ","), ("", ","), ('""', ","), ("gene", "\t"), ("", "\t"), (None, "\t")],
    ids=["named", "empty", "quoted-empty", "named-tsv", "empty-tsv", "no-index-field-tsv"],
)
def test_read_id_table_keeps_ids_as_written(tmp_path, header, sep):
    from de_toolkit.common import read_id_table

    fn = tmp_path / "counts.txt"
    fn.write_text(_padded_counts_text(header, sep))
    df = read_id_table(str(fn))
    # leading zeros kept, numeric Entrez IDs and versioned IDs untouched
    assert list(df.index) == _PADDED_IDS
    assert list(df.columns) == ["s1", "s2", "s3", "s4"]
    # the counts stay numeric
    assert all(pandas.api.types.is_integer_dtype(t) for t in df.dtypes)
    assert df.loc["007"].tolist() == [10, 20, 30, 40]
    assert df.index.name == ("gene" if header == "gene" else None)


@pytest.mark.parametrize(
    "ids",
    [
        ["ENSG00000000003.14", "ENSG00000000005.6", "ENSG00000000419.12"],
        ["1.10", "1.1", "2.0"],
        ["007", "ENSG00000000003.14", "5290"],
    ],
    ids=["ensembl-versioned", "numeric-versioned", "mixed"],
)
def test_read_id_table_versioned_ids_untouched(tmp_path, ids):
    from de_toolkit.common import read_id_table

    fn = tmp_path / "counts.csv"
    fn.write_text("gene,a,b\n" + "".join(f"{i},1,2\n" for i in ids))
    assert list(read_id_table(str(fn)).index) == ids


def test_read_id_table_stream_and_gzip(tmp_path):
    import gzip
    import io

    from de_toolkit.common import read_id_table

    text = _padded_counts_text()
    assert list(read_id_table(io.StringIO(text)).index) == _PADDED_IDS
    assert list(read_id_table(io.BytesIO(text.encode())).index) == _PADDED_IDS
    fn = tmp_path / "counts.csv.gz"
    with gzip.open(fn, "wt") as f:
        f.write(text)
    df = read_id_table(str(fn))
    assert list(df.index) == _PADDED_IDS
    assert df.loc["0099"].tolist() == [3, 4, 5, 6]


def _fifo_writer(path, data):
    """Write *data* to the FIFO at *path* from a thread; returns the thread."""
    import threading

    def write():
        with open(path, "wb") as f:
            f.write(data)

    t = threading.Thread(target=write, daemon=True)
    t.start()
    return t


def test_read_id_table_tilde_path_goes_to_pandas(tmp_path, monkeypatch):
    # a path the shell did not expand (~/...) is not a local file, but pandas
    # expands it, as on main; it must not be opened directly
    from de_toolkit.common import read_id_table

    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "counts.csv").write_text(",a,b\n007,1,2\n008,3,4\n")
    df = read_id_table("~/counts.csv")
    assert list(df.index) == ["007", "008"]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="needs os.mkfifo")
@pytest.mark.parametrize("name", ["counts.csv", "counts.csv.gz"])
def test_read_id_table_fifo(tmp_path, name):
    # a FIFO can be read only once, but the table is parsed twice
    import gzip

    from de_toolkit.common import read_id_table

    data = _padded_counts_text().encode()
    if name.endswith(".gz"):
        data = gzip.compress(data)
    fifo = tmp_path / name
    os.mkfifo(fifo)
    _fifo_writer(fifo, data)
    # read in a thread: a reader that opens the FIFO twice blocks forever
    import threading

    result = {}
    reader = threading.Thread(
        target=lambda: result.update(df=read_id_table(str(fifo))), daemon=True
    )
    reader.start()
    reader.join(timeout=30)
    assert "df" in result, "read_id_table did not read the FIFO"
    df = result["df"]
    assert list(df.index) == _PADDED_IDS
    assert df.loc["0099"].tolist() == [3, 4, 5, 6]


@pytest.mark.skipif(not os.path.exists("/dev/stdin"), reason="needs /dev/stdin")
def test_cli_reads_counts_from_dev_stdin(tmp_path):
    # cat counts.csv | detk-norm deseq2 /dev/stdin
    import subprocess
    import sys

    out_fn = tmp_path / "out.csv"
    code = "import sys; from de_toolkit.norm import main; main(sys.argv)"
    argv = ["deseq2", f"--output={out_fn}", "--no-report", "/dev/stdin"]
    proc = subprocess.run(
        [sys.executable, "-c", code, *argv],
        input=_padded_counts_text(),
        text=True,
        capture_output=True,
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    ids = [line.split(",")[0] for line in out_fn.read_text().splitlines()[1:]]
    assert ids == _PADDED_IDS


def test_read_id_table_falls_back_when_parses_disagree(caplog):
    # A degenerate table (found by fuzzing) whose last row has two more
    # fields than the header: pandas makes the index a MultiIndex of one
    # row, while the text parse sees two lines below the header. The rows
    # cannot be paired, so the table is returned as pandas typed it, with
    # a warning.
    import io
    import logging

    from de_toolkit.common import read_id_table

    text = ",,\n,\n,,,,"
    expected = pandas.read_csv(io.StringIO(text), sep=None, engine="python", index_col=0)
    with caplog.at_level(logging.WARNING, logger="de_toolkit.common"):
        df = read_id_table(io.StringIO(text))
    pandas.testing.assert_frame_equal(df, expected)
    assert "could not read the IDs" in caplog.text


def test_read_id_table_missing_ids_and_other_columns(tmp_path):
    from de_toolkit.common import read_id_table

    fn = tmp_path / "info.csv"
    fn.write_text("sample,cond,age,flag\n01,A,30,True\n02,B,4.5,False\nNA,B,,True\n")
    df = read_id_table(str(fn))
    assert df.index[:2].tolist() == ["01", "02"]
    # a missing-value token is a missing ID, as pandas reads it
    assert pandas.isna(df.index[2])
    # the other columns are typed as pandas infers them
    assert df["cond"].tolist() == ["A", "B", "B"]
    assert pandas.api.types.is_float_dtype(df["age"])
    assert df["flag"].dtype == bool


def test_CountMatrixFile_padded_ids(tmp_path):
    from de_toolkit import CountMatrixFile

    counts_fn = tmp_path / "counts.csv"
    counts_fn.write_text("gene,001,002,003,004\n007,10,20,30,40\n42,1,2,3,4\n5290,5,6,7,8\n")
    # zero-padded sample names match the counts header
    info_fn = tmp_path / "info.csv"
    info_fn.write_text("sample,cond\n001,A\n002,A\n003,B\n004,B\n")
    mat = CountMatrixFile(str(counts_fn), str(info_fn), design="counts ~ cond")
    assert list(mat.feature_names) == ["007", "42", "5290"]
    assert list(mat.sample_names) == ["001", "002", "003", "004"]
    assert list(mat.column_data.index) == ["001", "002", "003", "004"]
    assert mat.counts.loc["007"].tolist() == [10, 20, 30, 40]


@pytest.mark.parametrize("cmd", ["tpm", "fpkm"])
def test_padded_ids_match_lengths_file(tmp_path, cmd):
    import numpy as np

    from de_toolkit import CountMatrixFile
    from de_toolkit.norm import fpkm, read_lengths, tpm

    counts_fn = tmp_path / "counts.csv"
    counts_fn.write_text(_padded_counts_text())
    lengths_fn = tmp_path / "lengths.tsv"
    # a different order; 7 and 99 are other features than 007 and 0099
    lengths_fn.write_text("0099\t500\n007\t1000\n7\t1\n99\t1\n42\t3000\n010\t2000\n5290\t1500\n")
    counts = CountMatrixFile(str(counts_fn)).counts
    lengths = read_lengths(str(lengths_fn))
    res = (tpm if cmd == "tpm" else fpkm)(counts, lengths)
    assert list(res.index) == _PADDED_IDS
    lens = np.array([1000, 2000, 1500, 3000, 500])
    if cmd == "fpkm":
        expected = counts.values * 1e9 / (lens[:, None] * counts.values.sum(axis=0))
    else:
        rate = counts.values / lens[:, None]
        expected = rate / rate.sum(axis=0) * 1e6
    assert np.allclose(res.values, expected)


def _run_cli(module, argv):
    import importlib

    importlib.import_module(f"de_toolkit.{module}").main(argv)


@pytest.mark.parametrize(
    "module,args",
    [
        ("norm", ["deseq2"]),
        ("norm", ["library"]),
        ("norm", ["cpm"]),
        ("norm", ["tpm", "LENGTHS"]),
        ("norm", ["fpkm", "LENGTHS"]),
        ("filter", ["mean(all) > 1"]),
        ("filter", ["mean(cond) > 1", "INFO"]),
        ("transform", ["plog"]),
        ("stats", ["rowdist"]),
        ("outlier", ["entropy", "-p", "0.5"]),
        ("util", ["tidy", "INFO"]),
    ],
    ids=[
        "norm-deseq2",
        "norm-library",
        "norm-cpm",
        "norm-tpm",
        "norm-fpkm",
        "filter",
        "filter-groupwise",
        "transform-plog",
        "stats-rowdist",
        "outlier-entropy",
        "util-tidy",
    ],
)
def test_cli_output_keeps_padded_ids(tmp_path, module, args):
    counts_fn = tmp_path / "counts.csv"
    counts_fn.write_text(_padded_counts_text())
    lengths_fn = tmp_path / "lengths.csv"
    lengths_fn.write_text(
        "gene,length\n" + "".join(f"{i},{n}\n" for i, n in zip(_PADDED_IDS, [1, 2, 3, 4, 5]))
    )
    info_fn = tmp_path / "info.csv"
    info_fn.write_text("sample,cond\ns1,A\ns2,A\ns3,B\ns4,B\n")
    out_fn = tmp_path / "out.csv"

    files = {"LENGTHS": str(lengths_fn), "INFO": str(info_fn)}
    cmd, rest = args[0], args[1:]
    positional = [a for a in rest if a in files]
    options = [a for a in rest if a not in files]
    argv = [f"detk-{module}", cmd, *options, f"--output={out_fn}", "--no-report", str(counts_fn)]
    argv += [files[a] for a in positional]
    _run_cli(module, argv)

    ids = [line.split(",")[0] for line in out_fn.read_text().splitlines()[1:]]
    assert ids == _PADDED_IDS


def test_gather_then_norm_keeps_padded_ids(tmp_path):
    # detk-util gather reads its inputs as text; its matrix, read back by
    # the shared reader, keeps 007 and the zero-padded sample names
    for sample, counts in [("001", [10, 3, 5]), ("002", [12, 4, 6])]:
        (tmp_path / sample).mkdir()
        lines = [f"{i}\t{n}" for i, n in zip(["007", "42", "0099"], counts)]
        (tmp_path / sample / "s.counts.txt").write_text("\n".join(lines + ["__no_feature\t1"]))
    matrix_fn = tmp_path / "counts.csv"
    _run_cli(
        "util",
        ["detk-util", "gather", "--name-from=/([0-9]+)/", f"--output={matrix_fn}", "--no-report"]
        + [str(tmp_path / s / "s.counts.txt") for s in ("001", "002")],
    )
    out_fn = tmp_path / "out.csv"
    _run_cli("norm", ["detk-norm", "cpm", f"--output={out_fn}", "--no-report", str(matrix_fn)])
    lines = out_fn.read_text().splitlines()
    assert lines[0].split(",")[1:] == ["001", "002"]
    assert [line.split(",")[0] for line in lines[1:]] == ["007", "42", "0099"]
