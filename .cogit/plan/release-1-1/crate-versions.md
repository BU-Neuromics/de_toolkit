---
kind: task
objective: each R-backed step's crate action names the R version and the version of each R/Bioconductor package it loaded (DESeq2, fgsea, logistf, BiocParallel ...), as SoftwareApplication entities
acceptance:
  - 'reproduced first as a test: on v1.0.0 the crate of a detk-de deseq2 run names detk but neither R nor DESeq2''s version. After: the action''s instrument lists R and DESeq2 with versions read from the R session that ran, and the crate still validates'
  - docs/report.md and CHANGELOG 1.1
scope: [de_toolkit/wrapr.py, de_toolkit/crate.py, tests/report/, +docs/report.md, +CHANGELOG]
---

# The crate names R and the Bioconductor package versions

## Implementation plan

## Notes
