import numpy
import pandas
import pytest


@pytest.fixture
def model_data():
    N = 100
    df = pandas.DataFrame(
        {
            "cont": numpy.random.random(size=N),
            "binary_str": numpy.random.choice(["A", "B"], size=N),
            "binary_int": numpy.random.choice([0, 1], size=N),
            "cat_str": numpy.random.choice(list("ABCD"), size=N),
            "cat_int": numpy.random.choice([1, 2, 3, 4], size=N),
        }
    )
    return df


def test_to_formulaic(model_data):
    "detk formula syntax translates to formulaic's formula syntax."
    from de_toolkit.formula import to_formulaic, FormulaParseError

    def pltp(formula, **kwargs):
        return to_formulaic(formula, **kwargs).describe()

    assert pltp("A ~ B") == "A ~ B"
    assert pltp("A~B") == "A ~ B"
    assert pltp("A[one]~B[two]") == "C(A, Treatment('one')) ~ C(B, Treatment('two'))"
    assert pltp("A[one,two] ~ B") == "C(A, levels=['one', 'two']) ~ B"
    assert pltp("A[one,two] ~ B + C") == "C(A, levels=['one', 'two']) ~ B + C"
    assert (
        pltp("A[one,two] ~ B + C[case,control]")
        == "C(A, levels=['one', 'two']) ~ B + C(C, levels=['case', 'control'])"
    )
    # integer levels and references are passed as integers
    assert pltp("y ~ batch[2]") == "y ~ C(batch, Treatment(2))"
    assert pltp("y ~ batch[3,1,2]") == "y ~ C(batch, levels=[3, 1, 2])"
    with pytest.raises(FormulaParseError):
        pltp("B")
    with pytest.raises(FormulaParseError):
        pltp("A[one]~B[two]&C[three,four]")
    assert pltp("count ~ RIN + age_at_death") == "count ~ RIN + age_at_death"

    # : joins two terms, each translated on its own
    assert pltp("y ~ a:b") == "y ~ a : b"
    assert pltp("y ~ a[ref]:b") == "y ~ C(a, Treatment('ref')) : b"

    # names formulaic would not read as names are quoted with backticks
    assert pltp("fld.y ~ fld.a:b(c)") == "`fld.y` ~ `fld.a` : `b(c)`"
    assert pltp("fld.y ~ fld.a[x]") == "`fld.y` ~ C(`fld.a`, Treatment('x'))"
    assert pltp("np.log(x) ~ category[cont]") == "`np.log(x)` ~ C(category, Treatment('cont'))"
    assert (
        pltp("1 + np.log(x) ~ 1 + category[cont]")
        == "1 + `np.log(x)` ~ 1 + C(category, Treatment('cont'))"
    )
    assert (
        pltp("np.log(x) ~ -1 + category[cont]")
        == "`np.log(x)` ~ -1 + C(category, Treatment('cont'))"
    )

    # the levels of a boolean column are read as booleans, in any case
    assert pltp("y ~ flag[FALSE]", bool_columns=["flag"]) == "y ~ C(flag, Treatment(False))"
    assert pltp("y ~ flag[true,false]", bool_columns=["flag"]) == (
        "y ~ C(flag, levels=[True, False])"
    )
    assert pltp("y ~ flag[FALSE]") == "y ~ C(flag, Treatment('FALSE'))"

    # the name map takes each translated term back to its column name
    model = to_formulaic("fld.y ~ a[one] + b[x,y] + c")
    assert model.name_map == {
        "`fld.y`": "fld.y",
        "C(a, Treatment('one'))": "a",
        "C(b, levels=['x', 'y'])": "b",
        "c": "c",
    }
    assert model.levels == {"b": ["x", "y"]}


