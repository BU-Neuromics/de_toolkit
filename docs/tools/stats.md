# `stats` — count matrix statistics

Easy access to informative count matrix statistics. Each subcommand produces:

- a tabular form of the statistics on stdout (or `-o FILE`), formatted as CSV
  or a human-readable table (`-f table`, via [terminaltables])
- a JSON document recorded under the [report directory](../report.md) with the
  same statistics in machine-parsable form

[terminaltables]: https://github.com/matthewdeanmartin/terminaltables

## Tabular output format

Each tool prints CSV to standard output by default:

```console
$ detk-stats basestats test_counts.csv
stat,val
num_cols,3
num_rows,4
```

Pass `-f table` to pretty-print instead:

```console
$ detk-stats basestats -f table test_counts.csv
+basestats-+-----+
| stat     | val |
+----------+-----+
| num_cols | 4   |
| num_rows | 3   |
+----------+-----+
```

The [`summary`](#summary) subcommand runs multiple subtools; its CSV output
separates each tool's table with a `#<name>` comment line, and its
pretty-printed output prints each table serially.

## `summary`

Run the whole stats battery at once — equivalent to running `basestats`,
`coldist`, `colzero`, `rowzero`, `entropy`, and `pca` separately.

```text
Usage:
    detk-stats summary [options] <counts_fn> [<cov_fn>]

Options:
    --color-col=COLNAME    Use column data column COLNAME for coloring output plots
    --bins=BINS            Number of bins to use for the calculated
                           distributions [default: 20]
    --log                  log transform count statistics
    --density              Produce density distribution by dividing each distribution
                           by the appropriate sum
    -o FILE --output=FILE  Destination of primary output [default: stdout]
    -f FMT --format=FMT    Format of output, either csv or table [default: csv]
```

## `basestats`

Basic statistics of the counts file: number of samples and number of rows.

```text
Usage:
    detk-stats basestats [options] <counts_fn>
```

## `coldist`

Column-wise distribution of counts. Each column is binned by percentile, with
output identical to that produced by `np.histogram`. Recorded per column:
the bin boundaries, the (raw or density) mass in each bin, and extrema beyond
1.5× the inner quartile range.

```text
Usage:
    detk-stats coldist [options] <counts_fn>

Options:
    --bins=N               The number of bins to use when computing the counts
                           distribution [default: 20]
    --log                  Perform a log10 transform on the counts before
                           calculating the distribution. Zeros are omitted
                           prior to histogram calculation.
    --density              Return a density distribution instead of counts,
                           such that the sum of values in *dist* for each
                           column approximately sum to 1.
```

## `rowdist`

Row-wise analog of [`coldist`](#coldist): the distribution of counts within
each feature across samples.

```text
Usage:
    detk-stats rowdist [options] <counts_fn>

Options:
    --bins=N               The number of bins to use when computing the counts
                           distribution [default: 20]
    --log                  Perform a log10 transform on the counts before
                           calculating the distribution
    --density              Return a density distribution instead of counts
```

## `colzero`

Number and fraction of exact-zero counts for each column (sample), along with
the column mean and the mean of only the non-zero counts.

```text
Usage:
    detk-stats colzero [options] <counts_fn>
```

## `rowzero`

Number and fraction of exact-zero counts for each row (feature) — the key
statistic for deciding [filtering](filter.md) thresholds.

```text
Usage:
    detk-stats rowzero [options] <counts_fn>
```

## `entropy`

Row-wise Shannon entropy of counts across samples. For each row, the fraction
of the row's counts contributed by each sample is treated as a probability
distribution and its entropy `H = -Σ p_i · log2(p_i)` computed. Rows with very
low H have most of their count mass in a small number of samples — these are
the rows likely to drive spurious results in downstream analysis, e.g.
differential expression.

```text
Usage:
    detk-stats [options] entropy <counts_fn>
```

## `pca`

Principal component analysis of the counts matrix, returning component
weights, scores, and variances. Supplying a column data file annotates each
sample's projection with covariate values so that sample groups can be
distinguished in the report's PCA plot.

```text
Usage:
    detk-stats pca [options] <counts_fn> [<cov_fn>]
```
