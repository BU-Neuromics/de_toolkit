r"""
Utilities around a detk analysis: tidy a counts file and its sample
information so their samples match (tidy, tidy-counts, tidy-covs), annotate
a result table with feature metadata such as gene symbols (annotate),
gather per-sample quantifier outputs into one counts matrix (gather), and
run a command outside detk and record it as a step of the analysis (record).
"""

_GATHER_FORMATS = ("salmon", "kallisto", "htseq", "featurecounts", "auto")
_ON_MISMATCH = ("error", "fill", "drop")

# each subcommand: the one line the command's help lists it with, its
# description and its examples
SUBCOMMANDS = {
    "tidy": dict(
        help="Subset counts columns and sample information rows to the samples in both",
        description="""\
Subset both the counts columns and column data rows by intersection, returning
new outputs for both. Note the tidied column data is not output by default, and
the user must specify the -p argument to obtain it.""",
        examples=[
            (
                "Keep the samples in both files, writing both tidied files",
                "detk-util tidy -o counts_tidy.csv -p sample_info_tidy.csv counts.csv "
                "sample_info.csv",
            ),
        ],
    ),
    "tidy-counts": dict(
        help="Subset and order the counts columns by the sample information rows",
        description="""\
Subset and order the provided counts file columns according to the rows of the
provided column data file. Operation will fail if there are rows in the column
data file that do not exist as columns in the counts file.""",
        examples=[
            (
                "Order the counts columns as the samples in sample_info.csv",
                "detk-util tidy-counts -o counts_tidy.csv counts.csv sample_info.csv",
            ),
        ],
    ),
    "tidy-covs": dict(
        help="Subset and order the sample information rows by the counts columns",
        description="""\
Subset and order the provided column data file rows according to the columns of
the provided counts data file. Operation will fail if there are columns in the
counts file that do not exist as rows in the column data file.""",
        examples=[
            (
                "Order the sample information rows as the counts columns",
                "detk-util tidy-covs -o sample_info_tidy.csv counts.csv sample_info.csv",
            ),
        ],
    ),
    "annotate": dict(
        help="Add feature metadata, such as gene symbols, to a result table",
        description="""\
Annotate a result table (e.g. the output of detk-de) with feature metadata,
such as gene symbols, from a user-supplied mapping table. Both files are
delimited text files whose delimiter (comma, tab, semicolon, pipe or space)
is sniffed from the first line, a file with none being one column; the
result is read and written back as text, so IDs such as 007 are kept as
written. Rows and columns of the result table keep their order and number,
and the added columns come last: an ID with several mapping rows gets the
distinct values joined with ';', and an ID with no mapping row (or only rows
whose added columns are empty), or an empty or NA ID, gets empty columns; to
drop it, use the option --drop-unmapped. Columns are given by name or by
0-based position.""",
        examples=[
            (
                "Add the symbol column of genes.csv to the DE results, matching on gene_id",
                "detk-util annotate --map-from=gene_id --map-to=symbol -o de_annotated.csv "
                "de_results.csv genes.csv",
            ),
        ],
    ),
    "gather": dict(
        help="Gather per-sample salmon, kallisto, htseq or featureCounts output into a matrix",
        description="""\
Gather per-sample quantifier outputs (salmon quant.sf, kallisto abundance.tsv,
htseq-count or featureCounts output) into one counts matrix with a row per
feature and a column per sample. One column is extracted from each file as
written, without any aggregation (e.g. transcripts to genes). Feature IDs and
values are kept as written. The format is detected from each file's header
unless given with --format, and every file must have the same format. A file
argument that does not exist but holds a wildcard (*, ? or [) is expanded as a
glob, so a quoted pattern works too; its matches are taken in natural order
(s2 before s10).

The column is given by name or 0-based position; by default it is NumReads
for salmon, est_counts for kallisto, the count column for htseq and every
count column for featureCounts. An htseq-count file with several count
columns (htseq-count run on several BAMs) is refused unless --column is given,
since it has no header naming them. Every value must be a plain finite number
(digits, an optional sign, fraction and exponent); nan, inf and the like are
errors. htseq-count's summary lines (__no_feature, __ambiguous, ...) are not
features: they are left out of the matrix and recorded in the report.

Sample names come from each file's path: its file name without the last
extension, or, when those are not unique among the files given (quant.sf,
abundance.tsv), every file's directory name; a single quant.sf is therefore
named quant. With --name-from, the name is the first group of
the regular expression, or else its whole match, searched in the path. In
featureCounts output each count column is a sample, named the same way from
the column's header (the BAM file's path) rather than the file's path.

Every sample must list the same features, or gather stops with an error naming
the differences: --on-mismatch=fill keeps every feature and fills the absent
ones with 0, --on-mismatch=drop keeps only the features every sample lists.""",
        examples=[
            (
                "Gather the NumReads of every salmon sample into one counts matrix",
                "detk-util gather -o counts.csv 'salmon/*/quant.sf'",
            ),
            (
                "Gather htseq-count files, keeping only the features every sample lists",
                "detk-util gather --on-mismatch=drop -o counts.csv s1.htseq s2.htseq s3.htseq",
            ),
        ],
    ),
    "record": dict(
        help="Run a command outside detk and record it as a step in the report and crate",
        description="""\
Run an external command (Miller, awk, an R script, ...) and record it as a
step of the analysis, so the files it writes show in the module JSON and in
the provenance crate (ro-crate-metadata.json) as the output of that step, and
a later detk command that reads them has a producer to trace them to.

The command is everything after --, run as given without a shell: a pipeline
or a redirect inside the step needs sh -c '...'. It reads detk's stdin and
writes to detk's stdout and stderr, so a redirect of the whole line (detk-util
record ... -- cmd > out.csv) captures the command's own output; record itself
writes nothing to stdout, its messages go to stderr.

Every --input must exist before the run and every --output after it. Record
exits 1 and writes no module JSON when an input is missing, when the command
is not found or exits non-zero, or when an output is missing after the run; it
never deletes or rewrites a file. The check only asks that each output exists:
a file that was there before the run passes it, including the empty file a
shell redirect (> out.csv) creates before record starts. The module JSON holds
the command, the tool and its version, and the SHA-256 checksum and size of
every input (read before the run) and output (read after it), so the
checksums say what the files held when recorded.

The tool is the base name of the command's first word unless --tool names it
(needed for sh -c '...' or Rscript script.R). Its version is the first line
of '<command> --version', run with a 10 s timeout, unless --tool-version gives
it; when that fails, or --tool names a tool other than the command's first
word, the version is recorded as 'unknown' with a warning.

Without --tool-version, record runs '<command> --version' once to read the
version, so a script that ignores --version would run its whole step a second
time: give --tool-version for your own scripts (./derive.py).""",
        examples=[
            (
                "Record a Miller step that adds an age_group column to the sample information",
                "detk-util record -i sample_info.csv -o sample_info_derived.csv -- "
                'mlr --icsv --ocsv put \'$age_group = $age >= 50 ? "old" : "young"\' '
                "sample_info.csv > sample_info_derived.csv",
            ),
            (
                "Record a pipeline, run through sh -c, as an awk step",
                "detk-util record --tool=awk -i counts.csv -o counts_head.csv -- "
                "sh -c 'head -n 101 counts.csv | awk -F, \"NF > 1\" > counts_head.csv'",
            ),
        ],
    ),
}


