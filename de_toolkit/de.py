r"""
Test every feature of a counts matrix for differential expression with a
model of the sample information: DESeq2 (deseq2) or Firth's penalized
logistic regression (firth). Each takes a model <design> written as a
formula, a counts file and a sample information file whose first column
names the samples; the output is a table with one row per feature.
"""

TODO = r"""
    detk-de t-test ( help | [options] <counts_fn> <cov_fn> )
"""

_STRICT_HELP = (
    "Require the counts file's sample columns to be the same as, and in the same "
    "order as, the rows of the sample information file"
)

# each subcommand: the one line the command's help lists it with, its
# description and its examples
SUBCOMMANDS = {
    "deseq2": dict(
        help="Differential expression with DESeq2 (needs R and DESeq2)",
        description="""\
Test for differential expression with the DESeq2 Bioconductor package. The
<design> is a formula with counts on the left, such as "counts ~ group" or
"counts ~ cell + dex[untrt]", the bracket naming a factor's reference level.
By default the result reports the parameters of every variable in the model
and assumes the counts are raw.""",
        examples=[
            (
                "DESeq2 of counts.csv by group in sample_info.csv",
                'detk-de deseq2 -o deseq2_results.csv "counts ~ group" counts.csv sample_info.csv',
            ),
        ],
    ),
    "firth": dict(
        help="Firth's penalized logistic regression on each feature (needs R)",
        description="""\
Test for differential expression with Firth's penalized logistic regression
(the logistf R package): for each feature, the condition on the left of the
<design> is modelled from the feature's counts and the other variables, as
in "group ~ counts + age".""",
        examples=[
            (
                "Firth logistic regression of group on each feature of counts.csv",
                'detk-de firth -o firth_results.csv "group ~ counts" counts.csv sample_info.csv',
            ),
        ],
    ),
}


def build_parser():
    "The detk-de command line parser"
    parser = DetkParser(prog="detk-de", description=__doc__.strip())
    add_command_options(parser)
    subs = add_subcommands(parser)
    for name, spec in SUBCOMMANDS.items():
        sub = subs.add_parser(
            name, help=spec["help"], description=spec["description"], examples=spec["examples"]
        )
        sub.add_argument(
            "design", metavar="<design>", help='Model formula, quoted, such as "counts ~ group"'
        )
        sub.add_argument(
            "counts_fn",
            metavar="<counts_fn>",
            help="Counts file: features in rows, samples in columns, delimited",
        )
        sub.add_argument(
            "cov_fn",
            metavar="<cov_fn>",
            help="Sample information file: samples in rows, the first column their names",
        )
        sub.add_argument(
            "-o", "--output", metavar="FILE", default="stdout", help="Destination of primary output"
        )
        sub.add_argument(
            "--routput-dir",
            metavar="DIR",
            help="Directory to keep the R script, its inputs and outputs in, for debugging",
        )
        sub.add_argument(
            "--rda",
            metavar="FILE",
            help="File to saveRDS() the R result objects of the analysis to",
        )
        sub.add_argument("--strict", action="store_true", help=_STRICT_HELP)
        if name == "deseq2":
            sub.add_argument(
                "--norm-counts",
                action="store_true",
                help="Do not let DESeq2 normalize the counts: they are already normalized",
            )
            sub.add_argument(
                "--last-term-only",
                action="store_true",
                help="Report the parameters of the model's last term only (DESeq2's default)",
            )
            sub.add_argument(
                "--gene-wise-disp",
                action="store_true",
                help="Use estimateDispersionsGeneEst instead of estimateDispersions",
            )
            sub.add_argument(
                "--cores",
                metavar="N",
                default="none",
                help="Number of cores DESeq2 uses (needs the BiocParallel package)",
            )
        else:
            sub.add_argument(
                "--standardize",
                action="store_true",
                help="Standardize the counts first, so the coefficients are directly comparable",
            )
            sub.add_argument(
                "--cores",
                metavar="N",
                default="none",
                help="Number of cores R uses (needs the parallel R package)",
            )
        add_common_options(sub)
    return parser


import logging
from pprint import pformat
import sys
import os
from .common import (
    DetkModule,
    DetkParser,
    InvalidDesignException,
    add_command_options,
    add_common_options,
    add_subcommands,
    make_cli_count_obj,
    parse_cli,
    set_logging,
    write_output,
)
import numpy as np
import pandas as pd

