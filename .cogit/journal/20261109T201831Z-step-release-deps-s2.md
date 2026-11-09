---
kind: step
time: 2026-11-09T20:18:31Z
by: DETK/reviewer
node: release/deps
step: s2
branch: node/53-deps
verdict: approve
commits: []
decisions: []
---


# Review: release/deps, PR #54 (uv.lock for the Dependabot alerts; drop Python 3.10 per DETK-0016)

## Summary

Approve. Reviewed head 4b74ce5 against origin/main. The lock now
carries only patched versions of every package an open alert names,
with no Python split keeping an old one: `requires-python = ">=3.11"`
in the lock, one Pillow (13.0.0), one certifi (2026.10.23), one
urllib3 (2.8.0). `uv lock --check` is clean. Python 3.10 is gone from
`requires-python`, the classifiers, ruff's `target-version` (now
py311), the CI matrix, README, docs/index.md, docs/agent-skills.md,
the skill and the CHANGELOG; a repo-wide grep finds no other 3.10
claim (Dockerfile is Ubuntu 24.04 / Python 3.12; CITATION.cff and
environment.yml name no Python version). On Python 3.11 and newer
nothing moved in the lock apart from certifi, urllib3 and Pillow.
The packages that left were all 3.10-only. The suite passes locally
on 3.11 and 3.13 and in CI on every job, including the R job. The
UP017 change (`timezone.utc` -> `datetime.UTC`) is the same object
on 3.11+, so it changes no behaviour.

The alerts close only once this merges to main, because Dependabot
reads the default branch. All 45 are still open at review time, as
they should be.

### Alert-to-lock table (open alerts on main, 2026-11-09)

| Alerts | Package | First patched | In lock (PR) | Split? | OK |
|---|---|---|---|---|---|
| #82-#90, #93-#124 (41) | pillow | 13.0.0 | 13.0.0 | none | yes |
| #80, #81, #91 | urllib3 | 2.8.0 | 2.8.0 | none | yes |
| #125 | certifi | 2026.10.18 | 2026.10.23 | none | yes |

### Lock delta (origin/main -> PR)

Moved: certifi 2026.7.22 -> 2026.10.23, urllib3 2.7.0 -> 2.8.0,
pillow 12.3.0 -> 13.0.0. Removed, all 3.10-only: numpy 2.2.6,
scipy 1.15.3, pandas 2.3.3, scikit-learn 1.7.2, matplotlib 3.10.9,
contourpy 1.3.2, rpds-py 0.30.0, exceptiongroup, isodate, pytz.
Unchanged for 3.11+: numpy 2.4.6 (3.11) / 2.5.2 (3.12+), scipy 1.17.1
/ 1.18.0, pandas 3.0.5, scikit-learn 1.9.0, statsmodels 0.14.6,
matplotlib 3.11.1. No change in a major version that could change
results.

## Artifacts

- `uv lock --check`: Resolved 92 packages, clean
- `uv run --locked --python 3.11 pytest` (scratch venv; Py 3.11.16, Pillow 13.0.0, numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, sklearn 1.9.0, statsmodels 0.14.6): 216 passed, 49 skipped (R)
- `uv run --locked pytest` (Py 3.13.15, scratch venv): 216 passed, 49 skipped
- `uv run ruff check .`: all checks passed; `ruff format --check .`: 165 files already formatted
- `uv run --group docs mkdocs build --strict`: built clean
- `gh pr checks 54`: all pass. That covers test 3.11/3.12/3.13, test with R (bioconda) at 247 passed / 24 skipped in 8m20s, combined coverage, ruff, docs build (strict), CodeQL and Analyze.
- grep for 3.10 / py310 across tracked files (excluding uv.lock, .cogit and the vendored JS): only the new CHANGELOG line and skills/detk/SKILL.md:37, which is about 0.9.12 and still true

## Findings

1. Medium (pre-existing, not blocking): `.github/workflows/ci.yml:107-112`. The R job installs with `pip install -e '.[test]'` into micromamba's Python 3.12, not from `uv.lock`. It resolved pandas 3.1.1, matplotlib 3.11.2 and contourpy 1.4.0 where the lock has 3.0.5, 3.11.1 and 1.3.3. Pillow 13.0.0 happens to match. So the acceptance line "the full test suite, with R, passes on the updated lock" is met only approximately: the R-gated tests passed against a fresh PyPI resolution, not the lock. Suggest a follow-up so the R job installs from the lock, for example `uv export --locked` piped to pip, or `uv sync --locked --python $(which python)`.
2. Low: the PR #54 description is stale after 4b74ce5. It still says ruff's `target-version` "stays `py310`" and that the skill is "outside the node's scope". Both changed in 4b74ce5 (py311 plus UP017 fixes; scope widened). Update the body before merge so the record matches the diff.
3. Low (process): commit 4b74ce5 (ruff py311; `datetime.UTC` in `de_toolkit/common.py:27-29`, `de_toolkit/crate.py:33,222`, `de_toolkit/report.py:38,156`) came after the last s1 result, whose `commits:` lists only 05a25b4, 635517a and 7ad0b38. No step result records it. Reviewed here: no behaviour change, ruff and the tests are clean.
4. Info: `CHANGELOG:10-11` says "Modernized to Python 3.11-3.13" and then "Python 3.10 is no longer supported (it reached end of life in October 2026)". Accurate (PEP 619), slightly redundant, fine as is.
5. Info (pre-existing, out of scope): `environment.yml` is stale (docopt, sphinx, future, no Python pin) and does not reflect the pyproject dependencies. No 3.10 claim, so nothing for this node.

## Questions

1. For Adam (the record is his): DETK-0016's Consequences says "3.10 users stay on 0.9.x". But 0.9.12, the only 0.9.x on PyPI, cannot run on Python 3.10 or newer: skills/detk/SKILL.md:36-37 says it dies with `ImportError: cannot import name 'Mapping' from 'collections'`. In practice, 3.10 users have no working detk release, unless they install a pre-1.0 commit from GitHub. Should the Consequences line be amended to say so?
2. The lock already carries Python 3.14 resolution markers, but the classifiers and CI matrix stop at 3.13. Is 3.14 meant for 1.0 or later? Not this node's question; noted only.
