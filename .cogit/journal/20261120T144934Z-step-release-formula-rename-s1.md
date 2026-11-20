---
kind: step
time: 2026-11-20T14:49:34Z
by: DETK/developer
node: release/formula-rename
step: s1
branch: node/89-formula-rename
verdict: done
commits: [7fbb940, 32db222]
decisions: []
---

# Done: Rename the module to `formula.py`, the exception to `FormulaParseError`, the translation function and `tests/patsy_lite/` to `tests/formula/`; update the import and error text in `common.py`; rename the syntax in `docs/formulas.md` and drop its np.log claim; the clear error for a call in a formula (DETK-0050); the airway design pin; CHANGELOG; open the PR

## Summary

patsy_lite renamed formula (FormulaParseError, to_formulaic, tests/formula); call-in-formula error (DETK-0050); docs and CHANGELOG; airway pin built before the rename, unchanged after; PR #92

## Artifacts

## Findings

## Questions
