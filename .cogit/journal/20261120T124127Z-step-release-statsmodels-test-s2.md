---
kind: step
time: 2026-11-20T12:41:27Z
by: DETK/reviewer
node: release/statsmodels-test
step: s2
branch: review/statsmodels-test
verdict: approve
commits: []
decisions: []
---

# Approved: PR #76 makes statsmodels a test-only dependency

## Summary

Approved. The acceptance is met: statsmodels is in the `test` extra and
the `dev` group and not in `dependencies`, and uv.lock is relocked to
match. The new "runtime dependencies only" CI job imports every
de_toolkit module and runs `detk-norm cpm` without statsmodels. The
logistic comparison in tests/de/test_de.py still runs in the R job.
environment.yml is deleted and nothing outside the CHANGELOG and .cogit/
refers to it. The CHANGELOG states both changes. No change to de_toolkit/.

## Artifacts

- PR #76 reviewed at 014e27d

## Findings

- Checks run here: `uv sync --locked --no-dev` into a separate venv, then
  tests/check_runtime_deps.py: 18 modules import, detk-norm cpm runs,
  statsmodels absent, patsy 1.0.2 present (it is a direct runtime
  dependency, so dropping statsmodels does not take patsy with it before
  release/formula-migrate). Full suite: 1736 passed, 63 skipped (R not
  installed here). ruff check and format are clean.
- CI at 014e27d is all green: ruff, docs (strict), runtime dependencies
  only, test 3.11/3.12/3.13, test with R (bioconda) (1786 passed, 13
  skipped), CodeQL. The R job exports `--group dev` from uv.lock and
  installed statsmodels 0.14.6. test_firth and test_firth_w_cov are gated
  only on R and logistf (r-logistf is in that job's environment), so the
  Firth-vs-statsmodels logistic comparison ran there.
- uv.lock: statsmodels moves from the project's dependencies to the `test`
  extra and the dev group, `requires-dist` carries `extra == 'test'`, and
  the package entry stays (the dev group needs it). The diff is consistent.
- check_runtime_deps.py does not match pytest's test_*.py pattern, so the
  suite does not collect it. It refuses to run if statsmodels is installed,
  so the CI job cannot pass vacuously in a dev environment.
- Nit (non-blocking): the check catches module-level imports and anything
  that `detk-norm cpm` reaches. A function-local `import statsmodels`
  elsewhere in de_toolkit/ would only show up at call time. A
  source grep for `statsmodels` under de_toolkit/ in the same script would
  close that gap cheaply. Not required by the acceptance.

## Questions

None.
