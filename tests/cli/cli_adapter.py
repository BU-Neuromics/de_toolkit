"""
The one place the CLI pin tests touch the command line parser.

The tests in ``tests/cli/`` state what each ``detk-*`` command line means in
parser-neutral terms (``cli_tables.py``) and reach the commands only through
the functions here:

- :func:`parse` runs a command line through the command's own ``main`` and
  stops it at the point it dispatches, after the command line is parsed and
  before any work is done, returning the arguments the command would act on;
- :func:`invoke` does the same but returns how the process would end (exit
  code, stdout, stderr), for help, version and invalid command lines;
- :func:`run` runs the command to the end, in process;
- :func:`run_console` runs the installed console script in a subprocess.

Arguments are reported by name, without the parser's decoration: ``<counts_fn>``
is ``counts_fn``, ``--out-delim`` is ``out_delim``, and the subcommand is
reported apart from them. Values are what the parser hands the command.

Every command parses with ``common.parse_cli``, which the stop replaces in
the module. The tables do not change with the parser.

:func:`parser` and :func:`examples` reach a command's argparse parser, for
the checks of help's structure and examples (DETK-0025 Option B).
"""

import argparse
import contextlib
import importlib
import shlex
import io
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# entry point name -> module whose ``main`` it runs (pyproject [project.scripts])
ENTRY_POINTS = {
    "detk": "common",
    "detk-norm": "norm",
    "detk-de": "de",
    "detk-enrich": "enrich",
    "detk-transform": "transform",
    "detk-filter": "filter",
    "detk-stats": "stats",
    "detk-outlier": "outlier",
    "detk-wrapr": "wrapr",
    "detk-report": "report",
    "detk-util": "util",
}

# the modules whose parse is the point a command dispatches; the umbrella
# ``detk`` parses only to pick a module, so its own parse is not a stop
_DISPATCH_MODULES = [m for p, m in ENTRY_POINTS.items() if p != "detk"]

# names the parser reports that are not arguments a command acts on
_NOT_ARGUMENTS = {"help", "h", "version"}


@dataclass
class Parsed:
    "A parsed command line: which module parsed it, its subcommand and arguments"

    module: str
    subcommand: str | None
    args: dict


@dataclass
class Outcome:
    "How a command line ended, as the process would have ended"

    code: int
    stdout: str
    stderr: str
    parsed: Parsed | None = field(default=None)


class _Dispatch(Exception):
    "Raised in place of a module's parser returning, to stop ``main`` there"

    def __init__(self, parsed):
        self.parsed = parsed


def _module(name):
    return importlib.import_module(f"de_toolkit.{name}")


def _normalize(module, result):
    "The parser's result (an argparse Namespace) as a :class:`Parsed`"
    found = vars(result)
    args = {k: v for k, v in found.items() if k != "subcommand" and k not in _NOT_ARGUMENTS}
    return Parsed(module, found.get("subcommand"), args)


def _stopper(module, parser):
    def stop(*a, **kw):
        raise _Dispatch(_normalize(module, parser(*a, **kw)))

    return stop


@contextlib.contextmanager
def _process(argv, stop):
    """
    Run as the entry point would: ``sys.argv`` is *argv*, stdout and stderr
    are captured, log records reach stderr as ``set_logging`` sends them, and
    with *stop* each module's parse ends ``main``.
    """
    out, err = io.StringIO(), io.StringIO()
    saved_argv = sys.argv
    patched = []
    handler = logging.StreamHandler(err)
    handler.setLevel(logging.WARNING)
    root = logging.getLogger()
    try:
        sys.argv = list(argv)
        if stop:
            for name in _DISPATCH_MODULES:
                mod = _module(name)
                patched.append((mod, "parse_cli", mod.parse_cli))
                mod.parse_cli = _stopper(name, mod.parse_cli)
        root.addHandler(handler)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            yield out, err
    finally:
        root.removeHandler(handler)
        for mod, attr, parser in patched:
            setattr(mod, attr, parser)
        sys.argv = saved_argv


def _exit_code(exc):
    "The exit code and stderr text the interpreter gives a SystemExit"
    code = exc.code
    if code is None:
        return 0, ""
    if isinstance(code, int):
        return code, ""
    return 1, f"{code}\n"


def invoke(argv, stop=True):
    """
    Run the command line *argv* (``argv[0]`` the entry point name) through
    its entry point's ``main``, in process, and return its :class:`Outcome`.
    With *stop*, ``main`` stops where it dispatches and the outcome carries
    the :class:`Parsed` arguments.
    """
    main = _module(ENTRY_POINTS[argv[0]]).main
    parsed = None
    code = 0
    extra = ""
    with _process(argv, stop) as (out, err):
        try:
            main(list(argv))
        except _Dispatch as d:
            parsed = d.parsed
        except SystemExit as e:
            code, extra = _exit_code(e)
    return Outcome(code, out.getvalue(), err.getvalue() + extra, parsed)


def parse(argv):
    """
    The :class:`Parsed` arguments the command line *argv* dispatches with.
    Fails the test if the command line does not reach dispatch.
    """
    outcome = invoke(argv)
    assert outcome.parsed is not None, (
        f"{' '.join(argv)} did not dispatch: exit {outcome.code}\n{outcome.stderr}"
    )
    return outcome.parsed


def run(argv):
    "Run the command line *argv* to the end, in process; its :class:`Outcome`"
    return invoke(argv, stop=False)


def console_script(name):
    "Path of the installed console script *name*, beside the interpreter"
    return Path(sys.executable).parent / name


def run_console(argv, cwd=None):
    "Run the installed console script for *argv* in a subprocess; its :class:`Outcome`"
    env = dict(os.environ)
    p = subprocess.run(
        [str(console_script(argv[0])), *argv[1:]],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
    )
    return Outcome(p.returncode, p.stdout, p.stderr)


def same_value(expected, actual):
    """
    Whether the value the tables expect, written as on the command line, is
    the value the parser handed the command. A parser that converts types
    hands a number where the table has its text, which is the same value.
    """
    if isinstance(expected, list):
        return (
            isinstance(actual, list | tuple)
            and len(expected) == len(actual)
            and all(same_value(e, a) for e, a in zip(expected, actual))
        )
    if expected == actual:
        return True
    if (
        isinstance(expected, str)
        and isinstance(actual, int | float)
        and not isinstance(actual, bool)
    ):
        try:
            return float(expected) == float(actual)
        except ValueError:
            return False
    return False


def unset(value):
    "Whether a parsed value is the parser's 'not given' for an argument"
    return value is None or value is False or value == []


def parser(prog):
    "The argparse parser of the entry point *prog*"
    return _module(ENTRY_POINTS[prog]).build_parser()


def subparsers(p):
    "{name: parser} of the subcommands of the argparse parser *p*; {} for none"
    for action in p._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def examples(prog, sub=None):
    """
    The examples the help of *prog* (and its subcommand *sub*) gives, as
    (what it does, argv) pairs; ``detk x ...`` is given as ``detk-x ...``
    """
    p = parser(prog)
    if sub:
        p = subparsers(p)[sub]
    out = []
    for what, command in p.examples:
        argv = shlex.split(command)
        if len(argv) > 1 and argv[0] == "detk" and f"detk-{argv[1]}" in ENTRY_POINTS:
            argv = [f"detk-{argv[1]}", *argv[2:]]
        out.append((what, tuple(argv)))
    return out
