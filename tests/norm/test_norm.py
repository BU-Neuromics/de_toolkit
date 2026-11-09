import docopt
import numpy as np
import os
import pandas
import pytest
import tempfile
import warnings
from de_toolkit import wrapr

# decorator for skipping if Rscript is not installed
r_test = pytest.mark.skipif(
    not wrapr.check_r(), reason="Rscript executable not found, skipping test"
)
deseq2_test = pytest.mark.skipif(
    not wrapr.check_r_package("DESeq2"), reason="DESeq2 R package not found, skipping test"
)


@deseq2_test
def test_norm_cli():
    from de_toolkit.norm import main

    with pytest.raises(docopt.DocoptExit):
        main()


@deseq2_test
def test_deseq2_norm_cli_stdout(fake_counts_csv, fake_column_data_csv):
    from de_toolkit.norm import main

    main(["detk-norm", "deseq2", fake_counts_csv])


@deseq2_test
def test_deseq2_norm_cli(fake_counts_csv, fake_column_data_csv):

    from de_toolkit import CountMatrixFile
    from de_toolkit.norm import main, deseq2

    f = tempfile.NamedTemporaryFile("wt", delete=False)
    f.close()  # close the file so the command can write to it cross-platform

    main(["detk-norm", "deseq2", f"--output={f.name}", fake_counts_csv])

    in_counts = CountMatrixFile(fake_counts_csv)
    norm_counts = deseq2(in_counts)

    out_counts = CountMatrixFile(f.name)

    assert np.allclose(norm_counts, out_counts.counts)

    # cleanup the csv
    os.remove(f.name)


@deseq2_test
def test_estimateSizeFactors(fake_counts_numpy_matrix):

    from de_toolkit.norm import estimateSizeFactors, estimateSizeFactors_wrapr

    # the matrix is constructed such that the size factors are
    # 1/4, 1, 4
    # the geometric mean of each row is the middle sample
    cnts = fake_counts_numpy_matrix

    true_size_factors = cnts[2, :] / cnts[2, 1]
    deseq2_size_factors = estimateSizeFactors_wrapr(cnts)
    size_factors = estimateSizeFactors(cnts)

    assert np.allclose(size_factors, true_size_factors)
    assert np.allclose(size_factors, deseq2_size_factors)


def test_estimateSizeFactors_allzero(fake_counts_numpy_matrix):
    # make sure the function raises when all rows contain one zero
    from de_toolkit.norm import estimateSizeFactors, NormalizationException

    # set the first column to zero
    cnts = fake_counts_numpy_matrix.copy()
    cnts[:, 0] = 0

    # this will raise warnings that we can safely ignore (I think)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(NormalizationException):
            estimateSizeFactors(cnts)


@deseq2_test
def test_estimateSizeFactors_somezero(fake_counts_numpy_matrix):

    from de_toolkit.norm import estimateSizeFactors, estimateSizeFactors_wrapr

    # the matrix is constructed such that the size factors are
    # 1/4, 1, 4
    # the geometric mean of each row is the middle sample
    cnts = fake_counts_numpy_matrix.copy()
    cnts[0, 2] = cnts[4, 2] = 0

    # the is the median normalized factor is in cnts[2,:]

    geom_mean = cnts[2, :].prod() ** (1 / cnts.shape[1])

    # this will raise warnings that we can safely ignore (I think)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        true_size_factors = cnts[2, :] / geom_mean
        deseq2_size_factors = estimateSizeFactors_wrapr(cnts)
        size_factors = estimateSizeFactors(cnts)

    assert np.allclose(size_factors, true_size_factors)
    assert np.allclose(size_factors, deseq2_size_factors)


@deseq2_test
def test_deseq2(fake_counts_obj):

    from de_toolkit.norm import deseq2

    cnts = fake_counts_obj.counts.values

    true_size_factors = cnts[2, :] / cnts[2, 1]

    true_norm_cnts = cnts / true_size_factors

    norm_cnts = deseq2(fake_counts_obj)

    assert np.allclose(norm_cnts, true_norm_cnts)


