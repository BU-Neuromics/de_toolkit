---
kind: step
time: 2026-11-21T02:08:51Z
by: DETK/developer
node: release/ci-jsdom
step: s1
branch: node/130-ci-jsdom
verdict: done
commits: [30b4b62]
decisions: []
---

# Done: Set up node and a pinned jsdom in one CI job with NODE_PATH, make the jsdom tests required there through an environment variable, test the marker, update the test module's docstring; open the PR

## Summary

PR #132: 3.13 test job installs jsdom 25.0.1 (tests/report/package-lock.json) outside the tree, NODE_PATH, DETK_REQUIRE_JSDOM=1; needs_jsdom fixture marker skips or fails; marker test; docstring. 3.13 log: 15/15 passed in the render-test step, 8 needs_jsdom; 3.11/3.12 skip them

## Artifacts

## Findings

## Questions
