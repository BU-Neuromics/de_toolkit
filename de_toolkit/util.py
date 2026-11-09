r"""
Usage:
    detk-util tidy [options] <counts_fn> <cov_fn>
    detk-util tidy-counts [options] <counts_fn> <cov_fn>
    detk-util tidy-covs [options] <counts_fn> <cov_fn>
    detk-util annotate [options] <result_fn> <mapping_fn>
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
delimited text files whose delimiter is sniffed. Rows of the result table keep
their order and number: an ID with several mapping rows gets the distinct
values joined with ';', and an ID with no mapping row gets empty columns
unless --drop-unmapped is given. Columns are given by name or by 0-based
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
    vals = [v for v in pandas.unique(values) if not pandas.isna(v)]
    return ";".join(str(v) for v in vals) if vals else None


class Annotate(DetkModule):
    """
    Annotate the rows of *result* with columns of *mapping*, joined on the
    feature IDs.

    The rows of *result* keep their order and, unless *drop_unmapped*, their
    number. An ID with several mapping rows gets the distinct values of each
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

        result_keys = result[id_name].astype(str)
        mapping = mapping[[from_name] + to_names].dropna(subset=[from_name])
        mapping[from_name] = mapping[from_name].astype(str)
        if strip_versions:
            result_keys = _strip_versions(result_keys)
            mapping[from_name] = _strip_versions(mapping[from_name])

        counts = mapping[from_name].value_counts()
        collapsed = mapping.groupby(from_name, sort=False)[to_names].agg(_join_distinct)

        renamed = {c: f"{c}_annot" if c in result.columns else c for c in to_names}
        added = collapsed.reindex(result_keys.values).rename(columns=renamed)
        added.index = result.index

        mapped = result_keys.isin(collapsed.index).to_numpy()
        out = pandas.concat([result, added], axis=1)
        if drop_unmapped:
            out = out.loc[mapped]
        out = out.set_index(id_name)
        if str(id_name).startswith("Unnamed: "):
            # an unnamed index column, as pandas writes it, stays unnamed
            out.index.name = None
        self._output = out

        unmapped_ids = result.loc[~mapped, id_name].astype(str)
        self["properties"] = {
            "num_features": int(result.shape[0]),
            "num_mapped": int(mapped.sum()),
            "num_unmapped": int((~mapped).sum()),
            "num_multimapped": int(result_keys[mapped].map(counts).gt(1).sum()),
            "num_dropped": int((~mapped).sum()) if drop_unmapped else 0,
            "columns_added": list(renamed.values()),
            "unmapped_examples": unmapped_ids.head(10).tolist(),
        }
        logger.info(
            "features mapped: %d of %d (%d with several mapping rows)",
            self["properties"]["num_mapped"],
            self["properties"]["num_features"],
            self["properties"]["num_multimapped"],
        )
        if self["properties"]["num_unmapped"]:
            logger.warning(
                "%d features had no mapping, e.g. %s%s",
                self["properties"]["num_unmapped"],
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
        result = pandas.read_csv(args["<result_fn>"], sep=None, engine="python")
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
