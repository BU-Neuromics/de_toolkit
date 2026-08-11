import docopt
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
