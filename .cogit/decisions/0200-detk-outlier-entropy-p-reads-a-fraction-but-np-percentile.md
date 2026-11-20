---
template: adr
state: Proposed
authority: [human]
date: 2026-11-20
from: {node: release/tutorial-airway}
applies: [release/tutorial-airway]
---

# detk-outlier entropy -p reads a fraction but np.percentile takes a percent

## Background

`detk-outlier entropy` flags the genes (features) whose entropy across the
samples is below a percentile of all the genes' entropies: genes whose
counts come mostly from one or a few samples. The percentile is `-p N`,
which `--help` documents as "between 0 and 1", and whose help example reads
"Flag the features below the 5th entropy percentile" for `-p 0.05`. The
option is part of the 1.0 CLI promise (DETK-0001), so what `-p 0.05` means
must be settled before the tag.

## Context

Found writing the airway tutorial (release/tutorial-airway), which runs
`detk-outlier entropy counts_filtered.csv -p 0.05` on the 24,706 filtered
airway genes:

- `de_toolkit/outlier.py` (`EntropyCounts.__init__`) computes
  `np.percentile(entropy, q=threshold)`. numpy's `q` is a percent, 0 to 100,
  so `-p 0.05` is the 0.05th percentile, not the 5th: the airway run flags
  13 genes, where the 5th percentile flags 925.
- The column name `entropy_p0_05` and the help's "between 0 and 1" both
  read `-p` as a fraction. Nothing rejects `-p 5`, which gives the 5th
  percentile today (925 genes on airway) and names its column
  `entropy_p0_0`.
- A second defect beside it, same function: a counts file with any
  all-zero gene fails (`detk-outlier: error: Series.replace cannot specify
  both a dict-like 'to_replace' and a 'value'`, from
  `dropped_df.replace(dropped_df, "Null")`). Past that line, the results
  are concatenated as [non-zero genes, dropped genes] and then relabelled
  positionally with `results_df.index = counts_obj.counts.index`, which
  would put the entropies after an all-zero gene on the wrong genes. The
  airway tutorial runs on filtered counts (no all-zero genes), so it is not
  affected.
- Criteria: the option does what its help says; 1.0 users get the
  documented meaning; the fix is small and testable.

## Options

### Option A: `-p` is a fraction, as documented; fix the code

`np.percentile(entropy, q=threshold * 100)`, reject a `-p` outside (0, 1)
with a usage error (exit 2), and fix the all-zero case (no crash; align
the rows by gene, not by position). Matches the help, the column name and the example. Changes the
output for every existing `-p` value, which is the bug's fix; 0.x users who
passed `-p 5` to get the 5th percentile get a usage error that says why.

### Option B: `-p` is a percent; fix the help

Keep the code, change the help to "between 0 and 100", the example to
`-p 5`, and the column name. Breaks no 0.x run's numbers, but the column
name and every documented example change, and `-p 0.05` (what the docs and
the tutorials show) silently flags almost nothing.

## Decision

Recommended: Option A, as a node of its own (it is outside
release/tutorial-airway's scope): the documented meaning is the one users
and the tutorials rely on, and a fraction out of range can be refused
loudly. With it, fix the all-zero case and add tests for both
(a percentile against `numpy.percentile(..., 5)`, and an input with an
all-zero gene in the middle).

## Consequences

- `docs/tutorials/airway.md` checks the number of flagged genes (13 today);
  the fix changes it to the 5th percentile's count, so that node updates the
  page's expected output and regenerates `docs/example/` (the page's prose
  does not state the percentage, so only the count changes).
- `tests/outlier/test_outlier.py` calls `entropy(..., 0.05)`; its expected
  flags change with the fix.
- CHANGELOG: under Fixed.
