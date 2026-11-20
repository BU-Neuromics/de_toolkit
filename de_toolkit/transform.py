r"""
Transform the counts in a counts matrix: a log transform with a pseudocount
(plog), or DESeq2's variance stabilizing (vst) or regularized log (rlog)
transformation, which make the variance of a feature less dependent on its
mean. The input is a delimited counts file, features in rows and samples in
columns; the output is the transformed matrix in the same shape.
"""

_RDA_HELP = "Write the R result objects of the analysis to FILE with saveRDS()"

# each subcommand: the one line the command's help lists it with, its
# description and its examples
SUBCOMMANDS = {
    "plog": dict(
        help="log(count + pseudocount) in a given base",
        description="""\
Take the logarithm of each count plus a pseudocount: log(count + pseudocount),
in the given base.""",
        examples=[
            ("log10(count + 1) of counts.csv", "detk-transform plog -o plog.csv counts.csv"),
            ("log2(count + 0.5)", "detk-transform plog -b 2 -c 0.5 -o log2.csv counts.csv"),
        ],
    ),
    "vst": dict(
        help="DESeq2 variance stabilizing transformation (runs R)",
        description="""\
Apply the variance stabilizing transformation (varianceStabilizingTransformation)
of the DESeq2 package to the counts, blind to any design. Needs R with
DESeq2.""",
        examples=[("VST of counts.csv", "detk-transform vst -o vst.csv counts.csv")],
    ),
    "rlog": dict(
        help="DESeq2 regularized log transformation (runs R)",
        description="""\
Apply the regularized log transformation (rlog) of the DESeq2 package to the
counts. Give both <design> and <cov_fn>, or neither: with them, the design is
built from the sample information file. Needs R with DESeq2.""",
        examples=[("rlog of counts.csv", "detk-transform rlog -o rlog.csv counts.csv")],
    ),
}


def _rlog_design_and_cov_fn(args):
    "rlog takes both or neither of <design> and <cov_fn> (DETK-0033)"
    if (args.design is None) != (args.cov_fn is None):
        return "<design> and <cov_fn> go together: give both, or neither (missing: <cov_fn>)"
    return None


def build_parser():
    "The detk-transform command line parser"
    parser = DetkParser(prog="detk-transform", description=__doc__.strip())
    add_command_options(parser)
    subs = add_subcommands(parser)
    for name, spec in SUBCOMMANDS.items():
        sub = subs.add_parser(
            name,
            help=spec["help"],
            description=spec["description"],
            examples=spec["examples"],
            validate=_rlog_design_and_cov_fn if name == "rlog" else None,
        )
        sub.add_argument(
            "counts_fn",
            metavar="<counts_fn>",
            help="Counts file: features in rows, samples in columns, delimited",
        )
        if name == "rlog":
            sub.add_argument(
                "design",
                metavar="<design>",
                nargs="?",
                help="Design formula, e.g. 'counts ~ group' (with <cov_fn>)",
            )
            sub.add_argument(
                "cov_fn",
                metavar="<cov_fn>",
                nargs="?",
                help="Sample information file: samples in rows (with <design>)",
            )
        if name == "plog":
            sub.add_argument(
                "-c",
                "--pseudocount",
                metavar="N",
                default="1",
                help="The pseudocount added to each count before the log",
            )
            sub.add_argument(
                "-b", "--base", metavar="N", default="10", help="The base of the logarithm"
            )
        sub.add_argument(
            "-o",
            "--output",
            metavar="FILE",
            default="stdout",
            help="Destination of the transformed counts in CSV format",
        )
        if name in ("vst", "rlog"):
            sub.add_argument("--rda", metavar="FILE", help=_RDA_HELP)
        if name == "rlog":
            sub.add_argument(
                "--strict",
                action="store_true",
                help="Require the counts columns and the sample information rows to "
                "name the same samples in the same order",
            )
            sub.add_argument(
                "--blind",
                metavar="BOOL",
                help="Passed to DESeq2 rlog(blind=); when not given, blind is True",
            )
        add_common_options(sub)
    return parser


import logging
import os
import numpy
from pprint import pformat
import sys
from .common import (
    DetkModule,
    DetkParser,
    add_command_options,
    add_common_options,
    add_subcommands,
    make_cli_count_obj,
    parse_cli,
    set_logging,
    write_output,
)
from .formula import r_design
from .wrapr import require_r, wrapr
from .util import stub
from .report import DetkReport

