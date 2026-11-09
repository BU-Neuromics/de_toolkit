---
kind: step
time: 2026-11-09T22:42:42Z
by: DETK/developer
node: release/r-ids
step: s1
branch: node/67-r-ids
verdict: done
commits: [542893b, 55f96bd]
decisions: []
---

# Done: Read IDs and sample names as text at the R boundary (the R scripts in de.py and transform.py, wrapr's read-back) and in enrich and the tidy commands; R-gated round-trip tests; CHANGELOG; open the PR

## Summary

IDs and sample names kept as written through the R-backed commands (read.id.csv in wrapr's template; deseq2, firth, vst and rlog read counts and metadata as text; wrapr reads R's output back as text), detk-enrich fgsea and detk-util tidy-counts/tidy-covs (PR #68). Non-blind rlog no longer passes counts and Intercept to DESeq2, a bug the new test was first to run. The agent skill's ID paragraph is updated. CI's R job: 412 passed, 5 skipped, the six R-gated round-trip tests (007, 010, 1.10, 1.1; samples 001-006) among the passed.

## Artifacts

## Findings

## Questions
