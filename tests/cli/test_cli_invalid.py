"""
Command lines each command rejects (unknown subcommand, unknown option,
missing positional, an option without its value, a value outside its
choices) end with a non-zero exit and name the offending argument on stderr.
The exit code itself is not pinned: DETK-0031 and release/cli-gaps set it.
"""

import pytest

import cli_adapter
from cli_cases import bad_params


@pytest.mark.parametrize("argv,bad", bad_params())
def test_invalid_command_line_exits_nonzero_naming_it(argv, bad):
    if bad.stage == "parse":
        outcome = cli_adapter.invoke(argv)
        assert outcome.parsed is None, f"{' '.join(argv)} parsed: {outcome.parsed}"
    else:
        outcome = cli_adapter.run(argv)
    assert outcome.code != 0
    assert outcome.stdout == ""
    for name in bad.names:
        assert name in outcome.stderr, f"{name!r} not on stderr:\n{outcome.stderr}"