# cap on the number of per-feature (rank, sd) points emitted for the
# mean-variance trend chart
_MEANSD_BUDGET = 1200


def _transform_report_data(before_df, after_df):
    """Chart-ready before/after comparison for a count transformation.

    Emits per-sample quantile curves of both matrices plus a rank-sampled
    per-feature mean-vs-sd trend, which is the standard way to show that a
    variance-stabilizing transform actually stabilized the variance.
    """
    qs = list(range(0, 101, 5))
    dists = []
    for stage, df in (("before", before_df), ("after", after_df)):
        vals = numpy.percentile(df.values, qs, axis=0)
        for si, sample in enumerate(df.columns):
            dists.extend(
                {"stage": stage, "sample": str(sample), "q": q, "value": float(vals[qi][si])}
                for qi, q in enumerate(qs)
            )

    mean_sd = []
    for stage, df in (("before", before_df), ("after", after_df)):
        means = df.mean(axis=1)
        sds = df.std(axis=1)
        order = numpy.argsort(means.values)
        n = len(order)
        if n == 0:
            continue
        keep = numpy.unique(numpy.linspace(0, n - 1, min(n, _MEANSD_BUDGET)).astype(int))
        mean_sd.extend(
            {
                "stage": stage,
                "rank_pct": float(100.0 * i / max(n - 1, 1)),
                "sd": float(sds.values[order[i]]),
            }
            for i in keep
        )

    return {"dists": dists, "mean_sd": mean_sd}


# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def plog(count_obj, pseudocount=1, base=10):
    """
    Logarithmic transform of a counts matrix with fixed pseudocount, i.e. $\\log(x+c)$

    Parameters
    ----------
    count_obj : CountMatrix object
        count matrix object

    Returns
    -------
    pandas.DataFrame
        log transformed counts dataframe with the same dimensionality as input
        counts

    """
    obj = PlogCounts(count_obj, pseudocount, base)
    return obj.output


class PlogCounts(DetkModule):
    def __init__(self, count_obj, pseudocount=1, base=10):
        self["params"] = {"pseudocount": pseudocount, "base": base}
        logger.debug("plog params: %s", pformat(self["params"]))
        self.count_obj = count_obj
        self.plog_counts = numpy.log(count_obj.counts + pseudocount) / numpy.log(base)
        logger.info("done plog transform")

    @property
    def output(self):
        return self.plog_counts

    @property
    def properties(self):
        return {
            "num_length": len(self.plog_counts),
            "transform": _transform_report_data(self.count_obj.counts, self.plog_counts),
        }


def vst(count_obj):
    """
    Variance Stabilizing Transformation implemented in the DESeq2 bioconductor
    package.

    Parameters
    ----------
    count_obj : CountMatrix object
        count matrix object

    Returns
    -------
    pandas.DataFrame
        VST transformed counts dataframe with the same dimensionality as input
        counts
    """
    obj = VstCounts(count_obj)
    return obj.output


class VstCounts(DetkModule):
    @require_r("DESeq2", "SummarizedExperiment")
    def __init__(self, count_obj):
        self.count_obj = count_obj
        self["params"] = {"blind": True}
        script = """\
        library(DESeq2)
        library(SummarizedExperiment)

        # the IDs as text, as written (007 stays 007; see read.id.csv in wrapr)
        cnts <- as.matrix(read.id.csv(counts.fn,row.names=TRUE))
        colData <- data.frame(name=seq(ncol(cnts)),check.names=FALSE)
        dds <- DESeqDataSetFromMatrix(countData = cnts,
            colData = colData,
            design = ~ 1)
        dds <- varianceStabilizingTransformation(dds)
        write.csv(assay(dds),out.fn)
        """
        logger.debug("VST R script:\n%s", pformat(script))

        with wrapr(script, counts=count_obj.counts, raise_on_error=True) as r:
            vsd_values = r.output
            self.vsd_values = vsd_values

        logger.info("done VST transform")

    @property
    def output(self):
        return self.vsd_values

    @property
    def properties(self):
        return {
            "num_length": len(self.vsd_values),
            "transform": _transform_report_data(self.count_obj.counts, self.vsd_values),
        }


