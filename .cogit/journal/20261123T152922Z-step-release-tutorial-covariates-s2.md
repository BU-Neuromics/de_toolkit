---
kind: step
time: 2026-11-23T15:29:22Z
by: DETK/reviewer
node: release/tutorial-covariates
step: s2
branch: review/tutorial-covariates
verdict: approve
commits: []
decisions: []
---

# Approved: Follow the page as a new user would and check the crate entries

## Summary

Approved: all four acceptance items hold. I followed the page as a new user would and ran it with R 4.5.3, DESeq2, airway and mlr 6.22.0 under DETK_TUTORIALS_REQUIRE_ALL=1: 5 passed. Every block's output matches the page: the derived columns (z-score 0.7713... for 126 bases, mean 113.75 and sd 15.88 checked by hand; log2), the failure naming SRR1039516 with no output file and no record, detk-de deseq2's avgLength_zscore and dex__trt__ columns, and the DETK-0050 call-in-formula error. The three Miller programs are the recipes page's programs verbatim. The crate has a CreateAction for each recorded step, with instrument #tool-mlr-mlr%206.22.0 (softwareVersion 'mlr 6.22.0') and sha256 on every file record touched. detk-de's object is ../sample_info.covariates.csv, the result of the last mlr step. trace.py walks it back to Rscript, and the crate validates as process-run-crate-0.5 (rocrate-validator). I checked by hand the page's claim that without the check Miller writes '(error)' and exits 0: it does. The page explains column-names-only (DETK-0050) and links the recipes page and formulas.md, and it is in the tutorials index and the nav, with a CHANGELOG entry. CI on dbe92e8 is all green. 'test with R (bioconda)' ran the page and didn't skip it: tests/tutorials/test_tutorials.py 4 passed, test_covariates.py 3 passed, 2633 passed overall, with REQUIRE_ALL set so a skip would have failed the job. No changes asked.

## Artifacts

## Findings

None blocking. Note: a new user who runs detk-de deseq2 without -q sees detk's INFO log on stderr. That's harmless, and the airway tutorial does the same.

## Questions