from .wrapr import require_r, wrapr, require_r_package
from .util import stub
from .report import DetkReport

# caps for the per-term point sets emitted into the report JSON: all
# significant features up to DE_SIG_CAP, then a deterministic sample of the
# rest up to DE_POINT_BUDGET total. The full result table is the tool's
# primary output file; the report set only has to be visually faithful.
DE_POINT_BUDGET = 5000
DE_SIG_CAP = 2500
DE_SIG_THRESHOLD = 0.05


def _de_report_data(df, kind):
    """Build capped, plot-ready volcano/MA data from a DE result DataFrame.

    Emits coordinates rather than raw statistics (effect, -log10 p, log10
    mean, significance class) because the module JSON encoder rounds floats
    to 3 decimals, which would destroy small p-values.
    """
    if kind == "deseq2":
        eff_suffix, p_suffix, padj_suffix = "__log2FoldChange", "__pvalue", "__padj"
    else:
        eff_suffix, p_suffix, padj_suffix = "__beta", "__p", "__padj"

    feature_col = df.columns[0]
    features = df[feature_col].astype(str)
    lmean = None
    if "baseMean" in df.columns:
        lmean = np.log10(pd.to_numeric(df["baseMean"], errors="coerce") + 1)

    terms = []
    for col in df.columns:
        if not col.endswith(eff_suffix):
            continue
        term = col[: -len(eff_suffix)]
        if term == "Intercept":
            continue
        sub = pd.DataFrame(
            {
                "feature": features,
                "effect": pd.to_numeric(df[col], errors="coerce"),
                "p": pd.to_numeric(
                    df.get(term + p_suffix, pd.Series(index=df.index, dtype=float)),
                    errors="coerce",
                ),
                "padj": pd.to_numeric(
                    df.get(term + padj_suffix, pd.Series(index=df.index, dtype=float)),
                    errors="coerce",
                ),
            }
        )
        if lmean is not None:
            sub["lmean"] = lmean
        sub = sub.dropna(subset=["effect", "p"])
        total = len(sub)
        if total == 0:
            continue

        sig_mask = sub["padj"] < DE_SIG_THRESHOLD
        sub["sig"] = "ns"
        sub.loc[sig_mask & (sub["effect"] > 0), "sig"] = "up"
        sub.loc[sig_mask & (sub["effect"] < 0), "sig"] = "down"
        sub["nlp"] = -np.log10(sub["p"].clip(lower=1e-300))

        sig = sub[sig_mask].nsmallest(DE_SIG_CAP, "padj")
        rest = sub.loc[~sub.index.isin(sig.index)]
        n_fill = max(0, DE_POINT_BUDGET - len(sig))
        if len(rest) > n_fill:
            # deterministic, density-preserving: evenly spaced over the
            # p-sorted remainder
            rest = rest.sort_values("p")
            keep = np.unique(np.linspace(0, len(rest) - 1, n_fill).astype(int))
            rest = rest.iloc[keep]
        shown = pd.concat([sig, rest])

        cols = ["feature", "effect", "nlp", "sig"] + (["lmean"] if lmean is not None else [])
        terms.append(
            {
                "term": term,
                "total": int(total),
                "shown": int(len(shown)),
                "num_sig": int(sig_mask.sum()),
                "sig_threshold": DE_SIG_THRESHOLD,
                "points": shown[cols].to_dict("records"),
            }
        )

    return {"feature_col": feature_col, "kind": kind, "terms": terms}


# setup logging, null on the library level
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def deseq2(
    count_obj,
    normalized=True,
    rda=None,
    all_coeff_results=True,
    gene_wise_disp_est=False,
    cores=None,
    routput_dir=None,
):
    obj = DESeq2Counts(
        count_obj,
        normalized,
        rda,
        all_coeff_results,
        gene_wise_disp_est,
        cores,
        routput_dir=routput_dir,
    )
    return obj.output


