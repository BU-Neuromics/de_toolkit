# Derived covariates with Miller

<!-- tutorial: requires mlr -->

A [design formula](../formulas.md) takes column names only: detk does not
compute `log2(conc)` or a z-score of `age` inside a formula. A derived
covariate belongs in the column data file, as a column of its own that the
formula names. This page gives a recipe for each derived column a design
usually needs, written for [Miller] (`mlr`), a command line tool for CSV and
other tabular files, and shows each one run through
[`detk-util record`](../tools/util.md#record), so the step that made the
column is part of the analysis's report and provenance.

| Column | Recipe | Value |
| --- | --- | --- |
| a name you pick | [constant](#a-constant-column) | the same text in every sample |
| `<column>_log2` | [log base 2](#logarithms) | log2(x) |
| `<column>_log10` | [log base 10](#logarithms) | log10(x) |
| `<column>_ln` | [natural log](#logarithms) | ln(x) |
| `<column>_log2_pc1` | [log base 2 with a pseudocount](#logarithms) | log2(x + 1) |
| `<column>_zscore` | [z-score](#z-score-centring-and-min-max) | (x - mean) / sd, the sd over n - 1 |
| `<column>_center` | [centring](#z-score-centring-and-min-max) | x - mean |
| `<column>_minmax` | [min-max](#z-score-centring-and-min-max) | (x - min) / (max - min), from 0 to 1 |

The names keep the source column and add a suffix with one underscore, so
they cannot be mistaken for the `variable__level` columns of a model matrix.

Miller is not part of detk; install it from conda-forge, Homebrew or as a
single binary from its [releases](https://github.com/johnkerl/miller/releases):

```console
$ mamba install -c conda-forge miller      # or: brew install miller
$ mlr --version
mlr 6.22.0
```

The recipes need Miller 6; detk's tests run them with the version
conda-forge has.

## Why the recipes check their input

Miller does what it is told without complaint. `log(0)` is `-Inf`, the log
of a negative number is `NaN`, and arithmetic on an empty cell gives an
empty cell, each written to the output without a word. A `-Inf` or an empty
value in a covariate makes every model that uses it fail, or worse, quietly
drop samples. So each recipe checks every sample first and computes second:

- it keeps every record until the end of the file and notes the sample of
  any value it cannot use: a missing or non-numeric value, a value at or
  below zero for a log (after the pseudocount, for `_log2_pc1`), or, for the
  z-score and min-max, a column with the same value in every sample;
- if any were noted, it prints them to stderr, names the samples (from the
  first column), and stops with exit status 1 through a Miller type
  assertion (`asserting_null`), so `detk-util record` fails too and records
  nothing;
- otherwise it adds the new column and writes every record to the output
  file from inside Miller (`emit > @out`), not through a shell redirect, so
  a recipe that stops leaves no output file behind.

Each recipe is a Miller program kept in a shell variable, then one
`detk-util record` command that runs it. `-s col=...` names the column to
derive from and `-s out=...` the file to write, which is also the `-o` of
`detk-util record`. The program does not change, so copy it as it is and
change only those two and the file names.

## The sample sheet

A small sample sheet, with zero-padded sample names, a concentration
(`conc`, ng/µl), a dose that is zero in the controls, and the donor's age:

```bash
cat > sample_info.csv <<'EOF'
sample,condition,conc,dose,age
007,control,52.0,0,34
008,control,118.5,0,51
009,control,87.2,0,45
010,treated,64.9,10,38
011,treated,230.1,30,62
012,treated,41.3,100,29
EOF
```

Miller keeps every value it does not change as it was written, so `007`
stays `007` and `52.0` stays `52.0` in every output below.

## A constant column

A constant column, here `study`, labels every sample the same way, to tell
the samples apart after sheets from two studies are joined. (In a design it
would only repeat the intercept.)

```bash
detk-util record -q -i sample_info.csv -o sample_info.study.csv -- \
  mlr --icsv --ocsv put -q -s out=sample_info.study.csv '$study = "pilot"; tee > @out, $*' sample_info.csv
cat sample_info.study.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,study
007,control,52.0,0,34,pilot
008,control,118.5,0,51,pilot
009,control,87.2,0,45,pilot
010,treated,64.9,10,38,pilot
011,treated,230.1,30,62,pilot
012,treated,41.3,100,29,pilot
```

## Logarithms

Log base 2 of `conc`, as `conc_log2`. Miller has no `log2`, so the program
divides the natural log by `log(2)`:

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
cat sample_info.conc_log2.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,conc_log2
007,control,52.0,0,34,5.700439718141093
008,control,118.5,0,51,6.88874324889826
009,control,87.2,0,45,6.446256229889564
010,treated,64.9,10,38,6.020146573111776
011,treated,230.1,30,62,7.846117173336728
012,treated,41.3,100,29,5.368069876532083
```

Log base 10, as `conc_log10`:

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
cat sample_info.conc_log10.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,conc_log10
007,control,52.0,0,34,1.7160033436347992
008,control,118.5,0,51,2.0737183503461227
009,control,87.2,0,45,1.9405164849325671
010,treated,64.9,10,38,1.8122446968003691
011,treated,230.1,30,62,2.3619166186686433
012,treated,41.3,100,29,1.615950051656401
```

The natural log, as `conc_ln`:

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
cat sample_info.conc_ln.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,conc_ln
007,control,52.0,0,34,3.9512437185814275
008,control,118.5,0,51,4.774912960575186
009,control,87.2,0,45,4.468204330914934
010,treated,64.9,10,38,4.1728476237100445
011,treated,230.1,30,62,5.43851399704132
012,treated,41.3,100,29,3.720862499966987
```

A column with zeros in it, such as `dose`, has no log; log base 2 of the
value plus a pseudocount of 1 is the usual way round that, as
`dose_log2_pc1`. A value fails here only if it is at or below zero after
adding the 1:

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
cat sample_info.dose_log2_pc1.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,dose_log2_pc1
007,control,52.0,0,34,0
008,control,118.5,0,51,0
009,control,87.2,0,45,0
010,treated,64.9,10,38,3.4594316186372978
011,treated,230.1,30,62,4.954196310386876
012,treated,41.3,100,29,6.6582114827517955
```

## When a check fails

A sheet in which sample `009` has no concentration and `011` has a
concentration of 0:

```bash
cat > sample_info_bad.csv <<'EOF'
sample,condition,conc,dose,age
007,control,52.0,0,34
008,control,118.5,0,51
009,control,,0,45
010,treated,64.9,10,38
011,treated,0,30,62
012,treated,41.3,100,29
EOF
```

The log recipe, run on it, names both samples and stops; `detk-util record`
then stops too, with exit status 1, and records nothing:

<!-- tutorial: fails -->
```bash
detk-util record -q -i sample_info_bad.csv -o sample_info_bad.conc_log2.csv -- \
  mlr --icsv --ocsv put -q -s col=conc -s out=sample_info_bad.conc_log2.csv "$log2" sample_info_bad.csv
```

<!-- tutorial: expect -->
```text
conc_log2: conc is missing, not a number or not above 0 in 009, 011
mlr: is_null type-assertion failed at NR=6 FNR=6 FILENAME=sample_info_bad.csv
detk-util: error: command failed with exit status 1: mlr --icsv --ocsv put -q -s col=conc -s out=sample_info_bad.conc_log2.csv ' (--verbose for the traceback)
```

The second line is Miller's, from the assertion that stops it, and the last
is `detk-util record`'s. There is no output file:

```bash
ls sample_info_bad*
```

<!-- tutorial: expect -->
```text
sample_info_bad.csv
```

Without the check, Miller would have written `-Inf` for `011` and an empty
`conc_log2` for `009`, and exited 0.

## Z-score, centring and min-max

The z-score of `age`, as `age_zscore`: the age less the mean age, over the
sample standard deviation, the one that divides by n - 1 (as R's `sd()` and
`scale()` do, and numpy's `std(ddof=1)`). The program computes the mean and
standard deviation itself, in two passes over the values, rather than with
Miller's `stddev`, which is computed in one pass and can be off in the last
digits; on six samples that all have the value 7.2 it gives about 1.2e-7,
not 0. For the same reason a column that does not vary is found by its
smallest and largest values being equal:

```bash
zscore='
  @rec[NR] = $*; @ids[NR] = $[[[1]]];
  if (!is_numeric($[@col])) { @bad[NR] = $[[[1]]] }
  else { @min = min(@min, $[@col]); @max = max(@max, $[@col]) }
  end {
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
cat sample_info.age_zscore.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,age_zscore
007,control,52.0,0,34,-0.7582060886223619
008,control,118.5,0,51,0.6479215666409279
009,control,87.2,0,45,0.15164121772447264
010,treated,64.9,10,38,-0.4273525226780585
011,treated,230.1,30,62,1.5577688729877626
012,treated,41.3,100,29,-1.1717730460527414
```

Centring, as `age_center`: the age less the mean age. A column that does
not vary centres to zeros, which is not an error:

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
cat sample_info.age_center.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,age_center
007,control,52.0,0,34,-9.166666666666664
008,control,118.5,0,51,7.833333333333336
009,control,87.2,0,45,1.8333333333333357
010,treated,64.9,10,38,-5.166666666666664
011,treated,230.1,30,62,18.833333333333336
012,treated,41.3,100,29,-14.166666666666664
```

Min-max scaling, as `age_minmax`: the youngest donor gets 0, the oldest 1,
and the others fall between in proportion:

```bash
minmax='
  @rec[NR] = $*; @ids[NR] = $[[[1]]];
  if (!is_numeric($[@col])) { @bad[NR] = $[[[1]]] }
  else { @min = min(@min, $[@col]); @max = max(@max, $[@col]) }
  end {
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
cat sample_info.age_minmax.csv
```

<!-- tutorial: expect -->
```text
sample,condition,conc,dose,age,age_minmax
007,control,52.0,0,34,0.15151515151515152
008,control,118.5,0,51,0.6666666666666666
009,control,87.2,0,45,0.48484848484848486
010,treated,64.9,10,38,0.2727272727272727
011,treated,230.1,30,62,1
012,treated,41.3,100,29,0
```

## Several derived columns, and the design

Each recipe reads one sheet and writes another, so to add several columns,
run them one after another, each reading the sheet the one before wrote.
Then name the derived column in the design, as any other column:

```console
$ detk-de deseq2 -o de_results.csv "counts ~ age_zscore + condition[control]" counts.csv sample_info.age_zscore.csv
```

Each `detk-util record` wrote a module JSON document to `detk_report/json/`
naming the tool, `mlr`, and its version, with the command and the checksum
of every file it read and wrote. So `detk-report generate` lists each
recipe as a recorded step, and the provenance crate shows it as the step
that produced the sheet `detk-de` read (see
[`detk-util record`](../tools/util.md#record)).

[Miller]: https://miller.readthedocs.io
