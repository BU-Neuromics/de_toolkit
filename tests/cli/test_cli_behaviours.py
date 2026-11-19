"""
The parsing behaviours detk relies on today, each pinned by name, so that
replacing docopt-ng (release/cli-migrate) or closing a CLI gap
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
    # docopt reads each default from the "[default: ...]" in the usage text;
    # whatever states it, the command acts on that value when the option is
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


@pytest.mark.parametrize("prog", [c.prog for c in COMMANDS] + ["detk"])
def test_version_anywhere_prints_the_version(prog):
    # --version is answered before the command line is parsed
    for argv in ((prog, "--version"), (prog, "anything", "--version", "else")):
        outcome = cli_adapter.invoke(argv)
        assert outcome.code == 0
        assert outcome.parsed is None
        assert outcome.stdout.strip() == __version__


# ------------------------------------------------- deprecated or inert options
COUNTS_CSV = "gene,s1,s2,s3,s4\ng1,10,20,30,40\ng2,100,150,120,90\ng3,5,7,9,11\n"
COV_CSV = "sample,group\ns1,a\ns2,a\ns3,b\ns4,b\n"


@pytest.fixture
def counts_dir(tmp_path, monkeypatch):
    (tmp_path / "counts.csv").write_text(COUNTS_CSV)
    (tmp_path / "cov.csv").write_text(COV_CSV)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_filter_column_data_is_accepted_with_a_deprecation_warning(counts_dir):
    outcome = cli_adapter.run(
        (
            "detk-filter",
            "-o",
            "out.csv",
            "--no-report",
            "mean(all) > 10",
            "counts.csv",
            "--column-data=cov.csv",
        )
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


# ------------------------------------------------- open questions (DETK-0033)
@pytest.mark.skip(
    reason="DETK-0033: rlog [<design> <cov_fn>] accepts a design without cov_fn "
    "(docopt matches the optional group partially); pinned or rejected on Adam's answer"
)
def test_rlog_design_without_cov_fn():
    parsed = cli_adapter.parse(("detk-transform", "rlog", "c.csv", "d"))
    assert parsed.args["design"] == "d"
    assert parsed.args["cov_fn"] is None
