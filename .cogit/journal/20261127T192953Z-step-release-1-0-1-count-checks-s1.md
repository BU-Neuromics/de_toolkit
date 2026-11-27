---
kind: step
time: 2026-11-27T19:29:53Z
by: DETK/developer
node: release-1-0-1/count-checks
step: s1
branch: node/195-count-checks
verdict: done
commits: [61ada60, 1f7e1cc]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

check_counts in de_toolkit/common.py (duplicate header read as written, duplicate feature, negative count, zero-depth sample; first offender named, with how many more); detk-norm cpm calls it and exits 1 (DETK-0601) before writing. Reproduction tests/norm/test_cpm_count_checks.py fail on v1.0.0 (61ada60, no SystemExit) and pass here; unit tests tests/common/test_check_counts.py; docs/tools/norm.md; CHANGELOG 1.0.1. Full suite 2643 passed; ruff, mkdocs --strict clean.

## Artifacts

## Findings

## Questions
