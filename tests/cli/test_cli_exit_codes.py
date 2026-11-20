"""
The exit codes of DETK-0031, one failure per class: 0 on success, 2 on a
usage error (argparse's own, pinned for every invalid line in
test_cli_invalid, and the checks detk makes after parsing), 1 on any other
failure (a bad input file, a missing R or R package, a failing step). A
failure ends with one line on stderr, ``<command>: error: <cause>``; the
traceback comes before it only under --verbose.
"""

import re

import pytest

import cli_adapter
from cli_tables import COMMANDS
from de_toolkit import wrapr

COUNTS_CSV = "gene,s1,s2,s3,s4\ng1,10,20,30,40\ng2,5,0,15,25\ng3,100,90,80,70\n"
COV_CSV = "sample,group\ns1,a\ns2,a\ns3,b\ns4,b\n"


@pytest.fixture
def files(tmp_path, monkeypatch):
    (tmp_path / "counts.csv").write_text(COUNTS_CSV)
    (tmp_path / "cov.csv").write_text(COV_CSV)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def no_r(monkeypatch, tmp_path):
    "No Rscript on PATH"
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))


def last_line(outcome):
    lines = outcome.stderr.strip().splitlines()
    return lines[-1] if lines else ""


def assert_failure(outcome, prog, cause, code=1):
    "exit *code*, nothing on stdout, and the cause on stderr's last line"
    assert outcome.code == code, outcome.stderr
    assert outcome.stdout == ""
    line = last_line(outcome)
    assert line.startswith(f"{prog}: error: "), outcome.stderr
    assert re.search(cause, line), line


# ------------------------------------------------------------------ help
@pytest.mark.parametrize(
    "prog,sub",
    [pytest.param("detk", None, id="detk")]
    + [
        pytest.param(c.prog, s.name, id=c.prog + (f"-{s.name}" if s.name else ""))
        for c in COMMANDS
        for s in c.subcommands
    ]
    + [pytest.param(c.prog, None, id=c.prog) for c in COMMANDS if c.subcommands[0].name],
)
def test_help_states_the_exit_codes(prog, sub):
    outcome = cli_adapter.invoke((prog,) + ((sub,) if sub else ()) + ("--help",))
    assert outcome.code == 0
    section = outcome.stdout.split("\nexit codes:\n", 1)[1]
    for code, what in (("0", "success"), ("2", "usage error"), ("1", "any other failure")):
        assert re.search(rf"^  {code}  {what}", section, re.M), section


# --------------------------------------------------------------- success
def test_success_exits_0(files):
    outcome = cli_adapter.run(("detk-norm", "cpm", "-o", "out.csv", "--no-report", "counts.csv"))
    assert outcome.code == 0, outcome.stderr
    assert (files / "out.csv").exists()


# ------------------------------------------------- usage after parsing: 2
def test_design_without_counts_is_a_usage_error(files):
    # the design must name counts; detk checks it after parsing, before R
    outcome = cli_adapter.run(
        ("detk-de", "deseq2", "--no-report", "group ~ 1", "counts.csv", "cov.csv")
    )
    assert outcome.code == 2
    assert outcome.stdout == ""
    assert outcome.stderr.startswith("usage: detk-de deseq2 ")
    assert '"counts" must exist' in outcome.stderr
    assert "detk-de deseq2 --help" in outcome.stderr


@pytest.mark.parametrize(
    "argv,option",
    [
        (("detk-stats", "coldist", "--bins=many", "counts.csv"), "--bins"),
        (("detk-transform", "plog", "--pseudocount=x", "counts.csv"), "--pseudocount"),
        (("detk-de", "deseq2", "--cores=x", "counts ~ group", "counts.csv", "cov.csv"), "--cores"),
    ],
)
def test_a_number_option_that_is_not_a_number_is_a_usage_error(files, argv, option):
    outcome = cli_adapter.run(argv + ("--no-report",))
    assert outcome.code == 2
    assert outcome.stdout == ""
    assert re.search(rf"error: argument (-\w/)?{option}: invalid (int|float) value", outcome.stderr)


# ----------------------------------------------------------- failures: 1
def test_bad_input_file_exits_1_with_its_cause(files):
    outcome = cli_adapter.run(("detk-norm", "cpm", "--no-report", "missing.csv"))
    assert_failure(outcome, "detk-norm", r"missing\.csv")
    # no traceback without --verbose; the line says how to get it
    assert "Traceback" not in outcome.stderr
    assert "--verbose" in last_line(outcome)


def test_verbose_prints_the_traceback_before_the_cause(files):
    outcome = cli_adapter.run(("detk-norm", "cpm", "--no-report", "--verbose", "missing.csv"))
    assert_failure(outcome, "detk-norm", r"missing\.csv")
    assert "Traceback (most recent call last)" in outcome.stderr


def test_umbrella_passes_the_code_on(files):
    outcome = cli_adapter.run(("detk", "norm", "cpm", "--no-report", "missing.csv"))
    assert_failure(outcome, "detk-norm", r"missing\.csv")


def test_missing_r_exits_1_naming_rscript(files, no_r):
    outcome = cli_adapter.run(("detk-wrapr", "check"))
    assert_failure(outcome, "detk-wrapr", "Rscript")


def test_missing_r_for_a_step_exits_1_naming_rscript(files, no_r):
    outcome = cli_adapter.run(
        ("detk-de", "deseq2", "--no-report", "counts ~ group", "counts.csv", "cov.csv")
    )
    assert_failure(outcome, "detk-de", "Rscript")


def test_missing_r_package_exits_1_naming_it(files, monkeypatch):
    monkeypatch.setattr(wrapr, "check_r", lambda: True)
    monkeypatch.setattr(wrapr, "get_r_path", lambda: "/usr/bin/Rscript")
    monkeypatch.setattr(wrapr, "check_r_package", lambda pkg: False)
    outcome = cli_adapter.run(("detk-wrapr", "check"))
    assert_failure(outcome, "detk-wrapr", "jsonlite")


def test_failing_step_exits_1_with_its_cause(files):
    # tidy-covs needs every counts column among the column data rows
    (files / "cov.csv").write_text("sample,group\ns1,a\ns2,a\ns3,b\n")
    outcome = cli_adapter.run(("detk-util", "tidy-covs", "counts.csv", "cov.csv"))
    assert_failure(outcome, "detk-util", "tidy-covs requires")


@pytest.mark.skipif(not wrapr.check_r(), reason="R is not installed")
def test_failing_r_step_exits_1_with_its_cause(files):
    (files / "fail.R").write_text('stop("this script fails on purpose")\n')
    outcome = cli_adapter.run(("detk-wrapr", "run", "fail.R"))
    assert_failure(outcome, "detk-wrapr", "R")
