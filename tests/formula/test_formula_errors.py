"""
Design formulas never lose a term silently, and their errors read as plain
messages (release/parse-errors).

DETK-0190 Option A: a term that looks like a number, other than the
intercept numbers 0 and 1, is an error naming it, on either side of ~; the
message says to rename the column when the column data has one by that
name. Every error formula.py raises for a formula formulaic rejects is one
plain line naming the offending term: no tuple text, no ANSI colour codes.
"""

import pandas
import pytest

from de_toolkit.common import CountMatrix, InvalidDesignException
from de_toolkit.formula import DesignMatrix, FormulaParseError

NUMBERS = ("3", "2.5", "-2.5")


def data(numbered=True):
    "Column data with columns c and x, and with *numbered* the columns 3, 2.5 and -2.5"
    d = pandas.DataFrame(
        {"c": ["a", "b", "a", "b"], "x": [1.0, 2.0, 4.0, 3.0], "counts": 0.0},
        index=["s1", "s2", "s3", "s4"],
    )
    if numbered:
        for i, n in enumerate(NUMBERS):
            d[n] = [1.0 + i, 2.0, 3.0, 5.0 - i]
    return d


def message(formula, d):
    with pytest.raises(FormulaParseError) as e:
        DesignMatrix(formula, d)
    return str(e.value)


def assert_plain(msg):
    "One line, with no ANSI escape codes, formulaic's markers or tuple text"
    assert "\n" not in msg
    assert "\x1b" not in msg
    assert "⧛" not in msg and "⧚" not in msg
    assert "('" not in msg and "',)" not in msg


# --------------------------------------------------------- number-like terms
@pytest.mark.parametrize("number", NUMBERS)
@pytest.mark.parametrize("side", ["rhs", "lhs"])
def test_number_like_column_is_an_error_saying_to_rename_it(number, side):
    formula = f"counts ~ {number}" if side == "rhs" else f"{number} ~ c"
    msg = message(formula, data())
    assert msg.startswith(f"{number} in the design looks like a number")
    assert f"rename the column '{number}' of the column data file" in msg
    assert "letter or underscore" in msg
    assert_plain(msg)


@pytest.mark.parametrize("number", NUMBERS)
@pytest.mark.parametrize("side", ["rhs", "lhs"])
def test_number_without_a_column_is_an_error_naming_it(number, side):
    formula = f"counts ~ x + {number}" if side == "rhs" else f"{number} ~ c"
    msg = message(formula, data(numbered=False))
    assert msg.startswith(f"{number} in the design is a number, and formulas take column names")
    assert "rename" not in msg
    assert_plain(msg)


@pytest.mark.parametrize(
    "formula, number",
    [
        # the - of -2.5 is not read as removing a term: nothing is lost silently
        ("counts ~ x + -2.5", "-2.5"),
        ("counts ~ x - 2.5", "2.5"),
        ("counts ~ x * 2", "2"),
        ("counts ~ 1.0", "1.0"),
        ("counts ~ 2.5[a]", "2.5"),
    ],
)
def test_other_number_forms_are_errors(formula, number):
    msg = message(formula, data())
    assert msg.startswith(f"{number} in the design")
    assert_plain(msg)


def test_intercept_number_given_a_level_is_an_error():
    msg = message("counts ~ 1[a]", data())
    assert msg == "1[a] in the design is not a column name: 1 is the intercept"


@pytest.mark.parametrize(
    "formula, design",
    [
        ("counts ~ 1", "counts ~ Intercept"),
        ("counts ~ 0 + x", "counts ~ x"),
        ("counts ~ -1 + x", "counts ~ x"),
        ("counts ~ x - 1", "counts ~ x"),
        ("counts ~ 1 + x", "counts ~ Intercept + x"),
        ("x ~ 0 + c", "x ~ c__a + c__b"),
    ],
)
def test_zero_and_one_keep_their_intercept_meaning(formula, design):
    assert DesignMatrix(formula, data()).design == design


# ------------------------------------------- the messages of each error path
@pytest.mark.parametrize(
    "formula, expected",
    [
        # an unknown column, either side: checked before formulaic
        (
            "counts ~ nope",
            "nope in the design is not a column of the column data file (its columns: c, x)",
        ),
        (
            "nope ~ c",
            "nope in the design is not a column of the column data file (its columns: c, x)",
        ),
        # a misspelled term
        (
            "counts ~ cc + x",
            "cc in the design is not a column of the column data file (its columns: c, x)",
        ),
        # a reference level the column does not have
        (
            "counts ~ c[Z]",
            "c[Z] in the design names the reference level 'Z', which c does not have "
            "(its values: a, b)",
        ),
        # a value of the column outside its level list
        (
            "counts ~ c[a]:x + c[a,Z]",
            "c has the level(s) 'b', which are not among the levels the design gives it: 'a', 'Z'",
        ),
        # a character outside detk formula syntax: the lexer
        ("counts ~ c&x", "illegal character '&' in the design"),
        # a formula formulaic cannot parse: its message, plain, with the part it marks
        (
            "counts ~ x +",
            "could not read the design 'counts ~ x +': Operator `+` has insuffient "
            "arguments and/or is misplaced. (at '+')",
        ),
        (
            "counts ~ ~ x",
            "could not read the design 'counts ~ ~ x': Operator `~` is incorrectly used. "
            "(at '~ ~')",
        ),
    ],
)
def test_error_message_is_plain_and_names_the_term(formula, expected):
    msg = message(formula, data(numbered=False))
    assert msg == expected
    assert_plain(msg)


def test_count_matrix_message_is_one_plain_line():
    "CountMatrix, which the commands build, passes the message on as one line."
    d = data(numbered=False).drop(columns="counts")
    counts = pandas.DataFrame(1.0, index=["g1"], columns=d.index)
    with pytest.raises(InvalidDesignException) as e:
        CountMatrix(counts, d, "counts ~ x + -2.5")
    msg = str(e.value)
    assert msg.endswith(
        "-2.5 in the design is a number, and formulas take column names; "
        "only 0 and 1 have a meaning, the intercept (counts ~ 0 + x, counts ~ 1)"
    )
    assert_plain(msg)
