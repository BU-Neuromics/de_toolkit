---
kind: task
objective: docs/quickstart.md says, beside its detk-de deseq2 example, that detk takes the Wald coefficients with no independent filtering and no Cook's cutoff, so padj differs from a default DESeq2 vignette run
acceptance:
  - 'reproduced first as a test in tests/docs: the quickstart names neither independent filtering nor Cook''s distance on v1.0.0; after, it names both by the deseq2 example and links docs/tools/de.md, which states the matched results() settings'
scope: [docs/quickstart.md, tests/docs/, +CHANGELOG]
---

# The quickstart states how detk's DESeq2 differs from a default results() call

## Implementation plan

## Notes
