---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-1}
applies: [release-1-1/preflight]
issue: 173
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's decision via the driver session, 2026-11-27 (\"Yes, accept all recommendations\"): Option B, a detk-util preflight subcommand in de_toolkit/preflight.py"}
---

# Where the JSON preflight lives

- Proposed by: the plan session, 2026-11-27, for the driver to confirm

## Background

1.1 adds a JSON preflight (Adam's direction, 2026-11-27): before a fit,
report sample agreement, the design's rank, size-factor feasibility, count
validity and the R packages the method needs, with a plain-language fix
each. `detk-wrapr check` today checks R and jsonlite only; #164
(`features/wrapr-check-options`) makes it method-aware.

## Context

- The checks are mostly about data (counts, sample sheet, design), with one
  about the environment (R packages).
- A new command or subcommand is additive under DETK-0001; an agent needs
  one obvious place to call, with the same arguments as the step it
  precedes.

## Options

**A. Grow `detk-wrapr check`** with `<design> <counts_fn> <cov_fn>`,
`--method` and `--json`. One command, but wrapr is the R bridge, and the
data checks have nothing to do with R.

**B. `detk-util preflight`** (recommended), in a new module
de_toolkit/preflight.py: takes the same `<design> <counts_fn> <cov_fn>` as
`detk-de` plus `--method deseq2|firth` and prints JSON (versioned like the
module JSON); calls the method-aware wrapr check for the R half. util
already holds the input-preparation commands (tidy, gather, annotate).

**C. A `--preflight` option on each fitting command** (`detk-de deseq2
--preflight ...`): checks and exits without fitting. Closest to the step,
but adds an option to many commands and their help.

## Decision

Recommended: **B**, for the driver to confirm.

## Consequences

`release-1-1/preflight` waits on this record; its scope assumes B.
