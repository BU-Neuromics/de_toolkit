---
kind: step
time: 2026-11-20T18:25:36Z
by: DETK/reviewer
node: release/r-design-names
step: s2
branch: review/r-design-names
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: every R site covered, nothing in a column data file can run R code through the design, the R-gated tests in CI

## Summary

Approved: only detk's intercept 1 stays bare, number-shaped names quoted with tests incl. R-gated firth fit; CI green incl. R job at 70f01f1

## Artifacts

## Findings

Second review of PR #97 at 70f01f1 (fix in 0e58a23).

- The change I asked for is addressed. r_design now leaves only the intercept `1` bare (R_INTERCEPT), which is the only numeral detk writes in a resolved design. Probed: `counts ~ 0` and `counts ~ -1` both resolve to `counts ~ 1`, and a column named `1` resolves to Intercept. Every other term, number-shaped ones included, goes through r_name, so `2.5`, `1.0`, `0.5`, `1.` and `10.25` are quoted on either side of `~` and inside interactions. The output is still built only from safe tokens, so nothing can run.
- New tests: r_design cases for `2.5` on the right, `1.0` on the left, several decimals and an interaction; a resolved-design test from a CountMatrix with `2.5` and `1.0` columns; and an R-gated firth fit of `2.5 ~ counts` (20 rows, all status OK). The docstring and comments are updated. The CHANGELOG wording ("every name ... not a syntactic R name") already covers it.
- Earlier findings still hold: every R formula() site is covered, params.design stays unquoted, results are unchanged, and DESeq2's error on call-shaped names is acceptable within the node.
- Locally (no R): 2030 passed, 83 skipped; ruff check and format clean. CI on 70f01f1 all green, including test with R (bioconda): 2091 passed, 22 skipped; tests/de/test_r_design.py 46 passed, 0 skipped, so every R-gated test ran, the new firth fit included.
- Still outside scope, for a follow-up: the parser silently drops a column named `-2.5`, and it rejects integer column names but takes decimals.

## Questions
