"""
The design reaches R's formula() with its names quoted (DETK-0050): a column
data column named like a call is read as a column name and never run.

The call-shaped column is ``file.create(1)``: if R ran it, it would create a
file named ``1`` in the working directory, which these tests set to a fresh
temporary directory and check stays empty of it.
"""

import logging
import re

import numpy
import pandas
import pytest

from de_toolkit.common import CountMatrix
from de_toolkit.de import main as de_main
from de_toolkit.formula import r_design, r_name
from de_toolkit.wrapr import RExecutionError, check_r_package

deseq2_test = pytest.mark.skipif(
    not check_r_package("DESeq2"), reason="DESeq2 package not installed, skipping test"
)
logistf_test = pytest.mark.skipif(
    not check_r_package("logistf"), reason="logistf package not installed, skipping test"
)

CALL = "file.create(1)"


# the R-bound form of a name and a design


@pytest.mark.parametrize(
    "name,quoted",
    [
        ("group", "group"),
        ("fld.cont", "fld.cont"),
        ("category__case", "category__case"),
        (".hidden", ".hidden"),
        (".", "."),
        ("x1_y.z", "x1_y.z"),
        ("print(1)", "`print(1)`"),
        ('system("true")', '`system("true")`'),
        ("file.create(1)", "`file.create(1)`"),
        ("age(yrs)", "`age(yrs)`"),
        ("_x", "`_x`"),
        ("1x", "`1x`"),
        (".2x", "`.2x`"),
        ("a-b", "`a-b`"),
        ("a b", "`a b`"),
        ("cat[T.a-b]", "`cat[T.a-b]`"),
        ("if", "`if`"),
        ("TRUE", "`TRUE`"),
        ("NA_real_", "`NA_real_`"),
        ("...", "`...`"),
        ("..1", "`..1`"),
        ("a`b", r"`a\`b`"),
        ("a\\`b", r"`a\\\`b`"),
        ("é", "`é`"),
    ],
)
def test_r_name(name, quoted):
    assert r_name(name) == quoted


@pytest.mark.parametrize(
    "design,quoted",
    [
        ("counts ~ group__b", "counts ~ group__b"),
        ("counts ~ fld.cont + category__case", "counts ~ fld.cont + category__case"),
        ("counts ~ 1", "counts ~ 1"),
        (" ~ 1", "~ 1"),
        ("~ 1", "~ 1"),
        ("~ group__b", "~ group__b"),
        ("counts ~ print(1)", "counts ~ `print(1)`"),
        ("print(1) ~ counts", "`print(1)` ~ counts"),
        (
            "counts ~ a__x + age(yrs) + a__x:age(yrs)",
            "counts ~ a__x + `age(yrs)` + a__x:`age(yrs)`",
        ),
        ("counts ~ if + system(x)", "counts ~ `if` + `system(x)`"),
        # a number-shaped name is a column, not a constant; only the
        # intercept 1 detk writes for a trivial model is left bare
        ("counts ~ Intercept + 2.5", "counts ~ Intercept + `2.5`"),
        ("1.0 ~ Intercept + counts", "`1.0` ~ Intercept + counts"),
        ("counts ~ 0.5 + 1. + 10.25", "counts ~ `0.5` + `1.` + `10.25`"),
        ("counts ~ a__x:2.5", "counts ~ a__x:`2.5`"),
    ],
)
def test_r_design(design, quoted):
    assert r_design(design) == quoted


def test_r_design_of_resolved_design():
    "The resolved design is recorded unquoted; its R-bound form is quoted."
    counts = pandas.DataFrame(
        numpy.arange(1, 25).reshape(6, 4), columns=[f"s{_}" for _ in range(4)]
    )
    column_data = pandas.DataFrame(
        {CALL: [0.1, 0.5, 0.2, 0.9], "fld.cont": [1.0, 2.0, 3.0, 4.0]}, index=counts.columns
    )
    cm = CountMatrix(counts, column_data, f"counts ~ fld.cont + {CALL}")
    assert cm.design == f"counts ~ Intercept + fld.cont + {CALL}"
    assert r_design(cm.design) == f"counts ~ Intercept + fld.cont + `{CALL}`"


def test_r_design_of_resolved_number_shaped_design():
    "A column named 2.5 is resolved as a column and quoted for R."
    counts = pandas.DataFrame(
        numpy.arange(1, 25).reshape(6, 4), columns=[f"s{_}" for _ in range(4)]
    )
    column_data = pandas.DataFrame(
        {"2.5": [0.1, 0.5, 0.2, 0.9], "1.0": [0, 1, 0, 1]}, index=counts.columns
    )
    cm = CountMatrix(counts, column_data, "counts ~ 2.5")
    assert cm.design == "counts ~ Intercept + 2.5"
    assert r_design(cm.design) == "counts ~ Intercept + `2.5`"
    cm = CountMatrix(counts, column_data, "1.0 ~ counts + 2.5")
    assert cm.design == "1.0 ~ Intercept + counts + 2.5"
    assert r_design(cm.design) == "`1.0` ~ Intercept + counts + `2.5`"


