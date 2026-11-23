---
kind: step
time: 2026-11-22T17:56:26Z
by: DETK/developer
node: release/recipe-notes
step: s1
branch: node/140-recipe-notes
verdict: done
commits: [8a7e4ac]
decisions: []
---

# Done: Show a failed command on one line in detk-util record's messages (multi-line arguments elided), give the z-score and min-max recipes their own header-only message, and add the page and skill notes (zero-padded numbers, the constant recipe's rule, the stddev figure); tests in tests/util and tests/recipes; CHANGELOG; open the PR

## Summary

detk-util record's failure messages show a multi-line argument as its first line and ... in its quotes, or '...' (_command_line in util.py; tests in tests/util/test_record.py); the page's failing-recipe expected line updated and passing under the tutorial harness. z-score and min-max recipes stop on a header-only sheet with '<col> has no values: the sheet has no samples' (page and skill); tests/recipes case for every recipe on a header-only sheet. Page and skill notes: zero-padded numbers read as text (write without leading zeros, not mlr -O), constant recipe's column name and value may change, stddev about 1e-7 (1.07e-7 on Miller 6.22). CHANGELOG under Fixed. No decisions needed.

## Artifacts

## Findings

## Questions
