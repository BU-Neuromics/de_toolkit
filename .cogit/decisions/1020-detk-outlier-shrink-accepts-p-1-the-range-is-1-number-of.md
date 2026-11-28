---
template: adr
state: Accepted
authority: [human]
date: 2026-11-28
from: {node: release-1-0-1/outlier-shrink-axis, step: s2}
applies: [release-1-0-1/outlier-shrink-axis]
revisions:
  - {date: 2026-11-28, by: adamlabadorf, change: Accepted, why: "from the terminal: Option A (accept 1 / number of samples to 1, inclusive, as PR #227 does), accepted under Adam's delegation via the driver session, 2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27"}
---

# detk-outlier shrink accepts -p 1: the range is 1 / number of samples to 1

## Background

`detk-outlier shrink -p` (`p_max`) is the largest fraction of a feature's
counts one sample may hold before it is shrunk; by default it is
sqrt(1 / number of samples). DETK-0861 (Accepted) made `-p` below
1 / number of samples a usage error, exit 2, and its Option A also says
"(or outside (0, 1))". The fix in release-1-0-1/outlier-shrink-axis
(PR #227) accepts `-p` from 1 / number of samples to 1 inclusive, so
`-p 1` runs. This record asks Adam to confirm that reading.

## Context

- With one sample, 1 / n = 1 and the default sqrt(1/1) = 1. Read literally,
  "outside (0, 1)" makes every one-sample input a usage error, even with no
  `-p` given. Both of DETK-0861's bounds can't hold at n = 1, so its text
  contradicts itself there.
- `p_max = 1` is well defined: a sample's fraction can never be over 1, so
  nothing is shrunk and the counts are written as read (checked by the
  reviewer: a one-sample file runs, exit 0, output equals input). It is
  harmless, not a silent wrong answer (DETK-0600).
- DETK-0861 gives its reason for the lower bound: no feature with equal
  counts can meet a `p_max` below 1/n. It gives no reason for excluding 1.
  Its own Consequences mention only the 1/n check.
- Criteria: keep the interface promise; a bad option is a usage error
  (DETK-0031); one-sample input should not be refused when its default is
  in range.

## Options

### Option A: accept 1 / number of samples to 1, inclusive (as PR #227 does)

`-p 1` and one-sample input run and shrink nothing; above 1 and below 1/n
exit 2 naming the bound. The help says "from 1 / number of samples to 1".
It matches what the method defines and what the code is meant to do.

### Option B: follow DETK-0861's "(0, 1)" literally and exclude 1

`-p 1` is a usage error. One-sample input then fails by default unless
that case gets its own special rule. The extra rule adds nothing and
breaks the default.

## Decision

Recommended: **Option A**. The upper bound in DETK-0861 is incidental
wording ("or outside (0, 1)"); applied at n = 1 it contradicts the default
the same decision keeps. `p_max = 1` is a defined, harmless no-op. Accepting
this would read DETK-0861's range as [1/n, 1]; no code change is needed.

## Consequences

- PR #227 stands as written: `check_p_max` accepts `1/n <= p_max <= 1`; the
  `-p` help, docs/tools/outlier.md and CHANGELOG say "from 1 / number of
  samples to 1" / "or above 1".
- Under Option B, PR #227 needs a change: exclude 1, and decide what a
  one-sample input does.
