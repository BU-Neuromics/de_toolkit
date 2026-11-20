r"""
Gene set enrichment of a differential expression result: rank its features
by a statistic and test the gene sets of a GMT file for enrichment at the
top or bottom of the ranking (fgsea).
"""

todo = r"""
    detk-enrich fisher [options] <gmt_fn> <result_fn>
"""

# each subcommand: the one line the command's help lists it with, its
# description and its examples
SUBCOMMANDS = {
    "fgsea": dict(
        help="Preranked gene set enrichment with fgsea (needs R and fgsea)",
        description="""\
Perform preranked Gene Set Enrichment Analysis using the fgsea bioconductor
package on the given gmt gene set file.

The GMT file must be tab delimited with set name in the first column, a
description in the second column (ignored by detk), and an individual feature
ID in each column after, one feature set per line. The result file can be any
character delimited file, and is assumed to have column names in the first row.

The feature IDs must be from the same system (e.g. gene symbols, ENSGIDs, etc)
in both GMT and result files. The user will likely have to provide:

- -i COL: column in the results file that contains feature IDs
- -c COL: column in the results file that contains the statistics to
  use when computing enrichment, e.g. log2FoldChange

fgsea: https://bioconductor.org/packages/release/bioc/html/fgsea.html""",
        examples=[
            (
                "Rank the genes of deseq2_results.csv by log2FoldChange and test the "
                "sets in genesets.gmt",
                "detk-enrich fgsea -i gene -c log2FoldChange -o fgsea.csv "
                "genesets.gmt deseq2_results.csv",
            ),
        ],
    ),
}


def build_parser():
    "The detk-enrich command line parser"
    parser = DetkParser(prog="detk-enrich", description=__doc__.strip())
    add_command_options(parser)
    subs = add_subcommands(parser)
    spec = SUBCOMMANDS["fgsea"]
    sub = subs.add_parser(
        "fgsea", help=spec["help"], description=spec["description"], examples=spec["examples"]
    )
    sub.add_argument(
        "gmt_fn", metavar="<gmt_fn>", help="Gene sets in GMT format: name, description, IDs"
    )
    sub.add_argument(
        "result_fn",
        metavar="<result_fn>",
        help="Delimited result file with column names, such as a detk-de result",
    )
    sub.add_argument(
        "-o", "--output", metavar="FILE", default="stdout", help="Destination of fgsea output"
    )
    sub.add_argument(
        "-p",
        "--cores",
        metavar="N",
        help="Number of processes fgsea uses (needs the BiocParallel package)",
    )
    sub.add_argument(
        "-i",
        "--idcol",
        metavar="COL",
        default="0",
        help="Column (name or 0-based index) holding the feature IDs",
    )
    sub.add_argument(
        "-c",
        "--statcol",
        metavar="COL",
        help="Column (name or 0-based index) of the ranking statistic; "
        "the last numeric column if not given",
    )
    sub.add_argument(
        "-a",
        "--ascending",
        action="store_true",
        help="Rank ascending (for p-values, or to reverse the sign of NES)",
    )
    sub.add_argument(
        "--abs", action="store_true", help="Rank by the absolute value of the statistic"
    )
    sub.add_argument(
        "--filter-unannotated",
        action="store_true",
        help="Drop the features whose IDs are in no gene set of the GMT",
    )
    sub.add_argument("--minSize", metavar="N", default="15", help="minSize argument to fgsea")
    sub.add_argument("--maxSize", metavar="N", default="500", help="maxSize argument to fgsea")
    sub.add_argument("--nperm", metavar="N", default="10000", help="nperm argument to fgsea")
    sub.add_argument(
        "--multilevel", action="store_true", help="Use the fgseaMultilevel function, not fgsea"
    )
    sub.add_argument(
        "--routput-dir",
        metavar="DIR",
        help="Directory to keep the R script, its inputs and outputs in, for debugging",
    )
    sub.add_argument("--rda", metavar="FILE", help="File to saveRDS() the fgsea result to")
    add_common_options(sub)
    return parser


from collections import namedtuple, OrderedDict
import csv
from functools import reduce
import logging
import math
import os
import pandas
from pprint import pformat
import tempfile
import sys
import warnings
from .common import (
    cli_main,
    option_value,
    DetkModule,
    DetkParser,
    add_command_options,
    add_common_options,
    add_subcommands,
    parse_cli,
    read_delimited,
    set_logging,
    write_output,
)
from .wrapr import require_r, wrapr
from .report import DetkReport

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# number of top gene sets (by adjusted p-value) emitted for the report chart
_FGSEA_TOP = 30
_FGSEA_SIG_THRESHOLD = 0.05


