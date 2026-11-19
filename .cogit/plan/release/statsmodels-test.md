---
kind: task
objective: 'statsmodels is a test-only dependency, so installing detk no longer installs statsmodels or patsy (DETK-0026)'
acceptance:
  - 'pyproject.toml lists statsmodels in the `test` extra and the `dev` group and not in the runtime dependencies; uv.lock is relocked'
  - 'a CI check imports every de_toolkit module and runs a detk command in an environment without statsmodels (the runtime dependencies only), so a runtime use cannot creep back in'
  - 'tests/de/test_de.py''s logistic comparison still runs in CI'
  - 'environment.yml is deleted (DETK-0048), and nothing in the repository refers to it'
  - 'the CHANGELOG says statsmodels (and, after release/formula-migrate, patsy) is no longer installed with detk, and that environment.yml is gone'
from: [DETK-0026, DETK-0048]
scope: [pyproject.toml, uv.lock, environment.yml, .github/workflows/, tests/, +CHANGELOG]
prev: [DETK-0026, DETK-0048]
---

# Make statsmodels a test-only dependency

## Implementation plan

- [ ] @developer Move statsmodels to the test extra and dev group, relock, add the runtime-only import check to CI, delete `environment.yml`, CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR and the CI run <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-19 on Adam's answer ("move statsmodels to test-only
dependencies"). No module of `de_toolkit/` imports statsmodels (DETK-0024
study). Shares `pyproject.toml` and `uv.lock` with the two migrations:
whichever lands later relocks. The `tests/` entry is for the import check
only. Deletes `environment.yml` on Adam's answer of 2026-11-19 (DETK-0048,
"delete it"): it is the first of the three dependency nodes to land.
