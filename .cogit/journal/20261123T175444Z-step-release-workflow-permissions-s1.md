---
kind: step
time: 2026-11-23T17:54:44Z
by: DETK/developer
node: release/workflow-permissions
step: s1
branch: node/157-workflow-permissions
verdict: done
commits: [7f75d85]
decisions: []
---

# Done: Add a top-level `permissions: contents: read` to ci.yml and release.yml, keep publish's `id-token: write` and attach-to-release's `contents: write`, add the workflow-permissions test (pyyaml into the dev group if the test reads YAML; it is already locked through mkdocs); open the PR

## Summary

Top-level permissions: contents: read in ci.yml and release.yml; publish keeps id-token: write, attach-to-release keeps contents: write (unchanged job-level blocks). tests/ci/test_workflow_permissions.py (14 tests, run by the test and test-r jobs; no skip path) checks both workflows and fails on a missing/broader top-level block, publish without id-token: write, or any other write grant. pyyaml>=6.0.3 added to the dev group (already locked via mkdocs). Local: full non-R suite 2567 passed; ruff clean; uv lock --check clean. No decisions made.

## Artifacts

## Findings

## Questions
