"""
The umbrella ``detk <module> ...`` command as it behaves today: it hands
most module commands on to their own entry point, prints its usage for
enrich, and for report and util parses its own usage, matches no branch and
exits 0 having done nothing. release/cli-migrate fixes enrich, report and
util; these pins change with it.
"""

import pytest

import cli_adapter
from cli_cases import lines, prefix
from cli_tables import COMMANDS, UMBRELLA


def _subs(kind):
    return [
        pytest.param(c, s, id=f"{c.prog}-{s.name or ''}")
        for c in COMMANDS
        if c.umbrella == kind
        for s in c.subcommands
    ]


def _umbrella(command, sub, rest=()):
    "``detk <module> [<subcommand>] ...``"
    return ("detk", command.module) + prefix(command, sub)[1:] + tuple(rest)


@pytest.mark.parametrize("command,sub", _subs("dispatches"))
def test_umbrella_dispatches_like_the_entry_point(command, sub):
    for _, line in lines(sub):
        direct = cli_adapter.parse(prefix(command, sub) + tuple(line.argv))
        via = cli_adapter.parse(_umbrella(command, sub, line.argv))
        assert via == direct


@pytest.mark.parametrize("command,sub", _subs("dispatches"))
def test_umbrella_passes_help_through(command, sub):
    direct = cli_adapter.invoke(prefix(command, sub) + ("--help",))
    via = cli_adapter.invoke(_umbrella(command, sub, ("--help",)))
    assert via.code == direct.code == 0
    assert via.stdout == direct.stdout


@pytest.mark.parametrize("command,sub", _subs("rejected"))
def test_umbrella_rejects_module(command, sub):
    _, line = next(lines(sub))
    outcome = cli_adapter.invoke(_umbrella(command, sub, line.argv))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert outcome.stdout == ""
    assert command.module in outcome.stderr


@pytest.mark.parametrize("command,sub", _subs("no-op"))
def test_umbrella_accepts_module_and_does_nothing(command, sub):
    _, line = next(lines(sub))
    outcome = cli_adapter.invoke(_umbrella(command, sub, line.argv))
    assert outcome.parsed is None
    assert outcome.code == 0
    assert outcome.stdout == ""


@pytest.mark.parametrize("argv", [("-h",), ("--help",), ("help",)])
def test_umbrella_help_lists_modules(argv):
    outcome = cli_adapter.invoke(("detk",) + argv)
    assert outcome.code == 0
    assert outcome.stderr == ""
    for module in UMBRELLA.help_lists:
        assert f"detk {module}" in outcome.stdout
    # enrich is not listed
    assert "enrich" not in outcome.stdout


@pytest.mark.parametrize("rest", UMBRELLA.rejects, ids=lambda r: " ".join(r) or "no-args")
def test_umbrella_rejects(rest):
    outcome = cli_adapter.invoke(("detk",) + tuple(rest))
    assert outcome.parsed is None
    assert outcome.code != 0
    assert outcome.stdout == ""
    for word in rest[:1]:
        assert word in outcome.stderr


def test_every_module_command_is_classified():
    assert {c.umbrella for c in COMMANDS} <= {"dispatches", "rejected", "no-op"}
