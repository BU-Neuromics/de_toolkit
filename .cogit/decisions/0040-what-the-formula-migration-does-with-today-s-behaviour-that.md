---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release/formula-pin, step: s1}
applies: [release/formula-migrate]
---

# What the formula migration does with today's behaviour that differs from docs/formulas.md

- Proposed by: the @developer session on release/formula-pin s1
  (#71), 2026-11-19, from what the pins found.

## Background

release/formula-pin pins, in `tests/patsy_lite/test_formula_pins.py`,
the model matrices patsy-lite builds today on patsy, so that the
formulaic port (release/formula-migrate, DETK-0024) can be checked
against them. Writing the pins showed four places where today's
behaviour is not what `docs/formulas.md` says. The pins record them as
they are. The migration has to either reproduce each one or change it
and its pin, and that is a choice about the 1.0 formula promise
(DETK-0001, DETK-0025), so it is Adam's.

## Context

What the pins found (the case names are in the test module):

1. **`a:b` of two categorical terms loses its columns**
   (`interaction_colon`). The docs' own example,
   `cont ~ binary_str:cat_str`, gives `cont ~ Intercept`: no
   interaction columns, no error. patsy builds them; patsy-lite then
   drops them when it puts the columns back in formula order, because
   it matches column names by prefix against the term name
   (`binary_str:cat_str`) and patsy's names
   (`binary_str[case]:cat_str[A]`) do not start with it. `a*b` works
   (`interaction_star`), and so does `a:b` of two scalars
   (`interaction_colon_scalar`). A reference level inside `a:b`
   (`binary_str[control]:cat_str`) does not lex at all. The DETK-0024
   study and DETK-0028 say interactions work; for `a:b` alone they do
   not. A user fitting `counts ~ a:b` today gets an intercept-only
   model silently.
2. **`np.log(x)` fails** (`np_log_rhs`, `np_log_lhs`): already
   DETK-0024 and DETK-0028; pinned as an error naming
   `np.log(cont)`.
3. **A boolean column's reference cannot be named**
   (`boolean_ref_upper`, `boolean_ref_python`). A TRUE/FALSE column
   reads as bool and becomes `flag__True` with False the reference
   (`boolean`), but `flag[FALSE]`, `flag[False]` and `flag[True]` all
   fail with "level not found": the level is passed as the string, not
   the bool.
4. **Two docs examples do not come out as shown.**
   `disease_status[control] ~ age_at_death + batch + counts` shows
   `batch__2 + batch__3`, but an integer batch column is scalar and
   gives `batch` (`docs_disease_status`); the docs would need
   `batch[1]`. The `continent[NoAm]` example lists the levels as
   `SoAm, Asia, Aust, Euro, SoPo`; they come out sorted, `Asia, Aust,
   Euro, SoAm, SoPo` (`docs_gdp`).

Also pinned, and probably intended, but worth knowing: a level list
naming a level absent from the data (`cat_str[A,B,C,D]`, as the docs
write it) gives a column of zeros (`multinomial_unobserved_level`);
the `a*b` columns come grouped by their first factor
(`binary_str__control, binary_str__control:cat_str__B, ..., cat_str__B,
cat_str__C`), not patsy's order.

Criteria: no silent wrong models in the 1.0 promise; the migration
stays checkable against the pins; the docs match the behaviour.

## Options

- **A. Port the behaviour exactly, quirks included.** formulaic is made
  to give the pinned matrices, `a:b` losing its columns too; the docs
  are changed to say what happens. Easiest to check (every pin holds
  unchanged), but it carries a silent wrong model into 1.0.
- **B. Port, and fix the four in the migration, each with its pin.**
  release/formula-migrate makes `a:b` give its interaction columns
  (and accept a reference inside it), accepts a bool reference
  (`flag[FALSE]`), and changes the `interaction_colon` pin and the
  boolean error pins in the same PR, named in its description; the
  docs examples are corrected in release/formula-rename or cli-docs.
  np.log follows DETK-0028. Every other pin holds unchanged, so the
  port is still checked. Recommended.
- **C. Fix `a:b` now, on patsy, in its own node before the migration.**
  Smallest diff per change and the fix ships even if the migration
  slips, but it is work on the code the migration replaces.

## Decision

Waiting on Adam. Recommended: **B** — the `a:b` loss is a silent wrong
model that 1.0 should not promise, and fixing it inside the port keeps
one place where the matrices change, with every other pin still
holding.

## Consequences

- Under B, release/formula-migrate's acceptance gains: `a:b` of
  categorical terms gives its interaction columns; a bool reference
  can be named; the `interaction_colon` and boolean error pins change
  in that PR and no other pin does. The docs example fixes go to the
  docs node.
- Under A, the docs must describe the `a:b` behaviour, and a later fix
  changes the 1.0 promise.
- Revisit if formulaic cannot reproduce the other pins without
  special-casing.