def _counts_and_covs(sub):
    sub.add_argument(
        "counts_fn",
        metavar="<counts_fn>",
        help="Counts file: features in rows, samples in columns, delimited",
    )
    sub.add_argument(
        "cov_fn",
        metavar="<cov_fn>",
        help="Sample information file: samples in rows, delimited",
    )


def _output(sub, what):
    sub.add_argument(
        "-o", "--output", metavar="FILE", default="stdout", help=f"Destination of {what}"
    )


RECORD_USAGE = "detk-util record [options] [-i FILE]... -o FILE... -- <command> [<arg>...]"


def _record_arguments(sub):
    # every word after "--" is the command (common.parse_cli); the positional
    # is here for help and completion, and nothing before "--" may fill it
    sub.command_dest = "command"
    sub.add_argument(
        "command",
        metavar="<command>",
        nargs="*",
        help="The command to run and its arguments, after --; run as given, without a shell",
    )
    sub.add_argument(
        "-i",
        "--input",
        metavar="FILE",
        action="append",
        help="A file the command reads; give it once per file, or not at all",
    )
    sub.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        action="append",
        required=True,
        help="A file the command writes; give it once per file (at least one)",
    )
    sub.add_argument(
        "--tool",
        metavar="NAME",
        help="Name of the tool that runs (without it: the base name of the command's first word)",
    )
    sub.add_argument(
        "--tool-version",
        metavar="TEXT",
        help="Version of the tool to record (without it: the first line of '<command> --version')",
    )
    sub.validate = _validate_record


def _validate_record(args):
    if not args.command:
        return "the following arguments are required: <command> (the command to run, after --)"
    return None


def build_parser():
    "The detk-util command line parser"
    parser = DetkParser(prog="detk-util", description=__doc__.strip())
    add_command_options(parser)
    subs = add_subcommands(parser)
    for name, spec in SUBCOMMANDS.items():
        sub = subs.add_parser(
            name,
            help=spec["help"],
            description=spec["description"],
            examples=spec["examples"],
            # gather's files may be interleaved with its options
            intermixed=name == "gather",
            **(dict(usage=RECORD_USAGE) if name == "record" else {}),
        )
        if name == "tidy":
            _counts_and_covs(sub)
            _output(sub, "tidied counts data")
            sub.add_argument(
                "-p",
                "--column-data-output",
                metavar="FILE",
                help="Destination of tidied column data (not written without it)",
            )
        elif name == "tidy-counts":
            _counts_and_covs(sub)
            _output(sub, "tidied counts data")
        elif name == "tidy-covs":
            _counts_and_covs(sub)
            _output(sub, "tidied column data")
        elif name == "annotate":
            sub.add_argument(
                "result_fn",
                metavar="<result_fn>",
                help="Result table to annotate, e.g. the output of detk-de",
            )
            sub.add_argument(
                "mapping_fn",
                metavar="<mapping_fn>",
                help="Mapping table: feature IDs and the metadata columns to add",
            )
            sub.add_argument(
                "-i",
                "--idcol",
                metavar="COL",
                default="0",
                help="Column in the result file holding the feature IDs to join on",
            )
            sub.add_argument(
                "--map-from",
                metavar="COL",
                default="0",
                help="Column in the mapping file matching the result IDs",
            )
            sub.add_argument(
                "--map-to",
                metavar="COLS",
                default="all",
                help="Comma-separated mapping columns to add, or 'all' for every column "
                "but --map-from",
            )
            sub.add_argument(
                "--strip-versions",
                action="store_true",
                help="Strip trailing .N version suffixes from Ensembl-style IDs before joining",
            )
            sub.add_argument(
                "--drop-unmapped",
                action="store_true",
                help="Drop result rows with no mapping instead of leaving their added "
                "columns empty",
            )
            _output(sub, "the annotated table")
        elif name == "gather":
            sub.add_argument(
                "files",
                metavar="<files>",
                nargs="+",
                help="Quantifier output files, one per sample (a quoted glob is expanded)",
            )
            sub.add_argument(
                "--format",
                metavar="FMT",
                default="auto",
                choices=_GATHER_FORMATS,
                help="Format of the files; auto detects it from each file's header",
            )
            sub.add_argument(
                "--column",
                metavar="COL",
                help="Column to extract from each file, by name or 0-based position "
                "(without it: the format's count column)",
            )
            sub.add_argument(
                "--name-from",
                metavar="REGEX",
                help="Regular expression deriving each sample name from its file path "
                "(the first group, or the whole match)",
            )
            sub.add_argument(
                "--on-mismatch",
                metavar="WHAT",
                default="error",
                choices=_ON_MISMATCH,
                help="What to do when the samples list different features: stop with an "
                "error, fill with 0 or drop them",
            )
            _output(sub, "the counts matrix")
        elif name == "record":
            _record_arguments(sub)
        # record writes no table, so -d/--out-delim has nothing to act on
        add_common_options(sub, out_delim=name != "record")
    return parser


