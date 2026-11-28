# `outlier` — outlier identification

Functions for identifying and manipulating outlier counts.

## `entropy`

Identify samples that dominate low-entropy features. See
[`detk-stats entropy`](stats.md#entropy) for the underlying statistic.

```text
usage: detk-outlier entropy [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help          Print this help and exit
  -p, --percentile N  The entropy percentile below which a feature is flagged,
                      between 0 and 1 (default: 0.05)
  -o, --output FILE   Destination of the entropy and flag of each feature in CSV
                      format
  --plot-output FILE  Destination of a PNG plot of the entropy distribution and
                      threshold
```

## `shrink`

Iteratively shrink counts that contribute an outsized fraction of a feature's
mass toward the feature's distribution, using a probability-mass-function
transform.

The counts may be integers, the usual input, or decimals. The output is
always decimal: a shrunk count is a fraction (an integer count of 300 may
become 48.75), so integer counts are converted to decimals first and the
output is the same as for the same counts written with decimals. The Python
`shrink` and `pmf_transform` functions do the same and return float counts.

```text
usage: detk-outlier shrink [options] <counts_fn>

positional arguments:
  <counts_fn>  Counts file: features in rows, samples in columns, delimited

options:
  -h, --help             Print this help and exit
  -o, --output FILE      Destination of the shrunk counts in CSV format
                         (default: stdout)
  -f, --shrink-factor N  Shrinkage factor, between 0 and 1 (default: 0.25)
  -p, --p-max N          Largest fraction of a feature's counts one sample may
                         hold (when not given, sqrt(1 / number of samples))
  -i, --iters N          Number of iterations (default: 1000)
```
