---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/augment]
---

# The column data augmentation command: placement, operations, names and provenance

- Proposed by: the planning session, 2026-11-19, to design the command
  DETK-0050 calls for

## Background

DETK-0050 (Adam, 2026-11-19) keeps design formulas to the model alone
and moves derived covariates into a detk step that adds columns to the
column data file. Adam named the operations: "adding a column with a
constant, logs with options that control what should happen to zero
values and pseudocounts, parameters for scaling, e.g. having an option
that scales values to be between zero and one". He confirmed that scale
means a z-score with the sample standard deviation (n-1). The command is
part of the 1.0 CLI, so its name, options and output names are promised
until 2.0 (DETK-0001, DETK-0025).

## Context

- **The commands detk has today.** `detk-util` gathers several small
  utilities that work on files: `tidy`, `tidy-counts` and `tidy-covs`
  (which subset the column data file), `annotate` and `gather`. The
  other commands are each one family (`detk-norm`, `detk-transform`, and
  so on) with subcommands.
- **The closest existing options.** `detk-transform plog` takes
  `-c N --pseudocount=N` (default 1) and `-b B --base=B` (default 10) for
  the counts matrix.
- **Provenance today.** Every step writes a module JSON document
  (`in_file_path`, `column_data_path`, `out_file_path`, `params`,
  `properties`). The Process Run Crate turns each document into a
  `CreateAction`, each `params` key into a `PropertyValue`, and links
  input and output files, so a step whose output is the next step's
  column data shows up as lineage (`crate.py`; its `SUBTOOLS` table maps
  each module to its command).
- **Where the output is used.** The new column data file is what
  `detk-de`, `detk-transform rlog/vst` and `detk-norm` read as
  `<cov_fn>`. Its names go into design formulas, then into matrix columns
  and result names (`<column>__<statistic>`), and into R's `formula()`.
  So a new name has to be a plain name: no `__` (which means "variable,
  then level") and nothing R would read as a call.
- **Criteria:** explainable (each derived column traceable to its source
  and operation in the crate); consistent with the rest of the CLI; safe
  defaults (no silent change to the samples); small enough to promise.

## Options

Each item is a separate choice. The planning session's recommendation
comes first; the alternatives follow it.

### 1. Name and placement

**Recommended: its own command, `detk-augment`, with one subcommand per
operation: `constant`, `log`, `scale`.** It is one family of operations,
like `detk-norm`'s, and it uses Adam's word. Each run is one operation,
so each derived column has its own step in the crate.

Alternatives: (a) `detk-util augment`, next to `tidy-covs`, with no new
entry point, but the operations then become a third level
(`detk-util augment log`) or options of one subcommand; (b)
`detk-coldata constant|log|scale`, which names the file rather than the
act.

### 2. One operation per run, several columns

**Recommended:** each run does one operation, on one or more columns:
`detk-augment log --base 2 sample_info.csv age weight -o sample_info.aug.csv`.
Chaining runs is how detk composes steps already, and each run is
recorded.

Alternative: several operations in one run (`--log age --scale weight`).
Fewer files, but one step in the crate stands for several transforms, and
the option set gets combinatorial.

### 3. The operations and their options

**Recommended:**

- `detk-augment constant <cov_fn> <name> <value>` adds a column holding
  `<value>` for every sample. A value that parses as a number is written
  as a number; any other value is written as text.
- `detk-augment log [options] <cov_fn> <column>...`
  - `-b B --base=B`: `e`, `2` or `10`. Default 10, the same as
    `detk-transform plog`.
  - `-c N --pseudocount=N`: added to every value before the log. Default
    0. Unlike plog's default of 1, a covariate is not shifted unless the
    user asks for it.
  - `--zero=error|na`: what happens when a value is still 0 after the
    pseudocount. `error` (the default) fails, naming the column and the
    samples. `na` writes a missing value for those samples. A negative
    value is always an error.
- `detk-augment scale [options] <cov_fn> <column>...`
  - `-m M --method=M`: `zscore` (subtract the mean, divide by the sample
    standard deviation, n-1, as R's `scale()` does), `center` (subtract
    the mean) or `minmax` (to [0, 1]). Default `zscore`.
  - A column with zero variance (or zero range for `minmax`) is an error.

For every operation, a missing value in a source column is an error
naming the samples: no sample is dropped or filled silently.

Alternatives: (a) a third `--zero=pseudocount` mode that adds the
pseudocount only to the zero values (the driver's sketch). Not
recommended: it treats samples unequally, so equal raw values no longer
map to equal outputs. (b) A default base of 2, the usual base for fold
changes, at the cost of differing from `plog`. (c) `exp` or `square`:
not needed for DE designs; they can come in a 1.x minor release.

### 4. Which columns it accepts

**Recommended:** `log` and `scale` take numeric columns only. A column of
text, a boolean column, a column that does not exist and the sample-name
column are each an error naming the column. `constant` refuses a name
that already exists.

### 5. Output names and collisions

**Recommended:** a derived column is named `<column>_<operation>`:
`age_log2`, `age_log10`, `age_ln` (for base e), `age_log2_pc1` when a
pseudocount is used (`pc0.5` for 0.5), `age_zscore`, `age_center`,
`age_minmax`. The variable comes first, as in `<variable>__<level>`, and
a single underscore keeps `__` meaning "level". `-n NAME --name=NAME`
overrides the name when one column is given. A name that already exists
in the column data is an error. There is no flag to overwrite: write the
output to a new file and pick another name. The output keeps every
original column and row as written (IDs as text, DETK-0015), and appends
the new columns in the order given.

Alternatives: (a) the operation first (`log2_age`); (b) `--overwrite`
to replace an existing column, which keeps names short but loses the
source values in the file that is passed on.

### 6. Provenance

**Recommended:** each run writes a module JSON document like other
steps, with the input as `column_data_path` and the new file as
`out_file_path`. `params` holds the operation and its options (`columns`,
`base`, `pseudocount`, `zero`, `method`, `name`). `properties` holds,
for each new column, its source column, the operation, and the numbers
it used: the mean and standard deviation, or the minimum and maximum, for
`scale`, and the count of missing values written for `log --zero=na`.
The numbers let a reader reproduce the column or apply it to new samples.
The crate gets a `SUBTOOLS` entry per subcommand, and the existing
mechanism turns `params` into `PropertyValue`s. A `detk-de` run on the
augmented file then shows `detk-augment` as the step that produced its
column data. A report view shows the new columns and those numbers.

Alternative: no report view, only the module JSON and the crate. Less
to build, but every other step has a view.

## Decision

Open for Adam. The planning session recommends the first option of each
item. `release/augment` waits on this record.

## Consequences

`release/augment` builds the command as decided: its argparse parser
and help on the pattern of `release/cli-migrate` (DETK-0025), the exit
codes of DETK-0031, the completion scripts of DETK-0032, its cli-pin
table, the module JSON and crate entries, a report view, tests, a docs
page and the skill. It names itself in the formula error and in
`docs/formulas.md` (DETK-0050). Adding an operation later is a 1.x minor
release.
