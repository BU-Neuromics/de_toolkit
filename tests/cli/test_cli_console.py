"""
The installed console scripts behave as the in-process entry points the
other tests in this directory call, so those tests pin what users run.
"""

import pytest

import cli_adapter
from cli_tables import COMMANDS


@pytest.fixture(scope="module", autouse=True)
def _installed():
    if not cli_adapter.console_script("detk").exists():
        pytest.skip("detk console scripts are not installed beside this interpreter")


PROGS = ["detk"] + [c.prog for c in COMMANDS]


@pytest.mark.parametrize("prog", PROGS)
def test_console_help_matches_entry_point(prog, tmp_path):
    console = cli_adapter.run_console((prog, "--help"), cwd=tmp_path)
    in_process = cli_adapter.invoke((prog, "--help"))
    assert console.code == in_process.code == 0
    assert console.stdout == in_process.stdout
    assert console.stderr == ""


@pytest.mark.parametrize("command", [pytest.param(c, id=c.prog) for c in COMMANDS])
def test_console_rejects_unknown_option_like_entry_point(command, tmp_path):
    sub = command.subcommands[0]
    argv = (command.prog,) + ((sub.name,) if sub.name else ()) + ("--bogus-option",)
    console = cli_adapter.run_console(argv, cwd=tmp_path)
    in_process = cli_adapter.invoke(argv)
    assert console.code == in_process.code == 2
    assert "--bogus-option" in console.stderr
    assert console.stdout == ""
