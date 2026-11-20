---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/record, release/miller-recipes]
evidence:
  - {pointer: "DETK-0060", visibility: public}
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: "Retitled and rewritten for Adam's answer: Options B and C from the research (DETK-0060) added, the draft kept as Option A, Decision and Consequences for Option C", why: "Adam chose Option C on 2026-11-20, relayed by the driver session"}
---

# Derived covariates: Miller recipes and detk-util record, not a detk augmentation command

- Proposed by: the planning session, 2026-11-19, to design the command
  DETK-0050 calls for
- Revised by: the planning session, 2026-11-20, to add the options the
  research of DETK-0060 laid out and record Adam's answer

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

Before answering, Adam asked whether detk should build such a command at
all or point to an existing tool. A research session surveyed the
command-line CSV tools (DETK-0060, which keeps its report in full) and
recommended documenting Miller and adding one small detk command that
records an external step in detk's provenance.

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

### Option A: build `detk-augment` (the draft of 2026-11-19)

The draft as the planning session wrote it, kept for the record. Each
item was a separate choice, its recommendation first.

#### 1. Name and placement

**Recommended: its own command, `detk-augment`, with one subcommand per
operation: `constant`, `log`, `scale`.** It is one family of operations,
like `detk-norm`'s, and it uses Adam's word. Each run is one operation,
so each derived column has its own step in the crate.

Alternatives: (a) `detk-util augment`, next to `tidy-covs`, with no new
entry point, but the operations then become a third level
(`detk-util augment log`) or options of one subcommand; (b)
`detk-coldata constant|log|scale`, which names the file rather than the
act.

#### 2. One operation per run, several columns

**Recommended:** each run does one operation, on one or more columns:
`detk-augment log --base 2 sample_info.csv age weight -o sample_info.aug.csv`.
Chaining runs is how detk composes steps already, and each run is
recorded.

Alternative: several operations in one run (`--log age --scale weight`).
Fewer files, but one step in the crate stands for several transforms, and
the option set gets combinatorial.

#### 3. The operations and their options

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

#### 4. Which columns it accepts

**Recommended:** `log` and `scale` take numeric columns only. A column of
text, a boolean column, a column that does not exist and the sample-name
column are each an error naming the column. `constant` refuses a name
that already exists.

#### 5. Output names and collisions

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

#### 6. Provenance

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

### Option B: a separate tidyr-style utility package

A general verb set (select, rename, mutate, join, pivot) as its own
package. The most work: to be worth reusing it needs the whole verb set,
which Miller and xan already are; provenance is the hardest of the three
(its own format, or detk's module JSON, so not really independent); a
second package to maintain. DETK-0060 does not recommend it.

### Option C: document Miller and add `detk-util record`

detk builds no augmentation operations. Its docs and agent skill carry
tested Miller (`mlr`) recipes for the operations Adam named (a constant
column; log with a base and a pseudocount; z-score with n-1; centring;
min-max), each with the checks Miller lacks written into it (a zero or
negative value left after the pseudocount, a missing value, zero
variance or range: each fails and names the samples). One new detk
command, `detk-util record`, runs an external command and writes a
module JSON document for it (the command line, the tool's name and
`--version`, the input and output files named explicitly), with a
`SUBTOOLS` entry, so the Process Run Crate shows the step as the
producer of the column data a later `detk-de` run reads. It records any
external step (awk, an R script), not only Miller.

Against A: the safe defaults live in documented, tested recipes rather
than code, and the crate records a command rather than structured
statistics (the mean and standard deviation used). For it: one
subcommand promised in 1.0 instead of three, no reinvention, and
provenance covered once, generically.

## Decision

Option C, chosen by Adam on 2026-11-20, relayed by the driver session:
"go with c, and I like the record command, no need for the report here
but I'd like to keep it for later." The research report is kept in the
record as DETK-0060.

1. detk builds no augmentation command in 1.0. Option A's design stays
   above as a record of what was weighed.
2. The docs and the agent skill carry tested Miller recipes for a
   constant column, log with a base and a pseudocount, z-score (sample
   standard deviation, n-1), centring and min-max to [0, 1]. Each recipe
   carries the checks Miller lacks: a missing value in a source column,
   a value that is zero or negative where a log is taken (after the
   pseudocount), and zero variance or zero range each fail and name the
   samples. Each recipe is shown run through `detk-util record`. The
   names Option A item 5 recommended (`age_log2_pc1`, `age_zscore`)
   are the recipes' names, so no name carries `__` or reads as an R
   call. How the recipes are kept, checked and tested is DETK-0062.
3. `detk-util record` is part of the 1.0 CLI, under the promise of
   DETK-0025 like every other subcommand. Its open design details are
   DETK-0061.
4. The skill warns that tidyr's (and csvtk's) `gather` pivots to long
   format, the opposite of `detk-util gather`, which combines files
   into a wide matrix.
5. "No need for the report here but I'd like to keep it for later"
   answers the research session's offer to turn its report into a
   shareable page: the report is kept in the record instead (DETK-0060).
   Read as a report view for `detk-util record`, it matches the plan
   too: no view in 1.0 (DETK-0061 item 6).

## Consequences

- release/augment becomes release/record (`detk-util record`) and a
  new node, release/miller-recipes, carries the recipes, their docs,
  the skill entries and their tests.
- The formula error for a call in a formula (release/formula-rename)
  points to the derived-covariates recipes page rather than a detk
  command, and `docs/formulas.md` links it.
- Miller is not a dependency of detk. The recipe tests need `mlr` and
  are skipped where it is absent (DETK-0062).
- DETK-0050 item 3's "column data augmentation command" is met by the
  recipes run through `detk-util record`: the derived columns are added
  to a new column data file by a recorded step.
