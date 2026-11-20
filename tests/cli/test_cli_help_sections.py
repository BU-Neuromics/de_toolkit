"""
Help as DETK-0025 Option B promises it, beyond the facts test_cli_help
checks: for every command and subcommand, the sections in their order
(description, usage, positional arguments, options, common options,
examples); every positional and option with a one-line description and its
metavar in the one convention; and at least one example per subcommand,
which parses to that subcommand and, where the test data below allows,
runs.

A command still on docopt is skipped until release/cli-migrate s3
converts it.
"""

import re

import pytest

import cli_adapter
from cli_tables import COMMANDS

SECTIONS = ("usage:", "positional arguments:", "options:", "common options:", "examples:")

# option metavars (DETK-0025 gap 3): FILE for a file, DIR for a directory,
# N for a number, CHAR for a character
METAVARS = {"FILE", "DIR", "N", "CHAR"}

PROGS = ["detk"] + [c.prog for c in COMMANDS]

# the files an example may name, so it can be run
COUNTS_CSV = "gene,s1,s2,s3,s4\ng1,10,20,30,40\ng2,100,150,120,90\ng3,5,7,9,11\n"
EXAMPLE_DATA = {
    "counts.csv": COUNTS_CSV,
    "lengths.csv": "gene,length\ng1,1000\ng2,2500\ng3,800\n",
    "sample_info.csv": "sample,group\ns1,a\ns2,a\ns3,b\ns4,b\n",
}


def _parser_or_skip(prog):
    p = cli_adapter.parser(prog)
    if p is None:
        pytest.skip(f"{prog} is not on argparse yet (release/cli-migrate s3)")
    return p


def _help_params():
    "(prog, subcommand or None) for every command and subcommand"
    params = []
    for prog in PROGS:
        params.append(pytest.param(prog, None, id=prog))
        command = next((c for c in COMMANDS if c.prog == prog), None)
        for sub in command.subcommands if command else ():
            if sub.name:
                params.append(pytest.param(prog, sub.name, id=f"{prog}-{sub.name}"))
    return params


def _leaf_params():
    "(prog, subcommand or None) for every command line that runs something"
    return [
        pytest.param(c.prog, s.name, id=f"{c.prog}" + (f"-{s.name}" if s.name else ""))
        for c in COMMANDS
        for s in c.subcommands
    ]


def _parser(prog, sub):
    p = _parser_or_skip(prog)
    return cli_adapter.subparsers(p)[sub] if sub else p


def _help(prog, sub):
    argv = (prog,) + ((sub,) if sub else ()) + ("--help",)
    outcome = cli_adapter.invoke(argv)
    assert outcome.code == 0, outcome.stderr
    return outcome.stdout


@pytest.mark.parametrize("prog,sub", _help_params())
def test_help_sections_in_order(prog, sub):
    _parser_or_skip(prog)
    lines = _help(prog, sub).splitlines()
    # the description comes first, before the usage
    assert lines[0].strip() and not lines[0].startswith("usage:"), lines[0]
    found = [
        (i, h) for i, line in enumerate(lines) for h in SECTIONS if re.match(rf"{h}(\s|$)", line)
    ]
    headings = [h for _, h in found]
    assert headings == list(SECTIONS), f"sections are {headings}"


@pytest.mark.parametrize("prog,sub", _help_params())
def test_every_argument_has_a_one_line_description(prog, sub):
    p = _parser(prog, sub)
    for action in p._actions:
        if action.help == "==SUPPRESS==":
            continue
        name = "/".join(action.option_strings) or action.dest
        assert action.help and action.help.strip(), f"{name} has no description"
        assert "\n" not in action.help, f"{name}: the description is not one line"
        # the line each subcommand is listed with
        for listed in getattr(action, "_choices_actions", ()):
            assert listed.help and "\n" not in listed.help, f"{listed.dest}: no one-line help"


@pytest.mark.parametrize("prog,sub", _help_params())
def test_option_metavars_follow_the_convention(prog, sub):
    p = _parser(prog, sub)
    for action in p._actions:
        if action.option_strings and action.nargs != 0:
            assert action.metavar in METAVARS, (
                f"{'/'.join(action.option_strings)} has metavar {action.metavar!r}, "
                f"not one of {sorted(METAVARS)}"
            )


@pytest.mark.parametrize("prog,sub", _leaf_params())
def test_every_subcommand_has_an_example_that_parses(prog, sub):
    _parser_or_skip(prog)
    examples = cli_adapter.examples(prog, sub)
    assert examples, f"{prog} {sub or ''} has no example"
    for what, argv in examples:
        assert what.strip(), f"{argv}: the example does not say what it does"
        parsed = cli_adapter.parse(argv)
        assert parsed.module == prog.removeprefix("detk-")
        assert parsed.subcommand == sub


@pytest.mark.parametrize("prog", PROGS)
def test_command_help_examples_parse(prog):
    # the examples a command's own help lists (for a command with
    # subcommands, each subcommand's, and detk's own)
    _parser_or_skip(prog)
    for _, argv in cli_adapter.examples(prog):
        if argv[-1] in ("-h", "--help"):
            assert cli_adapter.invoke(argv).code == 0
        else:
            cli_adapter.parse(argv)


def _runnable(parsed):
    "Whether every file the example reads is in EXAMPLE_DATA"
    files = [v for k, v in parsed.args.items() if k.endswith("_fn") and v]
    return files and all(f in EXAMPLE_DATA for f in files)


@pytest.mark.parametrize("prog,sub", _leaf_params())
def test_examples_run_where_test_data_allows(prog, sub, tmp_path, monkeypatch):
    _parser_or_skip(prog)
    for name, text in EXAMPLE_DATA.items():
        (tmp_path / name).write_text(text)
    monkeypatch.chdir(tmp_path)
    ran = 0
    for _, argv in cli_adapter.examples(prog, sub):
        parsed = cli_adapter.parse(argv)
        if not _runnable(parsed):
            continue
        outcome = cli_adapter.run(argv)
        assert outcome.code == 0, f"{' '.join(argv)}:\n{outcome.stderr}"
        output = parsed.args.get("output")
        if output and output != "stdout":
            assert (tmp_path / output).exists(), f"{' '.join(argv)} wrote no {output}"
        ran += 1
    if not ran:
        pytest.skip("no example of this subcommand runs on the test data")
