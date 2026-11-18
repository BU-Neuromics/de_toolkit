---
template: adr
state: Proposed
authority: [human]
date: 2026-11-18
from: {node: release}
applies: [release]
---

# The formula library that replaces patsy

- Proposed by: the planning session for DETK-0001 Option B, 2026-11-18;
  Adam has not confirmed formulaic

## Background

Adam chose Option B of DETK-0001 (#18): replace docopt-ng and patsy
before 1.0 is tagged. detk's design formulas (`docs/formulas.md`) are a
"patsy-lite" syntax: `de_toolkit/patsy_lite.py` lexes them with ply,
translates `cat[A,B,C]` and `cat[ref]` into patsy terms (`C(...)`,
`Treatment(...)`, `Q("...")` for awkward names), lets patsy build the
full-rank model matrix, and renames its columns to `variable__level`.
DETK-0001 named formulaic as patsy's successor; Adam has not confirmed it.
The formula migration node under `release` waits on this record.

## Context

- The formulas and the design-matrix column names are part of the CLI
  promise: they are given as command-line arguments and the column names
  reach the R scripts and the DE outputs (`detk-de deseq2`, `firth`).
  `docs/formulas.md` also promises pass-through of other patsy terms
  (interactions `a:b`, `np.log(x)`) "at your own risk".
- statsmodels 0.14, a detk dependency, itself requires patsy, so patsy
  stays installed whatever detk chooses; the migration removes detk's own
  use of it and its direct pin, not the package from environments.
- `patsy_lite.py` is 98% covered; `release/formula-pin` adds tests that
  pin the matrices and column names for the documented formulas before
  the backend changes.
- Criteria: the same matrices and column names for the documented syntax;
  maintenance after 1.0; dependencies added; how much of the pass-through
  behaviour survives.

## Options

### Option A: formulaic

The maintained successor to patsy, with the same formula language in most
respects (`C()`, treatment contrasts, `:` and `*`, Python transforms).
Differences to absorb (to be confirmed in the node): how awkward names are
quoted (`Q("...")` today), and default column names and level orderings,
which the `__` renaming and the pin tests have to cover. One new
dependency.

### Option B: no formula library

Build the model matrix in detk from the parsed patsy-lite terms with
pandas (dummy encoding with the given reference or level order, numeric
pass-through). No dependency, full control of names and ordering; drops
the patsy pass-through terms (or detk has to implement interactions
itself), which is a change to documented behaviour.

### Option C: something else

Another formula library, if Adam has one in mind.

## Decision

Open for Adam. No option is recommended by the planning session.

## Consequences

`release/formula-migrate` carries out the choice and updates
`docs/formulas.md` (it names patsy as "the brain" today). Under B the
pass-through terms are removed or reimplemented and the CHANGELOG says
which.
