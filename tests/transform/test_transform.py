import docopt
import numpy
import pandas
import pytest
import warnings

from de_toolkit.transform import main
from de_toolkit.wrapr import check_r, check_r_package

r_test = pytest.mark.skipif(not check_r(), reason="r is not installed, skipping test")
deseq2_test = pytest.mark.skipif(
    not check_r_package("DESeq2"), reason="DESeq2 package not installed, skipping test"
)


def test_transform_cli(fake_counts_csv):
    with pytest.raises(docopt.DocoptExit):
        main()


@r_test
@deseq2_test
def test_transform_vst(fake_counts_obj):
    from de_toolkit.transform import vst

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vst(fake_counts_obj)


@r_test
@deseq2_test
def test_transform_vst_cli(fake_counts_csv):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(["detk-transform", "vst", fake_counts_csv])


@r_test
@deseq2_test
def test_transform_rlog(fake_counts_obj):
    from de_toolkit.transform import rlog

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rlog(fake_counts_obj)


@r_test
@deseq2_test
def test_transform_rlog_cli(fake_counts_csv, fake_column_data_csv):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(["detk-transform", "rlog", fake_counts_csv])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(
            [
                "detk-transform",
                "rlog",
                fake_counts_csv,
                "counts ~ category[cont]",
                fake_column_data_csv,
            ]
        )


def test_transform_plog(fake_counts_obj):
    from de_toolkit.transform import plog

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plog(fake_counts_obj)


def test_transform_plog_cli(fake_counts_csv):

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(["detk-transform", "plog", fake_counts_csv])


def test_plog_cli_accepts_output_option(tmp_path, fake_counts_csv):
    # regression: main used to parse the module-level usage first, whose
    # [options] did not include -o, so every subcommand option was rejected
    from de_toolkit.transform import main

    out = tmp_path / "plog.csv"
    main(["detk-transform", "plog", "-o", str(out), "--no-report", fake_counts_csv])
    assert out.exists()


# Zero-padded and versioned all-numeric IDs, and zero-padded sample names
# (DETK-0015, #67): R's read.csv would read 007 as 7 and both 1.10 and 1.1 as
# 1.1; each must come back from R as written.
PADDED_IDS = ["007", "010", "1.10", "1.1"] + [f"{_:03d}" for _ in range(20, 28)]
PADDED_SAMPLES = [f"{_:03d}" for _ in range(1, 7)]


@pytest.fixture
def padded_ids_csvs(tmp_path):
    rng = numpy.random.default_rng(67)
    means = rng.integers(20, 500, size=len(PADDED_IDS))
    counts = pandas.DataFrame(
        rng.poisson(means[:, None] * [1, 1, 1, 2, 2, 2]),
        index=pandas.Index(PADDED_IDS, name="gene"),
        columns=PADDED_SAMPLES,
    )
    covs = pandas.DataFrame(
        {"category": ["cont"] * 3 + ["case"] * 3},
        index=pandas.Index(PADDED_SAMPLES, name="sample"),
    )
    counts_fn, covs_fn = tmp_path / "counts.csv", tmp_path / "covs.csv"
    counts.to_csv(counts_fn)
    covs.to_csv(covs_fn)
    return str(counts_fn), str(covs_fn)


def _assert_as_written(fn):
    "The CSV *fn* has the padded IDs and sample names, as written."
    out = pandas.read_csv(fn, dtype=str, keep_default_na=False)
    assert out.iloc[:, 0].tolist() == PADDED_IDS
    assert out.columns[1:].tolist() == PADDED_SAMPLES


@r_test
@deseq2_test
def test_vst_keeps_padded_ids(padded_ids_csvs, tmp_path):
    counts_fn, _ = padded_ids_csvs
    out_fn = str(tmp_path / "out.csv")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(["detk-transform", "vst", "--no-report", counts_fn, "-o", out_fn])
    _assert_as_written(out_fn)


@r_test
@deseq2_test
def test_rlog_keeps_padded_ids(padded_ids_csvs, tmp_path):
    counts_fn, _ = padded_ids_csvs
    out_fn = str(tmp_path / "out.csv")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(["detk-transform", "rlog", "--no-report", counts_fn, "-o", out_fn])
    _assert_as_written(out_fn)


@r_test
@deseq2_test
def test_rlog_not_blind_keeps_padded_ids(padded_ids_csvs):
    # the sample information goes to R too: its row names (001, ...) must
    # stay text to line up with the counts columns
    from de_toolkit.common import CountMatrixFile
    from de_toolkit.transform import rlog

    counts_fn, covs_fn = padded_ids_csvs
    count_obj = CountMatrixFile(counts_fn, covs_fn, design="counts ~ category[cont]")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = rlog(count_obj, blind=False)
    assert out.index.tolist() == PADDED_IDS
    assert out.columns.tolist() == PADDED_SAMPLES
