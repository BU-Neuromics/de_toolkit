---
kind: task
objective: 'The formula module is de_toolkit/formula.py (DETK-0027), nothing in the code or docs names patsy-lite any more, and the docs no longer claim np.log(x) works (DETK-0024, DETK-0028)'
acceptance:
  - 'de_toolkit/patsy_lite.py is renamed de_toolkit/formula.py; PatsyLiteParseError becomes FormulaParseError with no alias kept; patsy_lite_to_patsy gets a name that says what it now translates to; tests/patsy_lite/ moves to tests/formula/; common.py imports the new module; the user-visible "patsy lite could not parse" text names "detk formula syntax"'
  - 'docs/formulas.md calls the syntax "detk formula syntax"; its fourth term type keeps interactions (a:b, a*b), which work once release/formula-migrate has fixed a:b (DETK-0040), and drops the np.log example, which does not work; transforms are left to release/formula-transforms (DETK-0028, DETK-0047)'
  - 'no module, test or doc of the repository still says patsy-lite or patsy_lite, except the CHANGELOG''s history'
  - 'the formula-pin fixtures pass unchanged except for the import path, the exception name and error text naming the syntax'
  - 'the CHANGELOG lists the rename and the exception''s new name'
from: [DETK-0024, DETK-0027, DETK-0028]
scope: [de_toolkit/patsy_lite.py, de_toolkit/formula.py, +de_toolkit/common.py, tests/patsy_lite/, tests/formula/, docs/formulas.md, +CHANGELOG]
prev: [DETK-0027, release/formula-migrate]
---

# Rename patsy-lite to formula

## Implementation plan

- [ ] @developer Rename the module to `formula.py`, the exception to `FormulaParseError`, the translation function and `tests/patsy_lite/` to `tests/formula/`; update the import and error text in `common.py`; rename the syntax in `docs/formulas.md` and drop its np.log claim; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: nothing still names patsy-lite, the formula-pin fixtures unchanged but for names <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-19 on Adam's answer to DETK-0024 ("we need to rename
patsy_lite.py to something else"); the name is DETK-0027 ("formula.py",
2026-11-19). Adam chose transforms for 1.0 (DETK-0028 Option B); they are
release/formula-transforms, which comes after this node, so the rename and
the new syntax review separately. Here the docs only stop claiming what
does not work. Its `common.py` edit is the import and the error text only.
