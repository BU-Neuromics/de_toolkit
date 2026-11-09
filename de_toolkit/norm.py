r"""
Usage:
    detk-norm deseq2 [options] <counts_fn>
    detk-norm library [options] <counts_fn>
    detk-norm fpkm [options] <counts_fn> <lengths_fn>
    detk-norm cpm [options] <counts_fn>
    detk-norm tpm [options] <counts_fn> <lengths_fn>
Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
"""

todo = r"""
    detk-norm custom <counts_fn>
"""
cmd_opts = {
    "deseq2": r"""
Perform counts normalization on the given counts matrix using the method
implemented in the DESeq2 package.

Usage:
    detk-norm deseq2 [options] <counts_fn>

Options:
    -h --help                    Print out this help
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
    --size-factors=FILE          Write out the size factors found by the DESeq2
                                 method to two column tab separated file where
                                 the first column is sample name and the second
                                 column is the size factor
""",
    "library": r"""
Perform library size normalization on the columns of the given counts matrix.
Counts in each column are divided by the sum of each column.

Usage:
    detk-norm library [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
""",
    "fpkm": r"""
Perform Fragments Per Kilobase per Million normalization on the given counts
file. <lengths_fn> should be a delimited file with two columns, the first
being the name of one of the rows in the counts file and the second is the
effective length of the gene/sequence/etc to use in the normalization.

*Note:* Program will throw an error and exit if there are genes/sequences
in the counts file that are not found in the lengths file.

The order of names in the counts and lengths files do *not* have to be the
same.

Usage:
    detk-norm fpkm [options] <counts_fn> <lengths_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]

""",
    "cpm": r"""
Perform Counts Per Million normalization on the columns of the given counts
matrix. Counts in each column are divided by the sum of that column and
multiplied by one million, so every column of the output sums to 1e6.

Usage:
    detk-norm cpm [options] <counts_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
""",
    "tpm": r"""
Perform Transcripts Per Million normalization on the given counts file. Each
count is divided by its feature's length in kilobases, then each column is
scaled so it sums to one million. <lengths_fn> is the same two column
delimited file the fpkm subcommand takes: the first column is the name of a
row in the counts file, the second its effective length in bases.

*Note:* Program will throw an error and exit if there are genes/sequences
in the counts file that are not found in the lengths file, or if any of
their lengths is not a positive number.

The order of names in the counts and lengths files do *not* have to be the
same.

Usage:
    detk-norm tpm [options] <counts_fn> <lengths_fn>

Options:
    -o FILE --output=FILE        Destination of normalized output in CSV format [default: stdout]
""",
}
from docopt import docopt
import logging
import numpy as np
import pandas
from pprint import pformat
import sys
import os
from .common import DetkModule, _cli_doc, set_logging, make_cli_count_obj, write_output
from .report import DetkReport
from .util import stub
from .wrapr import require_r, wrapr

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class NormalizationException(Exception):
    pass


# DESeq2 v1.14.1 uses this R code for normalization
# function (counts, locfunc = stats::median, geoMeans, controlGenes)
# {
#        if (missing(geoMeans)) {
#                loggeomeans <- rowMeans(log(counts))
#        }
#        else {
#                if (length(geoMeans) != nrow(counts)) {
#                        stop("geoMeans should be as long as the number of rows of counts")
#                }
#                loggeomeans <- log(geoMeans)
#        }
#        if (all(is.infinite(loggeomeans))) {
#                stop("every gene contains at least one zero, cannot compute log geometric means")
#        }
#        sf <- if (missing(controlGenes)) {
#                apply(counts, 2, function(cnts) {
#                        exp(locfunc((log(cnts) - loggeomeans)[is.finite(loggeomeans) &
#                                cnts > 0]))
#                })
#        }
#        else {
#                if (!(is.numeric(controlGenes) | is.logical(controlGenes))) {
#                        stop("controlGenes should be either a numeric or logical vector")
#                }
#                loggeomeansSub <- loggeomeans[controlGenes]
#                apply(counts[controlGenes, , drop = FALSE], 2, function(cnts) {
#                        exp(locfunc((log(cnts) - loggeomeansSub)[is.finite(loggeomeansSub) &
#                                cnts > 0]))
#                })
#        }
#        sf
# }


