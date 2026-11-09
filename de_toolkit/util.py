r"""
Usage:
    detk-util tidy [options] <counts_fn> <cov_fn>
    detk-util tidy-counts [options] <counts_fn> <cov_fn>
    detk-util tidy-covs [options] <counts_fn> <cov_fn>
    detk-util annotate [options] <result_fn> <mapping_fn>
    detk-util gather [options] <files>...
"""

cmd_opts = {
    "tidy": r"""

Subset both the counts columns and column data rows by intersection, returning
new outputs for both. Note the tidied column data is not output by default, and
the user must specify the -p argument to obtain it.

Usage:
    detk-util tidy [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
    -p FILE --column-data-output=FILE  Destination of tidied column data
""",
    "tidy-counts": r"""

Subset and order the provided counts file columns according to the rows of the
provided column data file. Operation will fail if there are rows in the column
data file that do not exist as columns in the counts file.

Usage:
    detk-util tidy-counts [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
""",
    "tidy-covs": r"""

Subset and order the provided column data file rows according to the columns of
the provided ccounts data file. Operation will fail if there are columns in the
counts file that do not exist as rows in the column data file.


Usage:
    detk-util tidy-covs [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied column data [default: stdout]
""",
    "annotate": r"""

Annotate a result table (e.g. the output of detk-de) with feature metadata,
such as gene symbols, from a user-supplied mapping table. Both files are
delimited text files whose delimiter is sniffed; the result is read and
written back as text, so IDs such as 007 are kept as written. Rows and
columns of the result table keep their order and number, and the added
columns come last: an ID with several mapping rows gets the distinct values
joined with ';', and an ID with no mapping row (or only rows whose added
columns are empty), or an empty or NA ID, gets empty columns; to drop it,
use the option --drop-unmapped. Columns are given by name or by 0-based
position.

Usage:
    detk-util annotate [options] <result_fn> <mapping_fn>

Options:
    -i FIELD --idcol=FIELD  Column in the result file holding the feature IDs to
                            join on [default: 0]
    --map-from=COL          Column in the mapping file matching the result IDs
                            [default: 0]
    --map-to=COLS           Comma-separated mapping columns to add, or 'all' for
                            every column but --map-from [default: all]
    --strip-versions        Strip trailing .N version suffixes from Ensembl-style
                            IDs on both sides before joining
    --drop-unmapped         Drop result rows with no mapping instead of leaving
                            their added columns empty
    -o FILE --output=FILE   Destination of the annotated table [default: stdout]
""",
    "gather": r"""

Gather per-sample quantifier outputs (salmon quant.sf, kallisto abundance.tsv,
htseq-count or featureCounts output) into one counts matrix with a row per
feature and a column per sample. One column is extracted from each file as
written, without any aggregation (e.g. transcripts to genes). Feature IDs and
values are kept as written. The format is detected from each file's header
unless given with --format, and every file must have the same format. A file
argument that does not exist but holds a wildcard (*, ? or [) is expanded as a
glob, so a quoted pattern works too.

The column is given by name or 0-based position; by default it is NumReads
for salmon, est_counts for kallisto, the count column for htseq and every
count column for featureCounts. htseq-count's summary lines (__no_feature,
__ambiguous, ...) are not features: they are left out of the matrix and
recorded in the report.

Sample names come from each file's path: its file name without the last
extension, or, when those are not unique (quant.sf, abundance.tsv), the name
of the directory holding it. With --name-from, the name is the first group of
the regular expression, or else its whole match, searched in the path. In
featureCounts output each count column is a sample, named the same way from
the column's header (the BAM file's path) rather than the file's path.

Every sample must list the same features, or gather stops with an error naming
the differences: --on-mismatch=fill keeps every feature and fills the absent
ones with 0, --on-mismatch=drop keeps only the features every sample lists.

Usage:
    detk-util gather [options] <files>...

Options:
    --format=FMT           salmon, kallisto, htseq, featurecounts or auto
                           [default: auto]
    --column=COL           Column to extract from each file, by name or 0-based
                           position (default: the format's count column)
    --name-from=REGEX      Regular expression deriving each sample name from
                           its file path (the first group, or the whole match)
    --on-mismatch=WHAT     What to do when the samples list different features:
                           error, fill (with 0) or drop [default: error]
    -o FILE --output=FILE  Destination of the counts matrix [default: stdout]
""",
}

from docopt import docopt
import logging
import pandas
import sys

