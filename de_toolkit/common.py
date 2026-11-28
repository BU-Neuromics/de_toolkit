r"""
detk, the differential expression toolkit: one command for every detk
module command. detk <command> ... runs detk-<command> ..., so
detk norm deseq2 counts.csv is detk-norm deseq2 counts.csv, and
detk norm --help is the help of detk-norm.

This module also holds what the commands share: the command line parser
(:class:`DetkParser` and :func:`parse_cli`), the common options, the counts
matrix and the module base class.
"""

import argparse
import functools
from collections import OrderedDict
from copy import deepcopy
import csv
import io
import logging
import os
import pandas
from pprint import pformat
import sys
import traceback
import warnings
from .formula import DesignMatrix, FormulaParseError
from .version import __version__

# process start time, recorded at import for provenance (a CLI invocation
# imports this module at startup, so this approximates the run's startTime)
from datetime import datetime, UTC

_PROCESS_START = datetime.now(UTC)

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ------------------------------------------------------------ command line
#
# Every detk command parses its command line with a DetkParser (argparse),
# whose help is what DETK-0025 Option B promises, in this order:
#
#   description          the command's or subcommand's description
#   usage                one line per way of calling it, docopt style
#   positional arguments each positional with a one-line description
#   options              the command's own options, -h first
#   common options       the options every detk command shares
#   examples             at least one command line per subcommand
#   exit codes           0 success, 2 usage error, 1 any other failure (DETK-0031)
#
# Every option states its metavar, default and choices, so that an agent
# reading --help has the facts in the same places for every command.
# Wording may improve in any release; the structure and the facts are the
# promise, and tests/cli/ checks them.

# help is formatted at a fixed width, so it is the same on a terminal, in a
# pipe and in a test
HELP_WIDTH = 80


class DetkHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    The help formatter of every detk parser: descriptions and examples as
    written, and each option's default and choices stated after its
    description, ``(choices: a, b)`` and ``(default: x)``.
    """

    def __init__(self, prog):
        super().__init__(prog, width=HELP_WIDTH, max_help_position=30)

    def _format_action_invocation(self, action):
        # "-o, --output FILE" on every Python (3.11 and 3.12 repeat the
        # metavar: "-o FILE, --output FILE")
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        return ", ".join(action.option_strings) + " " + self._format_args(action, default)

    def _split_lines(self, text, width):
        # keep "(default: x)" on one line
        glued = text.replace("(default: ", "(default:\0")
        return [line.replace("\0", " ") for line in super()._split_lines(glued, width)]

    def _get_help_string(self, action):
        text = action.help or ""
        if isinstance(
            action, (argparse._SubParsersAction, argparse._SubParsersAction._ChoicesPseudoAction)
        ):
            # a subcommand is listed with its own line below this one
            return text
        if action.choices and action.metavar is not None:
            text += " (choices: " + ", ".join(str(c) for c in action.choices) + ")"
        if action.option_strings and action.default not in (None, False, argparse.SUPPRESS):
            text += " (default: %(default)s)"
        return text


class _Once:
    """
    An option given more than once is an error, as it was under docopt
    (pinned in tests/cli/test_cli_behaviours.py), rather than argparse's
    last-one-wins.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        seen = namespace.__dict__.setdefault("_detk_seen", set())
        if self.dest in seen:
            raise argparse.ArgumentError(self, "given more than once")
        seen.add(self.dest)
        super().__call__(parser, namespace, values, option_string)


class _StoreOnce(_Once, argparse._StoreAction):
    pass


class _StoreTrueOnce(_Once, argparse._StoreTrueAction):
    pass


