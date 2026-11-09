---
kind: step
time: 2026-11-09T19:43:48Z
by: DETK/developer
node: release/gather
step: s1
branch: node/25-gather
verdict: done
commits: [563c91f, 279ff0c]
decisions: [DETK-0012, DETK-0013]
---

# Done: Implement with tests, a report view, the docs page and a CHANGELOG entry; open the PR

## Summary

Implemented detk-util gather (salmon, kallisto, htseq-count, featureCounts; header-based auto-detection; --column, --name-from, --on-mismatch=error|fill|drop, -o) in de_toolkit/util.py with a report view (report_specs.py) and a crate SUBTOOLS entry (crate.py, outside scope, for provenance). 27 tests with per-format fixtures under tests/util/; docs/tools/util.md section; csvgather replaced in docs/quickstart.md (docs/example.md never used it); CHANGELOG line. Checks pass: pytest 224 passed/49 skipped, ruff check and format, mkdocs --strict. Done: every part of the step is in place; decisions DETK-0012 and DETK-0013 are Provisional for review.

## Artifacts

## Findings

## Questions
