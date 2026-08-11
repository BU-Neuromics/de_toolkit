# `util` — counts and column data file utilities

Functions for tidying up counts and [column data](../concepts.md) files —
mostly subsetting one or the other so the sample IDs and their order match.
Combined with `csvgrep` from [csvkit], this is useful for extracting subsets
of samples for downstream differential expression analysis.

[csvkit]: https://csvkit.readthedocs.io

## `tidy`

Subset both the counts columns and the column data rows by intersection,
returning new outputs for both. The tidied column data is only written if you
pass `-p`.

```text
Usage:
    detk-util tidy [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
    -p FILE --column-data-output=FILE  Destination of tidied column data
```

## `tidy-counts`

Subset and order the counts file columns according to the rows of the column
data file. Fails if the column data contains samples missing from the counts
file.

```text
Usage:
    detk-util tidy-counts [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied counts data [default: stdout]
```

## `tidy-covs`

Subset and order the column data rows according to the columns of the counts
file. Fails if the counts file contains samples missing from the column data.

```text
Usage:
    detk-util tidy-covs [options] <counts_fn> <cov_fn>

Options:
    -o FILE --output=FILE  Destination of tidied column data [default: stdout]
```
