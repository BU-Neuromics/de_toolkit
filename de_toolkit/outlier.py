r"""
Find and treat outlier counts in a counts matrix: flag features whose counts
are dominated by a few samples (entropy), or shrink the counts of a sample
toward the others (shrink). The input is a delimited counts file, features
in rows and samples in columns.
"""

# each subcommand: the one line the command's help lists it with, its
# description and its examples
SUBCOMMANDS = {
    "entropy": dict(
        help="Flag features whose sample entropy is below a percentile",
        description="""\
Calculate the sample entropy of each feature and flag the features whose
entropy is below the given percentile: features overly influenced by the
counts of one or a few samples. Writes the entropy and the flag of each
feature to the -o file, and optionally plots the entropy distribution with
the threshold.""",
        examples=[
            (
                "Flag the features below the 5th entropy percentile",
                "detk-outlier entropy -p 0.05 -o entropy_flags.csv counts.csv",
            ),
        ],
    ),
    "shrink": dict(
        help="Shrink the counts of dominant samples toward the others",
        description="""\
Shrink the counts of features where one sample holds more than a given
fraction of the feature's counts toward the other samples, iteratively.""",
        examples=[
            ("Shrink outlier counts in counts.csv", "detk-outlier shrink -o shrunk.csv counts.csv"),
        ],
    ),
}


def build_parser():
    "The detk-outlier command line parser"
    parser = DetkParser(prog="detk-outlier", description=__doc__.strip())
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
        if name == "entropy":
            sub.add_argument(
                "-p",
                "--percentile",
                metavar="N",
                help="The entropy percentile below which a feature is flagged, between 0 and 1",
            )
            sub.add_argument(
                "-o",
                "--output",
                metavar="FILE",
                help="Destination of the entropy and flag of each feature in CSV format",
            )
            sub.add_argument(
                "--plot-output",
                metavar="FILE",
                help="Destination of a PNG plot of the entropy distribution and threshold",
            )
        else:
            sub.add_argument(
                "-o",
                "--output",
                metavar="FILE",
                default="stdout",
                help="Destination of the shrunk counts in CSV format",
            )
            sub.add_argument(
                "-f",
                "--shrink-factor",
                metavar="N",
                default="0.25",
                help="Shrinkage factor, between 0 and 1",
            )
            sub.add_argument(
                "-p",
                "--p-max",
                metavar="N",
                help="Largest fraction of a feature's counts one sample may hold "
                "(when not given, sqrt(1 / number of samples))",
            )
            sub.add_argument(
                "-i", "--iters", metavar="N", default="1000", help="Number of iterations"
            )
        add_common_options(sub)
    return parser


import os
import logging
import numpy as np
import pandas as pd
from pprint import pformat
import scipy.stats as sc
import sys

