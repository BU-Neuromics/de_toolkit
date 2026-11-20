---
kind: task
objective: 'The formula module is de_toolkit/formula.py (DETK-0027), nothing in the code or docs names patsy-lite any more, and formulas take column names only, with a clear error for a call (DETK-0024, DETK-0050)'
acceptance:
  - 'de_toolkit/patsy_lite.py is renamed de_toolkit/formula.py; PatsyLiteParseError becomes FormulaParseError with no alias kept; patsy_lite_to_patsy gets a name that says what it now translates to; tests/patsy_lite/ moves to tests/formula/; common.py imports the new module; the user-visible "patsy lite could not parse" text names "detk formula syntax"'
  - 'docs/formulas.md calls the syntax "detk formula syntax"; its fourth term type keeps interactions (a:b, a*b), which work once release/formula-migrate has fixed a:b (DETK-0040), and drops the np.log example, which does not work (DETK-0050)'
  - 'a term that is not a column of the column data file and looks like a call (np.log(x), log2(x)) raises FormulaParseError saying formulas take column names only and that derived columns belong in the column data file; release/miller-recipes later points that message to the derived-covariates recipes page (DETK-0051 Option C); a column whose name really is such a string still works as a column; the np.log pins change their expected message only'
  - 'no module, test or doc of the repository still says patsy-lite or patsy_lite, except the CHANGELOG''s history'
  - 'the formula-pin fixtures pass unchanged except for the import path, the exception name, and error text naming the syntax or the call error above'
  - 'the CHANGELOG lists the rename and the exception''s new name'
  - 'a formula pin covers the airway design `counts ~ cell + dex[untrt]`: the eight samples'' column data as examples/airway/prepare_data.R writes sample_info.csv, committed under tests/formula/, and a fixture of the full model matrix (column names and order, values, row order, dtype) and its left- and right-hand side names, built on main before the rename and passing unchanged after it, so that the matrix detk-de deseq2 and firth get for the airway example is checked by a test, not by the manual before/after comparison of release/formula-migrate''s review'
from: [DETK-0024, DETK-0027, DETK-0050]
scope: [de_toolkit/patsy_lite.py, de_toolkit/formula.py, +de_toolkit/common.py, tests/patsy_lite/, tests/formula/, docs/formulas.md, +CHANGELOG]
prev: [DETK-0027, DETK-0050, release/formula-migrate]
issue: 89
visited: 9a704f1
---

# Rename patsy-lite to formula

## Implementation plan

- [x] @developer Rename the module to `formula.py`, the exception to `FormulaParseError`, the translation function and `tests/patsy_lite/` to `tests/formula/`; update the import and error text in `common.py`; rename the syntax in `docs/formulas.md` and drop its np.log claim; the clear error for a call in a formula (DETK-0050); the airway design pin; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: nothing still names patsy-lite, the formula-pin fixtures unchanged but for names <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-19 on Adam's answer to DETK-0024 ("we need to rename
patsy_lite.py to something else"); the name is DETK-0027 ("formula.py",
2026-11-19). Adam first chose transforms in formulas (DETK-0028), then
the same day kept formulas to the model only (DETK-0050): derived columns
come from the Miller recipes of release/miller-recipes, run through detk-util record (DETK-0051 Option C). This node adds the error that says so. Its `common.py` edit is the import and the error text only.

The airway pin was added 2026-11-20 by the planning session on the
driver's list of follow-ups (Adam's delegation, DETK-0063): the reviewer of
release/formula-migrate checked by hand that the airway designs build
byte-identical matrices before and after the port to formulaic; the pin
makes that a test for this rename and every later change.
