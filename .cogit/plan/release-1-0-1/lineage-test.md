---
kind: task
objective: a regression test follows the crate's edges from an fgsea table back to the counts and sample information files it came from
acceptance:
  - the test runs counts.csv -> detk-filter -> detk-de deseq2 (with sample_info.csv) -> detk-enrich fgsea -c in one report directory, validates the crate with the Process Run Crate validator, and walks result -> action -> object edges from the fgsea table to counts.csv and sample_info.csv; it fails on v1.0.0 (no fgsea -> DE edge) and passes once fgsea-input and run-identity are in
  - it runs in the R CI job and skips, naming the package, where DESeq2 or fgsea is absent (as r-test-skips makes the others)
scope: [tests/report/]
prev: [release-1-0-1/fgsea-input, release-1-0-1/run-identity, release-1-0-1/r-test-skips]
issue: 207
visited: c490c55
status: done
done: 9a87c92
---

# Test that an enrichment table traces back to its counts and sample information

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Adam's direction
(2026-11-27): "Add a lineage regression test (enrichment table traces back
to counts and metadata)". It fails on 1.0.0 because the fgsea action has no
edge to the DE results (see fgsea-input). The release CI job of
release-1-1/wheel-ci reuses its assertions.