def _fgsea_report_data(df):
    """Chart-ready summary of an fgsea result table.

    Adjusted p-values are emitted both as -log10 (for the color scale) and as
    preformatted strings (for tooltips): the module JSON encoder rounds floats
    to 3 decimals, which would destroy small p-values.
    """
    d = df.copy()
    for c in ("padj", "NES"):
        if c in d.columns:
            d[c] = pandas.to_numeric(d[c], errors="coerce")
    if "padj" not in d.columns or "pathway" not in d.columns:
        return {"num_sig": None, "pathways": []}
    d = d.dropna(subset=["padj"]).sort_values("padj")
    num_sig = int((d["padj"] < _FGSEA_SIG_THRESHOLD).sum())
    top = d.head(_FGSEA_TOP)
    pathways = [
        {
            "pathway": str(r["pathway"]),
            "nes": float(r["NES"]) if "NES" in top.columns and pandas.notna(r["NES"]) else None,
            "size": int(r["size"]) if "size" in top.columns and pandas.notna(r["size"]) else None,
            "nlpadj": float(-math.log10(max(r["padj"], 1e-300))),
            "padj_str": f"{r['padj']:.2e}",
            "sig": bool(r["padj"] < _FGSEA_SIG_THRESHOLD),
        }
        for _, r in top.iterrows()
    ]
    return {
        "num_sig": num_sig,
        "sig_threshold": _FGSEA_SIG_THRESHOLD,
        "top_n": len(pathways),
        "pathways": pathways,
    }


GeneSet = namedtuple("GeneSet", ("name", "desc", "ids"))


class GMT(OrderedDict):
    def __init__(self, sets=None):
        super().__init__()
        for name, ids in (sets or {}).items():
            self[name] = ids

    def __setitem__(self, name, ids):
        self.add(name, ids)

    def add(self, name, ids, desc=None):
        OrderedDict.__setitem__(self, name, GeneSet(name, desc or name, ids))

    def load_file(self, fn):
        self.fn = fn
        with open(fn, encoding="utf-8") as f:
            for r in csv.reader(f, delimiter="\t"):
                self.add(r[0], r[2:], desc=r[1])
                # self[r[0]] = [_.strip() for _ in r[2:]]

    def write_file(self, out_fn):
        with open(out_fn, "w", encoding="utf-8") as f:
            out_f = csv.writer(f, delimiter="\t")
            for k, v in self.items():
                out_f.writerow([k, k] + list(v.ids))


def fgsea(
    gmt, stat, minSize=15, maxSize=500, nperm=10000, multilevel=False, nproc=None, rda_fn=None
):
    """
    Perform pre-ranked Gene Set Enrichment Analysis using the fgsea Bioconductor
    package

    Compute GSEA enrichment using the provided gene sets in the GMT object *gmt*
    using the statistics in the pandas.Series *stat*. The fgsea Bioconductor
    package must be installed on your system for this function to work.

    The output dataframe contains one result row per features set in the GMT
    file, in the same order. Output columns include:

    - name: name of feature set
    - ES: GSEA enrichment score
    - NES: GSEA normalized enrichment score
    - pval: nominal p-value
    - padj: Benjamini-Hochberg adjusted p-value
    - nMoreExtreme: number of permutations with a more extreme NES than true
    - size: number of features in the feature set
    - leadingEdge: the leading edge features as defined by GSEA (string with
      space-separated feature names)
    """
    obj = FGSEARes(gmt, stat, minSize, maxSize, nperm, multilevel, nproc, rda_fn)
    return obj.output


