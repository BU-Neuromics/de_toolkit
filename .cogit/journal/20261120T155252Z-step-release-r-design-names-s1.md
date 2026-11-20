---
kind: step
time: 2026-11-20T15:52:52Z
by: DETK/developer
node: release/r-design-names
step: s1
branch: node/94-r-design-names
verdict: done
commits: [7b54958]
decisions: []
---

# Done: Add the R-bound design form with quoting to the formula module, use it at every R `formula()` site, add the call-shaped-name tests (R-gated) and the dotted-name regression test; CHANGELOG; open the PR

## Summary

formula.r_design backtick-quotes every non-syntactic or reserved name in the resolved design; used at every R formula() site (de deseq2/firth, transform rlog, norm deseq2_wrapr; vst has no design); R-gated tests with a file.create(1) column (nothing runs) and fld.cont; CHANGELOG

## Artifacts

## Findings

## Questions
