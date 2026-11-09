"""Keep the agent skills under skills/ in step with the CLI (#38).

The skills tell an agent which detk commands to run. For every markdown file
under skills/, these tests check that:

- each ``detk-*`` command line in a fenced code block (any fence except
  ``text``, which holds copied usage) parses with that command's own docopt
  usage, as the installed CLI prints it with ``--help``: the command and
  subcommand exist, every option is declared, and no positional argument is
  missing or extra;
- each ``detk-*`` command named in an inline code span in the prose exists,
  with its subcommand, and each option named in an inline code span is
  declared by the nearest command named above it (or, before any command is
  named, by one of the commands the file names);
- each usage block copied under a ``## `detk-x sub` `` heading still appears
  line for line in that command's ``--help``.

So a CLI change that is not carried into the skills fails CI. The tests do
not run the commands: they check that what the skill names is valid usage,
not that the commands do what the skill says they do.
"""

import os
import re
import shlex
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest
from docopt import DocoptExit, docopt

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))
SKILL_MARKDOWN = sorted(SKILLS_DIR.glob("*/**/*.md"))
BIN_DIR = os.path.dirname(sys.executable)

FENCE = re.compile(r"^```([^\n`]*)\n(.*?)^```[ \t]*$", re.S | re.M)
SPAN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
SHELL_OPERATORS = {"|", "||", "&&", ";", ">", ">>", "<", "&"}