from .common import (
    UsageError,
    cli_main,
    option_value,
    CountMatrixFile,
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

# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def pmf_transform(count_obj, shrink_factor=0.25, p_max=None, iters=1000):
    obj = PMFTransform(count_obj, shrink_factor, p_max, iters)
    return obj.output


class PMFTransform(DetkModule):
    def __init__(self, count_obj, shrink_factor=0.25, p_max=None, iters=1000):
        self["params"] = {"shrink_factor": shrink_factor, "p_max": p_max, "iters": iters}
        count_obj = count_obj.copy()
        p_max = p_max or np.sqrt(1.0 / len(count_obj))

        for _ in range(iters):
            p_count = count_obj / count_obj.sum()

            if count_obj.sum() == 0:
                print("all samples set to zero, returning")
                break

            p_count_outliers = p_count > p_max

            if not p_count_outliers.any():
                break  # done

            max_non_outliers = max(count_obj[~p_count_outliers])

            count_obj[p_count_outliers] = (
                max_non_outliers + (count_obj[p_count_outliers] - max_non_outliers) * shrink_factor
            )
        #        if i == iters :
        #            print('PMF transform did not converge')
        #            print(p_x)
        #            print(p_x_outliers)

        self.count_obj = count_obj

    @property
    def output(self):
        return self.count_obj

    @property
    def properties(self):
        return {"num_kept": len(self.count_obj)}


def shrink(count_obj, shrink_factor=0.25, p_max=None, iters=1000):
    """
    Outlier count shrinkage routine as described in Labadorf et al, PLOSONE (2015)

    This algorithm identifies feature where a small number of samples contains a
    disproportionately large number of the overall counts for that feature
    across samples. For each feature the algorithm is as follows:

    1. Divide each sample count by the sum of counts (i.e. sample count
       proportions)

    2. Identify samples that have >*p_max* sample count proportion

        a. If no samples are identified, return the most recent set of adjusted
           counts

        b. Else, shrink the identified samples toward the largest sample *s* for
           which P(x)<*p_max* by multiplying the difference between the
           outlier sample and *s* by the shrinkage factor and replacing
           *o* with *s* the shrunken count value

    3. Go to 1, repeat until no samples exceed *p_max* count proportion

    This strategy assumes that samples with disproportionate count contribution
    are outliers and that the order of samples is correct and the magnitude is
    sometimes not. The order of the samples is thus always maintained, and the
    shrinking does not introduce new false positives beyond what would already
    be in the dataset. The maximum proportion of reads allowed in one sample,
    p, and the shrinkage factor were both set to 0.2.

    Parameters
    ----------
    count_obj: de_toolkit.CountMatrix object
        counts object
    shrink_factor: float
        number between 0 and 1 that determines how much the residual counts of
        outlier samples is shrunk in each iteration
    p_max: float
        number between 0 and 1 that indicates the maximum proportion of counts
        a sample may have before being considered an outlier, default is
        ``sqrt(1/num_samples)``
    """
    obj = ShrinkCounts(count_obj, shrink_factor, p_max, iters)
    return obj.output


class ShrinkCounts(DetkModule):
    def __init__(self, count_obj, shrink_factor=0.25, p_max=None, iters=1000):
        self["params"] = {"shrink_factor": shrink_factor, "p_max": p_max, "iters": iters}
        logger.info("PMF shrink params: %s", pformat(self["params"]))
        shrunk_counts = count_obj.counts.apply(
            pmf_transform, shrink_factor=shrink_factor, p_max=p_max, iters=iters
        )
        shrunk_counts = pd.DataFrame(
            shrunk_counts, index=count_obj.counts.index, columns=count_obj.counts.columns
        )

        logger.info(
            "counts removed by shrinking: %.2f",
            shrunk_counts.sum().sum() - count_obj.counts.sum().sum(),
        )
        self.shrunk_counts = shrunk_counts

        logger.info("PMF shrink done")

    @property
    def output(self):
        return self.shrunk_counts

    @property
    def properties(self):
        return {"num_kept": len(self.shrunk_counts)}


def entropy(counts_obj, threshold):
    """
    Calculate sample entropy for each gene and flag genes that exceed the lower
    threshold'ile

    Sample entropy is a metric that can be used to identify outlier samples by
    locating rows which are overly influenced by a single count value. This
    metric is calculated for each gene/feature *g* as follows::

        p_i = c_i/sumj(c_j)
        sum(p_i) = 1
        H_g = -sum_i(p_i*log2(p_i))

    Here, c_i is the number of counts in sample i, p_i is the fraction of reads
    contributed by sample i to the overall counts of the row, and H_g is the
    Shannon entropy of the row when using log2. The maximum value possible for
    H is 2 when using Shannon entropy. Genes/features with very low entropy are
    those where a small number of samples makes up most of the counts across
    all samples.

    Parameters
    ----------
    counts_obj: de_toolkit.CountMatrix
        count matrix object
    threshold: float
        the percentile below which to flag genes, as a fraction strictly
        between 0 and 1 (0.05 is the 5th percentile)

    Returns
    -------
    pandas.DataFrame
        data frame with one row for each row in the input counts matrix and two
        columns:

        - *entropy*: the calculated entropy value for that row
        - *entropy_p0_XX*: a True/False column for genes flagged as having an
          entropy value less than the *threshold* percentile; *XX* is the
          digits of the threshold after the decimal point, at least two
          (0.05 gives *entropy_p0_05*, 0.1 *entropy_p0_10*)

        A feature with no counts in any sample has no entropy: its *entropy*
        is missing (NaN) and it is not flagged, and the percentile is taken
        over the other features.
    """
    obj = EntropyCounts(counts_obj, threshold)
    return obj.output


def flag_column(threshold):
    """
    The name of the flag column for the fraction *threshold*: ``entropy_p0_``
    and the threshold's decimal digits, at least two (0.05 gives
    ``entropy_p0_05``, 0.1 ``entropy_p0_10``, 0.125 ``entropy_p0_125``, 1e-05
    ``entropy_p0_00001``).
    """
    digits = np.format_float_positional(float(threshold), trim="-").partition(".")[2]
    return f"entropy_p0_{digits.ljust(2, '0')}"


class EntropyCounts(DetkModule):
    def __init__(self, counts_obj, threshold):
        self["params"] = {"threshold": threshold}
        self.counts_obj = counts_obj
        logger.info("entropy thresholding")

        # -p is a fraction of the features, between 0 and 1 (DETK-0200);
        # numpy's percentile takes a percent
        if not 0 < threshold < 1:
            raise ValueError(
                f"the entropy percentile must be a fraction between 0 and 1, got {threshold}"
            )
        flag_col = flag_column(threshold)

        counts = counts_obj.counts
        # entropy is undefined for a feature with no counts: it is left out of
        # the percentile, written missing and not flagged
        nonzero = (counts != 0).any(axis=1)
        num_zero = int((~nonzero).sum())
        if num_zero:
            logger.warning(
                "%d feature(s) have no counts in any sample: their entropy is written "
                "missing and they are not flagged",
                num_zero,
            )

        # entropy of each non-zero feature across the samples
        entropy = counts.loc[nonzero].apply(func=sc.entropy, axis=1).astype(float)

        # the entropy below which a feature is flagged
        entropy_threshold = np.percentile(entropy, q=threshold * 100) if len(entropy) else np.nan
        flagged = entropy < entropy_threshold
        logger.info("number of flagged features: %d", flagged.sum())

        # one row per input feature, on the input's index and in its order: the
        # non-zero features' results go on the rows they were computed from
        # (by the same mask, so duplicate feature names cannot shift them)
        results_df = pd.DataFrame(index=counts.index)
        results_df["entropy"] = np.nan
        results_df.loc[nonzero, "entropy"] = entropy.to_numpy()
        results_df[flag_col] = False
        results_df.loc[nonzero, flag_col] = flagged.to_numpy()

        self.results_df = results_df
        self.entropy_threshold = float(entropy_threshold)
        self.num_flagged = int(flagged.sum())
        logger.info("entropy threshold done")

    @property
    def output(self):
        return self.results_df

    @property
    def properties(self):
        # percentile curve of the entropy distribution, same shape as the
        # stats Entropy module so the report can draw the same chart with
        # this module's actual threshold marked
        numeric = pd.to_numeric(self.results_df["entropy"], errors="coerce").dropna()
        pct = list(range(100))
        pctVal = np.percentile(numeric, pct, method="higher").tolist() if len(numeric) else []
        return {
            "num_kept": len(self.results_df),
            "num_flagged": self.num_flagged,
            "entropy_threshold": self.entropy_threshold,
            "entropies": {"pct": pct, "pctVal": pctVal},
        }


def plot_entropy(entropy_res, threshold, name=None, show=None):
    """
    Function accepts a counts file, a cutoff threshold. The counts file should have the samples
    as the columns and the features as the rows. The cutoff threshold should be a float value
    between 0 and 1. If a name (in the the form of *.png) is given, the figure will be saved with
    the specified name. If show is set to 'show', the plot will be shown.
    """

    import matplotlib.pyplot as plt

    # all-zero features have no entropy
    entropy = entropy_res["entropy"].dropna()

    # sort the entropy values in ascending order
    entropy = entropy.sort_values(ascending=True)
    # threshold is a fraction, numpy's percentile takes a percent
    entropy_threshold = np.percentile(entropy, q=threshold * 100)

    # plot histogram
    fig = plt.gcf()
    plt.hist(entropy, bins="auto", log=True)
    plt.axvline(entropy_threshold, color="red")
    plt.xlabel("Entropy")
    plt.ylabel("Samples Per Bin")
    plt.title("Binned Feature Entropy")
    plt.legend([f"P < {threshold}", "Data"])
    fig.set_size_inches(10, 10)

    if name is not None:
        fig.savefig(name, dpi=100)
    if show is not None:
        plt.show()


@cli_main
def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    cmd = args.subcommand

    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    if cmd == "entropy":
        count_obj = make_cli_count_obj(args)
        pval = option_value(args, "percentile", float)
        if not 0 < pval < 1:
            raise UsageError(
                f"argument -p/--percentile: must be a fraction between 0 and 1 "
                f"(0.05 is the 5th percentile), got {args.percentile}"
            )

        # run the entropy_calc function
        out = EntropyCounts(count_obj, pval)

        if args.plot_output:
            logger.info("plotting entropy threshold to %s", args.plot_output)
            plot_entropy(out.output, pval, name=args.plot_output)

    elif cmd == "shrink":
        count_obj = CountMatrixFile(args.counts_fn)
        p_max = args.p_max
        if p_max is not None:
            p_max = option_value(args, "p_max", float)
        else:
            p_max = np.sqrt(1.0 / count_obj.counts.shape[1])

        out = ShrinkCounts(
            count_obj,
            shrink_factor=option_value(args, "shrink_factor", float),
            p_max=float(p_max),
            iters=option_value(args, "iters"),
        )

    write_output(out.output, args)

    # write out the report json
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
    else:
        logging.info("not generating report due to --no-report")

    logging.info("done")


if __name__ == "__main__":
    main()
