---
kind: step
time: 2026-11-28T03:26:19Z
by: DETK/reviewer
node: release-1-0-1/outlier-shrink-axis
step: s2
branch: review/outlier-shrink-axis
verdict: approve
commits: []
decisions: [DETK-1020]
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved at e5880d1. ShrinkCounts applies the PMF transform per feature, across its samples, as --help, the shrink docstring and Labadorf et al. 2015 describe. The reproduction fails on v1.0.0 as stated and passes here. Each acceptance criterion holds, the hand-worked values check out independently, and all CI passes, including test with R (bioconda). One reading needs Adam: DETK-1020 (Proposed) on -p 1.

## Artifacts

## Findings

Reproduction: the PR's test_outlier.py was run against a v1.0.0 worktree. test_shrink_cli_judges_each_feature fails there with g1 written 1.5625 in every sample, as the acceptance states, and test_shrink_cli_shrinks_the_dominant_sample_alone fails too. Both pass here.
Hand values: checked with an independent exact-fraction (Fraction) implementation of the method, not the PR's code. 1,1,1,300 at p_max 0.5 gives 1,1,1,2.16796875. 10,12,11,301 gives 30.0625. 0,0,1,10 at p_max 0.25, 0,0,10,10 at 0.3 and 0,0,0,40 at 0.5 each reach a point with no non-outlier holding counts, so they are written as read. 10x4 is unchanged. All match the tests. The 300->301 change in the #219 tests is justified: 10,12,11,300 shrinks to exactly 30.0, which would no longer show a fractional result.
Acceptance: the per-feature fix holds. The single-sample feature is unchanged with a WARNING giving the count (DETK-0861 A). -p below 1/n exits 2 naming the bound, and the Python shrink/pmf_transform raise ValueError. pmf_transform no longer prints. Tests are checked against per-feature hand calculations. CHANGELOG 1.0.1 has the entry under Behaviour changes with DETK-0600 reasoning. docs/tools/outlier.md is updated.
Checks: full suite 2895 passed, 160 skipped (R-gated). ruff check and ruff format clean. PR CI all green at e5880d1, including test with R (bioconda), docs build (strict) and py3.11-3.13. The PR is mergeable.
Flagged choice (a), -p 1 accepted (range [1/n, 1]): sound. At n=1 the default sqrt(1)=1 = 1/n, so DETK-0861's '(0, 1)' wording would refuse every one-sample input by default. p_max=1 shrinks nothing and is harmless; a one-sample file runs, exit 0, output = input. This departs from an Accepted decision's literal text, so it is recorded as DETK-1020 (Proposed, recommending Option A: accept as written) for Adam. No code change either way unless B is chosen.
Flagged choice (b), a feature whose last over-p_max sample is pushed under mid-run is written as read: within DETK-0861 A ('the feature is written as read'), no ruling needed. It is the principled reading. A feature whose nonzero samples are fewer than 1/p_max can never meet p_max, so the result does not depend on how far shrinking got before it stopped, and the WARNING's count stays honest ('left unchanged').
Scope: de_toolkit/completions/detk.zsh is outside the listed scope. It is the generated completion for the changed -p help text, required by tests/completion, and earlier nodes added it the same way. Accept it as-is.
Nits, not blocking: the Python shrink(p_max=0) falls back to the default through 'p_max or ...' (an older pattern; the CLI rejects -p 0). The count of features left unchanged goes to the log only, not to the module JSON or report properties. The acceptance asks only for the log. The 'counts removed by shrinking' log line now has the right sign (it was negative on 1.0.0).

## Questions

- DETK-1020 detk-outlier shrink accepts -p 1: the range is 1 / number of samples to 1

The step is not ticked: a Proposed record blocks its node until the human answers it (ADR 0055).
