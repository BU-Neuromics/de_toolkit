---
kind: step
time: 2026-11-27T23:01:02Z
by: DETK/reviewer
node: release-1-0-1/lineage-test
step: s2
branch: review/lineage-test
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: lineage test fails on v1.0.0 for the stated reason, passes here and in the R CI job; acceptance holds; scope as expected

## Artifacts

## Findings

- Reproduction confirmed without R: ran the test's CHAIN in-process with DESeq2Counts/FGSEARes stubbed, against v1.0.0 and this head, then the PR's assert_traces_back. v1.0.0: fgsea action object is ['../sets.gmt'] only and the assertion fails with "../gsea.csv does not trace back to ['../counts.csv', '../sample_info.csv']; it traces back to ['../sets.gmt']". Head: fgsea object ['../sets.gmt', '../de.csv'], walk passes. -c/--statcol existed on v1.0.0, so the chain runs there and fails for the lineage reason, not a CLI one.
- R CI ('test with R (bioconda)', run 46077399940) passed: tests/report/test_lineage.py 4 passed, none skipped; the R test ran the Process Run Crate validator (2818 passed, 23 skipped overall). All other checks green (3.11/3.12/3.13, ruff, docs strict, runtime deps only, coverage, CodeQL).
- Locally (no R): 3 R-free tests pass, the R test skips with 'Rscript is not on PATH' via needs_r('DESeq2', 'fgsea'), which names the first missing package when Rscript is present, as r-test-skips does. ruff check/format clean.
- Acceptance 1: counts.csv -> detk-filter -> detk-de deseq2 with sample_info.csv -> detk-enrich fgsea -c group__b__stat in one working dir/report; crate validated; walk follows result -> action -> object to counts.csv and sample_info.csv and asserts the action path (fgsea, deseq2, filter). Acceptance 2: holds as above.
- Scope: code change only in tests/report/test_lineage.py; docs/report.md (one sentence) and the CHANGELOG 1.0.1 Fixed entry are outside tests/report/ but are what s1 asks for (docs and a CHANGELOG entry). Nothing else changed.
- Nits, no change asked: the validator importorskip comes after the R chain runs (same pattern as test_crate.py); a test-only addition sits under 'Fixed' in the CHANGELOG, which reads acceptably since it documents the #199 fix.

## Questions
