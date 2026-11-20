"""
The umbrella ``detk <module> ...`` command hands every module command on to
its own entry point, and its help lists them all. (Until release/cli-migrate
fixed DETK-0025 gap 1, it printed its usage for enrich and did nothing for
report and util.)
"""

import re

import pytest

import cli_adapter
from cli_cases import lines, prefix
from cli_tables import COMMANDS, UMBRELLA


def _subs():
    return [
        pytest.param(c, s, id=f"{c.prog}-{s.name or ''}") for c in COMMANDS for s in c.subcommands
    ]


def _umbrella(command, sub, rest=()):
    "``detk <module> [<subcommand>] ...``"
    return ("detk", command.module) + prefix(command, sub)[1:] + tuple(rest)


@pytest.mark.parametrize("command,sub", _subs())
def test_umbrella_dispatches_like_the_entry_point(command, sub):
    for _, line in lines(sub):
        direct = cli_adapter.parse(prefix(command, sub) + tuple(line.argv))
        via = cli_adapter.parse(_umbrella(command, sub, line.argv))
        assert via == direct


@pytest.mark.parametrize("command,sub", _subs())
def test_umbrella_passes_help_through(command, sub):
    direct = cli_adapter.invoke(prefix(command, sub) + ("--help",))
    via = cli_adapter.invoke(_umbrella(command, sub, ("--help",)))
    assert via.code == direct.code == 0
    assert via.stdout == direct.stdout


@pytest.mark.parametrize("argv", [("-h",), ("--help",), ("help",)])
def test_umbrella_help_lists_modules(argv):
    outcome = cli_adapter.invoke(("detk",) + argv)
    assert outcome.code == 0
    assert outcome.stderr == ""
    for module in UMBRELLA.help_lists:
        assert f"detk {module}" in outcome.stdout


@pytest.mark.parametrize("rest", UMBRELLA.rejects, ids=lambda r: " ".join(r) or "no-args")
def test_umbrella_rejects(rest):
    outcome = cli_adapter.invoke(("detk",) + tuple(rest))
    assert outcome.parsed is None
    assert outcome.code == 2
    assert outcome.stdout == ""
    for word in rest[:1]:
        assert word in outcome.stderr


def test_umbrella_help_lists_every_module_command():
    assert set(UMBRELLA.help_lists) == {c.module for c in COMMANDS}


# --------------------------------------------- detk completion (DETK-0032)
@pytest.mark.parametrize("shell", ["bash", "zsh", "tcsh"])
def test_completion_prints_the_shipped_script(shell):
    from de_toolkit.common import completion_script

    outcome = cli_adapter.invoke(("detk", "completion", shell))
    assert outcome.code == 0, outcome.stderr
    assert outcome.stdout == completion_script(shell)
    assert outcome.stderr == ""


@pytest.mark.parametrize(
    "rest,name",
    [
        (("completion",), "shell"),
        (("completion", "fish"), "fish"),
        (("completion", "bash", "zsh"), "zsh"),
        (("completion", "--bogus-option", "bash"), "--bogus-option"),
    ],
)
def test_completion_rejects(rest, name):
    outcome = cli_adapter.invoke(("detk",) + rest)
    assert outcome.code == 2
    assert outcome.stdout == ""
    assert outcome.stderr.startswith("usage: detk completion ")
    assert name in outcome.stderr


def test_completion_is_listed_in_detk_help():
    outcome = cli_adapter.invoke(("detk", "--help"))
    assert "detk completion <shell>" in outcome.stdout
    # listed with its line (Python 3.11 puts a long name's line under it)
    assert re.search(r"^ {4}completion\s+Print the shell completion", outcome.stdout, re.M)
