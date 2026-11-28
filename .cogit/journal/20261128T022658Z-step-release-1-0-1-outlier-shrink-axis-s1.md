---
kind: step
time: 2026-11-28T02:26:58Z
by: DETK/developer
node: release-1-0-1/outlier-shrink-axis
step: s1
branch: node/226-outlier-shrink-axis
verdict: done
commits: [c51bc8a, d611106]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

ShrinkCounts now applies the PMF transform per feature (row) across its samples, as --help, the shrink docstring and Labadorf et al. 2015 say; on 1.0.0 pandas' default apply axis judged each sample's count against the sample's total across features. Reproduction (tests/outlier/test_outlier.py: test_shrink_cli_judges_each_feature, test_shrink_cli_shrinks_the_dominant_sample_alone) run against a v1.0.0 worktree: g1 = 10.0 in A-D beside g2-g4 = 1.0 is written 1.5625 in every sample; both fail there and on main, pass here (g1 unchanged; 1,1,1,300 -> 1,1,1,2.16796875 in D alone, by hand). DETK-0861 Option A: a feature whose counts are all in samples over p_max (incl. one counted in a single sample, and one where shrinking brings the last non-outlier over p_max mid-way) is written as read, with a WARNING giving the count; -p below 1/n or above 1 exits 2 naming the bound; shrink/pmf_transform raise ValueError; pmf_transform no longer prints to stdout. Readings recorded in the PR: p_max = 1 is accepted (shrinks nothing; DETK-0861 says 'outside (0, 1)', but with one sample 1/n = 1 is the default); the #219 tests' g1 D changed 300 -> 301 so its shrunk count stays fractional (30.0625 by hand). The inner loop is numpy (20k x 10 in 1.3 s vs 4.4 s with pandas per feature). docs/tools/outlier.md, CHANGELOG 1.0.1 Behaviour changes (DETK-0600 reasoning), and de_toolkit/completions/detk.zsh regenerated for the -p help (outside the listed scope; generated, required by tests/completion). Full suite: 2868 passed, 1 failed before the completion regen (that one), ruff and mkdocs --strict clean.

## Artifacts

## Findings

## Questions
