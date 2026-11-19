---
template: adr
state: Proposed
authority: [human]
date: 2026-11-19
from: {node: release}
applies: [release/formula-rename]
---

# The name of the module that replaces patsy_lite.py

- Proposed by: the planning session, 2026-11-19; Adam asked for the
  rename but gave no name

## Background

With DETK-0024 accepted, `de_toolkit/patsy_lite.py` no longer uses
patsy, and Adam said "we need to rename patsy_lite.py to something
else". The module parses detk's design formulas
(`cont ~ cat_var[A,B,C]`) and builds the model matrix (`DesignMatrix`).

## Context

- The Python API is not part of the 1.0 promise (DETK-0001), so the
  rename breaks no promise. The CLI is unaffected except for one
  user-visible error text: "Invalid design, patsy lite could not parse
  ..." (`common.py` line 229).
- The rename goes beyond the file. It covers the exception
  `PatsyLiteParseError`, `patsy_lite_to_patsy`, `tests/patsy_lite/`, and
  the docs, which call the syntax "patsy-lite" (`docs/formulas.md` and
  three CHANGELOG entries).
- Users meet the word "design": the CLI argument is `<design>`, the class
  is `DesignMatrix`, and the docs page is "Design formulas".
- Criteria: says what it is; matches the words users see; no clash with
  `formulaic`.

## Options

### Option A: `de_toolkit/formula.py` (recommended)

Short. It matches the docs page (`docs/formulas.md`) and how the docs
talk about the syntax ("design formulas"). The exception becomes
`FormulaParseError`, and the syntax is called "detk formula syntax" in
the docs.

### Option B: `de_toolkit/design.py`

Matches the `<design>` argument and `DesignMatrix`. "design" is broader
than the parser, though: it could equally name the experiment design or
the column data.

### Option C: `de_toolkit/design_formula.py`

The most explicit name, and the longest.

## Decision

Open for Adam. The planning session recommends Option A,
`de_toolkit/formula.py`.

## Consequences

`release/formula-rename` renames the module, the exception, the
translation function and the test directory. It updates the error text
and the docs. `PatsyLiteParseError` is kept as an alias for one
release, or dropped; the Python API is not promised, so the planning
session suggests dropping it, but Adam may say otherwise.
