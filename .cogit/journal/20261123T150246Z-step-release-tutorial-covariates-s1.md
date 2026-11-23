---
kind: step
time: 2026-11-23T15:02:46Z
by: DETK/developer
node: release/tutorial-covariates
step: s1
branch: node/153-tutorial-covariates
verdict: done
commits: [9b275cc]
decisions: []
---

# Done: Write the page with its checked outputs and crate check, index and nav; CHANGELOG; open the PR

## Summary

docs/tutorials/covariates.md: airway data with avgLength (data step recorded with detk-util record), constant column, z-score and log2 of avgLength through the Miller recipes and detk-util record, the log recipe failing on an NA naming SRR1039516 with no output left, detk-de deseq2 with cell + avgLength_zscore + dex[untrt], a call in a formula shown failing (DETK-0050), and the crate traced from detk-de's inputs back to mlr (with version) and R with checksums. Explains column-names-only, links recipes page and formulas.md. tests/tutorials/test_covariates.py checks derived columns against numpy and the records. Index, nav, CHANGELOG. Runs green locally with R 4.5.3 + DESeq2 + airway + mlr 6.22.0 (5 tests); skips without them; mkdocs build --strict passes; full pytest 2503 passed. No decisions needed.

## Artifacts

## Findings

## Questions
