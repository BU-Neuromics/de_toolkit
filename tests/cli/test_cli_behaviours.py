"""
The parsing behaviours detk relies on today, each pinned by name, so that
the parser (docopt-ng until release/cli-migrate, argparse since) or closing a CLI gap
(release/cli-gaps, release/size-factors) changes one of these deliberately.
"""

import pytest

import cli_adapter
from cli_cases import options, prefix, required
from cli_tables import COMMANDS
from de_toolkit.version import __version__

DESEQ2 = ("detk-norm", "deseq2")


# ------------------------------------------------------------ option syntax
def test_long_option_unique_prefix_is_accepted():
    # --outp can only be --output, --rep only --report-dir
    parsed = cli_adapter.parse(DESEQ2 + ("--outp=out.csv", "--rep", "rep", "counts.csv"))
    assert parsed.args["output"] == "out.csv"
    assert parsed.args["report_dir"] == "rep"


def test_long_option_prefix_out_is_ambiguous_and_rejected():
    # --out is a prefix of both --output and the common --out-delim, so it is
    # not taken for --output
    outcome = cli_adapter.invoke(DESEQ2 + ("--out", "out.csv", "counts.csv"))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert "--out" in outcome.stderr


def test_long_option_value_after_equals_or_space():
    assert cli_adapter.parse(DESEQ2 + ("--output=a.csv", "c.csv")).args["output"] == "a.csv"
    assert cli_adapter.parse(DESEQ2 + ("--output", "a.csv", "c.csv")).args["output"] == "a.csv"


def test_short_option_value_attached_or_separate():
    assert cli_adapter.parse(DESEQ2 + ("-oa.csv", "c.csv")).args["output"] == "a.csv"
    assert cli_adapter.parse(DESEQ2 + ("-o", "a.csv", "c.csv")).args["output"] == "a.csv"


def test_options_may_follow_positionals():
    parsed = cli_adapter.parse(DESEQ2 + ("c.csv", "-o", "a.csv", "--no-report"))
    assert parsed.args["counts_fn"] == "c.csv"
    assert parsed.args["output"] == "a.csv"
    assert parsed.args["no_report"] is True


def test_subcommand_must_be_the_first_argument():
    # each main dispatches on argv[1], so an option before the subcommand
    # makes the command line unrecognised
    outcome = cli_adapter.invoke(("detk-norm", "-o", "a.csv", "deseq2", "c.csv"))
    assert outcome.parsed is None
    assert outcome.code != 0


def test_double_dash_is_not_an_end_of_options_marker():
    outcome = cli_adapter.invoke(DESEQ2 + ("--", "c.csv"))
    assert outcome.parsed is None
    assert outcome.code != 0


def test_single_value_option_given_twice_is_rejected():
    outcome = cli_adapter.invoke(DESEQ2 + ("-o", "a.csv", "-o", "b.csv", "c.csv"))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert "-o" in outcome.stderr


def test_flag_given_twice_is_rejected():
    outcome = cli_adapter.invoke(DESEQ2 + ("-v", "-v", "c.csv"))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert "-v" in outcome.stderr


def test_multi_valued_positional_collects_every_value():
    parsed = cli_adapter.parse(("detk-util", "gather", "a.sf", "b.sf", "c.sf"))
    assert parsed.args["files"] == ["a.sf", "b.sf", "c.sf"]


# ----------------------------------------------------------------- defaults
def _with_default():
    for c in COMMANDS:
        for s in c.subcommands:
            for o in options(s):
                if o.default is not None:
                    yield pytest.param(c, s, o, id=f"{c.prog}-{s.name or ''}{o.long}")


@pytest.mark.parametrize("command,sub,opt", list(_with_default()))
def test_documented_default_is_the_value_acted_on(command, sub, opt):
    # whatever states the default (docopt's "[default: ...]", argparse's
    # default=), the command acts on that value when the option is
    # not given, and help states it (test_cli_help)
    req, _ = required(sub)
    parsed = cli_adapter.parse(prefix(command, sub) + tuple(req))
    assert cli_adapter.same_value(opt.default, parsed.args[opt.key])


def test_de_cores_default_is_the_text_none():
    # "none" (not an absent value) is the default the de subcommands test for
    for sub in ("deseq2", "firth"):
        parsed = cli_adapter.parse(("detk-de", sub, "d", "c.csv", "v.csv"))
        assert parsed.args["cores"] == "none"


def test_option_without_documented_default_is_unset():
    parsed = cli_adapter.parse(DESEQ2 + ("c.csv",))
    assert parsed.args["size_factors"] is None
    # detk-outlier entropy states no default for -o, so without it nothing
    # names an output file
    parsed = cli_adapter.parse(("detk-outlier", "entropy", "c.csv"))
    assert parsed.args["output"] is None


# -------------------------------------------------------- help and version
def test_help_flag_after_other_arguments_prints_help():
    outcome = cli_adapter.invoke(DESEQ2 + ("c.csv", "-o", "a.csv", "-h"))
    assert outcome.code == 0
    assert outcome.parsed is None
    assert "counts_fn" in outcome.stdout