import logging
import pandas
import re
import sys

from .common import (
    cli_main,
    DetkModule,
    DetkParser,
    add_command_options,
    add_common_options,
    add_subcommands,
    CountMatrix,
    parse_cli,
    read_delimited,
    read_id_table,
    set_logging,
    write_output,
)

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class Stub(Exception):
    pass


def stub(f):
    def stub(*args, **kwargs):
        raise Stub(f"Not yet implemented - {f.__module__}.{f.__name__}")

    return stub


# ---------------------------------------------------------------------------
# tidy, tidy-counts, tidy-covs: match a counts file and its sample information
# ---------------------------------------------------------------------------

# the module name each tidy subcommand records in the report
_TIDY_NAMES = {"tidy": "tidy", "tidy-counts": "tidycounts", "tidy-covs": "tidycovs"}


class Tidy(DetkModule):
    """
    Match the samples of the counts table *counts* (samples in columns) and
    the column data *column_data* (samples in rows): keep the samples in
    both, in the order of the counts columns, the way detk's other commands
    match them (:class:`~de_toolkit.common.CountMatrix`).

    :attr:`counts` is the tidied counts and :attr:`column_data` the tidied
    column data with exactly the columns of *column_data*, in its order and
    under its index name: the ``counts`` column CountMatrix adds for its
    design machinery is not part of it. *command* names the subcommand
    (``tidy``, ``tidy-counts`` or ``tidy-covs``), which is the module's name
    in the report, and :attr:`output` its main output: the counts for tidy
    and tidy-counts, the column data for tidy-covs. tidy-counts raises
    ValueError when a column data sample is not a counts column, tidy-covs
    when a counts column is not a column data sample.
    """

    def __init__(self, counts, column_data, command="tidy"):
        if command not in _TIDY_NAMES:
            raise ValueError(f"unknown tidy command {command!r}")
        self.command = command
        self["params"] = {}

        if command == "tidy-counts" and len(column_data.index.difference(counts.columns)):
            raise ValueError(
                "tidy-counts requires that all row IDs in the "
                "column data file exist as columns in the counts file."
            )
        if command == "tidy-covs" and len(counts.columns.difference(column_data.index)):
            raise ValueError(
                "tidy-covs requires that all column IDs in the "
                "counts data file exist as rows in the column data file."
            )

        # CountMatrix adds a counts column to the frame it is given
        matched = CountMatrix(counts, column_data.copy())
        samples = matched.counts.columns
        self.counts = matched.counts
        tidied = column_data.loc[list(samples), list(column_data.columns)]
        # indexing by the counts columns would name the index as they are
        tidied.index.name = column_data.index.name
        self.column_data = tidied

        kept = set(samples)
        self["properties"] = {
            "num_features": int(counts.shape[0]),
            "num_counts_samples": int(counts.shape[1]),
            "num_column_data_samples": int(column_data.shape[0]),
            "num_samples": int(len(samples)),
            "counts_samples_dropped": [str(s) for s in counts.columns if s not in kept],
            "column_data_samples_dropped": [str(s) for s in column_data.index if s not in kept],
        }
        logger.info("samples in both: %d", len(samples))
        logger.info("counts columns lost: %d", len(self["properties"]["counts_samples_dropped"]))
        logger.info(
            "column data rows lost: %d", len(self["properties"]["column_data_samples_dropped"])
        )

    @property
    def name(self):
        return _TIDY_NAMES[self.command]

    @property
    def output(self):
        return self.column_data if self.command == "tidy-covs" else self.counts


def read_column_data(f):
    """
    Read the column data (sample information) file *f*, samples in rows,
    indexed by its first column, every field (the IDs too) as text exactly as
    written (empty cells stay empty), so the tidied file is written as it was
    read. The header may name the ID column (``sample,condition``), leave it
    empty (``,condition``, R's write.csv) or leave it out, one field short
    (``condition``, R's write.table with ``sep=","``); the index is named by
    the header's first cell in the first case only.
    """
    from pandas.errors import EmptyDataError

    from .common import _first_line, _read_with, _rewindable, sniff_delimiter

    # every line is read as fields of text, the header too, so pandas types
    # nothing: an index pandas infers from a short header would be typed
    # (001 read as 1), so the layout is told from the field counts instead
    f, compression = _rewindable(f)
    sep = sniff_delimiter(_first_line(f, compression))

    def read(**kwargs):
        return _read_with(
            f, compression, sep, header=None, dtype=str, keep_default_na=False, **kwargs
        )

    header = read(nrows=1).iloc[0].tolist()
    try:
        width = read(skiprows=1, nrows=1).shape[1]
    except EmptyDataError:
        width = len(header)
    short = width == len(header) + 1
    if not short and width != len(header):
        raise ValueError(
            f"the header of the column data has {len(header)} fields and its first "
            f"row {width}; they must be as many, or the header one fewer"
        )
    try:
        rows = read(skiprows=1, names=list(range(width)))
    except EmptyDataError:
        rows = pandas.DataFrame(columns=list(range(width)), dtype=str)

    table = rows.iloc[:, 1:]
    table.index = pandas.Index(rows[0].to_numpy(), name=None if short else (header[0] or None))
    table.columns = header if short else header[1:]
    return table


