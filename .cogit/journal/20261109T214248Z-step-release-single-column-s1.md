---
kind: step
time: 2026-11-09T21:42:48Z
by: DETK/developer
node: release/single-column
step: s1
branch: node/47-single-column
verdict: done
commits: [b725767, e8cf7de]
decisions: [DETK-0020]
---

# Done: Fix it with tests and a CHANGELOG entry; open the PR

## Summary

Every reader that sniffed the delimiter with sep=None (read_id_table in common.py; annotate's result and mapping and tidy-counts/tidy-covs in util.py; the fgsea result in enrich.py) now goes through common.read_delimited, which sniffs the first line for comma, tab, semicolon, pipe or space only and reads a line with none as one column (DETK-0020). gather reads with sep='\t' and never sniffed. tests/common/test_read_delimited.py covers id and gene_id one-column files with and without a header across read_delimited, read_id_table, annotate, tidy-counts and fgsea's reading, plus comma/tab/semicolon regressions; the one-column CLI tests fail on the previous code. pytest 344 passed/49 skipped, ruff check and format clean, mkdocs --strict builds. CHANGELOG entry under 1.0.0 Fixed. Done: the acceptance holds.

## Artifacts

## Findings

## Questions
