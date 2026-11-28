---
kind: step
time: 2026-11-27T23:39:57Z
by: DETK/developer
node: release-1-0-1/outlier-shrink-int
step: s1
branch: node/219-outlier-shrink-int
verdict: done
commits: [db9568e]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Reproduced on v1.0.0 code (outlier.py unchanged since the tag): the integer matrix exits 1 with Invalid value '[48.75]' for dtype 'int64'; the decimal one runs. Fix: PMFTransform casts to float before shrinking; output always float. Tests, docs, docstrings, CHANGELOG 1.0.1 Fixed. Full suite: 1 failure pre-existing on main bfbc2c1 (tests/common/test_check_counts.py, #198 vs #203), outside scope.

## Artifacts

## Findings

## Questions
