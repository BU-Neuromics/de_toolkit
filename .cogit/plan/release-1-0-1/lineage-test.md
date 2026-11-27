---
kind: task
objective: a regression test follows the crate's edges from an fgsea table back to the counts and sample information files it came from
acceptance:
  - the test runs counts.csv -> detk-filter -> detk-de deseq2 (with sample_info.csv) -> detk-enrich fgsea -c in one report directory, validates the crate with the Process Run Crate validator, and walks result -> action -> object edges from the fgsea table to counts.csv and sample_info.csv; it fails on v1.0.0 (no fgsea -> DE edge) and passes once fgsea-input and run-identity are in
  - it runs in the R CI job and skips, naming the package, where DESeq2 or fgsea is absent (as r-test-skips makes the others)
scope: [+tests/report/]
---

# Test that an enrichment table traces back to its counts and sample information

## Implementation plan

## Notes
