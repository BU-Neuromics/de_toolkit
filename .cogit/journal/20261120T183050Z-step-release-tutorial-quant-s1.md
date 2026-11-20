---
kind: step
time: 2026-11-20T18:30:50Z
by: DETK/developer
node: release/tutorial-quant
step: s1
branch: node/100-tutorial-quant
verdict: done
commits: [a9b38b0]
decisions: []
---

# Done: Write the data script and data, the page with its checked outputs and the TPM check, index and nav; CHANGELOG; open the PR

## Summary

docs/tutorials/quantifiers.md (gather, tidy, cpm, tpm, plog, stats summary, report, crate; no R) with checked outputs; data in docs/tutorials/data/quantifiers/ from the seeded stdlib-only simulate.py; tests/tutorials/test_quantifiers.py checks TPM against a direct computation and salmon's TPM column, and that simulate.py rewrites the data byte for byte; index row, nav, CHANGELOG. Decisions within the node: the data sit in docs/tutorials/data/quantifiers/ (not docs/tutorials/quantifiers/, which would share the page's URL) and are served on the site; the simulation uses only random.Random.random() with its own normal and Poisson draws so it does not depend on numpy's stream; one effective length per transcript across samples, so detk's TPM equals salmon's; the sample-sheet step drops a pilot library (P1) from the counts, and uses tidy without -p, since tidy's -p output carries a stray counts column (reported, outside this node's scope); P1 rather than 'pilot' so ls order does not depend on the locale.

## Artifacts

## Findings

## Questions
