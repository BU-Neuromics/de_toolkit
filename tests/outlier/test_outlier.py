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


@pytest.mark.parametrize(
    "threshold, name",
    [
        (0.05, "entropy_p0_05"),
        (0.1, "entropy_p0_10"),
        (0.10, "entropy_p0_10"),
        (0.5, "entropy_p0_50"),
        (0.25, "entropy_p0_25"),
        (0.125, "entropy_p0_125"),
        (0.001, "entropy_p0_001"),
        (1e-05, "entropy_p0_00001"),
        (0.999, "entropy_p0_999"),
    ],
)
def test_entropy_flag_column_name(threshold, name):
    from de_toolkit.outlier import entropy, flag_column

    assert flag_column(threshold) == name
    results = entropy(_entropy_counts([5]), threshold)
    assert list(results.columns) == ["entropy", name]


@pytest.mark.parametrize(
    "value, name",
    [("1e-05", "entropy_p0_00001"), ("0.1", "entropy_p0_10"), ("0.10", "entropy_p0_10")],
)
def test_entropy_cli_flag_column_name(tmp_path, value, name):
    # -p 1e-05 passed the range check and then failed naming the column (exit 1)
    from de_toolkit.outlier import main

    counts_fn = tmp_path / "counts.csv"
    _entropy_counts([]).counts.to_csv(counts_fn)
    out = tmp_path / "flags.csv"
    main(["detk-outlier", "entropy", str(counts_fn), "-p", value, "-o", str(out), "--no-report"])
    assert out.read_text().splitlines()[0].split(",")[1:] == ["entropy", name]


# -p left out (#222, DETK-0860): v1.0.0 exited 2 with "argument
# -p/--percentile: invalid float value: None"; -p defaults to 0.05


def test_entropy_cli_without_percentile(tmp_path, capsys):
    import json

    from de_toolkit.outlier import main

    counts_fn = tmp_path / "counts.csv"
    _entropy_counts([5]).counts.to_csv(counts_fn)
    out = tmp_path / "flags.csv"
    rep = tmp_path / "rep"
    main(["detk-outlier", "entropy", str(counts_fn), "-o", str(out), f"--report-dir={rep}"])
    assert "invalid float value: None" not in capsys.readouterr().err

    # the same flags, column and recorded parameter as an explicit -p 0.05
    out_p = tmp_path / "flags_p.csv"
    rep_p = tmp_path / "rep_p"
    main(
        [
            "detk-outlier",
            "entropy",
            str(counts_fn),
            "-p",
            "0.05",
            "-o",
            str(out_p),
            f"--report-dir={rep_p}",
        ]
    )
    assert out.read_text().splitlines()[0].split(",")[1:] == ["entropy", "entropy_p0_05"]
    assert out.read_text() == out_p.read_text()

    # the module JSON records the threshold and results of -p 0.05
    def module_json(rep_dir):
        (path,) = (rep_dir / "json").glob("*.json")
        return json.loads(path.read_text())

    mod, mod_p = module_json(rep), module_json(rep_p)
    assert mod["params"] == mod_p["params"] == {"threshold": 0.05}
    assert mod["properties"] == mod_p["properties"]


def test_entropy_help_states_percentile_default(capsys):
    from de_toolkit.outlier import main

    with pytest.raises(SystemExit) as exc:
        main(["detk-outlier", "entropy", "--help"])
    assert exc.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "between 0 and 1 (default: 0.05)" in help_text


# an integer matrix where a count is shrunk (g1's 301 in D), and the same
# counts written with decimals: on 1.0.0 the first exited 1 with
# "Invalid value '[...]' for dtype 'int64'" in PMFTransform (#219). By hand,
# per feature (#226), p_max 0.5, toward B's 12: D = 12 + (D - 12) * 0.25
#   301 / 334 > 0.5 -> 84.25; 84.25 / 117.25 > 0.5 -> 30.0625;
#   30.0625 / 63.0625 <= 0.5, done. g2 and g3 are unchanged
SHRUNK_301 = 30.0625
SHRINK_INT = "gene,A,B,C,D\ng1,10,12,11,301\ng2,20,22,21,23\ng3,30,31,33,32\n"
SHRINK_FLOAT = (
    "gene,A,B,C,D\ng1,10.0,12.0,11.0,301.0\ng2,20.0,22.0,21.0,23.0\ng3,30.0,31.0,33.0,32.0\n"
)


def _shrink_cli(counts, tmp_path, name, *extra):
    from de_toolkit.outlier import main

    counts_fn = tmp_path / f"{name}.csv"
    counts_fn.write_text(counts)
    out = tmp_path / f"{name}_shrunk.csv"
    try:
        main(["detk-outlier", "shrink", str(counts_fn), "--no-report", "-o", str(out), *extra])
    except SystemExit as e:
        return e.code, None
    return 0, pandas.read_csv(out, index_col=0)


