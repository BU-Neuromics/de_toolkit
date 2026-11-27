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
write.csv(results(dds, independentFiltering=FALSE, cooksCutoff=Inf), de.out.fn)
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
  `Status__case__log2FoldChange` for the `case` level of `Status`

```text
usage: detk-de deseq2 [options] <design> <counts_fn> <cov_fn>

positional arguments:
  <design>     Model formula, quoted, such as "counts ~ group"
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Sample information file: samples in rows, the first column their
               names

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  --routput-dir DIR  Directory to keep the R script, its inputs and outputs in,
                     for debugging
  --rda FILE         File to saveRDS() the R result objects of the analysis to
  --strict           Require the counts file's sample columns to be the same as,
                     and in the same order as, the rows of the sample
                     information file
  --norm-counts      Do not let DESeq2 normalize the counts: they are already
                     normalized
  --last-term-only   Report the parameters of the model's last term only
                     (DESeq2's default)
  --gene-wise-disp   Use estimateDispersionsGeneEst instead of
                     estimateDispersions
  --cores N          Number of cores DESeq2 uses (needs the BiocParallel
                     package) (default: none)
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
usage: detk-de firth [options] <design> <counts_fn> <cov_fn>

positional arguments:
  <design>     Model formula, quoted, such as "counts ~ group"
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Sample information file: samples in rows, the first column their
               names

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  --routput-dir DIR  Directory to keep the R script, its inputs and outputs in,
                     for debugging
  --rda FILE         File to saveRDS() the R result objects of the analysis to
  --strict           Require the counts file's sample columns to be the same as,
                     and in the same order as, the rows of the sample
                     information file
  --standardize      Standardize the counts first, so the coefficients are
                     directly comparable
  --cores N          Number of cores R uses (needs the parallel R package)
                     (default: none)
```

[DESeq2]: https://bioconductor.org/packages/release/bioc/html/DESeq2.html
[Firth's logistic regression]: https://onlinelibrary.wiley.com/doi/abs/10.1002/sim.1047
[Choi et al]: https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-017-1498-y
[complete separation]: https://stats.oarc.ucla.edu/other/mult-pkg/faq/general/faqwhat-is-complete-or-quasi-complete-separation-in-logisticprobit-regression-and-how-do-we-deal-with-them/