class FGSEARes(DetkModule):
    @require_r("fgsea")
    def __init__(
        self,
        gmt,
        stat,
        minSize=15,
        maxSize=500,
        nperm=10000,
        multilevel=True,
        nproc=None,
        filter_unannotated=False,
        rda_fn=None,
        routput_dir=None,
    ):
        self["params"] = {
            "minSize": minSize,
            "maxSize": maxSize,
            "nperm": nperm,
            "multilevel": multilevel,
            "nproc": nproc,
            "rda_fn": rda_fn,
        }
        self.gmt = gmt
        gmt_ids = reduce(lambda a, b: set(a).union(set(b)), (_.ids for _ in gmt.values()))

        # GMT IDs are always strings, but pandas parses an all-integer ID
        # column (e.g. Entrez gene IDs) as int64, which silently matched
        # nothing; compare as strings on both sides
        gmt_ids = {str(_) for _ in gmt_ids}
        if not stat.index.isnull().any():
            stat = stat.copy()
            stat.index = stat.index.map(str)

        # check for NAs in the stat
        if stat.isnull().any():
            nas = stat[stat.isnull()]
            msg = f"The following statistics were NaN and were filtered prior to fgsea:\n{nas}"
            warnings.warn(msg, stacklevel=2)
            logger.warning(msg)
            stat = stat[~stat.isnull()]

        # check for anything that isn't a string in the stat names
        if stat.index.isnull().any():
            null_mask = stat.index.isnull()
            nas = stat[null_mask]
            msg = f'The following statistic names were NaN and cast to unique "null_N" names prior to fgsea:\n{nas}'
            warnings.warn(msg, stacklevel=2)
            logger.warning(msg)
            # each null name must be given a unique placeholder: fgsea rejects
            # duplicate names(stats), so a single "null" for every NaN name would
            # crash on >1 NaN. Rebuild positionally because None/NaN index labels
            # cannot be reliably remapped via a dict (NaN keys collapse).
            new_index = list(stat.index)
            for i, is_null in enumerate(null_mask):
                if is_null:
                    new_index[i] = f"null_{i}"
            stat = stat.copy()
            stat.index = new_index

        if filter_unannotated:
            logger.info("filtering out features without annotation in GMT")
            logger.info(f"{len(gmt_ids)} unique IDs found in GMT")
            annotated_ids = stat.index.intersection(gmt_ids)
            logger.info(
                f"{len(annotated_ids)}/{stat.index.size} ({100 * len(annotated_ids) / stat.index.size:.2f}%) of features retained"
            )

            stat = stat.loc[annotated_ids]

        # make sure at least some IDs match
        if not any(_ in gmt_ids for _ in stat.index):
            err = (
                "No features map between GMT file and results. Check that the "
                "feature ID types match between your results and GMT."
            )
            logger.error(err)
            raise Exception(err)

        script = """\
        library(fgsea)
        library(data.table)
        library(BiocParallel)
        register(SerialParam())

        # ensure that execution is set to serial if no cores are specified
        # overrides potentially default behavior of bpparam() returning
        # registered parallel backend using all available cores, which is stupid
        if(params$nproc != 0) {
            bp.param <- fgsea:::setUpBPPARAM(nproc=params$nproc)
        } else {
            bp.param <- SerialParam()
        }

        ranks <- setNames(params$stat,params$id)
        pathways <- gmtPathways(params$gmt.fn)

        cat('relevant params:')
        str(params[c('minSize','maxSize','sampleSize','nproc','multilevel')])

        if(!is.null(params$multilevel) && params$multilevel==TRUE) {
            cat('running in multilevel mode')
            fgseaRes <- fgseaMultilevel(
                pathways,
                ranks,
                minSize=params$minSize,
                maxSize=params$maxSize,
                sampleSize=params$nperm,
                BPPARAM=bp.param
            )
        } else {
            cat('running in normal mode')
            fgseaRes <- fgsea(
                pathways,
                ranks,
                minSize=params$minSize,
                maxSize=params$maxSize,
                nperm=params$nperm,
                BPPARAM=bp.param
            )
        }
        if(!is.null(params$rda.fn)) {
            cat('saving fgsea output to RDS file')
            saveRDS(
                list(
                    fgseaRes=fgseaRes,
                    pathways=pathways,
                    ranks=ranks,
                    params=params
                ),
                file=params$rda.fn
            )
        }
        fwrite(fgseaRes,file=out.fn,sep=",",sep2=c("", " ", ""))
        """
        logger.debug("fgsea R script:\n%s", script)

        # need to write out the gmt to file
        with tempfile.NamedTemporaryFile() as f:
            gmt.write_file(f.name)
            params = {
                "gmt.fn": os.path.realpath(f.name),
                "stat": stat.tolist(),
                "id": stat.index.tolist(),
                "minSize": minSize,
                "maxSize": maxSize,
                "multilevel": multilevel,
                "nperm": nperm,
                "rda.fn": rda_fn,
                "nproc": nproc or 0,
            }
            logger.debug("fgsea wrapr params:\n%s", pformat(params))
            with wrapr(script, params=params, raise_on_error=True, routput_dir=routput_dir) as r:
                gsea_res = r.output

        self.gsea_res = gsea_res
        logger.info("shape of fgsea result dataframe: %s", gsea_res.shape)

        logger.info("fgsea done")

    @property
    def properties(self):
        return {
            "num_pathways": len(self.gsea_res),
            "fgsea": _fgsea_report_data(self.gsea_res),
        }

    @property
    def output(self):
        return self.gsea_res


