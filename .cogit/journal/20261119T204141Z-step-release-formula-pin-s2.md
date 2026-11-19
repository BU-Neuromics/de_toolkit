---
kind: step
time: 2026-11-19T20:41:41Z
by: DETK/reviewer
node: release/formula-pin
step: s2
branch: review/formula-pin
verdict: approve
commits: []
decisions: []
---

# Approved: PR #72 pins the formula matrices patsy-lite builds today

## Summary

Approved. The acceptance is met: every docs/formulas.md formula and every
design in tests/de/test_de.py has a literal full-matrix pin (names, order,
values, row order, float64), the listed term types and quoting cases are
covered, the error cases are pinned by exception and message substance,
np.log is pinned as it fails and raised in DETK-0040, and nothing imports
patsy. No change to de_toolkit/.

## Artifacts

- PR #72 reviewed at 5acfdde

## Findings

- Checks: `uv run pytest tests/patsy_lite` 73 passed; full suite 436 passed,
  62 skipped (R not installed here); ruff check/format clean. CI green on
  3.11/3.12/3.13, ruff, docs, CodeQL; "test with R (bioconda)" still running
  at review time. The PR adds no R-gated test (the detk-de exit cases fail
  before R is needed and passed here without R).
- Coverage, checked against the sources: the docs examples (cat_var[A,B,C],
  height, disease_status, gdp, the DESeq2 and Firth designs) and all nine
  test_de.py designs have a case; `category ~ cont_cov` (add_design) is
  covered as the counts-required error. The patsy C() form from the docs is
  pinned as a lex error, which is right: it is shown for comparison only.
- Independent of patsy: pins are literal CSVs, never regenerated, and
  test_every_pin_has_a_case keeps pins and cases in step. Spot-checked by
  hand: interaction_star, quote_interaction_star, integer_levels,
  boolean, docs_gdp, multinomial_unobserved_level, interaction_colon.
  Column data files use shuffled sample ids, so row order is really tested.
- Nit (non-blocking): `assert_frame_equal(..., check_names=False)` also
  skips the index name, so the first-column name of the column data file
  ("sample") is not pinned. Row labels are pinned by the explicit index
  assertion. Can be tightened in the migration PR if wanted.
- Note for the migration: a*b pins the column order patsy-lite gives today
  (alphabetical, not term order, e.g. binary_str__control:cat_str__B
  before cat_str__B). A port that keeps formula order will fail those pins
  on purpose; whether that order is part of the promise belongs with DETK-0040.

## Questions

None for this review. DETK-0040 (Proposed) waits on Adam; not decided here.
