"""Keep the agent skills under skills/ in step with the CLI (#38).

The skills tell an agent which detk commands to run. These tests fail when a
skill names a subcommand or an option the installed CLI does not have, or when
a usage block copied into a skill's reference no longer matches the command's
own --help, so a CLI change that is not carried into the skills shows up in CI.
"""

import os
import re
import shlex
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))
SKILL_MARKDOWN = sorted(SKILLS_DIR.glob("*/**/*.md"))
BIN_DIR = os.path.dirname(sys.executable)


def _front_matter(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no YAML front matter"
    fields = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def _code_blocks(path, lang):
    return re.findall(rf"^```{lang}\n(.*?)^```", path.read_text(), re.S | re.M)


def _detk_commands(path):
    """The detk command lines in a file's bash blocks, continuations joined."""
    commands = []
    for block in _code_blocks(path, "bash"):
        for line in block.replace("\\\n", " ").splitlines():
            line = line.strip()
            if line.startswith("detk-") or line.startswith("detk "):
                commands.append(line)
    return commands


@lru_cache
def _help(*argv):
    exe = os.path.join(BIN_DIR, argv[0])
    p = subprocess.run([exe, *argv[1:], "--help"], capture_output=True, text=True)
    return p.stdout + p.stderr


def _usage_lines(text, tool):
    return [line.split() for line in text.splitlines() if line.strip().startswith(tool + " ")]


def _subcommands(tool):
    subs = {u[1] for u in _usage_lines(_help(tool), tool) if len(u) > 1}
    return set() if subs <= {"[options]"} else subs


def _split(command):
    argv = shlex.split(command)
    if argv[0] == "detk":
        argv = [f"detk-{argv[1]}", *argv[2:]]
    tool = argv[0]
    sub = argv[1] if _subcommands(tool) else None
    return tool, sub, argv


def test_skills_exist():
    assert SKILL_FILES, f"no skills found under {SKILLS_DIR}"


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_front_matter(path):
    # the fields npx skills (and agents) read; name must match the directory
    fields = _front_matter(path)
    assert fields.get("name") == path.parent.name
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fields["name"])
    assert len(fields.get("description", "")) > 20


@pytest.mark.parametrize("path", SKILL_MARKDOWN, ids=lambda p: str(p.relative_to(SKILLS_DIR)))
def test_skill_commands_match_cli(path):
    for command in _detk_commands(path):
        tool, sub, argv = _split(command)
        assert os.path.exists(os.path.join(BIN_DIR, tool)), f"{command!r}: no command {tool}"
        if sub is not None:
            assert sub in _subcommands(tool), f"{command!r}: {tool} has no subcommand {sub}"
        usage = _help(tool, sub) if sub else _help(tool)
        for arg in argv[1:]:
            if arg.startswith("-") and len(arg) > 1:
                option = arg.split("=", 1)[0]
                assert re.search(rf"(^|\s){re.escape(option)}([\s=,]|$)", usage, re.M), (
                    f"{command!r}: {option} is not an option of {tool} {sub or ''}"
                )


@pytest.mark.parametrize("path", SKILL_MARKDOWN, ids=lambda p: str(p.relative_to(SKILLS_DIR)))
def test_skill_usage_blocks_match_help(path):
    # a "## `detk-x sub`" heading followed by a text block holding its usage
    text = path.read_text()
    for heading, block in re.findall(r"^## `(detk[^`]*)`\n\n```text\n(.*?)^```", text, re.S | re.M):
        help_lines = {line.strip() for line in _help(*heading.split()).splitlines()}
        for line in block.splitlines():
            assert not line.strip() or line.strip() in help_lines, (
                f"{path.name} {heading}: {line.strip()!r} is not in `{heading} --help`; "
                "copy the current usage into the skill"
            )
