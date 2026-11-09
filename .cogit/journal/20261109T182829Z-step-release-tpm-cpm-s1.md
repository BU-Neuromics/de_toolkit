---
kind: step
time: 2026-11-09T18:28:29Z
by: DETK/developer
node: release/tpm-cpm
step: s1
branch: node/24-tpm-cpm
verdict: done
commits: [436fbf0, eb55807, 589ed96, 431d4bc, d65fb9b, 99d49d7]
decisions: [DETK-0005, DETK-0006]
---

# Done: Implement with tests, a report view, the docs page and a CHANGELOG entry; open the PR

## Summary

detk-norm cpm and tpm with report views, tests, docs and CHANGELOG (PR #40); also fixed detk-norm library and fpkm, which failed on every CLI run. pytest 167 passed, 49 skipped (no R); ruff and mkdocs --strict clean. Found that FPKMCounts never divides by library size (DETK-0006, Proposed, for Adam). crate.py SUBTOOLS touched outside scope.

## Artifacts

## Findings

## Questions

- DETK-0006 Correct the FPKM formula before 1.0

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
