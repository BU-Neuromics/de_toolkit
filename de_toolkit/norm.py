r"""
Normalize the counts in a counts matrix, so that values can be compared
across samples (deseq2, library, cpm) or across samples and features (fpkm,
tpm). The input is a delimited counts file, features in rows and samples in
columns; the output is the normalized matrix in the same shape.
"""

_LENGTHS_NOTE = """
<lengths_fn> is a delimited file with two columns: the first is the name of
a row in the counts file, the second the effective length in bases of that
gene, transcript or other feature. The order of names in the two files does
*not* have to be the same; names are matched as text. The first line of the
lengths file is skipped as a header only when its second field is text that
is not a number or a missing value such as NA.

The command exits with an error if a feature in the counts file is not in
the lengths file, if any of their lengths is not a positive number, or if a
name is listed more than once in the lengths file."""

# each subcommand: the one line the command's help lists it with, its
# description, its positionals beyond <counts_fn> and its examples
SUBCOMMANDS = {
    "deseq2": dict(
        help="Normalize by the DESeq2 median-of-ratios size factors",
        description="""\
Perform counts normalization on the given counts matrix using the method
implemented in the DESeq2 package: each sample is divided by its size factor,
the median ratio of its counts to the geometric mean of each feature across
samples.""",
        examples=[
            (
                "Normalize counts.csv, writing norm_counts.csv",
                "detk-norm deseq2 -o norm_counts.csv counts.csv",
            ),
        ],
    ),
    "library": dict(
        help="Divide each count by its sample's total count",
        description="""\
Perform library size normalization on the columns of the given counts matrix.
Counts in each column are divided by the sum of that column.""",
        examples=[
            ("Library size normalize counts.csv to stdout", "detk-norm library counts.csv"),
        ],
    ),
    "fpkm": dict(
        help="Fragments per kilobase per million (needs feature lengths)",
        description="""\
Perform Fragments Per Kilobase per Million normalization on the given counts
file. Each count is divided by its feature's length in kilobases and by its
sample's total count in millions: count * 1e9 / (length * library size).
"""
        + _LENGTHS_NOTE,
        lengths=True,
        examples=[
            (
                "FPKM of counts.csv with the feature lengths in lengths.csv",
                "detk-norm fpkm -o fpkm.csv counts.csv lengths.csv",
            ),
        ],
    ),
    "cpm": dict(
        help="Counts per million: library size normalization times 1e6",
        description="""\
Perform Counts Per Million normalization on the columns of the given counts
matrix. Counts in each column are divided by the sum of that column and
multiplied by one million, so every column of the output sums to 1e6.""",
        examples=[("Counts per million of counts.csv", "detk-norm cpm -o cpm.csv counts.csv")],
    ),
    "tpm": dict(
        help="Transcripts per million (needs feature lengths)",
        description="""\
Perform Transcripts Per Million normalization on the given counts file. Each
count is divided by its feature's length in kilobases, then each column is
scaled so it sums to one million.
"""
        + _LENGTHS_NOTE,
        lengths=True,
        examples=[
            (
                "TPM of counts.csv with the feature lengths in lengths.csv",
                "detk-norm tpm -o tpm.csv counts.csv lengths.csv",
            ),
        ],
    ),
}


def build_parser():
    "The detk-norm command line parser"
    parser = DetkParser(prog="detk-norm", description=__doc__.strip())
    add_command_options(parser)
    subs = add_subcommands(parser)
    for name, spec in SUBCOMMANDS.items():
        sub = subs.add_parser(
            name, help=spec["help"], description=spec["description"], examples=spec["examples"]
        )
        sub.add_argument(
            "counts_fn",
            metavar="<counts_fn>",
            help="Counts file: features in rows, samples in columns, delimited",
        )
        if spec.get("lengths"):
            sub.add_argument(
                "lengths_fn",
                metavar="<lengths_fn>",
                help="Feature lengths file: feature name and length in bases",
            )
        sub.add_argument(
            "-o",
            "--output",
            metavar="FILE",
            default="stdout",
            help="Destination of normalized output in CSV format",
        )
        if name == "deseq2":
            sub.add_argument(
                "--size-factors",
                metavar="FILE",
                help="Write out the size factors found by the DESeq2 method to a two "
                "column tab separated file: a header line 'sample', 'size_factor', "
                "then one line per sample of its name and size factor",
            )
        add_common_options(sub)
    return parser