def rlog(count_obj, blind=True):
    """
    Regularized log (rlog) transformation implemented in the DESeq2 bioconductor
    package.

    Parameters
    ----------
    count_obj : CountMatrix object
        count matrix object
    blind : bool
        the `blind` parameter as passed to the `rlog` function in DESeq2. if
        False, `count_obj` is expected to have `column_data` and a valid
        design as required by the R function

    Returns
    -------
    pandas.DataFrame
        rlog transformed counts dataframe with the same dimensionality as input
        counts
    """
    obj = RlogCounts(count_obj, blind)
    return obj.output


class RlogCounts(DetkModule):
    @require_r("DESeq2", "SummarizedExperiment")
    def __init__(self, count_obj, blind=True):
        self["params"] = {"blind": blind}
        logger.debug("rlog params:\n%s", pformat(self["params"]))

        self.count_obj = count_obj

        script = """\
        library(DESeq2)
        library(SummarizedExperiment)

        # the IDs as text, as written (007 stays 007; see read.id.csv in wrapr)
        cnts <- as.matrix(read.id.csv(counts.fn,row.names=TRUE))

        rnames <- rownames(cnts)

        # DESeq2 whines when input counts aren't integers
        # round the counts matrix
        cnts <- data.frame(apply(cnts,2,function(x) { round(as.numeric(x)) }),
            check.names=FALSE
        )
        rownames(cnts) <- rnames

        # load design matrix
        if(file.info(metadata.fn)$size != 0) {
            colData <- read.id.csv(metadata.fn,row.names=TRUE)
        } else {
            # just to convince DESeq2 that everything is ok when we're doing a
            # blind rlog
            n.fake.class.1 <- floor(ncol(cnts)/2)
            fake.classes <- factor(c(
                rep(0,n.fake.class.1),
                rep(1,ncol(cnts)-n.fake.class.1))
            )
            colData <- data.frame(name=fake.classes)
        }

        blind <- params$blind
        form <- params$r_design

        dds <- DESeqDataSetFromMatrix(countData = cnts,
            colData = colData,
            design = formula(form)
        )

        dds <- rlog(dds,blind=blind)
        write.csv(assay(dds),out.fn)
        """
        logger.debug("VST R script:\n%s", script)
        column_data = None
        if not blind and count_obj.column_data is not None:
            # as detk-de deseq2 does: DESeq2 adds its own intercept and takes
            # the counts from countData, so neither belongs in the design
            # (with both, the model matrix is not full rank)
            count_obj.design_matrix.drop_from_lhs("counts", quiet=True)
            count_obj.design_matrix.drop_from_rhs("Intercept", quiet=True)
            column_data = count_obj.design_matrix.full_matrix

        params = {"design": "~ 1" if blind else count_obj.design, "blind": blind}
        logger.debug("VST R script params:\n%s", pformat(params))

        with wrapr(
            script,
            counts=count_obj.counts,
            metadata=column_data,
            params={**params, "r_design": r_design(params["design"])},
            raise_on_error=True,
        ) as r:
            vsd_values = r.output
            self.vsd_values = vsd_values

        logger.info("done rlog transform")

    @property
    def output(self):
        return self.vsd_values

    @property
    def properties(self):
        return {
            "num_length": len(self.vsd_values),
            "transform": _transform_report_data(self.count_obj.counts, self.vsd_values),
        }


@stub
def ruvseq(count_obj):
    pass


def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    cmd = args.subcommand
    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    count_obj = make_cli_count_obj(args)

    if cmd == "vst":
        out = VstCounts(count_obj)

    elif cmd == "plog":
        try:
            out = PlogCounts(count_obj, pseudocount=float(args.pseudocount), base=float(args.base))
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    elif cmd == "rlog":
        blind = True if args.blind is None else args.blind

        try:
            out = RlogCounts(count_obj, blind=blind)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    write_output(out.output, args)

    if not args.no_report:
        logging.info("writing report to %s", args.report_dir)
        with DetkReport(args.report_dir) as r:
            r.add_module(
                out,
                in_file_path=args.counts_fn,
                out_file_path=args.output,
                column_data_path=None,
                workdir=os.getcwd(),
            )

    logging.info("done")


if __name__ == "__main__":
    main()