def _front_matter(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no YAML front matter"
    fields = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


@lru_cache
def _help(*argv):
    exe = os.path.join(BIN_DIR, argv[0])
    p = subprocess.run([exe, *argv[1:], "--help"], capture_output=True, text=True)
    return p.stdout + p.stderr


@lru_cache
def _subcommands(tool):
    usage = [
        line.split() for line in _help(tool).splitlines() if line.strip().startswith(tool + " ")
    ]
    subs = {u[1] for u in usage if len(u) > 1}
    return frozenset() if subs <= {"[options]"} else frozenset(subs)


def _declared_options(doc):
    """The options a docopt doc declares: the flags at the start of each
    options-section line, before the two-space gap to the description."""
    options = set()
    for line in doc.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        spec = re.split(r"\s{2,}", line, maxsplit=1)[0]
        options.update(t for t in re.split(r"[\s,=]+", spec) if t.startswith("-"))
    return options


def _argv(command):
    """Split a shell command line into a detk argv, stopping at the first
    shell operator or comment, with ``detk x`` rewritten as ``detk-x``."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    argv = []
    for token in lexer:
        if token in SHELL_OPERATORS or token.startswith("#"):
            break
        argv.append(token)
    if len(argv) > 1 and argv[0] == "detk":
        argv = [f"detk-{argv[1]}", *argv[2:]]
    return argv


def _locate(argv, where, bare=False):
    """(tool, sub) for a detk argv; fails unless both exist. With *bare*, a
    command named without its subcommand is accepted (prose naming a tool)."""
    tool = argv[0]
    assert os.path.exists(os.path.join(BIN_DIR, tool)), f"{where}: no command {tool}"
    subs = _subcommands(tool)
    if not subs or (bare and len(argv) == 1):
        return tool, None
    sub = argv[1] if len(argv) > 1 else "(none)"
    assert sub in subs, f"{where}: {tool} has no subcommand {sub}; it has {sorted(subs)}"
    return tool, sub


def _doc(tool, sub):
    return _help(tool, sub) if sub else _help(tool)


def _walk(text):
    """Yield, in document order, ("block", line, command) for each detk command
    line in a fenced block other than ``text``, and ("span", line, content) for
    each inline code span outside the fenced blocks."""
    pos = 0
    for m in FENCE.finditer(text):
        yield from _spans(text, pos, m.start())
        pos = m.end()
        if m.group(1).strip().lower() == "text":
            continue
        lineno = text.count("\n", 0, m.start(2)) + 1
        logical, start = "", lineno
        for offset, raw in enumerate(m.group(2).splitlines()):
            if not logical:
                start = lineno + offset
            # join backslash continuations into one command line
            if raw.endswith("\\"):
                logical += raw[:-1] + " "
                continue
            line = (logical + raw).strip().removeprefix("$ ")
            logical = ""
            if line.startswith(("detk-", "detk ")):
                yield "block", start, line
    yield from _spans(text, pos, len(text))


def _spans(text, start, end):
    for m in SPAN.finditer(text, start, end):
        yield "span", text.count("\n", 0, m.start()) + 1, m.group(1).strip()


def _check_option(option, commands, where):
    """*option* must be declared by one of *commands*, a list of (tool, sub)."""
    option = option.split("=", 1)[0]
    if option in ("-h", "--help"):
        return  # docopt answers --help for every command
    declared = set().union(*(_declared_options(_doc(*c)) for c in commands))
    named = ", ".join(f"{t} {s or ''}".rstrip() for t, s in commands)
    assert option in declared, f"{where}: {option} is not an option of {named}"


def _named_commands(text):
    """Every valid (tool, sub) a file names, in a block or a prose span."""
    commands = []
    for kind, _, item in _walk(text):
        if item.startswith(("detk-", "detk ")):
            try:
                commands.append(_locate(_argv(item), "", bare=kind == "span"))
            except AssertionError:
                pass  # reported by check_markdown
    return list(dict.fromkeys(commands))


def check_markdown(text, name):
    """Check every detk command and option a skill markdown file names.

    An option named in prose is checked against the nearest command named
    above it; before any command, against every command the file names (a
    general remark such as "most commands take `-o FILE`").
    """
    context = _named_commands(text)
    for kind, lineno, item in _walk(text):
        where = f"{name}:{lineno}: {item!r}"
        if kind == "block":
            argv = _argv(item)
            tool, sub = _locate(argv, where)
            context = [(tool, sub)]
            try:
                docopt(_doc(tool, sub), argv[1:])
            except DocoptExit as e:
                raise AssertionError(f"{where} does not parse with its usage:\n{e}") from None
        elif item.startswith(("detk-", "detk ")):
            # a command named in prose usually leaves out its positionals, so
            # check the command, the subcommand and any options it shows
            argv = _argv(item)
            tool, sub = _locate(argv, where, bare=True)
            context = [(tool, sub)]
            for arg in argv[2 if sub else 1 :]:
                if arg.startswith("-") and len(arg) > 1:
                    _check_option(arg, context, where)
        elif re.match(r"--?[A-Za-z]", item):
            _check_option(item.split()[0], context, where)


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
    check_markdown(path.read_text(), path.relative_to(SKILLS_DIR))


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


GOOD = """\
```bash
detk-de deseq2 -o out.csv "counts ~ a[b]" counts.csv info.csv
```

Add `--last-term-only`, or `--report-dir=DIR`; see `detk-norm deseq2 -o FILE`.
"""


@pytest.mark.parametrize(
    "bad",
    [
        # missing positional
        "```bash\ndetk-de deseq2 -o out.csv 'counts ~ a[b]' counts.csv\n```\n",
        # extra positional
        "```bash\ndetk-norm deseq2 a.csv b.csv\n```\n",
        # bogus option, fenced sh, fenced without a language, continued line
        "```sh\ndetk-norm deseq2 --bogus counts.csv\n```\n",
        "```\ndetk-norm deseq2 --bogus counts.csv\n```\n",
        "```console\n$ detk-norm deseq2 \\\n    --bogus counts.csv\n```\n",
        # wrong subcommand in a block and in prose
        "```bash\ndetk-norm libary counts.csv\n```\n",
        "Use `detk-norm libary` instead.\n",
        # option in prose that the nearest command lacks
        GOOD + "\nThen `--last-term-onlyx`.\n",
        GOOD + "\n`detk-norm deseq2`, then `--last-term-only`.\n",
        # option before any command that no command in the file declares
        "Pass `--bogus`.\n" + GOOD,
        # an option the nearest command does not have
        "```bash\ndetk-enrich fgsea g.gmt r.csv\n```\n\nThen `--NES`.\n",
    ],
    ids=lambda text: re.sub(r"\W+", "-", text.strip())[-40:],
)
def test_checker_catches_drift(bad):
    check_markdown(GOOD, "good.md")
    with pytest.raises(AssertionError):
        check_markdown(bad, "bad.md")
