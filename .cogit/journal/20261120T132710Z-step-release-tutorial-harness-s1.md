---
kind: step
time: 2026-11-20T13:27:10Z
by: DETK/developer
node: release/tutorial-harness
step: s1
branch: node/83-tutorial-harness
verdict: done
commits: [a1768bb]
decisions: []
---

# Done: Build the collector and its markers with fixture pages and tests, the tutorials index and nav, the CI wiring and the docs/dev how-to; open the PR

## Summary

Runner tests/tutorials/tutorial_runner.py with requires/expect/fails/hidden markers, tested on fixture pages in tests/tutorials/pages/; tutorial_workdir fixture for test_<page>.py; docs/tutorials/index.md and nav; docs/dev/tutorials.md; R CI job installs Miller and sets DETK_TUTORIALS_REQUIRE_ALL=1. Decisions within the node: '...' wildcard plus 'expect regex' as the pattern forms; expect compares stdout, stderr after a fails block (or 'expect stdout|stderr'); hidden blocks sit inside an HTML comment; shell variables, functions and cwd carry between blocks; TUTORIAL_SRC names the page's directory for committed data; R job fails rather than skips on a missing requirement.

## Artifacts

## Findings

## Questions
