---
kind: task
objective: 'Every job in ci.yml and release.yml runs with a GITHUB_TOKEN limited to what it needs, closing CodeQL''s actions/missing-workflow-permissions alerts #1 #3 #4 #5 #7 #10 (ci.yml) and #6 (release.yml), with Trusted Publishing intact'
acceptance:
  - 'ci.yml and release.yml each set a top-level permissions block of contents: read; the publish job in release.yml keeps id-token: write (Trusted Publishing) and attach-to-release keeps contents: write; no job gains a permission it did not have; a test in tests/ci/test_workflow_permissions.py, run (not skipped) by the CI test job, fails when either workflow lacks the top-level block, when publish lacks id-token: write or when any job asks for a write permission other than those two'
  - every CI job passes on the PR with the reduced token (lint, docs, runtime-deps, test, test-r, coverage); CodeQL's analysis of the PR reports no actions/missing-workflow-permissions alert on either workflow, and after the merge gh api repos/BU-Neuromics/de_toolkit/code-scanning/alerts/N gives state fixed for each N in 1 3 4 5 6 7 10
scope: [.github/workflows/ci.yml, .github/workflows/release.yml, new:tests/ci/, +pyproject.toml, +uv.lock]
---

# CI and release workflows run with least-privilege token permissions

## Implementation plan

## Notes
