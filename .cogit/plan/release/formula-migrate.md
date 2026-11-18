---
kind: task
objective: 'patsy-lite builds its model matrices with the library chosen in DETK-0024, and detk no longer uses patsy (DETK-0001)'
acceptance:
  - 'de_toolkit/patsy_lite.py builds model matrices with the choice of DETK-0024; no module of de_toolkit imports patsy and pyproject.toml no longer lists it (statsmodels may still install it)'
  - 'the release/formula-pin tests pass with their fixtures unchanged. A matrix or column name that has to change is a decision for Adam first, and a breaking change in the CHANGELOG once agreed'
  - 'detk-de deseq2 and firth give the same results on the airway example as before, shown by the R-gated tests in CI'
  - 'docs/formulas.md describes the new backend and states which pass-through terms are supported'
from: [DETK-0001, DETK-0024]
scope: [de_toolkit/patsy_lite.py, tests/patsy_lite/, docs/formulas.md, pyproject.toml, uv.lock, environment.yml, +CHANGELOG]
prev: [DETK-0024, release/formula-pin]
---

# Replace patsy in patsy-lite

## Implementation plan

- [ ] @developer Rebuild `patsy_lite.py` on the DETK-0024 choice, keeping its parser, its `__` names and its errors; drop the patsy pin, relock; update `docs/formulas.md`; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR, including the formula-pin fixtures and the R-gated de tests in CI <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B); waits on his
choice of formula library (DETK-0024). The module keeps its name: the
patsy-lite syntax is what the docs call the formula language. Shares
`pyproject.toml`, `uv.lock` and `environment.yml` with
release/cli-migrate: whichever lands second relocks.