def _numeric_or_text(col):
    "*col* (text) as numbers when every value parses as one, else unchanged."
    try:
        return pandas.to_numeric(col)
    except (ValueError, TypeError):
        return col


def _resolve_result_column(res_df, col, what):
    "The name of column *col* of *res_df*: a column name or a 0-based index."
    if col in res_df.columns:
        return col
    try:
        pos = int(col)
    except (TypeError, ValueError):
        pos = None
    if pos is None or not 0 <= pos < len(res_df.columns):
        raise ValueError(
            f"{what} column {col} could not be found in the results or "
            "interpreted as an integer index, aborting"
        )
    return res_df.columns[pos]


def read_result_stat(result_fn, idcol=0, statcol=None):
    """
    Read the result table *result_fn* (any delimited file, see
    :func:`de_toolkit.common.read_delimited`) and return the ranking
    statistic for fgsea: a pandas.Series of column *statcol* (a column name
    or 0-based index; by default the last numeric column) indexed by the IDs
    in column *idcol* (a name or 0-based index, by default the first).

    The IDs are read as text, exactly as written, so ``007`` stays ``007``
    and matches ``007`` in the GMT file even when every ID in the column
    looks like a number; the other columns are numbers when every value in
    them parses as one.
    """
    res_df = read_delimited(result_fn, dtype=str)
    logger.info("result data frame shape: %s", res_df.shape)
    idcol = _resolve_result_column(res_df, 0 if idcol is None else idcol, "ID")
    for c in res_df.columns:
        if c != idcol:
            res_df[c] = _numeric_or_text(res_df[c])
    logger.info("using %s as identifier column", idcol)

    if statcol is not None:
        statcol = _resolve_result_column(res_df, statcol, "Stat")
    else:
        # pick the last numeric column
        numeric = [
            c for c in res_df.columns if c != idcol and pandas.api.types.is_numeric_dtype(res_df[c])
        ]
        if not numeric:
            raise ValueError("no numeric column found in the results to use as the statistic")
        statcol = numeric[-1]
    logger.info("using %s as statistic column", statcol)

    stat = pandas.to_numeric(res_df[statcol])
    stat.index = pandas.Index(res_df[idcol], name=idcol)
    return stat


@cli_main
def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    # fgsea, the only subcommand
    logger.info("reading in GMT file %s", args.gmt_fn)
    gmt = GMT()
    gmt.load_file(args.gmt_fn)

    logger.info("reading in results file %s", args.result_fn)
    stat = read_result_stat(args.result_fn, idcol=args.idcol, statcol=args.statcol)

    cores = None if args.cores is None else option_value(args, "cores")

    if args.abs:
        logger.info("taking absolute value of statistic column due to --abs")
        stat = stat.abs()

    if args.ascending:
        logger.info("sorting statistic into ascending order due to --ascending")
        stat = -stat

    out = FGSEARes(
        gmt,
        stat,
        minSize=option_value(args, "minSize"),
        maxSize=option_value(args, "maxSize"),
        nperm=option_value(args, "nperm"),
        multilevel=args.multilevel,
        nproc=cores,
        filter_unannotated=args.filter_unannotated,
        rda_fn=args.rda,
        routput_dir=args.routput_dir,
    )

    write_output(out.output, args)

    if not args.no_report:
        logging.info("writing report to %s", args.report_dir)
        with DetkReport(args.report_dir) as r:
            r.add_module(
                out,
                in_file_path=args.gmt_fn,
                out_file_path=args.output,
                workdir=os.getcwd(),
            )
    else:
        logging.info("not generating report due to --no-report")

    logging.info("done")


if __name__ == "__main__":
    main()