def test_shrink_cli_integer_counts(tmp_path):
    int_code, int_out = _shrink_cli(SHRINK_INT, tmp_path, "int")
    float_code, float_out = _shrink_cli(SHRINK_FLOAT, tmp_path, "float")
    assert (int_code, float_code) == (0, 0)
    # a count was shrunk, to a fraction
    assert int_out.loc["g1", "D"] == SHRUNK_301
    assert (
        int_out.drop(index="g1", columns="D")
        .eq(pandas.read_csv(tmp_path / "int.csv", index_col=0).drop(index="g1", columns="D"))
        .all(axis=None)
    )
    assert all(t.kind == "f" for t in int_out.dtypes)
    pandas.testing.assert_frame_equal(int_out, float_out)


@pytest.mark.parametrize("counts", [SHRINK_INT, SHRINK_FLOAT], ids=["int", "float"])
def test_shrink_integer_counts_python(counts, tmp_path):
    from de_toolkit.common import CountMatrix
    from de_toolkit.outlier import shrink

    counts_fn = tmp_path / "counts.csv"
    counts_fn.write_text(counts)
    frame = pandas.read_csv(counts_fn, index_col=0)
    out = shrink(CountMatrix(frame))
    assert all(t.kind == "f" for t in out.dtypes)
    assert out.loc["g1", "D"] == SHRUNK_301
    # the input is not changed
    assert frame.loc["g1", "D"] == 301


def test_pmf_transform_integer_counts():
    from de_toolkit.outlier import pmf_transform

    ints = pandas.Series([10, 12, 11, 301], index=list("ABCD"))
    out = pmf_transform(ints, p_max=0.5)
    assert out.dtype == float
    assert out.tolist() == [10.0, 12.0, 11.0, SHRUNK_301]
    pandas.testing.assert_series_equal(out, pmf_transform(ints.astype(float), p_max=0.5))
    assert ints.dtype.kind == "i" and ints["D"] == 301
    # nothing to shrink: still float
    assert pmf_transform(pandas.Series([1, 1, 1, 1]), p_max=0.5).dtype == float


# -------------------------------------------------- shrink judges per feature
# shrink compares each sample's count with the feature's total across the
# samples (Labadorf et al. 2015; --help, the shrink docstring). On 1.0.0 it
# compared it with the sample's total across features: with g1 = 10 in every
# sample beside g2-g4 = 1, each sample's g1 is 10/13 of that sample's counts,
# over p_max = sqrt(1/4) = 0.5, and every g1 was written 1.5625 (#226)
SHRINK_AXIS = "gene,A,B,C,D\ng1,10.0,10.0,10.0,10.0\ng2,1.0,1.0,1.0,1.0\ng3,1.0,1.0,1.0,1.0\ng4,1.0,1.0,1.0,1.0\n"

# 1, 1, 1, 300 by hand, p_max 0.5, shrink factor 0.25; each step shrinks D
# toward the largest sample under p_max (1): D = 1 + (D - 1) * 0.25
#   D = 300:        300 / 303        > 0.5 -> 1 + 299 * 0.25     = 75.75
#   D = 75.75:      75.75 / 78.75    > 0.5 -> 1 + 74.75 * 0.25   = 19.6875
#   D = 19.6875:    19.6875 / 22.6875 > 0.5 -> 1 + 18.6875 * 0.25 = 5.671875
#   D = 5.671875:   5.671875 / 8.671875 > 0.5 -> 1 + 4.671875 * 0.25 = 2.16796875
#   D = 2.16796875: 2.16796875 / 5.16796875 = 0.42 <= 0.5, done
SHRUNK_300 = 2.16796875


def test_shrink_cli_judges_each_feature(tmp_path):
    code, out = _shrink_cli(SHRINK_AXIS, tmp_path, "axis")
    assert code == 0
    # each sample holds 1/4 of each feature's counts: nothing is shrunk (on
    # 1.0.0 every g1 was 1.5625)
    expected = pandas.read_csv(tmp_path / "axis.csv", index_col=0)
    pandas.testing.assert_frame_equal(out, expected)


def test_shrink_cli_shrinks_the_dominant_sample_alone(tmp_path):
    counts = SHRINK_AXIS + "g5,1.0,1.0,1.0,300.0\n"
    code, out = _shrink_cli(counts, tmp_path, "dominant")
    assert code == 0
    expected = pandas.read_csv(tmp_path / "dominant.csv", index_col=0)
    expected.loc["g5", "D"] = SHRUNK_300
    pandas.testing.assert_frame_equal(out, expected)


