import docopt
import pandas
import pytest
import sys
from tempfile import NamedTemporaryFile

from de_toolkit.util import main


def is_windows():
    return sys.platform in ("win32", "cygwin")


@pytest.mark.skipif(is_windows(), reason="not sure how to test which() on Windows")
def test_which():
    from de_toolkit.util import which

    assert which("sh").endswith("/bin/sh")


@pytest.fixture
def fake_tidy_counts_csv(request):
    counts_data = [["gene", "A", "B", "C"], ["nogene", 0, 0, 0]]
    with pytest.temp_csv_wrap(counts_data, ",") as f:
        yield f.name


@pytest.fixture
def fake_untidy_counts_csv(request):
    counts_data = [["gene", "A", "B", "C", "D"], ["nogene", 0, 0, 0, 0]]
    with pytest.temp_csv_wrap(counts_data, ",") as f:
        yield f.name


@pytest.fixture
def fake_tidy_column_data_csv(request):
    column_data = [["sample", "col"], ["A", 0], ["B", 0], ["C", 0]]
    with pytest.temp_csv_wrap(column_data, ",") as f:
        yield f.name


@pytest.fixture
def fake_untidy_column_data_csv(request):
    column_data = [["sample", "col"], ["A", 0], ["B", 0], ["C", 0], ["E", 0]]
    with pytest.temp_csv_wrap(column_data, ",") as f:
        yield f.name


def test_util_cli():
    with pytest.raises(docopt.DocoptExit):
        main()


def test_tidy_cli(fake_untidy_counts_csv, fake_untidy_column_data_csv):
    with NamedTemporaryFile() as counts_out:
        with NamedTemporaryFile() as col_out:
            main(
                [
                    "detk-util",
                    "tidy",
                    "-v",
                    "-o",
                    counts_out.name,
                    "-p",
                    col_out.name,
                    fake_untidy_counts_csv,
                    fake_untidy_column_data_csv,
                ]
            )
            with open(counts_out.name) as f:
                print(f.read())
            counts = pandas.read_csv(counts_out.name, index_col=0)
            print(counts)
            col = pandas.read_csv(col_out.name, index_col=0)
            print(col)
            assert all(counts.columns == col.index)


def test_tidy_counts_cli(
    fake_untidy_counts_csv, fake_tidy_column_data_csv, fake_untidy_column_data_csv
):

    # untidy counts are tidied by tidy column data
    with NamedTemporaryFile() as counts_out:
        main(
            [
                "detk-util",
                "tidy-counts",
                fake_untidy_counts_csv,
                fake_tidy_column_data_csv,
                "-o",
                counts_out.name,
            ]
        )
        counts = pandas.read_csv(counts_out.name, index_col=0)
        col = pandas.read_csv(fake_tidy_column_data_csv, index_col=0)
        assert all(counts.columns == col.index)

    # untidy counts are not tidied by untidy column data
    # the untidy column data has an extra row ID not found in the counts
    with pytest.raises(SystemExit):
        main(
            [
                "detk-util",
                "tidy-counts",
                fake_untidy_counts_csv,
                fake_untidy_column_data_csv,
            ]
        )


def test_tidy_covs_cli(fake_tidy_counts_csv, fake_untidy_counts_csv, fake_untidy_column_data_csv):

    # untidy column data are tidied by tidy counts
    with NamedTemporaryFile() as covs_out:
        main(
            [
                "detk-util",
                "tidy-covs",
                fake_tidy_counts_csv,
                fake_untidy_column_data_csv,
                "-o",
                covs_out.name,
            ]
        )
        counts = pandas.read_csv(fake_tidy_counts_csv, index_col=0)
        col = pandas.read_csv(covs_out.name, index_col=0)
        assert all(counts.columns == col.index)

    # untidy column data are not tidied by untidy counts data
    # the untidy column data has an extra row ID not found in the counts
    with pytest.raises(SystemExit):
        main(
            [
                "detk-util",
                "tidy-covs",
                fake_untidy_counts_csv,
                fake_untidy_column_data_csv,
            ]
        )


# zero-padded feature IDs and sample names (DETK-0015, #67)
@pytest.fixture
def padded_csvs(tmp_path):
    counts_fn = tmp_path / "counts.csv"
    counts_fn.write_text("gene,001,002,003,004\n007,1,2,3,4\n010,5,6,7,8\n1.10,0,1,0,1\n")
    covs_fn = tmp_path / "covs.csv"
    covs_fn.write_text("sample,group\n003,b\n001,a\n002,a\n")
    return str(counts_fn), str(covs_fn)


def _as_written(fn):
    return pandas.read_csv(fn, dtype=str, keep_default_na=False)


def test_tidy_counts_keeps_padded_ids(padded_csvs, tmp_path):
    counts_fn, covs_fn = padded_csvs
    out_fn = str(tmp_path / "out.csv")
    main(["detk-util", "tidy-counts", counts_fn, covs_fn, "-o", out_fn])
    out = _as_written(out_fn)
    assert out.iloc[:, 0].tolist() == ["007", "010", "1.10"]
    assert out.columns[1:].tolist() == ["001", "002", "003"]


def test_tidy_covs_keeps_padded_ids(padded_csvs, tmp_path):
    counts_fn, covs_fn = padded_csvs
    # the counts lose sample 004, so every counts column is a covariates row
    tidy_counts_fn = tmp_path / "tidy_counts.csv"
    tidy_counts_fn.write_text("gene,002,001,003\n007,1,2,3\n")
    out_fn = str(tmp_path / "out.csv")
    main(["detk-util", "tidy-covs", str(tidy_counts_fn), covs_fn, "-o", out_fn])
    out = _as_written(out_fn)
    assert out.iloc[:, 0].tolist() == ["002", "001", "003"]
    assert out["group"].tolist() == ["a", "a", "b"]

    # sample 004 of the counts is not in the covariates
    with pytest.raises(SystemExit):
        main(["detk-util", "tidy-covs", counts_fn, covs_fn, "-o", out_fn])
