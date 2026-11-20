---
kind: step
time: 2026-11-20T14:04:21Z
by: DETK/reviewer
node: release/tutorial-harness
step: s2
branch: review/tutorial-harness
verdict: approve
commits: []
decisions: []
---

# Approved: second review of the tutorial runner (PR #84)

## Summary

The changes asked in the first review (d43c835) are made in d14d331, and CI on
3504813 passes everywhere. Approved.

- Finding 1 (the check that markers don't show on the site ran in no CI job):
  fixed. The docs job has a new step, "Tutorial markers do not render". It runs
  the site test with the docs and dev groups and fails unless the result is
  exactly "1 passed" with nothing skipped. Its log shows
  `1 passed, 31 deselected`.
- Finding 2 (wrong claim about `fails` blocks): fixed. docs/dev/tutorials.md
  now says that files, variables and the directory a failing block left carry
  to the next block. That matches what the runner does.
- Nit 3 (EXIT trap): documented under "How a page runs".
- Nit 4 (expect after a hidden block): documented under `hidden`.

Checks: `uv run --group docs pytest tests/tutorials` gives 32 passed and 1
skipped (the empty page set), and `mkdocs build --strict` is clean. The R job on
3504813 shows `mlr 6.22.0` and 1819 passed, 15 skipped. In `tests/tutorials`
its skips are the site test (expected there; it now runs in the docs job) and
the empty page set (expected until the tutorial pages land).

## Artifacts

## Findings

None outstanding.

## Decisions

None needed.

## Questions
