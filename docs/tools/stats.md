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
usage: detk-stats summary [options] <counts_fn> [<cov_fn>]

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Column data file: samples in rows, covariates in columns

options:
  -h, --help         Print this help and exit
  --color-col COL    Column of the column data to color the output plots by
  --bins N           Number of bins of the calculated distributions
                     (default: 20)
  --log              log10 transform the counts first (zeros are left out)
  --density          Report each distribution as a density, divided by its sum
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `basestats`

Basic statistics of the counts file: number of samples and number of rows.

```text
usage: detk-stats basestats [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `coldist`

Column-wise distribution of counts. Each column is binned by percentile, with
output identical to that produced by `np.histogram`. Recorded per column:
the bin boundaries, the (raw or density) mass in each bin, and extrema beyond
1.5× the inner quartile range.

```text
usage: detk-stats coldist [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  --bins N           Number of bins of the calculated distributions
                     (default: 20)
  --log              log10 transform the counts first (zeros are left out)
  --density          Report each distribution as a density, divided by its sum
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `rowdist`

Row-wise analog of [`coldist`](#coldist): the distribution of counts within
each feature across samples.

```text
usage: detk-stats rowdist [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  --bins N           Number of bins of the calculated distributions
                     (default: 20)
  --log              log10 transform the counts first (zeros are left out)
  --density          Report each distribution as a density, divided by its sum
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `colzero`

Number and fraction of exact-zero counts for each column (sample), along with
the column mean and the mean of only the non-zero counts.

```text
usage: detk-stats colzero [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `rowzero`

Number and fraction of exact-zero counts for each row (feature) — the key
statistic for deciding [filtering](filter.md) thresholds.

```text
usage: detk-stats rowzero [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `entropy`

Row-wise Shannon entropy of counts across samples. For each row, the fraction
of the row's counts contributed by each sample is treated as a probability
distribution and its entropy `H = -Σ p_i · log2(p_i)` computed. Rows with very
low H have most of their count mass in a small number of samples — these are
the rows likely to drive spurious results in downstream analysis, e.g.
differential expression.

```text
usage: detk-stats entropy [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```

## `pca`

Principal component analysis of the counts matrix, returning component
weights, scores, and variances. Supplying a column data file annotates each
sample's projection with covariate values so that sample groups can be
distinguished in the report's PCA plot.

```text
usage: detk-stats pca [options] <counts_fn> [<cov_fn>]

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited
  <cov_fn>     Column data file: samples in rows, covariates in columns

options:
  -h, --help         Print this help and exit
  -o, --output FILE  Destination of primary output (default: stdout)
  -f, --format FMT   Format of output (choices: csv, table) (default: csv)
```