def estimateSizeFactors(cnts):

    logger.debug("computing geometric means")
    loggeomeans = np.log(cnts).mean(axis=1)

    logger.info("features usable in geometric mean calculation: %d", np.isfinite(loggeomeans).sum())

    if all(~np.isfinite(loggeomeans)):
        raise NormalizationException(
            "every gene contains at least one zero, cannot compute log geometric means"
        )

    divFact = (np.log(cnts).T - loggeomeans).T
    sizeFactors = np.exp(np.apply_along_axis(lambda c: np.median(c[np.isfinite(c)]), 0, divFact))
    logger.debug("size factors:\n%s", pformat(sizeFactors))

    return sizeFactors


@require_r("DESeq2")
def estimateSizeFactors_wrapr(cnts):

    script = """\
    library(DESeq2)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1,check.names=FALSE))
    colData <- data.frame(name=seq(ncol(cnts)),check.names=FALSE)
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = ~ 1)
    dds <- estimateSizeFactors(dds)
    write.csv(sizeFactors(dds),out.fn)
    """

    with wrapr(script, counts=pandas.DataFrame(cnts), raise_on_error=False) as r:
        deseq2_size_factors = r.output["x"].values

    return list(deseq2_size_factors)


def deseq2(count_obj):
    obj = DESeq2Norm(count_obj)
    return obj.output


@require_r("DESeq2")
def deseq2_wrapr(count_obj):

    script = """\
    library(DESeq2)

    cnts <- as.matrix(read.csv(counts.fn,row.names=1,check.names=FALSE))
    colData <- read.csv(metadata.fn,row.names=1,check.names=FALSE)
    str(params$design)
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = formula(params$design))
    dds <- estimateSizeFactors(dds)
    write.csv(counts(dds,normalized=TRUE),out.fn,row.names=TRUE)
    """

    # we need to get rid of the counts from the left hand side and the Intercept
    # from the right, otherwise the model matrix is not full rank and DESeq2
    # whines, whines!
    count_obj.design_matrix.drop_from_lhs("counts")
    count_obj.design_matrix.drop_from_rhs("Intercept")

    with wrapr(
        script,
        counts=count_obj.counts,
        metadata=count_obj.design_matrix.full_matrix,
        params={"design": count_obj.design},
        raise_on_error=True,
    ) as r:
        norm_counts = r.output.values

    return norm_counts


class DESeq2Norm(DetkModule):
    def __init__(self, count_obj):
        logger.info("running DESeq2 normalization")
        self["params"] = {}
        count_mat = count_obj.counts.values
        sizeFactors = estimateSizeFactors(count_mat)
        self.size_factors = dict(zip(count_obj.counts.columns, sizeFactors.tolist()))
        norm_cnts = count_mat / sizeFactors
        normalized = pandas.DataFrame(
            norm_cnts, index=count_obj.counts.index, columns=count_obj.counts.columns
        )
        self.normalized = normalized
        logger.info("DESeq2 normalization done")

    @property
    def output(self):
        return self.normalized

    @property
    def properties(self):
        return {"num_kept": len(self.normalized), "size_factors": self.size_factors}


def library_size(count_df):
    """
    Divide each count by column sum
    """
    obj = LibrarySize(count_df)
    return obj.output


class LibrarySize(DetkModule):
    def __init__(self, count_df):
        logger.info("running library size normalization")
        sizes = count_df.sum(axis=0)
        logger.info("min/max library size: %d/%d", sizes.min(), sizes.max())
        self["params"] = {}
        cols = getattr(count_df, "columns", None)
        names = [str(c) for c in cols] if cols is not None else [str(i) for i in range(len(sizes))]
        self.library_sizes = dict(zip(names, np.asarray(sizes).tolist()))
        self.count_df = count_df
        self.normalized = count_df / sizes

        logger.info("library size normalization done")

    @property
    def output(self):
        return self.normalized

    @property
    def properties(self):
        return {"num_features": self.normalized.shape[0], "library_sizes": self.library_sizes}