def _tidy_main(args):
    import os

    from .report import DetkReport

    cmd = args.subcommand
    logger.info("performing %s", cmd)
    # the IDs and sample names are read as text, as the counts header is, so
    # a sample named 001 in the column data matches the counts column 001
    counts = read_id_table(args.counts_fn)
    logger.info("shape of counts: %s", counts.shape)
    column_data = read_column_data(args.cov_fn)
    logger.info("shape of column data: %s", column_data.shape)

    tidied = Tidy(counts, column_data, command=cmd)

    write_output(tidied.output, args)
    outputs = [args.output]
    p_output = getattr(args, "column_data_output", None)
    if p_output:
        logger.info("writing tidied column data to %s", p_output)
        tidied.column_data.to_csv(p_output, sep=args.out_delim)
        outputs.append(p_output)

    if not args.no_report:
        logging.info("writing report to %s", args.report_dir)
        with DetkReport(args.report_dir) as r:
            r.add_module(
                tidied,
                in_file_path=args.counts_fn,
                out_file_path=args.output,
                column_data_path=args.cov_fn,
                workdir=os.getcwd(),
                in_file_paths=[args.counts_fn, args.cov_fn],
                out_file_paths=outputs,
            )

    logging.info("done")


# ---------------------------------------------------------------------------
# annotate: join feature metadata onto a result table (#29)
# ---------------------------------------------------------------------------

_VERSION_SUFFIX = r"\.\d+$"

# the strings pandas.read_csv reads as missing by default; an ID cell holding
# one of them (or nothing) is a missing ID and is never joined
_MISSING_IDS = frozenset(
    [
        "",
        "#N/A",
        "#N/A N/A",
        "#NA",
        "-1.#IND",
        "-1.#QNAN",
        "-NaN",
        "-nan",
        "1.#IND",
        "1.#QNAN",
        "<NA>",
        "N/A",
        "NA",
        "NULL",
        "NaN",
        "None",
        "n/a",
        "nan",
        "null",
    ]
)


def _resolve_column(df, col, what):
    """Return the name of column *col* of *df*: a column name, or else a
    0-based position given as an int or a string of digits."""
    if col in df.columns:
        return col
    if isinstance(col, int) or (isinstance(col, str) and col.isdigit()):
        pos = int(col)
        if pos < df.shape[1]:
            return df.columns[pos]
    raise ValueError(f"{what} column {col!r} not found; columns are {list(df.columns)}")


def _strip_versions(ids):
    return ids.str.replace(_VERSION_SUFFIX, "", regex=True)


def _join_distinct(values):
    vals = [v for v in pandas.unique(values) if not pandas.isna(v) and str(v).strip() != ""]
    return ";".join(str(v) for v in vals) if vals else None


class Annotate(DetkModule):
    """
    Annotate the rows of *result* with columns of *mapping*, joined on the
    feature IDs.

    The rows of *result* keep their order and, unless *drop_unmapped*, their
    number; its columns keep their order, the first one becomes the index of
    the output and the added columns come last. IDs are compared as text, so
    pass an ID column of strings (the CLI reads the result file as text). An
    empty or missing ID (``NA``, ``NaN``, ...) is never joined.

    A mapping row counts only if at least one of the added columns has a
    value in it: an ID is mapped when some mapping row gives it a non-empty
    value. An ID with several such rows gets the distinct values of each
    added column joined with ``;``. An added column whose name is already a
    column of *result* is renamed with the suffix ``_annot``.
    """

    def __init__(
        self,
        result,
        mapping,
        idcol=0,
        map_from=0,
        map_to="all",
        strip_versions=False,
        drop_unmapped=False,
    ):
        self["params"] = {
            "idcol": idcol,
            "map_from": map_from,
            "map_to": map_to,
            "strip_versions": strip_versions,
            "drop_unmapped": drop_unmapped,
        }

        id_name = _resolve_column(result, idcol, "--idcol")
        from_name = _resolve_column(mapping, map_from, "--map-from")
        if map_to == "all" or map_to is None:
            to_names = [c for c in mapping.columns if c != from_name]
        else:
            if isinstance(map_to, str):
                map_to = [c.strip() for c in map_to.split(",") if c.strip()]
            to_names = [_resolve_column(mapping, c, "--map-to") for c in map_to]
        to_names = [c for c in to_names if c != from_name]
        if not to_names:
            raise ValueError("no mapping columns to add")
        logger.info("joining result column %r to mapping column %r", id_name, from_name)
        logger.info("adding mapping columns: %s", to_names)

        ids = result[id_name]
        missing = (ids.isna() | ids.astype(str).str.strip().isin(_MISSING_IDS)).to_numpy()
        result_keys = ids.astype(str).where(~missing)
        mapping = mapping[[from_name] + to_names].dropna(subset=[from_name])
        mapping[from_name] = mapping[from_name].astype(str)
        # a mapping row with no value in any added column maps nothing
        values = mapping[to_names].apply(lambda c: c.where(c.astype(str).str.strip() != ""))
        mapping = mapping.loc[values.notna().any(axis=1)]
        if strip_versions:
            result_keys = _strip_versions(result_keys)
            mapping[from_name] = _strip_versions(mapping[from_name])

        counts = mapping[from_name].value_counts()
        collapsed = mapping.groupby(from_name, sort=False)[to_names].agg(_join_distinct)

        renamed = {c: f"{c}_annot" if c in result.columns else c for c in to_names}
        added = collapsed.reindex(result_keys.values).rename(columns=renamed)
        added.index = result.index

        mapped = (result_keys.isin(collapsed.index) & ~missing).to_numpy()
        out = pandas.concat([result, added], axis=1)
        if drop_unmapped:
            out = out.loc[mapped]
        # the result's first column stays the index, whichever column is joined
        first = result.columns[0]
        out = out.set_index(first)
        if str(first).startswith("Unnamed: "):
            # an unnamed index column, as pandas writes it, stays unnamed
            out.index.name = None
        self._output = out

        unmapped_ids = result.loc[~mapped & ~missing, id_name].astype(str)
        self["properties"] = {
            "num_features": int(result.shape[0]),
            "num_mapped": int(mapped.sum()),
            "num_unmapped": int((~mapped).sum()),
            "num_missing_ids": int(missing.sum()),
            "num_multimapped": int(result_keys[mapped].map(counts).gt(1).sum()),
            "num_dropped": int((~mapped).sum()) if drop_unmapped else 0,
            "columns_added": list(renamed.values()),
            "unmapped_examples": unmapped_ids.drop_duplicates().head(10).tolist(),
        }
        logger.info(
            "features mapped: %d of %d (%d with several mapping rows)",
            self["properties"]["num_mapped"],
            self["properties"]["num_features"],
            self["properties"]["num_multimapped"],
        )
        if self["properties"]["num_missing_ids"]:
            logger.warning(
                "%d result rows have an empty or missing ID and stay unmapped",
                self["properties"]["num_missing_ids"],
            )
        if self["properties"]["unmapped_examples"]:
            logger.warning(
                "%d features had no mapping, e.g. %s%s",
                self["properties"]["num_unmapped"] - self["properties"]["num_missing_ids"],
                ", ".join(self["properties"]["unmapped_examples"][:3]),
                "" if strip_versions else " (try --strip-versions if the IDs carry .N suffixes)",
            )

    @property
    def output(self):
        return self._output


