---
template: adr
state: Provisional
authority: [DETK/developer]
date: 2026-11-09
from: {node: release/gather, step: s1}
applies: [release/gather]
allowed_by: [reasonable]
reason: A feature-set difference almost always means mixed annotations; silent filling would hide it
---

# gather refuses samples with different feature sets unless --on-mismatch=fill or drop

## Background

`detk-util gather` (DETK-0012) joins one column per sample on the
feature IDs. When the samples do not list the same features, something
must give: refuse, keep every feature and fill the gaps, or keep only
the shared ones. The issue asks for "clear errors on feature-set
mismatches" and a report of "any features dropped or filled".

## Context

salmon and kallisto write every transcript of the index, htseq-count
every gene of the GTF, featureCounts every meta-feature: samples
quantified against the same reference list the same features, in the
same order. A difference therefore almost always means a sample was run
against another index or annotation release, and its counts are not
comparable. On the other hand some users gather outputs that
legitimately differ (filtered per-sample tables, partial reruns) and
must be able to go on. Silent data change is the failure to avoid, and
the default is part of the 1.0 CLI (DETK-0001).

## Options

1. **Error by default, with `--on-mismatch=fill|drop`**: the error says
   how many features are in all and in every sample, and which samples
   lack how many, with examples; `fill` keeps the union and writes `0`,
   `drop` keeps the intersection. Safe default; an explicit way on.
2. **Outer join and fill with 0 by default** (what csvgather and a plain
   `pandas.concat` do), with a warning. Never stops a run, but hides a
   mixed-reference mistake in a log line.
3. **Inner join by default.** Same silence, and loses data.
4. **Error only, no option.** Strict, but leaves the legitimate cases
   to hand-editing.

## Decision

Option 1. The error catches the common mistake where it can still be
fixed, and the two values cover the legitimate cases explicitly. `fill`
writes `0` because an absent feature in these formats means nothing was
counted for it; rows follow the first sample's features, with features
others add appended in order of appearance; `drop` keeps the first
sample's order. The report records `num_features_all`,
`num_features_shared`, `num_features_filled`, `num_values_filled`,
`num_features_dropped`, per-sample `num_absent` and up to ten
`mismatch_examples`, and the report view shows them.

## Consequences

- `--on-mismatch` is an option beyond the issue's proposed usage; with
  the default value `error` the proposed usage behaves as the issue
  describes.
- Filling with `0` is wrong for TPM-like columns only in the sense that
  the feature was not quantified at all; users gathering `TPM` with
  `fill` should know that. The docs say what `fill` writes.
- Revisit if users mostly pass `fill`: that would suggest a common
  legitimate layout this policy does not anticipate.
