---
kind: task
objective: with Rscript on PATH but DESeq2, logistf or another needed package missing, the tests that need it skip naming the package instead of failing
acceptance:
  - 'reproduced first: with an Rscript whose library lacks DESeq2 and logistf (has fgsea and jsonlite), v1.0.0''s suite fails six tests: test_cli_help_sections::test_examples_run_where_test_data_allows[detk-de-deseq2, detk-de-firth, detk-transform-vst, detk-transform-rlog], test_docs_commands::test_quickstart_runs_as_written and test_record::test_lineage_into_detk_de. After: they skip, each naming the missing package; a test pins the skip helper with a stub Rscript, so it needs no R'
  - with every package present they run as before (the R CI job)
scope: [tests/]
---

# R tests skip when an R package they need is missing

## Implementation plan

## Notes
