# Derived covariates with Miller

A detk design formula takes column names only: `log2(conc)`, `np.log(x)` or
`scale(age)` in a formula is an error. Derive the column in the sample
information file first, then name it in the formula
(`"counts ~ age_zscore + condition[control]"`). detk has no command for
this; use [Miller](https://miller.readthedocs.io) (`mlr`) with the recipes
below, each run through `detk-util record` so the step is in the report and
the provenance crate.

Full page, with each recipe's output and a failure:
https://bu-neuromics.github.io/de_toolkit/recipes/covariates/

## Rules

- Use these recipes as written. Change only the column (`col=`), the output
  file (`out=`, and the same name after `-o`) and the input file; for the
  constant-column recipe, which has no `col=`, also its column name and
  value (`$study = "pilot"`). Do not
  write a bare `mlr put '$x_log2 = log($x) / log(2)'`: Miller writes -Inf
  for the log of 0, `NaN` for a negative and an empty value for a missing
  one, silently and with exit status 0.
- Each recipe checks every sample before it computes. On a missing or
  non-numeric value, a value at or below 0 for a log (after adding 1 for
  `_log2_pc1`), or a column with one value in every sample for the z-score
  and min-max, it prints the samples to stderr, exits 1, and writes no output
  file; `detk-util record` then exits 1 and records nothing. Report the
  named samples to the user and ask how to handle them; do not drop them or
  substitute values on your own.
- Miller reads a zero-padded whole number (`010`, `05`) as text, so a recipe
  names that sample as "missing or not a number". Tell the user the values
  need writing without leading zeros (`10`, `5`) in the sheet; do not use
  Miller's octal flag (`mlr -O`), which reads `010` as 8. Zero-padded
  sample names are fine.
- On a sheet with a header and no samples, the z-score and min-max recipes
  exit 1 with "has no values"; the others write no output file, so
  `detk-util record` exits 1 naming it. Either way nothing is recorded.
- Name the new column `<column>_log2`, `_log10`, `_ln`, `_log2_pc1`
  (log2 of x + 1), `_zscore` (sd over n - 1, as R's `scale()`), `_center`
  or `_minmax`; the recipes do so. One underscore, never two: `__` is how
  detk names model matrix columns.
- Each recipe reads one sheet and writes another. For several derived
  columns, run them one after another, each reading the last one's output,
  and give `detk-de` the last sheet.
- Miller is not installed with detk: `mamba install -c conda-forge miller`
  or `brew install miller`. If it is missing and cannot be installed, say so
  rather than deriving the column another way without the checks.

## Not the same gather

tidyr's `gather()` (and `pivot_longer()`) and csvtk's `gather` pivot a table
from wide to long format. `detk-util gather` does the opposite kind of job:
it combines per-sample quantifier files into one wide counts matrix. Do not
reach for tidyr or csvtk when asked to gather quantifier outputs, and do not
use `detk-util gather` to reshape a table. Miller's own wide/long verb is
`reshape` (`mlr reshape -i cols -o key,value` to long, `mlr reshape -s
key,value` back to wide), not gather.

## Recipes

A constant column (`study`, `pilot` in every sample):

```bash
detk-util record -q -i sample_info.csv -o sample_info.study.csv -- \
  mlr --icsv --ocsv put -q -s out=sample_info.study.csv '$study = "pilot"; tee > @out, $*' sample_info.csv
```

Log base 2 (`conc_log2`):

```bash
log2='
  @rec[NR] = $*;
  if (!is_numeric($[@col]) || $[@col] <= 0) { @bad[NR] = $[[[1]]] }
  end {
    if (length(@bad) > 0) {
      eprint @col . "_log2: " . @col . " is missing, not a number or not above 0 in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    for (i, r in @rec) { @rec[i][@col . "_log2"] = log(r[@col]) / log(2) }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.conc_log2.csv -- \
  mlr --icsv --ocsv put -q -s col=conc -s out=sample_info.conc_log2.csv "$log2" sample_info.csv
```

Log base 10 (`conc_log10`):

```bash
log10='
  @rec[NR] = $*;
  if (!is_numeric($[@col]) || $[@col] <= 0) { @bad[NR] = $[[[1]]] }
  end {
    if (length(@bad) > 0) {
      eprint @col . "_log10: " . @col . " is missing, not a number or not above 0 in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    for (i, r in @rec) { @rec[i][@col . "_log10"] = log10(r[@col]) }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.conc_log10.csv -- \
  mlr --icsv --ocsv put -q -s col=conc -s out=sample_info.conc_log10.csv "$log10" sample_info.csv
```

Natural log (`conc_ln`):

```bash
ln='
  @rec[NR] = $*;
  if (!is_numeric($[@col]) || $[@col] <= 0) { @bad[NR] = $[[[1]]] }
  end {
    if (length(@bad) > 0) {
      eprint @col . "_ln: " . @col . " is missing, not a number or not above 0 in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    for (i, r in @rec) { @rec[i][@col . "_ln"] = log(r[@col]) }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.conc_ln.csv -- \
  mlr --icsv --ocsv put -q -s col=conc -s out=sample_info.conc_ln.csv "$ln" sample_info.csv
```

Log base 2 with a pseudocount of 1, for a column with zeros (`dose_log2_pc1`):

```bash
log2_pc1='
  @rec[NR] = $*;
  if (!is_numeric($[@col]) || $[@col] + 1 <= 0) { @bad[NR] = $[[[1]]] }
  end {
    if (length(@bad) > 0) {
      eprint @col . "_log2_pc1: " . @col . " is missing, not a number or not above 0 plus 1 in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    for (i, r in @rec) { @rec[i][@col . "_log2_pc1"] = log(r[@col] + 1) / log(2) }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.dose_log2_pc1.csv -- \
  mlr --icsv --ocsv put -q -s col=dose -s out=sample_info.dose_log2_pc1.csv "$log2_pc1" sample_info.csv
```

Z-score, sd over n - 1 (`age_zscore`):

```bash
zscore='
  @rec[NR] = $*; @ids[NR] = $[[[1]]];
  if (!is_numeric($[@col])) { @bad[NR] = $[[[1]]] }
  else { @min = min(@min, $[@col]); @max = max(@max, $[@col]) }
  end {
    if (length(@rec) == 0) {
      eprint @col . "_zscore: " . @col . " has no values: the sheet has no samples";
      asserting_null("stop");
    }
    if (length(@bad) > 0) {
      eprint @col . "_zscore: " . @col . " is missing or not a number in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    if (@min == @max) {
      eprint @col . "_zscore: " . @col . " has the same value in every sample, " . joinv(@ids, ", ");
      asserting_null("stop");
    }
    n = length(@rec); sum = 0; ss = 0;
    for (i, r in @rec) { sum += r[@col] }
    mean = sum / n;
    for (i, r in @rec) { ss += (r[@col] - mean) ** 2 }
    sd = sqrt(ss / (n - 1));
    for (i, r in @rec) { @rec[i][@col . "_zscore"] = (r[@col] - mean) / sd }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.age_zscore.csv -- \
  mlr --icsv --ocsv put -q -s col=age -s out=sample_info.age_zscore.csv "$zscore" sample_info.csv
```

Centring (`age_center`):

```bash
center='
  @rec[NR] = $*;
  if (!is_numeric($[@col])) { @bad[NR] = $[[[1]]] }
  end {
    if (length(@bad) > 0) {
      eprint @col . "_center: " . @col . " is missing or not a number in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    n = length(@rec); sum = 0;
    for (i, r in @rec) { sum += r[@col] }
    mean = sum / n;
    for (i, r in @rec) { @rec[i][@col . "_center"] = r[@col] - mean }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.age_center.csv -- \
  mlr --icsv --ocsv put -q -s col=age -s out=sample_info.age_center.csv "$center" sample_info.csv
```

Min-max to [0, 1] (`age_minmax`):

```bash
minmax='
  @rec[NR] = $*; @ids[NR] = $[[[1]]];
  if (!is_numeric($[@col])) { @bad[NR] = $[[[1]]] }
  else { @min = min(@min, $[@col]); @max = max(@max, $[@col]) }
  end {
    if (length(@rec) == 0) {
      eprint @col . "_minmax: " . @col . " has no values: the sheet has no samples";
      asserting_null("stop");
    }
    if (length(@bad) > 0) {
      eprint @col . "_minmax: " . @col . " is missing or not a number in " . joinv(@bad, ", ");
      asserting_null("stop");
    }
    if (@min == @max) {
      eprint @col . "_minmax: " . @col . " has the same value in every sample, " . joinv(@ids, ", ");
      asserting_null("stop");
    }
    for (i, r in @rec) { @rec[i][@col . "_minmax"] = (r[@col] - @min) / (@max - @min) }
    emit > @out, @rec
  }'
detk-util record -q -i sample_info.csv -o sample_info.age_minmax.csv -- \
  mlr --icsv --ocsv put -q -s col=age -s out=sample_info.age_minmax.csv "$minmax" sample_info.csv
```
