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
from collections import OrderedDict
from copy import deepcopy
import csv
import io
import logging
import os
import pandas
from pprint import pformat
import sys
import warnings
from .patsy_lite import DesignMatrix, PatsyLiteParseError
from .version import __version__

# process start time, recorded at import for provenance (a CLI invocation
# imports this module at startup, so this approximates the run's startTime)
from datetime import datetime, UTC

_PROCESS_START = datetime.now(UTC)

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

_cli_version = f"""\
detk version: {__version__}\n
"""

# the docopt common options, for the commands not yet on argparse
# (release/cli-migrate s3 converts them and removes this)
_cli_common_opts = """\

Common options:
    -d CHAR --out-delim=CHAR  Delimiter to use for output file [default: ,]
    --report-dir=DIR          Specify the report directory [default: ./detk_report]
    --no-report               Do not generate the HTML report
    --version                 Print out detk version and exit
    -v --verbose              Make log output verbose
    -q --quiet                Turn off all logging except warnings and errors
    --shut-up                 Turn off ALL logging
"""


def _cli_doc(src):
    "Add the common command line arguments to the given *src* docopt string"
    return _cli_version + src + _cli_common_opts


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

    def __init__(self, *args, examples=(), add_help=True, **kwargs):
        kwargs.setdefault("formatter_class", DetkHelpFormatter)
        super().__init__(*args, add_help=False, **kwargs)
        self.examples = list(examples)
        if add_help:
            self.add_argument("-h", "--help", action="help", help="Print this help and exit")
        self.register("action", "store", _StoreOnce)
        self.register("action", None, _StoreOnce)
        self.register("action", "store_true", _StoreTrueOnce)

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
        left to argparse to report.
        """
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
        return "\n".join(sections)

    def error(self, message):
        "Print the usage and the error on stderr and exit 2 (DETK-0031)"
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\nRun '{self.prog} --help' for help.\n")


def add_common_options(parser):
    """
    Add the options every detk command shares to *parser*, in their own
    help section, "common options".
    """
    group = parser.add_argument_group("common options")
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
    if "--" in args:
        # docopt took "--" for an argument no usage declared; it is not an
        # end-of-options marker (pinned in tests/cli/test_cli_behaviours.py)
        parser.error("unrecognized arguments: --")
    leaf, rest = parser, args
    subs = parser._subcommands()
    if subs is not None and args and args[0] in subs.choices:
        leaf, rest = subs.choices[args[0]], args[1:]
    unknown = [a for a in rest if leaf.unknown_option(a)]
    if unknown:
        # name an unknown option before a missing positional, as docopt did
        # (argparse would report only the missing positional)
        leaf.error("unrecognized arguments: " + " ".join(unknown))
    namespace = parser.parse_args(args)
    namespace.__dict__.pop("_detk_seen", None)
    return namespace


def _arg(args, name, default=None):
    """
    The argument *name* (``counts_fn``, ``out_delim``) from a parsed command
    line: an argparse Namespace, or the dict docopt returns, for the
    commands not yet on argparse (release/cli-migrate s3 removes that).
    """
    if isinstance(args, argparse.Namespace):
        return getattr(args, name, default)
    for key in (f"--{name.replace('_', '-')}", f"<{name}>"):
        if key in args:
            return args[key]
    return default


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
    if not _arg(opts, "shut_up"):
        if _arg(opts, "quiet"):
            level = logging.WARNING
        elif _arg(opts, "verbose"):
            level = logging.DEBUG
        else:
            level = logging.INFO

        logging.basicConfig(format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s", level=level)

        logger.debug("Set logging level to %d", level)
        logger.info(banner)
        logger.info("detk version: %s", __version__)


def make_cli_count_obj(args):
    counts_fn, cov_fn, design = (_arg(args, n) for n in ("counts_fn", "cov_fn", "design"))
    logger.info("constructing counts matrix from %s and %s", counts_fn, cov_fn)
    logger.info("design is %s", design)
    try:
        count_obj = CountMatrixFile(
            counts_fn, cov_fn, design=design, strict=_arg(args, "strict", False)
        )
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    logger.info("counts matrix created successfully")

    return count_obj


def write_output(df, args):

    output = _arg(args, "output")
    if output == "stdout":
        f = sys.stdout
        logging.info("writing result to stdout")
    else:
        f = output
        logging.info("writing result to %s", f)

    df.to_csv(f, sep=_arg(args, "out_delim", ","))

    logging.info("finished writing output")


class InvalidDesignException(Exception):
    pass


class SampleMismatchException(Exception):
    pass


class CountMatrix:
    def __init__(self, counts, column_data=None, design=None, strict=False):

        self.strict = strict

        if column_data is not None:
            # line up the sample names from the column_data and counts matrices
            if strict and (
                len(column_data.index) != len(counts.columns)
                or not all(column_data.index == counts.columns)
            ):
                raise SampleMismatchException(
                    "When *strict* is supplied, the columns "
                    "of the counts file must correspond exactly to the row names in the "
                    "column_data matrix"
                )
            else:
                common_names = counts.columns.intersection(column_data.index)

                logger.debug(
                    "common names between counts and column data:\n %s", pformat(common_names)
                )

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
            except PatsyLiteParseError as e:
                raise InvalidDesignException(
                    f"Invalid design, patsy lite could not parse {e.args}"
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
# pipe, space); a first line with none of them is a one-column table. (The
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


def _first_line(f, compression, skiprows=None):
    "The first line of *f* (after *skiprows*), as written, or '' when there is none."
    if hasattr(f, "seek"):
        f.seek(0)
    try:
        line = pandas.read_csv(
            f,
            sep=_ONE_COLUMN,
            engine="python",
            header=None,
            nrows=1,
            skiprows=skiprows,
            quoting=csv.QUOTE_NONE,
            dtype=str,
            keep_default_na=False,
            compression=compression,
        )
    except pandas.errors.EmptyDataError:
        return ""
    return _ONE_COLUMN.join(line.iloc[0]) if len(line) else ""


def read_delimited(f, **kwargs):
    """
    Read the delimited table *f* with pandas.read_csv, passing on *kwargs*,
    its delimiter sniffed from its first line among ``SNIFF_DELIMITERS``
    (comma, tab, semicolon, pipe, then space). A first line with none of them
    makes a one-column table, read as one column, so a bare list of IDs is
    not split on a letter of its header. *f* is a path or URL (compression
    is inferred from the name) or a file-like object; a URL, or a path that
    can be read only once, is read once into memory.
    """
    f, compression = _rewindable(f)
    sep = sniff_delimiter(_first_line(f, compression, kwargs.get("skiprows")))
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
    :func:`read_delimited`) whose first column holds IDs, such as a counts
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
    sep = sniff_delimiter(_first_line(f, compression))

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
    return table


class CountMatrixFile(CountMatrix):
    def __init__(self, count_f, column_data_f=None, design=None, **kwargs):

        counts = read_id_table(count_f)

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
        usage="\n".join(f"detk {cmd} ..." for cmd in MODULE_COMMANDS) + "\ndetk help",
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
    subs.add_parser("help", help="Print this help", add_help=False)
    add_version_option(parser.add_argument_group("common options"))
    return parser


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


if __name__ == "__main__":
    main()
