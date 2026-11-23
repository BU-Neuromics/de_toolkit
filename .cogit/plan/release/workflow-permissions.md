---
kind: task
objective: 'Every job in ci.yml and release.yml runs with a GITHUB_TOKEN limited to what it needs, closing CodeQL''s actions/missing-workflow-permissions alerts #1 #3 #4 #5 #7 #10 (ci.yml) and #6 (release.yml), with Trusted Publishing intact'
acceptance:
  - 'ci.yml and release.yml each set a top-level permissions block of contents: read; the publish job in release.yml keeps id-token: write (Trusted Publishing) and attach-to-release keeps contents: write; no job gains a permission it did not have; a test in tests/ci/test_workflow_permissions.py, run (not skipped) by the CI test job, fails when either workflow lacks the top-level block, when publish lacks id-token: write or when any job asks for a write permission other than those two'
  - every CI job passes on the PR with the reduced token (lint, docs, runtime-deps, test, test-r, coverage); CodeQL's analysis of the PR reports no actions/missing-workflow-permissions alert on either workflow, and after the merge gh api repos/BU-Neuromics/de_toolkit/code-scanning/alerts/N gives state fixed for each N in 1 3 4 5 6 7 10
scope: [.github/workflows/ci.yml, .github/workflows/release.yml, new:tests/ci/, +pyproject.toml, +uv.lock]
issue: 157
visited: 203b21f
---

# CI and release workflows run with least-privilege token permissions

## Implementation plan

- [x] @developer Add a top-level `permissions: contents: read` to ci.yml and release.yml, keep publish's `id-token: write` and attach-to-release's `contents: write`, add the workflow-permissions test (pyyaml into the dev group if the test reads YAML; it is already locked through mkdocs); open the PR <!-- s1 -->
- [x] @reviewer Review the PR: every CI job green on the reduced token, CodeQL's PR analysis clean of actions/missing-workflow-permissions, release.yml read against PyPI's Trusted Publishing requirements; after the merge, check alerts 1 3 4 5 6 7 10 read fixed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-23. Seven older CodeQL alerts on main, all
actions/missing-workflow-permissions: ci.yml #1 (test, line 73), #3 (lint,
11), #4 (docs, 28), #5 (coverage, 216), #7 (test-r, 147), #10
(runtime-deps, 56); release.yml #6 (build, 18). Neither workflow has a
top-level block; release.yml's publish (`id-token: write`, environment
`pypi`) and attach-to-release (`contents: write`) already set their own,
which a job-level block keeps over the top-level one. No job pushes,
comments or writes packages; upload/download-artifact and setup-uv's cache
use the runtime token, not GITHUB_TOKEN. docs.yml already sets its own
block and has no alert.

No decision needed: least privilege with the two existing job grants is the
only reading of the alert that keeps Trusted Publishing (DETK-0063).
release.yml runs only on a tag, so its part is checked by the test and by
reading, not by a run; release/cut's tag is its first run.

No unfinished node holds `.github/workflows/`; `pyproject.toml` and
`uv.lock` are `+` entries only for adding pyyaml to the dev group, if the
test needs it (release/cut also edits pyproject.toml, after this node).
Ready now; before release/cut.
