---
kind: step
time: 2026-11-28T01:22:02Z
by: DETK/reviewer
node: release-1-0-1/outlier-shrink-int
step: s2
branch: review/outlier-shrink-int
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved at 52f68a1: the reproduction fails on v1.0.0 and passes here; both acceptance criteria hold; changes are within scope; all 12 CI checks pass, including test with R (bioconda).

## Artifacts

## Findings

1. Reproduction: tests/outlier/test_outlier.py copied onto a v1.0.0 checkout: the three integer tests fail (test_shrink_cli_integer_counts with (1, 0) != (0, 0) and stderr 'detk-outlier: error: Invalid value '[48.75]' for dtype 'int64''; test_shrink_integer_counts_python[int] with the same TypeError from PMFTransform.__init__; test_pmf_transform_integer_counts) and the float case passes. By hand on v1.0.0, 'detk-outlier shrink' on gene,A,B,C,D / g1,10,12,11,300 / ... exits 1 with that message. Here all pass. outlier.py's shrink path is unchanged between v1.0.0 and main apart from the reader's check='ids' (#203). 2. Acceptance 1: the CLI test runs the integer and decimal matrices, asserts both exit 0, that g1/D was shrunk to a fraction, that every column is float, and assert_frame_equal on the two outputs. 3. Acceptance 2: PMFTransform does count_obj.astype(float) in place of .copy(), so the input is still not changed and the output is always float, including when nothing is shrunk (tested). shrink and pmf_transform are tested from Python with integer input, and the test checks the input is unchanged. The new pmf_transform docstring and the Returns section of shrink say the output is float. So does docs/tools/outlier.md. CHANGELOG 1.0.1 has an entry under Fixed (#219). 4. Scope: de_toolkit/outlier.py, tests/outlier/test_outlier.py, docs/tools/outlier.md, CHANGELOG and .cogit records; nothing else changed. 5. Checks: full suite locally 2845 passed, 160 skipped (R not installed; the test_check_counts failure in the s1 note is gone since #221 merged in); ruff check and format clean; CI 12/12 pass, including test with R (bioconda), 24m10s. The per-feature vs per-sample p_max issue is left to outlier-shrink-axis (DETK-0861), as planned. No decisions needed.

## Questions
