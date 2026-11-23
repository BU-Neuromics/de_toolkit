"""
The usage blocks of the docs pages, kept in step with the installed --help.

A usage block is a ```` ```text ```` block on a page of docs/tools/ or on
docs/report.md whose first line starts with ``usage:``. It holds a command's
(or subcommand's) own part of its ``--help``, copied as it prints: the usage
line, the positional arguments and the options, up to the common options.
The common options, the examples and the exit codes are the same on every
command, so a page does not repeat them: docs/tools/index.md shows the
common options once, in a ```` ```text ```` block starting with
``common options:``, and docs/concepts.md the exit codes.

tests/docs/test_docs_usage.py checks every block; to regenerate them after
a change to the CLI, run::

    uv run python tests/docs/docs_usage.py

which rewrites each block from the installed ``--help`` and prints the
pages it changed.
"""

import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
BIN_DIR = os.path.dirname(sys.executable)

# the pages whose usage blocks are checked, and the command each documents
PAGES = {
    **{f"tools/{tool}.md": f"detk-{tool}" for tool in (
        "stats", "filter", "norm", "transform", "de", "enrich", "outlier", "util", "wrapr"
    )},
    "report.md": "detk-report",
}  # fmt: skip
COMMON_PAGE = "tools/index.md"

TEXT_BLOCK = re.compile(r"^```text\n(.*?)^```[ \t]*$", re.S | re.M)
# the sections of --help after a command's own part (DETK-0025 Option B)
SHARED_SECTIONS = ("common options:", "examples:", "exit codes:")


@lru_cache
def help_text(*argv):
    "The installed ``--help`` of the command *argv* (``detk-norm``, ``deseq2``)"
    exe = os.path.join(BIN_DIR, argv[0])
    p = subprocess.run(
        [exe, *argv[1:], "--help"], capture_output=True, text=True, stdin=subprocess.DEVNULL
    )
    assert p.returncode == 0, f"{' '.join(argv)} --help exited {p.returncode}: {p.stderr}"
    return p.stdout


def sections(text):
    "The sections of a help *text*, by heading (``usage:``, ``options:``), in order"
    found, heading = {}, None
    for line in text.splitlines():
        if line and not line[0].isspace() and line.endswith(":") or line.startswith("usage: "):
            heading = "usage:" if line.startswith("usage:") else line
            found[heading] = []
        if heading is not None:
            found[heading].append(line)
    return {h: "\n".join(lines).strip("\n") for h, lines in found.items()}


def own_part(text):
    "A help *text* from its usage line up to its first shared section"
    start = text.index("usage:")
    ends = [text.find("\n" + s, start) for s in SHARED_SECTIONS]
    end = min((e for e in ends if e >= 0), default=len(text))
    return text[start:end].strip("\n")


def command_of(block):
    "The command a usage *block* documents: its usage line's words before the first argument"
    words = block.split()
    words = words[next(i for i, w in enumerate(words) if w.startswith("detk")) :]
    argv = []
    for word in words:
        if word.startswith(("[", "<", "-")):
            break
        argv.append(word)
    return tuple(argv)


def subcommands(tool):
    "The subcommands of *tool* as its --help lists them, in order (none for detk-filter)"
    usage = sections(help_text(tool))["usage:"]
    subs = []
    for line in usage.splitlines():
        words = line.removeprefix("usage:").split()
        if len(words) > 1 and not words[1].startswith(("[", "<", "-")):
            subs.append(words[1])
    return subs


def usage_blocks(text):
    "Each usage block of a page *text*: (match, block)"
    # "Usage:" too, docopt's heading, so a block in the old layout is found
    return [
        (m, m.group(1))
        for m in TEXT_BLOCK.finditer(text)
        if m.group(1).lower().startswith("usage:")
    ]


def expected_block(block):
    "What the usage *block* should hold: the current own part of its command's help"
    return own_part(help_text(*command_of(block)))


def regenerate(text):
    "*text* with every usage block rewritten from the installed --help"
    out, pos = [], 0
    for m, block in usage_blocks(text):
        out.append(text[pos : m.start(1)])
        out.append(expected_block(block) + "\n")
        pos = m.end(1)
    out.append(text[pos:])
    return "".join(out)


def common_options():
    "The common options section that every subcommand of a module command prints"
    return sections(help_text("detk-norm", "deseq2"))["common options:"]


def main():
    changed = []
    for page in [*PAGES, COMMON_PAGE]:
        path = DOCS / page
        text = path.read_text()
        new = regenerate(text)
        if page == COMMON_PAGE:
            new = re.sub(
                r"^```text\n[Cc]ommon options:\n.*?^```",
                lambda m: "```text\n" + common_options() + "\n```",
                new,
                flags=re.S | re.M,
            )
        if new != text:
            path.write_text(new)
            changed.append(page)
    for page in changed:
        print(f"rewrote docs/{page}")


if __name__ == "__main__":
    main()
