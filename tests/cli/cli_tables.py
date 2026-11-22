"""
What every ``detk-*`` command line means today, one table per entry point.

These are the expectations the pin tests check, written without reference
to any parser: each subcommand's positionals and options (name, short form,
metavar, default, choices), the command lines that need more than the
generated cases, and the command lines each command rejects. The tests in
this directory generate from them a command line for every positional,
every option in its short and long forms and every default, and check
``--help`` states the same facts.

Values are written as on the command line (``"20"``, not ``20``). An
option's ``default`` is the value the command acts on when the option is not
given; for a flag it is False. ``metavar`` is None for a flag. A ``repeat``
option may be given more than once and yields the list of its values; a
``required`` one must be given. An ``after_dashdash`` positional is the
words after ``--`` (detk-util record's command), never parsed as detk's.

A change to the command line interface is a change to these tables
(DETK-0001: the CLI is the 1.0 promise; DETK-0025 Option B: help promises
these facts, not its wording). The parser itself is reached only through
``cli_adapter.py``.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Opt:
    long: str
    short: str | None = None
    metavar: str | None = None
    default: object = None
    choices: tuple = ()
    repeat: bool = False
    required: bool = False

    @property
    def key(self):
        return self.long[2:].replace("-", "_")

    @property
    def flag(self):
        return self.metavar is None

    @property
    def unset(self):
        "The value the command acts on when the option is not given"
        return False if self.flag else self.default


@dataclass(frozen=True)
class Pos:
    name: str
    optional: bool = False
    multi: bool = False
    after_dashdash: bool = False


@dataclass(frozen=True)
class Line:
    "A command line (after the entry point name) and the arguments it yields beyond the defaults"

    argv: tuple
    args: dict
    why: str = ""


@dataclass(frozen=True)
class Bad:
    """
    A command line the command rejects: exit 2, a usage error (DETK-0031),
    with each of *names* on stderr. *stage* is ``parse`` when the parser rejects it, ``run`` when
    the command does, after parsing.
    """

    argv: tuple
    names: tuple
    why: str = ""
    stage: str = "parse"


@dataclass(frozen=True)
class Sub:
    name: str | None
    positionals: tuple = ()
    options: tuple = ()
    lines: tuple = ()
    bad: tuple = ()
    # long names of the common options (COMMON) this subcommand does not take
    without_common: tuple = ()


@dataclass(frozen=True)
class Command:
    prog: str
    subcommands: tuple
    bad: tuple = ()

    @property
    def module(self):
        return self.prog.removeprefix("detk-")

    def sub(self, name):
        return next(s for s in self.subcommands if s.name == name)


# options every command shares, added to each subcommand by common.add_common_options
COMMON = (
    Opt("--out-delim", "-d", "CHAR", ","),
    Opt("--report-dir", None, "DIR", "./detk_report"),
    Opt("--no-report"),
    Opt("--verbose", "-v"),
    Opt("--quiet", "-q"),
    Opt("--shut-up"),
)

# common options help lists that are not arguments a command acts on:
# --version prints the version and exits; it is not handed to the command
COMMON_HELP_ONLY = (Opt("--version"),)

COUNTS = Pos("counts_fn")
OUTPUT = Opt("--output", "-o", "FILE", "stdout")

# ---------------------------------------------------------------- detk-norm
NORM = Command(
    "detk-norm",
    (
        Sub(
            "deseq2",
            (COUNTS,),
            (OUTPUT, Opt("--size-factors", None, "FILE")),
        ),
        Sub("library", (COUNTS,), (OUTPUT,)),
        Sub("fpkm", (COUNTS, Pos("lengths_fn")), (OUTPUT,)),
        Sub("cpm", (COUNTS,), (OUTPUT,)),
        Sub("tpm", (COUNTS, Pos("lengths_fn")), (OUTPUT,)),
    ),
)

# ------------------------------------------------------------------ detk-de
_DE_POS = (Pos("design"), COUNTS, Pos("cov_fn"))
_DE_SHARED = (
    OUTPUT,
    Opt("--routput-dir", None, "DIR"),
    Opt("--rda", None, "FILE"),
    Opt("--strict"),
)
# a design starting with "-" is the design, with options before or after
# it, not an unknown option: the command then gives DETK-0190's message
_DE_DASH_DESIGN = tuple(
    Line(
        argv,
        {"design": design, "counts_fn": "counts.csv", "cov_fn": "cov.csv", **extra},
        why,
    )
    for argv, design, extra, why in (
        (
            ("-2.5 ~ counts", "counts.csv", "cov.csv"),
            "-2.5 ~ counts",
            {},
            "a design starting with - is the design",
        ),
        (
            ("-2.5~counts", "counts.csv", "cov.csv"),
            "-2.5~counts",
            {},
            "a design starting with - and without spaces is the design",
        ),
        (
            ("-o", "out.csv", "-2.5 ~ counts", "counts.csv", "cov.csv", "--strict"),
            "-2.5 ~ counts",
            {"output": "out.csv", "strict": True},
            "options parse before and after a design starting with -",
        ),
        (
            ("-o~/out.csv", "-2.5 ~ counts", "counts.csv", "cov.csv"),
            "-2.5 ~ counts",
            {"output": "~/out.csv"},
            "an option with its value attached is still the option, with a ~ in it",
        ),
    )
)
DE = Command(
    "detk-de",
    (
        Sub(
            "deseq2",
            _DE_POS,
            _DE_SHARED
            + (
                Opt("--norm-counts"),
                Opt("--last-term-only"),
                Opt("--gene-wise-disp"),
                Opt("--cores", None, "N", "none"),
            ),
            lines=_DE_DASH_DESIGN,
            bad=(
                Bad(
                    ("--bogus", "-2.5 ~ counts", "counts.csv", "cov.csv"),
                    ("--bogus",),
                    "an unknown option is still one beside a design starting with -",
                ),
            ),
        ),
        Sub(
            "firth",
            _DE_POS,
            _DE_SHARED + (Opt("--standardize"), Opt("--cores", None, "N", "none")),
            lines=_DE_DASH_DESIGN,
        ),
    ),
)

# -------------------------------------------------------------- detk-enrich
ENRICH = Command(
    "detk-enrich",
    (
        Sub(
            "fgsea",
            (Pos("gmt_fn"), Pos("result_fn")),
            (
                OUTPUT,
                Opt("--cores", "-p", "N"),
                Opt("--idcol", "-i", "COL", "0"),
                Opt("--statcol", "-c", "COL"),
                Opt("--ascending", "-a"),
                Opt("--abs"),
                Opt("--filter-unannotated"),
                Opt("--minSize", None, "N", "15"),
                Opt("--maxSize", None, "N", "500"),
                Opt("--nperm", None, "N", "10000"),
                Opt("--multilevel"),
                Opt("--routput-dir", None, "DIR"),
                Opt("--rda", None, "FILE"),
            ),
        ),
    ),
)

# ----------------------------------------------------------- detk-transform
TRANSFORM = Command(
    "detk-transform",
    (
        Sub(
            "plog",
            (COUNTS,),
            (
                Opt("--pseudocount", "-c", "N", "1"),
                Opt("--base", "-b", "N", "10"),
                OUTPUT,
            ),
        ),
        Sub("vst", (COUNTS,), (OUTPUT, Opt("--rda", None, "FILE"))),
        Sub(
            "rlog",
            (COUNTS, Pos("design", optional=True), Pos("cov_fn", optional=True)),
            (
                OUTPUT,
                Opt("--rda", None, "FILE"),
                Opt("--strict"),
                Opt("--blind", None, "BOOL"),
            ),
            # --blind BOOL is True or False in any case, parsed to a bool;
            # not given it is None, which the command runs as blind (DETK-0081)
            lines=tuple(
                Line(
                    ("counts.csv", "--blind", token, "counts ~ group", "cov.csv"),
                    {
                        "counts_fn": "counts.csv",
                        "design": "counts ~ group",
                        "cov_fn": "cov.csv",
                        "blind": value,
                    },
                    f"--blind {token} is {value}",
                )
                for token, value in (
                    ("True", True),
                    ("true", True),
                    ("TRUE", True),
                    ("False", False),
                    ("false", False),
                    ("FALSE", False),
                )
            )
            + (
                Line(
                    ("counts.csv", "--blind=True"),
                    {"counts_fn": "counts.csv", "blind": True},
                    "a blind rlog needs no design",
                ),
                Line(
                    ("counts.csv", "-2.5 ~ counts", "--blind", "False", "cov.csv"),
                    {
                        "counts_fn": "counts.csv",
                        "design": "-2.5 ~ counts",
                        "cov_fn": "cov.csv",
                        "blind": False,
                    },
                    "a design starting with - is the design",
                ),
            ),
            bad=(
                Bad(
                    ("counts.csv", "counts ~ group"),
                    ("cov_fn",),
                    "rlog takes both or neither of <design> and <cov_fn> (DETK-0033)",
                ),
                Bad(
                    ("counts.csv", "--blind", "maybe"),
                    ("--blind", "maybe"),
                    "--blind takes True or False (DETK-0081)",
                ),
                Bad(
                    ("counts.csv", "--blind", "1"),
                    ("--blind",),
                    "--blind takes True or False, not 1 (DETK-0081)",
                ),
                Bad(
                    ("counts.csv", "--blind", "False"),
                    ("<design>", "<cov_fn>"),
                    "a non-blind rlog needs <design> and <cov_fn> (DETK-0081)",
                ),
            ),
        ),
    ),
)

# -------------------------------------------------------------- detk-filter
FILTER = Command(
    "detk-filter",
    (
        Sub(
            None,
            (Pos("command"), COUNTS, Pos("cov_fn", optional=True)),
            (Opt("--output", "-o", "FILE", "stdout"),),
            lines=(
                Line(
                    ("mean(flag[1]) > 10", "counts.csv", "cov.csv"),
                    {
                        "command": "mean(flag[1]) > 10",
                        "counts_fn": "counts.csv",
                        "cov_fn": "cov.csv",
                    },
                    "a group may be a number or true/false, matched as written in a column of "
                    "numbers or booleans; a group its column does not have, as in cond[Z], is "
                    "a usage error when the command runs (tests/filter/test_filter_groups.py)",
                ),
            ),
            bad=(
                Bad(
                    ("mean(all) > 10", "counts.csv", "--column-data=cov.csv"),
                    ("--column-data",),
                    "--column-data is removed; the column data is the positional <cov_fn> (DETK-0030)",
                ),
            ),
        ),
    ),
)

# --------------------------------------------------------------- detk-stats
_STATS_OUT = (
    Opt("--output", "-o", "FILE", "stdout"),
    Opt("--format", "-f", "FMT", "csv", choices=("csv", "table")),
)
_STATS_DIST = (
    Opt("--bins", None, "N", "20"),
    Opt("--log"),
    Opt("--density"),
)
STATS = Command(
    "detk-stats",
    (
        Sub(
            "summary",
            (COUNTS, Pos("cov_fn", optional=True)),
            (
                Opt("--color-col", None, "COL"),
                Opt("--bins", None, "N", "20"),
                Opt("--log"),
                Opt("--density"),
            )
            + _STATS_OUT,
            bad=(
                Bad(
                    ("counts.csv", "--column-data=cov.csv"),
                    ("--column-data",),
                    "--column-data is removed; the column data is the positional <cov_fn> (DETK-0030)",
                ),
            ),
        ),
        Sub(
            "basestats",
            (COUNTS,),
            _STATS_OUT,
            bad=(
                Bad(
                    ("-f", "bogus", "counts.csv"),
                    ("--format",),
                    "a value outside its choices is a parse error (DETK-0033)",
                ),
            ),
        ),
        Sub("coldist", (COUNTS,), _STATS_DIST + _STATS_OUT),
        Sub("rowdist", (COUNTS,), _STATS_DIST + _STATS_OUT),
        Sub("colzero", (COUNTS,), _STATS_OUT),
        Sub("rowzero", (COUNTS,), _STATS_OUT),
        Sub("entropy", (COUNTS,), _STATS_OUT),
        Sub(
            "pca",
            (COUNTS, Pos("cov_fn", optional=True)),
            _STATS_OUT,
            bad=(
                Bad(
                    ("counts.csv", "--column-data=cov.csv"),
                    ("--column-data",),
                    "--column-data is removed; the column data is the positional <cov_fn> (DETK-0030)",
                ),
            ),
        ),
    ),
)

# ------------------------------------------------------------- detk-outlier
OUTLIER = Command(
    "detk-outlier",
    (
        Sub(
            "entropy",
            (COUNTS,),
            (
                Opt("--percentile", "-p", "N"),
                # no [default: ...]: without -o the output is not written
                Opt("--output", "-o", "FILE"),
                Opt("--plot-output", None, "FILE"),
            ),
        ),
        Sub(
            "shrink",
            (COUNTS,),
            (
                OUTPUT,
                Opt("--shrink-factor", "-f", "N", "0.25"),
                Opt("--p-max", "-p", "N"),
                Opt("--iters", "-i", "N", "1000"),
            ),
        ),
    ),
    bad=(
        Bad(
            ("trim", "counts.csv"),
            ("trim",),
            "trim is not a subcommand (its unreachable branch is removed, DETK-0033)",
        ),
    ),
)

# --------------------------------------------------------------- detk-wrapr
# one usage block serves both subcommands, so both accept every option
_WRAPR_OPTS = (
    Opt("--rpath", None, "FILE"),
    Opt("--routput-dir", None, "DIR"),
    Opt("--meta-in", None, "FILE"),
    Opt("--meta-out", None, "FILE"),
    Opt("--params-in", None, "FILE"),
    Opt("--params-out", None, "FILE"),
    Opt("--strict"),
)
WRAPR = Command(
    "detk-wrapr",
    (
        Sub("check", (), _WRAPR_OPTS),
        Sub(
            "run",
            (Pos("rscript"), Pos("counts_in", optional=True), Pos("out", optional=True)),
            _WRAPR_OPTS,
        ),
    ),
)

# -------------------------------------------------------------- detk-report
REPORT = Command(
    "detk-report",
    (
        Sub("generate", (), (Opt("--dev"),)),
        Sub("clean", (), ()),
    ),
)

# ---------------------------------------------------------------- detk-util
UTIL = Command(
    "detk-util",
    (
        Sub(
            "tidy",
            (COUNTS, Pos("cov_fn")),
            (
                Opt("--output", "-o", "FILE", "stdout"),
                Opt("--column-data-output", "-p", "FILE"),
            ),
        ),
        Sub("tidy-counts", (COUNTS, Pos("cov_fn")), (OUTPUT,)),
        Sub("tidy-covs", (COUNTS, Pos("cov_fn")), (OUTPUT,)),
        Sub(
            "annotate",
            (Pos("result_fn"), Pos("mapping_fn")),
            (
                Opt("--idcol", "-i", "COL", "0"),
                Opt("--map-from", None, "COL", "0"),
                Opt("--map-to", None, "COLS", "all"),
                Opt("--strip-versions"),
                Opt("--drop-unmapped"),
                OUTPUT,
            ),
        ),
        Sub(
            "gather",
            (Pos("files", multi=True),),
            (
                Opt(
                    "--format",
                    None,
                    "FMT",
                    "auto",
                    choices=("salmon", "kallisto", "htseq", "featurecounts", "auto"),
                ),
                Opt("--column", None, "COL"),
                Opt("--name-from", None, "REGEX"),
                Opt("--on-mismatch", None, "WHAT", "error", choices=("error", "fill", "drop")),
                OUTPUT,
            ),
            lines=(
                Line(
                    ("a.sf", "b.sf", "c.sf"),
                    {"files": ["a.sf", "b.sf", "c.sf"]},
                    "<files>... takes every remaining argument, in order",
                ),
                Line(
                    ("a.sf", "--format=salmon", "b.sf"),
                    {"files": ["a.sf", "b.sf"], "format": "salmon"},
                    "options may come between the files",
                ),
            ),
            bad=(
                Bad(
                    ("--format=bogus", "missing.sf"),
                    ("--format",),
                    "a value outside its choices is a parse error (DETK-0033)",
                ),
                Bad(
                    ("--on-mismatch=bogus", "missing.sf"),
                    ("--on-mismatch",),
                    "a value outside its choices is a parse error (DETK-0033)",
                ),
            ),
        ),
        Sub(
            "record",
            (Pos("command", multi=True, after_dashdash=True),),
            (
                Opt("--input", "-i", "FILE", repeat=True),
                Opt("--output", "-o", "FILE", repeat=True, required=True),
                Opt("--tool", None, "NAME"),
                Opt("--tool-version", None, "TEXT"),
            ),
            lines=(
                Line(
                    ("-i", "a.csv", "-i", "b.csv", "-o", "c.csv", "--output=d.csv", "--", "mlr"),
                    {"input": ["a.csv", "b.csv"], "output": ["c.csv", "d.csv"], "command": ["mlr"]},
                    "--input and --output repeat, keeping their order (DETK-0061)",
                ),
                Line(
                    ("-o", "c.csv", "--", "mlr", "--icsv", "-o", "x", "--version", "-h"),
                    {
                        "output": ["c.csv"],
                        "command": ["mlr", "--icsv", "-o", "x", "--version", "-h"],
                    },
                    "every word after -- is the command's, detk's own options too",
                ),
                Line(
                    ("-o", "c.csv", "--", "sh", "-c", "a -- b", "--", "x"),
                    {"output": ["c.csv"], "command": ["sh", "-c", "a -- b", "--", "x"]},
                    "only the first -- ends detk's arguments",
                ),
                Line(
                    ("-o", "c.csv", "--tool=R", "--tool-version", "4.4.1", "--", "Rscript", "x.R"),
                    {
                        "output": ["c.csv"],
                        "tool": "R",
                        "tool_version": "4.4.1",
                        "command": ["Rscript", "x.R"],
                    },
                    "--tool and --tool-version name the software that runs",
                ),
            ),
            bad=(
                Bad(
                    ("-o", "c.csv", "stray", "--", "cmd"),
                    ("stray", "--"),
                    "a word before -- is not the command",
                ),
                Bad(("-o", "c.csv", "--"), ("command",), "-- with nothing after it"),
                Bad(("-o", "c.csv", "cmd"), ("cmd",), "the command must come after --"),
                Bad(
                    ("--", "cmd", "-o", "c.csv"),
                    ("--output",),
                    "an -o after -- is the command's, so --output is missing",
                ),
                Bad(
                    ("-o", "c.csv", "--bogus", "--", "cmd"),
                    ("--bogus",),
                    "an unknown option before -- is still an error",
                ),
                Bad(
                    ("-d", ",", "-o", "c.csv", "--", "cmd"),
                    ("-d",),
                    "record writes no table, so it takes no -d",
                ),
                Bad(
                    ("--out-delim=,", "-o", "c.csv", "--", "cmd"),
                    ("--out-delim",),
                    "record writes no table, so it takes no --out-delim",
                ),
            ),
            without_common=("--out-delim",),
        ),
    ),
)

COMMANDS = (NORM, DE, ENRICH, TRANSFORM, FILTER, STATS, OUTLIER, WRAPR, REPORT, UTIL)


# --------------------------------------------------------- the detk umbrella
@dataclass(frozen=True)
class Umbrella:
    "How ``detk`` itself answers command lines that name no module command"

    # module names its help lists: every module command (DETK-0025 gap 1)
    help_lists: tuple = (
        "norm",
        "de",
        "enrich",
        "transform",
        "filter",
        "stats",
        "outlier",
        "wrapr",
        "report",
        "util",
    )
    # command lines it rejects, non-zero with usage on stderr
    rejects: tuple = field(default_factory=lambda: ((), ("bogus",), ("bogus", "x")))


UMBRELLA = Umbrella()
