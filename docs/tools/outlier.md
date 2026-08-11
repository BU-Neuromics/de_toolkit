# `outlier` — outlier identification

Functions for identifying and manipulating outlier counts.

## `entropy`

Identify samples that dominate low-entropy features. See
[`detk-stats entropy`](stats.md#entropy) for the underlying statistic.

```text
Usage:
    detk-outlier entropy <counts_fn> [options]

Options:
    -p P --percentile=P    Float value between 0 and 1
    -o FILE --output=FILE  Name of the output csv
    --plot-output=FILE     Name of the plot png
```

## `shrink`

Iteratively shrink counts that contribute an outsized fraction of a feature's
mass toward the feature's distribution, using a probability-mass-function
transform.

```text
Usage:
    detk-outlier shrink [options] <counts_fn>

Options:
    -o FILE --output=FILE   Destination of primary output [default: stdout]
    -f N --shrink-factor=N  Shrinkage factor number float between 0 and 1 [default: 0.25]
    -p N --p-max=N          Percent counts of sample default is sqrt(1/num samples)
    -i N --iters=N          Number of iterations [default: 1000]
```