def annotate(result, mapping, **kwargs):
    "Return *result* with the columns of *mapping* added; see :class:`Annotate`."
    return Annotate(result, mapping, **kwargs).output


def _annotate_main(args):
    import os

    from .report import DetkReport

    # read as text, so numeric IDs keep their leading zeros and every
    # value is written back as it was read
    result = read_delimited(args.result_fn, dtype=str, keep_default_na=False)
    mapping = read_delimited(args.mapping_fn, dtype=str)
    logger.info("shape of result: %s", result.shape)
    logger.info("shape of mapping: %s", mapping.shape)
    annotated = Annotate(
        result,
        mapping,
        idcol=args.idcol,
        map_from=args.map_from,
        map_to=args.map_to,
        strip_versions=args.strip_versions,
        drop_unmapped=args.drop_unmapped,
    )

    write_output(annotated.output, args)

    if not args.no_report:
        # the module JSON has no slot for a second input file; keep the
        # mapping file's path with the parameters so the provenance names it
        annotated["params"]["mapping_fn"] = args.mapping_fn
        logging.info("writing report to %s", args.report_dir)
        with DetkReport(args.report_dir) as r:
            r.add_module(
                annotated,
                in_file_path=args.result_fn,
                out_file_path=args.output,
                workdir=os.getcwd(),
            )

    logging.info("done")


# ---------------------------------------------------------------------------
# gather: combine per-sample quantifier outputs into a counts matrix (#25)
# ---------------------------------------------------------------------------

GATHER_FORMATS = ("salmon", "kallisto", "htseq", "featurecounts")

# the exact header each headered format writes
_SALMON_HEADER = ["Name", "Length", "EffectiveLength", "TPM", "NumReads"]
_KALLISTO_HEADER = ["target_id", "length", "eff_length", "est_counts", "tpm"]
_FEATURECOUNTS_ANNOT = ["Geneid", "Chr", "Start", "End", "Strand", "Length"]

# the column extracted by default; None means every count column
_DEFAULT_COLUMN = {
    "salmon": "NumReads",
    "kallisto": "est_counts",
    "htseq": 1,
    "featurecounts": None,
}

_MISMATCH = ("error", "fill", "drop")


def _leading_comments(path):
    "Number of leading lines starting with '#' (featureCounts' command line)."
    n = 0
    with open(path) as f:
        for line in f:
            if not line.startswith("#"):
                break
            n += 1
    return n


def _first_line(path, skip=0):
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= skip:
                return line.rstrip("\r\n")
    return ""


# a plain finite decimal number, as quantifiers write counts and abundances:
# an optional sign, digits with an optional fraction, an optional exponent;
# not nan, inf, padding, digit separators or non-ASCII digits
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _is_number(text):
    return _NUMBER.fullmatch(text) is not None


def detect_format(path):
    """
    Return the quantifier format of the file at *path*, one of
    ``GATHER_FORMATS``, from its first lines: salmon and kallisto by their
    exact header, featureCounts by its ``# Program:featureCounts`` line or
    its ``Geneid Chr Start End Strand Length`` header, htseq-count by a
    header-less first line of tab-separated fields whose fields after the
    first are integers. Raises ``ValueError`` when none matches.
    """
    first = _first_line(path)
    if first.startswith("# Program:featureCounts"):
        return "featurecounts"
    header = _first_line(path, _leading_comments(path)).split("\t")
    if header == _SALMON_HEADER:
        return "salmon"
    if header == _KALLISTO_HEADER:
        return "kallisto"
    if header[: len(_FEATURECOUNTS_ANNOT)] == _FEATURECOUNTS_ANNOT and len(header) > 6:
        return "featurecounts"
    if len(header) >= 2 and all(re.fullmatch(r"-?[0-9]+", f) for f in header[1:]):
        return "htseq"
    raise ValueError(
        f"could not detect the format of {path}: its first line is not a salmon, "
        "kallisto, htseq-count or featureCounts header; pass --format"
    )


