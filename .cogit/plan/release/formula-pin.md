---
kind: task
objective: 'Tests pin the model matrices and column names patsy-lite builds today, before patsy is replaced (DETK-0001)'
acceptance:
  - 'for every formula in docs/formulas.md and every design used by the de tests, a fixture pins the full model matrix (column names and order, values, row order) and its left- and right-hand side names'
  - 'scalar, binary, multinomial (with and without level order and reference), integer-coded categories, counts, interactions (a:b, a*b) and boolean columns (TRUE/FALSE in the column data file) are each covered, as are names that need quoting (dots, brackets, parentheses), and the matrix dtype'
  - 'the error cases (no ~, no left-hand side, unknown column, unknown level, a design without counts where one is required) are pinned as PatsyLiteParseError or the command''s exit, by message substance; the documented np.log pass-through, which fails today (DETK-0024), is pinned as it behaves and raised with Adam, not fixed here'
  - 'the tests pass on main as it is (patsy) and import nothing from patsy'
from: [DETK-0001]
scope: [tests/patsy_lite/]
prev: [DETK-0001]
issue: 71
visited: a21a419
---

# Pin the formula matrices in tests

## Implementation plan

- [x] @developer Add fixtures and tests under `tests/patsy_lite/` for the documented formulas, the de tests' designs, quoting and the error cases; no change to `de_toolkit/`; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the documented syntax fully covered, fixtures independent of patsy <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B). Needs no
library choice, so it can start before DETK-0024 is answered, and is
worth landing whichever way DETK-0024 goes. The cases come from the
DETK-0024 study (bool columns, dtype, no left side).