def test_pmf_transform_per_feature_by_hand():
    from de_toolkit.outlier import pmf_transform

    # equal counts: each sample holds 1/4, nothing is over 0.5
    assert pmf_transform(pandas.Series([10.0] * 4), p_max=0.5).tolist() == [10.0] * 4
    assert pmf_transform(pandas.Series([1, 1, 1, 300]), p_max=0.5).tolist() == [
        1.0,
        1.0,
        1.0,
        SHRUNK_300,
    ]
    # D is shrunk toward C's 5: D = 5 + (D - 5) * 0.25, from 40 to 13.75,
    # 7.1875, 5.546875, ...: D / (D + 5) stays over 0.5 while D > 5, so D
    # comes to 5 (once 0.25 ** k * 35 is lost to rounding), and 5 / 10 is not
    # over 0.5
    assert pmf_transform(pandas.Series([0, 0, 5, 40]), p_max=0.5).tolist() == [0, 0, 5, 5]


# DETK-0861: a feature whose counts are all in samples over p_max has no
# sample to shrink toward and is left as read, the log giving how many
@pytest.mark.parametrize(
    "counts, p_max",
    [
        # counted in one sample: D holds all of it
        ([0, 0, 0, 40], 0.5),
        # two samples with counts, each 1/2 > p_max 0.3
        ([0, 0, 10, 10], 0.3),
        # D is shrunk toward C until C is over p_max too: by hand, p_max 0.25,
        # D = 1 + (D - 1) * 0.25: 10 / 11 > 0.25 -> 3.25; 3.25 / 4.25 > 0.25
        # (C 1 / 4.25 = 0.24 is not) -> 1.5625; now C is 1 / 2.5625 = 0.39 >
        # 0.25 too, and A and B, under it, have no counts
        ([0, 0, 1, 10], 0.25),
    ],
)
def test_pmf_transform_nothing_to_shrink_toward(counts, p_max):
    from de_toolkit.outlier import PMFTransform, pmf_transform

    feature = pandas.Series(counts, index=list("ABCD"))
    out = pmf_transform(feature, p_max=p_max)
    pandas.testing.assert_series_equal(out, feature.astype(float))
    assert PMFTransform(feature, p_max=p_max).unchanged


def test_shrink_cli_single_sample_feature_unchanged(tmp_path, caplog):
    import logging

    counts = SHRINK_AXIS + "g5,1.0,1.0,1.0,300.0\ng6,0.0,0.0,0.0,40.0\ng7,0.0,0.0,0.0,7.0\n"
    with caplog.at_level(logging.WARNING, logger="de_toolkit.outlier"):
        code, out = _shrink_cli(counts, tmp_path, "single")
    assert code == 0
    expected = pandas.read_csv(tmp_path / "single.csv", index_col=0)
    expected.loc["g5", "D"] = SHRUNK_300
    pandas.testing.assert_frame_equal(out, expected)
    assert "2 feature(s) have all their counts in samples over p_max 0.5" in caplog.text


@pytest.mark.parametrize("value", ["0.2", "0.249", "1.5", "0", "-0.5"])
def test_shrink_cli_p_max_out_of_range(value, tmp_path, capsys):
    code, out = _shrink_cli(SHRINK_AXIS, tmp_path, "bad_p", "-p", value)
    assert code == 2
    assert out is None
    err = capsys.readouterr().err
    assert "-p/--p-max" in err
    assert "at least 1 / number of samples (0.25 with 4 samples)" in err


@pytest.mark.parametrize("value", ["0.25", "1"])
def test_shrink_cli_p_max_bounds_accepted(value, tmp_path):
    # at 1/n a feature with equal counts is not over; at 1 nothing can be
    code, out = _shrink_cli(SHRINK_AXIS, tmp_path, "edge_p", "-p", value)
    assert code == 0
    pandas.testing.assert_frame_equal(out, pandas.read_csv(tmp_path / "edge_p.csv", index_col=0))


def test_shrink_python_p_max_below_one_over_n():
    from de_toolkit.common import CountMatrix
    from de_toolkit.outlier import pmf_transform, shrink

    frame = pandas.DataFrame({s: [10.0, 1.0] for s in "ABCD"}, index=["g1", "g2"])
    with pytest.raises(ValueError, match=r"at least 1 / number of samples \(0.25"):
        shrink(CountMatrix(frame), p_max=0.2)
    with pytest.raises(ValueError, match=r"at least 1 / number of samples \(0.25"):
        pmf_transform(frame.loc["g1"], p_max=0.2)
