---
kind: step
time: 2026-11-09T21:04:20Z
by: DETK/developer
node: release/ci-lock
step: s1
branch: node/58-ci-lock
verdict: done
commits: [34cc4ad, 9aa8c3d, 2c3a0ac]
decisions: [DETK-0018, DETK-0019]
---

# Done: Make the R job install from uv.lock; record the method and Python 3.14 as best effort (Provisional); open the PR

## Summary

The R job now exports uv.lock (uv export --frozen --group dev) and pip installs it into the micromamba Python, then detk with --no-deps; on PR #60 it printed python 3.12.16, numpy 2.5.2, pandas 3.0.5, matplotlib 3.11.1 (the locked versions), pip check clean, and the full suite with R passed (319 passed, 5 skipped). Python 3.14 is recorded best effort (DETK-0019), with a CHANGELOG line and no classifier or CI entry. Done because both acceptance lines hold on the PR's CI run.

## Artifacts

## Findings

## Questions
