"""Run a tutorial page: executable Markdown (DETK-0064, Option A).

A tutorial is a docs page whose ```bash blocks run in order, in one fresh
working directory, under ``bash -euo pipefail``. HTML comments, invisible on
the site, tell the runner what it needs to know:

``<!-- tutorial: requires R DESeq2 airway -->``
    The page needs these to run; where one is missing the test skips with
    the reason. ``R`` followed by R package names, or program names
    (``<!-- tutorial: requires mlr -->``). A page may carry several.
``<!-- tutorial: expect -->`` before a fenced block
    That block is the output of the previous bash block, compared after
    trimming trailing whitespace; ``...`` matches any text. ``expect regex``
    compares by a regular expression instead, and ``expect stderr`` compares
    stderr (the default after a ``fails`` block) rather than stdout.
``<!-- tutorial: fails -->`` before a bash block
    The block must exit non-zero.
``<!-- tutorial: hidden`` ... ``-->`` around bash blocks
    The blocks run but do not show on the site.
``<!-- tutorial -->``
    Marks a page outside ``docs/tutorials/`` (a recipe, say) as a tutorial.

Shell variables, functions and the current directory carry from one block to
the next, as they would in a reader's terminal. ``TUTORIAL_SRC`` holds the
directory of the page, so a hidden block can copy files committed next to it.

This module has no pytest dependency at import so its parser can be tested on
its own; ``run_page`` raises :class:`TutorialSkip` or :class:`TutorialFailure`.
"""

from __future__ import annotations

import functools
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"

#: seconds one block may run before it counts as failed
BLOCK_TIMEOUT = 1800
#: characters of stdout/stderr quoted in a failure message
TAIL = 4000

# when set, a missing requirement fails the test instead of skipping it, so a
# CI job that should run every tutorial cannot silently skip one
REQUIRE_ALL_ENV = "DETK_TUTORIALS_REQUIRE_ALL"

_MARKER = re.compile(r"^\s*<!--\s*tutorial(?::\s*(?P<body>.*?))?\s*(?P<close>-->)?\s*$")
_FENCE = re.compile(r"^(?P<indent>\s*)(?P<fence>`{3,}|~{3,})\s*(?P<info>[^`]*?)\s*$")


class TutorialError(Exception):
    """A page that cannot be run as written (a bad marker, say)."""


class TutorialSkip(Exception):
    """A requirement of the page is missing."""


class TutorialFailure(AssertionError):
    """A block failed or an output did not match."""


@dataclass
class Block:
    """A fenced block of the page."""

    lang: str
    code: str
    line: int  # 1-based line of the opening fence
    hidden: bool = False
    fails: bool = False
    expect: str | None = None  # None, or the expect marker's options


@dataclass
class Page:
    path: Path
    requires: list[list[str]] = field(default_factory=list)
    marked: bool = False  # carries a tutorial marker of any kind
    blocks: list[Block] = field(default_factory=list)

    @property
    def runnable(self) -> list[Block]:
        return [b for b in self.blocks if b.lang == "bash" or b.expect is not None]


def parse(path: Path | str) -> Page:
    """Parse a page into its blocks and markers."""
    path = Path(path)
    page = Page(path)
    lines = path.read_text().splitlines()
    pending: dict | None = None  # marker waiting for the next block
    hidden = False
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _MARKER.match(line)
        if m:
            page.marked = True
            body = (m.group("body") or "").split()
            word, args = (body[0], body[1:]) if body else ("", [])
            if word == "hidden":
                if m.group("close"):
                    raise TutorialError(
                        f"{path}:{i + 1}: put the hidden blocks between "
                        "'<!-- tutorial: hidden' and a closing '-->'"
                    )
                if hidden:
                    raise TutorialError(f"{path}:{i + 1}: hidden inside hidden")
                hidden = True
            elif not m.group("close"):
                raise TutorialError(f"{path}:{i + 1}: close the marker on its line with '-->'")
            elif word == "requires":
                if not args:
                    raise TutorialError(f"{path}:{i + 1}: requires names nothing")
                page.requires.append(args)
            elif word in ("expect", "fails"):
                if pending is not None:
                    raise TutorialError(f"{path}:{i + 1}: two markers before one block")
                pending = {"word": word, "args": args, "line": i + 1}
            elif word:
                raise TutorialError(f"{path}:{i + 1}: unknown tutorial marker {word!r}")
            i += 1
            continue
        if hidden and line.strip() == "-->":
            hidden = False
            i += 1
            continue
        f = _FENCE.match(line)
        if f:
            indent, fence = len(f.group("indent")), f.group("fence")
            lang = f.group("info").split()[0].lstrip("{.") if f.group("info") else ""
            start = i
            body = []
            i += 1
            while i < len(lines):
                close = lines[i].strip()
                if close.startswith(fence[0] * len(fence)) and set(close) == {fence[0]}:
                    break
                text = lines[i]
                body.append(text[indent:] if text[:indent].strip() == "" else text.lstrip())
                i += 1
            else:
                raise TutorialError(f"{path}:{start + 1}: unclosed code fence")
            block = Block(lang=lang, code="\n".join(body), line=start + 1, hidden=hidden)
            if pending is not None:
                if pending["word"] == "fails":
                    if lang != "bash":
                        raise TutorialError(
                            f"{path}:{pending['line']}: 'fails' must come before a bash block"
                        )
                    block.fails = True
                else:
                    block.expect = " ".join(pending["args"])
                pending = None
            page.blocks.append(block)
            i += 1
            continue
        if pending is not None and line.strip():
            raise TutorialError(
                f"{path}:{pending['line']}: '{pending['word']}' must come right before a block"
            )
        i += 1
    if hidden:
        raise TutorialError(f"{path}: a hidden marker is never closed with '-->'")
    if pending is not None:
        raise TutorialError(f"{path}:{pending['line']}: '{pending['word']}' before no block")
    return page


