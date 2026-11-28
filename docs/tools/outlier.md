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

Shrink the counts of a sample that holds an outsized fraction of a
feature's counts toward the feature's other samples (Labadorf et al., PLoS
ONE 2015). Each feature is judged on its own, across the samples: a sample
whose count is more than `-p` (`p_max`) of the feature's total is moved
toward the largest count of a sample under `p_max`, by `-f` of the
difference, and this repeats until no sample is over. With `p_max` 0.5,
a feature counted `1, 1, 1, 300` becomes `1, 1, 1, 2.168`; a feature with
the same count in every sample is left as it is.

- A feature whose counts are all in samples over `p_max`, for one a
  feature counted in only one sample, has no sample to shrink toward: it is
  written as read, and a warning gives how many features were left so
  (DETK-0861).
- `-p` must be from 1 / number of samples to 1: below 1 / number of
  samples, a feature with equal counts in every sample is over it, so the
  command exits 2 naming the bound. When not given, `p_max` is
  sqrt(1 / number of samples).

1.0.0 compared each sample's count with that sample's total across
features, not with the feature's total across samples, so its results
differ for every input (see the CHANGELOG, 1.0.1).

The counts may be integers, the usual input, or decimals. The output is
always decimal: a shrunk count is a fraction (an integer count of 301 may
become 30.0625), so integer counts are converted to decimals first and the
output is the same as for the same counts written with decimals. The Python
`shrink` and `pmf_transform` functions do the same and return float counts,
and raise `ValueError` for a `p_max` out of range.

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
                         hold, from 1 / number of samples to 1 (when not given,
                         sqrt(1 / number of samples))
  -i, --iters N          Number of iterations (default: 1000)
```
