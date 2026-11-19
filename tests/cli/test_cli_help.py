"""
Help as DETK-0025 Option B promises it: every command and subcommand answers
-h and --help on stdout with exit 0, and states each positional and option
with its metavar, default and choices, and the common options, as the tables
give them. Wording and layout are free; the checks look only for the facts.
Section order and examples are pinned by release/cli-migrate, which adds
them.
"""

import re

import pytest

import cli_adapter
from cli_cases import options, prefix, subcommand_params
from cli_tables import COMMANDS, COMMON_HELP_ONLY


def flag_re(flag):
    "A flag as a whole word: --output, but not --column-data-output"
    return re.compile(rf"(?<![\w-]){re.escape(flag)}(?![\w-])")


def entry(text, opt):
    """
    The help entry for *opt*: the line listing it among the options (the
    first line that starts with a dash and names it) and the lines that
    continue its description, up to a blank line or the next dash.
    """
    lines = text.splitlines()
    pat = flag_re(opt.long)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("-") and pat.search(line):
            out = [line]
            for more in lines[i + 1 :]:
                s = more.strip()
                if not s or s.startswith("-") or s.endswith(":"):
                    break
                out.append(more)
            return "\n".join(out)
    raise AssertionError(f"{opt.long} is not listed in help:\n{text}")


def assert_help_ok(outcome, argv):
    assert outcome.code == 0, f"{' '.join(argv)}: exit {outcome.code}\n{outcome.stderr}"
    assert outcome.stderr == ""
    assert outcome.stdout.strip(), f"{' '.join(argv)} printed no help"


def help_text(argv):
    outcome = cli_adapter.invoke(argv)
    assert_help_ok(outcome, argv)
    return outcome.stdout


@pytest.mark.parametrize("flag", ["-h", "--help"])
@pytest.mark.parametrize("command,sub", subcommand_params())
def test_subcommand_help_exits_zero_on_stdout(command, sub, flag):
    argv = prefix(command, sub) + (flag,)
    help_text(argv)


@pytest.mark.parametrize("flag", ["-h", "--help"])
@pytest.mark.parametrize("command", [pytest.param(c, id=c.prog) for c in COMMANDS])
def test_command_help_lists_its_subcommands(command, flag):
    text = help_text((command.prog, flag))
    for sub in command.subcommands:
        if sub.name:
            assert flag_re(sub.name).search(text), f"{sub.name} not in {command.prog} help"


@pytest.mark.parametrize("command,sub", subcommand_params())
def test_subcommand_help_states_positionals(command, sub):
    text = help_text(prefix(command, sub) + ("--help",))
    for p in sub.positionals:
        assert re.search(rf"\b{re.escape(p.name)}\b", text), f"{p.name} not in help"


@pytest.mark.parametrize("command,sub", subcommand_params())
def test_subcommand_help_states_options(command, sub):
    text = help_text(prefix(command, sub) + ("--help",))
    for opt in options(sub) + COMMON_HELP_ONLY:
        e = entry(text, opt)
        if opt.short:
            assert flag_re(opt.short).search(e), f"{opt.short} not with {opt.long}:\n{e}"
        if opt.metavar:
            forms = "|".join(re.escape(f) for f in (opt.long, opt.short) if f)
            assert re.search(rf"(?:{forms})[ =]{re.escape(opt.metavar)}", e), (
                f"metavar {opt.metavar} not given for {opt.long}:\n{e}"
            )
        if opt.default is not None:
            assert opt.default in e, f"default {opt.default!r} not stated for {opt.long}:\n{e}"
        for choice in opt.choices:
            assert flag_re(choice).search(e), f"choice {choice!r} not stated for {opt.long}:\n{e}"
