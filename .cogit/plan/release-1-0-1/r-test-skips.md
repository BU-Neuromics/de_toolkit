---
kind: task
objective: with Rscript on PATH but DESeq2, logistf or another needed package missing, the tests that need it skip naming the package instead of failing
acceptance:
  - 'reproduced first: with an Rscript whose library lacks DESeq2 and logistf (has fgsea and jsonlite), v1.0.0''s suite fails six tests: test_cli_help_sections::test_examples_run_where_test_data_allows[detk-de-deseq2, detk-de-firth, detk-transform-vst, detk-transform-rlog], test_docs_commands::test_quickstart_runs_as_written and test_record::test_lineage_into_detk_de. After: they skip, each naming the missing package; a test pins the skip helper with a stub Rscript, so it needs no R'
  - with every package present they run as before (the R CI job)
scope: [tests/]
issue: 187
visited: 557da83
---

# R tests skip when an R package they need is missing

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; with an R (conda) holding fgsea and
jsonlite but not DESeq2 or logistf, `pytest tests/cli tests/docs tests/util
tests/tutorials tests/recipes tests/report` gave exactly these 6 failures
(2085 passed, 84 skipped); tests/de, norm, transform, enrich and wrapr
already skip per package (`DESeq2 package not installed, skipping test`).
Reuse that check in a shared fixture or marker.
