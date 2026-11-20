---
template: adr
state: Proposed
authority: [human]
date: 2026-11-20
applies: [release/parse-errors]
issue: 108
---

# Column names that look like numbers in design formulas

## Background

Design formulas (`counts ~ condition`, DETK-0050) name columns of the
column data file. A column can have a name that looks like a number:
`3`, `2.5` or `-2.5`, for instance a time point or a dose written as a
header. Since the move from patsy to formulaic (release/formula-migrate)
detk reads such names inconsistently, and in two cases silently drops the
term. Once 1.0 is tagged the formula language is part of the promise
(DETK-0001), so what a number-like token means must be settled now.

## Context

What the formula module does today (checked on main at f3a014f with a
column data frame holding columns `-2.5`, `2.5`, `3` and `c`):

- `counts ~ -2.5` gives the right side `Intercept` only: the `-` is read
  as formula term removal and `2.5` as a number, so the column is dropped
  with no message.
- `-2.5 ~ c` gives an empty left side: the outcome is lost with no message.
- `counts ~ 2.5` uses the column `2.5` (the lexer's name pattern takes
  `2.5`, and `quote_var` backticks it because of the dot).
- `counts ~ 3` is an error: formulaic reads `3` as a numeric literal
  ("Numeric literals other than `1` can only be used to scale other
  terms"), shown as raw tuple text.
- Under patsy (0.x) a number-like token was a Python literal, never a
  column, so none of these were columns before 1.0's migration.
- `0` and `1` have a meaning in formulas (`~ 0 + x`, `~ 1`): the
  intercept. Any rule must keep that.
- Criteria: never silent (a term is used or the run stops with a message
  naming it); consistent across whole numbers, decimals and negatives and
  on both sides of `~`; no ambiguity with the `-` operator and the
  intercept numbers; the least new syntax to promise in 1.0.

## Options

### Option A: number-like names are not column names; using one is an error

A term that looks like a number, other than the intercept numbers `0`
and `1`, is a usage error (exit 2) on either side of `~`. When the column
data has a column by that name (`-2.5`, `2.5`, `3`) the message says the
column's name looks like a number and must be renamed to start with a
letter or underscore (for instance with Miller's `rename` verb, see the
recipes of release/miller-recipes show); otherwise it says formulas take
column names, not numbers. A `-` followed by a number that names a
column is caught the same way, so `counts ~ -2.5` stops instead of
dropping the term.

- Never silent: yes. Consistent: one rule for `3`, `2.5` and `-2.5`, both
  sides. No ambiguity: numbers keep their formula meaning. No new syntax.
- Cost: `counts ~ 2.5`, which works on main today (never in a release),
  stops working; users rename such columns, a one-line Miller step.

### Option B: a number-like token names a column when one exists

If the column data has a column whose name is the token, use it as a
column (`3`, `2.5`, and `-2.5` as one name); otherwise read it as a
number, and any number other than `0`/`1` is an error.

- Never silent only if the lexer resolves `-2.5` against the columns
  first; the meaning of `x - 1` or `~ 0 + x` then depends on whether a
  column named `1` or `0` exists, which makes a formula's meaning depend
  on the data. Consistent, but with an ambiguity the 1.0 promise would
  carry.
- No new syntax, but the rule needs documenting with its exceptions.

### Option C: an explicit quoting syntax for any name (backticks)

`` counts ~ `-2.5` `` names the column; an unquoted number-like token is
a number, and anything other than `0`/`1` is an error that suggests the
quoted form.

- Never silent and unambiguous. Adds a quoting syntax to the 1.0 formula
  language (docs, the skill, R-bound quoting of release/r-design-names
  must agree with it), and shell quoting of backticks is awkward on the
  command line.

## Decision

Recommended: Option A. It is the only option that is never silent,
unambiguous and adds nothing to the 1.0 formula language; it matches what
0.x did (a number was never a column), and a number-like header is rare
and fixed by one rename. Option C can be added after 1.0 without breaking
anything if a need appears.

## Consequences

release/parse-errors implements the rule in the formula module, with
tests for `3`, `2.5` and `-2.5` on each side of `~` (with and without a
column of that name) and for `0`/`1` keeping their intercept meaning;
docs/formulas.md states that column names in formulas start with a
letter or underscore; the CHANGELOG notes that `counts ~ 2.5` is no
longer read as a column. Revisit if users report number-like headers
they cannot rename.
