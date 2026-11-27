---
kind: step
time: 2026-11-27T22:28:49Z
by: DETK/reviewer
node: release-1-0-1/count-checks-readers
step: s2
branch: review/count-checks-readers
verdict: changes
commits: []
decisions: [DETK-0850]
---

# Changes asked: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Changes asked: the code meets both acceptance criteria and stays in scope, but docs/concepts.md and the CHANGELOG 1.0.1 entry say every command that reads counts runs the check, and detk-util tidy/tidy-counts/tidy-covs and detk-wrapr run do not (detk-util tidy-counts still drops a repeated header silently on c9cdf4b). Narrow the wording; the follow-up is DETK-0850 (Proposed). One wording nit in the concepts.md table.

## Artifacts

## Findings

1 (change asked). docs/concepts.md ('Every command that reads a counts matrix checks it as read') and CHANGELOG 1.0.1 ('Every other command that reads a counts matrix runs the same check'; 'now exits 1 in every command') overstate the change. detk-util tidy, tidy-counts and tidy-covs (util.py _tidy_main reads with read_id_table) and detk-wrapr run (wrapr.py CountMatrixFile without check) do not check. Reproduced on c9cdf4b: detk-util tidy-counts on gene,A,A,B,C with column data A,B,C exits 0, writes gene,A,B,C and logs only 'counts columns lost: 1'. util.py and wrapr.py are outside this node's scope, so do not fix them here. Name the commands that check (norm, de, transform, stats, filter, outlier) and say detk-util tidy* and detk-wrapr run are not checked yet (follow-up per DETK-0850, Proposed, recommended option A: a separate node). 2 (nit). The concepts.md table header says 'Needs raw counts (all four checks)', but the list above it has five: repeated header, repeated feature ID, negative count, no numeric value, zero depth. Say 'all the checks' or 'five'. Verified: reproduction tests/common/test_readers_count_checks.py fails on v1.0.0 in 66 cases (48 duplicate, 18 raw-value) and passes here. For the R commands (de deseq2, transform vst/rlog) the v1.0.0 failure here is 'Rscript not found', not acceptance; that 1.0.0 accepts is inferred from the CountMatrixFile path, which 1.0.0 shares for the Python commands. Full suite here: 2799 passed, 157 skipped. ruff check and format clean. CI is green on c9cdf4b, including 'test with R (bioconda)'. The diff touches only the node's scope; common.py is limited to check_counts, make_cli_count_obj and CountMatrixFile per DETK-0830, and CountMatrix.__init__ is untouched. The split is sound: detk-de firth uses counts as a predictor and detk-transform plog logs any non-negative matrix, so both may take normalized input, and putting them with the transformed commands is right. Note (no change asked): plog on a value below -pseudocount gives NaN without a word; that is pre-existing and not in this node's acceptance.

## Questions

- DETK-0850 The count checks in detk-util tidy and detk-wrapr run (#206)

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
