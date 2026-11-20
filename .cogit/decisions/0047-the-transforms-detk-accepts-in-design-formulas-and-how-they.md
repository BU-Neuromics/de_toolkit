---
template: adr
state: Superseded
superseded_by: DETK-0050
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/record]
revisions:
  - {date: 2026-11-19, by: adamlabadorf, change: Superseded by DETK-0050, why: "from the terminal: Adam changed his mind on 2026-11-19: formulas specify the model only; derived columns come from a column data augmentation command (DETK-0051)"}
---

# The transforms detk accepts in design formulas, and how they are named and recorded

- Proposed by: the planning session, 2026-11-19, to fill in what Adam's
  answer to DETK-0028 left open

## Background

Adam chose DETK-0028 Option B: "Support a small whitelist (log, log2,
etc.) in 1.0 and record it in provenance." A design such as
`counts ~ log2(age) + condition[control]` will work in 1.0, where today
any such term fails. He did not say which transforms are in the set, how
the transformed column is named in the model matrix and the results, what
happens with values a transform cannot take, or how the transform is
recorded. Whatever 1.0 ships here is promised until 2.0 (DETK-0001), so
each of these is his to settle. This record proposes concrete answers.

## Context

### How a design travels through detk today

- The formula module (`patsy_lite.py`, to be `formula.py` under DETK-0027)
  parses the design, builds the model matrix, and renames its columns to
  detk's names: a scalar keeps its column name, a category level becomes
  `<variable>__<level>`.
- The **resolved design**, the matrix's column names joined with ` + `
  (`DesignMatrix.design`), is what the R-backed commands receive. DESeq2
  and logistf call R's `formula()` on that string over the matrix written
  as a CSV (`de.py` lines 280-292 and 472-488). The results are named
  `<matrix column>__<statistic>` (the skill: `condition__treated__log2FoldChange`).
- The resolved design is also what the module JSON records as
  `params.design` (`de.py`, `norm.py`, `transform.py`). The Process Run
  Crate turns each `params` key into one `PropertyValue` (`crate.py`
  lines 161-175). The design as the user wrote it is only in the module
  JSON's `argv`, which the crate does not carry.

### What this means for transforms

- **Names reach R unquoted.** A transformed column named `log2(age)`
  would be read by R's `formula()` as a call to `log2` on a column `age`
  that the matrix does not have. Any name in the resolved design has to be
  one R reads as a plain name.
- **R evaluates calls in a formula.** `formula("counts ~ f(x)")` calls
  `f` when the model frame is built. Today a column data column whose
  name looks like a call (the lexer accepts `(`, `)`, `.` and `:` in
  names) reaches R in exactly that form. No working analysis depends on
  that: such a design fails in R. It is a way for a column data file to
  run R code through detk, and the transform work touches the same path.
- **formulaic evaluates Python** in formula terms (DETK-0028 Context).
  DETK-0028 Option B already fixes that detk computes the transformed
  columns itself in pandas, so formulaic only ever sees column names.
- **Name clashes.** The `__` separator means "variable, then level" in
  matrix and result names. A transform name built with `__`
  (`log2__age`) would read as level `age` of a variable `log2`, and its
  results as `log2__age__log2FoldChange`.
- **A column may already be called `log2(x)`.** Today such a column works
  (the lexer quotes it for patsy) as long as no R-backed command sees it.
  `release/formula-pin` pins today's behaviour, so the rule chosen here
  shows up as a deliberate edit to its pins.
- **Undefined values.** log of 0 is -inf and of a negative is NaN.
  Passed on silently, DESeq2 and logistf fail with messages that do not
  name the cause, or patsy and formulaic drop the sample.
- Criteria: what agents and analysts actually need in a DE design;
  explainable in one docs table; safe (no code from a formula is run);
  the same result in Python and R; small enough to promise.

## Options

Each item below is a separate choice. The planning session's
recommendation is given first; the alternatives follow it.

### 1. The set