def fpkm(count_df, lengths):
    """
    Calculate Fragments Per Kilobase per Million reads

    *lengths* should be a pandas.Series object that has an index value for
    every row name in the counts matrix. If no length is found for a row in the
    counts matrix, an exception is raised.
    """
    obj = FPKMCounts(count_df, lengths)
    return obj.output


class FPKMCounts(DetkModule):
    def __init__(self, count_df, lengths):
        logger.info("running FPKM normalization")
        logger.info("number of feature lengths provided: %d", lengths.size)

        self["params"] = {}
        self.count_df = count_df
        self.lengths = lengths

        missing_indices = count_df.index.difference(lengths.index)
        if len(missing_indices) != 0:
            raise NormalizationException(
                f"{len(missing_indices)} indices in the counts matrix were "
                + "not found in the lengths parameters, here are a couple: \n"
                + "\n".join(_ for _ in list(missing_indices)[:5])
            )
        lens = lengths[count_df.index]
        res = count_df.div(1e6 * lens, axis=0)
        self.res = res

        logger.info("running FPKM normalization")

    @property
    def output(self):
        return self.res

    @property
    def properties(self):
        # summarize the feature-length distribution rather than embedding the
        # full lengths vector (previously a raw pandas Series, which broke
        # JSON serialization of this module's report document)
        qs = list(range(0, 101, 5))
        lens = pandas.to_numeric(self.lengths, errors="coerce").dropna()
        quantiles = [{"q": q, "length": float(v)} for q, v in zip(qs, np.percentile(lens, qs))]
        return {"num_kept": len(self.res), "length_quantiles": quantiles}


def _length_quantiles(lengths):
    "Summarize a feature-length vector as 5-percentile steps for the report."
    qs = list(range(0, 101, 5))
    lens = pandas.to_numeric(lengths, errors="coerce").dropna()
    return [{"q": q, "length": float(v)} for q, v in zip(qs, np.percentile(lens, qs))]


def _lengths_for(count_df, lengths):
    """
    Return *lengths* (a pandas.Series indexed by feature name) aligned to the
    rows of *count_df*, raising NormalizationException when a feature has no
    length or a length that is not a positive number.
    """
    missing_indices = count_df.index.difference(lengths.index)
    if len(missing_indices) != 0:
        raise NormalizationException(
            f"{len(missing_indices)} indices in the counts matrix were "
            + "not found in the lengths parameters, here are a couple: \n"
            + "\n".join(str(_) for _ in list(missing_indices)[:5])
        )
    lens = pandas.to_numeric(lengths[count_df.index], errors="coerce")
    bad = lens.index[~(lens > 0)]
    if len(bad) != 0:
        raise NormalizationException(
            f"{len(bad)} features have a length that is not a positive number, "
            + "here are a couple: \n"
            + "\n".join(str(_) for _ in list(bad)[:5])
        )
    return lens


def read_lengths(lengths_fn):
    """
    Read a two column delimited lengths file (feature name, length in bases;
    the delimiter is sniffed) into a pandas.Series indexed by feature name. A
    header line is allowed and detected by its second field not being a
    number.
    """
    df = pandas.read_csv(lengths_fn, sep=None, engine="python", header=None, dtype=str)
    if df.shape[1] < 2:
        raise NormalizationException(
            f"lengths file {lengths_fn} must have two columns, found {df.shape[1]}"
        )
    if len(df) and pandas.isna(pandas.to_numeric(df.iloc[0, 1], errors="coerce")):
        df = df.iloc[1:]
    return pandas.Series(
        pandas.to_numeric(df.iloc[:, 1], errors="coerce").values, index=df.iloc[:, 0].values
    )


def cpm(count_df):
    """
    Counts Per Million: divide each count by its column sum and multiply by
    1e6
    """
    obj = CPMCounts(count_df)
    return obj.output


