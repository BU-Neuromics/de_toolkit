# `transform` — count transformations

Transformations of the distribution of counts in a matrix. `plog` is pure
Python; `rlog` and `vst` wrap [DESeq2] in R.

## `plog`

Pseudo-log transform: `log(counts + pseudocount)`.

```text
usage: detk-transform plog [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help           Print this help and exit
  -c, --pseudocount N  The pseudocount added to each count before the log
                       (default: 1)
  -b, --base N         The base of the logarithm (default: 10)
  -o, --output FILE    Destination of the transformed counts in CSV format
                       (default: stdout)
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
usage: detk-transform rlog [options] <counts_fn> [<design>] [<cov_fn>]

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <design>     Design formula, e.g. 'counts ~ group' (with <cov_fn>)
  <cov_fn>     Sample information file: samples in rows (with <design>)

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of the transformed counts in CSV format
                     (default: stdout)
  --rda FILE         Write the R result objects of the analysis to FILE with
                     saveRDS()
  --strict           Require the counts columns and the sample information rows
                     to name the same samples in the same order
  --blind BOOL       Passed to DESeq2 rlog(blind=); when not given, blind is
                     True
```

## `vst`

Command line interface to the DESeq2 variance-stabilizing transformation:

```bash
detk-transform vst norm_counts.csv > vst_norm_counts.csv
```

```text
usage: detk-transform vst [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of the transformed counts in CSV format
                     (default: stdout)
  --rda FILE         Write the R result objects of the analysis to FILE with
                     saveRDS()
```

[DESeq2]: https://bioconductor.org/packages/release/bioc/html/DESeq2.html