**Recommended:** `log(x)` (natural), `log2(x)`, `log10(x)`, `log1p(x)`
(natural log of 1 + x), `sqrt(x)`, `center(x)` (subtract the mean) and
`scale(x)` (subtract the mean, divide by the sample standard deviation,
as R's `scale()` does). These cover the common covariate transforms in
DE designs: log library size or concentration, and centred or scaled
age, which DESeq2 recommends for numeric covariates on large scales.

Alternatives: (a) the logs only (`log`, `log2`, `log10`, `log1p`), the
narrowest reading of "log, log2, etc."; (b) the recommended set plus
`exp` and `square`, which are rarely needed in DE designs.

### 2. Arguments and nesting

**Recommended:** each transform takes exactly one column name. No second
argument (R's `log(x, 2)` means base 2, numpy's does not exist), no
arithmetic inside the parentheses (`log2(x + 1)`), and no nesting
(`log2(scale(x))`). A pseudocount other than 1 means adding a column to
the column data file. Anything else in parentheses is an error naming
the allowed forms.

Alternative: allow `log2(x + c)` with a numeric constant `c`, as a
pseudocount. One more form to parse, document and pin.

### 3. Values a transform cannot take

**Recommended:** detk checks before building the matrix. Any value of 0
or below for `log`, `log2` and `log10`; any value of -1 or below for
`log1p`; any negative value for `sqrt`; and a column with zero variance
for `scale` is an error that names the column, the transform and the
offending samples, and suggests `log1p` or a column in the column data
file. A missing value in a transformed column is an error too, naming
the samples: no sample is dropped silently. These exit 1 (DETK-0031: not
a usage error).

Alternative: warn and let the engine drop the samples (patsy's and
formulaic's default for missing values). Fewer errors, but results then
silently rest on fewer samples.

### 4. Which columns and which sides

**Recommended:** a transform applies only to a numeric column data
column, on the right-hand side. `log2(counts)`, a transform of a
categorical column, a transform with a level (`log2(x)[a]`) and a
transform on the left-hand side are errors. A transformed column may take
part in an interaction (`log2(age):condition`), since it is a column like
any other.

### 5. Names in the matrix, the results and R

**Recommended:** the transformed column is named `<transform>_<column>`:
`log2_age`, with results `log2_age__log2FoldChange` and so on. A single
underscore keeps `__` meaning "level". If the column data already has a
column of that name, the design is an error naming both. Separately, every
name in the resolved design that is not a syntactic R name is
backtick-quoted before it reaches R's `formula()`, so a column data
column whose name looks like a call is read as a name, never run.

Alternatives: (a) `log2__age`, as DETK-0028's sketch had it, read as a
level by anyone who knows the convention; (b) keep `log2(age)` as the
column name and backtick-quote it for R: closest to what the user wrote,
but not a name pandas, R or a shell handles without quoting.

### 6. A column literally named like a transform

**Recommended:** an exact column name wins. If the column data has a
column called `log2(x)`, the term is that column, as today, and detk logs
that it did not apply a transform. Otherwise the whitelist applies.

Alternative: refuse the ambiguity, asking the user to rename the column.
Clearer, but it breaks a column name that works today.

### 7. Provenance

**Recommended:** every module that records `params.design` also records
`params.formula`, the design exactly as written, and, when the design
has transforms, `params.transforms`, an object from each transformed
column's name to what produced it:
`{"log2_age": {"transform": "log2", "column": "age"}}`. Both are new keys
in `params`, which the module schema leaves open, so the schema stays at
1.0. In the Process Run Crate, each transform becomes its own
`PropertyValue` (`detk-de deseq2 transform log2_age`, value `log2(age)`)
rather than one JSON string, so the crate reads without decoding.

Alternative: only `params.formula`, leaving the transforms to be read
from it. Less to build, but a reader of the crate then has to know detk's
formula syntax.

## Decision

Open for Adam. The planning session recommends the first option of each
item above. Until he answers, `release/formula-transforms` waits.

## Consequences

`release/formula-transforms` implements the answer after
`release/formula-rename`: the transforms in the formula module, the
checks, the names, the R quoting, the provenance keys and the crate
entities, with tests, `docs/formulas.md` (one table of the transforms and
their rules) and the skill's formula section. A transform added later is
a 1.x minor release; removing one waits for 2.0.