def _read_quant(path, fmt):
    "Read the file at *path* in format *fmt* as text, IDs and values as written."
    opts = dict(sep="\t", dtype=str, keep_default_na=False, na_filter=False)
    if fmt == "htseq":
        return pandas.read_csv(path, header=None, **opts)
    return pandas.read_csv(path, skiprows=_leading_comments(path), **opts)


def _default_names(sources):
    """Sample names from *sources* (paths): the file name without its last
    extension, or, when those are not unique among *sources*, every sample's
    parent directory name (all or nothing, so a name can depend on the other
    files in the run: a lone ``s1/quant.sf`` is ``quant``)."""
    import os

    stems = [os.path.splitext(os.path.basename(s))[0] for s in sources]
    if len(set(stems)) == len(stems):
        return stems
    parents = [os.path.basename(os.path.dirname(os.path.normpath(s))) for s in sources]
    if all(parents) and len(set(parents)) == len(parents):
        return parents
    raise ValueError(
        "could not derive unique sample names from the file names or their "
        "directories; pass --name-from"
    )


def _names_from(sources, pattern):
    regex = re.compile(pattern)
    names = []
    for s in sources:
        m = regex.search(s)
        if m is None:
            raise ValueError(f"--name-from {pattern!r} does not match {s!r}")
        name = m.group(1) if regex.groups else m.group(0)
        if not name:
            raise ValueError(f"--name-from {pattern!r} gives an empty name for {s!r}")
        names.append(name)
    return names


class Gather(DetkModule):
    """
    Gather one column from each of the per-sample quantifier outputs at
    *paths* into a counts matrix: a row per feature, a column per sample.

    *fmt* is one of ``GATHER_FORMATS`` or ``"auto"`` (detected per file by
    :func:`detect_format`; every file must have the same format). *column*
    names the column to extract, by name or 0-based position; by default the
    format's count column (``NumReads``, ``est_counts``, the htseq count, or
    every count column of a featureCounts file); an htseq file with more than
    one count column is refused unless *column* is given. Feature IDs and
    values are kept as text, as written; every value must be a plain finite
    decimal number (see ``_NUMBER``). htseq-count's
    summary lines (IDs starting with ``__``) are left out and recorded in the
    properties.

    Sample names come from the paths (see :func:`_default_names`) or, with
    *name_from*, from a regular expression's first group or whole match. A
    featureCounts count column is named from its header (the BAM file's
    path) instead of the file's path.

    The rows follow the first sample's features. When the samples do not
    list the same features, *on_mismatch* decides: ``"error"`` raises
    ``ValueError`` naming the differences, ``"fill"`` keeps every feature
    (those only some samples list are appended in order of appearance) and
    fills the absent cells with ``"0"``, ``"drop"`` keeps only the features
    every sample lists.
    """

    def __init__(self, paths, fmt="auto", column=None, name_from=None, on_mismatch="error"):
        paths = [str(p) for p in paths]
        self["params"] = {
            "files": paths,
            "format": fmt,
            "column": column,
            "name_from": name_from,
            "on_mismatch": on_mismatch,
        }
        if not paths:
            raise ValueError("no input files")
        if on_mismatch not in _MISMATCH:
            raise ValueError(f"--on-mismatch must be one of {', '.join(_MISMATCH)}")

        if fmt == "auto":
            fmts = {p: detect_format(p) for p in paths}
            found = sorted(set(fmts.values()))
            if len(found) > 1:
                first = {}
                for p, f in fmts.items():
                    first.setdefault(f, p)
                examples = ", ".join(f"{p} is {f}" for f, p in first.items())
                raise ValueError(f"the files are not all the same format: {examples}")
            fmt = found[0]
        elif fmt not in GATHER_FORMATS:
            raise ValueError(f"--format must be auto or one of {', '.join(GATHER_FORMATS)}")
        logger.info("format: %s", fmt)
        column_given = column is not None
        if column is None:
            column = _DEFAULT_COLUMN[fmt]

        # extract (source, ids, values) per sample, sources naming them
        sources, columns, counters = [], [], {}
        for path in paths:
            df = _read_quant(path, fmt)
            if df.shape[1] < 2:
                raise ValueError(f"{path} has fewer than two columns; is it {fmt} output?")
            ids = df.iloc[:, 0]
            if fmt == "htseq" and df.shape[1] > 2 and not column_given:
                # htseq-count 0.13+ given several BAMs writes a count column
                # per BAM and no header to name them: refuse rather than
                # keep the first and lose the others
                raise ValueError(
                    f"{path} has {df.shape[1] - 1} count columns (htseq-count run on "
                    "several BAM files), and htseq-count writes no header naming "
                    "them; pass --column=N to gather the count column at 0-based "
                    "position N, or run htseq-count once per sample"
                )
            if column is None:  # every featureCounts count column
                names = list(df.columns[len(_FEATURECOUNTS_ANNOT) :])
                if not names:
                    raise ValueError(f"{path} has no count columns after Length")
            else:
                names = [_resolve_column(df, column, "--column")]
            keep = pandas.Series(True, index=df.index)
            if fmt == "htseq":
                keep = ~ids.str.startswith("__")
            for name in names:
                # featureCounts names its count columns after the BAM files
                source = str(name) if fmt == "featurecounts" else path
                values = df[name]
                if fmt == "htseq":
                    for cid, v in zip(ids[~keep], values[~keep]):
                        counters.setdefault(cid, {})[len(sources)] = (
                            float(v) if _is_number(v) else v
                        )
                col = pandas.Series(values[keep].to_numpy(), index=ids[keep].to_numpy())
                bad = [v for v in col if not _is_number(v)]
                if bad:
                    raise ValueError(
                        f"{source}: column {name!r} holds non-numeric values, e.g. {bad[0]!r}"
                    )
                dup = col.index[col.index.duplicated()]
                if len(dup):
                    raise ValueError(f"{source}: feature {dup[0]!r} is listed more than once")
                sources.append(source)
                columns.append(col)

        samples = _names_from(sources, name_from) if name_from else _default_names(sources)
        if len(set(samples)) != len(samples):
            dup = pandas.Series(samples)[pandas.Series(samples).duplicated()].iloc[0]
            raise ValueError(f"sample name {dup!r} is given by more than one file")
        logger.info("samples: %s", ", ".join(samples))

        # the features: the first sample's order, then any others as they appear
        union = pandas.Index(columns[0].index)
        for col in columns[1:]:
            union = union.append(col.index.difference(union, sort=False))
        absent = {s: union.difference(c.index, sort=False) for s, c in zip(samples, columns)}
        mismatched = {s: a for s, a in absent.items() if len(a)}
        shared = union
        for col in columns:
            shared = shared.intersection(col.index, sort=False)

        if mismatched and on_mismatch == "error":
            detail = "; ".join(
                f"{s} lacks {len(a)} (e.g. {', '.join(map(str, a[:3]))})"
                for s, a in list(mismatched.items())[:5]
            )
            raise ValueError(
                f"the samples do not list the same features ({len(union)} in all, "
                f"{len(shared)} in every sample): {detail}; check that every sample "
                "was quantified against the same annotation, or pass "
                "--on-mismatch=fill or --on-mismatch=drop"
            )
        rows = shared if on_mismatch == "drop" else union
        out = pandas.concat([c.reindex(rows) for c in columns], axis=1, keys=samples)
        num_filled = int(out.isna().sum().sum())
        out = out.fillna("0")
        out.index.name = None
        self._output = out

        dropped = union.difference(shared, sort=False) if on_mismatch == "drop" else union[:0]
        filled = union.difference(shared, sort=False) if on_mismatch == "fill" else union[:0]
        self["params"]["format"] = fmt
        self["params"]["column"] = column
        self["properties"] = {
            "format": fmt,
            "column": None if column is None else str(column),
            "num_files": len(paths),
            "num_samples": len(samples),
            "num_features": int(out.shape[0]),
            "num_features_all": int(len(union)),
            "num_features_shared": int(len(shared)),
            "num_features_dropped": int(len(dropped)),
            "num_features_filled": int(len(filled)),
            "num_values_filled": num_filled,
            "samples": [
                {
                    "name": s,
                    "source": src,
                    "num_features": int(len(c)),
                    "num_absent": int(len(absent[s])),
                }
                for s, src, c in zip(samples, sources, columns)
            ],
            "mismatch_examples": [str(f) for f in union.difference(shared, sort=False)[:10]],
            "htseq_counters": {
                k: {samples[i]: v for i, v in byidx.items()} for k, byidx in counters.items()
            },
        }
        logger.info("gathered %d features from %d samples", out.shape[0], out.shape[1])
        if mismatched:
            logger.warning(
                "the samples do not list the same features: %d %s",
                len(dropped) or len(filled),
                "dropped" if on_mismatch == "drop" else "filled with 0 where absent",
            )

    @property
    def output(self):
        return self._output


