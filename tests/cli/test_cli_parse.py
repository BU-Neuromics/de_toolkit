"""
Each command line in the tables, run through its command's own entry point,
yields the arguments the table states: every positional, every option in its
short and long forms, every default and the common options.
"""

import pytest

import cli_adapter
from cli_cases import defaults, line_params, prefix


def assert_args(expected, parsed):
    for name, value in expected.items():
        assert name in parsed.args, f"{name} not parsed; got {sorted(parsed.args)}"
        assert cli_adapter.same_value(value, parsed.args[name]), (
            f"{name}: expected {value!r}, parsed {parsed.args[name]!r}"
        )
    # anything else the parser reports is an argument the subcommand does
    # not take, so it must be left unset
    extra = {k: v for k, v in parsed.args.items() if k not in expected and not cli_adapter.unset(v)}
    assert not extra, f"arguments not in the table were set: {extra}"


@pytest.mark.parametrize("command,sub,line", line_params())
def test_command_line_yields_arguments(command, sub, line):
    parsed = cli_adapter.parse(prefix(command, sub) + tuple(line.argv))
    assert parsed.module == command.module
    assert parsed.subcommand == sub.name
    assert_args(defaults(sub) | line.args, parsed)
