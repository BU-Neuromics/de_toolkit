"""
The shipped shell completion scripts (DETK-0032): generated from the parsers
by shtab, current with them, covering every detk command and subcommand,
and printed by ``detk completion <shell>`` without shtab installed.
"""

import argparse
import re
import shutil
import subprocess
import sys

import pytest

from de_toolkit.common import COMPLETION_SHELLS, MODULE_COMMANDS, completion_script
from de_toolkit.completions import _generate

ENTRY_POINTS = [f"detk-{cmd}" for cmd in MODULE_COMMANDS]


def _subcommands(parser):
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return list(action.choices)
    return []


def _commands():
    "(prog, [subcommands]) for every entry point and detk itself"
    out = [("detk", list(MODULE_COMMANDS) + ["completion"])]
    for cmd in MODULE_COMMANDS:
        out.append((f"detk-{cmd}", _subcommands(_generate.module_parser(cmd))))
    return out


@pytest.mark.parametrize("shell", COMPLETION_SHELLS)
def test_shipped_script_is_current(shell):
    pytest.importorskip("shtab")
    assert completion_script(shell) == _generate.generate(shell), (
        f"de_toolkit/completions/detk.{shell} is not what the parsers give; regenerate it "
        "with: uv run python -m de_toolkit.completions._generate"
    )


@pytest.mark.parametrize("shell", COMPLETION_SHELLS)
def test_script_covers_every_command_and_subcommand(shell):
    text = completion_script(shell)
    for prog, subs in _commands():
        if shell == "tcsh":
            assert re.search(rf"^complete {re.escape(prog)} ", text, re.M), prog
        else:
            # each command's script registers it with the shell
            assert re.search(rf"\s{re.escape(prog)}$", text, re.M), prog
        for sub in subs:
            assert re.search(rf"\b{re.escape(sub)}\b", text), f"{prog} {sub}"


def _bash_complete(words):
    "What the shipped bash script completes the last of *words* to"
    script = completion_script("bash")
    driver = f"""
{script}
COMP_WORDS=({" ".join(repr(w) for w in words)})
COMP_CWORD=$((${{#COMP_WORDS[@]}}-1))
COMP_LINE="${{COMP_WORDS[*]}}"
COMP_POINT=${{#COMP_LINE}}
COMPREPLY=()
f=$(complete -p "${{COMP_WORDS[0]}}" | sed 's/.*-F \\([^ ]*\\).*/\\1/')
$f "${{COMP_WORDS[0]}}" "${{COMP_WORDS[-1]}}" "${{COMP_WORDS[-2]}}"
printf '%s\\n' "${{COMPREPLY[@]}}"
"""
    p = subprocess.run(["bash", "-c", driver], capture_output=True, text=True, check=True)
    return set(p.stdout.split())


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
@pytest.mark.parametrize("prog,subs", _commands(), ids=lambda v: v if isinstance(v, str) else "")
def test_bash_completes_every_subcommand(prog, subs):
    if subs:
        assert set(subs) <= _bash_complete([prog, ""])


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
@pytest.mark.parametrize(
    "words,expected",
    [
        (["detk", "norm", "deseq2", "--si"], {"--size-factors"}),
        (["detk-norm", "deseq2", "--si"], {"--size-factors"}),
        (["detk", "completion", ""], set(COMPLETION_SHELLS)),
        (["detk-stats", "basestats", "-f", ""], {"csv", "table"}),
    ],
)
def test_bash_completes_options_and_choices(words, expected):
    assert _bash_complete(words) == expected


def test_completion_needs_no_shtab(tmp_path):
    # detk completion reads the shipped file: it runs with shtab unimportable
    blocker = tmp_path / "sitecustomize.py"
    blocker.write_text(
        "import sys\n"
        "class _Block:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] == 'shtab':\n"
        "            raise ImportError('shtab is blocked')\n"
        "sys.meta_path.insert(0, _Block())\n"
    )
    code = (
        "import sys\n"
        "from de_toolkit.common import main\n"
        "main(['detk', 'completion', 'bash'])\n"
        "assert 'shtab' not in sys.modules\n"
    )
    p = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(tmp_path), "PATH": ""},
    )
    assert p.returncode == 0, p.stderr
    assert p.stdout == completion_script("bash")