class DetkParser(argparse.ArgumentParser):
    """
    The argparse parser of every detk command and subcommand.

    *examples* is a list of ``(what it does, command line)`` pairs printed
    last in help; tests/cli/ checks that each parses and runs it where test
    data allows. A parser with subcommands lists its subcommands' usage
    lines and examples. Usage is written docopt style, one line per
    subcommand (``detk-norm cpm [options] <counts_fn>``); the options are
    listed in full below it.
    """

    def __init__(
        self, *args, examples=(), validate=None, intermixed=False, add_help=True, **kwargs
    ):
        kwargs.setdefault("formatter_class", DetkHelpFormatter)
        # every command's help ends with its exit codes (DETK-0031)
        kwargs.setdefault("epilog", EXIT_CODES_EPILOG)
        super().__init__(*args, add_help=False, **kwargs)
        self.examples = list(examples)
        # validate(args) returns an error message for a combination of
        # arguments argparse cannot express, or None; parse_cli reports it
        # as a usage error of this parser
        self.validate = validate
        # intermixed: positionals may come between options (detk-util
        # gather's ``a.sf --format=salmon b.sf``, as docopt allowed); plain
        # argparse gives a positional only one run of the command line. A
        # leaf parser with an optional positional is always intermixed (see
        # _parses_intermixed), so Python 3.11 takes ``counts.csv -o out.csv
        # cov.csv`` as 3.12+ and docopt do (DETK-0151)
        self.intermixed = intermixed
        self._intermixing = False
        if add_help:
            self.add_argument("-h", "--help", action="help", help="Print this help and exit")
        self.register("action", "store", _StoreOnce)
        self.register("action", None, _StoreOnce)
        self.register("action", "store_true", _StoreTrueOnce)

    def _parses_intermixed(self):
        """
        Whether this parser parses its options and positionals in two
        passes: when asked to, and for a leaf parser (no subcommands) with an
        optional positional, which Python 3.11's argparse gives only the run
        of positionals before the first option (DETK-0151)
        """
        if self.intermixed:
            return True
        if self._subcommands() is not None:
            return False
        return any(
            not action.option_strings and action.nargs in ("?", "*") for action in self._actions
        )

    def parse_known_args(self, args=None, namespace=None):
        if self._parses_intermixed() and not self._intermixing:
            # parse_known_intermixed_args calls back here
            self._intermixing = True
            try:
                namespace, extras = self.parse_known_intermixed_args(args, namespace)
            finally:
                self._intermixing = False
        else:
            namespace, extras = super().parse_known_args(args, namespace)
        # the bookkeeping of _Once is not an argument
        namespace.__dict__.pop("_detk_seen", None)
        return namespace, extras

    # -- the pieces of help
    def _subcommands(self):
        "The subparsers action, or None for a parser without subcommands"
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                return action
        return None

    def usage_lines(self):
        "One usage line per way of calling this command, without 'usage: '"
        if self.usage:
            return self.usage.splitlines()
        subs = self._subcommands()
        if subs is not None:
            return [line for p in subs.choices.values() for line in p.usage_lines()]
        words = [self.prog, "[options]"]
        for action in self._actions:
            if action.option_strings or action.help == argparse.SUPPRESS:
                continue
            metavar = action.metavar or action.dest
            if action.nargs == "?":
                words.append(f"[{metavar}]")
            elif action.nargs == "*":
                words.append(f"[{metavar}...]")
            elif action.nargs == "+":
                words.append(f"{metavar}...")
            else:
                words.append(metavar)
        return [" ".join(words)]

    def all_examples(self):
        "This command's examples, then each subcommand's"
        examples = list(self.examples)
        subs = self._subcommands()
        if subs is not None:
            for p in subs.choices.values():
                examples += [e for e in p.all_examples() if e not in examples]
        return examples

    def unknown_option(self, arg):
        """
        Whether the command line word *arg* looks like an option and is not
        one of this parser's, as argparse matches them: exactly, by a
        prefix of a long option (``--outp`` for ``--output``), or by a short
        option with its value attached (``-oFILE``). An ambiguous prefix is
        left to argparse to report. A :meth:`value_word` is not an option.
        """
        return self._not_an_option_of_ours(arg) and not self.value_word(arg)

    def value_word(self, arg):
        """
        Whether the command line word *arg*, which starts with ``-``, is a
        value and not an option: it is none of this parser's options and
        holds a ``~`` or a space, as a design does (``'-2.5 ~ counts'``,
        which then reaches the design's own message, DETK-0190). No option
        name has either, and an option of this parser written with its value
        attached (``-o~/out.csv``) is still that option.
        """
        return ("~" in arg or " " in arg) and self._not_an_option_of_ours(arg)

    def _parse_optional(self, arg_string):
        # argparse reads a word starting with "-" as an option unless it has
        # a space; a value_word is a positional, with or without one
        if self.value_word(arg_string):
            return None
        return super()._parse_optional(arg_string)

    def _not_an_option_of_ours(self, arg):
        "Whether *arg* looks like an option and matches none of this parser's"
        if not arg.startswith("-") or arg == "-" or self._negative_number_matcher.match(arg):
            return False
        names = self._option_string_actions
        if arg.startswith("--"):
            name = arg.split("=", 1)[0]
            return name not in names and not any(n.startswith(name) for n in names)
        return arg not in names and arg[:2] not in names

    def format_usage(self):
        indent = "\n" + " " * len("usage: ")
        return "usage: " + indent.join(self.usage_lines()) + "\n"

    # the help sections in their promised order; a group of another title
    # goes before the common options
    _SECTION_ORDER = {"positional arguments": 0, "options": 1, "common options": 3}

    def format_help(self):
        sections = []
        if self.description:
            sections.append(self.description.strip("\n") + "\n")
        sections.append(self.format_usage())
        groups = sorted(self._action_groups, key=lambda g: self._SECTION_ORDER.get(g.title, 2))
        for group in groups:
            if not group._group_actions:
                continue
            formatter = self._get_formatter()
            formatter.start_section(group.title)
            formatter.add_text(group.description)
            formatter.add_arguments(group._group_actions)
            formatter.end_section()
            sections.append(formatter.format_help())
        examples = self.all_examples()
        if examples:
            lines = ["examples:"]
            for what, command in examples:
                lines += [f"  # {what}", f"  {command}"]
            sections.append("\n".join(lines) + "\n")
        if self.epilog:
            sections.append(self.epilog.strip("\n") + "\n")
        return "\n".join(sections)

    def error(self, message):
        "Print the usage and the error on stderr and exit 2 (DETK-0031)"
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\nRun '{self.prog} --help' for help.\n")


def add_common_options(parser, out_delim=True):
    """
    Add the options every detk command shares to *parser*, in their own
    help section, "common options". *out_delim* False leaves out
    ``-d/--out-delim``, for a command that writes no table (detk-util record).
    """
    group = parser.add_argument_group("common options")
    if out_delim:
        group.add_argument(
            "-d",
            "--out-delim",
            metavar="CHAR",
            default=",",
            help="Delimiter to use for the output file",
        )
    group.add_argument(
        "--report-dir",
        metavar="DIR",
        default="./detk_report",
        help="Directory to write the HTML report and module JSON into",
    )
    group.add_argument("--no-report", action="store_true", help="Do not write the HTML report")
    add_version_option(group)
    group.add_argument("-v", "--verbose", action="store_true", help="Make log output verbose")
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Turn off all logging except warnings and errors",
    )
    group.add_argument("--shut-up", action="store_true", help="Turn off ALL logging")
    return group


def add_command_options(parser, what="subcommand"):
    """
    The options of a command's top level, in its "common options" section:
    ``--version``, with a line saying each *what* (subcommand) takes the
    common options in its own help.
    """
    group = parser.add_argument_group(
        "common options",
        f"Each {what} also takes the common options:\nsee {parser.prog} <{what}> --help.",
    )
    add_version_option(group)
    return group


def add_version_option(group):
    "``--version``: print the detk version and exit, honoured as an argument of its own"
    group.add_argument(
        "--version", action="version", version=__version__, help="Print the detk version and exit"
    )


