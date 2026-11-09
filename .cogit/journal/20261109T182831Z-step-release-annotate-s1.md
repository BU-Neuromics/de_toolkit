---
kind: step
time: 2026-11-09T18:28:31Z
by: DETK/developer
node: release/annotate
step: s1
branch: node/29-annotate
verdict: done
commits: [eae3a1e, 109a3e4, 44529cb, 8b63419]
decisions: [DETK-0007, DETK-0008]
---

# Done: Implement with tests, a report view, the docs page and a CHANGELOG entry; open the PR

## Summary

detk-util annotate joins a user-supplied mapping file onto result tables, offline, keeping every row (PR #41); report view in a util family, 11 tests, docs and CHANGELOG. pytest 159 passed, 49 skipped (no R); ruff and mkdocs --strict clean. crate.py SUBTOOLS touched outside scope; the mapping file is not yet an RO-Crate input.

## Artifacts

## Findings

## Questions
