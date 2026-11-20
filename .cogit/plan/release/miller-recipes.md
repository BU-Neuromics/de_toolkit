---
kind: task
objective: 'The docs and the agent skill carry tested Miller recipes for derived covariates (a constant column, log, z-score with n-1, centring, min-max), each with the checks Miller lacks and each run through detk-util record, so formulas stay model-only (DETK-0050, DETK-0051 Option C, DETK-0062)'
acceptance:
  - 'docs/recipes/covariates.md, in the nav and linked from docs/formulas.md, gives a recipe for each operation DETK-0062 lists, under the names it sets (<column>_log2, _log10, _ln, _log2_pc1, _zscore, _center, _minmax), each shown run through detk-util record with its output'
  - 'each recipe fails as DETK-0062 item 2 decides: a missing value, a value at or below zero after the pseudocount for a log, and zero variance or range for scaling each exit non-zero, name the samples on stderr and leave no output file; the page shows one such failure'
  - 'the page is an executable tutorial page (DETK-0064), so its commands are what CI runs; tests check the values against numpy (sample sd, n-1) and against R''s scale() in the R job, IDs as written (007 stays 007, DETK-0015), every failure case, and that detk-util record wrote a module JSON naming mlr and its version'
  - 'Miller is not a detk dependency: the tests skip with a reason where mlr is absent, and the R job installs miller from conda-forge so they run in CI on every PR'
  - 'skills/detk/references/covariates.md carries the recipes in short form, SKILL.md points to it, a test checks every recipe command in the skill appears on the docs page, and the skill warns that tidyr''s and csvtk''s gather pivots to long format, the opposite of detk-util gather (and that Miller''s long/wide verb is reshape)'
  - 'the formula error for a call in a formula (release/formula-rename) points to the recipes page; CHANGELOG'
from: [DETK-0050, DETK-0051, DETK-0062, DETK-0064]
scope: [new:docs/recipes/, new:tests/recipes/, docs/formulas.md, +mkdocs.yml, +.github/workflows/ci.yml, +skills/detk/SKILL.md, +de_toolkit/formula.py, +CHANGELOG]
prev: [DETK-0051, DETK-0062, DETK-0064, release/record, release/tutorial-harness, release/formula-rename]
issue: 115
visited: 118283e
---

# Miller recipes for derived covariates

## Implementation plan

- [x] @developer Write the recipes page as an executable tutorial page with each recipe and a failure, the numpy and R checks, the skill reference with its consistency test and the gather warning, Miller in the R job, the formula error's pointer and docs/formulas.md's link; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review each recipe's arithmetic (n-1, pseudocount, base) and its failures against DETK-0062, run the page with and without mlr, and read the skill from an agent's side <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 on Adam's answer to DETK-0051 ("go with c"), replacing
the operations of release/augment. DETK-0060 holds the research behind it,
including the Miller behaviours the checks guard against (`log(0)` gives
`-Inf`, a missing value an empty result, both silently). The failing form
(`asserting_null` in the end block, `emit > "file"`) was checked on Miller
6.22 by the planning session. New files go under `docs/recipes/` and
`skills/detk/references/`.
