---
template: adr
state: Proposed
authority: [human]
date: 2026-11-27
from: {node: release-1-0-1/outlier-shrink-axis}
applies: [release-1-0-1/outlier-shrink-axis]
issue: 211
---

# What detk-outlier shrink does with a feature counted in one sample, and a p_max below 1/n

## Background

`detk-outlier shrink` implements the outlier count shrinkage of Labadorf et
al., PLoS ONE (2015): for each feature (gene), a sample holding more than a
fraction `p_max` of the feature's counts across the samples is shrunk toward
the largest sample under `p_max` by the shrink factor, repeated until no
sample is over. `p_max` is `-p`, by default sqrt(1 / number of samples).
release-1-0-1/outlier-shrink-axis makes the code do this per feature (on
1.0.0 it judges each sample's count against the sample's total across
features). Applied per feature, two cases the paper's description does not
settle become common, and the code's literal reading is bad in both.

## Context

Tried by the plan session, 2026-11-27, calling `pmf_transform` on single
features (a feature's counts across four samples, `p_max` 0.5, shrink factor
0.25):

- `10, 10, 10, 10` stays as it is; `1, 1, 1, 300` becomes `1, 1, 1, 2.168`;
  `0, 0, 5, 40` becomes `0, 0, 5, 5`. These are the method as described.
- `0, 0, 0, 40` becomes `0, 0, 0, 0`: the only sample with counts is over
  `p_max`, the largest other sample is 0, so the count is shrunk toward 0
  until it underflows ("all samples set to zero, returning" printed to
  stdout). The same happens whenever every sample with counts is over
  `p_max` (`0, 0, 0, 10, 10` with five samples). Features seen in one
  sample are common in real counts, so per-feature shrinking would turn
  many of them into all-zero rows, deleting their counts.
- `p_max` below 1 / number of samples (`-p 0.2` with four samples): a
  feature with equal counts has every sample over `p_max`, no sample is
  left to shrink toward, and the run fails with `ValueError: max() iterable
  argument is empty`, exit 1, naming nothing. At `p_max` >= 1/n some sample
  is always at or under it, since the fractions sum to 1.
- Criteria: no silent wrong answer (DETK-0600); a feature's counts are not
  deleted by a step meant to damp one sample; a bad option is a usage error
  (as DETK-0200 did for entropy's `-p`); no option added (DETK-0001).

## Options

### Option A: leave such a feature unchanged; refuse p_max below 1/n

When no sample under `p_max` has counts (the largest non-outlier is 0),
there is nothing to shrink toward: the feature is written as read, and the
log names how many features were left so. `-p` below 1 / number of samples
(or outside (0, 1)) is a usage error, exit 2, naming the bound. The method
is applied where it is defined; nothing is deleted.

### Option B: follow the literal algorithm

Shrink toward 0, so these features become all zeros, and document it; make
`p_max` below 1/n a usage error as in A. Literal to the code, but deletes
counts silently from features that are, for the most part, real
single-sample expression, which the entropy subcommand exists to flag, not
remove.

### Option C: leave unchanged, and clamp p_max to 1/n

As A for the features, but a `-p` below 1/n is raised to 1/n with a
warning. Keeps a run going where A stops it, at the cost of running with a
value the user did not give.

## Decision

Recommended: **Option A**. A feature with no other sample holding counts
has no target to shrink toward, so leaving it is the method's own limit, not
a new rule; deleting its counts (B) would be a new silent wrong answer in
the fix for one. A `p_max` no feature can satisfy is a mistake on the
command line, which DETK-0031 makes exit 2. Proposed by the plan session,
2026-11-27, for Adam to accept or reject; release-1-0-1/outlier-shrink-axis
waits on it.

## Consequences

- Under A: `PMFTransform` stops when the largest non-outlier count is 0
  (and no longer prints to stdout); `main()` checks `-p` against
  1 / number of samples after reading the counts; `--help`'s `-p` line and
  docs/tools/outlier.md say both; CHANGELOG 1.0.1 under Behaviour changes
  with the per-feature fix.
- The Python functions `shrink` and `pmf_transform` raise `ValueError`
  naming the bound for such a `p_max`, as the CLI's check does.
- Revisit if users want single-sample features damped (e.g. toward a
  pseudocount): that would be a new option, for release-1-1.