class CPMCounts(DetkModule):
    def __init__(self, count_df):
        logger.info("running CPM normalization")
        sizes = count_df.sum(axis=0)
        logger.info("min/max library size: %d/%d", sizes.min(), sizes.max())
        if (np.asarray(sizes) == 0).any():
            logger.warning("some samples have zero total counts, their CPM values are NaN")
        self["params"] = {}
        cols = getattr(count_df, "columns", None)
        names = [str(c) for c in cols] if cols is not None else [str(i) for i in range(len(sizes))]
        self.library_sizes = dict(zip(names, np.asarray(sizes).tolist()))
        self.normalized = count_df / sizes * 1e6
        logger.info("CPM normalization done")

    @property
    def output(self):
        return self.normalized

    @property
    def properties(self):
        return {"num_features": self.normalized.shape[0], "library_sizes": self.library_sizes}


def tpm(count_df, lengths):
    """
    Transcripts Per Million: divide each count by its feature length in
    kilobases, then scale each column to sum to 1e6

    *lengths* should be a pandas.Series of lengths in bases that has an index
    value for every row name in the counts matrix. If no length is found for a
    row in the counts matrix, or a length is not positive, an exception is
    raised.
    """
    obj = TPMCounts(count_df, lengths)
    return obj.output


class TPMCounts(DetkModule):
    def __init__(self, count_df, lengths):
        logger.info("running TPM normalization")
        logger.info("number of feature lengths provided: %d", lengths.size)

        self["params"] = {}
        lens = _lengths_for(count_df, lengths)
        self.lengths = lens

        rate = count_df.div(lens / 1e3, axis=0)
        rate_sums = rate.sum(axis=0)
        if (np.asarray(rate_sums) == 0).any():
            logger.warning("some samples have zero total counts, their TPM values are NaN")
        self.normalized = rate / rate_sums * 1e6

        logger.info("TPM normalization done")

    @property
    def output(self):
        return self.normalized

    @property
    def properties(self):
        # summarized like FPKMCounts: the lengths actually used, as quantiles
        return {
            "num_features": self.normalized.shape[0],
            "length_quantiles": _length_quantiles(self.lengths),
        }


@stub
def custom_norm(count_mat, factors):
    pass


def main(argv=sys.argv):

    if "--version" in argv:
        from .version import __version__

        print(__version__)
        return

    # add the common opts to the docopt strings
    cmd_opts_aug = {}
    for k, v in cmd_opts.items():
        cmd_opts_aug[k] = _cli_doc(v)

    if len(argv) < 2 or (len(argv) > 1 and argv[1] not in cmd_opts):
        docopt(_cli_doc(__doc__), argv)
    argv = argv[1:]
    cmd = argv[0]

    args = docopt(cmd_opts_aug[cmd], argv)
    count_obj = make_cli_count_obj(args)
    set_logging(args)
    logger.info("cmd: %s", " ".join(argv))

    if cmd == "deseq2":
        try:
            out = DESeq2Norm(count_obj)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    elif cmd == "library":
        try:
            out = LibrarySize(count_obj.counts)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    elif cmd == "fpkm":
        # the lengths_fn is assumed to be a file with two columns
        # ID<delim>int
        # providing the lengths that should be used for each ID in the counts
        # file
        try:
            lengths = read_lengths(args["<lengths_fn>"])
        except Exception as e:
            logger.error(e)
            sys.exit(1)

        try:
            out = FPKMCounts(count_obj.counts, lengths)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    elif cmd == "cpm":
        try:
            out = CPMCounts(count_obj.counts)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    elif cmd == "tpm":
        try:
            lengths = read_lengths(args["<lengths_fn>"])
            out = TPMCounts(count_obj.counts, lengths)
        except Exception as e:
            logger.error(e)
            sys.exit(1)

    write_output(out.output, args)

    if not args["--no-report"]:
        logging.info("writing report to %s", args["--report-dir"])
        with DetkReport(args["--report-dir"]) as r:
            r.add_module(
                out,
                in_file_path=args["<counts_fn>"],
                out_file_path=args["--output"],
                column_data_path=args.get("--column-data"),
                workdir=os.getcwd(),
            )

    else:
        logging.info("not generating report due to --no-report")

    logging.info("done")


if __name__ == "__main__":
    main()
