---
kind: step
time: 2026-11-27T22:33:28Z
by: DETK/developer
node: release-1-0-1/lineage-test
step: s1
branch: node/207-lineage-test
verdict: done
commits: [f8398e2]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Added tests/report/test_lineage.py: filter -> deseq2 -> fgsea -c chain in one report dir, crate validated, lineage walked to counts.csv and sample_info.csv. Fails on v1.0.0 (traces back to ../sets.gmt only), passes on main with R. Skips naming DESeq2/fgsea. Docs (report.md) and CHANGELOG 1.0.1 Fixed.

## Artifacts

## Findings

## Questions