def test_DesignMatrix(model_data):

    from de_toolkit.formula import DesignMatrix, ModelError

    dm = DesignMatrix("cont ~ binary_str[B] + binary_int + cat_int", model_data)
    assert dm.design == "cont ~ Intercept + binary_str__A + binary_int + cat_int"
    assert dm.full_matrix.shape == (100, 5)
    assert (dm.full_matrix["cont"] == model_data["cont"]).all()
    assert (dm.full_matrix["binary_int"] == model_data["binary_int"]).all()
    assert (dm.full_matrix["cat_int"] == model_data["cat_int"]).all()

    # augmented designs are good for adding counts to things
    counts = pandas.DataFrame({"counts": model_data["cont"]})
    aug_dm = dm.augment_rhs(counts)
    assert all(aug_dm.full_matrix["counts"] == counts["counts"])

    counts = pandas.DataFrame({"other_counts": model_data["cont"]})
    aug_dm = aug_dm.augment_lhs(counts)
    assert all(aug_dm.full_matrix["other_counts"] == counts["other_counts"])

    aug_dm.update_design("counts", 1)
    assert all(aug_dm.full_matrix["counts"] == 1)

    with pytest.raises(ModelError):
        aug_dm.update_design("oogabooga", 1)

    with pytest.raises(ModelError):
        dm.drop_from_lhs("oogabooga")

    with pytest.raises(ModelError):
        dm.drop_from_rhs("oogabooga")

    # binary_str[A] is excluded on left
    dm = DesignMatrix("binary_str[B] ~ cont", model_data)
    assert dm.design == "binary_str__A ~ Intercept + cont"

    # binary_str[A] is excluded on left, binary_int stays as is (not categorical)
    dm = DesignMatrix("binary_str[B] ~ cont + binary_int", model_data)
    assert dm.design == "binary_str__A ~ Intercept + cont + binary_int"
    assert "binary_int" in dm.rhs

    # cat_str[A] is missing from right
    dm = DesignMatrix("binary_str[B] ~ cont + cat_str[A]", model_data)
    assert dm.design == "binary_str__A ~ Intercept + cont + cat_str__B + cat_str__C + cat_str__D"
    assert "cat_str__A" not in dm.rhs

    # cat_str[B] is missing from right
    dm = DesignMatrix("binary_str[B] ~ cont + cat_str[B,C,D,A]", model_data)
    assert dm.design == "binary_str__A ~ Intercept + cont + cat_str__C + cat_str__D + cat_str__A"
    assert "cat_str__B" not in dm.rhs

    # cat_str[A] is missing from right
    dm = DesignMatrix("binary_str[A] ~ cont + cat_str[B,C,D,A]", model_data)
    assert dm.design == "binary_str__B ~ Intercept + cont + cat_str__C + cat_str__D + cat_str__A"
    assert "cat_str__A" not in dm.lhs

    # cat_str[A] is missing from right implicitly (no ref group set)
    dm = DesignMatrix("binary_str ~ cont + cat_str", model_data)
    assert dm.design == "binary_str__B ~ Intercept + cont + cat_str__B + cat_str__C + cat_str__D"
    assert "cat_str__A" not in dm.lhs

    # binary_str[A] and cat_str[A] missing from right implicitly
    dm = DesignMatrix("cont ~ binary_str + cat_str", model_data)
    assert dm.design == "cont ~ Intercept + binary_str__B + cat_str__B + cat_str__C + cat_str__D"
    assert "binary_str__A" not in dm.rhs
    assert "cat_str__A" not in dm.rhs


def test_DesignMatrix_colnames(model_data):

    from de_toolkit.formula import DesignMatrix, FormulaParseError

    dm = DesignMatrix("cont ~ cont + binary_str", model_data)
    assert dm.design == "cont ~ Intercept + cont + binary_str__B"

    # add . to column names
    model_data.columns = [f"fld.{_}" for _ in model_data.columns]

    dm = DesignMatrix("fld.cont ~ fld.cat_int", model_data)
    assert dm.design == "fld.cont ~ Intercept + fld.cat_int"

    dm = DesignMatrix("fld.cont ~ fld.cat_int[4]", model_data)
    assert dm.design == "fld.cont ~ Intercept + fld.cat_int__1 + fld.cat_int__2 + fld.cat_int__3"

    dm = DesignMatrix("fld.cont ~ fld.cat_int[4,1,2,3]", model_data)
    assert dm.design == "fld.cont ~ Intercept + fld.cat_int__1 + fld.cat_int__2 + fld.cat_int__3"

    with pytest.raises(FormulaParseError):
        dm = DesignMatrix("fld.cont ~ fld.cat_int[4,1,2,3] + fld.]lsaj", model_data)


@pytest.mark.parametrize(
    "formula, call",
    [
        ("cont ~ np.log(cont)", "np.log(cont)"),
        ("cont ~ log2(cont) + binary_str", "log2(cont)"),
        ("np.log(cont) ~ binary_str", "np.log(cont)"),
        ("cont ~ binary_str[A] * log2(cat_int)", "log2(cat_int)"),
    ],
)
def test_DesignMatrix_call_is_an_error(model_data, formula, call):
    "Formulas take column names only: a call is an error (DETK-0050)."
    from de_toolkit.formula import DesignMatrix, FormulaParseError

    with pytest.raises(FormulaParseError) as e:
        DesignMatrix(formula, model_data)
    message = str(e.value)
    assert "column names only" in message
    assert call in message
    assert "column data file" in message


def test_DesignMatrix_column_named_like_a_call(model_data):
    "A column whose name looks like a call is a column."
    from de_toolkit.formula import DesignMatrix

    model_data["log2(cont)"] = model_data["cont"]
    model_data["np.log(x)"] = model_data["cat_str"]
    dm = DesignMatrix("cont ~ log2(cont) + np.log(x)[A]", model_data)
    assert list(dm.rhs.columns) == [
        "Intercept",
        "log2(cont)",
        "np.log(x)__B",
        "np.log(x)__C",
        "np.log(x)__D",
    ]
    assert (dm.rhs["log2(cont)"] == model_data["cont"]).all()
