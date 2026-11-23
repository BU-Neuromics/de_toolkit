---
kind: step
time: 2026-11-23T15:11:23Z
by: DETK/reviewer
node: release/example-paths
step: s2
branch: review/example-paths
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: open docs/example/detk_report.html and the crate, grep them for absolute paths, run the new test against the old files from 61bf890, and confirm the R job ran the tutorial

## Summary

Approved at f28463a (re-review after b9ceaea's changes asked).
- CodeQL #11 is fixed. .github/workflows/example.yml now declares a top-level `permissions: contents: read`, and the alert's instance on refs/pull/143/head reads fixed. The PR merge ref has no open alerts.
- CodeQL #12 was dismissed as "used in tests" at Adam's direction (2026-11-23), with the reason the review gave: it fails closed, and it is not a sanitizer.
- Nothing else changed. Outside .cogit/, b9ceaea..f28463a changes only those 3 lines of example.yml. The html.parser rewrite of the path test (56aa818, e22d65c) is fully reverted by 130fa33: tests/, docs/, de_toolkit/ and CHANGELOG are byte-identical to the reviewed fd81814. The merge of origin/main (501927d) brought only .cogit/ plan and decision files. docs/example/ is unchanged, and the permissions block does not affect the regenerated output.
- CI on f28463a is all green: ruff, docs build (strict), runtime deps, tests on 3.11/3.12/3.13, combined coverage, and CodeQL (actions, javascript-typescript, python). "test with R (bioconda)" (run 45198453915) passed 2633 with 23 skipped under DETK_TUTORIALS_REQUIRE_ALL=1, with tests/tutorials/test_airway.py 4/4 and test_example_paths 21/21.

## Artifacts

## Findings

## Questions
