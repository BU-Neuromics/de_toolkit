---
kind: step
time: 2026-11-20T18:51:08Z
by: DETK/developer
node: release/help-options
step: s1
branch: node/101-help-options
verdict: done
commits: [b88d790]
decisions: []
---

# Done: Make `--rda` (vst, rlog), `--color-col` (summary) and `--blind` (rlog) do what their help says, each with an end-to-end test, the blind vs non-blind rlog comparison in the R job, cli-pin rows; CHANGELOG under Fixed; open the PR

## Summary

Done: --rda (vst, rlog) saves the DESeqTransform via params$rda as detk-de; --color-col colors summary's coldist/colzero/pca views (module JSON color_by + params.color_col; CSV unchanged; unknown COL or no <cov_fn> exit 2); --blind parsed True/False to bool at parse time, invalid exit 2, False without <design>/<cov_fn> exit 2, params record blind and design (~ 1 when blind). End-to-end tests for each; R job ran the blind vs non-blind rlog comparison and the readRDS checks (tests/transform 22 passed, none skipped). cli-pin lines and Bad rows for --blind. CHANGELOG under Fixed. Scope note: small additive edit to de_toolkit/report_specs.py (the summary views live there). PR #105; CI green on b88d790 (all 12 checks incl. R).

## Artifacts

## Findings

## Questions
