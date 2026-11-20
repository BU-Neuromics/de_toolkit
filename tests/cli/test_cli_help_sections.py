"""
Help as DETK-0025 Option B promises it, beyond the facts test_cli_help
checks: for every command and subcommand, the sections in their order
(description, usage, positional arguments, options, common options,
examples, exit codes); every positional and option with a one-line description and its
metavar in the one convention; and at least one example per subcommand,
which parses to that subcommand and, where the test data below allows,
runs.
"""

import re

import pytest

import cli_adapter
from de_toolkit import wrapr
from cli_tables import COMMANDS

SECTIONS = (
    "usage:",
    "positional arguments:",
    "options:",
    "common options:",
    "examples:",
    "exit codes:",
)
# every help has these; argparse leaves out a section with nothing in it, so
# a subcommand without positionals has no "positional arguments:"
REQUIRED = ("usage:", "options:", "examples:", "exit codes:")

# option metavars (DETK-0025 gap 3), one closed list across commands: FILE
# for a file, DIR for a directory, N for a number; and for values that are
# none of those, CHAR (a character), COL (a column, by name or 0-based
# index), COLS (comma-separated columns), FMT (a format name), REGEX (a
# regular expression), WHAT (one of the listed choices), BOOL (True or
# False), NAME (a name, such as a tool's) and TEXT (free text, such as a
# version). A new kind of value adds a word here and to the CHANGELOG.
METAVARS = {
    "FILE",
    "DIR",
    "N",
    "CHAR",
    "COL",
    "COLS",
    "FMT",
    "REGEX",
    "WHAT",
    "BOOL",
    "NAME",
    "TEXT",
}

PROGS = ["detk"] + [c.prog for c in COMMANDS]


# the files an example may name, so it can be run: 200 features in 6
# samples of two groups, deterministic (a linear congruential generator), with
# enough spread for DESeq2's dispersion fit
def _counts_csv(n_genes=200, samples=("s1", "s2", "s3", "s4", "s5", "s6")):
    x = 12345
    rows = ["gene," + ",".join(samples)]
    for g in range(n_genes):
        base = 5 + (g * 37) % 500
        vals = []
        for j, _ in enumerate(samples):
            x = (1103515245 * x + 12345) % 2**31
            effect = 3 if (g % 10 == 0 and j >= 3) else 1
            vals.append(str(int(base * effect * (0.6 + 0.8 * x / 2**31))))
        rows.append(f"g{g}," + ",".join(vals))
    return "\n".join(rows) + "\n"


EXAMPLE_DATA = {
    "counts.csv": _counts_csv(),
    "lengths.csv": "gene,length\n" + "".join(f"g{g},{500 + (g * 53) % 4000}\n" for g in range(200)),
    "sample_info.csv": "sample,group,age\ns1,a,31\ns2,a,45\ns3,a,52\ns4,b,38\ns5,b,61\ns6,b,47\n",
}

# subcommands whose examples run R; they run where R is installed (the CI
# test-r job)
NEEDS_R = {
    ("detk-de", "deseq2"),
    ("detk-de", "firth"),
    ("detk-enrich", "fgsea"),
    ("detk-transform", "vst"),
    ("detk-transform", "rlog"),
    ("detk-wrapr", "check"),
    ("detk-wrapr", "run"),
}


def _help_params():
    "(prog, subcommand or None) for every command and subcommand"
    # detk's own command with arguments (the module commands are the tables')
    params = [pytest.param("detk", "completion", id="detk-completion")]
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
    p = cli_adapter.parser(prog)
    return cli_adapter.subparsers(p)[sub] if sub else p


def _help(prog, sub):
    argv = (prog,) + ((sub,) if sub else ()) + ("--help",)
    outcome = cli_adapter.invoke(argv)
    assert outcome.code == 0, outcome.stderr
    return outcome.stdout


@pytest.mark.parametrize("prog,sub", _help_params())
def test_help_sections_in_order(prog, sub):
    lines = _help(prog, sub).splitlines()
    # the description comes first, before the usage
    assert lines[0].strip() and not lines[0].startswith("usage:"), lines[0]
    found = [
        (i, h) for i, line in enumerate(lines) for h in SECTIONS if re.match(rf"{h}(\s|$)", line)
    ]
    headings = [h for _, h in found]
    assert headings == [h for h in SECTIONS if h in headings], f"sections out of order: {headings}"
    assert len(set(headings)) == len(headings), f"a section is repeated: {headings}"
    for h in REQUIRED:
        assert h in headings, f"no {h!r} section: {headings}"


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
    for _, argv in cli_adapter.examples(prog):
        if argv[-1] in ("-h", "--help") or argv[0] == "detk":
            # detk's own commands (help, completion) run in detk itself,
            # which has no dispatch point to stop at
            assert cli_adapter.invoke(argv).code == 0
        else:
            cli_adapter.parse(argv)


def _runnable(parsed):
    "Whether every file the example reads is in EXAMPLE_DATA"
    files = [v for k, v in parsed.args.items() if k.endswith("_fn") and v]
    return files and all(f in EXAMPLE_DATA for f in files)


@pytest.mark.parametrize("prog,sub", _leaf_params())
def test_examples_run_where_test_data_allows(prog, sub, tmp_path, monkeypatch):
    if (prog, sub) in NEEDS_R and not wrapr.check_r():
        pytest.skip("this subcommand runs R, which is not installed")
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