def gather(paths, **kwargs):
    "Return the counts matrix gathered from *paths*; see :class:`Gather`."
    return Gather(paths, **kwargs).output


def _natural_key(text):
    "Sort key comparing runs of digits in *text* as numbers."
    return [(0, int(t), t) if t.isdigit() else (1, 0, t) for t in re.split(r"([0-9]+)", text)]


def _expand_paths(args):
    """The paths given on the command line, with any argument that is not a
    file but holds a wildcard expanded as a glob in natural order (runs of
    digits compare as numbers, so ``s2`` comes before ``s10``)."""
    import glob
    import os

    paths = []
    for arg in args:
        if not os.path.exists(arg) and any(c in arg for c in "*?["):
            matched = sorted(glob.glob(arg), key=_natural_key)
            if not matched:
                raise ValueError(f"no files match {arg!r}")
            paths.extend(matched)
        else:
            paths.append(arg)
    return paths


def _gather_main(args):
    import os

    from .report import DetkReport

    gathered = Gather(
        _expand_paths(args.files),
        fmt=args.format,
        column=args.column,
        name_from=args.name_from,
        on_mismatch=args.on_mismatch,
    )

    write_output(gathered.output, args)

    if not args.no_report:
        # there are many inputs and the module JSON has one input slot; the
        # files are listed in the parameters (params["files"]) instead
        logging.info("writing report to %s", args.report_dir)
        with DetkReport(args.report_dir) as r:
            r.add_module(gathered, out_file_path=args.output, workdir=os.getcwd())

    logging.info("done")


# ---------------------------------------------------------------------------
# record: run an external command and record it as a step (DETK-0051, DETK-0061)
# ---------------------------------------------------------------------------

# seconds '<tool> --version' may take before the version is recorded unknown
VERSION_TIMEOUT = 10
UNKNOWN_VERSION = "unknown"


def file_digest(path):
    "The SHA-256 checksum (hex) and size in bytes of the file at *path*"
    import hashlib

    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
            size += len(block)
    return {"path": path, "sha256": h.hexdigest(), "size": size}


