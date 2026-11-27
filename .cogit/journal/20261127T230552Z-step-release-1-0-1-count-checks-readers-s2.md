---
kind: step
time: 2026-11-27T23:05:52Z
by: DETK/reviewer
node: release-1-0-1/count-checks-readers
step: s2
branch: review/count-checks-readers
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: f82ccac fixes both findings of the first round; DETK-0850 accepted (option A, 027fece); CI green on e2e9b1a including the R job.

## Artifacts

## Findings

Re-review of f82ccac, 027fece, e2e9b1a. Finding 1 fixed: docs/concepts.md and the CHANGELOG 1.0.1 entry name the commands that check (detk-norm, detk-de, detk-transform, detk-stats, detk-filter, detk-outlier) and say that detk-util tidy, tidy-counts, tidy-covs and detk-wrapr run do not check yet (DETK-0850). Finding 2 fixed: the table header reads 'all five checks'. DETK-0850 was accepted as option A (a follow-up node for util.py and wrapr.py), which this node's docs match. Merge e2e9b1a brings only main's changes; the node's diff against main is unchanged apart from the wording, .cogit records and the CHANGELOG. tests/common/test_readers_count_checks.py and test_check_counts.py: 141 passed here. CI on e2e9b1a: all green, including 'test with R (bioconda)' and 'docs build (strict)'. Still open, outside this node: the DETK-0850 follow-up node is not yet in the plan.

## Questions