def _version_lines(prog):
    "Command lines where --version is an argument of its own"
    if prog == "detk":
        return [(prog, "--version")]
    command = next(c for c in COMMANDS if c.prog == prog)
    sub = command.subcommands[0]
    req, _ = required(sub)
    return [
        (prog, "--version"),
        prefix(command, sub) + ("--version",),
        prefix(command, sub) + tuple(req) + ("--version",),
    ]


@pytest.mark.parametrize("prog", [c.prog for c in COMMANDS] + ["detk"])
def test_version_as_an_argument_of_its_own_prints_the_version(prog):
    for argv in _version_lines(prog):
        outcome = cli_adapter.invoke(argv)
        assert outcome.code == 0, f"{argv}: {outcome.stderr}"
        assert outcome.parsed is None
        assert outcome.stdout.strip() == __version__


@pytest.mark.parametrize("prog", [c.prog for c in COMMANDS] + ["detk"])
def test_version_after_an_unknown_subcommand_is_not_honoured(prog):
    # DETK-0033 Option A: --version is honoured only as an argument of its
    # own, as argparse's version action reads it; the unknown subcommand
    # before it is the error. (docopt-ng printed the version.)
    if prog != "detk" and not cli_adapter.subparsers(cli_adapter.parser(prog)):
        pytest.skip(f"{prog} has no subcommands: 'anything' is its first positional")
    outcome = cli_adapter.invoke((prog, "anything", "--version", "else"))
    assert outcome.code != 0
    assert outcome.stdout == ""
    assert "anything" in outcome.stderr


def test_version_as_an_option_value_is_not_honoured():
    # DETK-0033 Option A: --version given where -o expects its value is not
    # the version option; argparse rejects -o without a value
    outcome = cli_adapter.invoke(DESEQ2 + ("-o", "--version", "c.csv"))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert __version__ not in outcome.stdout
    assert "-o" in outcome.stderr


# ------------------------------------------------- deprecated or inert options
COUNTS_CSV = "gene,s1,s2,s3,s4\ng1,10,20,30,40\ng2,100,150,120,90\ng3,5,7,9,11\n"
COV_CSV = "sample,group\ns1,a\ns2,a\ns3,b\ns4,b\n"


@pytest.fixture
def counts_dir(tmp_path, monkeypatch):
    (tmp_path / "counts.csv").write_text(COUNTS_CSV)
    (tmp_path / "cov.csv").write_text(COV_CSV)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(("detk-filter", "mean(all) > 10"), id="detk-filter"),
        pytest.param(("detk-stats", "summary"), id="detk-stats-summary"),
        pytest.param(("detk-stats", "pca"), id="detk-stats-pca"),
    ],
)
def test_column_data_is_accepted_with_a_deprecation_warning(counts_dir, argv):
    # each usage marks --column-data DEPRECATED in favour of the positional
    # <cov_fn>; DETK-0030 decides filter's for 1.0 (it names only filter)
    outcome = cli_adapter.run(
        argv + ("-o", "out.csv", "--no-report", "counts.csv", "--column-data=cov.csv")
    )
    assert outcome.code == 0, outcome.stderr
    assert (counts_dir / "out.csv").exists()
    assert "--column-data" in outcome.stderr
    assert "deprecated" in outcome.stderr.lower()


def test_norm_deseq2_size_factors_is_accepted_and_writes_nothing(counts_dir):
    # declared in help, never read (DETK-0029 decides its fate)
    outcome = cli_adapter.run(
        DESEQ2 + ("--size-factors=sf.tsv", "-o", "out.csv", "--no-report", "counts.csv")
    )
    assert outcome.code == 0, outcome.stderr
    assert (counts_dir / "out.csv").exists()
    assert not (counts_dir / "sf.tsv").exists()


# ------------------------------------------------ DETK-0033 (Option A) pins
def test_rlog_design_without_cov_fn_is_rejected():
    # rlog takes both or neither of <design> and <cov_fn>; docopt matched the
    # optional group partially and took a design without column data
    outcome = cli_adapter.invoke(("detk-transform", "rlog", "c.csv", "d"))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert "cov_fn" in outcome.stderr


def test_rlog_with_design_and_cov_fn_parses():
    parsed = cli_adapter.parse(("detk-transform", "rlog", "c.csv", "d", "v.csv"))
    assert (parsed.args["design"], parsed.args["cov_fn"]) == ("d", "v.csv")


def test_outlier_trim_is_not_a_subcommand():
    # the unreachable trim branch is removed, not exposed
    assert "trim" not in cli_adapter.subparsers(cli_adapter.parser("detk-outlier"))


@pytest.mark.parametrize(
    "argv,option",
    [
        (("detk-stats", "basestats", "-f", "bogus", "c.csv"), "--format"),
        (("detk-util", "gather", "--format=bogus", "a.sf"), "--format"),
        (("detk-util", "gather", "--on-mismatch=bogus", "a.sf"), "--on-mismatch"),
    ],
)
def test_value_outside_choices_is_a_parse_error(argv, option):
    outcome = cli_adapter.invoke(argv)
    assert outcome.parsed is None
    assert outcome.code == 2
    assert option in outcome.stderr
    assert "bogus" in outcome.stderr