def discover(docs: Path = DOCS) -> list[Path]:
    """Every tutorial page: docs/tutorials/*.md but the index, and any other
    page under docs/ carrying a tutorial marker."""
    pages = {p for p in (docs / "tutorials").glob("*.md") if p.name != "index.md"}
    for p in docs.rglob("*.md"):
        if p not in pages and p.parent != docs / "tutorials" and parse(p).marked:
            pages.add(p)
    return sorted(pages)


# requirements -------------------------------------------------------------


@functools.cache
def _r_packages_missing(packages: tuple[str, ...]) -> tuple[str, ...]:
    if not packages:
        return ()
    expr = (
        "p <- commandArgs(TRUE); "
        "cat(p[!vapply(p, requireNamespace, logical(1), quietly = TRUE)], sep = '\\n')"
    )
    r = subprocess.run(
        ["Rscript", "-e", expr, *packages], capture_output=True, text=True, timeout=300
    )
    return tuple(x for x in r.stdout.split() if x)


def missing_requirements(page: Page) -> list[str]:
    """What the page requires that this machine lacks, as readable reasons."""
    missing = []
    for req in page.requires:
        if req[0] == "R":
            if shutil.which("Rscript") is None:
                missing.append("R (Rscript) is not on PATH")
            else:
                pkgs = _r_packages_missing(tuple(req[1:]))
                if pkgs:
                    missing.append("R package(s) not installed: " + ", ".join(pkgs))
        else:
            missing += [f"{prog} is not on PATH" for prog in req if shutil.which(prog) is None]
    return missing


# running --------------------------------------------------------------------

# saves the shell's variables, functions and directory on exit, so the next
# block starts where this one left off
_EPILOGUE = r"""
__tutorial_save() {
  { declare -p $(compgen -v | grep -vE "$__TUTORIAL_SKIP") 2>/dev/null || true
    declare -f
    printf 'cd %q\n' "$PWD"
  } > "$__TUTORIAL_STATE"
}
trap __tutorial_save EXIT
"""

# bash's own variables (read-only or changing by themselves) and the runner's,
# which are not carried from block to block
_SKIP_VARS = (
    "^(BASH.*|EUID|PPID|UID|SHELLOPTS|GROUPS|FUNCNAME|PIPESTATUS|RANDOM|SRANDOM|"
    "SECONDS|LINENO|EPOCH.*|HISTCMD|_|PWD|OLDPWD|SHLVL|DIRSTACK|COMP_.*|__TUTORIAL_.*)$"
)


@dataclass
class Result:
    block: Block
    returncode: int
    stdout: str
    stderr: str


def _tail(text: str) -> str:
    return text if len(text) <= TAIL else "[...]\n" + text[-TAIL:]


def _where(page: Page, line: int) -> str:
    try:
        name = page.path.resolve().relative_to(REPO)
    except ValueError:
        name = page.path
    return f"{name}:{line}"


def _env(workdir: Path, page: Page) -> dict:
    env = dict(os.environ)
    # the detk this test session imports, whatever environment it lives in
    env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + env.get("PATH", "")
    env["TUTORIAL_SRC"] = str(page.path.resolve().parent)
    return env


