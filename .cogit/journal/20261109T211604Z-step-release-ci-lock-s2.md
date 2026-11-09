---
kind: step
time: 2026-11-09T21:16:04Z
by: DETK/reviewer
node: release/ci-lock
step: s2
branch: node/58-ci-lock
verdict: approve
commits: []
decisions: []
---


# Review of #60: the R job installs from uv.lock; Python 3.14 best effort

## Summary

Approve. The R job (`test with R (bioconda)`) now exports `uv.lock` with
`uv export --frozen --group dev --no-hashes --no-emit-project`, pip installs
the list into micromamba's Python 3.12, installs detk with `--no-deps -e .`,
runs `pip check` and prints the key versions. The log of the R job shows the
locked versions (numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.1), `pip check`
clean, and the full suite with R passing. A local reproduction of the same
export and install in a fresh Python 3.12 venv gives exactly the lock's
3.12 set: the only differences between `pip freeze` and the export are the
entries whose markers exclude 3.12 on Linux. Both acceptance lines hold.

pip replaces conda's numpy (2.5.4 to the locked 2.5.2). It does no harm
here: wrapr calls R through `Rscript` in a subprocess
(de_toolkit/wrapr.py:34,75), rpy2 is not used, and nothing on the R side
loads Python's numpy; `pip check` is clean. `--frozen` does not check that
the lock is current, but the `test` matrix's `uv sync --locked` does, so a
stale lock still fails CI (as DETK-0018 says).

The 3.14 stance is consistent: no 3.14 classifier or matrix entry,
`requires-python = ">=3.11"` with no cap, README/docs say "3.11 or newer",
and the CHANGELOG line states best effort. The revised acceptance of
release/view-text and release/skill-update parses as YAML and covers what
the review of #57 asked.

## Artifacts

- Diff: origin/main...4c0c14b (node/58-ci-lock, main merged in)
- CI run 42697250745 (head before the merge of main), R job log; CI run
  42699147380 on head 4c0c14b
- Local reproduction: uv export of the lock, pip install into a fresh
  `uv venv --python 3.12`, `pip check`, version print

| package | uv.lock (3.12 pin) | R job log (runs 42697250745 and 42699147380) | local 3.12 venv |
|---|---|---|---|
| python | - | 3.12.16 | 3.12.3 |
| numpy | 2.5.2 (2.4.6 for <3.12) | 2.5.2 | 2.5.2 |
| pandas | 3.0.5 | 3.0.5 | 3.0.5 |
| matplotlib | 3.11.1 | 3.11.1 | 3.11.1 |
| scipy | 1.18.0 (1.17.1 for 3.11) | 1.18.0 (installed list) | 1.18.0 |
| statsmodels | 0.14.6 | - | 0.14.6 |
| scikit-learn | 1.9.0 | - | 1.9.0 |
| patsy | 1.0.2 | - | 1.0.2 |
| pip check | - | No broken requirements found | No broken requirements found |

Checks: `uv run pytest -q` 275 passed, 49 skipped; `ruff check .` clean;
`ruff format --check .` clean; `mkdocs build --strict` clean;
`cogit validate` 0 errors, 0 warnings; R job on run 42697250745: 319
passed, 5 skipped. PR checks on head 4c0c14b: all green (ruff, docs, test 3.11/3.12/3.13, test with R, combined coverage, CodeQL); the R job on run 42699147380 printed python 3.12.16, numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.1, pip check clean, 319 passed, 5 skipped.

## Findings

1. .cogit/decisions/0018-install-the-r-job-s-python-dependencies-from-an-export-of.md:16-17
   (low, wording): the Background says the `test` matrix runs Python 3.10
   to 3.13; after main's move to `>=3.11` it is 3.11 to 3.13
   (.github/workflows/ci.yml:47). Likewise DETK-0019's Background
   (.cogit/decisions/0019-python-3-14-is-best-effort-for-1-0.md:16-17, 53) still
   describes the 3.10 floor as current with the 3.11 move pending, and its
   Decision gives both ranges. Worth a one-line touch when either is
   accepted; the decisions themselves are unaffected.
2. .github/workflows/ci.yml:121 (info, pre-existing): `pip install
   --upgrade pip` is unpinned, so pip's version in the R job floats. It only
   affects the installer, not the installed set (the requirements are all
   `==` pins), so it is harmless; noted only because the node is about
   reproducibility.
3. .github/workflows/ci.yml:122 (info): pip overwrites conda's numpy 2.5.4
   with the locked 2.5.2, leaving conda's metadata out of step with
   site-packages. Harmless in an ephemeral CI environment where nothing
   uses conda to manage numpy afterwards and R does not load Python (see
   Summary); it would matter only if a later step ran `micromamba install`
   into the same environment.
4. .cogit/plan/release/skill-update.md:7 (info): the new acceptance asks
   the skill to recommend `detk-norm library` alongside cpm and tpm;
   `detk-norm library` now works on main (checked on a small matrix), and
   release/tpm-cpm is done, so the item is achievable. `prev` does not
   list release/tpm-cpm, but it is already done, so ordering is not at
   risk.

## Questions

- None blocking. The R job's 5 skipped tests are not listed in the log
  (no `-rs`); if it matters which they are, adding `-rs` to the R job's
  pytest line would show them.
