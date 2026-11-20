---
kind: step
time: 2026-11-20T17:40:21Z
by: DETK/reviewer
node: release/r-design-names
step: s2
branch: review/r-design-names
verdict: changes
commits: []
decisions: []
---

# Changes asked: Review the PR: every R site covered, nothing in a column data file can run R code through the design, the R-gated tests in CI

## Summary

Changes asked: every R formula() site quoted and safe by construction, CI green incl. R job; but numeral-shaped column names (e.g. 2.5) reach R unquoted and are read as constants

## Artifacts

## Findings

Review of PR #97 at 477cfa9 (diff against origin/main).

Checked
- Every R formula() site on a detk design uses formula.r_design: detk-de deseq2 and firth (de.py), detk-transform rlog (transform.py; blind gives `~ 1`), norm deseq2_wrapr (norm.py). vst and estimateSizeFactors_wrapr hard-code `~ 1`; enrich passes no design. No other wrapr script reads a design.
- No code can run: r_design emits only syntactic names, backtick-quoted names (backticks and backslashes escaped), numerals, and the separators ` + `, `:`, `~`. A name holding `:`, `~` or ` + ` is split but every piece is still quoted or syntactic, and detk's parser rejects such names before they get here anyway. Safe by construction.
- params.design stays unquoted (r_design is only added under params.r_design / at the R call); results and matrix column names are unchanged.
- Tests: 34 pure-Python cases for r_name/r_design, a resolved-design test, and R-gated tests with a `file.create(1)` column (deseq2, firth, rlog, norm deseq2_wrapr: no file `1` is created) plus the `fld.cont` regression. CI green on 477cfa9, including test with R (bioconda): tests/de/test_r_design.py 40 passed, 0 skipped, so all R-gated tests ran. Locally (no R): 2025 passed, 82 skipped; ruff check and format clean.
- DESeq2 failing on a call-shaped name ("object 'file.create(1)' not found") is acceptable within the node. The objective is that no name runs as code, and that's met. Such a design already failed in R before this change (or ran the code), so no working analysis gets worse, and the CHANGELOG says so. Making non-syntactic names fit in DESeq2 would mean renaming in detk and mapping names back into the results. That is a new feature, not this fix, so no decision is needed here.

Change asked
1. Numeral-shaped column names are left unquoted. R_NUMERAL (`-?\d+(?:\.\d*)?`) leaves any numeral bare, but detk's parser accepts decimal-looking column names as columns. With a column named `2.5` (or `1.0`, `0.5`, `1.`, `10.25`), `counts ~ 2.5` resolves to `counts ~ Intercept + 2.5`, and `2.5 ~ counts + x` to `2.5 ~ Intercept + counts + x`. r_design passes both through as-is, so R reads the constant 2.5 (or 1.0 as the response) instead of the column. This runs no code, but it breaks the acceptance wording ("every name R would not read as a plain name ... is backtick-quoted"), and for firth (logistf keeps the names) quoting would let the column fit. Fix: leave unquoted only the intercept numerals detk emits (`1`, and `0`/`-1` if they can occur) and quote every other term through r_name. Add r_design cases (`counts ~ Intercept + 2.5` -> ``counts ~ Intercept + `2.5` ``, and `1.0` on the left side) and a resolved-design case built from a CountMatrix with a `2.5` column. An R-gated firth test with that column would be good too.

Not blocking (pre-existing, outside scope)
- detk's parser silently drops a column named `-2.5`: `counts ~ -2.5` resolves to `counts ~ Intercept`, and `-2.5 ~ counts + x` loses its left side. Integer names such as `3` are rejected, but decimals are taken as columns. These are inconsistent parser behaviors for a follow-up issue, not this node.
- norm deseq2_wrapr still runs `str(params$design)`, which only prints the string and is harmless.

## Questions
