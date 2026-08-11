# `filter` — filtering count matrices

Filter features (rows) out of a counts matrix using a compact filter
mini-language.

```text
Usage:
    detk-filter [options] <command> <counts_fn> [<cov_fn>]

Options:
    -o <out_fn> --output=<out_fn>    Name of output file [default: stdout]
```

Quick start — keep only genes with a mean count greater than 10:

```bash
detk-filter -o counts_gt10.csv 'mean(all) > 10' norm_counts.csv
```

## The filter mini-language

A filter command has the form, enclosed in single or double quotes:

```text
<function>(<column spec>) <inequality> <number>
```

The command describes **rows that should be kept**; rows not meeting the
criterion are filtered out.

Available filter functions:

| Function | Keeps rows based on... |
|----------|------------------------|
| `mean` | the mean value across the column spec |
| `median` | the median value across the column spec |
| `max` | the maximum value across the column spec |
| `min` | the minimum value across the column spec |
| `zero` | how many counts are zero. A number strictly between 0 and 1 is interpreted as a *fraction* of samples; 0 or ≥ 1 as an absolute *number* of samples |
| `nonzero` | how many counts are nonzero, with the same fraction/absolute interpretation |

The supported inequalities are `>`, `>=`, `<`, `<=`, `==`, and `!=`. Numbers
may be positive or negative, integer or floating point. Whitespace is
ignored: `mean(all)>10` ≡ `mean(all) > 10`.

Terms combine with `and` / `or`, and parentheses group arbitrarily:

```text
mean(all) > 10 and zero(all) < 0.5
(mean(all) > 5 and nonzero(all) > 0.9) or mean(all) > 100
```

The second example keeps lowly-but-consistently expressed rows *plus* any row
with an overall mean above 100.

## Incorporating column data

Passing a [column data file](../concepts.md#the-column-data-file) lets filters
operate per sample group. Given column data like:

```text
sample_name, condition
A, test
B, test
C, test
D, control
E, control
```

**Group-wise filtering** — name a column data column as the column spec, and
the filter is applied to each group separately; a row is kept if *any* group
passes:

```text
mean(condition) > 10
```

keeps genes whose mean count exceeds 10 in *either* the test *or* control
samples. This enables expressive schemes like:

```text
nonzero(condition) > 0.5
```

which retains genes expressed in more than half the samples of either
condition — genes uniquely expressed in one group survive, where filtering on
the overall mean would discard them.

**Group-specific filtering** — subset to one level of the column:

```text
mean(condition[test]) > 10
```

keeps genes whose mean exceeds 10 in the test samples, regardless of the
control counts.
