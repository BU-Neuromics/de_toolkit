---
kind: step
time: 2026-11-27T21:30:29Z
by: DETK/developer
node: release-1-0-1/count-checks-readers
step: s1
branch: node/201-count-checks-readers
verdict: done
commits: [028a2bf, 2960e6d, b1e8403, c48339b]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Every reader checks the counts as read (DETK-0830, Accepted): make_cli_count_obj(args, raw=...) / CountMatrixFile(check='ids'|'raw') run check_counts before the column data selects or reorders a sample. Repeated sample headers and feature IDs exit 1 in all 24 commands tested; negative counts, samples with no numeric value and zero-depth samples also exit 1 in detk-norm (all), detk-de deseq2, detk-transform vst/rlog, and are accepted in detk-de firth, detk-transform plog, detk-stats, detk-filter, detk-outlier. Both #196 nits folded in (file-order positions; 'has no numeric counts'). Reproduction tests/common/test_readers_count_checks.py (2960e6d) fails on v1.0.0 (48 duplicate cases, 18 raw-value cases) and passes here; unit tests in tests/common/test_check_counts.py; docs/concepts.md and CHANGELOG 1.0.1. Full suite 2796 passed, 156 skipped; ruff and mkdocs --strict clean.

## Artifacts

## Findings

## Questions