def probe_version(executable, timeout=VERSION_TIMEOUT):
    """
    The first non-empty line ``<executable> --version`` prints (on stdout,
    else stderr), or None when it is not found, fails, prints nothing or
    takes longer than *timeout* seconds. Its output is captured, never shown.
    """
    import subprocess

    try:
        p = subprocess.run(
            [executable, "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    for text in (p.stdout, p.stderr):
        for line in text.splitlines():
            if line.strip():
                return line.strip()
    return None


class Record(DetkModule):
    """
    The record of an external command run as a step of the analysis: *argv*
    the command and its arguments, *tool* and *tool_version* the software
    that ran, *inputs* and *outputs* the files it read and wrote (as given),
    *input_digests* and *output_digests* their :func:`file_digest`, and
    *exit_status* the command's exit status.

    :func:`run_record` runs the command and builds one; the module JSON holds
    the command, tool, version and file lists in ``params`` and each file's
    checksum and size in ``properties``.
    """

    def __init__(
        self,
        argv,
        tool,
        tool_version,
        inputs,
        outputs,
        input_digests,
        output_digests,
        exit_status=0,
    ):
        import shlex

        self["params"] = {
            "command": shlex.join(argv),
            "argv": list(argv),
            "tool": tool,
            "tool_version": tool_version,
            "inputs": list(inputs),
            "outputs": list(outputs),
        }
        self["properties"] = {
            "inputs": list(input_digests),
            "outputs": list(output_digests),
            "exit_status": exit_status,
        }

    def relative_to(self, workdir):
        """Write every absolute path in the record relative to the absolute
        directory *workdir* (DETK-0281): the command's arguments, the input
        and output lists and the checksums' paths; the command string is
        rebuilt from the arguments. Returns the record."""
        import shlex

        from .report import _file_relpath, relative_argv

        params, props = self["params"], self["properties"]
        params["argv"] = relative_argv(params["argv"], workdir)
        params["command"] = shlex.join(params["argv"])
        params["inputs"] = [_file_relpath(p, workdir) for p in params["inputs"]]
        params["outputs"] = [_file_relpath(p, workdir) for p in params["outputs"]]
        for key in ("inputs", "outputs"):
            props[key] = [
                d | {"path": _file_relpath(d["path"], workdir)} if isinstance(d, dict) else d
                for d in props[key]
            ]
        return self


def run_record(argv, inputs=(), outputs=(), tool=None, tool_version=None):
    """
    Run the command *argv* (a list, run without a shell, with this process's
    stdin, stdout and stderr) and return its :class:`Record`.

    Raises ``ValueError`` naming the file when an input does not exist
    before the run or an output does not exist after it, and
    ``RuntimeError`` when the command is not found, cannot be run or exits
    non-zero. Nothing is recorded then, and no file is deleted or changed.
    """
    import os
    import shlex
    import subprocess

    argv = list(argv)
    inputs, outputs = list(inputs), list(outputs)
    if not argv:
        raise ValueError("no command to run")
    if not outputs:
        raise ValueError("at least one output file is required")
    for path in inputs:
        if not os.path.isfile(path):
            raise ValueError(f"input file {path} does not exist")
    input_digests = [file_digest(p) for p in inputs]

    command = shlex.join(argv)
    logger.info("running: %s", command)
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        status = subprocess.run(argv).returncode
    except FileNotFoundError:
        raise RuntimeError(f"command not found: {argv[0]}") from None
    except OSError as e:
        raise RuntimeError(f"command {argv[0]} could not be run: {e.strerror or e}") from None
    if status < 0:
        raise RuntimeError(f"command was killed by signal {-status}: {command}")
    if status != 0:
        raise RuntimeError(f"command failed with exit status {status}: {command}")

    for path in outputs:
        if not os.path.isfile(path):
            raise ValueError(f"output file {path} was not written by the command: {command}")
    output_digests = [file_digest(p) for p in outputs]

    executable = os.path.basename(argv[0])
    if tool is None:
        tool = executable
    if tool_version is None:
        # the command's first word is asked only for its own version: with
        # --tool naming another tool (sh -c '...', Rscript), it is unknown
        found = probe_version(argv[0]) if tool == executable else None
        if found is None:
            logger.warning(
                "the version of %s is not known; recording %r (give it with --tool-version)",
                tool,
                UNKNOWN_VERSION,
            )
        tool_version = found or UNKNOWN_VERSION
    logger.info("recorded %s %s", tool, tool_version)

    return Record(argv, tool, tool_version, inputs, outputs, input_digests, output_digests, status)


def _record_main(args):
    import os

    from .report import DetkReport

    inputs = args.input or []
    record = run_record(
        args.command,
        inputs=inputs,
        outputs=args.output,
        tool=args.tool,
        tool_version=args.tool_version,
    )

    if not args.no_report:
        logging.info("writing report to %s", args.report_dir)
        # the command ran as typed; it is recorded with no absolute path
        record.relative_to(os.getcwd())
        with DetkReport(args.report_dir) as r:
            r.add_module(
                record,
                in_file_path=inputs[0] if inputs else None,
                out_file_path=args.output[0],
                workdir=os.getcwd(),
                in_file_paths=inputs,
                out_file_paths=list(args.output),
            )

    logging.info("done")


@cli_main
def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    cmd = args.subcommand
    argv = argv[1:]

    if cmd == "annotate":
        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))
        return _annotate_main(args)

    if cmd == "gather":
        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))
        return _gather_main(args)

    if cmd == "record":
        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))
        return _record_main(args)

    set_logging(args)
    logger.info("cmd: %s", " ".join(argv))
    return _tidy_main(args)


if __name__ == "__main__":
    main()
