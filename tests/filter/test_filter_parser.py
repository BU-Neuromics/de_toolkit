"""
The filter mini language's parser: built quietly (detk-filter writes nothing
on stderr when it succeeds), its grammar free of conflicts, and the
grouping of and / or without parentheses: and binds tighter than or, both
group to the left (DETK-0270).
"""

import os
import subprocess
import sys

import pytest

from de_toolkit.filter import (
    SHIFT_REDUCE_CONFLICTS,
    And,
    Group,
    Or,
    build_filter_parser,
    parse_filter_command,
)

BIN_DIR = os.path.dirname(sys.executable)


def test_grammar_conflicts_are_pinned():
    # the precedence table resolves the 4 conflicts between AND and OR the
    # bare grammar has; a grammar change that adds one fails here
    _, _, conflicts = build_filter_parser()
    assert conflicts == {"shift/reduce": SHIFT_REDUCE_CONFLICTS, "reduce/reduce": 0}
    assert SHIFT_REDUCE_CONFLICTS == 0


def test_building_the_parser_is_quiet(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    build_filter_parser()
    out, err = capsys.readouterr()
    assert (out, err) == ("", "")
    assert list(tmp_path.iterdir()) == []  # no parsetab.py, no parser.out


A, B, C = "mean(all) > 1", "mean(all) > 2", "mean(all) > 3"


def shape(expr):
    "The and/or tree of a parsed expression, its clauses named by their threshold"
    if isinstance(expr, (And, Or)):
        return (type(expr).__name__, shape(expr.a), shape(expr.b))
    if isinstance(expr, Group):
        return shape(expr.member)
    return int(expr.val)


# and binds tighter than or, both group to the left (DETK-0270);
# parentheses group as written
@pytest.mark.parametrize(
    "command, tree",
    [
        (f"{A} and {B} or {C}", ("Or", ("And", 1, 2), 3)),
        (f"{A} or {B} and {C}", ("Or", 1, ("And", 2, 3))),
        (f"{A} and {B} and {C}", ("And", ("And", 1, 2), 3)),
        (f"{A} or {B} or {C}", ("Or", ("Or", 1, 2), 3)),
        (f"{A} or {B} and {C} or {A}", ("Or", ("Or", 1, ("And", 2, 3)), 1)),
        (f"{A} and {B} or {C} and {A}", ("Or", ("And", 1, 2), ("And", 3, 1))),
        (f"{A} and ({B} or {C})", ("And", 1, ("Or", 2, 3))),
        (f"({A} and {B}) or {C}", ("Or", ("And", 1, 2), 3)),
        (f"({A} or {B}) and {C}", ("And", ("Or", 1, 2), 3)),
    ],
)
def test_and_or_grouping(command, tree):
    assert shape(parse_filter_command(command)) == tree


def test_detk_filter_writes_nothing_on_stderr(tmp_path):
    counts = tmp_path / "counts.csv"
    counts.write_text("gene,s1,s2,s3,s4\ng1,1,2,3,4\ng2,5,6,7,8\n")
    out = tmp_path / "out.csv"
    p = subprocess.run(
        [
            os.path.join(BIN_DIR, "detk-filter"),
            "--shut-up",
            "--no-report",
            "-o",
            str(out),
            "mean(all) > 3 and nonzero(all) > 0.5",
            str(counts),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert p.returncode == 0
    assert p.stderr == ""
    assert out.read_text().splitlines() == ["gene,s1,s2,s3,s4", "g2,5,6,7,8"]
    assert sorted(_.name for _ in tmp_path.iterdir()) == ["counts.csv", "out.csv"]


def test_detk_filter_logs_carry_no_parser_generator_output(tmp_path):
    # with logging on, stderr is detk's log lines only
    counts = tmp_path / "counts.csv"
    counts.write_text("gene,s1,s2,s3,s4\ng1,1,2,3,4\ng2,5,6,7,8\n")
    p = subprocess.run(
        [os.path.join(BIN_DIR, "detk-filter"), "--no-report", "mean(all) > 3", str(counts)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert p.returncode == 0
    for noise in ("LALR", "shift/reduce", "WARNING", "parsetab"):
        assert noise not in p.stderr


def test_and_binds_tighter_than_or_in_the_rows_kept():
    import pandas

    from de_toolkit.common import CountMatrix

    counts = pandas.DataFrame(
        [[1, 9], [100, 100], [0, 0]], index=["g1", "g2", "g3"], columns=["s1", "s2"]
    )
    mat = CountMatrix(counts)
    # g1 fails the mean, passes nonzero and max: kept by (A and B) or C,
    # where A and (B or C), the grouping before DETK-0270, dropped it
    command = "mean(all) > 50 and nonzero(all) > 1 or max(all) > 5"
    assert parse_filter_command(command)(mat) == {"g1", "g2"}
    assert parse_filter_command("mean(all) > 50 and (nonzero(all) > 1 or max(all) > 5)")(mat) == {
        "g2"
    }
