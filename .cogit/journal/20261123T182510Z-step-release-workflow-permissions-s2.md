---
kind: step
time: 2026-11-23T18:25:10Z
by: DETK/reviewer
node: release/workflow-permissions
step: s2
branch: review/workflow-permissions
verdict: approve
commits: [c039617]
decisions: []
---

# Approved: Review the PR: every CI job green on the reduced token, CodeQL's PR analysis clean of actions/missing-workflow-permissions, release.yml read against PyPI's Trusted Publishing requirements; after the merge, check alerts 1 3 4 5 6 7 10 read fixed

## Summary

Approved: top-level contents: read in ci.yml and release.yml, publish keeps id-token: write and environment pypi, attach-to-release keeps contents: write, no job gains a permission; CI green on c039617 including the R job, the permissions test runs (not skipped) in test and test-r; CodeQL's actions analysis of the PR is clean (0 results vs 7 on main). Outstanding: the post-merge check that alerts 1 3 4 5 6 7 10 read fixed

## Artifacts

## Findings

Checks: CI is green on c039617 (PR #159 head), every job: ruff, docs build (strict), runtime dependencies only, test (python 3.11/3.12/3.13), test with R (bioconda), combined coverage, and CodeQL (actions, python, javascript-typescript). tests/ci/test_workflow_permissions.py runs and passes in both the test job (14 passed; 2567 passed, 154 skipped overall) and the R job (2698 passed, 23 skipped), so it is not skipped. Locally (uv, no R): tests/ci 14 passed, ruff clean, `uv lock --check` clean.

Reduced token: the repository's default workflow permission is `write`, so before this PR every job without its own block got a read/write token. Now ci.yml and release.yml set a top-level `contents: read`. No job in ci.yml uses GITHUB_TOKEN beyond checkout. setup-uv reads uv releases with the token, and read is enough for that. setup-micromamba, setup-node and setup-python need no write, and upload/download-artifact use the runtime token. Every CI job passing on the PR shows the reduced token is enough.

CodeQL: the actions-category analysis of refs/pull/159/head at c039617 reports 0 results, against 7 on main. The open alert list for the PR ref has no actions/missing-workflow-permissions alert, and alerts 1 3 4 5 6 7 10 have no instance on the PR ref. On main they are still open, as expected before the merge.

release.yml compared with PyPI's Trusted Publishing requirements: publish keeps its job-level `id-token: write`, which takes the place of the top-level block, and keeps `environment: pypi`, the environment named in the PyPI publisher config the header describes. It uses pypa/gh-action-pypi-publish@release/v1 and needs no checkout, so it does not need contents: read. attach-to-release keeps `contents: write` for `gh release view/upload` with github.token. build drops from the default write token to contents: read: it only checks out, runs uv build and uploads an artifact. No job gains a permission. The workflow trigger and the job blocks are unchanged. I checked release.yml by reading it and through the test; no run, because it runs only on a tag. Its first run is release/cut's tag.

Test: it covers all three failure modes in the acceptance (missing/broader top-level block, publish without id-token: write, any other write grant including write-all), each with a negative case on an altered copy. I found no gaps.

Record: PR #159 is linked by branch node/157-workflow-permissions and "Closes #157" (closingIssuesReferences [157]). The developer opened it with gh rather than `cogit node done`. So the node file has no status/done stamp and there is no node-done journal entry, and nothing in .cogit names #159. This matches the earlier nodes in this repo: none carries a PR field, and status: done is stamped by the human's step done at s3. Nothing is missing that the merge needs.

Outstanding, after the merge: the step's last check, that `gh api repos/BU-Neuromics/de_toolkit/code-scanning/alerts/N` reads state fixed for N in 1 3 4 5 6 7 10. It cannot run before the merge. Alert 6 (release.yml) closes when CodeQL re-analyses main, not on a release run. Run the check after the merge, before accepting s3.

## Questions
