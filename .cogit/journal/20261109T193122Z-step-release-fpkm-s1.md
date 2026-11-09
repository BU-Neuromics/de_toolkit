---
kind: step
time: 2026-11-09T19:31:22Z
by: DETK/developer
node: release/fpkm
step: s1
branch: node/50-fpkm
verdict: done
commits: [10d9ca4]
decisions: []
---

# Done: Fix the formula, the test and the CHANGELOG; open the PR

## Summary

FPKMCounts now computes count * 1e9 / (length * library size) (DETK-0006 Option A) and takes lengths through _lengths_for, so missing, zero and negative lengths are refused as in tpm. test_fpkm asserts hand-worked values (e.g. 3 counts, 2000 bp, library 4 -> 375,000); new tests for the refusals, an all-zero sample and the CLI values. docs/tools/norm.md gives the formula and length rules; CHANGELOG notes under 1.0.0 Changed that fpkm output differs from 0.9.x as a correction. Checks: uv sync, pytest (184 passed, 49 skipped), ruff check, ruff format --check, mkdocs build --strict all pass.

## Artifacts

## Findings

## Questions