def matches(expected: str, actual: str, regex: bool = False) -> bool:
    """Compare an output shown on the page with what the block printed.

    Trailing whitespace on each line and blank lines at either end are
    ignored. Without ``regex``, ``...`` in the expected text matches any text
    (across lines too); with it, the expected text is a regular expression
    that must match the whole output.
    """

    def norm(s: str) -> str:
        return "\n".join(x.rstrip() for x in s.strip("\n").splitlines()).strip("\n")

    expected, actual = norm(expected), norm(actual)
    if regex:
        return re.fullmatch(expected, actual, flags=re.DOTALL) is not None
    pattern = ".*?".join(re.escape(part) for part in expected.split("..."))
    return re.fullmatch(pattern, actual, flags=re.DOTALL) is not None


def run_page(path: Path | str, workdir: Path | str, *, require_all: bool | None = None) -> list:
    """Run a tutorial page in ``workdir`` (which should be empty).

    Returns the results of its bash blocks. Raises :class:`TutorialSkip` when a
    requirement is missing (or :class:`TutorialFailure` instead, with
    ``require_all`` or ``$DETK_TUTORIALS_REQUIRE_ALL`` set), and
    :class:`TutorialFailure` when a block fails or an output does not match.
    """
    page = parse(path)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    if require_all is None:
        require_all = os.environ.get(REQUIRE_ALL_ENV, "") not in ("", "0")
    missing = missing_requirements(page)
    if missing:
        reason = f"{_where(page, 1)}: " + "; ".join(missing)
        if require_all:
            raise TutorialFailure(reason + f" (and {REQUIRE_ALL_ENV} is set)")
        raise TutorialSkip(reason)

    state_dir = workdir / ".tutorial"
    state_dir.mkdir(exist_ok=True)
    state = state_dir / "state.sh"
    state.write_text(f"cd {shlex.quote(str(workdir))}\n")
    env = _env(workdir, page)
    env["__TUTORIAL_SKIP"] = _SKIP_VARS
    env["__TUTORIAL_STATE"] = str(state)

    results: list[Result] = []
    last: Result | None = None
    for block in page.runnable:
        if block.expect is not None:
            _check_expect(page, block, last)
            continue
        script_path = state_dir / f"block{block.line}.sh"
        script_path.write_text(
            f"source {shlex.quote(str(state))}\n{_EPILOGUE}\n"
            f"# {_where(page, block.line)}\n{block.code}\n"
        )
        try:
            p = subprocess.run(
                ["bash", "-euo", "pipefail", str(script_path)],
                cwd=workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=BLOCK_TIMEOUT,
            )
        except subprocess.TimeoutExpired as e:
            raise TutorialFailure(
                f"{_where(page, block.line)}: block timed out after {BLOCK_TIMEOUT}s\n"
                f"--- block ---\n{block.code}\n--- stderr ---\n{_tail(_text(e.stderr))}"
            ) from None
        last = Result(block, p.returncode, p.stdout, p.stderr)
        results.append(last)
        ok = (p.returncode != 0) if block.fails else (p.returncode == 0)
        if not ok:
            what = (
                "block was expected to fail (marked 'fails') but exited 0"
                if block.fails
                else f"block exited {p.returncode}"
            )
            raise TutorialFailure(
                f"{_where(page, block.line)}: {what}\n"
                f"--- block ---\n{block.code}\n"
                f"--- stderr ---\n{_tail(p.stderr)}\n"
                f"--- stdout ---\n{_tail(p.stdout)}"
            )
    return results


def _text(b) -> str:
    if b is None:
        return ""
    return b.decode(errors="replace") if isinstance(b, bytes) else b


def _check_expect(page: Page, block: Block, last: Result | None) -> None:
    opts = set(block.expect.split())
    unknown = opts - {"regex", "stdout", "stderr"}
    if unknown or {"stdout", "stderr"} <= opts:
        raise TutorialError(
            f"{_where(page, block.line)}: expect takes 'regex' and one of "
            f"'stdout' or 'stderr', not {block.expect!r}"
        )
    if last is None:
        raise TutorialError(f"{_where(page, block.line)}: expect follows no bash block")
    stream = (
        "stderr" if "stderr" in opts or (last.block.fails and "stdout" not in opts) else "stdout"
    )
    actual = getattr(last, stream)
    if not matches(block.code, actual, regex="regex" in opts):
        raise TutorialFailure(
            f"{_where(page, block.line)}: the {stream} of the block at line "
            f"{last.block.line} does not match the output shown"
            + (" (as a regex)" if "regex" in opts else "")
            + f"\n--- shown on the page ---\n{block.code}\n--- {stream} ---\n{_tail(actual)}"
        )
