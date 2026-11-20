---
template: adr
state: Accepted
authority: [human]
date: 2026-11-20
from: {node: release/formula-migrate, step: s1}
applies: [release/formula-migrate]
allowed_by: [reasonable]
revisions:
  - {date: 2026-11-20, by: DETK/developer, change: "Proposed for the driver/Adam: an error pin DETK-0040 does not list changes", why: "the node's acceptance lists the pins that may change; this one is not listed, so it is not the developer's to settle"}
  - {date: 2026-11-20, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A, under Adam's delegation via the driver session, 2026-11-20: within the formula migration's scope, no change to the 1.0 promise"}
---

# An a:b of names that need quoting builds its interaction instead of failing

## Background

detk's design formulas ("patsy-lite", `docs/formulas.md`) name columns
of the column data file. A name containing `.`, `(`, `)` and a few other
characters is quoted before the formula goes to the formula library
(patsy's `Q("...")` before, formulaic's backticks now). release/formula-pin
pinned, as an error, the case `quote_interaction_colon`:
`fld.cont ~ fld.cat:age(yrs)`, an interaction of two such names.

## Context

- Today (patsy): the lexer read `fld.cat:age(yrs)` as one name, because
  `:` was allowed inside a name, and quoted it whole as
  `Q("fld.cat:age(yrs)")`, a column that does not exist. The design
  failed with "Misspecified column" naming `fld.cat:age(yrs)`.
- DETK-0040 (accepted, Option B) has release/formula-migrate make `a:b`
  of categorical terms give its interaction columns and accept a
  reference level inside it (`binary_str[control]:cat_str`, which did
  not lex). Its acceptance names the pins that change for that:
  `interaction_colon`, `interaction_colon_ref` and the boolean-reference
  errors. It does not name `quote_interaction_colon`.
- The natural fix for `a[ref]:b` is to lex `:` as an operator, so each
  side is a term of its own. That also fixes `quote_interaction_colon`:
  each name is quoted separately (`` `fld.cat` : `age(yrs)` ``) and the
  design builds `Intercept, fld.cat__A:age(yrs), fld.cat__B:age(yrs),
  fld.cat__C:age(yrs)`, the same values patsy gives for
  `Q("fld.cat"):Q("age(yrs)")` (checked).
- The node's acceptance says any other matrix or column name that has to
  change is a question for Adam first. No matrix or column name changes
  here: a formula that was an error now builds. But an error pin changes
  that DETK-0040 does not list, so it is recorded.
- Criteria: no silent wrong models; no special cases that make the
  formula language irregular; the 1.0 promise (DETK-0001) and the docs
  agree.

## Options

### A. Let it build; change the pin to a matrix pin (recommended)

`a:b` works the same whatever the names are. No extra code. The pin
becomes a matrix pin checked against patsy's values. The CHANGELOG lists
it with the DETK-0040 fixes. Same root cause as `interaction_colon_ref`
(`:` was part of a name).

### B. Keep it an error

Would need code that refuses `:` between two quoted names, while
accepting it between plain names, to reproduce a failure nobody chose.
Leaves an irregular rule in the 1.0 formula promise.

## Decision

Proposed: A. It is the same defect DETK-0040 fixes (`:` read as part of
a name), it changes no existing matrix or column name, and keeping the
error would take code written only to fail. Implemented that way in the
PR for #78, so the pin can be reverted to the error if B is chosen.

## Consequences

- Under A: `tests/patsy_lite/pins/quote_interaction_colon.csv` replaces the
  error case; the CHANGELOG's Fixed entry for DETK-0040 names it.
- Under B: the PR adds a check that raises PatsyLiteParseError for a `:`
  between two names that need quoting and restores the error pin.