class DESeq2Counts(DetkModule):
    @require_r("DESeq2")
    def __init__(
        self,
        count_obj,
        normalized=True,
        rda=None,
        all_coeff_results=True,
        gene_wise_disp_est=False,
        cores=None,
        routput_dir=None,
    ):
        self.count_obj = count_obj
        self["params"] = {
            "design": count_obj.design,
            "normalized": normalized,
            "rda": rda,
            "all_coeff_results": all_coeff_results,
            "gene_wise_disp_est": gene_wise_disp_est,
            "cores": cores,
        }

        # make a copy of count_obj, since we mutate it
        count_obj = count_obj.copy()

        # validate the design matrix
        if count_obj.design is None or count_obj.design_matrix is None:
            raise InvalidDesignException("count_obj must have a design matrix to use DESeq2")

        if "counts" not in count_obj.design_matrix.lhs:
            raise InvalidDesignException(
                'The term "counts" must exist on the left  hand side of the model in DESeq2'
            )

        # drop the counts from the left hand side since DESeq2 doesn't use it
        count_obj.design_matrix.drop_from_lhs("counts", quiet=True)

        # make sure the rhs of the design matrix doesn't have an intercept
        count_obj.design_matrix.drop_from_rhs("Intercept", quiet=True)

        if cores is not None:
            logging.debug("Enabling parallelism with BiocParallel")
            require_r_package("BiocParallel")
            try:
                cores = int(cores)
            except ValueError as e:
                raise Exception("The cores argument to DESeq2 must be an integer") from e

        params = {
            "design": count_obj.design,
            "normalized": normalized,
            "rda": rda,
            "cores": cores,
            "all.coeff.results": all_coeff_results,
            "gene.wise.disp.est": gene_wise_disp_est,
        }
        logger.debug("DESeq2 wrapr params:\n %s", pformat(params))
        script = """\
            library(DESeq2)
            # the IDs as text, as written (007 stays 007; see read.id.csv in wrapr)
            cnts <- read.id.csv(counts.fn)
            index.name <- names(cnts)[1]

            # first column name is blank
            orig.index.name <- index.name
            if(index.name == '') {
                index.name <- 'feature'
                colnames(cnts)[1] <- index.name
            }
            rownames(cnts) <- cnts[[1]]
            cnts <- cnts[c(-1)]

            rnames <- rownames(cnts)

            # DESeq2 whines when input counts aren't integers
            # round the counts matrix
            cnts <- data.frame(lapply(cnts,function(x) { round(as.numeric(x)) }),
                check.names=FALSE
            )
            rownames(cnts) <- rnames

            # use parallelism if params$cores > 0
            cores <- if(is.null(params$cores)) { 0 } else { as.numeric(params$cores) }
            parallel <- FALSE
            if(cores>0) {
                library(BiocParallel)
                register(MulticoreParam(cores))
                parallel <- TRUE
            }

            # design formula
            form <- params$design

            # load design matrix
            # the sample names as text, as in the counts header (001 stays 001)
            design.mat <- read.id.csv(metadata.fn,row.names=TRUE)

            # make sure the counts and design matrix samples line up
            stopifnot(colnames(cnts) == rownames(design.mat))

            dds <- DESeqDataSetFromMatrix(
                countData = cnts,
                colData = design.mat,
                design = formula(form)
            )

            # if counts are already normalized, don't normalize them
            if(params$normalized) {
                sizeFactors(dds) <- rep(1,nrow(design.mat))
            } else {
                dds <- estimateSizeFactors(dds)
            }

            # in some cases R can throw this error:
            if(params$gene.wise.disp.est) {
                dds <- estimateDispersionsGeneEst(dds)
                dispersions(dds) <- mcols(dds)$dispGeneEst
            } else {
                dds <- estimateDispersions(dds)
            }

            # turn off cooks distance outlier replacement
            #dds <- DESeq(dds,minReplicatesForReplace=Inf,parallel=parallel)

            dds <- nbinomWaldTest(dds)

            result_from_dds <- function(name) {
                res.df <- data.frame(
                    log2FoldChange=mcols(dds)[[name]],
                    lfcSE=mcols(dds)[[paste0('SE_',name)]],
                    stat=mcols(dds)[[paste0('WaldStatistic_',name)]],
                    pvalue=mcols(dds)[[paste0('WaldPvalue_',name)]],
                    padj=p.adjust(mcols(dds)[[paste0('WaldPvalue_',name)]],method='fdr')
                )
                colnames(res.df) <- paste(name,colnames(res.df),sep='__')
                res.df
            }

            # organize output results
            res.df <- if(params$all.coeff.results==TRUE) {
                # report statistics and p-values on all model variables
                # output columns are:
                #   basemean
                #   for each model variable:
                #     <varname>__log2FoldChange (mcols(dds)[['<varname>']])
                #     <varname>__lfcSE (mcols(dds)[['SE_<varname>']])
                #     <varname>__stat (mcols(dds)[['WaldStatistic_<varname>']])
                #     <varname>__pvalue (mcols(dds)[['WaldPvalue_<varname>']])
                #     <varname>__padj (p.adjust(mcols(dds)[['WaldPvalue_<varname>']],method='fdr')

                # example mcols(dds) names:
                # Intercept
                # category__case
                # SE_Intercept
                # SE_category__case
                # WaldStatistic_Intercept
                # WaldStatistic_category__case
                # WaldPvalue_Intercept
                # WaldPvalue_category__case
                do.call(
                    cbind,
                    lapply(
                        colnames(design.mat),
                        result_from_dds
                    )
                )
            } else {
                # just report the last column as is the DESeq2 default
                result_from_dds(tail(colnames(design.mat),n=1))
            }

            # add on the basemean
            res.df <- cbind(mcols(dds)[['baseMean']],res.df)
            colnames(res.df)[1] <- 'baseMean'

            if(!is.null(params$rda)) {
                saveRDS(dds,params$rda)
            }

            # because R is stupid and can't easily write out a column name for
            # a row name
            res.df.cols <- colnames(res.df)
            res.df[[index.name]] <- rnames
            res.df <- res.df[c(index.name,res.df.cols)]

            # put the original first column name back
            colnames(res.df)[1] <- orig.index.name

            write.csv(res.df,out.fn,row.names=F)
        """
        logging.info("Executing DESeq2 in wrapr")
        with wrapr(
            script,
            counts=count_obj.counts,
            metadata=count_obj.design_matrix.full_matrix,
            params=params,
            routput_dir=routput_dir,
        ) as wr:
            self.wr_output = wr.output

        logging.info("Done executing DESeq2 in wrapr")

    @property
    def output(self):
        return self.wr_output

    @property
    def properties(self):
        return {"num_length": len(self.wr_output), "de": _de_report_data(self.wr_output, "deseq2")}


