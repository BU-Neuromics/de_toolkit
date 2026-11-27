from collections import OrderedDict
import csv
import numpy as np
import pandas
import pytest
import os
import tempfile

from de_toolkit.wrapr import check_r, check_r_package

r_test = pytest.mark.skipif(not check_r(), reason="r is not installed, skipping test")
fgsea_test = pytest.mark.skipif(
    not check_r_package("fgsea"), reason="fgsea package not installed, skipping test"
)


@pytest.fixture
def gset_dict(request):
    d = OrderedDict()
    d["set1"] = ["gene1", "gene2", "gene3"]
    d["set2"] = ["gene1", "gene4", "gene5"]
    d["set3"] = ["gene1", "gene2", "gene3", "gene4", "gene5"]
    d["set4"] = ["gene6", "gene7", "gene8", "gene9", "gene10"]
    d["set5"] = ["gene1", "gene7", "gene3", "gene9", "gene5"]
    return d


@pytest.fixture()
def gmt_file(request, gset_dict):
    with tempfile.NamedTemporaryFile("wt", delete=False) as f:
        tmp_f = csv.writer(f, delimiter="\t")
        for name, ids in gset_dict.items():
            tmp_f.writerow([name, name] + list(ids))

    yield f.name

    # cleanup the csv
    os.remove(f.name)


@pytest.fixture()
def gmt_file_w_unicode(request):
    with tempfile.NamedTemporaryFile("wt", delete=False) as f:
        tmp_f = csv.writer(f, delimiter="\t")
        tmp_f.writerow(["set1", "tgf\u03b1", "gene1", "gene2"])

    yield f.name

    # cleanup the csv
    os.remove(f.name)


@pytest.fixture()
def gmt_obj(request, gset_dict):
    from de_toolkit.enrich import GMT

    return GMT(gset_dict)


@pytest.fixture()
def stat(request):
    return pandas.Series(range(10), index=[f"gene{_ + 1}" for _ in range(10)])


@pytest.fixture
def result_csv(request, stat):
    with tempfile.NamedTemporaryFile("wt", delete=False) as f:
        df = pandas.DataFrame(
            {
                "negstat": -stat.values,
                "nonsense": np.random.random(size=10),
                "stat": stat.values,
                "gene": stat.index.tolist(),
            },
            index=stat.index,
        )
        df.to_csv(f.name, index_label="id")

    yield f.name

    # cleanup the csv
    os.remove(f.name)


@pytest.fixture
def result_w_unannotated_csv(request, stat):
    with tempfile.NamedTemporaryFile("wt", delete=False) as f:
        new_stat = stat.copy()
        new_stat.loc["gene11"] = 0
        new_stat.loc["gene12"] = 0
        new_stat.loc["gene13"] = 0
        print(new_stat)

        df = pandas.DataFrame(
            {
                "negnew_stat": -new_stat.values,
                "nonsense": np.random.random(size=new_stat.size),
                "new_stat": new_stat.values,
                "gene": new_stat.index.tolist(),
            },
            index=new_stat.index,
        )
        df.to_csv(f.name, index_label="id")

    yield f.name

    # cleanup the csv
    os.remove(f.name)


@r_test
@fgsea_test
def test_fgsea_id_type_mismatch(gmt_obj, stat):
    from de_toolkit.enrich import fgsea

    # rename the stat index so there are no matches
    stat.index = ["X" + _ for _ in stat.index]
    with pytest.raises(Exception):
        fgsea(gmt_obj, stat, minSize=1)


