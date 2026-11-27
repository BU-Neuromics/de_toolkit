---
kind: task
objective: each R-backed step's crate action names the R version and the version of each R/Bioconductor package it loaded (DESeq2, fgsea, logistf, BiocParallel ...), as SoftwareApplication entities
acceptance:
  - 'reproduced first as a test: on v1.0.0 the crate of a detk-de deseq2 run names detk but neither R nor DESeq2''s version. After: the action''s instrument lists R and DESeq2 with versions read from the R session that ran, and the crate still validates'
  - docs/report.md and CHANGELOG 1.1
scope: [de_toolkit/wrapr.py, de_toolkit/crate.py, tests/report/, +docs/report.md, +CHANGELOG]
prev: [release-1-0-1/crate-inputs]
---

# The crate names R and the Bioconductor package versions

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.1 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.1.0; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.1 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the audit: "the crate also lacks R and Bioconductor package versions".
Confirmed on main: the crate's SoftwareApplication entities are the detk
tools, with no version and nothing for R.
