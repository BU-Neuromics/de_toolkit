r"""
Filter features (rows) out of a counts matrix with a filter expression,
written in a small mini-language and quoted on the command line. The
expression describes the rows to keep:

    <function>(<column spec>) <inequality> <number>

The functions are mean, median, max, min, zero and nonzero (for zero and
nonzero, a number strictly between 0 and 1 is a fraction of samples, 0 or
>= 1 a number of samples); the inequalities >, >=, <, <=, == and !=. Terms
combine with and / or and group with parentheses. The column spec is all
(every sample), a column of <cov_fn> (the filter is applied to each of its
groups, and a row is kept if any group passes), or one group of it, as in
condition[test]: a group is a value of the column as written, a number for
a column of numbers (flag[1]) and true or false for a column of booleans. A
group the column does not have is an error.
"""

import functools
import logging
import os.path
import ply.lex as lex
import ply.yacc as yacc
import sys

import pandas

from .common import (
    UsageError,
    cli_main,
    DetkModule,
    DetkParser,
    add_common_options,
    make_cli_count_obj,
    parse_cli,
    set_logging,
    write_output,
)
from .report import DetkReport

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Available tokens for mini language
reserved = ("ALL", "OR", "AND", "MEDIAN", "MEAN", "ZERO", "NONZERO", "MAX", "MIN")
tokens = ("LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "OP", "WORD", "NUMBER") + reserved
reserved = dict((_,) * 2 for _ in reserved)

# Definitions of the mini language tokens
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_OP = r">=|<=|==|!=|<|>"
t_NUMBER = r"-?[0-9]+([.][0-9]+)?"


# http://www.dabeaz.com/ply/ply.html#ply_nn6
def t_WORD(t):
    r"[a-zA-Z_.][a-zA-Z0-9_.]*"
    t.type = reserved.get(t.value.upper(), "WORD")
    return t


# Mini language ignores spaces, tabs, brackets, and parentheses
t_ignore = " "


class FilterCommandError(ValueError):
    """
    A filter expression detk cannot use: it does not parse, or it names a
    column the column data does not have, or a column without column data.
    detk-filter reports it as a usage error (exit 2, DETK-0031).
    """


# Prints an error message if there's an invalid token
def t_error(t):
    raise FilterCommandError(f"illegal character {t.value[0]!r} at position {t.lexpos}")


# mini language is like:
#
# expression : spec OP NUMBER
#            | expression OR expression
#            | expression AND expression
#            | LPAREN expression RPAREN
# spec       : FUNC LPAREN ALL RPAREN
#            | FUNC LPAREN word RPAREN
#            | FUNC LPAREN word LBRACKET word RBRACKET RPAREN
class Expr:
    pass


class And(Expr):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __call__(self, mat):
        # inner join
        return self.a(mat).intersection(self.b(mat))

    def __repr__(self):
        return f"And({repr(self.a)},{repr(self.b)})"


class Or(Expr):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __call__(self, mat):
        # outer join
        return self.a(mat).union(self.b(mat))

    def __repr__(self):
        return f"Or({repr(self.a)},{repr(self.b)})"


class Group(Expr):
    def __init__(self, member):
        self.member = member

    def __call__(self, mat):
        return self.member(mat)

    def __repr__(self):
        return f"Group({repr(self.member)})"


class Clause(Expr):
    def __init__(self, func, spec, op, val):
        self.func = func.lower()
        self.spec = spec
        self.op = op
        self.val = float(val)

    def __call__(self, mat):
        dfs = self.spec(mat)
        idx = set()
        for df in dfs:
            # aggregate
            if self.func == "median":
                val = df.median(axis=1)
            elif self.func == "mean":
                val = df.mean(axis=1)
            elif self.func == "min":
                val = df.min(axis=1)
            elif self.func == "max":
                val = df.max(axis=1)
            elif self.func == "zero":
                val = (df == 0).sum(axis=1)
                if 0 < self.val < 1:
                    val /= df.shape[1]
            elif self.func == "nonzero":
                val = (df != 0).sum(axis=1)
                if 0 < self.val < 1:
                    val /= df.shape[1]

            # compare
            if self.op == ">=":
                idx.update(set(val[val >= self.val].index))
            elif self.op == ">":
                idx.update(set(val[val > self.val].index))
            elif self.op == "<=":
                idx.update(set(val[val <= self.val].index))
            elif self.op == "<":
                idx.update(set(val[val < self.val].index))
            elif self.op == "==":
                idx.update(set(val[val == self.val].index))
            elif self.op == "!=":
                idx.update(set(val[val != self.val].index))

        return idx

    def __repr__(self):
        return f"Clause({repr(self.func)},{repr(self.spec)},{repr(self.op)},{repr(self.val)})"


def group_matches(values, group):
    """
    A boolean mask of the column *values* equal to the *group* as written in
    a filter expression: compared as a number for a column of numbers
    (``cond[1]`` on a 0/1 column), as true or false in any case for a
    column of booleans, and as text otherwise.
    """
    if pandas.api.types.is_bool_dtype(values) or (
        values.dtype == object
        and len(values.dropna())
        and all(isinstance(_, bool) for _ in values.dropna())
    ):
        if group.lower() not in ("true", "false"):
            return pandas.Series(False, index=values.index)
        return values == (group.lower() == "true")
    if pandas.api.types.is_numeric_dtype(values):
        try:
            number = float(group)
        except ValueError:
            return pandas.Series(False, index=values.index)
        return values == number
    return values.astype(str) == group


class ColSpec(Expr):
    def __init__(self, field=None, group=None):
        self.field = field
        self.group = group

    def __call__(self, mat):
        # return a list of dataframes containing the column subsets that the
        # Clause will use to filter
        if self.field is None and self.group is None:
            # no column filters
            return [mat.counts]
        elif self.field is not None:
            if mat.column_data is None:
                raise FilterCommandError(
                    f"the filter expression names the column {self.field!r}, but no column "
                    "data was supplied; give the column data file (<cov_fn>) to filter by "
                    "its columns and groups"
                )
            # column_data always has a counts column of its own (CountMatrix)
            columns = [c for c in mat.column_data.columns if c != "counts"]
            if self.field not in columns:
                raise FilterCommandError(
                    f"the filter expression names the column {self.field!r}, which is not "
                    f"in the column data (its columns: {', '.join(map(str, columns))})"
                )
            if self.group is not None:
                # only one group is selected: the samples whose value in the
                # column is the group as written; a group the column does
                # not have is an error, not an empty selection
                values = mat.column_data[self.field]
                cols = mat.column_data.index[group_matches(values, self.group)]
                if cols.size == 0:
                    present = sorted({str(_) for _ in values.dropna()})
                    raise FilterCommandError(
                        f"the filter expression names the group {self.group!r} of the column "
                        f"{self.field!r}, which has no such value (its values: "
                        f"{', '.join(present)})"
                    )
                return [mat.counts[cols]]
            else:
                # return a list of dataframe slices, one per
                # group
                dfs = []
                for _, df in mat.column_data.groupby(self.field):
                    dfs.append(mat.counts[df.index])
                return dfs

    def __repr__(self):
        return f"ColSpec(field={repr(self.field)},group={repr(self.group)})"


def p_expression(p):
    """expression : clause
    | expression OR expression
    | expression AND expression
    | LPAREN expression RPAREN"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        if issubclass(p[2].__class__, Expr):
            p[0] = Group(p[2])
        elif p[2].lower() == "and":
            p[0] = And(p[1], p[3])
        elif p[2].lower() == "or":
            p[0] = Or(p[1], p[3])
        else:
            raise Exception("unrecognized expression:", p)


def p_clause(p):
    """clause : func LPAREN colspec RPAREN OP NUMBER"""
    p[0] = Clause(p[1], p[3], p[5], p[6])


def p_func(p):
    """func : MEAN
    | MEDIAN
    | ZERO
    | NONZERO
    | MIN
    | MAX
    """
    p[0] = p[1]


def p_spec(p):
    """colspec : ALL
    | WORD
    | WORD LBRACKET WORD RBRACKET
    | WORD LBRACKET NUMBER RBRACKET"""
    if p[1].lower() == "all":
        obj = ColSpec()
    else:
        if len(p) == 5:
            obj = ColSpec(p[1], p[3])
        else:
            obj = ColSpec(p[1])
    p[0] = obj


def p_error(p):
    if p is None:
        raise FilterCommandError("it ends before the expression is complete")
    raise FilterCommandError(f"unexpected {p.value!r} at position {p.lexpos}")


# The grammar has 4 shift/reduce conflicts, all between AND and OR: ply
# resolves each as a shift, so and/or have equal precedence and group to
# the right, "a and b or c" as "a and (b or c)". tests/filter pins the
# count and the grouping; parentheses group as written.
SHIFT_REDUCE_CONFLICTS = 4


class _CountingLog:
    "A ply log that keeps quiet and counts the shift/reduce conflicts it is told of"

    def __init__(self):
        self.conflicts = {"shift/reduce": 0, "reduce/reduce": 0}

    def warning(self, msg, *args, **kwargs):
        for kind in self.conflicts:
            if msg.endswith((f"{kind} conflict", f"{kind} conflicts")):
                self.conflicts[kind] = args[0] if args else 1

    def error(self, msg, *args, **kwargs):
        raise FilterCommandError("the filter grammar is invalid: " + (msg % args))

    def info(self, msg, *args, **kwargs):
        pass

    debug = critical = info


def build_filter_parser():
    """
    The lexer and parser of the filter mini language, built in memory and
    quietly: ply writes no table or parser.out file and nothing on stderr.
    Returns (lexer, parser, conflicts), *conflicts* the grammar's number of
    shift/reduce and of reduce/reduce conflicts by kind (ply counts them
    only when it builds the tables with debug on, into the quiet log).
    """
    log = _CountingLog()
    lexer = lex.lex(module=sys.modules[__name__], errorlog=log)
    parser = yacc.yacc(
        module=sys.modules[__name__],
        debug=True,
        debuglog=log,
        write_tables=False,
        errorlog=log,
    )
    return lexer, parser, log.conflicts


@functools.cache
def _filter_parser():
    lexer, parser, _ = build_filter_parser()
    return lexer, parser


def parse_filter_command(cmd):
    lexer, parser = _filter_parser()
    try:
        parsed = parser.parse(cmd, lexer=lexer.clone())
    except FilterCommandError as e:
        raise FilterCommandError(f"could not parse the filter expression {cmd!r}: {e}") from e
    if parsed is None:  # failed to parse
        raise FilterCommandError(f"could not parse the filter expression {cmd!r}")

    return parsed


def filter_counts(counts_obj, command):
    obj = FilterCounts(counts_obj, command)
    return obj.output


class FilterCounts(DetkModule):
    def __init__(self, counts_obj, command):
        self["params"] = {"command": command}
        logger.info("filtering counts with command: %s", command)

        logger.debug("constructing parser from command")
        parser = parse_filter_command(command)

        logger.debug("constructing parser from command")
        self.counts_obj = counts_obj

        logger.debug("filtering counts")

        self.kept = parser(counts_obj)

        logger.info("features filtered: %d", self.counts_obj.counts.shape[0] - len(self.kept))
        logger.info("features kept after filtering: %d", len(self.kept))

    @property
    def output(self):
        return self.counts_obj.counts.loc[self.counts_obj.counts.index.isin(self.kept)]

    @property
    def properties(self):
        return {
            "num_kept": len(self.kept),
            "num_filtered": self.counts_obj.counts.shape[0] - len(self.kept),
        }


def build_parser():
    "The detk-filter command line parser"
    parser = DetkParser(
        prog="detk-filter",
        description=__doc__.strip(),
        examples=[
            (
                "Keep the genes with a count above zero in at least half the samples",
                "detk-filter -o counts_filtered.csv 'nonzero(all) >= 0.5' counts.csv",
            ),
            (
                "Keep the genes whose mean count is above 10 in either group",
                "detk-filter -o counts_filtered.csv 'mean(group) > 10' counts.csv sample_info.csv",
            ),
        ],
    )
    parser.add_argument(
        "command", metavar="<command>", help="Filter expression: the rows to keep, quoted"
    )
    parser.add_argument(
        "counts_fn",
        metavar="<counts_fn>",
        help="Counts file: features in rows, samples in columns, delimited",
    )
    parser.add_argument(
        "cov_fn",
        metavar="<cov_fn>",
        nargs="?",
        help="Column data file: samples in rows, covariates in columns, for group filters",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE", default="stdout", help="Name of the output file"
    )
    add_common_options(parser)
    return parser


@cli_main
def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)

    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    count_obj = make_cli_count_obj(args)

    try:
        filtered = FilterCounts(count_obj, args.command)
    except FilterCommandError as e:
        # the <command> argument is wrong: a usage error (DETK-0031)
        raise UsageError(str(e)) from e

    write_output(filtered.output, args)

    if not args.no_report:
        logging.info("writing report to %s", args.report_dir)
        # write out the report json
        with DetkReport(args.report_dir) as r:
            r.add_module(
                filtered,
                in_file_path=args.counts_fn,
                out_file_path=args.output,
                column_data_path=args.cov_fn,
                workdir=os.getcwd(),
            )

    logging.info("done")


if __name__ == "__main__":
    main()