@r_test
@fgsea_test
def test_fgsea_filter_unannot_cli(gmt_file, result_w_unannotated_csv):
    from de_toolkit.enrich import main

    # TODO I WAS TESTING --filter-unannotated
    with tempfile.NamedTemporaryFile("wt") as f:
        # test multilevel flag
        main(
            [
                "detk-enrich",
                "fgsea",
                "--nperm=100",
                "--filter-unannotated",
                "--statcol=new_stat",
                "--minSize=1",
                gmt_file,
                result_w_unannotated_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
        assert all(res.loc[["set4", "set5"], "NES"] > 0)


@r_test
@fgsea_test
def test_fgsea(gmt_obj, stat):
    from de_toolkit.enrich import fgsea
    import numpy

    # this way has set1, set2, and set3 negative NES,
    # set4 and set5 positive
    res = fgsea(gmt_obj, stat, minSize=1)
    assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
    assert all(res.loc[["set4", "set5"], "NES"] > 0)

    # same thing with parallelism
    res = fgsea(gmt_obj, stat, minSize=1, nproc=2)
    assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
    assert all(res.loc[["set4", "set5"], "NES"] > 0)

    # this is the opposite direction
    res = fgsea(gmt_obj, -stat, minSize=1)
    assert all(res.loc[["set1", "set2", "set3"], "NES"] > 0)
    assert all(res.loc[["set4", "set5"], "NES"] < 0)

    # if the stat column has NAs in it, fgsea warns the user that the
    # gene has been filtered out
    na_stat = stat.copy().astype(float)
    na_stat[0] = np.nan
    with pytest.warns(UserWarning):
        res = fgsea(gmt_obj, na_stat, minSize=1)

    # if some of the gene names are None detk should handle gracefully
    # and warn user
    null_stat = stat.copy().astype(float)
    null_stat.rename(index={"gene1": None}, inplace=True)
    null_stat.rename(index={"gene2": numpy.nan}, inplace=True)
    null_stat.rename(index={"gene3": ("a", "tuple")}, inplace=True)
    with pytest.warns(UserWarning):
        res = fgsea(gmt_obj, null_stat, minSize=1)


@r_test
@fgsea_test
def test_fgsea_multilevel(gmt_obj, stat):
    from de_toolkit.enrich import fgsea

    # same thing, but with multilevel mode
    res = fgsea(gmt_obj, stat, minSize=1, multilevel=True, nperm=100)
    assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
    assert all(res.loc[["set4", "set5"], "NES"] > 0)


@r_test
@fgsea_test
def test_fgsea_cli(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # normal operation, ranking by stat
        main(
            [
                "detk-enrich",
                "fgsea",
                "--minSize=1",
                "-c",
                "stat",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
        assert all(res.loc[["set4", "set5"], "NES"] > 0)


@r_test
@fgsea_test
def test_fgsea_cli_cores(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # normal operation, with two cores
        main(
            [
                "detk-enrich",
                "fgsea",
                "--cores=2",
                "--minSize=1",
                "-c",
                "stat",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
        assert all(res.loc[["set4", "set5"], "NES"] > 0)


@r_test
@fgsea_test
def test_fgsea_cli_routput(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        with tempfile.TemporaryDirectory() as d:
            main(
                [
                    "detk-enrich",
                    "fgsea",
                    f"--routput-dir={d}",
                    "--statcol=stat",
                    "--minSize=1",
                    gmt_file,
                    result_csv,
                    "-o",
                    f.name,
                ]
            )
            res = pandas.read_csv(f.name, index_col=0)
            assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
            assert all(res.loc[["set4", "set5"], "NES"] > 0)
            assert os.path.exists(os.path.join(d, "script.R"))

            with open(os.path.join(d, "stdout")) as f:
                out = f.read()
                assert len(out) != 0


@r_test
@fgsea_test
def test_fgsea_cli_alt_statcol(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # different column as statistic
        main(
            [
                "detk-enrich",
                "fgsea",
                "--minSize=1",
                "--statcol=negstat",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] > 0)
        assert all(res.loc[["set4", "set5"], "NES"] < 0)


@r_test
@fgsea_test
def test_fgsea_cli_abs_statcol(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # different column as statistic, but with abs value is
        # the same as normal stat
        main(
            [
                "detk-enrich",
                "fgsea",
                "--minSize=1",
                "--statcol=negstat",
                "--abs",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
        assert all(res.loc[["set4", "set5"], "NES"] > 0)


@r_test
@fgsea_test
def test_fgsea_cli_ascending(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # sort ascending operation on stat
        main(
            [
                "detk-enrich",
                "fgsea",
                "--minSize=1",
                "-c",
                "stat",
                "-a",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] > 0)
        assert all(res.loc[["set4", "set5"], "NES"] < 0)


@r_test
@fgsea_test
def test_fgsea_cli_idcol(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # speficy idcol
        main(
            [
                "detk-enrich",
                "fgsea",
                "--minSize=1",
                "--idcol=gene",
                "--statcol=stat",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
        assert all(res.loc[["set4", "set5"], "NES"] > 0)


@r_test
@fgsea_test
def test_fgsea_cli_wrapr_cores(gmt_file, result_csv):
    from de_toolkit.enrich import main
    from de_toolkit.wrapr import wrapr

    with tempfile.NamedTemporaryFile("wt") as f:
        with tempfile.NamedTemporaryFile("rt") as r_f:
            # check that the R script got the cores argument, which I assume
            # means it ran with that number of cores question mark?
            # this also is a test that the rda functionality works
            main(
                [
                    "detk-enrich",
                    "fgsea",
                    "--minSize=1",
                    "--cores=2",
                    f"--rda={r_f.name}",
                    "--statcol=stat",
                    gmt_file,
                    result_csv,
                    "-o",
                    f.name,
                ]
            )
            res = pandas.read_csv(f.name, index_col=0)
            assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
            assert all(res.loc[["set4", "set5"], "NES"] > 0)

            with wrapr(f'cat(readRDS("{r_f.name}")$params$nproc)') as r:
                assert r.stdout == "2"


@r_test
@fgsea_test
def test_fgsea_multilevel_cli(gmt_file, result_csv):
    from de_toolkit.enrich import main

    with tempfile.NamedTemporaryFile("wt") as f:
        # test multilevel flag
        main(
            [
                "detk-enrich",
                "fgsea",
                "--nperm=100",
                "--multilevel",
                "--minSize=1",
                "--statcol=stat",
                gmt_file,
                result_csv,
                "-o",
                f.name,
            ]
        )
        res = pandas.read_csv(f.name, index_col=0)
        assert all(res.loc[["set1", "set2", "set3"], "NES"] < 0)
        assert all(res.loc[["set4", "set5"], "NES"] > 0)


def test_gmt_obj(gset_dict):
    from de_toolkit.enrich import GMT

    gmt = GMT(gset_dict)
    assert gmt["set1"].name == "set1"
    assert gmt["set1"].ids == gset_dict["set1"]

    gmt["setX"] = gset_dict["set1"]

    assert gmt["setX"].name == "setX"
    assert gmt["setX"].ids == gset_dict["set1"]

    gmt.add("setY", gset_dict["set1"])

    assert gmt["setY"].name == "setY"
    assert gmt["setY"].desc == "setY"
    assert gmt["setY"].ids == gset_dict["set1"]

    gmt.add("setZ", gset_dict["set1"], desc="yippee")

    assert gmt["setZ"].name == "setZ"
    assert gmt["setZ"].desc == "yippee"
    assert gmt["setZ"].ids == gset_dict["set1"]


def test_gmt_file(gset_dict, gmt_file):
    from de_toolkit.enrich import GMT

    gmt = GMT()
    gmt.load_file(gmt_file)

    assert gmt["set1"].name == "set1"
    assert gmt["set1"].ids == gset_dict["set1"]

    with tempfile.NamedTemporaryFile("rt") as out_f:
        gmt.write_file(out_f.name)
        with open(out_f.name) as f:
            line = next(f).strip().split("\t")
            assert line[0] == "set1"
            assert line[1] == "set1"
            assert line[2:] == ["gene1", "gene2", "gene3"]


def test_gmt_file_w_unicode(gset_dict, gmt_file_w_unicode):
    from de_toolkit.enrich import GMT

    gmt = GMT()
    gmt.load_file(gmt_file_w_unicode)

    assert gmt["set1"].name == "set1"
    assert gmt["set1"].desc == "tgf\u03b1"


def test_fgsea_matches_numeric_ids():
    # regression: an all-integer ID column (e.g. Entrez) is parsed as int64
    # by pandas and used to silently match nothing against the string GMT IDs
    import pandas as pd

    from de_toolkit.enrich import GMT, FGSEARes

    gmt = GMT({"set1": [str(i) for i in range(100, 120)]})
    stat = pd.Series([float(i) for i in range(20)], index=pd.Index(list(range(100, 120))))
    assert stat.index.dtype.kind == "i"  # the problematic int64 index
    try:
        FGSEARes(gmt, stat, minSize=1)
    except Exception as e:
        # without R this raises before fgsea runs, but never the ID-mismatch
        # error the bug produced
        assert "No features map" not in str(e)


# an all-numeric ID column with zero-padded and versioned IDs (DETK-0015, #67)
PADDED_IDS = ["007", "010", "1.10", "1.1"]


@pytest.fixture
def padded_result_csv(tmp_path):
    fn = tmp_path / "result.csv"
    fn.write_text(
        "gene,baseMean,log2FoldChange,label\n007,10,1.5,a\n010,20,-2,b\n1.10,30,0.5,c\n1.1,40,3,d\n"
    )
    return str(fn)


def test_read_result_stat_keeps_ids_as_written(padded_result_csv):
    from de_toolkit.enrich import read_result_stat

    stat = read_result_stat(padded_result_csv, statcol="log2FoldChange")
    assert stat.index.tolist() == PADDED_IDS
    # as numbers
    assert stat.name == "log2FoldChange"
    assert stat.tolist() == [1.5, -2.0, 0.5, 3.0]

    stat = read_result_stat(padded_result_csv, idcol="gene", statcol="baseMean")
    assert stat.index.tolist() == PADDED_IDS
    assert stat.tolist() == [10, 20, 30, 40]

    stat = read_result_stat(padded_result_csv, idcol="0", statcol="1")
    assert stat.index.tolist() == PADDED_IDS
    assert stat.name == "baseMean"


def test_read_result_stat_id_not_first(tmp_path):
    from de_toolkit.enrich import read_result_stat

    fn = tmp_path / "result.tsv"
    fn.write_text("stat\tid\n1.5\t007\n-2\t010\n")
    stat = read_result_stat(str(fn), idcol="id")
    assert stat.index.tolist() == ["007", "010"]
    assert stat.tolist() == [1.5, -2.0]


def test_read_result_stat_bad_columns(padded_result_csv):
    from de_toolkit.enrich import read_result_stat

    with pytest.raises(ValueError, match="ID column"):
        read_result_stat(padded_result_csv, idcol="nope")
    with pytest.raises(ValueError, match="Stat column"):
        read_result_stat(padded_result_csv, statcol="9")


def test_fgsea_cli_passes_ids_as_written(monkeypatch, tmp_path, padded_result_csv):
    # the CLI hands fgsea the IDs as written, so 007 matches 007 in the GMT
    from de_toolkit import enrich

    gmt_fn = tmp_path / "sets.gmt"
    gmt_fn.write_text("set1\tset1\t007\t1.10\nset2\tset2\t010\t1.1\n")
    seen = {}

    class FakeFGSEARes(dict):
        def __init__(self, gmt, stat, **kwargs):
            self["params"] = {}
            seen["stat"] = stat
            seen["gmt_ids"] = {i for s in gmt.values() for i in s.ids}
            self.output = pandas.DataFrame({"pval": [0.5]}, index=["set1"])

    monkeypatch.setattr(enrich, "FGSEARes", FakeFGSEARes)
    enrich.main(
        [
            "detk-enrich",
            "fgsea",
            "--no-report",
            "-c",
            "log2FoldChange",
            str(gmt_fn),
            padded_result_csv,
            "-o",
            str(tmp_path / "out.csv"),
        ]
    )
    assert seen["stat"].index.tolist() == PADDED_IDS
    assert set(seen["stat"].index) == seen["gmt_ids"]


# DETK-0600: without -c, fgsea ranked by the last numeric column, which in a
# DESeq2 result is the last term's __padj (the audit's planted 'up' set came
# out NES -2.76, padj 0.5 where condition__treated__stat gives +2.13, padj
# 0.0003). Where more than one numeric column could rank, -c is required.
DESEQ2_COLUMNS = ["baseMean"] + [
    f"{term}__{s}"
    for term in ("Intercept", "condition__treated")
    for s in ("log2FoldChange", "lfcSE", "stat", "pvalue", "padj")
]


@pytest.fixture
def deseq2_result_csv(tmp_path):
    "A detk-de deseq2 result table: the ID column and 11 numeric columns"
    rng = np.random.default_rng(0)
    df = pandas.DataFrame(
        rng.random((10, len(DESEQ2_COLUMNS))),
        columns=DESEQ2_COLUMNS,
        index=pandas.Index([f"gene{_ + 1}" for _ in range(10)], name="gene"),
    )
    fn = tmp_path / "de.csv"
    df.to_csv(fn)
    return str(fn)


@pytest.fixture
def fake_fgsea(monkeypatch):
    """
    FGSEARes replaced by a stand-in that needs no R: it records the stat it
    was given in ``calls`` and returns a one-row result
    """
    from de_toolkit import enrich

    calls = []

    class fgseares(enrich.FGSEARes):
        def __init__(self, gmt, stat, **kwargs):
            calls.append(stat)
            self["params"] = {"minSize": kwargs.get("minSize")}
            self.gsea_res = pandas.DataFrame(
                {"pval": [0.5], "padj": [0.5], "NES": [1.0], "size": [3]},
                index=pandas.Index(["set1"], name="pathway"),
            )

    monkeypatch.setattr(enrich, "FGSEARes", fgseares)
    return calls


def test_fgsea_cli_ambiguous_statcol_is_usage_error(
    fake_fgsea, gmt_file, deseq2_result_csv, tmp_path, capsys
):
    from de_toolkit.enrich import main

    out = tmp_path / "out.csv"
    with pytest.raises(SystemExit) as e:
        main(["detk-enrich", "fgsea", "-o", str(out), gmt_file, deseq2_result_csv])
    assert e.value.code == 2
    # checked before fgsea (and R) runs
    assert fake_fgsea == []
    assert not out.exists()
    err = capsys.readouterr().err
    assert err.startswith("usage: detk-enrich fgsea")
    msg = [line for line in err.splitlines() if "error:" in line]
    assert len(msg) == 1
    assert "-c/--statcol" in msg[0]
    for col in DESEQ2_COLUMNS:
        assert col in msg[0]


def test_fgsea_cli_statcol_given_ranks_by_it(fake_fgsea, gmt_file, deseq2_result_csv, tmp_path):
    from de_toolkit.enrich import main

    main(
        [
            "detk-enrich",
            "fgsea",
            "--no-report",
            "-c",
            "condition__treated__stat",
            "-o",
            str(tmp_path / "out.csv"),
            gmt_file,
            deseq2_result_csv,
        ]
    )
    (stat,) = fake_fgsea
    assert stat.name == "condition__treated__stat"


def test_fgsea_cli_one_numeric_column_ranks_by_it(fake_fgsea, gmt_file, tmp_path):
    # the ID column, a text column and one numeric column: no -c needed
    from de_toolkit.enrich import main

    fn = tmp_path / "res.csv"
    fn.write_text("gene,symbol,score\ngene1,A,1.5\ngene2,B,-2\ngene3,C,0.5\n")
    main(
        ["detk-enrich", "fgsea", "--no-report", "-o", str(tmp_path / "out.csv"), gmt_file, str(fn)]
    )
    (stat,) = fake_fgsea
    assert stat.name == "score"
    assert stat.tolist() == [1.5, -2.0, 0.5]


def test_fgsea_cli_idcol_counts_as_not_a_ranking(fake_fgsea, gmt_file, tmp_path):
    # numeric columns are counted after -i: a numeric ID column is not one
    from de_toolkit.enrich import main

    fn = tmp_path / "res.csv"
    fn.write_text("score,entrez\n1.5,7\n-2,10\n")
    main(
        [
            "detk-enrich",
            "fgsea",
            "--no-report",
            "-i",
            "entrez",
            "-o",
            str(tmp_path / "out.csv"),
            gmt_file,
            str(fn),
        ]
    )
    (stat,) = fake_fgsea
    assert stat.name == "score"
    assert stat.index.tolist() == ["7", "10"]


@pytest.mark.parametrize("ascending", [False, True])
def test_fgsea_cli_params_record_ranking(
    fake_fgsea, gmt_file, deseq2_result_csv, tmp_path, ascending
):
    # the module JSON params name the resolved statistic and ID columns and
    # the direction (DETK-0600); -c and -i given as 0-based indexes
    import json
    from de_toolkit.enrich import main

    report = tmp_path / "report"
    main(
        [
            "detk-enrich",
            "fgsea",
            "-c",
            "9",
            "-i",
            "0",
            *(["-a"] if ascending else []),
            "--report-dir",
            str(report),
            "-o",
            str(tmp_path / "out.csv"),
            gmt_file,
            deseq2_result_csv,
        ]
    )
    (module,) = [json.loads(fn.read_text()) for fn in (report / "json").glob("*.json")]
    assert module["name"] == "fgseares"
    params = module["params"]
    assert params["statcol"] == "condition__treated__stat"
    assert params["idcol"] == "gene"
    assert params["ascending"] is ascending


def test_read_result_stat_ambiguous(deseq2_result_csv):
    from de_toolkit.common import UsageError
    from de_toolkit.enrich import read_result_stat

    with pytest.raises(UsageError, match="11 numeric columns"):
        read_result_stat(deseq2_result_csv)
    stat = read_result_stat(deseq2_result_csv, statcol="condition__treated__stat")
    assert stat.name == "condition__treated__stat"


def test_fgsea_crate_lists_results_file_as_input(
    fake_fgsea, gset_dict, deseq2_result_csv, tmp_path, monkeypatch
):
    # DETK-0720: the results file fgsea ranked is an input of its crate action
    # beside the GMT, so the enrichment links to the DE step that wrote it. In
    # 1.0.0 the action's object held gene_sets.gmt and the params only, though
    # argv names de.csv
    import json
    from de_toolkit.crate import CRATE_FILENAME
    from de_toolkit.enrich import main

    monkeypatch.chdir(tmp_path)
    with open("gene_sets.gmt", "w") as f:
        for name, ids in gset_dict.items():
            f.write("\t".join([name, name] + list(ids)) + "\n")
    argv = [
        "detk-enrich",
        "fgsea",
        "-c",
        "condition__treated__stat",
        "-o",
        "enrich.csv",
        "gene_sets.gmt",
        "de.csv",
    ]
    # the record's argv is the process's command line
    monkeypatch.setattr("sys.argv", argv)
    main(argv)
    report = tmp_path / "detk_report"
    (module,) = [json.loads(fn.read_text()) for fn in (report / "json").glob("*.json")]
    assert "de.csv" in module["argv"]
    # the primary input stays the GMT; every input is listed in in_file_paths
    assert module["in_file_path"] == "gene_sets.gmt"
    assert module["in_file_paths"] == ["gene_sets.gmt", "de.csv"]
    assert module["out_file_path"] == "enrich.csv"

    crate = json.loads((report / CRATE_FILENAME).read_text())
    graph = {e["@id"]: e for e in crate["@graph"]}
    (action,) = [e for e in graph.values() if e["@type"] == "CreateAction"]
    files = {o["@id"] for o in action["object"] if not o["@id"].startswith("#")}
    assert files == {"../gene_sets.gmt", "../de.csv"}
    assert graph["../de.csv"]["@type"] == "File"
    assert action["result"] == [{"@id": "../enrich.csv"}]
