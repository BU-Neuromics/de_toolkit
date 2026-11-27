---
template: adr
state: Accepted
authority: [human]
date: 2026-11-27
from: {node: release-1-1}
applies: [release-1-1/fgsea-seed]
issue: 174
revisions:
  - {date: 2026-11-27, by: adamlabadorf, change: Accepted, why: "from the terminal: Adam's decision via the driver session, 2026-11-27 (\"Yes, accept all recommendations\"): Option A, with no --seed fgsea draws a seed, uses it and records it"}
---

# What fgsea does with no --seed

- Proposed by: the plan session, 2026-11-27, for the driver to confirm

## Background

fgsea's p-values are estimated by sampling, so two identical runs differ
(reproduced: NES 2.1317 and 2.1233 for the same set). 1.1 adds `--seed`
(Adam's direction). What happens when a run gives none is open.

## Context

- Under DETK-0001 a new option is additive; a 1.0 command line should give the
  same kind of result in 1.1.
- The point of the seed is replay: any run, not only seeded ones, should be
  reproducible from its record.

## Options

**A. No seed given: draw one, use it and record it** (recommended). Runs
stay as varied as in 1.0, but every run's params hold the seed it used, so
any run can be replayed exactly with `--seed`.

**B. No seed given: a fixed default seed.** Every run repeatable by
default, but 1.0 command lines change results in a minor release, and a
fixed seed hides the sampling variation users may need to see.

**C. No seed given: as 1.0, nothing recorded.** Least change; a run
without `--seed` cannot be replayed.

## Decision

Recommended: **A**, for the driver to confirm.

## Consequences

`release-1-1/fgsea-seed` waits on this record.