from .common import DetkModule, _cli_doc, set_logging, make_cli_count_obj, write_output

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

    try:
        # read as text, so numeric IDs keep their leading zeros and every
        # value is written back as it was read
        result = pandas.read_csv(
            args["<result_fn>"], sep=None, engine="python", dtype=str, keep_default_na=False
        )
        mapping = pandas.read_csv(args["<mapping_fn>"], sep=None, engine="python", dtype=str)
        logger.info("shape of result: %s", result.shape)
        logger.info("shape of mapping: %s", mapping.shape)
        annotated = Annotate(
            result,
            mapping,
            idcol=args["--idcol"],
            map_from=args["--map-from"],
            map_to=args["--map-to"],
            strip_versions=args["--strip-versions"],
            drop_unmapped=args["--drop-unmapped"],
        )
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    write_output(annotated.output, args)

    if not args["--no-report"]:
        # the module JSON has no slot for a second input file; keep the
        # mapping file's path with the parameters so the provenance names it
        annotated["params"]["mapping_fn"] = args["<mapping_fn>"]
        logging.info("writing report to %s", args["--report-dir"])
        with DetkReport(args["--report-dir"]) as r:
            r.add_module(
                annotated,
                in_file_path=args["<result_fn>"],
                out_file_path=args["--output"],
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


def _is_number(text):
    try:
        float(text)
    except ValueError:
        return False
    return True


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
    if len(header) >= 2 and all(f.strip().lstrip("-").isdigit() for f in header[1:]):
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
    extension, or the parent directory's name when those are not unique."""
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
    import re

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
    every count column of a featureCounts file). Feature IDs and values are
    kept as text, as written; every value must be a number. htseq-count's
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
        if column is None:
            column = _DEFAULT_COLUMN[fmt]

        # extract (source, ids, values) per sample, sources naming them
        sources, columns, counters = [], [], {}
        for path in paths:
            df = _read_quant(path, fmt)
            if df.shape[1] < 2:
                raise ValueError(f"{path} has fewer than two columns; is it {fmt} output?")
            ids = df.iloc[:, 0]
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


def _expand_paths(args):
    """The paths given on the command line, with any argument that is not a
    file but holds a wildcard expanded as a sorted glob."""
    import glob
    import os

    paths = []
    for arg in args:
        if not os.path.exists(arg) and any(c in arg for c in "*?["):
            matched = sorted(glob.glob(arg))
            if not matched:
                raise ValueError(f"no files match {arg!r}")
            paths.extend(matched)
        else:
            paths.append(arg)
    return paths


def _gather_main(args):
    import os

    from .report import DetkReport

    try:
        gathered = Gather(
            _expand_paths(args["<files>"]),
            fmt=args["--format"],
            column=args["--column"],
            name_from=args["--name-from"],
            on_mismatch=args["--on-mismatch"],
        )
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    write_output(gathered.output, args)

    if not args["--no-report"]:
        # there are many inputs and the module JSON has one input slot; the
        # files are listed in the parameters (params["files"]) instead
        logging.info("writing report to %s", args["--report-dir"])
        with DetkReport(args["--report-dir"]) as r:
            r.add_module(gathered, out_file_path=args["--output"], workdir=os.getcwd())

    logging.info("done")


def main(argv=sys.argv):

    if "--version" in argv:
        from .version import __version__

        print(__version__)
        return

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts):
        docopt(_cli_doc(__doc__))
    argv = argv[1:]
    cmd = argv[0]

    # add the common opts to the docopt strings
    cmd_opts_aug = {}
    for k, v in cmd_opts.items():
        cmd_opts_aug[k] = _cli_doc(v)

    args = docopt(cmd_opts_aug[cmd], argv)

    if cmd == "annotate":
        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))
        return _annotate_main(args)

    if cmd == "gather":
        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))
        return _gather_main(args)

    count_obj = make_cli_count_obj(args)
    set_logging(args)
    logger.info("cmd: %s", " ".join(argv))

    if cmd == "tidy":
        logger.info("tidying counts...")

        out = count_obj.counts

        if args["--column-data-output"]:
            logger.info("...and covs to --column-data-output=%s", args["--column-data-output"])
            count_obj.column_data.to_csv(
                args["--column-data-output"], sep=args.get("--out-delim", ",")
            )

    elif cmd in ("tidy-counts", "tidy-covs"):
        logger.info("performing %s", cmd)

        args = docopt(cmd_opts_aug[cmd], argv)
        set_logging(args)
        logger.info("cmd: %s", " ".join(argv))

        # read in the counts and covs so we can compare
        counts = pandas.read_csv(args["<counts_fn>"], index_col=0, sep=None, engine="python")
        logger.info("shape of counts: %s", counts.shape)
        covs = pandas.read_csv(args["<cov_fn>"], index_col=0, sep=None, engine="python")
        logger.info("shape of covs: %s", covs.shape)

        logger.info("shape of counts after merge: %s", count_obj.counts.shape)
        logger.info("counts columns lost: %s", counts.shape[1] - count_obj.counts.shape[1])

        logger.info("shape of covs after merge: %s", count_obj.column_data.shape)
        logger.info("cov rows lost: %s", covs.shape[1] - count_obj.column_data.shape[1])

        if cmd == "tidy-counts":
            # check to make sure the counts columns are a subset of the column
            # data rows
            if len(covs.index.difference(counts.columns)) != 0:
                logger.error(
                    Exception(
                        "tidy-counts requires that all row IDs in the "
                        "column data file exist as columns in the counts file."
                    )
                )
                sys.exit(1)
            out = count_obj.counts

        elif cmd == "tidy-covs":
            # check to make sure the column data rows are a subset of the counts
            # columns
            if len(counts.columns.difference(covs.index)) != 0:
                logger.error(
                    Exception(
                        "tidy-covs requires that all column IDs in the "
                        "counts data file exist as rows in the column data file."
                    )
                )
                sys.exit(1)
            out = count_obj.column_data

    write_output(out, args)

    logging.info("done")


if __name__ == "__main__":
    main()