# R: the call-shaped column is a column name, and no code runs


@pytest.fixture
def r_data(tmp_path, monkeypatch):
    """
    Counts and column data in *tmp_path*, the working directory: a two group
    design with the group as ``file.create(1)`` and ``2.5``, and ``fld.cont``.
    """
    rng = numpy.random.default_rng(0)
    n = 10
    samples = [f"s{_}" for _ in range(n)]
    group = [0] * (n // 2) + [1] * (n - n // 2)
    counts = pandas.DataFrame(
        rng.negative_binomial(5, 5 / 105, size=(20, n)),
        index=[f"gene{_}" for _ in range(20)],
        columns=samples,
    )
    column_data = pandas.DataFrame(
        {CALL: group, "fld.cont": numpy.linspace(0, 1, n), "2.5": group},
        index=pandas.Index(samples),
    )
    counts_fn = tmp_path / "counts.csv"
    column_data_fn = tmp_path / "column_data.csv"
    counts.to_csv(counts_fn)
    column_data.to_csv(column_data_fn)
    monkeypatch.chdir(tmp_path)
    return tmp_path, str(counts_fn), str(column_data_fn)


# R looked for a column of that name: DESeq2 makes its column data names
# syntactic (file.create.1.), so it finds none and stops, having run nothing
NOT_FOUND = re.compile(r"object 'file\.create\(1\)' not found")


def read_count_matrix(counts_fn, column_data_fn, design):
    return CountMatrix(
        pandas.read_csv(counts_fn, index_col=0),
        pandas.read_csv(column_data_fn, index_col=0),
        design,
    )


def assert_not_run(tmp_path):
    assert not (tmp_path / "1").exists(), f"R ran the column name {CALL} as code"


@deseq2_test
def test_deseq2_call_shaped_column(r_data, caplog):
    tmp_path, counts_fn, column_data_fn = r_data
    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit):
        de_main(
            ["detk-de", "deseq2", f"counts ~ {CALL}", counts_fn, column_data_fn, "-o", "out.csv"]
        )
    assert NOT_FOUND.search(caplog.text)
    assert_not_run(tmp_path)


@deseq2_test
def test_deseq2_dotted_column(r_data):
    "A dotted name (issue #34's fld.cont) is syntactic, unquoted, and works."
    tmp_path, counts_fn, column_data_fn = r_data
    de_main(["detk-de", "deseq2", "counts ~ fld.cont", counts_fn, column_data_fn, "-o", "out.csv"])
    res = pandas.read_csv(tmp_path / "out.csv", index_col=0)
    assert "fld.cont__log2FoldChange" in res.columns
    assert len(res) == 20


@logistf_test
def test_firth_call_shaped_column(r_data):
    "logistf keeps the column names, so the call-shaped outcome is fitted."
    tmp_path, counts_fn, column_data_fn = r_data
    de_main(["detk-de", "firth", f"{CALL} ~ counts", counts_fn, column_data_fn, "-o", "out.csv"])
    assert_not_run(tmp_path)
    res = pandas.read_csv(tmp_path / "out.csv", index_col=0)
    assert "counts__beta" in res.columns
    assert len(res) == 20


@logistf_test
def test_firth_number_shaped_column(r_data):
    "A column named 2.5 is fitted as the outcome, not read as the constant 2.5."
    tmp_path, counts_fn, column_data_fn = r_data
    de_main(["detk-de", "firth", "2.5 ~ counts", counts_fn, column_data_fn, "-o", "out.csv"])
    res = pandas.read_csv(tmp_path / "out.csv", index_col=0)
    assert "counts__beta" in res.columns
    assert len(res) == 20
    assert (res["status"] == "OK").all()


@deseq2_test
def test_rlog_call_shaped_column(r_data):
    tmp_path, counts_fn, column_data_fn = r_data
    from de_toolkit.transform import rlog

    cm = read_count_matrix(counts_fn, column_data_fn, f"counts ~ {CALL}")
    with pytest.raises(RExecutionError, match=NOT_FOUND):
        rlog(cm, blind=False)
    assert_not_run(tmp_path)


@deseq2_test
def test_norm_deseq2_wrapr_call_shaped_column(r_data):
    "deseq2_wrapr, the R-backed DESeq2 normalization, passes a design."
    from de_toolkit.norm import deseq2_wrapr

    tmp_path, counts_fn, column_data_fn = r_data
    cm = read_count_matrix(counts_fn, column_data_fn, f"counts ~ {CALL}")
    with pytest.raises(RExecutionError, match=NOT_FOUND):
        deseq2_wrapr(cm)
    assert_not_run(tmp_path)
