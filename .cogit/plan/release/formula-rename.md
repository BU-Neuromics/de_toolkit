---
kind: task
objective: 'The formula module has the name DETK-0027 gives it, and formulas handle transforms such as np.log(x) as DETK-0028 decides (DETK-0024)'
acceptance:
  - 'de_toolkit/patsy_lite.py is renamed per DETK-0027 with its exception and translation function, tests/patsy_lite/ moves with it, common.py imports the new module, and the user-visible text "patsy lite could not parse" names the new syntax'
  - 'docs/formulas.md calls the syntax by its new name and handles transforms per DETK-0028: under Option A the np.log claim is gone and a term that is not a column fails with a message telling the user to add the transformed column to the column data file; under B or C the chosen behaviour is implemented and tested'
  - 'no module, test or doc of the repository still says patsy-lite or patsy_lite, except the CHANGELOG''s history'
  - 'the formula-pin fixtures pass, with only the import path and the DETK-0028 term changed'
from: [DETK-0024, DETK-0027, DETK-0028]
scope: [de_toolkit/patsy_lite.py, de_toolkit/formula.py, de_toolkit/design.py, de_toolkit/design_formula.py, +de_toolkit/common.py, tests/patsy_lite/, tests/formula/, tests/design/, tests/design_formula/, docs/formulas.md, +CHANGELOG]
prev: [DETK-0027, DETK-0028, release/formula-migrate]
---

# Rename patsy-lite and settle transforms in formulas

## Implementation plan

- [ ] @developer Rename the module, exception, function and tests per DETK-0027; carry out DETK-0028 in the module and `docs/formulas.md`; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: nothing still names patsy-lite, the transforms behaviour matches DETK-0028 <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-19 on Adam's answer to DETK-0024 ("we need to rename
patsy_lite.py to something else"). The scope lists the three candidate
paths of DETK-0027; once the name is chosen, the other two are dropped. Its
`common.py` edit is the import and the error text only.