import logging
import numpy as np
import pandas
from pprint import pformat
import sys
import os
from .common import (
    cli_main,
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
from .report import DetkReport
from .util import stub
from .formula import r_design
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
    # the design's names quoted for R (formula.r_design)
    dds <- DESeqDataSetFromMatrix(countData = cnts,
        colData = colData,
        design = formula(params$r_design))
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
        params={"design": count_obj.design, "r_design": r_design(count_obj.design)},
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

    def write_size_factors(self, path):
        """
        Write the size factors to *path*: tab separated, a ``sample`` and
        ``size_factor`` header line (DETK-0082), then one row per sample of
        its name and size factor, in the counts file's column order, with the
        sample names as they were written
        """
        logger.info("writing size factors to %s", path)
        with open(path, "w", newline="") as f:
            f.write("sample\tsize_factor\n")
            for sample, factor in self.size_factors.items():
                f.write(f"{sample}\t{factor!r}\n")


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
    Calculate Fragments Per Kilobase per Million reads: divide each count by
    its feature length in kilobases and by its column's total count (the
    library size) in millions, i.e. count * 1e9 / (length * library size)

    *lengths* should be a pandas.Series of lengths in bases that has an index
    value for every row name in the counts matrix. If no length is found for a
    row in the counts matrix, or a length is not positive, an exception is
    raised.
    """
    obj = FPKMCounts(count_df, lengths)
    return obj.output


class FPKMCounts(DetkModule):
    def __init__(self, count_df, lengths):
        logger.info("running FPKM normalization")
        logger.info("number of feature lengths provided: %d", lengths.size)

        self["params"] = {}
        self.count_df = count_df
        lens = _lengths_for(count_df, lengths)
        self.lengths = lens

        sizes = count_df.sum(axis=0)
        logger.info("min/max library size: %d/%d", sizes.min(), sizes.max())
        if (np.asarray(sizes) == 0).any():
            logger.warning("some samples have zero total counts, their FPKM values are NaN")
        # count / (length in kb) / (library size in millions)
        #   = count * 1e9 / (length * library size)
        self.res = count_df.div(lens / 1e3, axis=0) / (sizes / 1e6)

        logger.info("FPKM normalization done")

    @property
    def output(self):
        return self.res

    @property
    def properties(self):
        # summarize the lengths actually used, rather than embedding the full
        # lengths vector (previously a raw pandas Series, which broke JSON
        # serialization of this module's report document)
        return {"num_kept": len(self.res), "length_quantiles": _length_quantiles(self.lengths)}


def _length_quantiles(lengths):
    "Summarize a feature-length vector as 5-percentile steps for the report."
    qs = list(range(0, 101, 5))
    lens = pandas.to_numeric(lengths, errors="coerce").dropna()
    return [{"q": q, "length": float(v)} for q, v in zip(qs, np.percentile(lens, qs))]


def _align_lengths(count_df, lengths):
    """
    Return *lengths* (a pandas.Series indexed by feature name) aligned to the
    rows of *count_df*, indexed like *count_df*. Feature names are matched as
    strings. The counts and lengths file readers already give text IDs, so
    ``007`` matches only ``007``; the conversion here is for a *count_df* or
    *lengths* built in Python with integer IDs (e.g. Entrez gene IDs), which
    then match the same IDs written as text. Raises
    NormalizationException when a feature name appears more than once in
    *lengths* or a feature of *count_df* has no length.
    """
    lengths = pandas.Series(lengths.values, index=lengths.index.astype(str))
    dups = lengths.index[lengths.index.duplicated()].unique()
    if len(dups) != 0:
        raise NormalizationException(
            f"{len(dups)} feature names appear more than once in the lengths "
            + "parameters, here are a couple: \n"
            + "\n".join(list(dups)[:5])
        )
    keys = count_df.index.astype(str)
    missing = ~keys.isin(lengths.index)
    if missing.any():
        missing_indices = count_df.index[missing]
        raise NormalizationException(
            f"{len(missing_indices)} indices in the counts matrix were "
            + "not found in the lengths parameters, here are a couple: \n"
            + "\n".join(str(_) for _ in list(missing_indices)[:5])
        )
    return pandas.Series(lengths[keys].values, index=count_df.index)


def _lengths_for(count_df, lengths):
    """
    Like _align_lengths, and also raise NormalizationException when a
    feature's length is not a positive number.
    """
    lens = pandas.to_numeric(_align_lengths(count_df, lengths), errors="coerce")
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
    the delimiter is sniffed) into a pandas.Series indexed by feature name
    (as a string). The first line is taken as a header, and skipped, only
    when its second field is neither a number nor a missing-value token
    (empty, NA, NaN, N/A, NULL, None); otherwise it is a feature row, so a
    bad first length is reported like any other. A feature name that
    appears more than once raises NormalizationException.
    """
    df = pandas.read_csv(
        lengths_fn, sep=None, engine="python", header=None, dtype=str, keep_default_na=False
    )
    if df.shape[1] < 2:
        raise NormalizationException(
            f"lengths file {lengths_fn} must have two columns, found {df.shape[1]}"
        )
    if len(df) and _looks_like_header(df.iloc[0, 1]):
        df = df.iloc[1:]
    ids = df.iloc[:, 0].str.strip()
    dups = ids[ids.duplicated()].unique()
    if len(dups) != 0:
        raise NormalizationException(
            f"lengths file {lengths_fn} lists {len(dups)} feature names more than "
            + "once, here are a couple: \n"
            + "\n".join(list(dups)[:5])
        )
    return pandas.Series(
        pandas.to_numeric(df.iloc[:, 1].str.strip(), errors="coerce").values, index=ids.values
    )


