---
kind: step
time: 2026-11-27T19:39:34Z
by: DETK/reviewer
node: release-1-0-1/r-test-skips
step: s2
branch: review/r-test-skips
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: reproduction fails 6/6 on v1.0.0 and skips 6/6 naming the package here; helper pinned with a stub Rscript; R CI job runs all six; README/CHANGELOG in scope of the step

## Artifacts

## Findings

- Reproduction: tests/wrapr/test_missing_r_package_skips.py copied onto v1.0.0 (557da83) fails, its inner run "6 failed" (the six named tests); at 486b38a it passes with "6 skipped", each naming DESeq2 or logistf.
- The helper is pinned with a stub Rscript, no R needed (tests/wrapr/test_r_packages.py, 9 tests incl. the reproduction): names the first missing package, "Rscript is not on PATH" without R, needs_r marker reasons, cache keyed per Rscript path.
- With every package present (CI "test with R (bioconda)", run 46054271156): 2763 passed, 23 skipped; none of the six skipped and no R-package skip reasons appear, so they ran as before.
- Local (no R): 2631 passed, 155 skipped; ruff check and format clean; all 12 PR checks green.
- Scope: code changes are under tests/; README.md (one paragraph pointing new R tests at tests/r_packages.py) and CHANGELOG (1.0.1 Fixed entry) are the docs and CHANGELOG step s1 asked for, accurate, nothing more. No de_toolkit/ change.
- Quickstart test: without R it now runs the non-R steps and their assertions, leaves out the R steps and the steps reading their outputs, then skips naming what was missing (previously it passed silently). That is what the acceptance asks ("they skip, each naming the missing package") and is the more honest signal; DETK_TUTORIALS_REQUIRE_ALL still turns it into a failure in the R job. Accepted, no decision needed.
- Nit, not blocking: NEEDS_R lists SummarizedExperiment for vst/rlog, which matches de_toolkit/transform.py's R code; deseq2's BiocParallel (only with -j) is not listed, fine since the help examples don't use -j.

## Questions
