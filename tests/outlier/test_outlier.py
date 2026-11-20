import pandas
import pytest
import warnings


def test_shrink(fake_counts_obj):
    from de_toolkit.outlier import shrink

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        shrink(fake_counts_obj)
    # TODO need *actual* tests


def test_shrink_cli(fake_counts_csv):
    from de_toolkit.outlier import main

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main(["detk-outlier", "shrink", fake_counts_csv])
    # TODO need *actual* tests


@pytest.fixture
def entropy_test_counts_obj(request):
    from de_toolkit.common import CountMatrix

    ## Generate fake count data ##
    # initialize a vector of zeros with length 20
    base = list([0] * 20)

    # initialize the test df
    test_df = pandas.DataFrame()

    # loop through and incrememnt the base vector
    for num in range(0, 20):
        base[num] = 1
        test_df[num] = base

    colnames = []
    for num in range(0, 20):
        colnames.append("sample_" + str(num))
    rownames = []
    for num in range(0, 20):
        rownames.append("feature_" + str(num))

    test_df.columns = colnames
    test_df.index = rownames

    ## Run unit test ##
    # run the test data through the program
    return CountMatrix(test_df)


def test_entropy(entropy_test_counts_obj):

    from de_toolkit.outlier import entropy

    results = entropy(entropy_test_counts_obj, 0.05)

    # check the results of the unit test
    assert results["entropy"].iloc[19] == 0 and results["entropy_p0_05"].iloc[19]
    assert True not in results["entropy_p0_05"].iloc[0:18].values.tolist()


def test_entropy_cli(tmp_path, fake_counts_csv):
    # regression: main passed the raw DataFrame instead of the count object,
    # so the entropy subcommand crashed on any invocation
    from de_toolkit.outlier import main

    out = tmp_path / "flags.csv"
    main(
        [
            "detk-outlier",
            "entropy",
            fake_counts_csv,
            "-p",
            "0.05",
            "-o",
            str(out),
            f"--report-dir={tmp_path / 'rep'}",
        ]
    )
    assert out.exists()


# all-zero features and row alignment (#123), -p as a fraction (#123, DETK-0200)


def _entropy_counts(zero_rows):
    """
    A 12-feature x 6-sample counts matrix with distinct, non-trivial rows; the
    features named in *zero_rows* (by position) are all zero.
    """
    import numpy as np
    from de_toolkit.common import CountMatrix

    rng = np.random.default_rng(123)
    data = rng.integers(1, 200, size=(12, 6))
    # a few rows dominated by one sample, so some entropies are low
    data[2] = [500, 0, 0, 1, 0, 0]
    data[7] = [0, 0, 900, 0, 2, 0]
    data[10] = [0, 0, 0, 0, 0, 40]
    for i in zero_rows:
        data[i] = 0
    df = pandas.DataFrame(
        data,
        index=[f"gene_{i:02d}" for i in range(12)],
        columns=[f"s{j}" for j in range(6)],
    )
    return CountMatrix(df)


@pytest.mark.parametrize(
    "zero_rows",
    [[], [0], [5], [11], [0, 5, 11], [3, 4, 9]],
    ids=["none", "first", "middle", "last", "first-middle-last", "several"],
)
def test_entropy_all_zero_features(zero_rows, caplog):
    import numpy as np
    import scipy.stats
    from de_toolkit.outlier import entropy

    counts_obj = _entropy_counts(zero_rows)
    counts = counts_obj.counts
    with caplog.at_level("WARNING", logger="de_toolkit.outlier"):
        results = entropy(counts_obj, 0.25)

    # rows are the input's features, in the input's order
    assert results.index.equals(counts.index)
    assert list(results.columns) == ["entropy", "entropy_p0_25"]
    assert results["entropy_p0_25"].dtype == bool

    zero = [counts.index[i] for i in zero_rows]
    nonzero = [g for g in counts.index if g not in zero]

    # each row's entropy is its own feature's
    for gene in nonzero:
        assert results.loc[gene, "entropy"] == pytest.approx(
            scipy.stats.entropy(counts.loc[gene].to_numpy())
        )

    # all-zero features: missing entropy, not flagged, one warning with the count
    assert results.loc[zero, "entropy"].isna().all()
    assert not results.loc[zero, "entropy_p0_25"].any()
    warnings_ = [r for r in caplog.records if r.levelname == "WARNING"]
    if zero:
        assert len(warnings_) == 1
        assert str(len(zero)) in warnings_[0].getMessage()
    else:
        assert not warnings_

    # the percentile is the 25th over the non-zero features only
    nonzero_entropy = results.loc[nonzero, "entropy"].to_numpy()
    threshold = np.percentile(nonzero_entropy, 25)
    assert results.loc[nonzero, "entropy_p0_25"].tolist() == (nonzero_entropy < threshold).tolist()


def test_entropy_threshold_is_a_fraction():
    # -p 0.05 is the 5th percentile, not the 0.05th (DETK-0200)
    import numpy as np
    from de_toolkit.common import CountMatrix
    from de_toolkit.outlier import EntropyCounts

    rng = np.random.default_rng(7)
    data = rng.integers(0, 50, size=(400, 5))
    data[:, 0] += 1  # no all-zero rows
    counts_obj = CountMatrix(pandas.DataFrame(data, index=[f"g{i}" for i in range(400)]))
    obj = EntropyCounts(counts_obj, 0.05)
    ent = obj.output["entropy"].to_numpy()
    assert obj.entropy_threshold == pytest.approx(np.percentile(ent, 5))
    assert obj.num_flagged == int((ent < np.percentile(ent, 5)).sum())
    assert obj.output["entropy_p0_05"].sum() == obj.num_flagged
    # the 5th percentile of 400 features flags about 20, not 0 or 1
    assert 10 <= obj.num_flagged <= 25


@pytest.mark.parametrize("threshold", [0, 1, 5, -0.1, 1.5])
def test_entropy_threshold_out_of_range(threshold):
    from de_toolkit.outlier import entropy

    with pytest.raises(ValueError, match="between 0 and 1"):
        entropy(_entropy_counts([]), threshold)


def test_entropy_cli_all_zero_middle(tmp_path):
    import scipy.stats
    from de_toolkit.outlier import main

    counts = _entropy_counts([5]).counts
    counts_fn = tmp_path / "counts.csv"
    counts.to_csv(counts_fn)
    out = tmp_path / "flags.csv"
    plot = tmp_path / "plot.png"
    main(
        [
            "detk-outlier",
            "entropy",
            str(counts_fn),
            "-p",
            "0.25",
            "-o",
            str(out),
            "--plot-output",
            str(plot),
            f"--report-dir={tmp_path / 'rep'}",
        ]
    )
    assert plot.exists()
    text = out.read_text().splitlines()
    # the all-zero feature's entropy is empty in the CSV, and it is not flagged
    assert text[1 + 5] == "gene_05,,False"
    res = pandas.read_csv(out, index_col=0)
    assert res.index.tolist() == counts.index.tolist()
    for gene in counts.index.drop("gene_05"):
        assert res.loc[gene, "entropy"] == pytest.approx(
            scipy.stats.entropy(counts.loc[gene].to_numpy())
        )


@pytest.mark.parametrize("value", ["0", "1", "5", "-0.05", "1.5"])
def test_entropy_cli_percentile_out_of_range(tmp_path, fake_counts_csv, value, capsys):
    from de_toolkit.outlier import main

    with pytest.raises(SystemExit) as exc:
        main(["detk-outlier", "entropy", fake_counts_csv, "-p", value, "--no-report"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "-p/--percentile" in err and "between 0 and 1" in err
