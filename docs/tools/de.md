# `de` — differential expression

!!! important

    The model formulas in this module use detk's
    [formula mini-language](../formulas.md). Read that first before writing
    your models.

    Also remember to [filter](filter.md) prior to differential expression —
    the number of genes provided for hypothesis testing affects the results.
    You may need to filter out genes with zero expression in all samples of
    interest.

Each method accepts a design formula, a counts matrix file, and a
[column data file](../concepts.md#the-column-data-file). Both methods run in R
via the [wrapr bridge](wrapr.md) and require the corresponding R package.

## `deseq2`

Command line interface to a canonical [DESeq2] analysis:

```bash
detk-de deseq2 "counts ~ AgeOfDeath + Status" raw_counts.csv column_data.csv > deseq2_results.csv
```

!!! tip

    - You can provide the whole raw counts matrix with a column data file
      containing only the samples you care about — detk subsets for you.
    - Add brackets with the name of the reference group to control what you
      are comparing against, e.g. `"counts ~ Status[control]"`.

This is roughly equivalent to the following R:

```r
library(DESeq2)

counts <- read.csv("raw_counts.csv", rownames=1)
design.mat <- read.csv("column_data.csv")

dds <- DESeqDataSetFromMatrix(
    countData = counts,
    colData = design.mat,
    design = ~ AgeOfDeath + Status
)

dds <- DESeq(dds, minReplicatesForReplace=Inf)
write.csv(results(dds, cooksCutoff=Inf), de.out.fn)
```

**The analysis implemented here differs from the default DESeq2 analysis** in
the following ways:

- the design formula *must* have `counts` as the only term on the left hand
  side
- no outlier mean trimming based on Cook's distance is performed
- no p-values or adjusted p-values are flagged or omitted due to outliers
- estimated parameters, statistics, and p-values are reported for *all
  variables in the model*, rather than just the last term (request the DESeq2
  default with `--last-term-only`)
- no independent filtering is performed
- every output column is prefixed with its model term, e.g.
  `Status__log2FoldChange`

```text
Usage:
    detk-de deseq2 [options] <design> <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
    --norm-counts          Prevent DESeq2 from normalizing counts prior to
                           running differential expression, default behavior
                           assumes that provided counts are raw
    --last-term-only       Use the default DESeq2 behavior of returning DE parameters
                           for the last term in the model, default behavior is to
                           report parameters for all variables in the model
    --gene-wise-disp       Use estimateDispersionsGeneEst instead of estimateDispersions
    --cores=N              Tell DESeq2 to use N cores when running, requires the
                           BiocParallel Bioconductor package to be installed [default: none]
```

## `firth`

When comparing two classes of samples, [Firth's logistic regression] as
described by [Choi et al] has desirable statistical properties: a better
controlled type I error rate, and less loss of power from including additional
covariates, compared with other DE methods including DESeq2. It uses a
penalized likelihood to avoid [complete separation] of the data, a common
occurrence in RNA-seq. The trade-off is that it needs more samples than
negative-binomial methods — at least ~10 replicates per condition.

A `counts` term must be included on the *right* hand side of the design
formula, with the sample class on the left:

```bash
detk-de firth "Status ~ AgeOfDeath + counts" norm_counts.csv column_data.csv > firth_results.csv
```

```text
Usage:
    detk-de firth [options] <design> <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
    --standardize          Standardize counts prior to running logistic regression
                           as to obtain standardized (i.e. directly comparable)
                           beta coefficients
    --cores=N              Tell R to use N cores when running, requires the
                           parallel R package to be installed [default: none]
```

[DESeq2]: https://bioconductor.org/packages/release/bioc/html/DESeq2.html
[Firth's logistic regression]: https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.1047
[Choi et al]: https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-017-1498-y
[complete separation]: https://stats.oarc.ucla.edu/other/mult-pkg/faq/general/faqwhat-is-complete-or-quasi-complete-separation-in-logisticprobit-regression-and-how-do-we-deal-with-them/