_MISSING_TOKENS = {"", "NA", "NAN", "N/A", "NULL", "NONE"}


def _looks_like_header(field):
    "A lengths-file first line is a header when its length field is text."
    field = str(field).strip()
    if field.upper() in _MISSING_TOKENS:
        return False
    return pandas.isna(pandas.to_numeric(field, errors="coerce"))


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
        # summarized as in FPKMCounts: the lengths actually used, as quantiles
        return {
            "num_features": self.normalized.shape[0],
            "length_quantiles": _length_quantiles(self.lengths),
        }


@stub
def custom_norm(count_mat, factors):
    pass


@cli_main
def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    cmd = args.subcommand
    # every normalization needs raw counts: a malformed counts file exits 1
    # before anything is written or logged (DETK-0601, DETK-0830)
    count_obj = make_cli_count_obj(args, raw=True)
    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    if cmd == "deseq2":
        out = DESeq2Norm(count_obj)

    elif cmd == "library":
        out = LibrarySize(count_obj.counts)

    elif cmd == "fpkm":
        # the lengths_fn is assumed to be a file with two columns
        # ID<delim>int
        # providing the lengths that should be used for each ID in the counts
        # file
        lengths = read_lengths(args.lengths_fn)

        out = FPKMCounts(count_obj.counts, lengths)

    elif cmd == "cpm":
        out = CPMCounts(count_obj.counts)

    elif cmd == "tpm":
        lengths = read_lengths(args.lengths_fn)
        out = TPMCounts(count_obj.counts, lengths)

    # the size factors first, so an unwritable path stops the command before
    # any normalized counts are written
    if cmd == "deseq2" and args.size_factors:
        out.write_size_factors(args.size_factors)

    write_output(out.output, args)

    if not args.no_report:
        logging.info("writing report to %s", args.report_dir)
        with DetkReport(args.report_dir) as r:
            # fpkm and tpm read a lengths file, and deseq2 --size-factors
            # writes a file beside the counts: each is in the provenance (#209)
            lengths = getattr(args, "lengths_fn", None)
            size_factors = getattr(args, "size_factors", None)
            r.add_module(
                out,
                in_file_path=args.counts_fn,
                out_file_path=args.output,
                workdir=os.getcwd(),
                in_file_paths=[args.counts_fn, lengths] if lengths else None,
                out_file_paths=[args.output, size_factors] if size_factors else None,
            )

    else:
        logging.info("not generating report due to --no-report")

    logging.info("done")


if __name__ == "__main__":
    main()
