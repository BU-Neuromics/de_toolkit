---
kind: step
time: 2026-11-27T20:40:49Z
by: DETK/reviewer
node: release-1-0-1/sample-match
step: s2
branch: review/sample-match
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: reproduction fails on v1.0.0 (22 of the 27 new tests, run against the v1.0.0 tree) and all pass here; the check is in CountMatrix with every sample-information command pinned; reorder allowed, --strict kept; stats fixtures faithful; R CI ran all 27 and every tutorial; diff within scope

## Artifacts

## Findings

Checked at dab8c0f (PR #198).
- Reproduction: tests/cli/test_sample_match.py run against a v1.0.0 worktree: 22 failed, 3 passed (the reorder tests, which hold on 1.0.0 too), 2 skipped (DESeq2, no R locally). The R-free commands (detk-filter, detk-stats summary/pca, detk-wrapr run) show the silent subset on v1.0.0; the DESeq2 audit case is R-gated and ran (passed) in 'test with R (bioconda)', while its v1.0.0 exit 0 rests on the plan session's reproduction at 75aacb3.
- Here: full suite 2656 passed, 157 skipped locally; CI green on every job; the R job ran 2790 passed, 23 skipped, all 27 sample-match tests and every tutorial (DETK_TUTORIALS_REQUIRE_ALL=1).
- Acceptance 1: exit 1, no output file, one 'detk-de: error: ...' line naming 008 (counts only) and 999 (sample information only); extra/missing in either file covered; long lists cut to five plus 'and N more'.
- Acceptance 2: reorder gives equal output (filter, stats pca; deseq2 under R); --strict refuses a reorder with a 'same order' message and checks the sets first.
- Acceptance 3: the check is in CountMatrix.__init__, which every command reaches (make_cli_count_obj / CountMatrixFile); pinned for detk-de deseq2 and firth, detk-transform rlog (the only transform with a design), detk-filter, detk-stats summary and pca, and detk-wrapr run --meta-in. detk-outlier and detk-norm take no sample information.
- Acceptance 4: docs/concepts.md and CHANGELOG 1.0.1 'Behaviour changes' say what the ticket asks, including CountMatrix(subset=True) for Python callers.
- tests/stats/test_stats.py: faithful. The local fake_column_data lists samples a-t, more than any counts table there; the old fixtures got 1.0.0's silent intersection through CountMatrixFile, and the new make_subset_obj asks for the same intersection explicitly (read_id_table + CountMatrix subset=True, which is what CountMatrixFile does). No assertion changed; only the fixtures. tests/common/test_common.py now asserts the error and drops the extra sample before its old not-strict checks, also not weaker.
- DETK-0700: util.py changes one line (Tidy passes subset=True); tests/util/test_tidy.py is unchanged and passes, so tidy's subsetting is pinned.
- Scope: code changes only in de_toolkit/common.py, de_toolkit/util.py, tests/, docs/concepts.md, CHANGELOG (+ .cogit records).
- Nits, no change asked: the --strict help texts (de, transform, wrapr) still read as if strict were what makes the sets match; still true, now redundant on that point. The 'fewer than 2 in common' branch is now reached only with subset=True or a sheet of under two samples.

## Questions