def add_subcommands(parser):
    """
    The subparsers of a command with subcommands. Add each with
    ``add_parser(name, help=..., description=..., examples=[...])``: *help*
    is the one line the command's help lists it with, *description* the
    text its own help starts with, *examples* its ``(what it does, command
    line)`` pairs; then its arguments and :func:`add_common_options`.
    """
    return parser.add_subparsers(
        dest="subcommand",
        metavar="<subcommand>",
        help="The subcommand to run, one of:",
        required=True,
        title="positional arguments",
        parser_class=DetkParser,
    )


def parse_cli(parser, argv):
    """
    Parse the command line *argv* (``argv[0]`` the command's name) with
    *parser* and return the arguments as an ``argparse.Namespace``, the
    subcommand (if any) as ``subcommand``. On a usage error, print it with
    the usage and exit 2; ``-h``/``--help`` and ``--version`` print and
    exit 0. This is the point every command dispatches from, and the one
    the tests in tests/cli/ stop a command at.
    """
    args = list(argv[1:])
    # the parser that reports a usage error: the subcommand's, once it is
    # named, so the error shows its usage and points at its help
    leaf, rest = parser, args
    subs = parser._subcommands()
    if subs is not None and args and args[0] in subs.choices:
        leaf, rest = subs.choices[args[0]], args[1:]
    # a subcommand that runs another command (detk-util record) sets
    # command_dest on its parser: every word after the first "--" is that
    # command, taken as given and never parsed as detk's arguments
    command_dest = getattr(leaf, "command_dest", None)
    command = []
    if "--" in rest:
        if command_dest is None:
            # docopt took "--" for an argument no usage declared; it is not an
            # end-of-options marker (pinned in tests/cli/test_cli_behaviours.py)
            leaf.error("unrecognized arguments: --")
        cut = rest.index("--")
        command = rest[cut + 1 :]
        args = args[: len(args) - len(rest) + cut]
        rest = rest[:cut]
    unknown = [a for a in rest if leaf.unknown_option(a)]
    if unknown:
        # name an unknown option before a missing positional, as docopt did
        # (argparse would report only the missing positional)
        leaf.error("unrecognized arguments: " + " ".join(unknown))
    namespace, extras = parser.parse_known_args(args)
    if extras:
        leaf.error("unrecognized arguments: " + " ".join(extras))
    if command_dest is not None:
        stray = getattr(namespace, command_dest, None) or []
        if stray:
            leaf.error(
                "unrecognized arguments: " + " ".join(stray) + " (the command to run goes after --)"
            )
        setattr(namespace, command_dest, command)
    if leaf.validate is not None:
        message = leaf.validate(namespace)
        if message:
            leaf.error(message)
    # what cli_main needs to report a failure after parsing: the parser whose
    # usage a usage error shows, and whether --verbose asked for tracebacks
    _CLI_STATE.update(parser=leaf, verbose=bool(getattr(namespace, "verbose", False)))
    return namespace


# ---------------------------------------------------------------- exit codes
#
# DETK-0031: every detk command exits
#
#   0  on success
#   2  on a usage error: argparse's own (DetkParser.error), and a check detk
#      makes after parsing (UsageError, InvalidDesignException)
#   1  on any other failure: a bad input file, a missing R or R package, a
#      step that fails
#
# A failure prints one line on stderr, "<command>: error: <cause>"; the
# traceback is printed before it only under --verbose. cli_main is the one
# place that turns an exception into an exit code.

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2

EXIT_CODES_EPILOG = (
    "exit codes:\n"
    "  0  success\n"
    "  2  usage error: the command line is wrong (see the usage above)\n"
    "  1  any other failure: bad input, a missing R or R package, a failing step;\n"
    "     the cause is the last line on stderr (--verbose adds the traceback)"
)

# set by parse_cli for cli_main
_CLI_STATE = {}


class UsageError(Exception):
    """
    A command line detk rejects after parsing it, for a reason argparse
    cannot check: exits 2 with the command's usage, like an argparse error.
    """


def option_value(args, dest, kind=int):
    """
    The value of the option *dest* in *args* converted with *kind* (int or
    float); a value that does not convert is a :class:`UsageError` naming
    the option, as argparse names one.
    """
    value = getattr(args, dest)
    try:
        return kind(value)
    except (TypeError, ValueError):
        names = [f"--{dest.replace('_', '-')}"]
        parser = _CLI_STATE.get("parser")
        if parser is not None:
            for action in parser._actions:
                if action.dest == dest and action.option_strings:
                    names = action.option_strings
        raise UsageError(
            f"argument {'/'.join(names)}: invalid {kind.__name__} value: {value!r}"
        ) from None


def one_line(exc):
    "The cause of the exception *exc* on one line: its message's first line, else its type"
    lines = [line.strip() for line in str(exc).splitlines() if line.strip()]
    return lines[0] if lines else type(exc).__name__


def cli_main(main):
    """
    Decorate a command's ``main(argv)`` with the exit codes of DETK-0031:
    a :class:`UsageError` or :class:`InvalidDesignException` exits 2 with the
    usage, any other exception exits 1 with its cause on one line of stderr
    (and its traceback first under ``--verbose``). ``SystemExit`` passes
    through: argparse's usage errors already exit 2, help and version 0.
    """

    @functools.wraps(main)
    def wrapper(argv=None):
        argv = list(sys.argv if argv is None else argv)
        _CLI_STATE.clear()
        try:
            return main(argv)
        except (UsageError, InvalidDesignException) as e:
            parser = _CLI_STATE.get("parser")
            if _CLI_STATE.get("verbose"):
                traceback.print_exc()
            if parser is not None:
                parser.error(one_line(e))
            prog = os.path.basename(argv[0]) if argv else "detk"
            sys.stderr.write(f"{prog}: error: {one_line(e)}\n")
            sys.exit(EXIT_USAGE)
        except Exception as e:
            prog = os.path.basename(argv[0]) if argv else "detk"
            if _CLI_STATE.get("verbose"):
                traceback.print_exc()
                hint = ""
            else:
                hint = " (--verbose for the traceback)"
            sys.stdout.flush()
            sys.stderr.write(f"{prog}: error: {one_line(e)}{hint}\n")
            sys.exit(EXIT_FAILURE)

    return wrapper


