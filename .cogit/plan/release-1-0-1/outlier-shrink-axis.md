---
kind: task
objective: detk-outlier shrink compares each sample's count with the feature's total across the samples, as --help and the shrink docstring (Labadorf et al. 2015) describe, not with the sample's total across features
acceptance:
  - 'reproduced first: on v1.0.0, a decimal counts file (integer input fails until outlier-shrink-int) with g1 = 10.0 in all four samples A-D beside g2-g4 = 1.0 everywhere: ''detk-outlier shrink'' (p_max = sqrt(1/4) = 0.5) writes g1 = 1.5625 in every sample, because each sample''s g1 is 10/13 of that sample''s counts. A test shows it; after, g1 is unchanged (each sample holds 1/4 of g1), and a feature where one sample holds more than p_max of its counts, e.g. 1, 1, 1, 300, is shrunk in that sample alone, the others unchanged'
  - 'a feature counted in only one sample and a -p below 1 / number of samples behave as DETK-0861 decides, with a test each; shrink''s tests are checked against a per-feature hand calculation; CHANGELOG 1.0.1 under Behaviour changes: shrink''s results change for every input, a silent wrong answer fixed under DETK-0600''s reasoning'
from: [DETK-0600, DETK-0861]
prev: [DETK-0861, release-1-0-1/outlier-shrink-int, DETK-1020]
scope: [de_toolkit/outlier.py, tests/outlier/, +docs/tools/outlier.md, +CHANGELOG]
issue: 226
visited: 873d65c
---

# detk-outlier shrink judges each feature across its samples

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Seen by the plan session while reproducing outlier-shrink-int and added on
the driver's direction, 2026-11-27. On v1.0.0 (and main at 2bac95c)
`ShrinkCounts` calls `count_obj.counts.apply(pmf_transform, ...)` with
`DataFrame.apply`'s default axis, so `pmf_transform` gets one sample's
column and `p_count = count_obj / count_obj.sum()` is a fraction of that
sample's counts. `--help` ("one sample holds more than a given fraction of
the feature's counts"), the `-p` help and the `shrink` docstring ("For
each feature ... divide each sample count by the sum of counts") all mean
per feature: `axis=1`. `PMFTransform`'s own default `sqrt(1 / len(...))` is
then the number of samples, as `main()` already computes.

Reproduced on v1.0.0 with
`gene,A,B,C,D / g1,10.0,10.0,10.0,10.0 / g2..g4,1.0,1.0,1.0,1.0`:
every g1 written as 1.5625. Per feature, the method zeroes a feature whose
counts are all in samples over `p_max` and crashes on `-p` below 1/n:
DETK-0861 (accepted 2026-11-27) settles both: such a feature is left
unchanged and counted in the log, and `-p` below 1/n is a usage error, exit 2. After
outlier-shrink-int, which fixes the integer input in the same function;
every shrink result changes, so the existing tests' expected values are
recomputed by hand, per feature, not copied from the new output.
