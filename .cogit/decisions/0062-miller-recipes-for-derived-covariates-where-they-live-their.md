---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release}
applies: [release/miller-recipes]
revisions:
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's delegation via the driver session, 2026-11-20: accepted on the planning session's recommendation (the first option of each item); within the scope Adam set and no change to the 1.0 promise"}
---

# Miller recipes for derived covariates: where they live, their checks and their tests

- Proposed by: the planning session, 2026-11-20, for the details of
  DETK-0051 item 2. Within the 1.0 definition of done and the scope Adam
  set, so it may be accepted under his delegation (DETK-0063).

## Background

DETK-0051 (Option C, Adam, 2026-11-20) puts derived covariates in
tested Miller (`mlr`) recipes in detk's docs and agent skill, each with
the checks Miller lacks, each run through `detk-util record`. DETK-0060
found that Miller writes `-Inf` for `log(0)` and an empty value for a
missing input, both silently, and that its `stddev` uses n-1. This
record settles where the recipes live, how the checks are written, the
column names, and how they are tested.

## Context

- The docs are a mkdocs site (DETK-0004); the agent skill is
  `skills/detk/` with `references/commands.md`, kept in step with the
  CLI by DETK-0010's test.
- Tutorials are planned as executable Markdown pages run by pytest
  (DETK-0064, Proposed).
- CI has uv-based test jobs and one job with R from bioconda through
  micromamba (conda-forge and bioconda channels).
- Miller is on conda-forge (`miller`), Homebrew and as a static binary;
  Ubuntu's apt package lags.

## Options

Each item is a separate choice; the recommendation first.

### 1. Where the recipes live

**Recommended:** one docs page, `docs/recipes/covariates.md` ("Derived
covariates with Miller"), in the nav after "Design formulas", which
links to it. It is an executable page under DETK-0064's harness, so the
commands on the page are the commands tested. The skill gets
`skills/detk/references/covariates.md` with the same recipes in short
form and a pointer from `SKILL.md`; a test checks that every recipe
command in the skill also appears on the docs page.

Alternative: shipped shell scripts (`detk-recipes log ...`). That is
a command in all but name, and DETK-0051 chose not to build one.

### 2. How a recipe carries its checks

**Recommended:** each recipe is one `mlr ... put -q` command that
checks first and computes second. Each record is kept in a map and its
sample name is noted if the source value is missing (or, for a log, at
or below zero after the pseudocount). In the `end` block, if any were
noted, it prints them to stderr and fails through a Miller type
assertion (`asserting_null("fail")`), which exits 1; otherwise it
computes the new column and writes every record with
`emit > "out.csv", v`. Writing from the expression rather than through
a shell redirect means a failed recipe leaves no output file at all.
The planning session checked this form on Miller 6.22 (a log recipe on
a sheet with a 0 and an empty value: exit 1, both samples named, no
file; on a clean sheet: exit 0, IDs such as `007` kept). Run through
record it reads
`detk-util record -i sample_info.csv -o sample_info.aug.csv -- mlr --icsv --ocsv put -q '...' sample_info.csv`.
The tests prove each failure is non-zero, names the samples and leaves
no output.

Alternative: a separate check command before the compute command (two
recorded steps for one column; clutter in the crate).

### 3. Names and the operations covered

**Recommended:** the names of DETK-0051 Option A item 5:
`<column>_log2`, `_log10`, `_ln`, `_log2_pc1` with a pseudocount,
`_zscore`, `_center`, `_minmax`, and a constant column under the name
the user picks. A single underscore, never `__`. Recipes: a constant
column; log (base 2, 10 and e; with and without a pseudocount); z-score
with n-1; centring; min-max to [0, 1]; z-score and min-max fail on
zero variance or zero range. Each shows its output on the airway
`sample_info.csv` (or a small sheet on the page) and the failure on a
bad value.

### 4. Tests and CI

**Recommended:** Miller is not a dependency of detk. The recipe tests
(the executable page, plus checks against numpy and R's `scale()`
where R is there) need `mlr` and are skipped when it is absent, with
the reason given. CI installs `miller` from conda-forge in the R job's
micromamba environment, so the recipes run in CI on every PR. The
tests check: values against numpy (n-1 for the z-score), IDs as
written (`007` stays `007`, DETK-0015), each failure (non-zero exit,
the sample names on stderr, no output), and that `detk-util record`
wrote a module JSON naming `mlr` and its version.

Alternative: install Miller in every test job (more CI time for little
gain).

### 5. The tidyr `gather` warning

**Recommended:** the skill's covariates reference and `SKILL.md` say
that tidyr's and csvtk's `gather` pivots a table to long format, the
opposite of `detk-util gather`, which combines quantifier files into a
wide matrix; and that Miller's own long/wide verb is `reshape`.

## Decision

Proposed. The planning session recommends the first option of each
item and that it be accepted under Adam's delegation (DETK-0063).

## Consequences

release/miller-recipes builds the page, the skill reference and its
consistency test, the Miller install in the R job, and the tests. The
formula error (release/formula-rename) and `docs/formulas.md` point to
the page.