banner = rf"""
===========================
        _      _   _    
       | |    | | | |   
     __| | ___| |_| | __
    / _` |/ _ \ __| |/ /
   | (_| |  __/ |_|   < 
    \__,_|\___|\__|_|\_\
                        
 de-toolkit.readthedocs.io
 Version: {__version__}
==========================="""


def set_logging(opts):
    if not opts.shut_up:
        if opts.quiet:
            level = logging.WARNING
        elif opts.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO

        logging.basicConfig(format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s", level=level)

        logger.debug("Set logging level to %d", level)
        logger.info(banner)
        logger.info("detk version: %s", __version__)


def make_cli_count_obj(args, raw=False):
    """
    The :class:`CountMatrix` of a command's ``counts_fn``, with its
    ``cov_fn`` and ``design`` when the command takes them.

    The counts are checked as read, before the column data selects or
    reorders any sample (:func:`check_counts`, DETK-0830): a repeated sample
    header or feature ID always raises :class:`CountsError`; with *raw*, for a
    command that needs raw counts, so does a negative count or a zero-depth
    sample.
    """
    counts_fn, cov_fn, design = (getattr(args, n, None) for n in ("counts_fn", "cov_fn", "design"))
    logger.info("constructing counts matrix from %s and %s", counts_fn, cov_fn)
    logger.info("design is %s", design)
    count_obj = CountMatrixFile(
        counts_fn,
        cov_fn,
        design=design,
        strict=getattr(args, "strict", False),
        check="raw" if raw else "ids",
    )

    logger.info("counts matrix created successfully")

    return count_obj


def write_output(df, args):

    output = args.output
    if output == "stdout":
        f = sys.stdout
        logging.info("writing result to stdout")
    else:
        f = output
        logging.info("writing result to %s", f)

    df.to_csv(f, sep=args.out_delim)

    logging.info("finished writing output")


class InvalidDesignException(Exception):
    pass


class SampleMismatchException(Exception):
    pass


def _sample_list(names, most=5):
    "*names* for a one-line message: the first *most*, then how many more"
    names = [str(n) for n in names]
    shown = ", ".join(names[:most])
    return shown + (f" and {len(names) - most} more" if len(names) > most else "")


class CountMatrix:
    """
    A counts matrix (features in rows, samples in columns) and, optionally,
    its sample information *column_data* (samples in rows) and a *design*.

    The counts columns and the column data rows must name the same samples
    (DETK-0600): a sample in only one of them raises
    :class:`SampleMismatchException` naming it. The column data is matched
    to the counts by name, so its rows may come in any order, unless
    *strict*, which requires the same order too. *subset* keeps the samples
    in both instead, in the counts' order; it is what ``detk-util tidy``
    does, the explicit way to subset the two.
    """

    def __init__(self, counts, column_data=None, design=None, strict=False, subset=False):

        self.strict = strict

        if column_data is not None:
            in_counts, in_column_data = set(counts.columns), set(column_data.index)
            counts_only = [s for s in counts.columns if s not in in_column_data]
            column_data_only = [s for s in column_data.index if s not in in_counts]
            if (counts_only or column_data_only) and not subset:
                parts = []
                if counts_only:
                    parts.append(f"in the counts only: {_sample_list(counts_only)}")
                if column_data_only:
                    parts.append(
                        f"in the sample information only: {_sample_list(column_data_only)}"
                    )
                raise SampleMismatchException(
                    "the counts columns and the sample information rows must name the "
                    "same samples; " + "; ".join(parts) + " (to subset the two to the "
                    "samples in both, run detk-util tidy first)"
                )
            if strict and list(column_data.index) != list(counts.columns):
                raise SampleMismatchException(
                    "--strict requires the counts columns and the sample information "
                    "rows to name the same samples in the same order"
                )

            common_names = counts.columns.intersection(column_data.index, sort=False)

            logger.debug("common names between counts and column data:\n %s", pformat(common_names))

            # fix to a "no memory available" issue (old Bitbucket tracker) when matrices are
            # empty
            if len(common_names) < 2:
                raise SampleMismatchException(
                    "No sample names were found to be in "
                    "common between the counts and column data or specified sample "
                    "names. Check that the first column of the column_data matrix "
                    "and the first row of the counts matrix contain at least 2 values "
                    "in common"
                )

            counts = counts[common_names]
            column_data = column_data.loc[common_names]

        # if the design is provided, it must have a 'counts' term somewhere
        if design is not None and "counts" not in design:
            raise InvalidDesignException(
                'The term "counts" must exist on at least one side of the CountsMatrix design'
            )

        # set the things
        self.counts = counts
        logger.info("counts matrix has shape: %s", self.counts.shape)

        self.column_data = column_data
        if column_data is not None:
            logger.info("column data matrix has shape: %s", self.column_data.shape)
        else:
            logger.info("column data was not provided")

        # set the design no matta wat
        self._design_matrix = None
        self.design = self._original_design = design
        logger.info("design: %s", design)
        logger.debug("full design:\n %s", pformat(self.design_matrix))

        # TODO this is not yet implemented or thought out
        # members to keep track of count mutations
        self.transformed = {}
        self.normalized = {}

    @property
    def column_data(self):
        return self._column_data

    @column_data.setter
    def column_data(self, column_data):
        # if column_data does not have a counts column, add one with trivial values
        # so things work
        if column_data is not None and "counts" not in column_data:
            column_data["counts"] = 0

        self._column_data = column_data

        # update the design matrix by setting the design to itself
        self.design = self.design

    @property
    def design(self):
        if hasattr(self, "design_matrix") and self.design_matrix is not None:
            return self.design_matrix.design
        if hasattr(self, "_design"):
            return self._design
        return None

    @design.setter
    def design(self, design):
        self._design = design
        if design is not None and self.column_data is not None:
            try:
                self.design_matrix = DesignMatrix(design, self.column_data)
            except FormulaParseError as e:
                # each FormulaParseError names its cause: a term that is not
                # a column, a level the data lacks, a number-like term
                # (DETK-0190), or formula syntax detk could not read
                raise InvalidDesignException(
                    "Invalid design: " + "; ".join(str(a) for a in e.args)
                ) from e

            # check if the full design matrix has lost any rows due to
            # missing data
            if self.design_matrix.full_matrix.index.size != self.column_data.index.size:
                msg = (
                    "The full design matrix rows do not match the input column "
                    "data matrix, likely due to some missing fields. "
                    f"# design matrix rows: {self.design_matrix.full_matrix.index.size}, # column data rows: {self.column_data.shape[0]}. "
                )

                if self.strict:
                    raise SampleMismatchException(msg + "Aborting.")
                else:
                    warnings.warn(
                        msg + "Adjusting the counts matrix and column data to fit.", stacklevel=2
                    )
                    logger.warning(msg + "Adjusting the counts matrix and column data to fit.")
                    logger.warning("counts shape prior to fit: %s", self.counts.shape)
                    logger.warning("column data prior to fit: %s", self.column_data.shape)
                    self.counts = self.counts[self.design_matrix.full_matrix.index]
                    self._column_data = self.column_data.loc[self.design_matrix.full_matrix.index]

                    logger.warning("counts shape after fit: %s", self.counts.shape)
                    logger.warning("column data after fit: %s", self._column_data.shape)

        elif design is not None and self.column_data is None:
            raise InvalidDesignException(
                "There must be column data associated with a "
                "CountMatrix object before specifying a design"
            )

    @property
    def design_matrix(self):
        return self._design_matrix

    @design_matrix.setter
    def design_matrix(self, design_matrix):
        self._design_matrix = design_matrix

    @property
    def sample_names(self):
        return self.counts.columns

    @sample_names.setter
    def sample_names(self, value):
        try:
            self.counts = self.counts[value]
        except Exception as e:
            raise Exception(
                "Sample names provided that are not contained in the counts matrix"
            ) from e

    @property
    def feature_names(self):
        return self.counts.index

    @feature_names.setter
    def feature_names(self, value):
        try:
            self.counts = self.counts.loc[value]
        except Exception as e:
            raise Exception(
                "Feature names provided that are not contained in the counts matrix"
            ) from e

    def copy(self):
        return deepcopy(self)

    def transform(self, transf):
        self.transformed[transf.__name__] = transf(self)

    def add_normalized(self, method="deseq2"):
        pass


# the compression pandas infers from a path's extension, in pandas' order
# (".tar.gz" before ".gz")
_COMPRESSION_EXTS = {
    ".tar": "tar",
    ".tar.gz": "tar",
    ".tar.bz2": "tar",
    ".tar.xz": "tar",
    ".gz": "gzip",
    ".bz2": "bz2",
    ".zip": "zip",
    ".xz": "xz",
    ".zst": "zstd",
}


# the delimiters a table's first line is sniffed for (comma, tab, semicolon,
# pipe, space); a first line with none of them is sniffed again from the
# first data lines (see _sniff), and otherwise is a one-column table. (The
# csv sniffer, left to any character, splits a bare list of IDs on a letter
# of its header: ``gene_id`` became ``g``, ``n``, ``_id``.)
SNIFF_DELIMITERS = ",\t;| "

# the separator a one-column table is read with: a control character that
# does not occur in text, so each line is one field
_ONE_COLUMN = "\x1f"


def sniff_delimiter(line):
    """
    Return the delimiter of the table whose first line is *line*, one of
    ``SNIFF_DELIMITERS``, or None when the line has none of them, as in a
    one-column table such as a bare list of IDs.
    """
    try:
        sep = csv.Sniffer().sniff(line, delimiters=SNIFF_DELIMITERS).delimiter
    except csv.Error:
        return None
    if sep == " ":
        # the sniffer prefers space to pipe, so ``g|sample 1|sample 2`` was
        # split on its spaces: a delimiter other than space that splits the
        # line outside quotes wins over space
        for other in SNIFF_DELIMITERS.replace(" ", ""):
            if len(next(csv.reader([line], delimiter=other))) > 1:
                return other
    return sep


def _rewindable(f):
    """
    Return *f* in a form that can be read more than once, and the
    compression to read it with: a file-like object, a URL pandas would
    fetch (``http``, ``https``, ``ftp``, ``file``, ``s3`` and the other
    fsspec protocols) or a local path that is not a regular file (a FIFO,
    ``/dev/stdin``, a shell process substitution ``<(zcat f.gz)``) is read
    once into memory, so a URL is fetched once; anything else (a regular
    file, an unexpanded ~, a missing path) is returned as it is, for pandas.
    """
    if hasattr(f, "read"):
        content = f.read()
        return (io.StringIO(content) if isinstance(content, str) else io.BytesIO(content)), "infer"
    name = os.fspath(f)
    is_url = pandas.io.common.is_url(name) or pandas.io.common.is_fsspec_url(name)
    if is_url or (os.path.exists(name) and not os.path.isfile(name)):
        # the buffer has no name, so take the compression from the path's
        compression = next(
            (method for ext, method in _COMPRESSION_EXTS.items() if name.lower().endswith(ext)),
            None,
        )
        if is_url:
            # pandas' own opener decompresses as pandas would read the URL:
            # by the name, and undoing an HTTP Content-Encoding without
            # decompressing twice, so the buffer is plain
            with pandas.io.common.get_handle(name, "rb", compression="infer", is_text=False) as h:
                return io.BytesIO(h.handle.read()), None
        with open(name, "rb") as fh:
            return io.BytesIO(fh.read()), compression
    return f, "infer"


def _first_lines(f, compression, skiprows=None, n=1):
    """
    The first *n* lines of *f* (after *skiprows*), as written, padded with
    '' when it has fewer.
    """
    if hasattr(f, "seek"):
        f.seek(0)
    try:
        lines = pandas.read_csv(
            f,
            sep=_ONE_COLUMN,
            engine="python",
            header=None,
            nrows=n,
            skiprows=skiprows,
            quoting=csv.QUOTE_NONE,
            dtype=str,
            keep_default_na=False,
            compression=compression,
        )
    except pandas.errors.EmptyDataError:
        lines = pandas.DataFrame()
    found = [_ONE_COLUMN.join(row) for row in lines.itertuples(index=False)]
    return found + [""] * (n - len(found))


# how many data lines the delimiter sniffed from a data line must split
# alike (DETK-0320)
_SNIFF_DATA_LINES = 10


class RaggedTableError(ValueError):
    """
    A table whose header has one field over data lines that split unalike
    on a delimiter (see :func:`_sniff`): malformed, so it is an error rather
    than a one-column table that silently loses the rows that split.
    """


# the delimiters by name, for messages
_DELIMITER_NAMES = {",": "comma", "\t": "tab", ";": "semicolon", "|": "pipe", " ": "space"}


def _source_name(f):
    "The name of the table *f* (a path, URL or file-like object) for messages"
    if hasattr(f, "read"):
        return str(getattr(f, "name", "<stream>"))
    return os.fspath(f)


def _sniff(f, compression, skiprows=None, name=None):
    """
    The delimiter of *f*, as :func:`_rewindable` returned it, or None for a
    one-column table: sniffed from its first line, or, when that line has
    none of ``SNIFF_DELIMITERS``, from its first data lines. R's
    ``write.table`` leaves out the header cell over the row names, so a
    one-column sheet is ``"condition"`` over ``"S1","a"``: the header has no
    delimiter, its rows do.

    A data line's delimiter counts only when (DETK-0320) it splits the line
    outside quotes and is not space, or is space and the line's first field
    is quoted, as R's default ``write.table`` writes it (``"S1" "a"``). The
    first data line (up to ``_SNIFF_DATA_LINES``) with a delimiter that
    counts gives the delimiter, and the first data lines must all split on
    it, outside quotes, into the same number of fields: then the table is
    read with it. When they split unalike (``condition`` over ``S1,a`` and
    ``S2``), the table is malformed and :class:`RaggedTableError` is raised,
    naming the file *name*, the delimiter and the first two lines whose
    field counts differ (release/ragged-sheet). When no data line has a
    delimiter that counts, the table is one column, so a list of IDs with
    spaces in them, quoted (``"sample 1"``) or not (``ctrl 1``), stays a
    list of IDs.
    """
    header, *data = _first_lines(f, compression, skiprows, n=1 + _SNIFF_DATA_LINES)
    sep = sniff_delimiter(header)
    if sep is not None:
        return sep
    data = [line for line in data if line]
    for line in data:
        sep = sniff_delimiter(line)
        if sep is None or (sep == " " and not line.startswith('"')):
            continue
        if len(next(csv.reader([line], delimiter=sep))) > 1:
            break
    else:
        return None
    widths = [len(fields) for fields in csv.reader(data, delimiter=sep)]
    differ = next((i for i, width in enumerate(widths) if width != widths[0]), None)
    if differ is None:
        return sep
    # the header is line 1, after the rows skipped
    first = 2 + (skiprows if isinstance(skiprows, int) else 0)

    def fields(n):
        return "1 field" if n == 1 else f"{n} fields"

    raise RaggedTableError(
        f"{name if name is not None else _source_name(f)}: the header {header!r} has one"
        f" field and its data lines split unalike on {_DELIMITER_NAMES[sep]}:"
        f" line {first} {data[0]!r} has {fields(widths[0])},"
        f" line {first + differ} {data[differ]!r} has {fields(widths[differ])};"
        " quote a field that holds the delimiter, or give every line the same fields"
    )


def read_delimited(f, **kwargs):
    """
    Read the delimited table *f* with pandas.read_csv, passing on *kwargs*,
    its delimiter sniffed from its first line among ``SNIFF_DELIMITERS``
    (comma, tab, semicolon, pipe, then space). A first line with none of them
    is sniffed again from the first data lines, for R's layout of a
    one-column sheet (``"condition"`` over ``"S1","a"``; see :func:`_sniff`
    for when a data line's delimiter counts); when none has one, the table
    is read as one column, so a bare list of IDs is not split on a letter of
    its header. When one does but the first data lines split unalike on it
    (``condition`` over ``S1,a`` and ``S2``), the table is malformed:
    :class:`RaggedTableError` is raised, naming the file, the delimiter and
    the first two lines whose field counts differ, and a detk command exits
    1 with that message. *f* is a path or URL (compression
    is inferred from the name) or a file-like object; a URL, or a path that
    can be read only once, is read once into memory.
    """
    name = _source_name(f)
    f, compression = _rewindable(f)
    sep = _sniff(f, compression, kwargs.get("skiprows"), name)
    return _read_with(f, compression, sep, **kwargs)


def _read_with(f, compression, sep, **kwargs):
    """
    Read *f*, as :func:`_rewindable` returned it, with the sniffed
    delimiter *sep* (None for one column).
    """
    if hasattr(f, "seek"):
        f.seek(0)
    return pandas.read_csv(
        f, sep=sep or _ONE_COLUMN, engine="python", compression=compression, **kwargs
    )


def read_id_table(f):
    """
    Read a delimited table (the delimiter is sniffed, see
    :func:`read_delimited`, which also says when a one-field header over
    ragged rows raises :class:`RaggedTableError`) whose first column holds IDs, such as a counts
    file (feature IDs) or a sample-info file (sample names), into a
    pandas.DataFrame indexed by that column.

    The IDs are read as text, exactly as written, so ``007`` stays ``007``
    rather than becoming the number 7, and matches the same ID in another
    file; the other columns are typed as pandas infers them, so counts stay
    numeric. Empty IDs and pandas' missing-value tokens (``NA``, ``NaN``, ...)
    are missing, as before. *f* is a path or URL (compression is inferred
    from the name) or a file-like object. A URL, or a path that can be read
    only once, such as a FIFO, ``/dev/stdin`` or a shell process
    substitution ``<(zcat f.gz)``, is read once into memory.
    """
    source = f
    # the table is parsed twice below, so make it rewindable (and fetch a
    # URL) once here, and sniff its delimiter once
    f, compression = _rewindable(f)
    sep = _sniff(f, compression, name=_source_name(source))

    def read(**kwargs):
        return _read_with(f, compression, sep, **kwargs)

    table = read(index_col=0)
    # A second parse reads the first field of every line as text; below the
    # header line, those are the IDs as written. (pandas applies no dtype to
    # the index column when the header leaves its name empty or omits its
    # field, so the IDs cannot come from a typed parse of the index.)
    ids = read(header=None, usecols=[0], dtype=str).iloc[1:, 0]
    if len(ids) == len(table):
        table.index = pandas.Index(ids.to_numpy(), name=table.index.name)
    else:
        logger.warning("could not read the IDs of %s as text; pandas typed them", source)
    # each column's name as the header line writes it, by its name in the
    # table, since pandas renames a repeated name A to A.1 (for
    # check_counts); a mapping, so it holds after the columns are selected
    # or reordered
    header = read(header=None, nrows=1, dtype=str, keep_default_na=False).iloc[0].tolist()
    if len(header) == len(table.columns) + 1:
        header = header[1:]
    if len(header) == len(table.columns):
        table.attrs[COLUMNS_AS_WRITTEN] = dict(zip(map(str, table.columns), header))
    return table


# the key in a table's ``attrs`` under which read_id_table keeps a mapping
# of its column names to the names as the header line writes them
COLUMNS_AS_WRITTEN = "detk_columns_as_written"


class CountsError(ValueError):
    """
    A counts matrix that cannot be counts (see :func:`check_counts`): a bad
    input file, so a detk command exits 1 with its message (DETK-0601).
    """


def _more(offenders, what):
    "' (and n more <what>s)' for the offenders after the first, or ''"
    n = len(offenders) - 1
    return f" (and {n} more {what}{'s' if n > 1 else ''})" if n else ""


def check_counts(counts, name="counts", values=True):
    """
    Raise :class:`CountsError` if the counts matrix *counts* (a
    pandas.DataFrame, features in rows and samples in columns, as
    :func:`read_id_table` reads it) is malformed, naming the file *name* and
    the first offender:

    - a sample named more than once in the header; read from the header as
      written (``read_id_table`` keeps, in ``attrs``, each column's name as
      written by its name in the table), since pandas renames a repeated
      name ``A`` to ``A.1``; a column not in that mapping goes by its name
    - a feature ID listed more than once
    - with *values* (for a command that needs raw counts; a normalized or
      transformed matrix may hold either):

      - a negative count
      - a sample with no numeric value (all missing or not numbers)
      - a sample whose counts sum to 0 (zero depth)

    The checks run in that order, and the message names the first offender
    of the first that fails, and how many more of its kind there are.
    Positions are counted from 1 among the samples (columns after the
    feature IDs) and the features (rows after the header) of *counts*, so
    they are the file's when *counts* is the table as read (the commands
    check it before any sample is selected or reordered, DETK-0830).
    """
    as_written = counts.attrs.get(COLUMNS_AS_WRITTEN, {})
    columns = [as_written.get(str(c), str(c)) for c in counts.columns]
    seen = {}
    for i, sample in enumerate(columns):
        if sample in seen:
            repeats = pandas.Index(columns)[pandas.Index(columns).duplicated()]
            raise CountsError(
                f"{name}: sample {sample!r} is named more than once in the header"
                f" (sample columns {seen[sample] + 1} and {i + 1})"
                + _more(repeats, "repeated sample name")
            )
        seen[sample] = i

    dup = counts.index.duplicated()
    if dup.any():
        feature = counts.index[dup][0]
        rows = [i + 1 for i, f in enumerate(counts.index) if f == feature][:2]
        raise CountsError(
            f"{name}: feature {str(feature)!r} is listed more than once"
            f" (feature rows {rows[0]} and {rows[1]})"
            + _more(counts.index[dup], "repeated feature ID")
        )

    if not values:
        return

    values = counts.apply(pandas.to_numeric, errors="coerce")
    negative = values.lt(0).to_numpy().nonzero()
    if len(negative[0]):
        row, col = negative[0][0], negative[1][0]
        value = values.iat[row, col]
        if float(value).is_integer():
            value = int(value)
        raise CountsError(
            f"{name}: feature {str(counts.index[row])!r} in sample {str(columns[col])!r}"
            f" has a negative count, {value}" + _more(negative[0], "negative count")
        )

    blank = [str(columns[i]) for i, n in enumerate(values.notna().sum(axis=0)) if n == 0]
    if blank:
        raise CountsError(
            f"{name}: sample {blank[0]!r} has no numeric counts: its values are"
            " all missing or not numbers" + _more(blank, "sample")
        )

    empty = [str(columns[i]) for i, total in enumerate(values.sum(axis=0)) if total == 0]
    if empty:
        raise CountsError(
            f"{name}: sample {empty[0]!r} has no counts: its counts sum to 0"
            + _more(empty, "zero-depth sample")
        )


class CountMatrixFile(CountMatrix):
    """
    A :class:`CountMatrix` read from the counts file *count_f* (and the column
    data file *column_data_f*). With *check* ``"ids"`` or ``"raw"``, the
    counts are run through :func:`check_counts` as read, before the column
    data selects or reorders any sample: ``"ids"`` for the repeated sample
    header and feature ID checks only, ``"raw"`` for all of them. The
    default, ``None``, checks nothing, as in 1.0.0.
    """

    def __init__(self, count_f, column_data_f=None, design=None, check=None, **kwargs):

        counts = read_id_table(count_f)
        if check is not None:
            if check not in ("ids", "raw"):
                raise ValueError(f"check must be None, 'ids' or 'raw', not {check!r}")
            check_counts(counts, _source_name(count_f), values=check == "raw")

        column_data = None
        if column_data_f is not None:
            column_data = read_id_table(column_data_f)

        CountMatrix.__init__(self, counts, column_data=column_data, design=design, **kwargs)


class DetkModule(OrderedDict):
    """
    Base class for all detk methods.

    Each function in detk is a subclass of this class.
    A module has the following properties:
    - ``name``: name of the module
    - ``params``: the module-dependent params passed to the module
    - ``output``: the output of the module in tabular form
    - ``properties``: properties and statistics about the module, used for
        formatting the results into a report

    All of these properties are JSON serializable, i.e. basic python
    types (int, float, str, bool, array, dict).
    """

    @property
    def json(self):
        """
        Format the module object into a form amenable to serializing with JSON
        for report creation. By default this returns all of the module-level
        fields except output. Override if additional serialization is needed.
        """
        return {"name": self.name, "params": self.params, "properties": self.properties}

    @property
    def params(self):
        """
        Override this method to return a dictionary with relevant parameters
        for the method.
        """
        return self.get("params", {})

    @property
    def output(self):
        """
        Override this method to return a tabular form of the output. Can be
        any rectangular-shaped object (i.e. list of lists, pandas.DataFrame,
        numpy array, etc)
        """
        return []

    @property
    def properties(self):
        """
        Override this method to return a dictionary with relevant properties
        for the method. These might include metadata or summary statistics of
        the output that would not otherwise be included. Primarily used in the
        construction of report sections.
        """
        return self.get("properties", {})

    @property
    def name(self):
        "Name of this stats object, by default the class name in all lower case"
        return self.__class__.__name__.lower()


# the module commands the umbrella ``detk <command>`` runs, with the one
# line its help lists for each
MODULE_COMMANDS = {
    "norm": "Normalize a counts matrix",
    "de": "Test for differential expression",
    "enrich": "Gene set enrichment of a differential expression result",
    "transform": "Transform a counts matrix (vst, rlog, plog, ...)",
    "filter": "Filter the rows of a counts matrix",
    "stats": "Summary statistics and diagnostics of a counts matrix",
    "outlier": "Find and treat outlier counts",
    "wrapr": "Run R scripts and check the R packages detk uses",
    "report": "Generate or clean the detk HTML report",
    "util": "Utilities: gather quantification files, convert IDs, ...",
}


def build_parser():
    "The parser of the umbrella ``detk``, for its help and its usage errors"
    parser = DetkParser(
        prog="detk",
        description=__doc__.split("\n\n")[0].strip(),
        usage="\n".join(f"detk {cmd} ..." for cmd in MODULE_COMMANDS)
        + "\ndetk completion <shell>\ndetk help",
        examples=[
            ("Normalize counts.csv with DESeq2 size factors", "detk norm deseq2 counts.csv"),
            ("The help of one command", "detk norm --help"),
        ],
    )
    subs = parser.add_subparsers(
        dest="command",
        metavar="<command>",
        required=True,
        title="positional arguments",
        help="The detk command to run, one of:",
    )
    for cmd, line in MODULE_COMMANDS.items():
        subs.add_parser(cmd, help=line, add_help=False)
    completion = subs.add_parser(
        "completion",
        # argparse would build its prog from detk's usage, which lists every command
        prog="detk completion",
        help="Print the shell completion script for bash, zsh or tcsh",
        description=COMPLETION_DESCRIPTION,
        examples=[
            ("Print the bash completion script", "detk completion bash"),
            ("Print the tcsh completion script", "detk completion tcsh"),
        ],
    )
    completion.add_argument(
        "shell",
        metavar="<shell>",
        choices=COMPLETION_SHELLS,
        help="The shell to print the completion script for",
    )
    subs.add_parser("help", help="Print this help", add_help=False)
    add_command_options(parser, "command")
    return parser


# shell completion (DETK-0032): scripts for every detk command, generated from
# the parsers by shtab when detk is built (de_toolkit/completions/_generate.py)
# and shipped in the package; ``detk completion <shell>`` prints one, so a user
# needs no shtab
COMPLETION_SHELLS = ("bash", "zsh", "tcsh")

COMPLETION_DESCRIPTION = """\
Print the shell completion script for every detk command (detk and each
detk-<command>) on stdout. Load it in the shell's startup file:

  bash   eval "$(detk completion bash)"         in ~/.bashrc
  zsh    eval "$(detk completion zsh)"          in ~/.zshrc, after compinit
  tcsh   detk completion tcsh > ~/.detk.tcsh    once, then in ~/.tcshrc:
         source ~/.detk.tcsh

The scripts ship with detk; printing one needs nothing else installed."""


def completion_script(shell):
    "The shipped completion script for *shell* (one of COMPLETION_SHELLS), as text"
    from importlib.resources import files

    return (files("de_toolkit.completions") / f"detk.{shell}").read_text()


@cli_main
def main(argv=sys.argv):
    """
    ``detk <command> ...`` runs the module command ``detk-<command> ...``;
    ``detk``, ``detk -h`` and ``detk help`` answer with the umbrella's help.
    """
    argv = list(argv)
    if len(argv) > 1 and argv[1] in MODULE_COMMANDS:
        # the module commands expect an argv[0] of the form detk-<command>
        import importlib

        module = importlib.import_module(f"de_toolkit.{argv[1]}")
        return module.main([f"detk-{argv[1]}"] + argv[2:])

    parser = build_parser()
    args = parse_cli(parser, argv)
    if args.command == "help":
        parser.print_help()
    elif args.command == "completion":
        try:
            sys.stdout.write(completion_script(args.shell))
            sys.stdout.flush()
        except BrokenPipeError:
            # the reader stopped early (detk completion bash | head): not a
            # failure; stdout goes to devnull so the exit flush is quiet
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())


if __name__ == "__main__":
    main()