@deseq2_test
def test_deseq2_py_vs_wrapr(fake_counts_obj):

    from de_toolkit.norm import deseq2, deseq2_wrapr

    # this raises R warnings about converting floats to integers that we can
    # ignore
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # the design associated with fake_counts_obj is category ~ counts
        # which is intended for testing Firth
        # change it to something DESeq2 expects
        fake_counts_obj.design = "counts ~ cont_cov + category"

        rpy_norm_counts = deseq2_wrapr(fake_counts_obj)

    py_norm_counts = deseq2(fake_counts_obj)

    assert np.allclose(rpy_norm_counts, py_norm_counts)


@deseq2_test
def test_deseq2_py_vs_wrapr_somezero(fake_counts_obj):

    from de_toolkit.norm import deseq2, deseq2_wrapr

    fake_counts_obj.counts.iloc[0, 2] = 0
    fake_counts_obj.counts.iloc[4, 2] = 0

    # this raises R warnings about converting floats to integers that we can
    # ignore
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # the design associated with fake_counts_obj is category ~ counts
        # which is intended for testing Firth
        # change it to something DESeq2 expects
        fake_counts_obj.design = "counts ~ cont_cov + category"

        rpy_norm_counts = deseq2_wrapr(fake_counts_obj)

        # suppress divide by zero warnings
        py_norm_counts = deseq2(fake_counts_obj)

    assert np.allclose(rpy_norm_counts, py_norm_counts)


