---
kind: task
objective: detk-outlier shrink works on an integer counts matrix, the usual input, and writes float counts
acceptance:
  - 'reproduced first: on v1.0.0, ''detk-outlier shrink counts.csv'' on any integer matrix where a count is shrunk exits 1 with "Invalid value ''[...]'' for dtype ''int64''" (pandas refusing a float into an int column, PMFTransform.__init__); the same matrix written with decimals runs. A test shows it, and after both exit 0 with the same float output'
  - pmf_transform and shrink called from Python with integer counts work too; the output is float (shrunk counts are fractional, as the float input's run already shows), and docs/tools/outlier.md and the shrink and pmf_transform docstrings say so; CHANGELOG 1.0.1 under Fixed
prev: [release-1-0-1/count-checks-readers]
scope: [de_toolkit/outlier.py, tests/outlier/, +docs/tools/outlier.md, +CHANGELOG]
---

# detk-outlier shrink takes integer counts

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Found by the count-checks-readers session, whose tests feed `detk-outlier
shrink` a decimal matrix (`TRANSFORMED_OK` in
tests/common/test_readers_count_checks.py, PR #203) to get past it.
Reproduced by the plan session, 2026-11-27, on a v1.0.0 install:
`gene,A,B,C,D / g1,10,12,11,300 / ...` exits 1 with
`Invalid value '[32.5]' for dtype 'int64'` at `count_obj[p_count_outliers] = ...`
in `PMFTransform.__init__`; the same counts with `.5` added run. Cast to
float before shrinking. Waits on count-checks-readers, which edits shrink's
reader in the same file; with this fix that test may use integer counts.

Seen while reproducing, not this node's fix: `ShrinkCounts` applies
`pmf_transform` with `DataFrame.apply`'s default axis, so each call gets a
sample's column and `p_max` is a fraction of the sample's counts, not of
the feature's as `--help` says ("Largest fraction of a feature's counts one
sample may hold"). On v1.0.0, a feature with 10 in every one of four samples
(beside three features of 1) is shrunk to 1.5625 in all four. Reported to
Adam with this plan; not planned here.