def firth_logistic_regression(count_obj, standardize=False, rda=None, cores=None, routput_dir=None):
    obj = FLGCounts(count_obj, standardize, rda, cores)
    return obj.output


class FLGCounts(DetkModule):
    @require_r("logistf")
    def __init__(self, count_obj, standardize=False, rda=None, cores=None, routput_dir=None):
        self.count_obj = count_obj

        # make a copy of count_obj, since we mutate it
        count_obj = count_obj.copy()

        # validate the design matrix
        if count_obj.design is None or count_obj.design_matrix is None:
            raise InvalidDesignException(
                "count_obj must have a design matrix in Firth logistic regression"
            )

        if "counts" not in count_obj.design_matrix.rhs:
            raise InvalidDesignException(
                'The term "counts" must exist on the right hand'
                "side of the model in Firth logistic regression"
            )

        # make sure the rhs of the design matrix doesn't have an intercept
        count_obj.design_matrix.drop_from_rhs("Intercept", quiet=True)

        if cores is not None:
            require_r_package("parallel")
            try:
                cores = int(cores)
            except ValueError as e:
                raise Exception(
                    "The cores argument to firth_logistic_regression must be an integer"
                ) from e

        params = {
            "design": count_obj.design,
            "standardize": standardize,
            "rda": rda,
            "cores": cores,
        }
        # record on the module so the report/provenance layer sees them
        self["params"] = params
        logger.debug("logistf wrapr params:\n %s", pformat(params))
        script = """\
            library(logistf)
            # the IDs as text, as written (007 stays 007; see read.id.csv in wrapr)
            cnts <- read.id.csv(counts.fn)
            index.name <- names(cnts)[1]

            # first column name is blank
            orig.index.name <- index.name
            if(index.name == '') {
                index.name <- 'feature'
                colnames(cnts)[1] <- index.name
            }

            rownames(cnts) <- cnts[[1]]
            cnts <- cnts[c(-1)]

            rnames <- rownames(cnts)
            cnts <- data.frame(lapply(cnts,as.numeric),check.names=FALSE)
            rownames(cnts) <- rnames

            # scale counts to obtain standardized beta estimates
            if(params$standardize) {
                cnts <- data.frame(t(scale(t(cnts))),check.names=FALSE)
            }

            # design formula
            form <- params$design

            # load design matrix
            # the sample names as text, as in the counts header (001 stays 001)
            design.mat <- read.id.csv(metadata.fn,row.names=TRUE)

            fit <- NULL

            applyf <- lapply
            if(!is.null(params$cores)) {
                library(parallel)
                applyf <- function(l,f) { mclapply(l,f,mc.cores=params$cores) }
            }
            res.orig <- applyf(rownames(cnts),
                function(gene) {
                  x <- data.frame(design.mat,check.names=FALSE)
                  x$counts <- unlist(cnts[gene,])
                  log.fit <- logistf(formula(form),data=x,pl=F)
                  fit <<- log.fit
                  out <- c(gene, 'OK')
                  names(out) <- c(index.name,'status')
                  coeffs <- log.fit$coeff
                  names(coeffs) <- paste0(names(coeffs),'__beta')
                  probs <- log.fit$prob
                  names(probs) <- paste0(names(probs),'__p')
                  padj <- rep(NA,length(probs))
                  names(padj) <- paste0(names(log.fit$prob),'__padj')
                  cp <- c(rbind(coeffs,probs,padj))
                  cp.names <- c(rbind(names(coeffs),names(probs),names(padj)))
                  cp.names <- gsub(".Intercept.","int",cp.names)
                  names(cp) <- cp.names
                  c(out,cp)
                }
            )

            if(!is.null(params$rda)) {
                saveRDS(fit,params$rda)
            }
            res <- do.call(rbind,res.orig)
            res.df <- as.data.frame(res,stringsAsFactors=F,check.names=FALSE)
            for(c in colnames(res.df)[c(-1,-2)]) {
                res.df[c] <- as.numeric(res.df[c][[1]])
            }
            # calculate p.adjust for each pvalue col
            for(c in Filter(function(x) endsWith(x,'__p'),colnames(res.df))) {
                res.df[paste0(c,'adj')] <- p.adjust(res.df[[c]],"fdr")
            }

            # put the original first column name back
            colnames(res.df)[1] <- orig.index.name

            write.csv(res.df,out.fn,row.names=F)
        """
        logging.info("Executing logistf in wrapr")
        with wrapr(
            script,
            counts=count_obj.counts,
            metadata=count_obj.design_matrix.full_matrix,
            params=params,
            routput_dir=routput_dir,
        ) as wr:
            self.wr_output = wr.output

        logging.info("Done executing logistf in wrapr")

    @property
    def output(self):
        return self.wr_output

    @property
    def properties(self):
        return {"num_length": len(self.wr_output), "de": _de_report_data(self.wr_output, "firth")}


@stub
def t_test(count_obj):
    pass


def main(argv=sys.argv):

    args = parse_cli(build_parser(), argv)
    cmd = args.subcommand
    set_logging(args)
    logger.info("cmd: %s", " ".join(argv[1:]))

    count_obj = make_cli_count_obj(args)

    try:
        cores = int(args.cores) if args.cores != "none" else None
        if cmd == "deseq2":
            logger.info("running DESeq2")
            out = DESeq2Counts(
                count_obj,
                normalized=args.norm_counts,
                rda=args.rda,
                all_coeff_results=not args.last_term_only,
                gene_wise_disp_est=args.gene_wise_disp,
                cores=cores,
                routput_dir=args.routput_dir,
            )
        elif cmd == "firth":
            logger.info("running Firth logistic regression")
            out = FLGCounts(
                count_obj,
                rda=args.rda,
                standardize=args.standardize,
                cores=cores,
                routput_dir=args.routput_dir,
            )
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
                workdir=os.getcwd(),
            )
    else:
        logging.info("not generating report due to --no-report")

    logging.info("done")


if __name__ == "__main__":
    main()
