---
kind: task
objective: 'patsy-lite builds its model matrices with formulaic, and detk no longer uses patsy (DETK-0001, DETK-0024)'
acceptance:
  - 'de_toolkit/patsy_lite.py builds model matrices with formulaic (formula object and model_matrix in place of ModelDesc and dmatrices); no module of de_toolkit imports patsy; pyproject.toml lists formulaic and no longer lists patsy'
  - 'the DETK-0024 study''s fixes are in: bool columns are made categorical before the matrix is built (so a TRUE/FALSE column still gives `x__True`), the matrices are cast to float, awkward names are quoted with backticks and the name map follows, term order is restored from formulaic''s terms (with its intercept term `1` mapped to `Intercept`), and every invalid formula, including one with no left-hand side, raises PatsyLiteParseError'
  - 'the release/formula-pin tests pass with their fixtures unchanged, except error-message text, which may change and is listed in the CHANGELOG; any matrix or column name that has to change is a question for Adam first'
  - '`test_patsy_lite_to_patsy`, which asserts patsy''s ModelDesc strings, is rewritten against the formulaic translation'
  - 'detk-de deseq2 and firth give the same results on the airway example as before, shown by the R-gated tests in CI'
  - 'docs/formulas.md no longer names patsy as the engine; the np.log claim and transforms are left to release/formula-rename and release/formula-transforms (DETK-0028)'
from: [DETK-0001, DETK-0024]
scope: [de_toolkit/patsy_lite.py, tests/patsy_lite/, docs/formulas.md, pyproject.toml, uv.lock, +CHANGELOG]
prev: [DETK-0024, release/formula-pin]
---

# Replace patsy with formulaic in patsy-lite

## Implementation plan

- [ ] @developer Port `patsy_lite.py` to formulaic as studied in DETK-0024 (bool to categorical, float cast, backtick quoting, term order, error wrapping), keeping its parser, its `__` names and its API; rewrite the translation test; swap patsy for formulaic in `pyproject.toml`, relock; drop the patsy wording in `docs/formulas.md`; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR, including the formula-pin fixtures and the R-gated de tests in CI <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18; DETK-0024 accepted formulaic on 2026-11-19 ("accept
the migration to formulaic and proceed to planning and implementation").
The study, with the port's four changes and the 21-of-26 comparison, is in
the record's Context and How to reproduce. The rename Adam asked for is
release/formula-rename (DETK-0027); this node keeps the name so the port
and the rename review separately. Shares `pyproject.toml` and `uv.lock`
with release/cli-migrate and release/statsmodels-test: whichever lands
later relocks. `environment.yml` is deleted by release/statsmodels-test
(DETK-0048), so this node no longer touches it. Keeps the file name
`patsy_lite.py`; release/formula-rename renames it to `formula.py`
(DETK-0027) afterwards.
