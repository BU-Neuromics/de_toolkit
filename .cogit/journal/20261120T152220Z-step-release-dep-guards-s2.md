---
kind: step
time: 2026-11-20T15:22:20Z
by: DETK/reviewer
node: release/dep-guards
step: s2
branch: review/dep-guards
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR

## Summary

Approved: TEST_ONLY guards statsmodels, patsy and docopt-ng; failure reproduced for patsy and docopt-ng; E402 comment accurate (ignore still needed: 101 sites); CI green on all 12 checks incl. R

## Artifacts

## Findings

- Diff (9a704f1..77b3ca8) touches only tests/check_runtime_deps.py and pyproject.toml, within scope. TEST_ONLY maps import name to package (docopt -> docopt-ng); message, docstring and success line name all three.
- Reproduced by hand in a scratch worktree (not committed): with "patsy" added to [project] dependencies, uv lock + uv sync --locked --no-dev, the check exits 1 with 'patsy is installed: ...'; same with "docopt-ng": exits 1 with 'docopt-ng is installed: ...'. Clean tree: exit 0, '17 modules import and detk-norm runs without statsmodels, patsy, docopt-ng'.
- Runtime dependencies on the branch: jinja2, matplotlib, numpy, pandas, ply, scipy, scikit-learn, terminaltables, formulaic>=1.1; statsmodels only in the test extra and dev group.
- E402: with the ignore removed ruff finds 101 sites in de, enrich, norm, outlier, report, stats, transform, util, wrapr; each opens with SUBCOMMANDS (and build_parser) before its imports, so the new comment is accurate and keeping the ignore is right. ruff check and ruff format --check clean.
- CI on 77b3ca8: all 12 checks pass, including 'test with R (bioconda)' and 'runtime dependencies only'. No CHANGELOG line needed (nothing user-visible), per the node notes.
- No decisions needed.

## Questions
