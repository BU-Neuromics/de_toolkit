---
kind: step
time: 2026-11-27T23:15:48Z
by: DETK/developer
node: release-1-0-1/crate-inputs
step: s1
branch: node/209-crate-inputs
verdict: done
commits: [9cb2be0, cc6abff]
decisions: [DETK-0890]
---

# Done: Write the reproduction tests of the first acceptance criterion and confirm they fail on v1.0.0; then fix, with a CHANGELOG entry under 1.0.1; open the PR

## Summary

Every file a command read or wrote is in its crate action: annotate mapping (#45), gather files, rlog cov_fn, vst/rlog --rda, entropy --plot-output, norm --size-factors and fpkm/tpm lengths; reproduction fails 11/13 on v1.0.0 (filter/stats already record cov_fn; outlier reads none); CHANGELOG 1.0.1; DETK-0890 Proposed (de/enrich --rda, docs/report.md)

## Artifacts

## Findings

## Questions

- DETK-0890 Which crate-inputs gaps outside its scope this node closes (#212)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
