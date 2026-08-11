# `transform` — count transformations

Transformations of the distribution of counts in a matrix. `plog` is pure
Python; `rlog` and `vst` wrap [DESeq2] in R.

## `plog`

Pseudo-log transform: `log(counts + pseudocount)`.

```text
Usage:
    detk-transform plog [options] <counts_fn>

Options:
    -c N --pseudocount=N   The pseudocount to use when taking the log transform [default: 1]
    -b B --base=B          The base of the log to use [default: 10]
    -o FILE --output=FILE  Destination of primary output [default: stdout]
```

## `rlog`

Command line interface to the DESeq2 regularized-log transformation. As in the
originating package, the default is a *blind* transformation, i.e. without
respect to an experimental design:

```bash
detk-transform rlog norm_counts.csv > rlog_norm_counts.csv
```

To perform a non-blind transformation, provide a
[design formula](../formulas.md) and column data file:

```bash
detk-transform rlog norm_counts.csv "counts ~ AgeOfDeath + Status" column_data.csv > rlog_nonblind.csv
```

```text
Usage:
    detk-transform rlog [options] <counts_fn> [<design> <cov_fn>]

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
    --strict               Require that the sample order indicated by the column names in the
                           counts file are the same as, and in the same order as, the
                           sample order in the row names of the covariates file
```

## `vst`

Command line interface to the DESeq2 variance-stabilizing transformation:

```bash
detk-transform vst norm_counts.csv > vst_norm_counts.csv
```

```text
Usage:
    detk-transform vst [options] <counts_fn>

Options:
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    --rda=RDA              Filename passed to saveRDS() R function of the result
                           objects from the analysis
```

[DESeq2]: https://bioconductor.org/packages/release/bioc/html/DESeq2.html