def test_library_size():

    from de_toolkit.norm import library_size

    cnts = np.array([[1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])

    true_norm_cnts = np.array([[1 / 3, 1 / 3, 1 / 3], [1 / 3, 1 / 3, 1 / 3], [1 / 3, 1 / 3, 1 / 3]])

    norm_cnts = library_size(cnts)

    assert np.allclose(norm_cnts, true_norm_cnts)


def test_fpkm_missing_lens(fake_counts_obj, fake_counts_gene_lengths):
    from de_toolkit.norm import fpkm, NormalizationException

    with pytest.raises(NormalizationException):
        fpkm(fake_counts_obj.counts, pandas.Series([1, 2, 3], index=("gene1", "gene2", "gene3")))


def test_fpkm(fake_counts_obj, fake_counts_gene_lengths):
    from de_toolkit.norm import fpkm

    # FPKM = count * 1e9 / (length * library size), worked by hand on
    # _small_counts and _small_lengths (lengths g1 1000, g2 2000, g3 4000):
    #   a = [1, 3, 0], library size 4:
    #     g1: 1 * 1e9 / (1000 * 4) = 250,000
    #     g2: 3 * 1e9 / (2000 * 4) = 375,000
    #     g3: 0
    #   b = [2, 4, 4], library size 10:
    #     g1: 2 * 1e9 / (1000 * 10) = 200,000
    #     g2: 4 * 1e9 / (2000 * 10) = 200,000
    #     g3: 4 * 1e9 / (4000 * 10) = 100,000
    res = fpkm(_small_counts(), _small_lengths())
    assert list(res.index) == ["g1", "g2", "g3"]
    assert np.allclose(res["a"], [250_000.0, 375_000.0, 0.0])
    assert np.allclose(res["b"], [200_000.0, 200_000.0, 100_000.0])

    # the fixture: lengths 2..6, column a equals the length, b its square and
    # c its cube, with library sizes 20, 90 and 440
    res = fpkm(fake_counts_obj.counts, fake_counts_gene_lengths)
    lens = np.arange(2, res.shape[0] + 2)
    assert np.allclose(res["a"], 1e9 / 20)
    assert np.allclose(res["b"], lens * 1e9 / 90)
    assert np.allclose(res["c"], lens**2 * 1e9 / 440)


def test_fpkm_is_cpm_per_kb():
    # FPKM is CPM divided by the length in kilobases
    from de_toolkit.norm import cpm, fpkm

    cnts = _small_counts()
    lens = pandas.Series([1000.0, 2000.0, 4000.0], index=cnts.index)
    assert np.allclose(fpkm(cnts, lens), cpm(cnts).div(lens / 1e3, axis=0))


@pytest.mark.parametrize("bad", [0, -5, float("nan")])
def test_fpkm_nonpositive_lens(bad):
    # fpkm refuses missing, zero and negative lengths, as tpm does
    from de_toolkit.norm import fpkm, NormalizationException

    lens = pandas.Series([1000, 1000, bad], index=["g1", "g2", "g3"])
    with pytest.raises(NormalizationException, match="not a positive number"):
        fpkm(_small_counts(), lens)


def test_fpkm_missing_first_length_from_file(tmp_path):
    # a missing length read from a lengths file is refused, not "not found"
    from de_toolkit.norm import read_lengths, fpkm, NormalizationException

    fn = tmp_path / "lengths.tsv"
    fn.write_text("g1\tNA\ng2\t2000\ng3\t4000\n")
    with pytest.raises(NormalizationException, match="not a positive number"):
        fpkm(_small_counts(), read_lengths(str(fn)))


def test_fpkm_properties(fake_counts_obj, fake_counts_gene_lengths):
    # regression: FPKMCounts.properties used to reference an undefined name
    from de_toolkit.norm import FPKMCounts

    obj = FPKMCounts(fake_counts_obj.counts, fake_counts_gene_lengths)
    props = obj.properties
    assert props["num_kept"] == len(obj.output)
    # lengths are summarized as quantiles (the raw Series broke serialization)
    qs = props["length_quantiles"]
    assert qs[0]["q"] == 0 and qs[-1]["q"] == 100
    assert qs[0]["length"] == float(fake_counts_gene_lengths.min())
    assert qs[-1]["length"] == float(fake_counts_gene_lengths.max())
    import json

    json.dumps(props)  # must be serializable


# --------------------------------------------------------------------------
# CPM and TPM (#24)
# --------------------------------------------------------------------------


def _small_counts():
    return pandas.DataFrame({"a": [1.0, 3.0, 0.0], "b": [2.0, 4.0, 4.0]}, index=["g1", "g2", "g3"])


def _small_lengths():
    # deliberately out of order and with an unused entry
    return pandas.Series([4000, 1000, 2000, 99], index=["g3", "g1", "g2", "unused"])


def test_cpm():
    from de_toolkit.norm import cpm

    cnts = _small_counts()
    res = cpm(cnts)
    assert np.allclose(res["a"], [0.25e6, 0.75e6, 0.0])
    assert np.allclose(res["b"], [0.2e6, 0.4e6, 0.4e6])
    assert np.allclose(res.sum(axis=0), 1e6)
    # CPM is library size normalization scaled by one million
    from de_toolkit.norm import library_size

    assert np.allclose(res, library_size(cnts) * 1e6)


def test_cpm_properties():
    import json

    from de_toolkit.norm import CPMCounts

    obj = CPMCounts(_small_counts())
    props = obj.properties
    assert props["num_features"] == 3
    assert props["library_sizes"] == {"a": 4.0, "b": 10.0}
    assert obj.name == "cpmcounts"
    json.dumps(props)


def test_tpm():
    from de_toolkit.norm import tpm

    res = tpm(_small_counts(), _small_lengths())
    # a: rates per kb 1, 1.5, 0 -> 1/2.5, 1.5/2.5, 0
    assert np.allclose(res["a"], [0.4e6, 0.6e6, 0.0])
    # b: rates per kb 2, 2, 1 -> 2/5, 2/5, 1/5
    assert np.allclose(res["b"], [0.4e6, 0.4e6, 0.2e6])
    assert np.allclose(res.sum(axis=0), 1e6)
    assert list(res.index) == ["g1", "g2", "g3"]


def test_tpm_equal_lengths_is_cpm():
    from de_toolkit.norm import cpm, tpm

    cnts = _small_counts()
    lens = pandas.Series([1500] * 3, index=cnts.index)
    assert np.allclose(tpm(cnts, lens), cpm(cnts))


def test_tpm_missing_lens():
    from de_toolkit.norm import tpm, NormalizationException

    with pytest.raises(NormalizationException):
        tpm(_small_counts(), pandas.Series([1, 2], index=["g1", "g2"]))


@pytest.mark.parametrize("bad", [0, -5, float("nan")])
def test_tpm_nonpositive_lens(bad):
    from de_toolkit.norm import tpm, NormalizationException

    lens = pandas.Series([1000, 1000, bad], index=["g1", "g2", "g3"])
    with pytest.raises(NormalizationException):
        tpm(_small_counts(), lens)


def test_tpm_properties():
    import json

    from de_toolkit.norm import TPMCounts

    obj = TPMCounts(_small_counts(), _small_lengths())
    props = obj.properties
    assert props["num_features"] == 3
    assert obj.name == "tpmcounts"
    qs = props["length_quantiles"]
    # only the lengths of features in the counts matrix are summarized
    assert qs[0]["length"] == 1000.0 and qs[-1]["length"] == 4000.0
    json.dumps(props)


@pytest.mark.parametrize("header", [False, True])
@pytest.mark.parametrize("delim", [",", "\t"])
def test_read_lengths(tmp_path, header, delim):
    from de_toolkit.norm import read_lengths

    fn = tmp_path / "lengths.txt"
    lines = ([f"id{delim}length"] if header else []) + [f"g1{delim}1000", f"g2{delim}2500"]
    fn.write_text("\n".join(lines) + "\n")
    lens = read_lengths(str(fn))
    assert list(lens.index) == ["g1", "g2"]
    assert list(lens.values) == [1000, 2500]


@pytest.mark.parametrize("first", ["NA", "", "nan"])
def test_read_lengths_missing_first_length_is_not_header(tmp_path, first):
    # a headerless file whose first length is missing keeps that feature, so
    # tpm reports it as "not a positive number", not as "not found"
    from de_toolkit.norm import read_lengths, tpm, NormalizationException

    fn = tmp_path / "lengths.tsv"
    fn.write_text(f"g1\t{first}\ng2\t2000\ng3\t4000\n")
    lens = read_lengths(str(fn))
    assert list(lens.index) == ["g1", "g2", "g3"]
    assert np.isnan(lens["g1"])
    with pytest.raises(NormalizationException, match="not a positive number"):
        tpm(_small_counts(), lens)


def test_read_lengths_duplicate_ids(tmp_path):
    from de_toolkit.norm import read_lengths, NormalizationException

    fn = tmp_path / "lengths.tsv"
    fn.write_text("id\tlength\ng1\t1000\ng2\t2000\ng1\t1500\ng3\t4000\n")
    with pytest.raises(NormalizationException, match="more than once"):
        read_lengths(str(fn))


@pytest.mark.parametrize("norm", ["tpm", "fpkm"])
def test_duplicate_lens_series(norm):
    # a duplicated name in an in-memory lengths Series is refused too, rather
    # than adding a row to the output
    from de_toolkit import norm as norm_mod

    lens = pandas.Series([1000, 2000, 4000, 1500], index=["g1", "g2", "g3", "g1"])
    with pytest.raises(norm_mod.NormalizationException, match="more than once"):
        getattr(norm_mod, norm)(_small_counts(), lens)


def test_tpm_numeric_ids():
    # integer feature IDs (as read from a counts file of Entrez IDs) match the
    # string IDs of a lengths file, and the output keeps the integer index
    from de_toolkit.norm import tpm

    cnts = _small_counts()
    cnts.index = [101, 102, 103]
    lens = pandas.Series([4000, 1000, 2000], index=["103", "101", "102"])
    res = tpm(cnts, lens)
    assert list(res.index) == [101, 102, 103]
    assert np.allclose(res["a"], [0.4e6, 0.6e6, 0.0])
    assert np.allclose(res["b"], [0.4e6, 0.4e6, 0.2e6])


@pytest.mark.parametrize("cmd", ["tpm", "fpkm"])
def test_norm_cli_numeric_ids(tmp_path, cmd):
    from de_toolkit.norm import main

    counts_fn = tmp_path / "counts.csv"
    cnts = _small_counts()
    cnts.index = [101, 102, 103]
    cnts.rename_axis("gene").to_csv(counts_fn)
    lengths_fn = tmp_path / "lengths.tsv"
    lengths_fn.write_text("103\t4000\n101\t1000\n102\t2000\n")
    out_fn = tmp_path / "out.csv"
    main(["detk-norm", cmd, f"--output={out_fn}", "--no-report", str(counts_fn), str(lengths_fn)])
    res = pandas.read_csv(out_fn, index_col=0)
    assert list(res.index) == [101, 102, 103]
    if cmd == "tpm":
        assert np.allclose(res.values, [[0.4e6, 0.4e6], [0.6e6, 0.4e6], [0.0, 0.2e6]])
    else:
        assert np.allclose(res.values, [[2.5e5, 2e5], [3.75e5, 2e5], [0.0, 1e5]])
    assert "101" in out_fn.read_text().splitlines()[1]


@pytest.mark.parametrize("norm", ["cpm", "tpm", "fpkm"])
def test_all_zero_sample(norm, caplog):
    # a sample with no counts has NaN output and a warning
    import logging

    from de_toolkit import norm as norm_mod

    cnts = _small_counts()
    cnts["z"] = 0.0
    args = (cnts,) if norm == "cpm" else (cnts, _small_lengths())
    with caplog.at_level(logging.WARNING):
        res = getattr(norm_mod, norm)(*args)
    assert res["z"].isna().all()
    if norm != "fpkm":
        assert np.allclose(res[["a", "b"]].sum(axis=0), 1e6)
    assert "zero total counts" in caplog.text


def _write_small_inputs(tmp_path):
    counts_fn = tmp_path / "counts.csv"
    _small_counts().rename_axis("gene").to_csv(counts_fn)
    lengths_fn = tmp_path / "lengths.tsv"
    lengths_fn.write_text("g3\t4000\ng1\t1000\ng2\t2000\n")
    return str(counts_fn), str(lengths_fn)


@pytest.mark.parametrize(
    "cmd,expected",
    [
        ("library", [[0.25, 0.2], [0.75, 0.4], [0.0, 0.4]]),
        ("cpm", [[0.25e6, 0.2e6], [0.75e6, 0.4e6], [0.0, 0.4e6]]),
        ("tpm", [[0.4e6, 0.4e6], [0.6e6, 0.4e6], [0.0, 0.2e6]]),
    ],
)
def test_norm_cli_cpm_tpm_library(tmp_path, cmd, expected):
    import json

    from de_toolkit.norm import main
    from de_toolkit.report_specs import view_for

    counts_fn, lengths_fn = _write_small_inputs(tmp_path)
    out_fn = str(tmp_path / "out.csv")
    report_dir = str(tmp_path / "report")
    argv = ["detk-norm", cmd, f"--output={out_fn}", f"--report-dir={report_dir}", counts_fn]
    if cmd == "tpm":
        argv.append(lengths_fn)
    main(argv)

    res = pandas.read_csv(out_fn, index_col=0)
    assert np.allclose(res.values, expected)

    docs = [json.loads(p.read_text()) for p in (tmp_path / "report" / "json").glob("*.json")]
    assert len(docs) == 1
    family, _, _, view = view_for(docs[0])
    assert family == "norm"
    assert view["type"] == "vega"


def test_norm_cli_fpkm_reads_lengths(tmp_path):
    # the fpkm subcommand shares the lengths reader with tpm
    from de_toolkit.norm import main

    counts_fn, lengths_fn = _write_small_inputs(tmp_path)
    out_fn = str(tmp_path / "out.csv")
    main(["detk-norm", "fpkm", f"--output={out_fn}", "--no-report", counts_fn, lengths_fn])
    res = pandas.read_csv(out_fn, index_col=0)
    assert res.shape == (3, 2)
    # the values worked by hand in test_fpkm
    assert np.allclose(res.values, [[2.5e5, 2e5], [3.75e5, 2e5], [0.0, 1e5]])


@pytest.mark.parametrize("name", ["cpmcounts", "tpmcounts"])
def test_cpm_tpm_report_specs_compile(name):
    import json

    from de_toolkit.norm import CPMCounts, TPMCounts
    from de_toolkit.report_specs import view_for

    obj = (
        CPMCounts(_small_counts())
        if name == "cpmcounts"
        else TPMCounts(_small_counts(), _small_lengths())
    )
    mod = {"name": name, "params": {}, "properties": obj.properties}
    family, title, _, view = view_for(mod)
    assert family == "norm"
    assert view["type"] == "vega"
    vlc = pytest.importorskip("vl_convert")
    svg = vlc.vegalite_to_svg(json.dumps(view["spec"]))
    assert "<svg" in svg[:300]
